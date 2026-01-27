
import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';
import '../widgets/post_card.dart';
import '../../../../core/utils/role_mapper.dart'; // Import RoleMapper
import 'dart:async';

class PostDetailScreen extends StatefulWidget {
  final Post post;

  const PostDetailScreen({super.key, required this.post});

  @override
  State<PostDetailScreen> createState() => _PostDetailScreenState();
}

class _PostDetailScreenState extends State<PostDetailScreen> {
  final CommunityService _service = CommunityService();
  final TextEditingController _commentController = TextEditingController();
  List<Comment> _comments = [];
  bool _isLoading = true;
  bool _isSending = false;
  late Post _post;
  Timer? _pollingTimer;

  @override
  void initState() {
    super.initState();
    _post = widget.post;
    _refreshPost(); // Fetch fresh data immediately
    _loadComments();
    _startPolling();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }

  void _startPolling() {
    _pollingTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      _refreshPost();
    });
  }

  Future<void> _refreshPost() async {
    final updatedPost = await _service.getPost(_post.id);
    if (updatedPost != null && mounted) {
      setState(() {
        _post = updatedPost;
      });
    }
  }

  Future<void> _loadComments({bool quiet = false}) async {
    if (!quiet) {
       if (mounted) setState(() => _isLoading = true);
    }
    try {
      final comments = await _service.getComments(widget.post.id);
      if (mounted) {
        setState(() {
          _comments = comments;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted && !quiet) setState(() => _isLoading = false);
    }
  }

  Future<void> _sendComment() async {
    final content = _commentController.text.trim();
    if (content.isEmpty) return;

    setState(() => _isSending = true);
    try {
      final newComment = await _service.createComment(widget.post.id, content);
      
      _commentController.clear();
      FocusScope.of(context).unfocus();
      
      // 1. Optimistic Update: Show immediately at bottom
      setState(() {
        _comments.add(newComment);
      });

      // 2. Silent Background Sync -- REMOVED to prevent race condition (stale read overwriting local).
      // _loadComments(quiet: true);  
      
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Xatolik: $e")),
      );
    } finally {
      if (mounted) setState(() => _isSending = false);
    }
  }

  Widget _buildCommentItem(Comment comment) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey[100]!)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: Colors.blue[100],
                backgroundImage: comment.authorAvatar.isNotEmpty 
                  ? NetworkImage(comment.authorAvatar) 
                  : null,
                child: comment.authorAvatar.isEmpty 
                  ? Text(comment.authorName.isNotEmpty ? comment.authorName[0].toUpperCase() : "?", 
                      style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold))
                  : null,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text(
                                    comment.authorName,
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                  ),
                                  if (comment.authorIsPremium) ...[
                                    const SizedBox(width: 4),
                                    const Icon(Icons.verified, color: Colors.blue, size: 14),
                                  ]
                                ],
                              ),
                              if (comment.authorUsername.isNotEmpty)
                                Text(
                                  "@${comment.authorUsername}",
                                  style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.w500, fontSize: 12),
                                ),
                            ],
                          ),
                        ),
                        // Like Button for Comment
                         GestureDetector(
                           onTap: () async {
                              // Optimistic Like
                              final oldState = comment.isLiked;
                              final oldCount = comment.likes;
                              
                              setState(() {
                                final index = _comments.indexOf(comment);
                                if (index != -1) {
                                  _comments[index] = comment.copyWith(
                                    isLiked: !oldState,
                                    likes: oldState ? oldCount - 1 : oldCount + 1
                                  );
                                }
                              });
                              
                              final success = await _service.likeComment(comment.id);
                              if (!success) {
                                // Revert on failure
                                setState(() {
                                  final index = _comments.indexOf(comment);
                                  if (index != -1) {
                                     _comments[index] = comment.copyWith(isLiked: oldState, likes: oldCount);
                                  }
                                });
                              }
                           },
                           child: Row(
                             children: [
                               Icon(
                                 comment.isLiked ? Icons.favorite : Icons.favorite_border,
                                 size: 16,
                                 color: comment.isLiked ? Colors.red : Colors.grey,
                               ),
                               if (comment.likes > 0)
                                 Padding(
                                   padding: const EdgeInsets.only(left: 4),
                                   child: Text("${comment.likes}", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                                 )
                             ],
                           ),
                         )
                      ],
                    ),
                    const SizedBox(height: 2),
                    if (comment.content.startsWith("🚫"))
                        Text(comment.content, style: TextStyle(color: Colors.grey[500], fontStyle: FontStyle.italic))
                    else
                        Text(comment.content, style: const TextStyle(fontSize: 14)),
                    
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Text(
                          comment.timeAgo,
                          style: TextStyle(color: Colors.grey[500], fontSize: 12),
                        ),
                        const SizedBox(width: 16),
                        GestureDetector(
                          onTap: () {
                             // Reply logic (simplified: populate input)
                             _commentController.text = ""; // TODO: Implement @mention logic if needed
                             FocusScope.of(context).requestFocus();
                          },
                          child: Text(
                            "Javob berish", 
                            style: TextStyle(color: Colors.grey[600], fontSize: 12, fontWeight: FontWeight.w500)
                          ),
                        )
                      ],
                    )
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false, // We handle pop manually
      onPopInvoked: (didPop) {
        if (didPop) return;
        Navigator.pop(context, _post);
      },
      child: Scaffold(
        backgroundColor: Colors.white,
        appBar: AppBar(
          backgroundColor: Colors.white,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.black),
            onPressed: () => Navigator.pop(context, _post), 
          ),
          title: const Text("Muhokama", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        ),
        body: Column(
          children: [
            Expanded(
              child: RefreshIndicator(
                onRefresh: _loadComments,
                child: ListView(
                  padding: const EdgeInsets.only(bottom: 20),
                  children: [
                    // Main Post
                    PostCard(
                      post: _post, 
                      isDetail: true,
                      onDelete: () {
                        Navigator.pop(context, 'deleted');
                      },
                      onLikeChanged: (isLiked, count) {
                         setState(() {
                           _post = _post.copyWith(isLiked: isLiked, likes: count);
                         });
                      },
                    onRepostChanged: (isReposted, count) {
                       setState(() {
                         _post = _post.copyWith(isRepostedByMe: isReposted, repostsCount: count);
                       });
                    },
                  ),  
                    
                    const Divider(thickness: 1, height: 1),
                    
                    Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Text(
                        "Muhokamalar", 
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.grey[800])
                      ),
                    ),
  
                    // Comments List
                     if (_isLoading)
                        const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator()))
                     else if (_comments.isEmpty)
                        Center(
                          child: Padding(
                            padding: const EdgeInsets.all(32.0),
                            child: Text("Hozircha sharhlar yo'q", style: TextStyle(color: Colors.grey[500])),
                          ),
                        )
                     else
                        ..._comments.map((comment) => _buildCommentItem(comment)),
                  ],
                ),
              ),
            ),
  
            // Input Area
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border(top: BorderSide(color: Colors.grey[200]!)),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, -2))
                ]
              ),
              child: SafeArea( // For iPhone bottom bar
                child: Row(
                  children: [
                     // User Avatar (Placeholder)
                     CircleAvatar(
                       backgroundColor: Colors.grey[200],
                       radius: 18,
                       child: const Icon(Icons.person, color: Colors.grey, size: 20),
                     ),
                     const SizedBox(width: 12),
                     
                     // Input Field
                     Expanded(
                       child: Container(
                         padding: const EdgeInsets.symmetric(horizontal: 16),
                         decoration: BoxDecoration(
                           color: Colors.grey[100],
                           borderRadius: BorderRadius.circular(24),
                         ),
                         child: TextField(
                           controller: _commentController,
                           decoration: InputDecoration(
                             hintText: "Fikringizni yozing...",
                             border: InputBorder.none,
                             contentPadding: const EdgeInsets.symmetric(vertical: 10),
                           ),
                           minLines: 1,
                           maxLines: 4,
                         ),
                       ),
                     ),
                     const SizedBox(width: 8),
                     CircleAvatar(
                        backgroundColor: AppTheme.primaryBlue,
                        child: IconButton(
                          icon: _isSending 
                              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                              : const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                          onPressed: _isSending ? null : _sendComment,
                        ),
                      )
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
