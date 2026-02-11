import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart'; // Add MediaType
import 'package:flutter/foundation.dart';
import '../constants/api_constants.dart';
import 'auth_service.dart';
import '../models/attendance.dart';
import '../models/lesson.dart';
import 'package:talabahamkor_mobile/features/social/models/social_activity.dart';
import 'package:talabahamkor_mobile/features/home/models/announcement_model.dart';
import 'package:talabahamkor_mobile/features/home/models/banner_model.dart'; // [NEW]
import 'local_database_service.dart';
import '../../features/academic/models/survey_models.dart';

class DataService {
  final AuthService _authService = AuthService();
  final LocalDatabaseService _dbService = LocalDatabaseService();
  static const bool useMock = false; // Disable Mock Data

  // Callback for auth errors
  static Function(String)? onAuthError;

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
      'User-Agent': 'TalabaHamkor/1.0 (Mobile)',
    };
  }
  
  // Centralized Error Handling
  void _handleAuthError(http.Response response) {
    // DISCONNECTION FIX: Do not trigger global auth update on 401.
    // This allows the user to continue using cached data or retry without being blocked.
    /*
    if (response.statusCode == 401) {
      try {
        final body = json.decode(response.body);
        if (body['detail'] == 'HEMIS_AUTH_ERROR') {
          onAuthError?.call('HEMIS_AUTH_ERROR');
        }
      } catch (_) {}
    }
    */
  }

  Future<http.Response> _get(String url, {Duration timeout = const Duration(seconds: 60)}) async {
    final response = await http.get(Uri.parse(url), headers: await _getHeaders()).timeout(timeout);
    _handleAuthError(response);
    return response;
  }

  Future<http.Response> _post(String url, {Object? body, Duration timeout = const Duration(seconds: 45)}) async {
    final response = await http.post(
      Uri.parse(url), 
      headers: await _getHeaders(),
      body: body != null ? json.encode(body) : null,
    ).timeout(timeout);
    _handleAuthError(response);
    return response;
  }
  
  // Public Accessors for Management Services
  Future<http.Response> authGet(String url) => _get(url);
  Future<http.Response> authPost(String url, {Object? body}) => _post(url, body: body);




  // 1. Get Profile
  Future<Map<String, dynamic>> getProfile() async {
    final response = await _get(ApiConstants.profile);

    if (response.statusCode == 200) {
      final body = json.decode(response.body);
      return body['data'] ?? body;
    } else if (response.statusCode == 403) {
      // Premium revoked/expired
      throw Exception("PREMIUM_REQUIRED");
    }
    throw Exception('Failed to load profile');
  }

  // 26. Upload Avatar
  Future<String?> uploadAvatar(File imageFile) async {
    try {
      final uri = Uri.parse('${ApiConstants.backendUrl}/student/image');
      final request = http.MultipartRequest('POST', uri);
      
      // Auth Header
      final token = await _authService.getToken();
      request.headers['Authorization'] = 'Bearer $token';

      // File
      request.files.add(
        await http.MultipartFile.fromPath(
          'file', 
          imageFile.path,
          contentType: MediaType('image', 'jpeg')
        )
      );

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data']['image_url'];
        } else {
             throw Exception(body['message'] ?? "Server xatosi");
        }
      }
      throw Exception("Server xatosi: ${response.statusCode}");
    } catch (e) {
      print("Error uploading avatar: $e");
      rethrow; // Pass error to UI
    }
  }

  // Cache for Dashboard
  Map<String, dynamic>? _dashboardCache;

  DateTime? _lastDashboardFetch;

  // 2. Get Dashboard Stats (Via Backend Proxy for Real Data)
  Future<Map<String, dynamic>> getDashboardStats({bool refresh = false, String? semester}) async {
    final student = await _authService.getSavedUser();
    final studentId = student?.id ?? 0;

    // 1. Skip Local Cache - Always Fetch from API (User Request)
    // if (!refresh) { ... }

    // 2. Fetch from API
    return await _backgroundRefreshDashboard(studentId, refresh: refresh);
  }

  Future<Map<String, dynamic>> _backgroundRefreshDashboard(int studentId, {bool refresh = false, String? semester}) async {
    try {
      String url = ApiConstants.dashboard;
      if (refresh) {
        url += (url.contains('?') ? '&' : '?') + 'refresh=true';
      }
      if (studentId > 0 && semester != null) {
         // Note: Backend dashboard might not support filtering yet, 
         // but we adding param structure for future or if we modify backend
      }
      
      final response = await _get(url, timeout: const Duration(seconds: 60));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final result = {
          "gpa": double.tryParse(data['gpa']?.toString() ?? "0") ?? 0.0,
          "missed_hours": data['missed_hours'] ?? 0,
          "missed_hours_excused": data['missed_hours_excused'] ?? 0,
          "missed_hours_unexcused": data['missed_hours_unexcused'] ?? 0,
          "activities_count": data['activities_count'] ?? 0,
          "clubs_count": data['clubs_count'] ?? 0,
          "activities_approved_count": data['activities_approved_count'] ?? 0,
          "has_active_election": data['has_active_election'] ?? false,
          "active_election_id": data['active_election_id']
        };

        // Update Local DB (Non-blocking or at least non-failing for UI)
        try {
          await _dbService.saveCache('dashboard', studentId, result);
        } catch (e) {
          print("Warning: Failed to cache dashboard: $e");
        }
        
        return result; // RETURN LIVE DATA
      }
    } catch (e) {
      print("Dashboard Sync Error: $e");
    }



    // FALLBACK: Try to load from cache if API failed
    try {
      final cached = await _dbService.getCache('dashboard', studentId);
      if (cached != null) {
         return Map<String, dynamic>.from(cached);
      }
    } catch (_) {}

    return {
      "gpa": 0.0,
      "missed_hours": 0,
      "missed_hours_excused": 0, 
      "missed_hours_unexcused": 0,
      "activities_count": 0,
      "clubs_count": 0,
      "has_active_election": false
    };
  }

  Map<String, dynamic> _getMockProfile() {
      return {
        "id": "3902111",
        "full_name": "Aliyev Vali Valiyevich",
        "group_number": "315-21 Axborot Xavfsizligi",
        "faculty": "Kiberxavfsizlik Fakulteti",
        "phone": "+998901234567"
      };
  }

  Map<String, dynamic> _getMockStats() {
      return {
        "gpa": 4.8,
        "missed_hours": 12,
        "activities_count": 12,
        "clubs_count": 3
      };
  }

  // Management Dashboard
  Future<Map<String, dynamic>> getManagementDashboard({bool refresh = false}) async {
    try {
      String url = ApiConstants.managementDashboard;
      if (refresh) {
        url += (url.contains('?') ? '&' : '?') + 'refresh=true';
      }
      final response = await _get(url);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching management dashboard: $e");
    }
    return {};
  }

  Future<List<dynamic>> getManagementFaculties() async {
    try {
      final response = await _get(ApiConstants.managementFaculties);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body['data'];
      }
    } catch (e) {
      debugPrint("DataService: Error fetching management faculties: $e");
    }
    return [];
  }

  Future<List<dynamic>> getManagementLevels(int facultyId) async {
    try {
      final response = await _get("${ApiConstants.managementFaculties}/$facultyId/levels");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body['data'];
      }
    } catch (e) {
      debugPrint("DataService: Error fetching management levels: $e");
    }
    return [];
  }

  Future<List<dynamic>> getManagementGroupStudents(String groupNumber) async {
    try {
      final response = await _get("${ApiConstants.managementGroups}/$groupNumber/students");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body['data'];
      }
    } catch (e) {
      debugPrint("DataService: Error fetching management group students: $e");
    }
    return [];
  }

  Future<Map<String, dynamic>> searchStudents({
    String? query,
    int? facultyId,
    String? educationType,
    String? educationForm,
    String? levelName,
    String? specialtyName,
    String? groupNumber,
  }) async {
    try {
      final queryParams = <String>[];
      if (query != null && query.isNotEmpty) queryParams.add("query=${Uri.encodeComponent(query)}");
      if (facultyId != null) queryParams.add("faculty_id=$facultyId");
      if (educationType != null) queryParams.add("education_type=${Uri.encodeComponent(educationType)}");
      if (educationForm != null) queryParams.add("education_form=${Uri.encodeComponent(educationForm)}");
      if (levelName != null) queryParams.add("level_name=${Uri.encodeComponent(levelName)}");
      if (specialtyName != null) queryParams.add("specialty_name=${Uri.encodeComponent(specialtyName)}");
      if (groupNumber != null) queryParams.add("group_number=${Uri.encodeComponent(groupNumber)}");

      String url = "${ApiConstants.managementStudents}/search";
      if (queryParams.isNotEmpty) {
        url += "?${queryParams.join("&")}";
      }

      final response = await _get(url);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body;
      }
    } catch (e) {
      debugPrint("DataService: Error searching students: $e");
    }
    return {"success": false, "data": [], "total_count": 0, "app_users_count": 0};
  }

  Future<List<dynamic>> searchStaff({
    String? query,
    int? facultyId,
    String? role,
  }) async {
    try {
      final queryParams = <String>[];
      if (query != null && query.isNotEmpty) queryParams.add("query=${Uri.encodeComponent(query)}");
      if (facultyId != null) queryParams.add("faculty_id=$facultyId");
      if (role != null) queryParams.add("role=${Uri.encodeComponent(role)}");

      String url = "${ApiConstants.managementStaff}/search";
      if (queryParams.isNotEmpty) {
        url += "?${queryParams.join("&")}";
      }

      final response = await _get(url);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body['data'];
      }
    } catch (e) {
      debugPrint("DataService: Error searching staff: $e");
    }
    return [];
  }

  Future<List<dynamic>> getManagementSpecialties({int? facultyId, String? educationType}) async {
    try {
      String url = "${ApiConstants.backendUrl}/management/specialties";
      final queryParams = <String>[];
      if (facultyId != null) queryParams.add("faculty_id=$facultyId");
      if (educationType != null) queryParams.add("education_type=${Uri.encodeComponent(educationType)}");
      
      if (queryParams.isNotEmpty) {
        url += "?${queryParams.join("&")}";
      }
      final response = await _get(url);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body['data'];
      }
    } catch (e) {
      debugPrint("DataService: Error fetching management specialties: $e");
    }
    return [];
  }

  Future<List<dynamic>> getManagementGroups({
    int? facultyId, 
    String? levelName,
    String? educationType,
    String? educationForm,
    String? specialtyName,
  }) async {
    try {
      String url = "${ApiConstants.backendUrl}/management/groups";
      final queryParams = <String>[];
      if (facultyId != null) queryParams.add("faculty_id=$facultyId");
      if (levelName != null) queryParams.add("level_name=${Uri.encodeComponent(levelName)}");
      if (educationType != null) queryParams.add("education_type=${Uri.encodeComponent(educationType)}");
      if (educationForm != null) queryParams.add("education_form=${Uri.encodeComponent(educationForm)}");
      if (specialtyName != null) queryParams.add("specialty_name=${Uri.encodeComponent(specialtyName)}");
      
      if (queryParams.isNotEmpty) {
        url += "?${queryParams.join("&")}";
      }

      final response = await _get(url);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body['data'];
      }
    } catch (e) {
      debugPrint("DataService: Error fetching management groups: $e");
    }
    return [];
  }

  Future<Map<String, dynamic>> getManagementDocuments({
    String? query,
    int? facultyId,
    String? title,
    String? educationType,
    String? educationForm,
    String? levelName,
    String? specialtyName,
    String? groupNumber,
    int page = 1,
    int limit = 50,
  }) async {
    try {
      final queryParams = <String>[];
      if (query != null && query.isNotEmpty) queryParams.add("query=${Uri.encodeComponent(query)}");
      if (facultyId != null) queryParams.add("faculty_id=$facultyId");
      if (title != null && title.isNotEmpty) queryParams.add("title=${Uri.encodeComponent(title)}");
      if (educationType != null) queryParams.add("education_type=${Uri.encodeComponent(educationType)}");
      if (educationForm != null) queryParams.add("education_form=${Uri.encodeComponent(educationForm)}");
      if (levelName != null) queryParams.add("level_name=${Uri.encodeComponent(levelName)}");
      if (specialtyName != null) queryParams.add("specialty_name=${Uri.encodeComponent(specialtyName)}");
      if (groupNumber != null) queryParams.add("group_number=${Uri.encodeComponent(groupNumber)}");
      queryParams.add("page=$page");
      queryParams.add("limit=$limit");

      String url = ApiConstants.managementDocumentsArchive;
      if (queryParams.isNotEmpty) {
        url += "?${queryParams.join("&")}";
      }

      final response = await _get(url);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body;
      }
    } catch (e) {
      debugPrint("DataService: Error fetching management documents: $e");
    }
    return {"success": false, "data": []};
  }

  Future<Map<String, dynamic>> exportManagementDocumentsZip({
    String? query,
    int? facultyId,
    String? title,
    String? educationType,
    String? educationForm,
    String? levelName,
    String? specialtyName,
    String? groupNumber,
  }) async {
    try {
      final queryParams = <String>[];
      if (query != null && query.isNotEmpty) queryParams.add("query=${Uri.encodeComponent(query)}");
      if (facultyId != null) queryParams.add("faculty_id=$facultyId");
      if (title != null && title.isNotEmpty) queryParams.add("title=${Uri.encodeComponent(title)}");
      if (educationType != null) queryParams.add("education_type=${Uri.encodeComponent(educationType)}");
      if (educationForm != null) queryParams.add("education_form=${Uri.encodeComponent(educationForm)}");
      if (levelName != null) queryParams.add("level_name=${Uri.encodeComponent(levelName)}");
      if (specialtyName != null) queryParams.add("specialty_name=${Uri.encodeComponent(specialtyName)}");
      if (groupNumber != null) queryParams.add("group_number=${Uri.encodeComponent(groupNumber)}");

      String url = "${ApiConstants.backendUrl}/management/documents/export-zip";
      if (queryParams.isNotEmpty) {
        url += "?${queryParams.join("&")}";
      }

      final response = await _post(url);
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      debugPrint("DataService: Error exporting documents zip: $e");
    }
    return {"success": false, "message": "Xatolik yuz berdi"};
  }

  Future<Map<String, dynamic>> getStudentFullDetails(int studentId) async {
    try {
      final response = await _get("${ApiConstants.managementStudents}/$studentId/full-details");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) return body['data'];
      }
    } catch (e) {
      debugPrint("DataService: Error fetching student full details: $e");
    }
    return {};
  }

  // 3. Get Activities
  Future<List<dynamic>> getActivities() async {
    // Attempt to fetch from backend
    try {
      print("DataService: Fetching activities...");
      final response = await http.get(
        Uri.parse(ApiConstants.activities), 
        headers: await _getHeaders()
      ).timeout(const Duration(seconds: 10));
      
      print("DataService: Activities response: ${response.statusCode}");
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      debugPrint("DataService API error: $e");
    }
    
    // Fallback or empty if offline
    if (useMock) {
       // ... existing mock data logic if desired, or return empty
    }
    return [];
  }

  // NEW: Init Upload Session
  Future<void> initUploadSession(String sessionId, String category) async {
    final token = await _authService.getToken();
    final response = await http.post(
      Uri.parse('${ApiConstants.activities}/upload/init'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
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
    final token = await _authService.getToken();
    final response = await http.get(
      Uri.parse('${ApiConstants.activities}/upload/status/$sessionId'),
      headers: {'Authorization': 'Bearer $token'},
    );

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
      // Consume response to debug
      final respStr = await response.stream.bytesToString();
      debugPrint("Add Activity Failed: ${response.statusCode} - $respStr");
      throw Exception('Failed to add activity: ${response.statusCode}');
    }
  }

  // 4. Get Clubs
  Future<List<dynamic>> getMyClubs() async {
     if (useMock) return [];
     return [];
  }

  // Announcements
  Future<List<AnnouncementModel>> getAnnouncementModels() async {
    try {
      final response = await _get(ApiConstants.announcements);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          final List<dynamic> list = body['data'];
          return list.map((item) => AnnouncementModel.fromJson(item)).toList();
        }
      }
    } catch (e) {
      debugPrint("Error fetching announcements: $e");
    }
    return [];
  }

  // Banner
  Future<BannerModel?> getActiveBanner() async {
    try {
      final response = await _get(ApiConstants.banner);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['active'] == true) {
           return BannerModel.fromJson(body);
        }
      }
    } catch (e) {
      debugPrint("Error fetching banner: $e");
    }
    return null;
  }

  Future<void> trackBannerClick(int bannerId) async {
    try {
      await _post('${ApiConstants.banner}/click/$bannerId');
    } catch (e) {
      debugPrint("Error tracking banner click: $e");
    }
  }

  Future<bool> markAnnouncementModelAsRead(int id) async {
    try {
      final response = await _post('${ApiConstants.announcements}/$id/read');
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        return body['success'] == true;
      }
    } catch (e) {
      debugPrint("Error marking announcement as read: $e");
    }
    return false;
  }

  // 5. Get Feedback
  Future<List<dynamic>> getMyFeedback() async {
    try {
      final response = await http.get(
        Uri.parse(ApiConstants.feedback),
        headers: await _getHeaders(),
      ).timeout(const Duration(seconds: 10));
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
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      debugPrint("Feedback Send Error: $e");
      return false;
    }
  }

  // 6.5 Get Feedback Detail (Chat)
  Future<Map<String, dynamic>?> getFeedbackDetail(int id) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.feedback}$id'),
        headers: await _getHeaders(),
      ).timeout(const Duration(seconds: 10));
      
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
    final token = await _authService.getToken();
    final response = await http.post(
      Uri.parse('${ApiConstants.feedback}$id/reply'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: {'text': text},
    ).timeout(const Duration(seconds: 15));

    if (response.statusCode != 200) {
      throw Exception('Failed to reply');
    }
  }


  // 7. Get Documents
  Future<List<dynamic>> getMyDocuments() async {
    final response = await http.get(
      Uri.parse(ApiConstants.documents),
      headers: await _getHeaders(),
    ).timeout(const Duration(seconds: 10));
    if (response.statusCode == 200) return json.decode(response.body);
    throw Exception('Failed to load documents');
  }

  // 9. Get Detailed Attendance List
  Future<List<Attendance>> getAttendanceList({String? semester, bool forceRefresh = false}) async {
    final student = await _authService.getSavedUser();
    final studentId = student?.id ?? 0;
    final semCode = semester ?? 'all';

    // 1. Skip Local Cache - Always Fetch from API (User Request)
    // if (!forceRefresh) { ... }

    return await _backgroundRefreshAttendance(studentId, semCode, refresh: forceRefresh);
  }

  Future<List<Attendance>> _backgroundRefreshAttendance(int studentId, String semCode, {bool refresh = false}) async {
    try {
      String url = ApiConstants.attendanceList;
      List<String> queryParams = [];
      
      if (semCode != 'all') {
        queryParams.add("semester=$semCode");
      }
      if (refresh) {
        queryParams.add("refresh=true");
      }
      
      if (queryParams.isNotEmpty) {
        url += "?${queryParams.join('&')}";
      }

      final response = await _get(url);

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        final data = body is Map && body.containsKey('data') ? body['data'] : body;
        final List<dynamic> items = (data is List) ? data : (data['items'] ?? []);
        
        // DISABLED LOCAL CACHE: No update
        // await _dbService.saveCache('attendance', studentId, {'items': items}, semesterCode: semCode);
        
        return items.map((json) => Attendance.fromJson(json)).toList();
      }
    } catch (e) {
       print("Attendance Sync Error: $e");
    }
    return [];
  }

  // 11. Get Weekly Schedule
  Future<List<Lesson>> getSchedule() async {
    final student = await _authService.getSavedUser();
    final studentId = student?.id ?? 0;
    
    // DISABLED LOCAL CACHE
    // final cached = await _dbService.getCache('schedule', studentId);
    // if (cached != null && cached.containsKey('items')) {
    //    final List<dynamic> items = cached['items'];
    //    // _backgroundRefreshSchedule(studentId);
    //    return items.map((json) => Lesson.fromJson(json)).toList();
    // }

    return await _backgroundRefreshSchedule(studentId);
  }

  Future<List<Lesson>> _backgroundRefreshSchedule(int studentId) async {
    try {
      final response = await _get(ApiConstants.scheduleList);

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        final data = body['data'];
        final List<dynamic> items = (data is List) ? data : (data['items'] ?? []);
        
        // DISABLED LOCAL CACHE: No update
        // await _dbService.saveCache('schedule', studentId, {'items': items});
        
        return items.map((json) => Lesson.fromJson(json)).toList();
      }
    } catch (e) {
      print("Schedule Sync Error: $e");
    }
    return [];
  }



  // 12. Get Detailed Grades (O'zlashtirish)
  Future<List<dynamic>> getGrades({String? semester, bool forceRefresh = false}) async {
    final student = await _authService.getSavedUser();
    final studentId = student?.id ?? 0;
    
    // User requested to remove cache usage for grades.
    // Always force refresh to ensure fresh data from backend.
    return await _backgroundRefreshGrades(studentId, semester: semester, forceRefresh: true);
  }

  Future<List<dynamic>> _backgroundRefreshGrades(int studentId, {String? semester, bool forceRefresh = false}) async {
    try {
      String url = ApiConstants.grades;
      // Build query parameters
      Map<String, String> queryParams = {};
      if (semester != null) queryParams['semester'] = semester;
      if (forceRefresh) queryParams['refresh'] = 'true';
      
      if (queryParams.isNotEmpty) {
        url += (url.contains('?') ? '&' : '?') + Uri(queryParameters: queryParams).query;
      }
      
      final response = await _get(url);

      if (response.statusCode == 200) {
        final dynamic body = json.decode(response.body);
        List<dynamic> items = [];
        
        if (body is Map && body['success'] == true) {
           items = body['data'] ?? [];
        } else if (body is List) {
           items = body;
        }

        if (items.isNotEmpty) {
          // DISABLED LOCAL CACHE: No update
          // try {
          //   final semCode = semester ?? 'all';
          //   final dynamic cached = await _dbService.getCache('subjects', studentId, semesterCode: semCode);
          //   final Map<String, dynamic> existing = (cached is Map) ? Map<String, dynamic>.from(cached) : {};
          //   existing['grades'] = items;
          //   await _dbService.saveCache('subjects', studentId, existing, semesterCode: semCode);
          // } catch (e) {
          //   print("Warning: Failed to cache grades: $e");
          // }
          return items;
        }
      } else {
        print("Grades API Error: ${response.statusCode} - ${response.body}");
      }
    } catch (e) {
      print("Grades Sync Error: $e");
    }
    return [];
  }
  

  // NEW: Get Semesters
  Future<List<dynamic>> getSemesters({bool refresh = false}) async {
    try {
      String url = "${ApiConstants.academic}/semesters";
      if (refresh) {
        url += "?refresh=true";
      }
      final response = await _get(url);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      print("DataService: Error fetching semesters: $e");
    }
    return [];
  }

  // 13. Get Detailed Subjects
  // 13. Get Detailed Subjects
  Future<List<dynamic>> getSubjects({String? semester, bool refresh = false}) async {
    final student = await _authService.getSavedUser();
    final studentId = student?.id ?? 0;

    // DISABLED LOCAL CACHE: Force live data
    // if (!refresh) {
    //   final cached = await _dbService.getCache('subjects', studentId, semesterCode: semester ?? 'all');
    //   if (cached != null && cached.containsKey('list')) {
    //     // Disable silent background refresh to prevent stale backend data from overwriting fresh local cache ("rollback" bug)
    //     // _backgroundRefreshSubjects(studentId, semester: semester);
    //     return cached['list'];
    //   }
    // }
    return await _backgroundRefreshSubjects(studentId, semester: semester, refresh: refresh);
  }

  Future<List<dynamic>> _backgroundRefreshSubjects(int studentId, {String? semester, bool refresh = false}) async {
    try {
      String url = ApiConstants.subjects;
      
      // Add Query Params
      final params = <String>[];
      if (semester != null) params.add("semester=$semester");
      if (refresh) params.add("refresh=true");
      
      if (params.isNotEmpty) {
        url += "?${params.join("&")}";
      }

      final response = await _get(url);

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          final items = body['data'];
          // DISABLED LOCAL CACHE: No update
          // await _dbService.saveCache('subjects', studentId, {'list': items}, semesterCode: semester ?? 'all');
          return items;
        }
      }
    } catch (e) {
      print("Subjects Sync Error: $e");
    }
    return [];
  }

  // 14. Get Subject Resources
  Future<List<dynamic>> getResources(String subjectId) async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConstants.resources}/$subjectId"),
        headers: await _getHeaders(),
      ).timeout(const Duration(seconds: 20));

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
      final response = await http.post(
        Uri.parse("${ApiConstants.resources}/send"),
        headers: await _getHeaders(),
        body: json.encode({"url": url, "name": name})
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
      final response = await http.get(
        Uri.parse("${ApiConstants.academic}/subject/$subjectId/details"),
        headers: await _getHeaders(),
      );

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
      final response = await http.post(
        Uri.parse(ApiConstants.aiChat),
        headers: await _getHeaders(),
        body: json.encode({'message': message}),
      );

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
           return body['data'];
        }
      } else if (response.statusCode == 403) {
        throw Exception("PREMIUM_REQUIRED");
      }
      return null;
    } catch (e) {
      if (e.toString().contains("PREMIUM_REQUIRED")) rethrow;
      print("DataService: Error sending AI message: $e");
      return null;
    }
  }

  // 17.5 Predict Grant
  Future<String?> predictGrant() async {
    try {
      final response = await _post('${ApiConstants.backendUrl}/ai/predict-grant');

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
      return null;
    } catch (e) {
      if (e.toString().contains("PREMIUM_REQUIRED")) rethrow;
      print("DataService: Error predicting grant: $e");
      return null;
    }
  }

  // 18. Get AI History
  Future<List<dynamic>?> getAiHistory() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/ai/history'),
        headers: await _getHeaders(),
      );

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

      return response.statusCode == 200;
    } catch (e) {
      print("DataService: Error clearing AI history: $e");
      return false;
    }
  }
  // 20. Document Management
  Future<List<dynamic>> getDocuments() async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConstants.backendUrl}/student/documents"),
        headers: await _getHeaders(),
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['data'] ?? [];
      }
    } catch (e) {
      print("DataService: Error getting documents: $e");
    }
    return [];
  }

  Future<Map<String, dynamic>> initiateDocUpload({required String sessionId, String? category, String? title}) async {
    try {
      final response = await _post(
        "${ApiConstants.backendUrl}/student/documents/init-upload",
        body: {
          'session_id': sessionId,
          'category': category,
          'title': title,
        },
      );
      return json.decode(response.body);
    } catch (e) {
      print("DataService: Error initiating upload: $e");
      return {"success": false, "message": "Tarmoq xatosi"};
    }
  }

  Future<Map<String, dynamic>> checkDocUploadStatus(String sessionId) async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/student/documents/upload-status/$sessionId");
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print("DataService: Error checking status: $e");
    }
    return {"status": "pending"};
  }

  Future<Map<String, dynamic>> finalizeDocUpload(String sessionId) async {
    try {
      final response = await _post(
        "${ApiConstants.backendUrl}/student/documents/finalize",
        body: {'session_id': sessionId},
      );
      return json.decode(response.body);
    } catch (e) {
      print("DataService: Error finalizing upload: $e");
      return {"success": false, "message": "Tarmoq xatosi"};
    }
  }

  Future<Map<String, dynamic>> initiateFeedbackUpload({
    required String sessionId,
    required String text,
    String role = "dekanat",
    bool isAnonymous = false,
  }) async {
    try {
      final response = await _post(
        "${ApiConstants.backendUrl}/student/feedback/init-upload",
        body: {
          'session_id': sessionId,
          'text': text,
          'role': role,
          'is_anonymous': isAnonymous,
        },
      );
      return json.decode(response.body);
    } catch (e) {
      print("DataService: Error initiating feedback upload: $e");
      return {"success": false, "message": "Tarmoq xatosi"};
    }
  }

  // 24. Election Methods
  Future<Map<String, dynamic>> getElectionDetails(int electionId) async {
    final response = await _get("${ApiConstants.backendUrl}/election/$electionId");
    if (response.statusCode == 200) {
      final body = json.decode(response.body);
      if (body['success'] == true) return body['data'];
    }
    return {};
  }
  
  // ==========================================================
  // TYUTOR MODULE
  // ==========================================================
  
  // 30. Get Tutor Groups
  Future<List<dynamic>> getTutorGroups() async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/tutor/groups");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching tutor groups: $e");
    }
    return [];
  }
  

  // 30.1 Get Group Appeals
  Future<List<dynamic>> getGroupAppeals(String groupNumber) async {
    debugPrint("DataService: Fetching appeals for group '$groupNumber'...");
    try {
      final url = "${ApiConstants.backendUrl}/tutor/groups/${groupNumber.trim()}/appeals";
      debugPrint("DataService: URL: $url");
      final response = await _get(url);
      
      debugPrint("DataService: Status: ${response.statusCode}");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          final list = body['data'] as List;
          debugPrint("DataService: Found ${list.length} appeals");
          return list;
        } else {
             debugPrint("DataService: Success false. Message: ${body['message']}");
        }
      } else {
         debugPrint("DataService: Error Error Body: ${response.body}");
      }
    } catch (e) {
      debugPrint("DataService: Error fetching group appeals: $e");
    }
    return [];
  }

  // 30.2 Reply to Appeal (Tutor)
  Future<void> replyToTutorAppeal(int appealId, String text) async {
    final token = await _authService.getToken();
    final uri = Uri.parse('${ApiConstants.backendUrl}/tutor/appeals/$appealId/reply?text=${Uri.encodeComponent(text)}');
    
    final response = await http.post(
      uri,
      headers: {
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode != 200) {
      throw Exception("Failed to reply: ${response.body}");
    }
  }

  // 31. Get Tutor Dashboard
  Future<Map<String, dynamic>> getTutorDashboard() async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/tutor/dashboard");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching tutor dashboard: $e");
    }
    return {};
  }
  
  // 32. Get Tutor Students
  Future<List<dynamic>> getTutorStudents({String? group}) async {
    try {
      String url = "${ApiConstants.backendUrl}/tutor/students";
      if (group != null) {
        url += "?group=$group";
      }
      
      final response = await _get(url);
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching tutor students: $e");
    }
    return [];
  }

  Future<bool> voteInElection(int electionId, int candidateId) async {
    final response = await _post(
      "${ApiConstants.backendUrl}/election/$electionId/vote",
      body: {"candidate_id": candidateId},
    );
    if (response.statusCode == 200) return true;
    final body = json.decode(response.body);
    throw Exception(body['detail'] ?? "Ovoz berishda xato yuz berdi");
  }

  // 34. Get Tutor Activity Stats
  Future<List<dynamic>?> getTutorActivityStats() async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/tutor/activities/stats");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching activity stats: $e");
      return null;
    }
    return [];
  }

  // 35. Get Group Activities
  Future<List<dynamic>?> getGroupActivities(String groupNumber) async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/tutor/activities/group/$groupNumber");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching group activities: $e");
      return null;
    }
    return [];
  }

  // 36. Review Activity
  Future<bool> reviewActivity(int activityId, String status) async {
    try {
      final response = await _post(
        "${ApiConstants.backendUrl}/tutor/activity/$activityId/review",
        body: {"status": status},
      );
      if (response.statusCode == 200) {
        return true;
      }
    } catch (e) {
      debugPrint("DataService: Error reviewing activity: $e");
    }
    return false;
  }
  
  // 37. Legacy Upload Status (if needed) or keep existing
  Future<Map<String, dynamic>> checkFeedbackUploadStatus(String sessionId) async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/student/feedback/upload-status/$sessionId");
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print("DataService: Error checking feedback status: $e");
    }
    return {"status": "pending"};
  }

  Future<Map<String, dynamic>> createFeedback({
    required String text,
    String role = "dekanat",
    bool isAnonymous = false,
    String? sessionId,
  }) async {
    try {
      final uri = Uri.parse("${ApiConstants.backendUrl}/student/feedback");
      var request = http.MultipartRequest('POST', uri);
      
      final token = await _authService.getToken();
      request.headers['Authorization'] = 'Bearer $token';

      request.fields['text'] = text;
      request.fields['role'] = role;
      request.fields['is_anonymous'] = isAnonymous.toString();
      
      if (sessionId != null) {
        request.fields['session_id'] = sessionId;
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      return json.decode(response.body);
    } catch (e) {
      print("DataService: Error creating feedback: $e");
      return {"status": "error", "message": "Tarmoq xatosi"};
    }
  }

  Future<bool> deleteDocument(int docId) async {
    try {
      final response = await http.delete(
        Uri.parse("${ApiConstants.backendUrl}/student/documents/$docId"),
        headers: await _getHeaders(),
      );
      return response.statusCode == 200;
    } catch (e) {
      print("DataService: Error deleting document: $e");
      return false;
    }
  }

  Future<String?> sendDocumentToBot(int docId) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.backendUrl}/student/documents/$docId/send-to-bot"),
        headers: await _getHeaders(),
      );
      final data = json.decode(response.body);
      return data['message'];
    } catch (e) {
      print("DataService: Error sending doc to bot: $e");
      return "Tarmoq xatosi";
    }
  }

  Future<String?> requestDocument(String type) async {
    try {
      final response = await http.post(
        Uri.parse(ApiConstants.documentsSend),
        headers: await _getHeaders(),
        body: json.encode({'type': type}),
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
  // 21. Certificate Management
  Future<List<dynamic>> getCertificates() async {
    try {
      final response = await http.get(
        Uri.parse("${ApiConstants.backendUrl}/student/certificates"),
        headers: await _getHeaders(),
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['data'] ?? [];
      }
    } catch (e) {
      print("DataService: Error getting certificates: $e");
    }
    return [];
  }

  Future<Map<String, dynamic>> initiateCertificateUpload({required String sessionId, String? title}) async {
    try {
      final response = await _post(
        "${ApiConstants.backendUrl}/student/certificates/init-upload",
        body: {
          'session_id': sessionId,
          'title': title,
        },
      );
      return json.decode(response.body);
    } catch (e) {
      print("DataService: Error initiating certificate upload: $e");
      return {"success": false, "message": "Tarmoq xatosi"};
    }
  }

  Future<Map<String, dynamic>> checkCertUploadStatus(String sessionId) async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/student/certificates/upload-status/$sessionId");
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print("DataService: Error checking certificate status: $e");
    }
    return {"status": "pending"};
  }

  Future<Map<String, dynamic>> finalizeCertUpload(String sessionId) async {
    try {
      final response = await _post(
        "${ApiConstants.backendUrl}/student/certificates/finalize",
        body: {'session_id': sessionId},
      );
      return json.decode(response.body);
    } catch (e) {
      print("DataService: Error finalizing certificate upload: $e");
      return {"success": false, "message": "Tarmoq xatosi"};
    }
  }

  Future<bool> deleteCertificate(int certId) async {
    try {
      final response = await http.delete(
        Uri.parse("${ApiConstants.backendUrl}/student/certificates/$certId"),
        headers: await _getHeaders(),
      );
      return response.statusCode == 200;
    } catch (e) {
      print("DataService: Error deleting certificate: $e");
      return false;
    }
  }

  Future<String?> sendCertificateToBot(int certId) async {
    try {
      final response = await http.post(
        Uri.parse("${ApiConstants.backendUrl}/student/certificates/$certId/send-to-bot"),
        headers: await _getHeaders(),
      );
      final data = json.decode(response.body);
      return data['message'];
    } catch (e) {
      print("DataService: Error sending cert to bot: $e");
      return "Tarmoq xatosi";
    }
  }

  Future<String?> summarizeContent({String? text, String? filePath}) async {
    try {
      final token = await _authService.getToken();
      
      // Use MultipartRequest for optional file upload
      var request = http.MultipartRequest('POST', Uri.parse('${ApiConstants.backendUrl}/ai/summarize'));
      request.headers['Authorization'] = 'Bearer $token';

      if (text != null && text.isNotEmpty) {
        request.fields['text'] = text;
      }

      if (filePath != null) {
        request.files.add(await http.MultipartFile.fromPath('file', filePath));
      }

      var response = await request.send();
      
      if (response.statusCode == 200) {
         final respStr = await response.stream.bytesToString();
         final body = json.decode(respStr);
         if (body['success'] == true) {
            return body['data'];
         } else {
            return "Xatolik: ${body['message']}";
         }
      } else {
         return "Server xatosi: ${response.statusCode}";
      }
    } catch (e) {
      print("DataService: Error summarizing content: $e");
      return "Tarmoq xatosi yoki fayl muammosi.";
    }
  }
  // 22. Upload Profile Image
  Future<String?> uploadProfileImage(String filePath) async {
    try {
      final token = await _authService.getToken();
      
      var request = http.MultipartRequest('POST', Uri.parse('${ApiConstants.backendUrl}/student/image'));
      request.headers['Authorization'] = 'Bearer $token';
      
      request.files.add(await http.MultipartFile.fromPath('file', filePath));
      
      final response = await request.send();
      
      if (response.statusCode == 200) {
        final respStr = await response.stream.bytesToString();
        final body = json.decode(respStr);
        if (body['success'] == true) {
          return body['data']['image_url'];
        }
      }
      return null;
    } catch (e) {
      print("Error uploading profile image: $e");
      return null;
    }
  }

  // 23. Get Payme URL
  Future<String?> getPaymeUrl({int amount = 10000}) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/payment/payme-url?amount=$amount'),
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['url'];
        }
      }
      return null;
    } catch (e) {
      print("Error fetching Payme URL: $e");
      return null;
    }
  }

  // 24. Get Click URL
  Future<String?> getClickUrl({int amount = 10000}) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/payment/click-url?amount=$amount'),
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['url'];
        }
      }
      return null;
    } catch (e) {
      print("Error fetching Click URL: $e");
      return null;
    }
  }

  // 25. Get Uzum URL
  Future<String?> getUzumUrl({int amount = 10000}) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/payment/uzum-url?amount=$amount'),
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['url'];
        }
      }
      return null;
    } catch (e) {
      print("Error fetching Uzum URL: $e");
      return null;
    }
  }

  // 27. Get Subscription Plans
  Future<List<dynamic>> getSubscriptionPlans() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/plans'),
        headers: await _getHeaders(),
      );
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return [];
    } catch (e) {
      print("Error fetching subscription plans: $e");
      return [];
    }
  }

  // 28. Purchase Subscription Plan
  Future<Map<String, dynamic>> purchasePlan(String planId) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConstants.backendUrl}/plans/buy/$planId'),
        headers: await _getHeaders(),
      );
      final body = json.decode(response.body);
      
      if (response.statusCode == 200) {
         return {"status": "success", "message": body['message'] ?? "Muvaffaqiyatli xarid"};
      } else {
         return {"status": "error", "message": body['detail'] ?? "Xatolik"};
      }
    } catch (e) {
      print("Error purchasing plan: $e");
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // 29. Activate Trial
  Future<Map<String, dynamic>> activateTrial() async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConstants.backendUrl}/plans/trial'),
        headers: await _getHeaders(),
      );
      final body = json.decode(response.body);
      
      if (response.statusCode == 200) {
        return body; 
      } else {
        return {"status": "error", "message": body['detail'] ?? "Xatolik"};
      }
    } catch (e) {
      print("Error activating trial: $e");
      return {'status': 'error', 'message': e.toString()};
    }
  }

  // 30. Update Badge
  Future<bool> updateBadge(String emoji) async {
    try {
      final response = await http.put(
        Uri.parse("${ApiConstants.backendUrl}/student/badge"),
        headers: await _getHeaders(),
        body: json.encode({"emoji": emoji}),
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print("DataService: Error updating badge: $e");
      return false;
    }
  }

  // --- Surveys (So'rovnomalar) ---

  Future<SurveyListResponse> getSurveys() async {
    final response = await _get(ApiConstants.surveys);
    if (response.statusCode == 200) {
      return SurveyListResponse.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to load surveys');
  }

  Future<SurveyStartResponse> startSurvey(int surveyId) async {
    final response = await _post(
      ApiConstants.surveyStart,
      body: {'survey_id': surveyId},
    );
    if (response.statusCode == 200) {
      return SurveyStartResponse.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to start survey');
  }

  Future<bool> submitSurveyAnswer(int questionId, String buttonType, dynamic answer) async {
    final response = await _post(
      ApiConstants.surveyAnswer,
      body: {
        'question_id': questionId,
        'button_type': buttonType,
        'answer': answer,
      },
    );
    if (response.statusCode == 200) {
      final body = json.decode(response.body);
      return body['success'] == true;
    }
    return false;
  }

  Future<bool> finishSurvey(int quizRuleId) async {
    final response = await _post(
      ApiConstants.surveyFinish,
      body: {'quiz_rule_id': quizRuleId},
    );
    if (response.statusCode == 200) {
      final body = json.decode(response.body);
      return body['success'] == true;
    }
    return false;
  }

  // 36. Get Tutor Document Stats
  Future<List<dynamic>?> getTutorDocumentStats() async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/tutor/documents/stats");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching document stats: $e");
      return null;
    }
    return [];
  }

  // 37. Get Group Document Details
  Future<List<dynamic>?> getGroupDocumentDetails(String groupNumber) async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/tutor/documents/group/$groupNumber");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching group document details: $e");
      return null;
    }
    return [];
  }

  // 38. Request Documents
  Future<bool> requestDocuments({int? studentId, String? groupNumber, String? categoryName}) async {
    try {
      final response = await _post(
        "${ApiConstants.backendUrl}/tutor/documents/request",
        body: {
          if (studentId != null) 'student_id': studentId,
          if (groupNumber != null) 'group_number': groupNumber,
          if (categoryName != null) 'category': categoryName,
        },
      );
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        return body['success'] == true;
      }
    } catch (e) {
      debugPrint("DataService: Error requesting documents: $e");
    }
    return false;
  }

  // 39. Get Tutor Certificate Stats
  Future<List<dynamic>?> getTutorCertificateStats() async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/tutor/certificates/stats");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching tutor certificate stats: $e");
      return null;
    }
    return [];
  }

  // 40. Get Group Certificate Details
  Future<List<dynamic>?> getTutorGroupCertificateDetails(dynamic groupNumber) async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/tutor/certificates/group/${groupNumber.toString()}");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching group certificate details: $e");
      return null;
    }
    return [];
  }

  // 41. Get Student Certificates for Tutor
  Future<List<dynamic>?> getStudentCertificatesForTutor(int studentId) async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/tutor/certificates/student/$studentId");
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching student certificates for tutor: $e");
      return null;
    }
    return [];
  }

  // 42. Download Student Certificate for Tutor (via Bot)
  Future<String?> downloadStudentCertificateForTutor(int certId) async {
    try {
      final response = await _post("${ApiConstants.backendUrl}/tutor/certificates/$certId/download");
      final body = json.decode(response.body);
      if (response.statusCode == 200) {
        return body['message'] ?? "Sertifikat botga yuborildi";
      }
      return body['message'] ?? "Xatolik yuz berdi";
    } catch (e) {
      debugPrint("DataService: Error downloading certificate: $e");
      return "Tarmoq xatosi";
    }
  }
  // 43. Management Analytics
  Future<Map<String, dynamic>?> getManagementAnalytics() async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/management/analytics");
      if (response.statusCode == 200) {
        final body = json.decode(utf8.decode(response.bodyBytes));
        if (body['success'] == true) {
          return body['data'];
        }
      }
    } catch (e) {
      debugPrint("DataService: Error fetching management analytics: $e");
    }
    return null;
  }

  // 44. Management AI Report
  Future<String?> getManagementAiReport() async {
    try {
      final response = await _get("${ApiConstants.backendUrl}/management/ai-report", timeout: const Duration(seconds: 45));
      if (response.statusCode == 200) {
        final body = json.decode(utf8.decode(response.bodyBytes));
        if (body['success'] == true) {
          return body['data'];
        }
      }
      return "Hisobotni yuklashda xatolik";
    } catch (e) {
      debugPrint("DataService: Error fetching management AI report: $e");
      return "Tarmoq xatosi: $e";
    }
  }

  // 45. Download Student Certificate for Management
  Future<String?> downloadStudentCertificateForManagement(int certId) async {
    try {
      final response = await _post("${ApiConstants.backendUrl}/management/certificates/$certId/download");
      final body = json.decode(response.body);
      if (response.statusCode == 200) {
        return body['message'] ?? "Sertifikat botga yuborildi";
      }
      return body['message'] ?? "Xatolik yuz berdi";
    } catch (e) {
      debugPrint("DataService: Error downloading certificate for management: $e");
      return "Tarmoq xatosi";
    }
  }

  // 46. Download Student Document for Management
  Future<String?> downloadStudentDocumentForManagement(int docId, {String type = "document"}) async {
    try {
      final response = await _post("${ApiConstants.backendUrl}/management/documents/$docId/download?type=$type");
      final body = json.decode(response.body);
      if (response.statusCode == 200) {
        return body['message'] ?? "Hujjat botga yuborildi";
      }
      return body['message'] ?? "Xatolik yuz berdi";
    } catch (e) {
      debugPrint("DataService: Error downloading document for management: $e");
      return "Tarmoq xatosi";
    }
  }

  // 47. Predict Sentiment Analysis
  Future<String?> predictSentiment() async {
    try {
      final response = await _post("${ApiConstants.backendUrl}/ai/predict-sentiment");
      final body = json.decode(utf8.decode(response.bodyBytes));
      if (response.statusCode == 200 && body['success'] == true) {
        return body['data'];
      }
      return body['message'] ?? "Tahlil jarayonida xatolik.";
    } catch (e) {
      debugPrint("DataService: Error predicting sentiment: $e");
      return "Tarmoq xatosi yoki server ishlamayapti.";
    }
  }
}
