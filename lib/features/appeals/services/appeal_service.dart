import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/models/student.dart';
import 'package:talabahamkor_mobile/features/appeals/models/appeal_model.dart';

class AppealService {
  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  // Get List of My Appeals
  Future<List<Appeal>> getMyAppeals() async {
    final token = await _getToken();
    if (token == null) return [];

    final url = Uri.parse("${ApiConstants.backendUrl}/student/feedback");

    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((e) => Appeal.fromJson(e)).toList();
      } else {
        print("Error fetching appeals: ${response.body}");
        return [];
      }
    } catch (e) {
      print("Exception fetching appeals: $e");
      return [];
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
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
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
  }) async {
    final token = await _getToken();
    if (token == null) return false;

    final url = Uri.parse("${ApiConstants.backendUrl}/student/feedback/");

    try {
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/x-www-form-urlencoded', // Using form data as per backend
        },
        body: {
          'text': text,
          'role': role,
          'is_anonymous': isAnonymous.toString(),
        },
      );

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      print("Exception creating appeal: $e");
      return false;
    }
  }
}
