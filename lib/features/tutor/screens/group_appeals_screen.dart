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

  void _showLoading(bool show) {
    if (show) {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (_) => const Center(child: CircularProgressIndicator()),
      );
    } else {
      Navigator.of(context, rootNavigator: true).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100], // Slightly darker background for contrast
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        title: Text(
          "Murojaatlar: ${widget.groupNumber}",
          style: const TextStyle(color: Colors.black),
        ),
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _appeals.isEmpty
              ? _buildEmptyState()
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _appeals.length,
                  itemBuilder: (context, index) {
                    return _buildAppealCard(_appeals[index]);
                  },
                ),
    );
  }
  
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.mark_email_read_outlined, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            "Yangi murojaatlar yo'q",
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }

  Widget _buildAppealCard(dynamic appeal) {
    final isPending = appeal['status'] == 'pending';
    final studentName = appeal['student_name'] ?? "Noma'lum";
    final studentGroup = appeal['student_group'] ?? widget.groupNumber;
    final studentFac = appeal['student_faculty'] ?? "";
    final date = _formatDate(appeal['created_at']);
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // HEADER: User Info
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 24,
                  backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                  backgroundImage: appeal['student_image'] != null 
                    ? NetworkImage(appeal['student_image']) 
                    : null,
                  child: appeal['student_image'] == null 
                    ? Text(studentName[0].toUpperCase(), style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue)) 
                    : null,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        studentName,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.black87),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        "$studentFac • $studentGroup",
                        style: TextStyle(color: Colors.grey[600], fontSize: 12),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                
                // Date Badge
                Text(
                  date,
                  style: TextStyle(color: Colors.grey[400], fontSize: 11),
                ),
              ],
            ),
          ),
          
          const Divider(height: 1),
          
          // BODY: Content + Image
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  appeal['text'] ?? "",
                  style: const TextStyle(fontSize: 15, height: 1.4, color: Colors.black87),
                ),
                if (appeal['file_id'] != null && appeal['file_id'] != "") ...[
                  const SizedBox(height: 12),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      height: 180,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        border: Border.all(color: Colors.grey.withOpacity(0.2)),
                      ),
                      child: Image.network(
                        "${ApiConstants.backendUrl}/static/uploads/${appeal['file_id']}",
                        fit: BoxFit.cover,
                        errorBuilder: (c, o, s) => Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.broken_image_rounded, color: Colors.grey[400], size: 40),
                            const SizedBox(height: 8),
                            Text("Rasm mavjud", style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          
          // FOOTER: Actions
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.grey[50],
              borderRadius: const BorderRadius.vertical(bottom: Radius.circular(16)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Status Badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: isPending ? Colors.orange.withOpacity(0.1) : Colors.green.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: isPending ? Colors.orange.withOpacity(0.3) : Colors.green.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        isPending ? Icons.access_time_rounded : Icons.check_circle_rounded,
                        size: 14,
                        color: isPending ? Colors.orange[800] : Colors.green[800]
                      ),
                      const SizedBox(width: 6),
                      Text(
                        isPending ? "Javob kutilmoqda" : "Javob berilgan",
                        style: TextStyle(
                          color: isPending ? Colors.orange[800] : Colors.green[800],
                          fontWeight: FontWeight.bold,
                          fontSize: 12
                        ),
                      ),
                    ],
                  ),
                ),
                
                // Action Button
                if (isPending)
                  ElevatedButton.icon(
                    onPressed: () => _showReplyDialog(appeal['id'], studentName),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryBlue,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      elevation: 0,
                    ),
                    icon: const Icon(Icons.reply_rounded, size: 18),
                    label: const Text("Javob berish"),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _formatDate(String? iso) {
    if (iso == null) return "";
    try {
      final dt = DateTime.parse(iso);
      final now = DateTime.now();
      if (dt.year == now.year && dt.month == now.month && dt.day == now.day) {
        return "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
      }
      return "${dt.day}.${dt.month.toString().padLeft(2, '0')}";
    } catch (_) {
      return "";
    }
  }
}
