import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/services/auth_service.dart';
import '../../../../core/models/student.dart';
import '../models/community_models.dart';

class CommunityService {
  // Singleton Pattern
  static final CommunityService _instance = CommunityService._internal();

  factory CommunityService() {
    return _instance;
  }

  CommunityService._internal();

  final AuthService _authService = AuthService();

   // --- Subscription / Social ---


  Future<Map<String, int>> getProfileStats(String targetId) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/community/subscribers/count?target_id=$targetId'),
         headers: await _getHeaders(), // Ideally authentication not required? But safer.
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return {
          'followers': data['followers'] ?? 0,
          'following': data['following'] ?? 0,
        };
      }
      return {'followers': 0, 'following': 0};
    } catch (e) {
      return {'followers': 0, 'following': 0};
    }
  }
  
  Future<List<Student>> getFollowers(String targetId) async {
    try {
       final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/community/followers-list/$targetId'),
        headers: await _getHeaders(),
      );
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return data.map((e) => Student.fromJson(e)).toList();
      }
      return [];
    } catch(e) {
      print("Error getting followers: $e");
      return [];
    }
  }

  Future<List<Student>> getFollowing(String targetId) async {
    try {
       final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/community/following-list/$targetId'),
        headers: await _getHeaders(),
      );
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return data.map((e) => Student.fromJson(e)).toList();
      }
      return [];
    } catch(e) {
      print("Error getting following: $e");
      return [];
    }
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  // --- Search History (Recent Users) ---
  Future<void> saveRecentUser(Student student, {String key = 'recent_users'}) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      List<String> history = prefs.getStringList(key) ?? [];
      
      // Remove if exists (by ID check)
      history.removeWhere((item) {
        try {
          final map = json.decode(item);
          return map['id'].toString() == student.id.toString();
        } catch (e) {
          return false;
        }
      });
      
      // Add to start (Convert to JSON string)
      history.insert(0, json.encode(student.toJson()));
      
      // Limit to 10
      if (history.length > 10) {
        history = history.sublist(0, 10);
      }
      
      await prefs.setStringList(key, history);
    } catch (e) {
      print("Error saving recent user: $e");
    }
  }

  Future<List<Student>> getRecentUsers({String key = 'recent_users'}) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final list = prefs.getStringList(key) ?? [];
      return list.map((item) => Student.fromJson(json.decode(item))).toList();
    } catch (e) {
      print("Error getting recent users: $e");
      return [];
    }
  }

  Future<void> clearSearchHistory({String key = 'recent_users'}) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(key);
    } catch (e) {
      print("Error clearing search history: $e");
    }
  }

  Future<List<Student>> searchStudents(String query) async {
    try {
      if (query.length < 2) return [];
      
      final url = Uri.parse('${ApiConstants.backendUrl}/student/search?query=$query');
      final response = await http.get(url, headers: await _getHeaders());
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return data.map((e) => Student.fromJson(e)).toList();
      }
      return [];
    } catch (e) {
      print("Error searching students: $e");
      return [];
    }
  }

  Future<void> createPost(Post post) async {
    try {
      final response = await http.post(
        Uri.parse(ApiConstants.communityPosts),
        headers: await _getHeaders(),
        body: json.encode({
          'content': post.content,
          'category_type': post.scope,
          'is_poll': post.pollOptions != null && post.pollOptions!.isNotEmpty,
          'poll_options': post.pollOptions,
          'target_faculty_id': post.targetFacultyId != null ? int.tryParse(post.targetFacultyId!) : null,
          'target_specialty_name': post.targetSpecialtyId,
        }),
      );

      if (response.statusCode != 200 && response.statusCode != 201) {
        throw Exception("Failed to create post: ${response.statusCode} ${response.body}");
      }
    } catch (e) {
      print("CommunityService: Error creating post: $e");
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getCommunityFilters() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/community/filters/meta'),
        headers: await _getHeaders(),
      );
      if (response.statusCode == 200) {
        return json.decode(utf8.decode(response.bodyBytes));
      }
      return {'faculties': [], 'specialties': []};
    } catch (e) {
      print("Error getting community filters: $e");
      return {'faculties': [], 'specialties': []};
    }
  }

  Future<List<Post>> getPosts({
    required String scope, 
    int skip = 0, 
    int limit = 20,
    int? facultyId,
    String? specialtyName,
  }) async {
    try {
      String url = '${ApiConstants.communityPosts}?category=$scope&skip=$skip&limit=$limit';
      if (facultyId != null) {
        url += '&faculty_id=$facultyId';
      }
      if (specialtyName != null && specialtyName.isNotEmpty) {
        url += '&specialty_name=${Uri.encodeComponent(specialtyName)}';
      }

      final response = await http.get(
        Uri.parse(url),
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return data.map((json) => _mapJsonToPost(json)).toList();
      } else {
        print("CommunityService: Failed to load posts: ${response.statusCode}");
        return [];
      }
    } catch (e) {
      print("CommunityService: Error loading posts: $e");
      return [];
    }
  }

  Future<List<Post>> getRepostedPosts(String studentId, {int skip = 0, int limit = 20}) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.communityPosts}/reposted?target_student_id=$studentId&skip=$skip&limit=$limit'),
        headers: await _getHeaders(),
      );
      print("Reposts Response CODE: ${response.statusCode} for $studentId");

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return data.map((json) => _mapJsonToPost(json)).toList();
      }
      return [];
    } catch (e) {
      print("Error loading reposts: $e");
      return [];
    }
  }

  Future<Post?> getPost(String postId) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.communityPosts}/$postId'),
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        return _mapJsonToPost(json.decode(response.body));
      } else {
        print("CommunityService: Failed to load post: ${response.statusCode}");
        return null;
      }
    } catch (e) {
      print("CommunityService: Error loading post: $e");
      return null;
    }
  }

  Future<Map<String, dynamic>?> likePost(String postId) async {
    final token = await _authService.getToken(); 
    final url = '${ApiConstants.communityPosts}/$postId/like';
    print("CommunityService: Liking post at $url");
    
    try {
      final response = await http.post(
        Uri.parse(url),
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        print("CommunityService: Like failed ${response.statusCode}");
        return null;
      }
    } catch (e) {
      print("CommunityService: Like error $e");
      return null;
    }
  }

  Future<Map<String, dynamic>?> repostPost(String postId) async {
    final url = '${ApiConstants.communityPosts}/$postId/repost';
    print("CommunityService: Reposting post at $url");
    
    try {
      final response = await http.post(
        Uri.parse(url),
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        print("CommunityService: Repost failed ${response.statusCode}");
        return null;
      }
    } catch (e) {
       print("CommunityService: Repost error $e");
       return null;
    }
  }

  Future<bool> votePoll(String postId, int optionIndex) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConstants.communityPosts}/$postId/vote'),
        headers: await _getHeaders(),
        body: json.encode({'option_index': optionIndex}),
      );
      
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      print("CommunityService: Error voting in poll: $e");
      return false;
    }
  }

  Future<bool> deletePost(String postId) async {
    try {
      final response = await http.delete(
         Uri.parse('${ApiConstants.communityPosts}/$postId'),
         headers: await _getHeaders(),
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print("CommunityService: Error deleting post: $e");
      return false;
    }
  }

  Future<bool> editPost(String postId, String newContent) async {
    try {
      final response = await http.put(
        Uri.parse('${ApiConstants.communityPosts}/$postId'),
        headers: await _getHeaders(),
        body: json.encode({
          'content': newContent,
          'category_type': 'university', 
        }),
      );
      
      print("Edit Post Result: ${response.statusCode}");
      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (e) {
      print("CommunityService: Error editing post: $e");
      return false;
    }
  }


  Future<int?> viewPost(String postId) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConstants.communityPosts}/$postId/view'),
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return data['views_count'] as int?;
      }
      return null;
    } catch (e) {
      // print("Error viewing post: $e");
      return null;
    }
  }

  // --- Subscription ---
  Future<Map<String, dynamic>?> toggleSubscription(String targetId) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConstants.backendUrl}/community/subscribe/$targetId'),
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        return json.decode(utf8.decode(response.bodyBytes));
      }
      return {"error": "Server javob bermadi: ${response.statusCode}"};
    } catch (e) {
      print("CommunityService: Toggle sub error: $e");
      return {"error": "Tarmoq xatosi: $e"};
    }
  }

  Future<Map<String, int>?> getSubscriberCounts(String targetId) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/community/subscribers/count?target_id=$targetId'),
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return {
          "followers": data['followers'] ?? 0,
          "following": data['following'] ?? 0
        };
      }
      return null;
    } catch (e) {
      print("CommunityService: Get counts error: $e");
      return null;
    }
  }
  
  Future<bool> checkSubscription(String targetId) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.backendUrl}/community/check-subscription/$targetId'),
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return data['subscribed'] ?? false;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Post _mapJsonToPost(Map<String, dynamic> json) {
    return Post(
      id: json['id'].toString(),
      authorId: json['author_id']?.toString() ?? "0", // NEW
      authorName: json['author_name'] ?? "Noma'lum",
      authorUsername: json['author_username'] ?? "",
      authorAvatar: json['author_avatar'] ?? json['author_image'] ?? json['image'] ?? "", 
      authorRole: json['author_role'] ?? "student", // Use code
      content: json['content'] ?? "",
      timeAgo: _formatDate(json['created_at']),
      scope: json['category_type'],
      targetUniversityId: json['target_university_id']?.toString(),
      targetFacultyId: json['target_faculty_id']?.toString(),
      targetSpecialtyId: json['target_specialty_name'], 
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : DateTime.now(),
      
      likes: json['likes_count'] ?? 0,
      isLiked: json['is_liked_by_me'] ?? false,
      repostsCount: json['reposts_count'] ?? 0,
      isRepostedByMe: json['is_reposted_by_me'] ?? false,
      commentsCount: json['comments_count'] ?? 0,
      isVerified: json['author_is_premium'] ?? false,
      authorIsPremium: json['author_is_premium'] ?? false, // NEW
      authorCustomBadge: json['author_custom_badge'], // NEW
      isMine: json['is_mine'] ?? false,
      views: json['views_count'] ?? 0,
    );
  }

  String _formatDate(String? dateStr) {
    if (dateStr == null) return "";
    try {
      // Backend returns UTC time (e.g. 2024-01-19T07:00:00)
      // We must append 'Z' if missing to properly parse as UTC, or force isUtc: true.
      if (!dateStr.endsWith('Z')) {
        dateStr = "${dateStr}Z";
      }
      
      final date = DateTime.parse(dateStr).toLocal();
      final now = DateTime.now();
      
      final diff = now.difference(date);

      if (diff.inMinutes < 1) return "Hozirgina";
      if (diff.inMinutes < 60) return "${diff.inMinutes} daqiqa oldin";
      if (diff.inHours < 24) return "${diff.inHours} soat oldin";
      return "${diff.inDays} kun oldin";
    } catch (e) {
      return "Yaqinda";
    }
  }

  // --- Mocked Chat Methods (Keep as Mock for now) ---

  Future<List<Comment>> getComments(String postId) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConstants.communityPosts}/$postId/comments?t=${DateTime.now().millisecondsSinceEpoch}'),
        headers: await _getHeaders(),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) {
          final createdAtStr = json['created_at'];
          return Comment.fromJson(json);
        }).toList();
      } else {
        print("CommunityService: Failed to load comments: ${response.statusCode}");
        return [];
      }
    } catch (e) {
      print("CommunityService: Error loading comments: $e");
      return [];
    }
  }

  Future<Comment> createComment(String postId, String content, {String? replyToId}) async {
    try {
      final body = {
        'content': content,
      };
      if (replyToId != null) {
        body['reply_to_comment_id'] = replyToId;
      }

      final response = await http.post(
        Uri.parse('${ApiConstants.communityPosts}/$postId/comments'),
        headers: await _getHeaders(),
        body: json.encode(body),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final jsonMap = json.decode(response.body);
        
        // Map manually because it's a single object, not list
        final createdAtStr = jsonMap['created_at'];
        return Comment.fromJson(jsonMap);
      } else {
        throw Exception("Failed to create comment: ${response.statusCode}");
      }
    } catch (e) {
      print("CommunityService: Error creating comment: $e");
      rethrow;
    }
  }

  Future<bool> likeComment(String commentId) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConstants.backendUrl}/community/comments/$commentId/like'),
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        return true;
      }
      return false;
    } catch (e) {
      print("CommunityService: Error liking comment: $e");
      return false;
    }
  }

  Future<bool> deleteComment(String commentId) async {
    try {
      final response = await http.delete(
        Uri.parse('${ApiConstants.backendUrl}/community/comments/$commentId'),
        headers: await _getHeaders(),
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print("CommunityService: Error deleting comment: $e");
      return false;
    }
  }

  Future<Comment?> editComment(String commentId, String newContent) async {
    try {
      final response = await http.put(
        Uri.parse('${ApiConstants.backendUrl}/community/comments/$commentId'),
        headers: await _getHeaders(),
        body: json.encode({'content': newContent}),
      );

      if (response.statusCode == 200) {
        return Comment.fromJson(json.decode(response.body));
      } else {
        print("CommunityService: Failed to edit comment: ${response.statusCode}");
        return null;
      }
    } catch (e) {
      print("CommunityService: Error editing comment: $e");
      return null;
    }
  }


  Future<Student?> getCurrentUser() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final profileStr = prefs.getString('user_profile');
      if (profileStr != null) {
        return Student.fromJson(json.decode(profileStr));
      }
    } catch (e) {
      print("Error getting cached user: $e");
    }
    return null;
  }
}

