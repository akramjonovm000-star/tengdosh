import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../screens/user_profile_screen.dart';
import 'package:cached_network_image/cached_network_image.dart';

class CommentItem extends StatelessWidget {
  final Comment comment;
  final Function(String commentId) onLike;
  final Function(Comment comment)? onReply;
  final Function(String commentId)? onDelete;
  final Function(Comment comment, String newContent)? onEdit; // New Callback
  final bool isReply;
  final bool isParent; // For showing centered/highlighted in thread view

  const CommentItem({
    super.key,
    required this.comment,
    required this.onLike,
    this.onReply,
    this.onDelete,
    this.onEdit, // Initialize onEdit
    this.isReply = false,
    this.isParent = false,
  });

  @override
  Widget build(BuildContext context) {
    if (comment.isMine) {
      return Dismissible(
        key: Key(comment.id),
        direction: DismissDirection.startToEnd,
        background: Container(
          color: Colors.red[50],
          alignment: Alignment.centerLeft,
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: const Icon(Icons.delete_outline, color: Colors.red),
        ),
        confirmDismiss: (direction) async {
          if (onDelete == null) return false;
          return await showDialog(
            context: context,
            builder: (ctx) => AlertDialog(
              title: const Text("O'chirish"),
              content: const Text("Ushbu sharhni o'chirmoqchimisiz?"),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Yo'q")),
                TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("Ha", style: TextStyle(color: Colors.red))),
              ],
            ),
          );
        },
        onDismissed: (direction) {
          onDelete?.call(comment.id);
        },
        child: _buildContent(context),
      );
    } 
    
    // Swipe to Reply for others
    return Dismissible(
      key: ValueKey("reply_${comment.id}"), // Unique key different from delete key
      direction: DismissDirection.endToStart,
      confirmDismiss: (direction) async {
        if (onReply != null) {
          onReply!.call(comment);
        }
        return false;
      },
      background: Container(
        color: Colors.blue[50],
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: const Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            Text("Javob berish", style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold)),
            SizedBox(width: 8),
            Icon(Icons.reply, color: AppTheme.primaryBlue),
          ],
        ),
      ),
      child: _buildContent(context),
    );
  }

  Widget _buildContent(BuildContext context) {
    // "Indented to the right" for replies
    // User Requirement: "Replies must be visually indented to the right (one tab / padding-left)"
    // Increased indentation to 48.0 for better visibility.
    final content = Container(
      // Switch to Padding for robust indentation inside Dismissible
      // Margin was not rendering correctly in some layouts.
      // Padding ensures the content (avatar+text) is shifted, while the container fills width.
      padding: EdgeInsets.only(
        left: isReply ? 56.0 : 16.0, // 56px indent for replies, 16px default
        right: 16,
        top: 8,
        bottom: 8
      ),
      color: isParent ? Colors.grey[50] : Colors.white,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onLongPress: () {
              if (comment.isMine) {
                showModalBottomSheet(
                  context: context,
                  builder: (ctx) => Wrap(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.edit, color: Colors.blue),
                        title: const Text("Tahrirlash"),
                        onTap: () {
                          Navigator.pop(ctx);
                          _showEditDialog(context);
                        },
                      ),
                      ListTile(
                        leading: const Icon(Icons.delete, color: Colors.red),
                        title: const Text("O'chirish"),
                        onTap: () {
                          Navigator.pop(ctx);
                          // Trigger existing delete logic
                          onDelete?.call(comment.id);
                        },
                      ),
                    ],
                  ),
                );
              }
            },
            onTap: () {
               Navigator.push(context, MaterialPageRoute(builder: (_) => UserProfileScreen(
                  authorName: comment.authorName,
                  authorId: comment.authorId,
                  authorUsername: comment.authorUsername,
                  authorAvatar: comment.authorAvatar,
                  authorRole: comment.authorRole ?? "Talaba",
                  authorIsPremium: comment.authorIsPremium, // NEW
               )));
            },
            child: CircleAvatar(
              backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
              radius: isReply ? 14 : 18, 
              child: comment.authorAvatar.isNotEmpty 
                ? ClipOval(
                    child: CachedNetworkImage(
                      imageUrl: comment.authorAvatar,
                      width: isReply ? 28 : 36,
                      height: isReply ? 28 : 36,
                      fit: BoxFit.cover,
                      placeholder: (context, url) => Icon(Icons.person, size: isReply ? 16 : 20, color: Colors.grey),
                      errorWidget: (context, url, error) => Text(comment.authorName.isNotEmpty ? comment.authorName[0] : "?", style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue, fontSize: isReply ? 12 : 14)),
                    ),
                  )
                : Text(comment.authorName.isNotEmpty ? comment.authorName[0] : "?", style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue, fontSize: isReply ? 12 : 14)),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                RichText(
                  text: TextSpan(
                    style: const TextStyle(color: Colors.black, fontFamily: 'Inter'),
                    children: [
                      TextSpan(
                        text: comment.authorName, 
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)
                      ),
                      if (comment.authorIsPremium) ...[
                        const WidgetSpan(child: SizedBox(width: 4)),
                        const WidgetSpan(child: Icon(Icons.verified, color: Colors.blue, size: 14)),
                      ],
                      const WidgetSpan(child: SizedBox(width: 4)),
                      if (comment.authorUsername.isNotEmpty)
                        TextSpan(
                          text: "@${comment.authorUsername}",
                          style: const TextStyle(color: AppTheme.primaryBlue, height:1.2, fontSize: 13, fontWeight: FontWeight.w500)
                        ),
                    ]
                  )
                ),
                
                 if (comment.replyToUserName != null && !isParent) 
                   Container(
                     margin: const EdgeInsets.only(top: 4, bottom: 6),
                     padding: const EdgeInsets.only(left: 8),
                     decoration: const BoxDecoration(
                       border: Border(left: BorderSide(color: AppTheme.primaryBlue, width: 2))
                     ),
                     child: Column(
                       crossAxisAlignment: CrossAxisAlignment.start,
                       children: [
                         Text(
                           comment.replyToUserName!.startsWith('@') 
                               ? comment.replyToUserName! 
                               : "@${comment.replyToUserName}", 
                           style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppTheme.primaryBlue)
                         ),
                         if (comment.replyToContent != null && comment.replyToContent!.isNotEmpty)
                           Padding(
                             padding: const EdgeInsets.only(top: 2),
                             child: Text(
                               comment.replyToContent!,
                               maxLines: 1,
                               overflow: TextOverflow.ellipsis,
                               style: const TextStyle(fontSize: 12, color: AppTheme.primaryBlue)
                             ),
                           ),
                       ],
                     ),
                   ),

                Padding(
                  padding: const EdgeInsets.only(top: 2, bottom: 4),
                  child: Text(
                    comment.content,
                    style: const TextStyle(fontSize: 14, height: 1.3),
                  ),
                ),

                Row(
                  children: [
                    Text(comment.timeAgo, style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                    if (!isParent) ...[
                      const SizedBox(width: 16),
                      GestureDetector(
                        onTap: () => onReply?.call(comment),
                        child: const Text("Javob berish", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.grey)),
                      ),
                    ],
                    const Spacer(),
                    GestureDetector(
                      onTap: () => onLike(comment.id),
                      child: Row(
                        children: [
                           Icon(
                             comment.isLiked ? Icons.favorite : Icons.favorite_outline, 
                             size: 14, 
                             color: comment.isLiked ? Colors.red : Colors.grey 
                           ),
                           if (comment.likes > 0) ...[
                             const SizedBox(width: 4),
                             Text("${comment.likes}", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                           ]
                        ],
                      ),
                    )
                  ],
                )
              ],
            ),
          )
        ],
      ),
    );

    if (isReply) {
      return Stack(
        children: [
          content,
          // Custom Painter for Connector Line
          Positioned(
            top: 0,
            bottom: 0,
            left: 0,
            width: 56, // Padding area
            child: CustomPaint(
              painter: ConnectorLinePainter(),
            ),
          )
        ],
      );
    }

    return content;
  }

  void _showEditDialog(BuildContext context) {
    final controller = TextEditingController(text: comment.content);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Sharhni tahrirlash"),
        content: TextField(
          controller: controller,
          maxLines: 3,
          decoration: const InputDecoration(border: OutlineInputBorder()),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Bekor qilish")),
          TextButton(
            onPressed: () {
              if (controller.text.trim().isNotEmpty) {
                 onEdit?.call(comment, controller.text.trim());
                 Navigator.pop(ctx);
              }
            }, 
            child: const Text("Saqlash")
          ),
        ],
      ),
    );
  }
}

class ConnectorLinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final Paint paint = Paint()
      ..color = Colors.grey[300]!
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    // Logic: Draw line from top to center-left
    // Start X: Center of Parent Avatar (visually around 16 + 18 = 34px) 
    // But since we are inside the item, 'top' starts from this item's top.
    // We assume the line comes from above.
    
    // Path:
    // 1. Vertical Line from top (0) to (Center Y - radius)
    // 2. Curve to Right
    // 3. Horizontal Line to (Right Edge)
    
    // Avatar Center Y in this item:
    // Padding Top: 8. Radius: 14. Diameter: 28. Center Y = 8 + 14 = 22.
    
    final double startX = 34.0; // Approx center of parent avatar column
    final double endX = 50.0; // Near the reply avatar
    final double centerY = 22.0; 
    final double cornerRadius = 12.0;

    final Path path = Path();
    path.moveTo(startX, -10); // Start from above (connecting to previous)
    path.lineTo(startX, centerY - cornerRadius);
    path.quadraticBezierTo(startX, centerY, startX + cornerRadius, centerY);
    path.lineTo(endX, centerY); // Horizontal line

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
