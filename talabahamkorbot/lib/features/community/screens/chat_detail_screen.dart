import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';

class ChatDetailScreen extends StatefulWidget {
  final Chat chat;

  const ChatDetailScreen({super.key, required this.chat});

  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final CommunityService _service = CommunityService();
  final TextEditingController _controller = TextEditingController();
  List<Message> _messages = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadMessages();
  }

  Future<void> _loadMessages() async {
    final msgs = await _service.getMessages(widget.chat.id);
    if (mounted) {
      setState(() {
        _messages = msgs.reversed.toList(); // Reverse for standard chat view
        _isLoading = false;
      });
    }
  }

  void _sendMessage() {
    if (_controller.text.trim().isEmpty) return;

    final newMessage = Message(
      id: DateTime.now().toString(),
      content: _controller.text.trim(),
      isMe: true,
      timestamp: "${DateTime.now().hour}:${DateTime.now().minute.toString().padLeft(2, '0')}",
      isRead: false,
    );

    setState(() {
      _messages.insert(0, newMessage);
      _controller.clear();
    });
    
    // Mock Reply
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
         setState(() {
           _messages.insert(0, Message(
             id: "reply_${DateTime.now()}", 
             content: "Ok, tushunarli.", 
             isMe: false, 
             timestamp: "Hozirgina"
           ));
         });
      }
    });
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
        title: Row(
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
               child: Text(
                widget.chat.partnerName[0],
                style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue, fontSize: 14),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   Text(widget.chat.partnerName, style: const TextStyle(color: Colors.black, fontSize: 16)),
                   Text(
                     widget.chat.isOnline ? "Online" : "Last seen ${widget.chat.timeAgo}",
                     style: TextStyle(color: widget.chat.isOnline ? Colors.green : Colors.grey, fontSize: 12),
                   )
                ],
              ),
            )
          ],
        ),
        actions: [
          IconButton(icon: const Icon(Icons.call), onPressed: (){}),
          IconButton(icon: const Icon(Icons.more_vert), onPressed: (){}),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator())
              : ListView.builder(
                  reverse: true,
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
      child: SafeArea( // For iPhone bottom bar
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
