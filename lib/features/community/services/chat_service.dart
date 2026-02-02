import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../../../core/constants/api_constants.dart';
import '../../../../core/services/auth_service.dart';
import '../models/community_models.dart';

class ChatService {
  static final ChatService _instance = ChatService._internal();

  factory ChatService() {
    return _instance;
  }

  ChatService._internal();

  final AuthService _authService = AuthService();

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  // Start Chat (or get existing)
  Future<Chat?> startChat(String targetUserId) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConstants.backendUrl}/chat/start/$targetUserId'),
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
         final data = json.decode(utf8.decode(response.bodyBytes));
         // Backend returns { "chat_id": 1, "target_user": {...} }
         // We need to construct a partial Chat object or fetch the full list?
         // Optimally, return a Chat object.
         // Let's manually construct it from the response to be safe.
         return Chat(
           id: data['chat_id'].toString(),
           partnerId: data['target_user']['id'].toString(), // NEW
           partnerName: data['target_user']['full_name'],
           partnerAvatar: data['target_user']['image_url'] ?? "",
           partnerUsername: data['target_user']['username'] ?? "", 
           partnerRole: data['target_user']['role'] ?? "student",  
           lastMessage: "Suhbat boshlandi", 
           timeAgo: "Hozirgina",
           isLastMessageMine: true,
           partnerIsPremium: data['target_user']['is_premium'] ?? false, // NEW
         );
      } else {
        print("Chat Start Error: ${response.statusCode} - ${response.body}");
      }
      return null;
    } catch (e) {
      print("Chat Service Error: $e");
      return null;
    }
  }

  // List Chats
  Future<List<Chat>> getChats() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/chat/list'),
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return data.map((json) => Chat.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print("Chat List Error: $e");
      return [];
    }
  }

  // Get Messages
  Future<List<Message>> getMessages(String chatId, {String? beforeId}) async {
    try {
      String url = '${ApiConstants.backendUrl}/chat/$chatId/messages?limit=50';
      if (beforeId != null) {
        url += '&before_id=$beforeId';
      }
      
      final response = await http.get(
        Uri.parse(url),
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return data.map((json) => Message.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print("Get Messages Error: $e");
      return [];
    }
  }

  // Send Message
  Future<Message?> sendMessage(String chatId, String content) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConstants.backendUrl}/chat/$chatId/send'),
        headers: await _getHeaders(),
        body: json.encode({'content': content}),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        // Construct Message from response: { "id":..., "content":..., "created_at":... }
        return Message(
          id: data['id'].toString(),
          content: data['content'],
          isMe: true, // Always me if I sent it
          timestamp: "Hozirgina",
          isRead: false
        );
      }
      return null;
    } catch (e) {
      print("Send Message Error: $e");
      return null;
    }
  }

  // Get Total Unread Count
  Future<int> getTotalUnreadCount() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/chat/unread-count'),
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return data['total'] ?? 0;
      }
      return 0;
    } catch (e) {
      print("Unread Count Error: $e");
      return 0;
    }
  }
}
