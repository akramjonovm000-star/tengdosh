class Post {
  final String id;
  final String authorId; // NEW
  final String authorName;
  final String authorUsername; // @handle
  final String authorAvatar; // Url or Initials
  final String authorRole; // e.g. "315-21 Guruh", "Dekan"
  final String content;
  final String? timeAgo;
  final int likes;
  final int commentsCount;
  final int sharesCount;
  final int repostsCount;
  final List<String> tags;
  final List<String> mediaUrls; // Images/Videos
  final bool isLiked; // by current user
  final bool isVerified; // Blue checkmark (Official)
  final bool isTyutor; // Special badge
  final int views; // View count
  final int usefulScore; // "Foydali" score
  final List<String>? pollOptions; // If not null, it's a poll
  final List<int>? pollVotes; // Vote counts per option
  final int? userVote; // Index of option user voted for (or null)
  final String? scope; // 'university', 'faculty', 'specialty'
  final String? targetUniversityId;
  final String? targetFacultyId;
  final String? targetSpecialtyId;
  final bool isMine;
  final bool isRepostedByMe;
  final DateTime createdAt; // Added
  final bool authorIsPremium; // NEW
  final String? authorCustomBadge; // NEW

  Post({
    required this.id,
    required this.authorId, // Added
    required this.authorName,
    this.authorUsername = "",
    required this.authorAvatar,
    required this.authorRole,
    required this.content,
    this.timeAgo = "Hozirgina", // Can be calculated from createdAt
    required this.createdAt, // Added
    this.likes = 0,
    this.commentsCount = 0,
    this.sharesCount = 0,
    this.repostsCount = 0,
    this.tags = const [],
    this.mediaUrls = const [],
    this.isLiked = false,
    this.isVerified = false,
    this.isTyutor = false,
    this.views = 0,
    this.usefulScore = 0,
    this.pollOptions,
    this.pollVotes,
    this.userVote,
    this.scope,
    this.targetUniversityId,
    this.targetFacultyId,
    this.targetSpecialtyId,
    this.isMine = false,
    this.isRepostedByMe = false,
    this.authorIsPremium = false, // NEW
    this.authorCustomBadge, // NEW
  });

  factory Post.fromJson(Map<String, dynamic> json) {
    // print("DEBUG POST JSON: $json"); // Just for build tracking, can remove later
    return Post(
      id: json['id'].toString(),
      authorId: json['author_id'].toString(), // NEW
      content: json['content'],
      scope: json['category_type'],
      authorName: json['author_name'],
      authorUsername: json['author_username'] ?? "",
      authorAvatar: json['author_avatar'] ?? "",
      authorRole: json['author_role'] ?? "Talaba",
      createdAt: DateTime.parse(json['created_at']),
      likes: json['likes_count'] ?? 0,
      commentsCount: json['comments_count'] ?? 0,
      repostsCount: json['reposts_count'] ?? 0,
      isLiked: json['is_liked_by_me'] ?? false,
      isRepostedByMe: json['is_reposted_by_me'] ?? false,
      isMine: json['is_mine'] ?? false,
      targetUniversityId: json['target_university_id']?.toString(),
      targetFacultyId: json['target_faculty_id']?.toString(),
      targetSpecialtyId: json['target_specialty_name'],
      authorIsPremium: json['author_is_premium'] ?? false, // NEW
      authorCustomBadge: json['author_custom_badge'], // NEW
      pollOptions: json['poll_options'] != null ? List<String>.from(json['poll_options']) : null,
      pollVotes: json['poll_votes'] != null ? List<int>.from(json['poll_votes']) : null,
      userVote: json['user_vote_index'],
    );
  }

  Post copyWith({
    String? id,
    String? authorId,
    String? authorName,
    String? authorUsername,
    String? authorAvatar,
    String? authorRole,
    String? content,
    String? timeAgo,
    int? likes,
    int? commentsCount,
    int? sharesCount,
    int? repostsCount,
    List<String>? tags,
    List<String>? mediaUrls,
    bool? isLiked,
    bool? isVerified,
    bool? isTyutor,
    int? views,
    int? usefulScore,
    List<String>? pollOptions,
    List<int>? pollVotes,
    int? userVote,
    String? scope,
    String? targetUniversityId,
    String? targetFacultyId,
    String? targetSpecialtyId,
    bool? isMine,
    bool? isRepostedByMe,
    DateTime? createdAt,
    bool? authorIsPremium, // NEW
    String? authorCustomBadge, // NEW
  }) {
    return Post(
      id: id ?? this.id,
      authorId: authorId ?? this.authorId,
      authorName: authorName ?? this.authorName,
      authorUsername: authorUsername ?? this.authorUsername,
      authorAvatar: authorAvatar ?? this.authorAvatar,
      authorRole: authorRole ?? this.authorRole,
      content: content ?? this.content,
      timeAgo: timeAgo ?? this.timeAgo,
      createdAt: createdAt ?? this.createdAt,
      likes: likes ?? this.likes,
      commentsCount: commentsCount ?? this.commentsCount,
      sharesCount: sharesCount ?? this.sharesCount,
      repostsCount: repostsCount ?? this.repostsCount,
      tags: tags ?? this.tags,
      mediaUrls: mediaUrls ?? this.mediaUrls,
      isLiked: isLiked ?? this.isLiked,
      isVerified: isVerified ?? this.isVerified,
      isTyutor: isTyutor ?? this.isTyutor,
      views: views ?? this.views,
      usefulScore: usefulScore ?? this.usefulScore,
      pollOptions: pollOptions ?? this.pollOptions,
      pollVotes: pollVotes ?? this.pollVotes,
      userVote: userVote ?? this.userVote,
      scope: scope ?? this.scope,
      targetUniversityId: targetUniversityId ?? this.targetUniversityId,
      targetFacultyId: targetFacultyId ?? this.targetFacultyId,
      targetSpecialtyId: targetSpecialtyId ?? this.targetSpecialtyId,
      isMine: isMine ?? this.isMine,
      isRepostedByMe: isRepostedByMe ?? this.isRepostedByMe,
      authorIsPremium: authorIsPremium ?? this.authorIsPremium, // NEW
      authorCustomBadge: authorCustomBadge ?? this.authorCustomBadge, // NEW
    );
  }
}

