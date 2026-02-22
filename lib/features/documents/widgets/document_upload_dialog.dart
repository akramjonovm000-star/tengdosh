import 'dart:async';
import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';

class DocumentUploadDialog extends StatefulWidget {
  final VoidCallback onUploadSuccess;
  final List<String> existingTitles;

  const DocumentUploadDialog({super.key, required this.onUploadSuccess, this.existingTitles = const []});

  @override
  State<DocumentUploadDialog> createState() => _DocumentUploadDialogState();
}

class _DocumentUploadDialogState extends State<DocumentUploadDialog> {
  final DataService _dataService = DataService();
  final String _sessionId = const Uuid().v4().substring(0, 8).toUpperCase();
  
  String _selectedCategory = "passport";
  final TextEditingController _titleController = TextEditingController();
  
  bool _isInitiated = false;
  bool _isReceived = false;
  bool _isSaving = false;
  bool _isLoading = false;
  
  Timer? _pollingTimer;

  final List<Map<String, dynamic>> _categories = [
    {"id": "passport", "name": "Passport", "icon": Icons.credit_card_rounded},
    {"id": "diplom", "name": "Diplom", "icon": Icons.school_rounded},
    {"id": "rezyume", "name": "Rezyume", "icon": Icons.work_outline_rounded},
    {"id": "obyektivka", "name": "Obyektivka", "icon": Icons.assignment_ind_rounded},
    {"id": "boshqa", "name": "Boshqa", "icon": Icons.folder_shared_rounded},
  ];

  List<Map<String, dynamic>> get _availableCategories {
    return _categories.where((cat) {
      if (['passport', 'diplom', 'rezyume', 'obyektivka'].contains(cat['id'])) {
        return !widget.existingTitles.any((title) => title.toLowerCase() == cat['name'].toString().toLowerCase());
      }
      return true;
    }).toList();
  }

  @override
  void initState() {
    super.initState();
    if (_availableCategories.isNotEmpty) {
      _selectedCategory = _availableCategories.first['id'] as String;
    }
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _initiateUpload() async {
    if (_selectedCategory == "boshqa" && _titleController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Iltimos, hujjat nomini kiriting")),
      );
      return;
    }

    setState(() => _isLoading = true);

    final title = _selectedCategory == "boshqa" ? _titleController.text : _categories.firstWhere((c) => c['id'] == _selectedCategory)['name'];

    try {
      final result = await _dataService.initiateDocUpload(
        sessionId: _sessionId,
        category: _selectedCategory,
        title: title,
      );

      if (mounted) {
        setState(() => _isLoading = false);
        
        // [SMART UPLOAD LOGIC]
        if (result['success'] == true || result['requires_auth'] == true) {
           // Success OR Auth Required -> We proceed to polling
           setState(() => _isInitiated = true);
           
           String urlToLaunch = "";
           if (result['requires_auth'] == true) {
             urlToLaunch = result['auth_link'];
           } else {
             urlToLaunch = result['bot_link'] ?? "https://t.me/talabahamkorbot";
           }
           
           // Launch Telegram
           if (await canLaunchUrl(Uri.parse(urlToLaunch))) {
             await launchUrl(Uri.parse(urlToLaunch), mode: LaunchMode.externalApplication);
           } else {
             ScaffoldMessenger.of(context).showSnackBar(
               const SnackBar(content: Text("Telegramni ochib bo'lmadi"), backgroundColor: Colors.orange),
             );
           }
           
           _startPolling();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(result['message'] ?? "Xatolik yuz berdi"), backgroundColor: Colors.red),
          );
        }
      }
    } catch (e) {
       if (mounted) setState(() => _isLoading = false);
       ScaffoldMessenger.of(context).showSnackBar(
         SnackBar(content: Text("Xatolik: $e"), backgroundColor: Colors.red),
       );
    }
  }

  void _startPolling() {
    _pollingTimer?.cancel();
    
    // Immediate initial check
    _dataService.checkDocUploadStatus(_sessionId).then((status) {
      if (status['status'] == 'uploaded' && mounted) {
        _pollingTimer?.cancel();
        setState(() {
          _isReceived = true;
        });
      }
    });

    _pollingTimer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      final status = await _dataService.checkDocUploadStatus(_sessionId);
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
    final result = await _dataService.finalizeDocUpload(_sessionId);
    if (mounted) {
      setState(() => _isSaving = false);
      if (result['success'] == true) {
        widget.onUploadSuccess();
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Hujjat muvaffaqiyatli saqlandi!"), backgroundColor: Colors.green),
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
              const Text("Hujjat yuklash", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close)),
            ],
          ),
          const SizedBox(height: 20),
          
          if (!_isInitiated) ...[
            const Text("Hujjat turini tanlang:", style: TextStyle(fontWeight: FontWeight.w600, color: Colors.grey)),
            const SizedBox(height: 12),
            _buildCategoryGrid(),
            if (_selectedCategory == "boshqa") ...[
              const SizedBox(height: 16),
              TextField(
                controller: _titleController,
                decoration: InputDecoration(
                  labelText: "Hujjat nomi",
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  prefixIcon: const Icon(Icons.edit_note_rounded),
                ),
              ),
            ],
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

  Widget _buildCategoryGrid() {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: _availableCategories.map((cat) {
        final isSelected = _selectedCategory == cat['id'];
        return InkWell(
          onTap: () => setState(() => _selectedCategory = cat['id']),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: isSelected ? AppTheme.primaryBlue : Colors.grey[100],
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: isSelected ? AppTheme.primaryBlue : Colors.grey[300]!),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(cat['icon'], color: isSelected ? Colors.white : Colors.grey[600], size: 18),
                const SizedBox(width: 8),
                Text(
                  cat['name'],
                  style: TextStyle(
                    color: isSelected ? Colors.white : Colors.grey[800],
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
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
                            : "Telegram botga hujjatni yuboring",
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
