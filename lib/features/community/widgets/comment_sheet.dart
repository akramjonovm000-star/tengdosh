import 'package:flutter/material.dart';
import 'dart:async';
import 'package:flutter/services.dart'; // For Haptics
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';
import 'comment_item.dart';
import 'comment_input.dart';
import 'reply_thread_sheet.dart';

class CommentSheet extends StatefulWidget {
  final Post post;
  final Function(int newCount)? onCommentCountChanged;

  const CommentSheet({
    super.key, 
    required this.post,
    this.onCommentCountChanged
  });

  @override
  State<CommentSheet> createState() => _CommentSheetState();
}

class _CommentSheetState extends State<CommentSheet> {
  final CommunityService _service = CommunityService();
  final ScrollController _scrollController = ScrollController();
  
  List<Comment> _comments = [];
  final Set<String> _expandedCommentIds = {}; // Track expanded threads inline
  bool _isLoading = true;
  bool _isSending = false;
  
  // State for Optimistic Updates
  String _currentUserName = "Men"; 
  String _currentUserAvatar = "";
  String _currentUserId = "";

  Comment? _replyingTo;
  Post? _currentPost;

  @override
  void initState() {
    super.initState();
    _currentPost = widget.post; 
    _loadCurrentUser(); 
    _refreshAll();
  }

  Future<void> _loadCurrentUser() async {
    final user = await CommunityService().getCurrentUser();
    if (user != null && mounted) {
      setState(() {
        _currentUserName = user.fullName;
        _currentUserAvatar = user.imageUrl ?? "";
        _currentUserId = user.id.toString();
      });
    }
  }

  Future<void> _refreshAll() async {
    if (_comments.isEmpty) setState(() => _isLoading = true);
    await _loadComments();
    if (mounted) setState(() => _isLoading = false);
    _loadPostDetails(); 
  }

  Future<void> _loadPostDetails() async {
    try {
      final updatedPost = await _service.getPost(widget.post.id);
      if (updatedPost != null && mounted) setState(() => _currentPost = updatedPost);
    } catch (e) { print("Error loading post: $e"); }
  }

  Future<void> _loadComments() async {
    try {
      final comments = await _service.getComments(widget.post.id);
      if (mounted) setState(() => _comments = comments);
    } catch (e) { print("Error loading comments: $e"); }
  }

