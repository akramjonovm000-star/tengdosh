import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';
import 'comment_item.dart';
import 'comment_input.dart';
import 'package:flutter/services.dart';

class ReplyThreadSheet extends StatefulWidget {
  final Comment parentComment;
  final List<Comment> initialReplies;
  final Function(int count)? onReplyCountChanged;

  const ReplyThreadSheet({
    super.key, 
    required this.parentComment,
    required this.initialReplies,
    this.onReplyCountChanged,
  });

  @override
  State<ReplyThreadSheet> createState() => _ReplyThreadSheetState();
}

class _ReplyThreadSheetState extends State<ReplyThreadSheet> {
  late List<Comment> _replies;
  final CommunityService _service = CommunityService();
  bool _isSending = false;
  Comment? _replyingTo; // If replying to specific sub-reply (mentions)
  final FocusNode _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _replies = List.from(widget.initialReplies);
  }

  Future<void> _sendReply(String content) async {
    setState(() => _isSending = true);
    HapticFeedback.mediumImpact();

    // Optimistic Update
    final user = await _service.getCurrentUser();
    final tempId = DateTime.now().millisecondsSinceEpoch.toString();
    
    final tempComment = Comment(
      id: "temp_$tempId",
      postId: widget.parentComment.postId,
      authorId: user?.id.toString() ?? "0",
      authorName: user?.fullName ?? "Men",
      authorAvatar: user?.imageUrl ?? "",
      authorUsername: user?.username ?? "",
      content: content,
      timeAgo: "Hozirgina",
      createdAt: DateTime.now(),
      likes: 0,
      isLiked: false,
      isLikedByAuthor: false,
      isMine: true,
      // CRITICAL: Linking to correct parent
      // If we are in a thread, we reply to the PARENT COMMENT ID usually, 
      // but if we are replying to a specific sub-comment, we might want to tag them?
      // Backend expects 'reply_to_comment_id'.
      // If we reply to thread parent -> reply_to_comment_id = widget.parentComment.id
      // If we reply to a sub-reply -> reply_to_comment_id = _replyingTo.id ?? widget.parentComment.id
      replyToCommentId: _replyingTo?.id ?? widget.parentComment.id, 
      replyToUserName: _replyingTo?.authorName ?? widget.parentComment.authorName, // For UI context
    );

    setState(() {
      _replies.add(tempComment);
      _replyingTo = null; // Clear target
    });

    try {
      final realComment = await _service.createComment(
        widget.parentComment.postId, 
        content, 
        replyToId: tempComment.replyToCommentId
      );

      if (mounted) {
        setState(() {
          final idx = _replies.indexWhere((c) => c.id == "temp_$tempId");
          if (idx != -1) _replies[idx] = realComment;
        });
        widget.onReplyCountChanged?.call(_replies.length);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _replies.removeWhere((c) => c.id == "temp_$tempId"));
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Xatolik: $e")));
      }
    } finally {
      if (mounted) setState(() => _isSending = false);
    }
  }

  void _handleLike(String commentId) async {
    // Basic like toggling for UI
    final index = _replies.indexWhere((c) => c.id == commentId);
    if (index != -1) {
       final old = _replies[index];
       setState(() {
         _replies[index] = old.copyWith(
           isLiked: !old.isLiked,
           likes: !old.isLiked ? old.likes + 1 : old.likes - 1
         );
       });
       await _service.likeComment(commentId);
    } else if (widget.parentComment.id == commentId) {
      // Like parent? Use callback or handle here?
      // Just ignore for now or handle optimistic
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.95,
      minChildSize: 0.5,
      maxChildSize: 1.0,
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
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  border: Border(bottom: BorderSide(color: Colors.grey[200]!))
                ),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.arrow_back),
                      onPressed: () => Navigator.pop(context, _replies), // Return updated list
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                    const SizedBox(width: 16),
                    const Text(
                      "Javoblar", 
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)
                    ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(context, _replies),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
              ),

              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: EdgeInsets.zero,
                  children: [
                    // Parent Comment
                    Container(
                      color: Colors.grey[50], // Distinction
                      child: CommentItem(
                        comment: widget.parentComment,
                        onLike: (id) {}, // Can't like parent from here efficiently without syncing back, ignore or implement later
                        isParent: true,
                        onReply: (c) {
                          _focusNode.requestFocus();
                        },
                      ),
                    ),
                    const Divider(height: 1),
                    
                    // Replies
                    ..._replies.map((reply) => CommentItem(
                      comment: reply,
                      onLike: _handleLike,
                      isReply: true, // This triggers visual indentation and small avatar
                      onReply: (target) {
                        setState(() => _replyingTo = target);
                        _focusNode.requestFocus();
                      },
                      onDelete: (id) async {
                         setState(() => _replies.removeWhere((c) => c.id == id));
                         await _service.deleteComment(id);
                      },
                    )).toList(),
                    
                    if (_replies.isEmpty)
                      const Padding(
                        padding: EdgeInsets.all(32.0),
                        child: Center(child: Text("Hozircha javoblar yo'q", style: TextStyle(color: Colors.grey))),
                      )
                  ],
                ),
              ),

              CommentInput(
                onSend: _sendReply,
                isSending: _isSending,
                // Logic: Show Username if available, else Author Name (YouTube Style)
                replyToName: _replyingTo != null 
                    ? (_replyingTo!.authorUsername.isNotEmpty 
                        ? "@${_replyingTo!.authorUsername}" 
                        : _replyingTo!.authorName)
                    : null,
                onCancelReply: () => setState(() => _replyingTo = null),
                focusNode: _focusNode,
              )
            ],
          ),
        );
      },
    );
  }
}
