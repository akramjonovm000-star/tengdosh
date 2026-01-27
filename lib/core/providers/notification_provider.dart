import 'dart:async';
import 'package:flutter/foundation.dart';
import '../../features/notifications/services/notification_service.dart';

class NotificationProvider with ChangeNotifier {
  final NotificationService _service = NotificationService();
  int _unreadCount = 0;
  Timer? _pollingTimer;
  bool _isPolling = false;

  int get unreadCount => _unreadCount;

  NotificationProvider() {
    startPolling();
  }

  Future<void> refreshUnreadCount() async {
    try {
      final count = await _service.getUnreadCount();
      if (_unreadCount != count) {
        _unreadCount = count;
        notifyListeners();
      }
    } catch (e) {
      if (kDebugMode) {
        print('Error refreshing unread count: $e');
      }
    }
  }

  void startPolling() {
    if (_isPolling) return;
    _isPolling = true;
    
    // Initial fetch
    refreshUnreadCount();
    
    // Poll every 30 seconds
    _pollingTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      refreshUnreadCount();
    });
  }

  void stopPolling() {
    _pollingTimer?.cancel();
    _isPolling = false;
  }

  @override
  void dispose() {
    stopPolling();
    super.dispose();
  }
}
