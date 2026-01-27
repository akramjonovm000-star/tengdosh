import 'dart:async';
import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/chat_service.dart';
import 'user_profile_screen.dart';

class ChatDetailScreen extends StatefulWidget {
  final Chat chat;

  const ChatDetailScreen({super.key, required this.chat});

  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final ChatService _service = ChatService();
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  
  List<Message> _messages = [];
  bool _isLoading = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _loadMessages();
    _startPolling();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _startPolling() {
    _timer = Timer.periodic(const Duration(seconds: 3), (timer) {
      if (mounted) {
        _loadMessages(silent: true);
      }
    });
  }

  Future<void> _loadMessages({bool silent = false}) async {
    final msgs = await _service.getMessages(widget.chat.id);
    if (mounted) {
      setState(() {
        _messages = msgs; // API returns ordered by desc (newest first), which matches reverse list view
        if (!silent) _isLoading = false;
      });
    }
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    _controller.clear();
    
    // Optimistic UI (Optional, but let's wait for server for consistency or add simple local pending)
    // Actually, let's just send and refresh.
    
    final newMsg = await _service.sendMessage(widget.chat.id, text);
    
    if (newMsg != null && mounted) {
      setState(() {
        _messages.insert(0, newMsg);
      });
    } else {
      // Error
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Xabar yuborishda xatolik")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5), // Light grey bg
      appBar: AppBar(
        titleSpacing: 0,
        backgroundColor: Colors.white,
        elevation: 1,
        iconTheme: const IconThemeData(color: Colors.black),
        title: InkWell(
          onTap: () {
             Navigator.push(
               context,
               MaterialPageRoute(
                 builder: (_) => UserProfileScreen(
                   authorId: widget.chat.partnerId,
                   authorName: widget.chat.formattedName,
                   authorUsername: widget.chat.partnerUsername, // No @ here, screen adds it?
                   authorAvatar: widget.chat.partnerAvatar,
                   authorRole: widget.chat.partnerRole,
                 )
               )
             );
          },
          child: Row(
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                backgroundImage: widget.chat.partnerAvatar.isNotEmpty 
                    ? NetworkImage(widget.chat.partnerAvatar) 
                    : null,
               child: widget.chat.partnerAvatar.isEmpty 
                    ? Text(widget.chat.formattedName.isNotEmpty ? widget.chat.formattedName[0] : "?", style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue, fontSize: 14))
                    : null,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                     Text(widget.chat.formattedName, style: const TextStyle(color: Colors.black, fontSize: 16, fontWeight: FontWeight.bold)),
                     Text("@${widget.chat.partnerUsername} • ${widget.chat.partnerRole}", style: const TextStyle(color: Colors.grey, fontSize: 12)) 
                  ],
                ),
              )
            ],
          ),
        ),
        actions: [
          IconButton(icon: const Icon(Icons.more_vert), onPressed: (){}),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator())
              : _messages.isEmpty 
                  ? Center(child: Text("Hozircha xabarlar yo'q", style: TextStyle(color: Colors.grey[400])))
                  : ListView.builder(
                      controller: _scrollController,
                      reverse: true, // Bottom to top
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                      itemCount: _messages.length,
                      itemBuilder: (context, index) {
                        final msg = _messages[index];
                        return _buildMessageBubble(msg);
                      },
                    ),
          ),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(Message msg) {
    final isMe = msg.isMe;
    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isMe ? AppTheme.primaryBlue : Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: isMe ? const Radius.circular(16) : const Radius.circular(0),
            bottomRight: isMe ? const Radius.circular(0) : const Radius.circular(16),
          ),
          boxShadow: [
             BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset:const Offset(0, 2))
          ]
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              msg.content,
              style: TextStyle(color: isMe ? Colors.white : Colors.black87, fontSize: 15),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  msg.timestamp,
                  style: TextStyle(color: isMe ? Colors.white70 : Colors.grey[400], fontSize: 10),
                ),
                if (isMe) ...[
                   const SizedBox(width: 4),
                   Icon(
                     msg.isRead ? Icons.done_all : Icons.done, 
                     size: 12, 
                     color: Colors.white70
                   )
                ]
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: Colors.white,
      child: SafeArea( 
        child: Row(
          children: [
            IconButton(
              icon: const Icon(Icons.add, color: AppTheme.primaryBlue),
              onPressed: () {},
            ),
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(24),
                ),
                child: TextField(
                  controller: _controller,
                  decoration: const InputDecoration(
                    hintText: "Xabar yozing...",
                    border: InputBorder.none,
                  ),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: const Icon(Icons.send_rounded, color: AppTheme.primaryBlue),
              onPressed: _sendMessage,
            ),
          ],
        ),
      ),
    );
  }
}
