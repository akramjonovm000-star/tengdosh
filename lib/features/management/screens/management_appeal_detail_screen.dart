import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/core/constants/api_constants.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/appeal_service.dart';
import '../../appeals/models/appeal_model.dart' as student_models;

class ManagementAppealDetailScreen extends StatefulWidget {
  final int appealId;
  const ManagementAppealDetailScreen({super.key, required this.appealId});

  @override
  State<ManagementAppealDetailScreen> createState() => _ManagementAppealDetailScreenState();
}

class _ManagementAppealDetailScreenState extends State<ManagementAppealDetailScreen> {
  final AppealService _service = AppealService();
  student_models.AppealDetail? _detail;
  bool _isLoading = true;
  String? _error;
  final TextEditingController _replyController = TextEditingController();
  bool _isReplying = false;

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  Future<void> _loadDetail() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final detail = await _service.getAppealDetail(widget.appealId);
      if (mounted) {
        setState(() {
          _detail = detail;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _sendReply() async {
    final text = _replyController.text.trim();
    if (text.isEmpty) return;

    setState(() => _isReplying = true);
    try {
      await _service.replyAppeal(widget.appealId, text);
      if (mounted) {
        _replyController.clear();
        _loadDetail(); // Refresh
        setState(() => _isReplying = false);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isReplying = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Xatolik: $e"), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppTheme.backgroundWhite,
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null || _detail == null) {
      return Scaffold(
        appBar: AppBar(title: const Text("Xatolik")),
        body: Center(child: Text(_error ?? "Murojaat topilmadi")),
      );
    }

    String statusLabel = _detail!.status.toUpperCase();
    Color statusColor = Colors.orange;
    if (_detail!.status == 'answered' || _detail!.status == 'resolved' || _detail!.status == 'replied') {
      statusColor = Colors.green;
      statusLabel = "JAVOB BERILDI";
    } else if (_detail!.status == 'closed') {
      statusColor = Colors.red;
      statusLabel = "YOPILGAN";
    }

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Column(
          children: [
            Text("Murojaat #${_detail!.id}", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black)),
            Text(statusLabel, style: TextStyle(fontSize: 12, color: statusColor, fontWeight: FontWeight.bold)),
          ],
        ),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 1,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _detail!.messages.length,
              itemBuilder: (context, index) {
                final msg = _detail!.messages[index];
                final isMe = msg.sender == 'staff'; // From management perspective, staff is 'me'
                final isStudent = msg.sender == 'me'; 
                
                return Align(
                  alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(12),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: isMe ? AppTheme.primaryBlue : Colors.white,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(16),
                        topRight: const Radius.circular(16),
                        bottomLeft: isMe ? const Radius.circular(16) : const Radius.circular(4),
                        bottomRight: isMe ? const Radius.circular(4) : const Radius.circular(16),
                      ),
                      boxShadow: isMe ? [] : [
                        BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 5, offset: const Offset(0, 2))
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (msg.fileId != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8.0),
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: CachedNetworkImage(
                                imageUrl: "${ApiConstants.fileProxy}/${msg.fileId}",
                                placeholder: (context, url) => const Center(child: CircularProgressIndicator()),
                                errorWidget: (context, url, error) => const Icon(Icons.broken_image, color: Colors.grey),
                              ),
                            ),
                          ),
                        Text(
                          msg.text ?? (msg.fileId != null ? "" : "[Fayl]"), 
                          style: TextStyle(color: isMe ? Colors.white : Colors.black87),
                        ),
                        const SizedBox(height: 4),
                        Align(
                          alignment: Alignment.bottomRight,
                          child: Text(
                            msg.time,
                            style: TextStyle(
                              color: isMe ? Colors.white.withOpacity(0.7) : Colors.grey[500],
                              fontSize: 10
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          if (_detail!.status != 'closed') _buildReplyAction(),
        ],
      ),
    );
  }

  Widget _buildReplyAction() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, -5))],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _replyController,
                enabled: !_isReplying,
                decoration: InputDecoration(
                  hintText: "Javob yozish...",
                  filled: true,
                  fillColor: Colors.grey[100],
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
              ),
            ),
            const SizedBox(width: 8),
            CircleAvatar(
              backgroundColor: AppTheme.primaryBlue,
              child: _isReplying 
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : IconButton(
                    icon: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                    onPressed: _sendReply,
                  ),
            )
          ],
        ),
      ),
    );
  }
}