  Future<void> _sendComment(String content) async {
    HapticFeedback.mediumImpact(); 
    setState(() => _isSending = true);
    
    final tempId = DateTime.now().millisecondsSinceEpoch.toString();
    final tempComment = Comment(
      id: "temp_$tempId",
      postId: widget.post.id,
      authorId: _currentUserId.isNotEmpty ? _currentUserId : "0", 
      authorName: _currentUserName, 
      authorAvatar: _currentUserAvatar, 
      content: content,
      timeAgo: "Hozirgina",
      createdAt: DateTime.now(),
      likes: 0,
      isLiked: false,
      isLikedByAuthor: false,
      authorRole: "Talaba",
      // If we are replying to someone in Main Sheet, we usually just reply to thread or create new thread?
      // For now, let's keep it simple: Replying here targets the Parent (Post).
      // Unless _replyingTo is set (which is only for swipes).
      replyToCommentId: _replyingTo?.id, 
      replyToUserName: _replyingTo?.authorName, 
      replyToContent: _replyingTo?.content, // Fix: Show quoted content immediately
      isMine: true,
    );

    setState(() {
      _comments.add(tempComment);
      _replyingTo = null; // Clear reply context
    });

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent + 100, 
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });

    try {
      final realComment = await _service.createComment(
        widget.post.id, 
        content, 
        replyToId: tempComment.replyToCommentId
      );
      
      if (mounted) {
        setState(() {
          final index = _comments.indexWhere((c) => c.id == "temp_$tempId");
          if (index != -1) _comments[index] = realComment;
          else _comments.add(realComment);
        });
        widget.onCommentCountChanged?.call(_comments.length);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _comments.removeWhere((c) => c.id == "temp_$tempId"));
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Xatolik: $e")));
      }
    } finally {
      if (mounted) setState(() => _isSending = false);
    }
  }

  void _toggleCommentLike(String commentId) async {
    final index = _comments.indexWhere((c) => c.id == commentId);
    if (index == -1) return;

    final oldComment = _comments[index];
    setState(() {
      _comments[index] = oldComment.copyWith(
        isLiked: !oldComment.isLiked,
        likes: !oldComment.isLiked ? oldComment.likes + 1 : oldComment.likes - 1
      );
    });

    final success = await _service.likeComment(commentId);
    if (!success && mounted) setState(() => _comments[index] = oldComment);
  }

  void _deleteComment(String commentId) async {
    final deletedComment = _comments.firstWhere((c) => c.id == commentId);
    setState(() => _comments.removeWhere((c) => c.id == commentId));
    widget.onCommentCountChanged?.call(_comments.length);

    final success = await _service.deleteComment(commentId);
    if (!success && mounted) {
      setState(() => _comments.add(deletedComment)); // Restore
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("O'chirishda xatolik bo'ldi")));
    }
  }

  void _handleEditComment(Comment comment, String newContent) async {
    // Optimistic Update
    final index = _comments.indexWhere((c) => c.id == comment.id);
    if (index == -1) return;

    final oldContent = comment.content;
    setState(() {
      _comments[index] = comment.copyWith(content: newContent);
    });

    final updatedComment = await _service.editComment(comment.id, newContent);
    if (updatedComment == null && mounted) {
       // Revert
       setState(() {
         _comments[index] = comment.copyWith(content: oldContent);
       });
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Tahrirlashda xatolik bo'ldi")));
    } else if (updatedComment != null && mounted) {
       // Update with server response (optional, but good for sync)
       setState(() {
         _comments[index] = updatedComment;
       });
    }
  }

  // --- Nesting Logic Helpers ---
  Map<String, List<Comment>> _getRepliesMap() {
    final Map<String, List<Comment>> map = {};
    
    // Helper to find root ID
    // Since we don't have the full tree structure in memory explicitly linked,
    // we iterate up using replyToCommentId.
    // Optimization: Create a Id -> Comment lookup first.
    final Map<String, Comment> lookup = { for (var c in _comments) c.id : c };

    String? findRootId(String startId) {
      String currentId = startId;
      int depth = 0;
      while (depth < 100) { // Safety break - increased to support deep threads
        final current = lookup[currentId];
        if (current == null) return null; // Parent not found in list (maybe deleted or pagination)
        
        if (current.replyToCommentId == null || current.replyToCommentId == "0" || current.replyToCommentId == "null") {
          return current.id; // Found root
        }
        currentId = current.replyToCommentId!;
        depth++;
      }
      return null;
    }

    for (var c in _comments) {
      if (c.replyToCommentId != null && c.replyToCommentId != "0" && c.replyToCommentId != "null") {
         // This is a reply (either level 1 or level 2+)
         // Find its ultimate root to group under
         final rootId = findRootId(c.id);
         if (rootId != null && rootId != c.id) {
           map.putIfAbsent(rootId, () => []).add(c);
         }
      }
    }
    
    // Sort Oldest -> Newest
    for (var list in map.values) list.sort((a, b) => a.createdAt.compareTo(b.createdAt));
    return map;
  }

  List<Comment> _getRoots() {
    final Map<String, Comment> lookup = { for (var c in _comments) c.id : c };
    return _comments.where((c) {
      final isExplicitRoot = c.replyToCommentId == null || c.replyToCommentId == "0" || c.replyToCommentId == "null";
      if (isExplicitRoot) return true;
      
      // Safety: If parent is missing from the list, treat as root (Orphan)
      // This prevents "invisible comments" bug.
      if (c.replyToCommentId != null && !lookup.containsKey(c.replyToCommentId)) {
        return true;
      }
      return false;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final roots = _getRoots();
    final repliesMap = _getRepliesMap();

    return DraggableScrollableSheet(
      initialChildSize: 0.75,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Header
              Container(
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  border: Border(bottom: BorderSide(color: Colors.grey[200]!))
                ),
                child: Column(
                  children: [
                    Container(
                      width: 40, height: 4,
                      decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      "Sharhlar (${_comments.length})", 
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)
                    ),
                  ],
                ),
              ),

              _buildPostHeader(),
              const Divider(height: 1, thickness: 1),

              // Comments List
              Expanded(
                child: _isLoading && _comments.isEmpty
                  ? const Center(child: CircularProgressIndicator())
                  : RefreshIndicator(
                      onRefresh: _refreshAll,
                      color: AppTheme.primaryBlue,
                      child: _comments.isEmpty
                        ? SingleChildScrollView(child: _buildEmptyState())
                        : ListView.builder(
                            controller: scrollController,
                            itemCount: roots.length,
                            padding: const EdgeInsets.only(bottom: 20),
                            itemBuilder: (context, index) {
                              final root = roots[index];
                              final replies = repliesMap[root.id] ?? [];
                              final isExpanded = _expandedCommentIds.contains(root.id);
                              
                              return Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  CommentItem(
                                    comment: root,
                                    onLike: _toggleCommentLike,
                                    onReply: (c) => setState(() => _replyingTo = c),
                                    onDelete: _deleteComment,
                                    onEdit: _handleEditComment, // Pass Edit Handler
                                  ),
                                  
                                  // Inline "Javoblar (N)" Dropdown Button
                                  if (replies.isNotEmpty)
                                    Padding(
                                      padding: const EdgeInsets.only(left: 60, bottom: 8),
                                      child: GestureDetector(
                                        onTap: () {
                                          HapticFeedback.lightImpact();
                                          setState(() {
                                            if (isExpanded) {
                                              _expandedCommentIds.remove(root.id);
                                            } else {
                                              _expandedCommentIds.add(root.id);
                                            }
                                          });
                                        },
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Text(
                                              "${replies.length} ta javoblar",
                                              style: const TextStyle(
                                                color: AppTheme.primaryBlue, 
                                                fontWeight: FontWeight.bold,
                                                fontSize: 12
                                              ),
                                            ),
                                            const SizedBox(width: 4),
                                            Icon(
                                              isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                                              size: 16,
                                              color: AppTheme.primaryBlue,
                                            )
                                          ],
                                        ),
                                      ),
                                    ),
                                    
                                  // Expanded Replies List
                                  if (isExpanded)
                                    ...replies.map((reply) => CommentItem(
                                      comment: reply,
                                      onLike: _toggleCommentLike,
                                      isReply: true, // Use the visual Reply connector
                                      onReply: (c) => setState(() => _replyingTo = c), 
                                      onDelete: _deleteComment,
                                      onEdit: _handleEditComment, // Pass Edit Handler
                                    )).toList(),
                                ],
                              );
                            },
                          ),
                    ),
              ),

              // 3. Reply Preview logic is now handled INSIDE CommentInput via replyToName param
              // if (_replyingTo != null) _buildReplyPreview(), // REMOVED to avoid duplication

              // 4. Input Area
              CommentInput(
                onSend: _sendComment,
                isSending: _isSending,
                // Logic: Show Username if available, else Author Name (YouTube Style)
                replyToName: _replyingTo != null 
                    ? (_replyingTo!.authorUsername.isNotEmpty 
                        ? "@${_replyingTo!.authorUsername}" // Just "@username"
                        : _replyingTo!.authorName)
                    : null,
                onCancelReply: () => setState(() => _replyingTo = null),
              )
            ],
          ),
        );
      },
    );
  }

  Widget _buildPostHeader() {
    final post = _currentPost ?? widget.post;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        border: Border(bottom: BorderSide(color: Colors.grey[200]!))
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 20,
            backgroundImage: post.authorAvatar.isNotEmpty ? NetworkImage(post.authorAvatar) : null,
            child: post.authorAvatar.isEmpty ? Text(post.authorName[0]) : null,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(post.authorName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        if (post.authorIsPremium) ...[
                          const SizedBox(width: 4),
                          const Icon(Icons.verified, color: Colors.blue, size: 14),
                        ]
                      ],
                    ),
                    if (post.authorUsername.isNotEmpty)
                      Text("@${post.authorUsername}", style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.w500, fontSize: 11)),
                  ],
                ),
                const SizedBox(height: 4),
                Text(post.content, maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13, height: 1.3)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Icon(post.isLiked ? Icons.favorite : Icons.favorite_border, size: 14, color: post.isLiked ? Colors.red : Colors.grey[400]),
                    const SizedBox(width: 4),
                    Text("${post.likes}", style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                    const SizedBox(width: 12),
                    Icon(Icons.remove_red_eye, size: 14, color: Colors.grey[400]),
                    const SizedBox(width: 4),
                    Text("Ko'rildi", style: TextStyle(fontSize: 12, color: Colors.grey[600])), 
                  ],
                )
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
     return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.chat_bubble_outline, size: 48, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text("Hozircha sharhlar yo'q", style: TextStyle(color: Colors.grey[500], fontSize: 14)),
          Text("Birinchi bo'lib fikr bildiring!", style: TextStyle(color: Colors.grey[400], fontSize: 12)),
        ],
      ),
    );
  }
}
