import 'dart:async';
import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';

class FeedbackUploadDialog extends StatefulWidget {
  final String text;
  final String role;
  final bool isAnonymous;
  final VoidCallback onUploadSuccess;

  const FeedbackUploadDialog({
    super.key,
    required this.text,
    required this.role,
    required this.isAnonymous,
    required this.onUploadSuccess,
  });

  @override
  State<FeedbackUploadDialog> createState() => _FeedbackUploadDialogState();
}

class _FeedbackUploadDialogState extends State<FeedbackUploadDialog> {
  final DataService _dataService = DataService();
  final String _sessionId = const Uuid().v4().substring(0, 8).toUpperCase();
  
  bool _isInitiated = false;
  bool _isReceived = false;
  bool _isSaving = false;
  bool _isLoading = false;
  
  Timer? _pollingTimer;

  @override
  void initState() {
    super.initState();
    _initiateUpload();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }

  Future<void> _initiateUpload() async {
    setState(() => _isLoading = true);

    final result = await _dataService.initiateFeedbackUpload(
      sessionId: _sessionId,
      text: widget.text,
      role: widget.role,
      isAnonymous: widget.isAnonymous,
    );

    if (mounted) {
      setState(() => _isLoading = false);
      if (result['success'] == true) {
        setState(() => _isInitiated = true);
        _startPolling();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? "Xatolik yuz berdi"), backgroundColor: Colors.red),
        );
        Navigator.pop(context); // Close if initiation fails
      }
    }
  }

  void _startPolling() {
    _pollingTimer?.cancel();
    _pollingTimer = Timer.periodic(const Duration(seconds: 3), (timer) async {
      final status = await _dataService.checkFeedbackUploadStatus(_sessionId);
      if (status['status'] == 'uploaded') {
        timer.cancel();
        if (mounted) {
          setState(() {
            _isReceived = true;
          });
        }
      }
    });
  }

  Future<void> _finalize() async {
    setState(() => _isSaving = true);
    final result = await _dataService.createFeedback(
      text: widget.text,
      role: widget.role,
      isAnonymous: widget.isAnonymous,
      sessionId: _sessionId,
    );
    
    if (mounted) {
      setState(() => _isSaving = false);
      if (result['status'] == 'success') {
        widget.onUploadSuccess();
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Murojaat muvaffaqiyatli yuborildi!"), backgroundColor: Colors.green),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? "Yuborishda xatolik"), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("Murojaatga fayl biriktirish", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close)),
            ],
          ),
          const SizedBox(height: 20),
          
          if (!_isInitiated) 
            const Center(child: Padding(
              padding: EdgeInsets.all(20.0),
              child: CircularProgressIndicator(),
            ))
          else ...[
             _buildProgressView(),
             const SizedBox(height: 24),
             _buildActionButton(
              onPressed: _isReceived && !_isSaving ? _finalize : null,
              label: _isSaving ? "Saqlanmoqda..." : "Saqlash",
              icon: Icons.check_circle_rounded,
              color: Colors.green,
            ),
          ],
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildSummaryView() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.person_pin_circle_rounded, size: 18, color: AppTheme.primaryBlue),
              const SizedBox(width: 8),
              Text(
                "Kimga: ${widget.role.toUpperCase()}",
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              ),
              if (widget.isAnonymous) ...[
                const SizedBox(width: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(color: Colors.black87, borderRadius: BorderRadius.circular(4)),
                  child: const Text("ANONIM", style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                )
              ]
            ],
          ),
          const Divider(height: 24),
          Text(
            widget.text,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: Colors.grey[800], fontSize: 14),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressView() {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: _isReceived ? Colors.green[50] : Colors.blue[50],
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            children: [
              Row(
                children: [
                  Stack(
                    alignment: Alignment.center,
                    children: [
                      if (!_isReceived)
                        const SizedBox(width: 40, height: 40, child: CircularProgressIndicator(strokeWidth: 3)),
                      Icon(
                        _isReceived ? Icons.check_circle_rounded : Icons.telegram_rounded,
                        color: _isReceived ? Colors.green : AppTheme.primaryBlue,
                        size: 30,
                      ),
                    ],
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _isReceived ? "Fayl qabul qilindi!" : "Botni kuting...",
                          style: TextStyle(
                            fontSize: 16, 
                            fontWeight: FontWeight.bold,
                            color: _isReceived ? Colors.green[700] : Colors.blue[700],
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _isReceived 
                            ? "Saqlash tugmasini bosishingiz mumkin" 
                            : "Telegram botga faylni yuboring",
                          style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (!_isReceived) ...[
                const SizedBox(height: 20),
                const LinearProgressIndicator(
                  minHeight: 6, 
                  borderRadius: BorderRadius.all(Radius.circular(3)),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildActionButton({required VoidCallback? onPressed, required String label, required IconData icon, required Color color}) {
    return SizedBox(
      width: double.infinity,
      height: 54,
      child: ElevatedButton.icon(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: color,
          foregroundColor: Colors.white,
          disabledBackgroundColor: Colors.grey[300],
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          elevation: 0,
        ),
        icon: Icon(icon),
        label: Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
      ),
    );
  }
}
