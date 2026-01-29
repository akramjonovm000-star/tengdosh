import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';
import '../constants/api_constants.dart';
import 'auth_service.dart';
import '../models/attendance.dart';
import '../models/lesson.dart';
import 'package:talabahamkor_mobile/features/social/models/social_activity.dart';

class DataService {
  final AuthService _authService = AuthService();
  static const bool useMock = false; // Disable Mock Data

  // Callback for auth errors
  static Function(String)? onAuthError;

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  // Centralized Error Handling
  void _handleAuthError(http.Response response) {
    if (response.statusCode == 401) {
      try {
        final body = json.decode(response.body);
        if (body['detail'] == 'HEMIS_AUTH_ERROR') {
          onAuthError?.call('HEMIS_AUTH_ERROR');
        }
      } catch (_) {}
    }
  }

  Future<http.Response> _get(String url, {Duration timeout = const Duration(seconds: 15)}) async {
    final response = await http.get(Uri.parse(url), headers: await _getHeaders()).timeout(timeout);
    _handleAuthError(response);
    return response;
  }

  Future<http.Response> _post(String url, {Object? body, Duration timeout = const Duration(seconds: 15)}) async {
    final response = await http.post(
      Uri.parse(url), 
      headers: await _getHeaders(),
      body: body != null ? json.encode(body) : null,
    ).timeout(timeout);
    _handleAuthError(response);
    return response;
  }

  // 1. Get Profile
  Future<Map<String, dynamic>> getProfile() async {
    final response = await _get(ApiConstants.profile);

    if (response.statusCode == 200) {
      final body = json.decode(response.body);
      return body['data'] ?? body;
    }
    throw Exception('Failed to load profile');
  }

  // Cache for Dashboard
  Map<String, dynamic>? _dashboardCache;
  DateTime? _lastDashboardFetch;

  // 2. Get Dashboard Stats (Via Backend Proxy for Real Data)
  Future<Map<String, dynamic>> getDashboardStats({bool forceRefresh = false}) async {
    // Check Cache (valid for 5 mins)
    if (!forceRefresh && _dashboardCache != null && _lastDashboardFetch != null) {
      if (DateTime.now().difference(_lastDashboardFetch!).inMinutes < 5) {
        return _dashboardCache!;
      }
    }

    try {
      final response = await _get(ApiConstants.dashboard);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        // Backend returns top-level fields directly in current Schema
        final result = {
          "gpa": double.tryParse(data['gpa']?.toString() ?? "0") ?? 0.0,
          "missed_hours": data['missed_hours'] ?? 0,
          "missed_hours_excused": data['missed_hours_excused'] ?? 0,
          "missed_hours_unexcused": data['missed_hours_unexcused'] ?? 0,
          "activities_count": data['activities_count'] ?? 0,
          "clubs_count": data['clubs_count'] ?? 0,
          "activities_approved_count": data['activities_approved_count'] ?? 0
        };

        // Update Cache
        _dashboardCache = result;
        _lastDashboardFetch = DateTime.now();
        return result;
      }
    } catch (e) {
      print("Dashboard Error: $e");
    }