class Comment {
  final String id;
  final String postId; // Added
  final String authorId; // NEW
  final String authorName;
  final String authorUsername; // Added
  final String authorAvatar;
  final String content;
  final String timeAgo;
  final DateTime createdAt; // Added
  final int likes;
  final bool isLiked;
  final bool isLikedByAuthor;
  final String? authorRole;
  final String? replyToUserName; // Restored
  final String? replyToContent;  // Restored
  final bool isMine;             // Restored
  final String? replyToCommentId; // NEW
  final bool authorIsPremium; // NEW
  final String? authorCustomBadge; // NEW

  Comment({
    required this.id,
    required this.postId,
    required this.authorId,
    required this.authorName,
    this.authorUsername = "", 
    this.authorAvatar = "",
    required this.content,
    required this.timeAgo,
    required this.createdAt,
    this.likes = 0,
    this.isLiked = false,
    this.isLikedByAuthor = false,
    this.authorRole,
    this.replyToUserName,
    this.replyToContent,
    this.isMine = false,
    this.replyToCommentId, // NEW
    this.authorIsPremium = false, // NEW
    this.authorCustomBadge, // NEW
  });

  factory Comment.fromJson(Map<String, dynamic> json) {
    DateTime parseDate(dynamic dateStr) {
      if (dateStr == null) return DateTime.now();
      try {
        return DateTime.parse(dateStr.toString());
      } catch (e) {
        return DateTime.now();
      }
    }

    return Comment(
      id: json['id']?.toString() ?? "0",
      postId: json['post_id']?.toString() ?? "0",
      content: json['content']?.toString() ?? "",
      authorId: json['author_id']?.toString() ?? "0",
      authorName: json['author_name']?.toString() ?? "Noma'lum",
      authorUsername: json['author_username']?.toString() ?? "",
      authorAvatar: json['author_avatar']?.toString() ?? "",
      authorRole: json['author_role']?.toString() ?? "Talaba",
      createdAt: parseDate(json['created_at']),
      timeAgo: "Hozirgina", 
      likes: json['likes_count'] is int ? json['likes_count'] : int.tryParse(json['likes_count']?.toString() ?? "0") ?? 0,
      isLiked: json['is_liked'] ?? false,
      isMine: json['is_mine'] ?? false,
      isLikedByAuthor: json['is_liked_by_author'] ?? false,
      replyToUserName: json['reply_to_username']?.toString(), 
      replyToContent: json['reply_to_content']?.toString(), 
      replyToCommentId: json['reply_to_comment_id']?.toString(), // NEW
      authorIsPremium: json['author_is_premium'] ?? false, // NEW
      authorCustomBadge: json['author_custom_badge']?.toString(), // NEW
    );
  }

