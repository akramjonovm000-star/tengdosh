import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/core/constants/api_constants.dart';

class GroupAppealsScreen extends StatefulWidget {
  final String groupNumber;

  const GroupAppealsScreen({super.key, required this.groupNumber});

  @override
  State<GroupAppealsScreen> createState() => _GroupAppealsScreenState();
}

class _GroupAppealsScreenState extends State<GroupAppealsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _appeals = [];
  final TextEditingController _replyController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadAppeals();
  }

  Future<void> _loadAppeals() async {
    setState(() => _isLoading = true);
    try {
      final appeals = await _dataService.getGroupAppeals(widget.groupNumber);
      if (mounted) {
        setState(() {
          _appeals = appeals;
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint("Error loading appeals: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showReplyDialog(int appealId, String studentName) {
    _replyController.clear();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Javob yozish: $studentName"),
        content: TextField(
          controller: _replyController,
          maxLines: 4,
          decoration: const InputDecoration(
            hintText: "Javobingizni shu yerga yozing...",
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Bekor qilish"),
          ),
          ElevatedButton(
            onPressed: () async {
              if (_replyController.text.trim().isEmpty) return;
              Navigator.pop(context); // Close dialog
              await _sendReply(appealId, _replyController.text.trim());
            },
            child: const Text("Yuborish"),
          ),
        ],
      ),
    );
  }

  Future<void> _sendReply(int appealId, String text) async {
    _showLoading(true);
    try {
      await _dataService.replyToTutorAppeal(appealId, text);
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(content: Text("✅ Javob yuborildi")),
         );
         _loadAppeals(); // Refresh
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(content: Text("❌ Xatolik bo'ldi: $e")),
         );
      }
    } finally {
      if (mounted) _showLoading(false);
    }
  }

  // Simple loading overlay or just rely on global state? 
  // For simplicity, we assume fast interactions or non-blocking, but for reply lets refresh.
  void _showLoading(bool show) {
    if (show) {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (_) => const Center(child: CircularProgressIndicator()),
      );
    } else {
      // Pop loading dialog - fragile if navigation changed, but OK for simple logic.
      // Better to check if dialog is open, but assuming standard flow.
      // Actually we just pushed a dialog in _sendReply start? No, I will put it in _sendReply.
      Navigator.of(context, rootNavigator: true).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text("Murojaatlar: ${widget.groupNumber}"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _appeals.isEmpty
              ? const Center(child: Text("Hozircha murojaatlar yo'q"))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _appeals.length,
                  itemBuilder: (context, index) {
                    final appeal = _appeals[index];
                    final isPending = appeal['status'] == 'pending';
                    
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 1,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    appeal['student_name'] ?? "Noma'lum",
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: isPending ? Colors.orange.withOpacity(0.1) : Colors.green.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    isPending ? "Yangi" : "Javob berilgan",
                                    style: TextStyle(
                                      color: isPending ? Colors.orange[800] : Colors.green[800],
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              appeal['text'] ?? "",
                              style: const TextStyle(fontSize: 14),
                              maxLines: 4,
                              overflow: TextOverflow.ellipsis,
                            ),
                            if (appeal['file_id'] != null && appeal['file_id'] != "") ...[
                              const SizedBox(height: 8),
                              Container(
                                height: 150,
                                width: double.infinity,
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(8),
                                  color: Colors.grey[200],
                                  image: DecorationImage(
                                    image: NetworkImage("${ApiConstants.backendUrl}/static/uploads/${appeal['file_id']}"),
                                    fit: BoxFit.cover,
                                    onError: (e, s) => const Icon(Icons.broken_image, color: Colors.grey),
                                  ),
                                ),
                              ),
                            ],
                            const SizedBox(height: 12),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                Text(
                                  _formatDate(appeal['created_at']),
                                  style: TextStyle(color: Colors.grey[500], fontSize: 12),
                                ),
                                const Spacer(),
                                if (isPending)
                                  ElevatedButton.icon(
                                    onPressed: () => _showReplyDialog(appeal['id'], appeal['student_name']),
                                    icon: const Icon(Icons.reply, size: 16),
                                    label: const Text("Javob berish"),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: AppTheme.primaryBlue,
                                      foregroundColor: Colors.white,
                                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                      textStyle: const TextStyle(fontSize: 12),
                                    ),
                                  ),
                              ],
                            )
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }

  String _formatDate(String? iso) {
    if (iso == null) return "";
    try {
      final dt = DateTime.parse(iso);
      return "${dt.day}.${dt.month.toString().padLeft(2, '0')} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}";
    } catch (_) {
      return iso;
    }
  }
}
