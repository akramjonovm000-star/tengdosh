import 'dart:io';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'auth_service.dart';
import '../constants/api_constants.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class PushNotificationService {
  static final FirebaseMessaging _fcm = FirebaseMessaging.instance;

  static Future<void> initialize() async {
    try {
      // 1. Request Permission (iOS)
      if (Platform.isIOS) {
        await _fcm.requestPermission(
          alert: true,
          badge: true,
          sound: true,
        );
      }

      // 2. Get Token
      String? token = await _fcm.getToken();
      if (token != null) {
        if (kDebugMode) print("FCM Token: $token");
        // Move to background to avoid blocking initialization
        _registerTokenWithBackend(token); 
      }

      // 3. Listen for Token Refreshes
      _fcm.onTokenRefresh.listen((newToken) {
        _registerTokenWithBackend(newToken);
      });

      // 4. Handle Foreground Messages
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        if (kDebugMode) print("Got foreground message: ${message.notification?.title}");
        // We can show a local notification here if needed
      });

      // 5. Handle Background/Terminated Messages
      FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
        if (kDebugMode) print("App opened from notification: ${message.data}");
        // Deep link to specific screen
      });

    } catch (e) {
      if (kDebugMode) print("Error initializing Push Notifications: $e");
    }
  }

  static Future<void> _registerTokenWithBackend(String token) async {
    try {
      final authService = AuthService();
      final userToken = await authService.getToken();
      
      if (userToken == null) return;

      final response = await http.post(
        Uri.parse("${ApiConstants.backendUrl}/student/notifications/register-token"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $userToken",
        },
        body: jsonEncode({"fcm_token": token}),
      );

      if (response.statusCode == 200) {
        if (kDebugMode) print("Successfully registered FCM token with backend.");
      } else {
        if (kDebugMode) print("Failed to register FCM token: ${response.body}");
      }
    } catch (e) {
      if (kDebugMode) print("Error registering FCM token: $e");
    }
  }
}
