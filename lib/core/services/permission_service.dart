import 'package:permission_handler/permission_handler.dart';
import 'dart:io';

class PermissionService {
  
  static Future<void> requestInitialPermissions() async {
    // List of permissions to request
    List<Permission> permissions = [
      Permission.camera,
      Permission.storage, // legacy storage
      Permission.notification,
    ];
    
    // For Android 13+ Photo/Video permissions are separate
    if (Platform.isAndroid) {
       // Check SDK version logically or just request these specific ones safely
       // Flutter Permission Handler handles API level checks internally usually
       permissions.add(Permission.photos);
       // permissions.add(Permission.videos); // If needed
    }

    try {
      Map<Permission, PermissionStatus> statuses = await permissions.request();
      
      statuses.forEach((permission, status) {
        print('Permission ${permission.toString()}: $status');
      });
      
    } catch (e) {
      print("Error requesting permissions: $e");
    }
  }
}
