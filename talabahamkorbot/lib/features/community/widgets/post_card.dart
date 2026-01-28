import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../screens/post_detail_screen.dart';
import '../screens/user_profile_screen.dart';

class PostCard extends StatefulWidget {
  final Post post;
  final bool isDetail;

  const PostCard({super.key, required this.post, this.isDetail = false});

  @override
  State<PostCard> createState() => _PostCardState();
}

class _PostCardState extends State<PostCard> {
  late bool _isLiked;
  late int _likeCount;
  late int _repostCount;

  @override
  void initState() {
    super.initState();
    _isLiked = widget.post.isLiked;
    _likeCount = widget.post.likes;
    _repostCount = widget.post.repostsCount;
  }


  void _toggleLike() {
    setState(() {
      _isLiked = !_isLiked;
      _likeCount += _isLiked ? 1 : -1;
    });
  }

  void _toggleRepost() {
    // Note: Repost logic usually requires API. For now we just show it.
  }

  void _sharePost() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Havola nusxalandi! (Mock)")),
    );
  }

  @override
  Widget build(BuildContext context) {
    Widget content = Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: Colors.grey[200]!, width: 1)), // Divider style
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header (Avatar + Names)
          GestureDetector(
            onTap: () {
               Navigator.push(context, MaterialPageRoute(builder: (_) => UserProfileScreen(
                 authorName: widget.post.authorName,
                authorUsername: widget.post.authorUsername ?? "@talaba",
                 authorAvatar: widget.post.authorAvatar,
                 authorRole: widget.post.authorRole,
               )));
            },
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
              Hero(
                tag: "avatar_${widget.post.id}",
                child: CircleAvatar(
                  radius: 22,
                  backgroundImage: widget.post.authorAvatar.isNotEmpty ? NetworkImage(widget.post.authorAvatar) : null,
                  backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                  child: widget.post.authorAvatar.isEmpty 
                    ? Text(widget.post.authorName[0], style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold))
                    : null,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            widget.post.authorName,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (widget.post.isVerified) ...[
                          const SizedBox(width: 4),
                          const Icon(Icons.verified, color: Colors.blue, size: 16),
                        ],
                      ],
                    ),
                    Text(
                      "${widget.post.authorUsername ?? '@talaba'} • ${widget.post.timeAgo ?? 'Hozirgina'}",
                      style: TextStyle(color: Colors.grey[500], fontSize: 13),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.more_horiz, color: Colors.grey),
                onPressed: () {},
                constraints: const BoxConstraints(),
                padding: EdgeInsets.zero,
              )
            ],
          ),
          ),
          
          // Body content
          Padding(
             padding: const EdgeInsets.only(left: 56), // Align with text start
             child: Column(
               crossAxisAlignment: CrossAxisAlignment.start,
               children: [
                 const SizedBox(height: 4),
                 Text(widget.post.content, style: const TextStyle(fontSize: 15, height: 1.4, color: Colors.black87)),
                 
                 // Tags
                 if (widget.post.tags.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Wrap(
                        spacing: 8,
                        children: widget.post.tags.map((tag) => Text(tag, style: const TextStyle(color: AppTheme.primaryBlue, fontSize: 13))).toList(),
                      ),
                    ),

                 // Media Grid
                 if (widget.post.mediaUrls.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: _buildMediaGrid(),
                    ),


                 const SizedBox(height: 12),
                 
                 // Actions
                 Row(
                   mainAxisAlignment: MainAxisAlignment.spaceBetween,
                   children: [
                      _buildAction(
                        icon: Icons.chat_bubble_outline_rounded, 
                        count: widget.post.commentsCount, 
                        color: Colors.grey,
                        onTap: () {
                           if (!widget.isDetail) {
                              Navigator.push(context, MaterialPageRoute(builder: (_) => PostDetailScreen(post: widget.post)));
                           }
                        }
                      ),
                      _buildAction(
                        icon: Icons.repeat_rounded, 
                        count: _repostCount, 
                        color: Colors.grey,
                        onTap: _toggleRepost
                      ),
                      _buildAction(
                        icon: _isLiked ? Icons.favorite_rounded : Icons.favorite_border_rounded, 
                        count: _likeCount, 
                        color: _isLiked ? Colors.pink : Colors.grey,
                        onTap: _toggleLike
                      ),
                      _buildAction(
                        icon: Icons.share_rounded, 
                        count: null, // Share usually doesn't show count locally unless API provided
                        color: Colors.grey,
                        onTap: _sharePost
                      ),
                   ],
                 )
               ],
             ),
          )
        ],
      ),
    );

    if (widget.isDetail) return content;

    return InkWell(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => PostDetailScreen(post: widget.post),
          ),
        );
      },
      child: content,
    );
  }

  Widget _buildMediaGrid() {
    final urls = widget.post.mediaUrls;
    if (urls.isEmpty) return const SizedBox.shrink();

    // Simple implementation: Just show first image rounded
    // In real app, would use GridView or StaggeredGrid
    // Since mock data only has 1 url usually, we keep it simple.
    
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: AspectRatio(
        aspectRatio: 16/9,
        child: Image.network(
           urls.first, 
           fit: BoxFit.cover,
           errorBuilder: (ctx, _, __) => Container(
             color: Colors.grey[200],
             child: const Center(child: Icon(Icons.broken_image, color: Colors.grey)),
           ),
        ),
      ),
    );
  }

  Widget _buildAction({required IconData icon, int? count, required Color color, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Row(
          children: [
            Icon(icon, size: 20, color: color),
            if (count != null && count > 0) ...[
               const SizedBox(width: 4),
               Text("$count", style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.normal))
            ]
          ],
        ),
      ),
    );
  }

}
