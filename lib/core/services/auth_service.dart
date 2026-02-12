import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/student.dart';
import '../constants/api_constants.dart';

class AuthService {
  
  SharedPreferences? _prefs;

  Future<SharedPreferences> get _getPrefs async {
    _prefs ??= await SharedPreferences.getInstance();
    return _prefs!;
  }

  // Bridger for AuthProvider
  Future<bool> loginWithHemis(String login, String password) async {
    final student = await this.login(login, password);
    return student != null;
  }

  Future<void> saveToken(String token) async {
    await _saveToken(token);
  }

  // Telegram Login Stubs
  Future<Map<String, dynamic>> initAuth() async {
    await Future.delayed(const Duration(seconds: 1));
    return {
      'uuid': 'test-uuid',
      'url': 'https://t.me/talabahamkorbot?start=login'
    };
  }

  Future<Map<String, dynamic>?> checkAuth(String uuid) async {
    return null;
  }

  // Using PROXY (Our Server) for Login now as updated in api_constants
  Future<Student?> login(String login, String password) async {
    // 0. DEMO MODE - Disabled strict local logic to allow Backend Real Demo Login
    // if (login == 'demo' && password == '123') { ... }

    final url = Uri.parse(ApiConstants.authLogin);
    try {
      print('AuthService: Attempting login to $url');
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'TalabaHamkor/1.0 (Mobile)',
        },
        body: jsonEncode({'login': login, 'password': password}),
      ).timeout(const Duration(seconds: 15));

      print('AuthService: Response ${response.statusCode}');

      if (response.statusCode == 200) {
        final body = jsonDecode(response.body);
        final data = body['data'];
        
        // Robust extraction: Token might be in 'data' or at root
        final token = data?['token'] ?? body['token'];
        
        if (token != null) {
          final role = data?['role'] ?? body['role'] ?? 'student';
          
          await _saveToken(token);
          await _saveRole(role); 
          
          final profileMap = data?['profile'] ?? body['profile'];
          if (profileMap != null) {
             await _saveProfile(profileMap);
             return Student.fromJson(profileMap);
          }
          return await fetchAndSaveProfile(token);
        } else {
             throw Exception("Token topilmadi. Javob: ${response.body}");
        }
      } else if (response.statusCode == 401 || response.statusCode == 400) {
           final body = jsonDecode(response.body);
           throw Exception(body['error'] ?? "Login yoki parol noto'g'ri");
      } else {
           throw Exception("Server xatosi: ${response.statusCode}");
      }
    } catch (e) {
      print('Auth Error: $e');
      throw e; // Rethrow to stop loading in Provider
    }
  }
  
  // --- Username Methods ---
  
  Future<Map<String, dynamic>> setUsername(String username) async {
    try {
      final token = await getToken();
      if (token == null) return {'success': false, 'message': 'Avtorizatsiya yo\'q'};
      
      final url = Uri.parse("${ApiConstants.backendUrl}/student/username");
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json'
        },
        body: jsonEncode({'username': username}),
      );
      
      final body = jsonDecode(response.body);
      if (response.statusCode == 200) {
        // Update local cache if successful
        final prefs = await _getPrefs;
        final profileStr = prefs.getString('user_profile');
        if (profileStr != null) {
          final profile = jsonDecode(profileStr);
          profile['username'] = username;
          await prefs.setString('user_profile', jsonEncode(profile));
        }
        return body;
      } else {
        return {'success': false, 'message': body['detail'] ?? 'Xatolik'};
      }
    } catch (e) {
      return {'success': false, 'message': 'Tarmoq xatosi: $e'};
    }
  }

  Future<bool> checkUsernameAvailability(String username) async {
    try {
      final token = await getToken();
      if (token == null) return false;
      
      final url = Uri.parse("${ApiConstants.backendUrl}/student/check-username?username=$username");
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json'
        },
      );
      
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body);
        return body['available'] == true;
      }
    } catch (e) {
      print("Check username error: $e");
    }
    return false;
  }

  Future<void> _saveRole(String role) async {
    final prefs = await _getPrefs;
    await prefs.setString('user_role', role);
  }

  Future<String?> getUserRole() async {
    final prefs = await _getPrefs;
    return prefs.getString('user_role') ?? 'student';
  }

  Future<Student?> fetchAndSaveProfile(String token) async {
    try {
      final url = Uri.parse(ApiConstants.profile);
      print('AuthService: Fetching profile from $url');
      
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json'
        },
      ).timeout(const Duration(seconds: 15));
      
      print('AuthService: Profile Response ${response.statusCode}');

      if (response.statusCode == 200) {
        final body = jsonDecode(response.body);
        final profileData = body['data'] ?? body;
        
        await _saveProfile(profileData);
        return Student.fromJson(profileData);
      } else {
        throw Exception("Profilni yuklab bo'lmadi: ${response.statusCode}");
      }
    } catch (e) {
      print('Profile Error: $e');
      throw e;
    }
  }

  Future<void> _saveToken(String token) async {
    final prefs = await _getPrefs;
    await prefs.setString('auth_token', token);
  }

  Future<void> saveProfileManually(Map<String, dynamic> profile) async {
     final prefs = await _getPrefs;
     await prefs.setString('user_profile', jsonEncode(profile));
  }
  
  Future<void> _saveProfile(Map<String, dynamic> profile) async {
     await saveProfileManually(profile);
  }
  
  Future<Student?> getSavedUser() async {
     final prefs = await _getPrefs;
     final profileStr = prefs.getString('user_profile');
     if (profileStr != null) {
       return Student.fromJson(jsonDecode(profileStr));
     }
     return null;
  }

  Future<String?> getToken() async {
    final prefs = await _getPrefs;
    return prefs.getString('auth_token');
  }

  Future<void> logout() async {
    final prefs = await _getPrefs;
    await prefs.clear();
  }

  Future<Student?> loginWithOAuthToken(String token) async {
    try {
      // 1. Save token first
      await _saveToken(token);
      
      // 2. Fetch profile using this token
      final student = await fetchAndSaveProfile(token);
      
      // 3. Save role (standard for token login)
      await _saveRole('student');
      
      return student;
    } catch (e) {
      print("OAuth Token Login Error: $e");
      return null;
    }
  }

  Future<Map<String, dynamic>> deleteAccount(String login, String password) async {
    final url = Uri.parse("${ApiConstants.backendUrl}/auth/delete-account");
    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'login': login, 'password': password}),
      );
      
      final body = jsonDecode(response.body);
      
      if (response.statusCode == 200 && body['success'] == true) {
        return {'success': true};
      } else {
        return {'success': false, 'message': body['detail'] ?? "Xatolik yuz berdi"};
      }
      return {'success': false, 'message': "Tarmoq xatosi: $e"};
    }
  }

  Future<void> updateSavedPassword(String newPassword) async {
    final prefs = await _getPrefs;
    // We don't store raw password in prefs usually for security, 
    // but if we did (for auto-login), we would update it here.
    // However, we DO need to invalidate/update current session if needed.
    // For now, let's assume we just keep the token.
    // But if we have a 'remember me' functional that uses stored creds:
    if (prefs.containsKey('user_password')) {
       await prefs.setString('user_password', newPassword);
    }
  }
}