  Comment copyWith({
    String? id,
    String? postId,
    String? authorId,
    String? authorName,
    String? authorUsername,
    String? authorAvatar,
    String? content,
    String? timeAgo,
    DateTime? createdAt,
    int? likes,
    bool? isLiked,
    bool? isLikedByAuthor,
    String? authorRole,
    String? replyToUserName,
    String? replyToContent,
    bool? isMine,
    String? replyToCommentId, // NEW
    bool? authorIsPremium, // NEW
    String? authorCustomBadge, // NEW
  }) {
    return Comment(
      id: id ?? this.id,
      postId: postId ?? this.postId,
      authorId: authorId ?? this.authorId,
      authorName: authorName ?? this.authorName,
      authorUsername: authorUsername ?? this.authorUsername,
      authorAvatar: authorAvatar ?? this.authorAvatar,
      content: content ?? this.content,
      timeAgo: timeAgo ?? this.timeAgo,
      createdAt: createdAt ?? this.createdAt,
      likes: likes ?? this.likes,
      isLiked: isLiked ?? this.isLiked,
      isLikedByAuthor: isLikedByAuthor ?? this.isLikedByAuthor,
      authorRole: authorRole ?? this.authorRole,
      replyToUserName: replyToUserName ?? this.replyToUserName,
      replyToContent: replyToContent ?? this.replyToContent,
      isMine: isMine ?? this.isMine,
      replyToCommentId: replyToCommentId ?? this.replyToCommentId, // NEW
      authorIsPremium: authorIsPremium ?? this.authorIsPremium, // NEW
      authorCustomBadge: authorCustomBadge ?? this.authorCustomBadge, // NEW
    );
  }
}

class Chat {
  final String id;
  final String partnerId; // NEW
  final String partnerName;
  final String partnerAvatar;
  final String partnerUsername; 
  final String partnerRole;     
  final String lastMessage;
  final String timeAgo;
  final int unreadCount;
  final bool isOnline;
  final bool isLastMessageMine; 
  final String? partnerCustomBadge; // NEW

  Chat({
    required this.id,
    required this.partnerId, // NEW
    required this.partnerName,
    required this.partnerAvatar,
    required this.partnerUsername, 
    required this.partnerRole,     
    required this.lastMessage,
    required this.timeAgo,
    this.unreadCount = 0,
    this.isOnline = false,
    this.isLastMessageMine = false, 
    this.partnerCustomBadge, // NEW
  });

  factory Chat.fromJson(Map<String, dynamic> json) {
    final user = json['target_user'] ?? {};
    return Chat(
      id: json['id'].toString(),
      partnerId: user['id']?.toString() ?? "0", // NEW
      partnerName: user['full_name'] ?? "Foydalanuvchi",
      partnerAvatar: user['image_url'] ?? "",
      partnerUsername: user['username'] ?? "", 
      partnerRole: user['role'] ?? "Talaba",  
      lastMessage: json['last_message'] ?? "",
      timeAgo: _formatDate(json['last_message_time']), 
      unreadCount: json['unread_count'] ?? 0,
      isOnline: false, 
      isLastMessageMine: json['is_last_message_mine'] ?? false, 
      partnerCustomBadge: user['custom_badge'], // NEW
    );
  }

  String get formattedName {
    if (partnerName.isEmpty) return "Noma'lum";
    final parts = partnerName.trim().split(RegExp(r'\s+'));
    
    String capitalize(String s) {
      if (s.isEmpty) return "";
      if (s.length == 1) return s.toUpperCase();
      return s[0].toUpperCase() + s.substring(1).toLowerCase();
    }

    if (parts.length >= 2) {
      final surname = capitalize(parts[0]);
      final name = capitalize(parts[1]);
      return "$name $surname";
    } else {
      return capitalize(parts[0]);
    }
  }
}

class Message {
  final String id;
  final String content;
  final bool isMe;
  final String timestamp;
  final bool isRead;
  final String? mediaUrl;

  Message({
    required this.id,
    required this.content,
    required this.isMe,
    required this.timestamp,
    this.isRead = false,
    this.mediaUrl,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'].toString(),
      content: json['content'] ?? "",
      isMe: json['is_mine'] ?? false,
      timestamp: _formatTime(json['created_at']),
      isRead: json['is_read'] ?? false,
    );
  }
}

String _formatDate(String? dateStr) {
  if (dateStr == null) return "Unknown";
  try {
    if (!dateStr.endsWith('Z')) dateStr = "${dateStr}Z"; // Fix Timezone
    final date = DateTime.parse(dateStr).toLocal(); 
    final now = DateTime.now();
    final diff = now.difference(date);
    
    if (diff.inMinutes < 1) return "Hozirgina";
    if (diff.inMinutes < 60) return "${diff.inMinutes} daqiqa";
    if (diff.inHours < 24) return "${diff.inHours} soat";
    if (diff.inDays < 7) return "${diff.inDays} kun";
    return "${date.day}/${date.month}/${date.year}";
  } catch (e) {
    return "";
  }
}

String _formatTime(String? dateStr) {
  if (dateStr == null) return "";
  try {
    if (!dateStr.endsWith('Z')) dateStr = "${dateStr}Z"; // Fix Timezone
    final date = DateTime.parse(dateStr).toLocal();
    return "${date.hour.toString().padLeft(2,'0')}:${date.minute.toString().padLeft(2, '0')}";
  } catch (e) {
    return "";
  }
}
