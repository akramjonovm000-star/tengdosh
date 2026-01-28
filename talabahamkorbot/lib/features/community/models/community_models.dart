class Post {
  final String id;
  final String authorName;
  final String? authorUsername; // @handle
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
  final DateTime createdAt; // Added

  Post({
    required this.id,
    required this.authorName,
    this.authorUsername,
    required this.authorAvatar,
    required this.authorRole,
    required this.content,
    this.timeAgo = "Hozirgina",
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
  });
}

class Comment {
  final String id;
  final String postId; // Added
  final String authorName;
  final String authorAvatar; // Url or Initials
  final String? authorUsername; // Added
  final String authorRole; // Added
  final String content;
  final String timeAgo;
  final DateTime createdAt; // Added for sorting if needed
  
  final int likes; // Added
  final bool isLiked; // Added
  final bool isLikedByAuthor; // Added
  final bool isMine; // Added
  
  final String? replyToUserName; // Added
  final String? replyToContent; // Added

  Comment({
    required this.id,
    this.postId = "",
    required this.authorName,
    this.authorAvatar = "",
    this.authorUsername,
    this.authorRole = "Talaba",
    required this.content,
    required this.timeAgo,
    required this.createdAt,
    this.likes = 0,
    this.isLiked = false,
    this.isLikedByAuthor = false,
    this.isMine = false,
    this.replyToUserName,
    this.replyToContent,
  });
  
  Comment copyWith({
    String? id,
    String? postId,
    String? authorName,
    String? authorAvatar,
    String? authorUsername,
    String? authorRole,
    String? content,
    String? timeAgo,
    DateTime? createdAt,
    int? likes,
    bool? isLiked,
    bool? isLikedByAuthor,
    bool? isMine,
    String? replyToUserName,
    String? replyToContent,
  }) {
    return Comment(
      id: id ?? this.id,
      postId: postId ?? this.postId,
      authorName: authorName ?? this.authorName,
      authorAvatar: authorAvatar ?? this.authorAvatar,
      authorUsername: authorUsername ?? this.authorUsername,
      authorRole: authorRole ?? this.authorRole,
      content: content ?? this.content,
      timeAgo: timeAgo ?? this.timeAgo,
      createdAt: createdAt ?? this.createdAt,
      likes: likes ?? this.likes,
      isLiked: isLiked ?? this.isLiked,
      isLikedByAuthor: isLikedByAuthor ?? this.isLikedByAuthor,
      isMine: isMine ?? this.isMine,
      replyToUserName: replyToUserName ?? this.replyToUserName,
      replyToContent: replyToContent ?? this.replyToContent,
    );
  }
}

class Chat {
  final String id;
  final String partnerName;
  final String partnerAvatar;
  final String lastMessage;
  final String timeAgo;
  final int unreadCount;
  final bool isOnline;

  Chat({
    required this.id,
    required this.partnerName,
    required this.partnerAvatar,
    required this.lastMessage,
    required this.timeAgo,
    this.unreadCount = 0,
    this.isOnline = false,
  });
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
}
