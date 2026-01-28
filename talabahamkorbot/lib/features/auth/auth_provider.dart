import 'dart:async';
import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/auth_service.dart';
import 'package:url_launcher/url_launcher.dart';

enum AuthStatus { initial, authenticating, authenticated, unauthenticated }

class AuthProvider with ChangeNotifier {
  AuthStatus _status = AuthStatus.initial;
  String? _token;
  final AuthService _authService = AuthService();
  Timer? _pollTimer;

  AuthStatus get status => _status;
  String? get token => _token;

  // Check valid token on startup
  Future<void> checkLoginStatus() async {
    final savedToken = await _authService.getToken();
    if (savedToken != null) {
      _token = savedToken;
      _status = AuthStatus.authenticated;
    } else {
      _status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  // Start Login Flow
  Future<void> startLogin() async {
    try {
      _status = AuthStatus.authenticating;
      notifyListeners();

      // 1. Get UUID & Link
      final data = await _authService.initAuth();
      final uuid = data['uuid'];
      final url = data['url'];

      // 2. Open Telegram
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      }

      // 3. Start Polling
      _startPolling(uuid);
    } catch (e) {
      print("Login error: $e");
      _status = AuthStatus.unauthenticated;
      notifyListeners();
    }
  }

  // HEMIS Login
  Future<bool> loginWithHemis(String login, String password) async {
    try {
      _status = AuthStatus.authenticating;
      notifyListeners();
      
      final success = await _authService.loginWithHemis(login, password);
      
      if (success) {
        final token = await _authService.getToken();
        _token = token;
        _status = AuthStatus.authenticated;
        notifyListeners();
        return true;
      } else {
        _status = AuthStatus.unauthenticated;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      return false;
    }
  }

  void _startPolling(String uuid) {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      final data = await _authService.checkAuth(uuid);
      if (data != null && data['status'] == 'verified') {
        _pollTimer?.cancel();
        
        final token = data['token'];
        await _authService.saveToken(token);
        _token = token;
        _status = AuthStatus.authenticated;
        notifyListeners();
      }
    });
  }
  
  Future<void> logout() async {
    await _authService.logout();
    _token = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }
}
