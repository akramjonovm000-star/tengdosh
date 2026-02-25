import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../../core/constants/api_constants.dart';
import '../../auth/services/auth_service.dart';

class YetakchiService {
  final AuthService _authService = AuthService();

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  // 1. Dashboard Stats
  Future<Map<String, dynamic>> getDashboardStats() async {
    try {
      final response = await http.get(
        Uri.parse(ApiConstants.yetakchiDashboard),
        headers: await _getHeaders(),
      );
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {};
    } catch (e) {
      return {};
    }
  }

  // 2. Students List
  Future<List<dynamic>> getStudents({
    String? search,
    int? facultyId,
    int? course,
    int skip = 0,
    int limit = 20,
  }) async {
    try {
      final queryParams = <String, String>{
        'skip': skip.toString(),
        'limit': limit.toString(),
      };
      if (search != null && search.isNotEmpty) queryParams['search'] = search;
      if (facultyId != null) queryParams['faculty_id'] = facultyId.toString();
      if (course != null) queryParams['course'] = course.toString();

      final uri = Uri.parse(ApiConstants.yetakchiStudents).replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: await _getHeaders());
      
      if (response.statusCode == 200) {
        return json.decode(response.body) as List<dynamic>;
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  // 3. Activities
  Future<List<dynamic>> getActivities({String? status, int skip = 0, int limit = 20}) async {
    try {
      final queryParams = <String, String>{
        'skip': skip.toString(),
        'limit': limit.toString(),
      };
      if (status != null && status.isNotEmpty) queryParams['status'] = status;

      final uri = Uri.parse(ApiConstants.yetakchiActivities).replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: await _getHeaders());
      
      if (response.statusCode == 200) {
        return json.decode(response.body) as List<dynamic>;
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  // Review Activity
  Future<bool> reviewActivity(int activityId, String status, int points) async {
    try {
      var request = http.MultipartRequest(
        'PUT',
        Uri.parse('${ApiConstants.yetakchiActivities}/$activityId/review'),
      );
      request.headers.addAll(await _getHeaders());
      
      // Remove content-type for multipart
      request.headers.remove('Content-Type');
      
      request.fields['status'] = status;
      request.fields['points'] = points.toString();

      final response = await request.send();
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // 4. Events
  Future<List<dynamic>> getEvents({int skip = 0, int limit = 20}) async {
    try {
      final uri = Uri.parse('${ApiConstants.yetakchiEvents}?skip=$skip&limit=$limit');
      final response = await http.get(uri, headers: await _getHeaders());
      
      if (response.statusCode == 200) {
        return json.decode(response.body) as List<dynamic>;
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  // 5. Documents
  Future<List<dynamic>> getDocuments({String? search, int skip = 0, int limit = 20}) async {
    try {
      final queryParams = <String, String>{
        'skip': skip.toString(),
        'limit': limit.toString(),
      };
      if (search != null && search.isNotEmpty) queryParams['search'] = search;

      final uri = Uri.parse(ApiConstants.yetakchiDocuments).replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: await _getHeaders());
      
      if (response.statusCode == 200) {
        return json.decode(response.body) as List<dynamic>;
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  // 6. Announcements
  Future<bool> createAnnouncement(String content, {String? imagePath}) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse(ApiConstants.yetakchiAnnouncements),
      );
      request.headers.addAll(await _getHeaders());
      request.headers.remove('Content-Type');
      
      request.fields['content'] = content;
      if (imagePath != null) {
        request.files.add(await http.MultipartFile.fromPath('image', imagePath));
      }

      final response = await request.send();
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
