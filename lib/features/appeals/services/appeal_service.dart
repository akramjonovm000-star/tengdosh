import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../../core/constants/api_constants.dart';
import 'package:talabahamkor_mobile/features/appeals/models/appeal_model.dart';
import '../../../core/services/auth_service.dart';

class AppealService {
  final AuthService _authService = AuthService();

  Future<String?> _getToken() async {
    return await _authService.getToken();
  }
  
  Future<Map<String, String>> _getHeaders() async {
    final token = await _getToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  // Get List of My Appeals
  Future<AppealsResponse?> getMyAppeals() async {
    final token = await _getToken();
    if (token == null) return null;

    final url = Uri.parse("${ApiConstants.backendUrl}/student/feedback");
    
    // Create headers with User-Agent
    final headers = await _getHeaders();
    headers['User-Agent'] = 'TalabaHamkor/1.0 (Mobile)';

    try {
      print("AppealService: Fetching appeals from $url");
      final response = await http.get(
        url,
        headers: headers,
      );

      print("AppealService: Response ${response.statusCode}");
      
      if (response.statusCode == 200) {
        final dynamic decoded = jsonDecode(response.body);
        
        // Safety check: Is it a List?
        if (decoded is! List) {
           print("Error: Appeals API returned non-list: $decoded");
           return null;
        }

        final List<Appeal> appeals = [];
        for (var e in decoded) {
            try {
                appeals.add(Appeal.fromJson(e));
            } catch (parseError) {
                print("Error parsing appeal item: $parseError | Data: $e");
            }
        }
        
        // Fetch stats separately
        AppealStats stats = AppealStats(answered: 0, pending: 0, closed: 0);
        try {
          final statsResponse = await http.get(
            Uri.parse("${ApiConstants.backendUrl}/student/feedback/stats"),
            headers: {
              "Authorization": "Bearer $token",
              "Accept": "application/json",
              "User-Agent": "TalabaHamkor/1.0 (Mobile)",
            },
          );
          if (statsResponse.statusCode == 200) {
            stats = AppealStats.fromJson(jsonDecode(statsResponse.body));
          }
        } catch (e) {
          print("Error fetching feedback stats: $e");
        }

        print("AppealService: Successfully parsed ${appeals.length} appeals");
        return AppealsResponse(appeals: appeals, stats: stats);
      } else {
        print("Error fetching appeals: ${response.statusCode} - ${response.body}");
        return null;
      }
    } catch (e) {
      print("Exception fetching appeals: $e");
      return null;
    }
  }

  // Get Detail
  Future<AppealDetail?> getAppealDetail(int id) async {
    final token = await _getToken();
    if (token == null) return null;

    final url = Uri.parse("${ApiConstants.backendUrl}/student/feedback/$id");

    try {
      final response = await http.get(
        url,
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return AppealDetail.fromJson(data);
      } else {
        print("Error fetching appeal detail: ${response.body}");
        return null;
      }
    } catch (e) {
      print("Exception fetching appeal detail: $e");
      return null;
    }
  }

  // Create New Appeal
  Future<bool> createAppeal({
    required String text,
    required String role,
    bool isAnonymous = false,
    String? sessionId,
  }) async {
    final token = await _getToken();
    if (token == null) return false;

    final url = Uri.parse("${ApiConstants.backendUrl}/student/feedback");

    try {
      final body = {
        'text': text,
        'role': role,
        'is_anonymous': isAnonymous.toString(),
      };
      if (sessionId != null) {
        body['session_id'] = sessionId;
      }

      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return true;
      }
      print("Appeal Create Error: ${response.statusCode} - ${response.body}");
      return false;
    } catch (e) {
      print("Exception creating appeal: $e");
      return false;
    }
  }

  // Init Upload (for Telegram file)
  Future<Map<String, dynamic>> initUpload(String text, {required String role, bool isAnonymous = false}) async {
    final token = await _getToken();
    if (token == null) return {'success': false, 'message': 'Auth error'};

    final url = Uri.parse("${ApiConstants.backendUrl}/student/feedback/init-upload");
    final sessionId = DateTime.now().millisecondsSinceEpoch.toString();

    try {
      final response = await http.post(
        url,
        headers: await _getHeaders(),
        body: jsonEncode({
          'session_id': sessionId,
          'text': text,
          'role': role,
          'is_anonymous': isAnonymous,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        data['session_id'] = sessionId; // Ensure session_id is returned
        return data; 
      }
      return {'success': false, 'message': 'Server error: ${response.statusCode}'};
    } catch (e) {
      return {'success': false, 'message': 'Connection error: $e'};
    }
  }

  // Check Upload Status
  Future<String> checkUploadStatus(String sessionId) async {
    final token = await _getToken();
    if (token == null) return 'error';

    final url = Uri.parse("${ApiConstants.backendUrl}/student/feedback/upload-status/$sessionId");
    
    try {
      final response = await http.get(
        url,
        headers: { 'Authorization': 'Bearer $token' },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['status'] ?? 'pending';
      }
      return 'error';
    } catch (e) {
      return 'error';
    }
  }

  // Send Reply
  Future<bool> sendReply(int parentId, String text) async {
    final token = await _getToken();
    if (token == null) return false;

    final url = Uri.parse("${ApiConstants.backendUrl}/student/feedback/$parentId/reply");
    
    try {
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: {'text': text},
      );

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      return false;
    }
  }

  // Close Appeal
  Future<bool> closeAppeal(int id) async {
    final token = await _getToken();
    if (token == null) return false;

    final url = Uri.parse("${ApiConstants.backendUrl}/student/feedback/$id/close");
    
    try {
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