    // Fallback: Real 0s (Clean Data Policy)
    return {
      "gpa": 0.0,
      "missed_hours": 0,
      "missed_hours_excused": 0, 
      "missed_hours_unexcused": 0,
      "activities_count": 0,
      "clubs_count": 0
    };
  }

  // Clear Session Cache (Logout)
  void clearCache() {
    _dashboardCache = null;
    _lastDashboardFetch = null;
    print("DataService: Cache cleared.");
  }


  // 3. Get Activities
  Future<List<dynamic>> getActivities() async {
    try {
      final response = await _get(ApiConstants.activities);
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      debugPrint("DataService API error: $e");
    }
    return [];
  }

  // NEW: Init Upload Session
  Future<void> initUploadSession(String sessionId, String category) async {
    final response = await _post(
      '${ApiConstants.activities}/upload/init',
      body: {
        'session_id': sessionId,
        'category': category
      },
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to init session: ${response.body}');
    }
  }

  // NEW: Check Upload Status
  Future<Map<String, dynamic>> checkUploadStatus(String sessionId) async {
    final response = await _get('${ApiConstants.activities}/upload/status/$sessionId');

    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    return {"status": "pending"};
  }

  Future<SocialActivity?> addActivity(String category, String name, String description, String date, {String? sessionId}) async {
    final token = await _authService.getToken();
    var request = http.MultipartRequest('POST', Uri.parse(ApiConstants.activities));
    request.headers['Authorization'] = 'Bearer $token';
    
    request.fields['category'] = category;
    request.fields['name'] = name;
    request.fields['description'] = description;
    request.fields['date'] = date;
    
    if (sessionId != null) {
      request.fields['session_id'] = sessionId;
    }
    
    final response = await request.send();
    
    if (response.statusCode == 200 || response.statusCode == 201) {
      final respStr = await response.stream.bytesToString();
      return SocialActivity.fromJson(json.decode(respStr));
    } else {
      // Check for Auth Error
      if (response.statusCode == 401) {
        final respStr = await response.stream.bytesToString();
        try {
          final body = jsonDecode(respStr);
          if (body['detail'] == 'HEMIS_AUTH_ERROR') {
            onAuthError?.call('HEMIS_AUTH_ERROR');
          }
        } catch (_) {}
      }
      throw Exception('Failed to add activity: ${response.statusCode}');
    }
  }

  // 4. Get Clubs
  Future<List<dynamic>> getMyClubs() async {
     return [];
  }

  // 5. Get Feedback
  Future<List<dynamic>> getMyFeedback() async {
    try {
      final response = await _get(ApiConstants.feedback);
      if (response.statusCode == 200) return json.decode(response.body);
    } catch (e) {
      debugPrint("Feedback Load Error: $e");
    }
    return [];
  }

  // 6. Send Feedback (Multipart)
  Future<bool> sendFeedback(String text, String role, String? filePath, {bool isAnonymous = false}) async {
    try {
      final token = await _authService.getToken();
      var request = http.MultipartRequest('POST', Uri.parse(ApiConstants.feedback));
      
      request.headers.addAll({
        'Authorization': 'Bearer $token',
      });

      request.fields['text'] = text;
      request.fields['role'] = role;
      request.fields['is_anonymous'] = isAnonymous.toString();

      if (filePath != null) {
        request.files.add(await http.MultipartFile.fromPath('file', filePath));
      }

      var response = await request.send().timeout(const Duration(seconds: 30));
      
      if (response.statusCode == 401) {
        final respStr = await response.stream.bytesToString();
        try {
          final body = jsonDecode(respStr);
          if (body['detail'] == 'HEMIS_AUTH_ERROR') {
            onAuthError?.call('HEMIS_AUTH_ERROR');
          }
        } catch (_) {}
      }
      
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      debugPrint("Feedback Send Error: $e");
      return false;
    }
  }

  // 6.5 Get Feedback Detail (Chat)
  Future<Map<String, dynamic>?> getFeedbackDetail(int id) async {
    try {
      final response = await _get('${ApiConstants.feedback}$id');
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      debugPrint("Feedback Detail Error: $e");
    }
    return null;
  }

  // 6.6 Reply to Feedback
  Future<void> replyToFeedback(int id, String text) async {
    final response = await _post(
      '${ApiConstants.feedback}$id/reply',
      body: {'text': text},
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to reply');
    }
  }


  // 7. Get Documents
  Future<List<dynamic>> getMyDocuments() async {
    final response = await _get(ApiConstants.documents);
    if (response.statusCode == 200) return json.decode(response.body);
    throw Exception('Failed to load documents');
  }

  // 9. Get Detailed Attendance List
  Future<List<Attendance>> getAttendanceList({String? semester}) async {
    try {
      String url = ApiConstants.attendanceList;
      if (semester != null && semester.isNotEmpty) {
        url += "?semester=$semester";
      }

      final response = await _get(url);

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        final data = body is Map && body.containsKey('data') ? body['data'] : body;
        final List<dynamic> items = (data is List) ? data : (data['items'] ?? []);
        return items.map((json) => Attendance.fromJson(json)).toList();
      } else {
        throw Exception("Failed to load attendance: ${response.statusCode}");
      }
    } catch (e) {
       print("DataService: Error fetching attendance: $e");
       return [];
    }
  }

  // 11. Get Weekly Schedule
  Future<List<Lesson>> getSchedule() async {
    try {
      final response = await _get(ApiConstants.scheduleList);

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        final data = body['data'];
        final List<dynamic> items = (data is List) ? data : (data['items'] ?? []);
        return items.map((json) => Lesson.fromJson(json)).toList();
      } else {
        throw Exception("Failed to load schedule: ${response.statusCode}");
      }
    } catch (e) {
      print("DataService: Error fetching schedule: $e");
      return [];
    }
  }



  // 12. Get Detailed Grades (O'zlashtirish)
  Future<List<dynamic>> getGrades() async {
    try {
      final response = await _get(ApiConstants.grades);

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
           return body['data'];
        }
      } 
      return [];
    } catch (e) {
      print("DataService: Error fetching grades: $e");
      return [];
    }
  }

  // 13. Get Detailed Subjects
  Future<List<dynamic>> getSubjects() async {
    try {
      final response = await _get(ApiConstants.subjects);

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body['data'];
      }
      return [];
    } catch (e) {
      print("DataService: Error fetching subjects: $e");
      return [];
    }
  }

  // 14. Get Subject Resources
  Future<List<dynamic>> getResources(String subjectId) async {
    try {
      final response = await _get("${ApiConstants.resources}/$subjectId");

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body['data'];
      }
      return [];
    } catch (e) {
      print("DataService: Error fetching resources: $e");
      return [];
    }
  }

  // 15. Send Resource to Bot
  Future<bool> sendResourceToBot(String url, String name) async {
    try {
      final response = await _post(
        "${ApiConstants.resources}/send",
        body: {"url": url, "name": name}
      );

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        print("Bot Send Response: $body");
        return body['success'] == true;
      }
      return false;
    } catch (e) {
      print("DataService: Error sending resource: $e");
      return false;
    }
  }

  // 16. Get Subject Details
  Future<Map<String, dynamic>?> getSubjectDetails(String subjectId) async {
    try {
      final response = await _get("${ApiConstants.academic}/subject/$subjectId/details");

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
      return null;
    } catch (e) {
      print("DataService: Error fetching subject details: $e");
      return null;
    }
  }

  // 17. Send AI Message
  Future<String?> sendAiMessage(String message) async {
    try {
      final response = await _post(
        ApiConstants.aiChat,
        body: {'message': message},
      );

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
           return body['data'];
        }
      }
      return null;
    } catch (e) {
      print("DataService: Error sending AI message: $e");
      return null;
    }
  }

  // 18. Get AI History
  Future<List<dynamic>?> getAiHistory() async {
    try {
      final response = await _get('${ApiConstants.backendUrl}/ai/history');

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
           return body['data'];
        }
      }
      return null;
    } catch (e) {
      print("DataService: Error fetching AI history: $e");
      return null;
    }
  }

  // 19. Clear AI History
  Future<bool> clearAiHistory() async {
    try {
      final response = await http.delete(
        Uri.parse('${ApiConstants.backendUrl}/ai/history'),
        headers: await _getHeaders(),
      );
      _handleAuthError(response);
      return response.statusCode == 200;
    } catch (e) {
      print("DataService: Error clearing AI history: $e");
      return false;
    }
  }

  // 20. Request Document
  Future<String?> requestDocument(String type) async {
    try {
      final response = await _post(
        ApiConstants.documentsSend,
        body: {'type': type},
      );

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
           return body['message'];
        } else {
           return body['message']; // Return error message from server
        }
      }
      return null;
    } catch (e) {
      print("DataService: Error requesting document: $e");
      return null;
    }
  }

  // 21. AI Summarize (Konspekt)
  Future<String?> summarizeContent({String? text, String? filePath, String? fileName}) async {
    try {
      final token = await _authService.getToken();
      var request = http.MultipartRequest('POST', Uri.parse('${ApiConstants.backendUrl}/ai/summarize'));
      
      request.headers['Authorization'] = 'Bearer $token';

      if (filePath != null) {
        request.files.add(await http.MultipartFile.fromPath('file', filePath, filename: fileName));
      }
      
      if (text != null && text.isNotEmpty) {
        request.fields['text'] = text;
      }

      final response = await request.send().timeout(const Duration(seconds: 60));
      
      if (response.statusCode == 200) {
        final respStr = await response.stream.bytesToString();
        final body = json.decode(respStr);
        if (body['success'] == true) {
          return body['data'];
        }
      } else if (response.statusCode == 401) {
        final respStr = await response.stream.bytesToString();
        try {
          final body = jsonDecode(respStr);
          if (body['detail'] == 'HEMIS_AUTH_ERROR') {
            onAuthError?.call('HEMIS_AUTH_ERROR');
          }
        } catch (_) {}
      }
    } catch (e) {
      debugPrint("Summarize Error: $e");
    }
    return null;
  }
}
