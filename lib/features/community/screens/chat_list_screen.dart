import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/chat_service.dart';
import 'chat_detail_screen.dart';
import '../widgets/user_search_delegate.dart'; // NEW
import 'package:cached_network_image/cached_network_image.dart';

class ChatListScreen extends StatefulWidget {
  const ChatListScreen({super.key});

  @override
  State<ChatListScreen> createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  final ChatService _service = ChatService();
  late Future<List<Chat>> _chatsFuture;

  @override
  void initState() {
    super.initState();
    _refreshChats();
  }

  void _refreshChats() {
    setState(() {
      _chatsFuture = _service.getChats();
    });
  }

  Future<void> _confirmDelete(Chat chat) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Chatni o'chirish"),
        content: Text("Haqiqatan ham ${chat.formattedName} bilan suhbatni o'chirib yubormoqchimisiz?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text("Bekor qilish", style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("O'chirish", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final success = await _service.deleteChat(chat.id);
      if (success) {
        _refreshChats();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Chat muvaffaqiyatli o'chirildi")),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Xatolik yuz berdi")),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("Xabarlar", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: FutureBuilder<List<Chat>>(
        future: _chatsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return _buildEmptyState();
          }

          final chats = snapshot.data!;
          return RefreshIndicator(
            onRefresh: () async {
              _refreshChats();
              await _chatsFuture;
            },
            child: ListView.separated(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: chats.length,
              separatorBuilder: (ctx, i) => const Divider(height: 1, indent: 72),
              itemBuilder: (context, index) {
                final chat = chats[index];
                return ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ChatDetailScreen(chat: chat),
                      ),
                    ).then((_) => _refreshChats()); // Refresh on return
                  },
                  onLongPress: () => _confirmDelete(chat),
                  leading: Stack(
                    children: [
                      CircleAvatar(
                      radius: 24,
                      backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                      child: chat.partnerAvatar.isNotEmpty
                          ? ClipOval(
                              child: CachedNetworkImage(
                                imageUrl: chat.partnerAvatar,
                                width: 48,
                                height: 48,
                                fit: BoxFit.cover,
                                placeholder: (context, url) => const Center(child: CircularProgressIndicator(strokeWidth: 2)),
                                errorWidget: (context, url, error) => Text(
                                  chat.partnerName.isNotEmpty ? chat.partnerName[0] : "?",
                                  style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue),
                                ),
                              ),
                            )
                          : Text(
                              chat.partnerName.isNotEmpty ? chat.partnerName[0] : "?",
                              style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue),
                            ),
                    ),
                    if (chat.isOnline)
                      Positioned(
                        right: 0,
                        bottom: 0,
                        child: Container(
                          width: 14,
                          height: 14,
                          decoration: BoxDecoration(
                            color: Colors.green,
                            border: Border.all(color: Colors.white, width: 2),
                            shape: BoxShape.circle,
                          ),
                        ),
                      )
                  ],
                ),
                title: Row(
                  children: [
                    Text(
                      chat.formattedName,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    if (chat.partnerIsPremium) ...[
                      const SizedBox(width: 4),
                      chat.partnerCustomBadge != null 
                          ? Text(chat.partnerCustomBadge!, style: const TextStyle(fontSize: 14))
                          : const Icon(Icons.verified, color: Colors.blue, size: 16),
                    ]
                  ],
                ),
                subtitle: Text(
                  chat.isLastMessageMine ? "Siz: ${chat.lastMessage}" : chat.lastMessage,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: (chat.unreadCount > 0 && !chat.isLastMessageMine) ? Colors.black87 : Colors.grey,
                    fontWeight: (chat.unreadCount > 0 && !chat.isLastMessageMine) ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
                trailing: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      chat.timeAgo,
                      style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                    ),
                    if (chat.unreadCount > 0 && !chat.isLastMessageMine) ...[
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: const BoxDecoration(
                          color: AppTheme.primaryBlue,
                          shape: BoxShape.circle,
                        ),
                        child: Text(
                          "${chat.unreadCount}",
                          style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      )
                    ]
                  ],
                ),
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          showSearch(
            context: context,
            delegate: UserSearchDelegate(
              historyKey: 'chat_users', // Distinct history
              onUserSelected: (student) async {
                // print("User selected: ${student.fullName}");
                final chat = await _service.startChat(student.id.toString());
                if (chat != null && mounted) {
                   // print("Chat created: ${chat.id}, Navigating...");
                   Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => ChatDetailScreen(chat: chat))
                  );
                } else {
                  // print("Chat creation failed or unmounted");
                }
              }
            ),
          );
        },
        backgroundColor: AppTheme.primaryBlue,
        child: const Icon(Icons.add_comment_rounded, color: Colors.white),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.mark_chat_unread_outlined, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            "Xabarlar yo'q",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          const Text(
            "Do'stlaringizga birinchi bo'lib yozing!",
            style: TextStyle(color: Colors.grey),
          ),
        ],
      ),
    );
  }
}
