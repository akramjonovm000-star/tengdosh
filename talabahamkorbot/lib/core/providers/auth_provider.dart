import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/auth_service.dart';
import '../models/student.dart';
// import '../constants/universities.dart'; // No longer needed
// import '../constants/api_constants.dart'; // No longer dynamic
import '../services/data_service.dart';

class AuthProvider with ChangeNotifier {
  final AuthService _authService = AuthService();
  Student? _currentUser;
  bool _isLoading = true;
  bool _isAuthUpdateRequired = false;

  Student? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _currentUser != null;
  bool get isAuthUpdateRequired => _isAuthUpdateRequired;

  AuthProvider() {
    loadUser();
    
    // Listen for auth errors from DataService
    // We import it here or at top
    // Note: We need to import data_service.dart
    _initDataServiceListener();
  }

  void _initDataServiceListener() {
    // This is a bit of a singleton-ish approach but effective for global errors
    // Since DataService is static for the callback
    DataService.onAuthError = (errorType) {
      if (errorType == 'HEMIS_AUTH_ERROR') {
        _isAuthUpdateRequired = true;
        notifyListeners();
      }
    };
  }
  
  void resetAuthUpdateRequired() {
    _isAuthUpdateRequired = false;
    notifyListeners();
  }

  Future<void> loadUser() async {
    try {
      _currentUser = await _authService.getSavedUser();
    } catch (e) {
      print("Error loading user: $e");
      await _authService.logout();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Alias for clearer intent in UI
  Future<void> checkLoginStatus() => loadUser();

  Future<String?> login(String login, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final student = await _authService.login(login, password);
      if (student != null) {
        _currentUser = student;
        // URL is now static constant, no need to save preference
        _isLoading = false;
        notifyListeners();
        return null; // Success
      } else {
         _isLoading = false;
        notifyListeners();
        return "Login yoki parol noto'g'ri";
      }
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return "Xatolik yuz berdi: $e";
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    _currentUser = null;
    notifyListeners();
  }

  // Allow other screens (Home) to update simple state without full re-logic
  Future<void> updateUser(Map<String, dynamic> json) async {
    try {
      final updatedStudent = Student.fromJson(json);
      _currentUser = updatedStudent;
      // Also update local storage so it persists on restart
      await _authService.saveProfileManually(json);
      notifyListeners();
    } catch (e) {
      print("Error updating user state: $e");
    }
  }

  Future<bool> updateUsername(String newUsername) async {
    final success = await _authService.updateUsername(newUsername);
    if (success) {
      // Re-load to update UI
      await loadUser();
    }
    return success;
  }

  Future<String?> loginWithToken(String token) async {
    _isLoading = true;
    notifyListeners();

    try {
      final student = await _authService.loginWithOAuthToken(token);
      if (student != null) {
        _currentUser = student;
        _isLoading = false;
        notifyListeners();
        return null;
      } else {
        _isLoading = false;
        notifyListeners();
        return "Tizimga kirishda xatolik (Token yaroqsiz)";
      }
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return "Xatolik: $e";
    }
  }
}
