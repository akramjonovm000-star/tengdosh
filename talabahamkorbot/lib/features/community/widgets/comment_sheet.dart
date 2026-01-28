import 'package:flutter/material.dart';
import 'dart:async';
import 'package:flutter/services.dart'; // For Haptics
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';
import '../screens/user_profile_screen.dart';

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
  final TextEditingController _commentController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _inputFocusNode = FocusNode();
  
  List<Comment> _comments = [];
  bool _isLoading = true;
  bool _isSending = false;
  
  // State for Optimistic Updates
  String _currentUserName = "Men"; 
  String _currentUserAvatar = "";
  
  // Variables needed for logic
  Comment? _replyingTo;
  Post? _currentPost;

  @override
  void initState() {
    super.initState();
    _currentPost = widget.post; // Initial state
    _loadCurrentUser(); 
    _refreshAll();
  }

  Future<void> _loadCurrentUser() async {
    final user = await CommunityService().getCurrentUser(); 
    if (user != null && mounted) {
      setState(() {
        _currentUserName = user.fullName;
        _currentUserAvatar = user.imageUrl ?? "";
      });
    }
  }

  Future<void> _refreshAll() async {
    if (_comments.isEmpty) setState(() => _isLoading = true);
    
    // 1. Load Comments FIRST (Priority)
    await _loadComments();
    
    if (mounted) setState(() => _isLoading = false);

    // 2. Load Post Details in Background (don't block UI)
    _loadPostDetails(); 
  }

  Future<void> _loadPostDetails() async {
    try {
      final updatedPost = await _service.getPost(widget.post.id);
      if (updatedPost != null && mounted) {
        setState(() => _currentPost = updatedPost);
      }
    } catch (e) {
      print("Error loading post details: $e");
    }
  }

  Future<void> _loadComments() async {
    try {
      final comments = await _service.getComments(widget.post.id);
      if (mounted) {
        setState(() {
          _comments = comments;
        });
      }
    } catch (e) {
      print("Error loading comments: $e");
    }
  }

  Future<void> _sendComment() async {
    final content = _commentController.text.trim();
    if (content.isEmpty) return;

    HapticFeedback.mediumImpact(); 

    setState(() => _isSending = true);
    
    // OPTIMISTIC UPDATE
    final tempId = DateTime.now().millisecondsSinceEpoch.toString();
    final tempComment = Comment(
      id: "temp_$tempId",
      postId: widget.post.id,
      authorName: _currentUserName, 
      authorAvatar: _currentUserAvatar, 
      content: content,
      timeAgo: "Hozirgina",
      createdAt: DateTime.now(),
      likes: 0,
      isLiked: false,
      isLikedByAuthor: false,
      authorRole: "Talaba",
      replyToUserName: _replyingTo?.authorName,
      replyToContent: _replyingTo?.content,
      isMine: true, 
    );

    setState(() {
      _comments.add(tempComment);
      _commentController.clear();
    });

    // Scroll slightly to show new comment
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
           // If we are at bottom, scroll more. If list is reversed, scroll to top. 
           // Standard ListView: scroll to bottom.
          _scrollController.position.maxScrollExtent + 150, 
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });

    final replyId = _replyingTo?.id;
    setState(() => _replyingTo = null); // Clear reply state
    _inputFocusNode.unfocus(); // Close keyboard or keep it? user might want to write more. keep it.

    try {
      final realComment = await _service.createComment(widget.post.id, content, replyToId: replyId);
      
      if (mounted) {
        setState(() {
          final index = _comments.indexWhere((c) => c.id == "temp_$tempId");
          if (index != -1) {
            _comments[index] = realComment;
          } else {
             _comments.add(realComment);
          }
        });
        widget.onCommentCountChanged?.call(_comments.length);
      }
      
    } catch (e) {
      if (mounted) {
        setState(() {
          _comments.removeWhere((c) => c.id == "temp_$tempId");
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Xatolik: $e")),
        );
      }
    } finally {
      if (mounted) setState(() => _isSending = false);
    }
  }

  void _toggleCommentLike(String commentId) async {
    final index = _comments.indexWhere((c) => c.id == commentId);
    if (index == -1) return;

    final oldComment = _comments[index];
    final bool newLiked = !oldComment.isLiked;
    final int newCount = newLiked ? oldComment.likes + 1 : oldComment.likes - 1;

    setState(() {
      _comments[index] = oldComment.copyWith(
        isLiked: newLiked,
        likes: newCount
      );
    });

    final success = await _service.likeComment(commentId);
    
    if (!success && mounted) {
      setState(() {
        _comments[index] = oldComment; // Rollback
      });
    }
  }

  void _deleteComment(String commentId) {
      // Implement delete logic via service
      // Optimistic remove
      final index = _comments.indexWhere((c) => c.id == commentId);
      if (index == -1) return;
      
      final deleted = _comments[index];
      setState(() {
          _comments.removeAt(index);
      });
      
      // Call Service
      // _service.deleteComment(commentId).catchError(...)
  }

  @override
  Widget build(BuildContext context) {
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
                    Text("Sharhlar (${_comments.length})", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
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
                            itemCount: _comments.length,
                            padding: const EdgeInsets.only(bottom: 20),
                            itemBuilder: (context, index) => _buildCommentItem(_comments[index]),
                          ),
                    ),
              ),

              if (_replyingTo != null) _buildReplyPreview(),

              _buildInputArea(),
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
      decoration: BoxDecoration(color: const Color(0xFFF9FAFB), border: Border(bottom: BorderSide(color: Colors.grey[200]!))),
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
                Text(post.authorName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 4),
                Text(post.content, maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13, height: 1.3)),
                 const SizedBox(height: 8),
                Row(
                  children: [
                    Icon(post.isLiked ? Icons.favorite : Icons.favorite_border, size: 14, color: post.isLiked ? Colors.red : Colors.grey[400]),
                    const SizedBox(width: 4),
                    Text("${post.likes}", style: TextStyle(fontSize: 12, color: Colors.grey[600])),
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
      child: Padding(
        padding: const EdgeInsets.all(40.0),
        child: Column(
          children: [
            Icon(Icons.chat_bubble_outline, size: 48, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text("Hozircha sharhlar yo'q", style: TextStyle(color: Colors.grey[500], fontSize: 14)),
          ],
        ),
      ),
    );
  }

  Widget _buildReplyPreview() {
    return Container(
      color: const Color(0xFFF5F7FA),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          const Icon(Icons.reply, size: 20, color: AppTheme.primaryBlue),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "Javob: ${_replyingTo!.authorName}",
                  style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue, fontSize: 12),
                ),
                Text(
                  _replyingTo!.content,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(color: Colors.grey[600], fontSize: 11),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, size: 18),
            onPressed: () => setState(() => _replyingTo = null),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          )
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: EdgeInsets.only(
        left: 16, right: 16, top: 8, 
        bottom: MediaQuery.of(context).viewInsets.bottom + 16
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey[200]!)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, -2))]
      ),
      child: Row(
        children: [
           CircleAvatar(backgroundColor: Colors.grey[200], radius: 18, child: const Icon(Icons.person, color: Colors.grey, size: 20)),
           const SizedBox(width: 12),
           Expanded(
             child: Container(
               padding: const EdgeInsets.symmetric(horizontal: 16),
               decoration: BoxDecoration(color: const Color(0xFFF5F5F5), borderRadius: BorderRadius.circular(24)),
               child: TextField(
                 controller: _commentController,
                 focusNode: _inputFocusNode,
                 decoration: const InputDecoration(
                   hintText: "Fikringizni yozing...",
                   border: InputBorder.none,
                   contentPadding: EdgeInsets.symmetric(vertical: 10),
                   isDense: true,
                 ),
                 minLines: 1, maxLines: 4,
               ),
             ),
           ),
           const SizedBox(width: 8),
           IconButton(
             onPressed: _isSending ? null : _sendComment,
             icon: _isSending 
               ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
               : const CircleAvatar(backgroundColor: AppTheme.primaryBlue, radius: 20, child: Icon(Icons.send_rounded, color: Colors.white, size: 18)),
           )
        ],
      ),
    );
  }

  String _getShortName(String fullName) {
    final parts = fullName.trim().replaceAll(RegExp(r'\s+'), ' ').split(' ');
    // Logic: Return Last Name (First Word) or First Name (Second Word)? 
    // Usually Uzbek names: SURNAME NAME. So Name is parts[1].
    if (parts.length >= 2) return parts[1];
    return parts.isNotEmpty ? parts[0] : "Talaba";
  }

  Widget _buildCommentItem(Comment comment) {
    // -------------------------------------------------------------
    // ADVANCED UI LOGIC: Indentation & Visual Threading
    // -------------------------------------------------------------
    final bool isReply = comment.replyToUserName != null;
    final double indent = isReply ? 32.0 : 0.0;
    
    final content = _buildCommentContent(comment);

    if (comment.isMine) {
      return Dismissible(
        key: Key(comment.id),
        direction: DismissDirection.startToEnd,
        background: Container(
          color: Colors.red[50],
          margin: EdgeInsets.only(left: indent),
          alignment: Alignment.centerLeft,
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: const Icon(Icons.delete_outline, color: Colors.red),
        ),
        onDismissed: (direction) => _deleteComment(comment.id),
        child: Padding(padding: EdgeInsets.only(left: indent), child: content),
      );
    } else {
      return Padding(padding: EdgeInsets.only(left: indent), child: content);
    }
  }

  Widget _buildCommentContent(Comment comment) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white, // Maybe slightly grey if reply? 
        border: Border(bottom: BorderSide(color: Colors.grey[100]!))
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Avatar
          GestureDetector(
            onTap: () {
               // Open Profile
               Navigator.push(context, MaterialPageRoute(builder: (_) => UserProfileScreen(
                  authorName: comment.authorName,
                  authorUsername: "@student", // TODO: Add username to Comment model
                  authorAvatar: comment.authorAvatar,
                  authorRole: comment.authorRole,
               )));
            },
            child: CircleAvatar(
              backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
              backgroundImage: comment.authorAvatar.isNotEmpty ? NetworkImage(comment.authorAvatar) : null,
              radius: comment.replyToUserName != null ? 14 : 18, // Smaller avatar for replies
              child: comment.authorAvatar.isEmpty 
                ? Text(comment.authorName.isNotEmpty ? comment.authorName[0] : "?", style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue, fontSize: comment.replyToUserName != null ? 10 : 14))
                : null,
            ),
          ),
          const SizedBox(width: 12),
          
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. Author Name
                Row(
                  children: [
                    Text(
                      _getShortName(comment.authorName),
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    if (comment.isLikedByAuthor)
                       Padding(
                         padding: const EdgeInsets.only(left: 4),
                         child: Icon(Icons.check_circle, size: 12, color: Colors.blue), // Author verification or like badge?
                       )
                  ],
                ),
                
                // 2. Reply Context Header (The "↪ @username" part)
                if (comment.replyToUserName != null)
                   Padding(
                     padding: const EdgeInsets.only(top: 2, bottom: 2),
                     child: Text(
                       "↪ ${comment.replyToUserName}", 
                       style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppTheme.primaryBlue)
                     ),
                   ),

                // 3. Content
                const SizedBox(height: 2),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start, // Align top
                  children: [
                    Expanded(
                      child: Text(
                        comment.content, 
                        style: const TextStyle(fontSize: 13, height: 1.3, color: Colors.black87)
                      ),
                    ),
                    // Like Button (Right aligned next to text)
                     GestureDetector(
                      onTap: () => _toggleCommentLike(comment.id),
                      behavior: HitTestBehavior.opaque,
                      child: Padding(
                        padding: const EdgeInsets.only(left: 8),
                        child: Column(
                          children: [
                             Icon(
                              comment.isLiked ? Icons.favorite : Icons.favorite_border,
                              size: 16,
                              color: comment.isLiked ? Colors.red : Colors.grey[400],
                            ),
                            if (comment.likes > 0)
                               Text("${comment.likes}", style: TextStyle(fontSize: 10, color: Colors.grey[600])),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 6),

                // 4. Action Row (Time, Reply)
                Row(
                  children: [
                    Text(comment.timeAgo, style: TextStyle(color: Colors.grey[500], fontSize: 11)),
                    const SizedBox(width: 16),
                    GestureDetector(
                      onTap: () {
                        HapticFeedback.lightImpact();
                        setState(() {
                          _replyingTo = comment;
                        });
                        // Focus input
                        _inputFocusNode.requestFocus();
                      },
                      child: Text(
                        "Javob berish", 
                        style: TextStyle(color: Colors.grey[600], fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          )
        ],
      ),
    );
  }
}
