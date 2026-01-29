import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/models/student.dart';
import '../models/community_models.dart' as community;

class CommunityService {
  static final CommunityService _instance = CommunityService._internal();

  factory CommunityService() {
    return _instance;
  }

  CommunityService._internal();

  // ALIAS for backward compatibility
  Future<List<community.Post>> getPosts({String scope = 'university'}) => getFeed(scope: scope);

  // Helper to get headers
  Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  // Helper: Get Current User (Mapped from Core Student)
  Future<Person?> getCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final name = prefs.getString('full_name') ?? "Talaba";
    final avatar = prefs.getString('image_url') ?? "";
    return Person(fullName: name, imageUrl: avatar);
  }

  // --- POSTS API (REAL) ---

  Future<List<community.Post>> getFeed({String scope = 'university'}) async {
    try {
      final headers = await _getHeaders();
      // Map scope to backend category_type
      final category = scope; 
      
      final url = Uri.parse('${ApiConstants.backendUrl}/posts?category=$category');
      
      final response = await http.get(url, headers: headers);

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(response.bodyBytes));
        return data.map((json) => _fromJsonPost(json)).toList();
      } else {
        print("Failed to load posts: ${response.statusCode} ${response.body}");
        return [];
      }
    } catch (e) {
      print("Error fetching posts: $e");
      // Fallback: Return empty to avoid confusion with "Old Mock Data"
      return [];
    }
  }

  Future<void> createPost(community.Post post) async {
    try {
      final headers = await _getHeaders();
      final url = Uri.parse('${ApiConstants.backendUrl}/posts');
      
      final body = {
        "content": post.content,
        "category_type": post.scope ?? 'university'
      };

      final response = await http.post(
        url, 
        headers: headers, 
        body: jsonEncode(body)
      );

      if (response.statusCode != 200) {
        throw Exception("Failed to create post: ${response.body}");
      }
    } catch (e) {
      print("Error creating post: $e");
      rethrow;
    }
  }

  community.Post? getPost(String id) {
     return null; // TODO: Implement get single post API if needed
  }
  
  // --- COMMENTS API (REAL) ---

  Future<List<community.Comment>> getComments(String postId) async {
    try {
      final headers = await _getHeaders();
      final url = Uri.parse('${ApiConstants.backendUrl}/posts/$postId/comments');
      
      final response = await http.get(url, headers: headers);

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(utf8.decode(response.bodyBytes));
        return data.map((json) => _fromJsonComment(json)).toList();
      } else {
        return [];
      }
    } catch (e) {
      return [];
    }
  }

  Future<community.Comment> createComment(String postId, String content, {String? replyToId}) async {
    final headers = await _getHeaders();
    final url = Uri.parse('${ApiConstants.backendUrl}/posts/$postId/comments');
    
    final body = {
      "content": content,
      "reply_to_comment_id": replyToId // nullable
    };

    final response = await http.post(
      url, 
      headers: headers, 
      body: jsonEncode(body)
    );

    if (response.statusCode == 200) {
      final json = jsonDecode(utf8.decode(response.bodyBytes));
      return _fromJsonComment(json);
    } else {
      throw Exception("Failed to send comment");
    }
  }

  Future<bool> likeComment(String commentId) async {
    try {
      final headers = await _getHeaders();
      final url = Uri.parse('${ApiConstants.backendUrl}/comments/$commentId/like');
      
      final response = await http.post(url, headers: headers);
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // --- MAPPING HELPERS ---
  
  community.Post _fromJsonPost(Map<String, dynamic> json) {
    final date = DateTime.tryParse(json['created_at'] ?? "") ?? DateTime.now();
    
    return community.Post(
      id: json['id'].toString(),
      authorName: json['author_name'] ?? "Noma'lum",
      authorUsername: json['author_username'] ?? "",
      authorAvatar: json['author_avatar'] ?? "",
      authorRole: json['author_role'] ?? "student",
      content: json['content'] ?? "",
      
      likes: json['likes_count'] ?? 0,
      commentsCount: json['comments_count'] ?? 0,
      sharesCount: 0, 
      repostsCount: json['reposts_count'] ?? 0,
      
      timeAgo: _formatTimeAgo(date),
      createdAt: date,
      isVerified: false, 
      usefulScore: 0,
      
      scope: json['category_type'] ?? 'university',
      targetUniversityId: json['target_university_id'],
      targetFacultyId: json['target_faculty_id'],
      targetSpecialtyId: json['target_specialty_name'], 
      
      mediaUrls: [], 
      tags: [],
      pollOptions: [],
      pollVotes: [],
    );
  }

  community.Comment _fromJsonComment(Map<String, dynamic> json) {
    final date = DateTime.tryParse(json['created_at'] ?? "") ?? DateTime.now();

    return community.Comment(
      id: json['id'].toString(),
      postId: json['post_id'].toString(),
      authorName: json['author_name'] ?? "Noma'lum",
      authorAvatar: json['author_avatar'] ?? "",
      authorRole: json['author_role'] ?? "Talaba",
      content: json['content'] ?? "",
      timeAgo: _formatTimeAgo(date),
      createdAt: date,
      
      likes: json['likes_count'] ?? 0,
      isLiked: json['is_liked'] ?? false,
      isLikedByAuthor: json['is_liked_by_author'] ?? false,
      isMine: json['is_mine'] ?? false,
      
      replyToUserName: json['reply_to_username'],
      replyToContent: json['reply_to_content'],
    );
  }

  String _formatTimeAgo(DateTime date) {
    final diff = DateTime.now().difference(date);
    if (diff.inDays > 365) return "${(diff.inDays / 365).floor()} yil oldin";
    if (diff.inDays > 30) return "${(diff.inDays / 30).floor()} oy oldin";
    if (diff.inDays > 0) return "${diff.inDays} kun oldin";
    if (diff.inHours > 0) return "${diff.inHours} soat oldin";
    if (diff.inMinutes > 0) return "${diff.inMinutes} daqiqa oldin";
    return "Hozirgina";
  }
  
  // Stubs
  Future<List<community.Chat>> getChats() async => [];
  Future<List<community.Message>> getMessages(String id) async => [];
}

class Person {
  final String fullName;
  final String? imageUrl;
  Person({required this.fullName, this.imageUrl});
}
