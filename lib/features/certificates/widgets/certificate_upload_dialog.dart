import 'dart:async';
import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';

class CertificateUploadDialog extends StatefulWidget {
  final VoidCallback onUploadSuccess;

  const CertificateUploadDialog({super.key, required this.onUploadSuccess});

  @override
  State<CertificateUploadDialog> createState() => _CertificateUploadDialogState();
}

class _CertificateUploadDialogState extends State<CertificateUploadDialog> {
  final DataService _dataService = DataService();
  final String _sessionId = const Uuid().v4().substring(0, 8).toUpperCase();
  
  final TextEditingController _titleController = TextEditingController();
  
  bool _isInitiated = false;
  bool _isReceived = false;
  bool _isSaving = false;
  bool _isLoading = false;
  
  Timer? _pollingTimer;

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _initiateUpload() async {
    if (_titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Iltimos, sertifikat nomini kiriting")),
      );
      return;
    }

    setState(() => _isLoading = true);

    final result = await _dataService.initiateCertificateUpload(
      sessionId: _sessionId,
      title: _titleController.text.trim(),
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
      }
    }
  }

  void _startPolling() {
    _pollingTimer?.cancel();

    // Immediate initial check
    _dataService.checkCertUploadStatus(_sessionId).then((status) {
      if (status['status'] == 'uploaded' && mounted) {
        _pollingTimer?.cancel();
        setState(() {
          _isReceived = true;
        });
      }
    });

    _pollingTimer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      final status = await _dataService.checkCertUploadStatus(_sessionId);
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
    final result = await _dataService.finalizeCertUpload(_sessionId);
    if (mounted) {
      setState(() => _isSaving = false);
      if (result['success'] == true) {
        widget.onUploadSuccess();
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Sertifikat muvaffaqiyatli saqlandi!"), backgroundColor: Colors.green),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? "Saqlashda xatolik"), backgroundColor: Colors.red),
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
              const Text("Sertifikat yuklash", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close)),
            ],
          ),
          const SizedBox(height: 20),
          
          if (!_isInitiated) ...[
            TextField(
              controller: _titleController,
              decoration: InputDecoration(
                labelText: "Sertifikat nomi",
                hintText: "Masalan: IELTS, IT-Park va h.k.",
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                prefixIcon: const Icon(Icons.workspace_premium_rounded),
              ),
            ),
            const SizedBox(height: 24),
            _buildActionButton(
              onPressed: _isLoading ? null : _initiateUpload,
              label: _isLoading ? "Yuborilmoqda..." : "Telegram orqali yuklash",
              icon: Icons.telegram_rounded,
              color: AppTheme.primaryBlue,
            ),
          ] else ...[
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
                          _isReceived ? "Sertifikat qabul qilindi!" : "Botni kuting...",
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
                            : "Telegram botga sertifikatni yuboring",
                          style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (!_isReceived) ...[
                const SizedBox(height: 20),
                const LinearProgressIndicator(minHeight: 6, borderRadius: BorderRadius.all(Radius.circular(3))),
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
