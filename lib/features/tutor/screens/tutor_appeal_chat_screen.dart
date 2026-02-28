import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/core/constants/api_constants.dart';
import 'package:cached_network_image/cached_network_image.dart';

class TutorAppealChatScreen extends StatefulWidget {
  final int appealId;

  const TutorAppealChatScreen({super.key, required this.appealId});

  @override
  State<TutorAppealChatScreen> createState() => _TutorAppealChatScreenState();
}

class _TutorAppealChatScreenState extends State<TutorAppealChatScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  Map<String, dynamic>? _detail;
  final TextEditingController _replyController = TextEditingController();
  bool _isReplying = false;

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  Future<void> _loadDetail() async {
    setState(() => _isLoading = true);
    try {
      final detail = await _dataService.getTutorAppealDetail(widget.appealId);
      if (mounted) {
        setState(() {
          _detail = detail;
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint("Error loading chat detail: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _sendReply() async {
    final text = _replyController.text.trim();
    if (text.isEmpty) return;

    setState(() => _isReplying = true);
    try {
      await _dataService.replyToTutorAppeal(widget.appealId, text);
      if (mounted) {
        _replyController.clear();
        await _loadDetail(); // Refresh chat
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Xatolik: $e")),
        );
      }
    } finally {
      if (mounted) setState(() => _isReplying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text(_detail != null ? "${_detail!['student_name']}" : "Murojaat chati"),
        actions: [
          if (_detail != null && (_detail!['status'] == 'closed' || _detail!['status'] == 'resolved'))
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Center(
                child: Text("Hal qilingan", style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
              ),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _detail == null
              ? const Center(child: Text("Ma'lumot topilmadi."))
              : Column(
                  children: [
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: (_detail!['messages'] as List).length,
                        itemBuilder: (context, index) {
                          final msg = _detail!['messages'][index];
                          final isMe = msg['sender'] == 'me';
                          return _buildChatBubble(msg, isMe);
                        },
                      ),
                    ),
                    _buildInputArea(),
                  ],
                ),
    );
  }

  Widget _buildChatBubble(dynamic msg, bool isMe) {
    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isMe ? AppTheme.primaryBlue : Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isMe ? 16 : 0),
            bottomRight: Radius.circular(isMe ? 0 : 16),
          ),
          border: isMe ? null : Border.all(color: Colors.grey[200]!),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Sender name if not me
            if (!isMe && msg['sender_name'] != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  msg['sender_name'],
                  style: TextStyle(
                    color: Colors.blue[800],
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),

            // Image attachment
            if (msg['file_id'] != null && msg['file_id'] != "") ...[
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: CachedNetworkImage(
                  imageUrl: "${ApiConstants.backendUrl}/static/uploads/${msg['file_id']}",
                  fit: BoxFit.cover,
                  width: double.infinity,
                  placeholder: (context, url) => Container(
                    height: 150,
                    color: Colors.grey[200],
                    child: const Center(child: CircularProgressIndicator()),
                  ),
                  errorWidget: (context, url, error) => Container(
                    height: 80,
                    color: Colors.grey[200],
                    child: const Icon(Icons.broken_image, color: Colors.grey),
                  ),
                ),
              ),
              const SizedBox(height: 8),
            ],

            // Text
            Text(
              msg['text'] ?? "",
              style: TextStyle(
                color: isMe ? Colors.white : Colors.black87,
                fontSize: 15,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 4),

            // Time
            Align(
              alignment: Alignment.bottomRight,
              child: Text(
                msg['time'] ?? "",
                style: TextStyle(
                  color: isMe ? Colors.white70 : Colors.grey[500],
                  fontSize: 10,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInputArea() {
    final isResolved = _detail!['status'] == 'closed' || _detail!['status'] == 'resolved';
    
    if (isResolved) {
      return Container(
        padding: const EdgeInsets.all(16),
        color: Colors.grey[100],
        child: const Center(
          child: Text(
            "Bu murojaat hal qilingan, javob yozish imkoni yo'q.",
            style: TextStyle(color: Colors.grey),
          ),
        ),
      );
    }

    return Container(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 12,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _replyController,
              decoration: InputDecoration(
                hintText: AppDictionary.tr(context, 'hint_write_answer'),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: Colors.grey[100],
                contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              ),
              maxLines: null,
            ),
          ),
          const SizedBox(width: 12),
          _isReplying
              ? const CircularProgressIndicator()
              : CircleAvatar(
                  radius: 24,
                  backgroundColor: AppTheme.primaryBlue,
                  child: IconButton(
                    icon: const Icon(Icons.send_rounded, color: Colors.white),
                    onPressed: _sendReply,
                  ),
                ),
        ],
      ),
    );
  }
}
