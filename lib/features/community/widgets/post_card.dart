
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/role_mapper.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';
import '../screens/user_profile_screen.dart'; 
import 'package:cached_network_image/cached_network_image.dart';
import 'edit_post_sheet.dart';
import 'comment_sheet.dart';

class PostCard extends StatefulWidget {
  final Post post;
  final bool isDetail;
  final Function(bool isLiked, int count)? onLikeChanged;
  final Function(bool isReposted, int count)? onRepostChanged;
  final Function(String newContent)? onContentChanged; // NEW
  final VoidCallback? onDelete; 

  const PostCard({
    super.key, 
    required this.post, 
    this.isDetail = false,
    this.onLikeChanged,
    this.onRepostChanged,
    this.onContentChanged,
    this.onDelete,
  });

  @override
  State<PostCard> createState() => _PostCardState();
}

class _PostCardState extends State<PostCard> {
  bool _isLiked = false;
  int _likeCount = 0;
  int _repostCount = 0;
  bool _isReposted = false;
  bool _isVoting = false;
  
  List<int>? _pollVotes;
  int? _userVote; 
  bool _isExpanded = false;
  
  late int _commentCount;
  late String _currentContent;

  @override
  void initState() {
    super.initState();
    _initializeState();
  }

  @override
  void didUpdateWidget(PostCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.post.id != widget.post.id || oldWidget.post != widget.post) {
      _initializeState();
    }
  }

  void _initializeState() {
     _isLiked = widget.post.isLiked;
     _likeCount = widget.post.likes;
     _commentCount = widget.post.commentsCount;
     _repostCount = widget.post.repostsCount;
     _isReposted = widget.post.isRepostedByMe; 
     _pollVotes = widget.post.pollVotes;
     _userVote = widget.post.userVote;
     _currentContent = widget.post.content; 
  }

  void _toggleLike() async {
    setState(() {
      _isLiked = !_isLiked;
      _likeCount += _isLiked ? 1 : -1;
    });

    widget.onLikeChanged?.call(_isLiked, _likeCount); 

    final result = await CommunityService().likePost(widget.post.id);
    if (result == null && mounted) {
       setState(() {
          _isLiked = !_isLiked;
          _likeCount += _isLiked ? 1 : -1;
       });
       widget.onLikeChanged?.call(_isLiked, _likeCount);
    }
  }

  void _toggleRepost() async {
    setState(() {
      _isReposted = !_isReposted;
      _repostCount += _isReposted ? 1 : -1;
    });

    widget.onRepostChanged?.call(_isReposted, _repostCount); 

    final result = await CommunityService().repostPost(widget.post.id);

    if (result == null && mounted) {
       setState(() {
         _isReposted = !_isReposted;
         _repostCount += _isReposted ? 1 : -1;
       });
       widget.onRepostChanged?.call(_isReposted, _repostCount);
    }
  }

  void _votePoll(int optionIndex) async {
    if (_userVote != null || _isVoting) return;

    setState(() => _isVoting = true);

    final success = await CommunityService().votePoll(widget.post.id, optionIndex);
    
    if (success && mounted) {
       setState(() {
         _userVote = optionIndex;
         _pollVotes![optionIndex]++;
         _isVoting = false;
       });
    } else {
      if (mounted) setState(() => _isVoting = false);
    }
  }

  void _showEditDialog() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20))
      ),
      builder: (context) => EditPostSheet(
        postId: widget.post.id, 
        initialContent: _currentContent, 
      )
    ).then((updatedContent) async {
       if (updatedContent != null && updatedContent is String) {
           setState(() => _currentContent = updatedContent); // Optimistic Update
           
           final success = await CommunityService().editPost(widget.post.id, updatedContent);
           if (!success && mounted) {
              // Revert on failure
              setState(() => _currentContent = widget.post.content); 
              // Removed toast as requested
           } else if (success && widget.onContentChanged != null) {
              widget.onContentChanged!(updatedContent);
           } 
       }
    });
  }

  void _showDeleteDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("O'chirish"),
        content: const Text("Haqiqatan ham bu postni o'chirmoqchimisiz?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Yo'q")),
          TextButton(
            child: const Text("Ha, o'chirish", style: TextStyle(color: Colors.red)),
            onPressed: () async {
              Navigator.pop(ctx);
              final success = await CommunityService().deletePost(widget.post.id);
              if (success && widget.onDelete != null) {
                 widget.onDelete!();
              }
            },
          )
        ],
      )
    );
  }

  void _showShareOptions() {
    final link = "https://talabahamkor.uz/posts/${widget.post.id}";
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20))
      ),
      builder: (context) { // Opening builder
        return Container(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40, height: 4,
                margin: const EdgeInsets.only(bottom: 20),
                decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)),
              ),
              const Text("Ulashish", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 20),
              
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: Colors.grey[100], shape: BoxShape.circle),
                  child: const Icon(Icons.copy, color: Colors.blueAccent),
                ),
                title: const Text("Linkdan nusxa olish", style: TextStyle(fontWeight: FontWeight.w500)),
                onTap: () async {
                  await Clipboard.setData(ClipboardData(text: link));
                  if (mounted) {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text("Link buferga nusxalandi!", style: TextStyle(color: Colors.white)), 
                        backgroundColor: Colors.black87, 
                        behavior: SnackBarBehavior.floating,
                        duration: Duration(seconds: 1)
                      )
                    );
                  }
                },
              ),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: Colors.grey[100], shape: BoxShape.circle),
                  child: const Icon(Icons.share, color: Colors.green),
                ),
                title: const Text("Boshqa ilovalar orqali...", style: TextStyle(fontWeight: FontWeight.w500)),
                subtitle: const Text("Telegram, Instagram, SMS va boshqalar"),
                onTap: () {
                   Navigator.pop(context);
                   Share.share("Talaba Hamkor ilovasidagi qiziqarli postni ko'ring:\n\n$link");
                },
              ),
              const SizedBox(height: 20),
            ],
          ),
        );
      } // Closing builder
    ); // Closing showModalBottomSheet
  }

  Color _getCategoryColor(String type) {
    switch (type) {
      case 'university': return Colors.blue;
      case 'faculty': return Colors.orange;
      case 'specialty': return Colors.purple; 
      default: return Colors.blue;
    }
  }

  String _getCategoryLabel(String type) {
    switch (type) {
      case 'university': return "Universitet";
      case 'faculty': return "Fakultet";
      case 'specialty': return "Yo'nalish";
      default: return "Umumiy";
    }
  }

  @override
  Widget build(BuildContext context) {
    return _buildCardContent();
  }

  Widget _buildCardContent() {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            InkWell(
              onTap: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => UserProfileScreen(
                  authorName: widget.post.authorName,
                  authorId: widget.post.authorId,
                  authorUsername: widget.post.authorUsername,
                  authorAvatar: widget.post.authorAvatar,
                  authorRole: widget.post.authorRole,
                  authorIsPremium: widget.post.authorIsPremium, // NEW
                  authorCustomBadge: widget.post.authorCustomBadge, // NEW
                )));
              },
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 20,
                    backgroundColor: Colors.grey[200],
                    child: widget.post.authorAvatar.isNotEmpty
                        ? ClipOval(
                            child: CachedNetworkImage(
                              imageUrl: widget.post.authorAvatar,
                              width: 40,
                              height: 40,
                              fit: BoxFit.cover,
                              placeholder: (context, url) => const Icon(Icons.person, color: Colors.grey),
                              errorWidget: (context, url, error) => Text(widget.post.authorName.isNotEmpty ? widget.post.authorName[0] : "?", style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue)),
                            ),
                          )
                        : Text(widget.post.authorName.isNotEmpty ? widget.post.authorName[0] : "?", style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue)),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              widget.post.authorName,
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                            ),
                            if (widget.post.authorIsPremium) ...[
                              const SizedBox(width: 4),
                              widget.post.authorCustomBadge != null 
                                  ? Text(widget.post.authorCustomBadge!, style: const TextStyle(fontSize: 16))
                                  : const Icon(Icons.verified, color: Colors.blue, size: 16),
                            ]
                          ],
                        ),
                        const SizedBox(height: 2),
                        Wrap(
                          spacing: 6,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                             Text(
                              "@${widget.post.authorUsername}",
                              style: TextStyle(color: Colors.grey[600], fontSize: 13),
                            ),
                             const Text("•", style: TextStyle(color: Colors.grey, fontSize: 10)),
                            Text(
                              RoleMapper.getLabel(widget.post.authorRole),
                              style: TextStyle(color: Colors.grey[600], fontSize: 13),
                            ),
                             const Text("•", style: TextStyle(color: Colors.grey, fontSize: 10)),
                          Container(
                           padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                           decoration: BoxDecoration(
                             color: _getCategoryColor(widget.post.scope ?? 'university').withOpacity(0.1),
                             borderRadius: BorderRadius.circular(4),
                             border: Border.all(color: _getCategoryColor(widget.post.scope ?? 'university').withOpacity(0.3), width: 0.5)
                           ),
                           child: Text(
                             _getCategoryLabel(widget.post.scope ?? 'university'),
                             style: TextStyle(color: _getCategoryColor(widget.post.scope ?? 'university'), fontSize: 10, fontWeight: FontWeight.bold),
                           ),
                         ),
                        Text(
                          "• ${widget.post.timeAgo}",
                          style: TextStyle(color: Colors.grey[400], fontSize: 13),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (widget.post.isMine || context.read<AuthProvider>().isManagement)
                PopupMenuButton<String>(
                  icon: const Icon(Icons.more_vert, color: Colors.grey), 
                  onSelected: (val) {
                    if (val == 'edit') _showEditDialog();
                    if (val == 'delete') _showDeleteDialog();
                  },
                  itemBuilder: (context) => [
                    const PopupMenuItem(value: 'edit', child: Row(children: [Icon(Icons.edit, size: 20), SizedBox(width: 8), Text("Tahrirlash")])),
                    const PopupMenuItem(value: 'delete', child: Row(children: [Icon(Icons.delete, color: Colors.red, size: 20), SizedBox(width: 8), Text("O'chirish", style: TextStyle(color: Colors.red))])),
                  ],
                )
             ],
            ),
          ),
          
          const SizedBox(height: 12),
          
          _buildFoldableContent(),
          
          const SizedBox(height: 12),

          if (widget.post.pollOptions != null && widget.post.pollOptions!.isNotEmpty)
            _buildPoll(),

          if (widget.post.mediaUrls.isNotEmpty)
             _buildMediaGrid(), 

          const SizedBox(height: 12),
          
          // Actions Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
               _buildActionButton(
                 icon: Icons.chat_bubble_outline, 
                 label: "$_commentCount",
                 onTap: () {
                   showModalBottomSheet(
                     context: context,
                     isScrollControlled: true, 
                     backgroundColor: Colors.transparent,
                     builder: (context) => CommentSheet(
                       post: widget.post,
                       onCommentCountChanged: (newCount) {
                         setState(() => _commentCount = newCount);
                       },
                     )
                   );
                 } 
               ),
               _buildActionButton(
                 icon: _isReposted ? Icons.repeat : Icons.repeat, 
                 label: "$_repostCount", 
                 color: _isReposted ? Colors.green : null,
                 onTap: _toggleRepost
               ),
               _buildActionButton(
                 icon: _isLiked ? Icons.favorite : Icons.favorite_border, 
                 label: "$_likeCount", 
                 color: _isLiked ? Colors.red : null,
                 onTap: _toggleLike
               ),
               IconButton(
                 icon: const Icon(Icons.share_outlined, color: Colors.grey, size: 20),
                 onPressed: _showShareOptions, 
               )
            ],
          )
        ],
      ),
      ),
    );
  }

  Widget _buildActionButton({required IconData icon, required String label, Color? color, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Row(
          children: [
            Icon(icon, size: 20, color: color ?? Colors.grey[600]),
            const SizedBox(width: 4),
            if (label != "0")
              Text(label, style: TextStyle(color: color ?? Colors.grey[600], fontSize: 13)),
          ],
        ),
      ),
    );
  }

  Widget _buildMediaGrid() {
    return SizedBox(
      height: 200, 
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: widget.post.mediaUrls.length,
        itemBuilder: (ctx, index) {
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: CachedNetworkImage(
                imageUrl: widget.post.mediaUrls[index],
                fit: BoxFit.cover,
                placeholder: (context, url) => Container(color: Colors.grey[100], child: const Center(child: CircularProgressIndicator(strokeWidth: 2))),
                errorWidget: (context, url, error) => const Icon(Icons.error),
              ),
            ),
          );
        }
      ),
    );
  }
  
  Widget _buildPoll() {
     if (widget.post.pollOptions == null) return const SizedBox.shrink();
     
     int totalVotes = 0;
     if (_pollVotes != null) {
       totalVotes = _pollVotes!.fold(0, (p, c) => p + c);
     }
     if (totalVotes == 0) totalVotes = 1; 

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50], 
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!)
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: List.generate(widget.post.pollOptions!.length, (index) {
          final option = widget.post.pollOptions![index];
          final votes = _pollVotes![index];
          final percent = votes / totalVotes;
          final isSelected = _userVote == index;
          final showResults = _userVote != null;

          return Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: InkWell(
              onTap: () => _votePoll(index),
              borderRadius: BorderRadius.circular(8),
              child: Stack(
                children: [
                  if (showResults)
                    Container(
                      height: 36,
                      width: MediaQuery.of(context).size.width * percent * 0.7, 
                      decoration: BoxDecoration(
                         color: isSelected ? AppTheme.primaryBlue.withOpacity(0.2) : Colors.grey[200],
                         borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                  
                  Container(
                    height: 36,
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: isSelected ? AppTheme.primaryBlue : Colors.grey[300]!,
                        width: isSelected ? 2 : 1
                      ),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(option, style: TextStyle(fontWeight: isSelected ? FontWeight.bold : FontWeight.normal, fontSize: 13)),
                        if (showResults)
                          Text("${(percent * 100).toStringAsFixed(0)}%", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: isSelected ? AppTheme.primaryBlue : Colors.grey[600]))
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildFoldableContent() {
    final content = _currentContent; 
    
    // Unified Parsing Logic
    final RegExp titleRegex = RegExp(r'^\*\*(.*?)\*\*\n+(.*)', multiLine: true, dotAll: true);
    final match = titleRegex.firstMatch(content);
    
    String title = "";
    String body = content;
    bool hasTitle = false;

    if (match != null) {
      title = match.group(1)?.trim() ?? "";
      body = match.group(2)?.trim() ?? "";
      hasTitle = true;
    } else {
      // Fallback for simple single-newline posts (Legacy/Quick posts)
      final lines = content.split('\n');
      if (lines.length > 1 && lines.first.length < 100) { // Limit title length for fallback
         title = lines.first.trim();
         body = lines.sublist(1).join('\n').trim();
         hasTitle = title.isNotEmpty && body.isNotEmpty;
      }
    }
    
    const maxLines = 4;
    final shouldFold = body.length > 150 || body.split('\n').length > 5;

    if (!shouldFold || widget.isDetail || _isExpanded) {
       return Column(
         crossAxisAlignment: CrossAxisAlignment.start,
         children: [
           if (hasTitle)
             Padding(
               padding: const EdgeInsets.only(bottom: 6),
               child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17, height: 1.3, color: Colors.black)),
             ),
           Text(
             body, 
             style: const TextStyle(
               fontWeight: FontWeight.normal,
               fontSize: 15, 
               height: 1.4, 
               color: Colors.black87
             )
           ),
           if (shouldFold && !widget.isDetail)
             GestureDetector(
               onTap: () => setState(() => _isExpanded = false),
               child: Padding(
                 padding: const EdgeInsets.only(top: 4),
                 child: Text("Kamroq o'qish", style: TextStyle(color: Colors.grey[600], fontSize: 13, fontWeight: FontWeight.bold)),
               ),
             )
         ],
       );
    } else {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
           if (hasTitle)
             Padding(
               padding: const EdgeInsets.only(bottom: 4),
               child: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17, height: 1.3, color: Colors.black)),
             ),
           Text(
             body, 
             maxLines: hasTitle ? 3 : 4,
             overflow: TextOverflow.ellipsis,
             style: const TextStyle(
               fontWeight: FontWeight.normal,
               fontSize: 15, 
               height: 1.4, 
               color: Colors.black87
             )
           ),
           GestureDetector(
             onTap: () => setState(() => _isExpanded = true),
             child: Padding(
               padding: const EdgeInsets.only(top: 4),
               child: Text("Davomi", style: TextStyle(color: Colors.grey[600], fontSize: 13, fontWeight: FontWeight.bold)),
             ),
           )
        ],
      );
    }
  }
}
