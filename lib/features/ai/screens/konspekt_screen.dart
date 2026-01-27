import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/services.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';

class KonspektScreen extends StatefulWidget {
  const KonspektScreen({super.key});

  @override
  State<KonspektScreen> createState() => _KonspektScreenState();
}

class _KonspektScreenState extends State<KonspektScreen> {
  final TextEditingController _textController = TextEditingController();
  final DataService _dataService = DataService();
  
  File? _selectedFile;
  String? _result;
  bool _isLoading = false;

  Future<void> _pickFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'pptx', 'txt'],
      );

      if (result != null && result.files.single.path != null) {
        setState(() {
          _selectedFile = File(result.files.single.path!);
          _result = null; // Clear previous result
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Fayl tanlashda xatolik: $e")),
      );
    }
  }

  void _clearFile() {
    setState(() {
      _selectedFile = null;
    });
  }

  Future<void> _generateKonspekt() async {
    final text = _textController.text.trim();
    
    if (text.isEmpty && _selectedFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Iltimos, matn yozing yoki fayl tanlang.")),
      );
      return;
    }

    setState(() {
      _isLoading = true;
      _result = null;
    });

    try {
      final summary = await _dataService.summarizeContent(
        text: text.isNotEmpty ? text : null,
        filePath: _selectedFile?.path,
      );
      
      if (mounted) {
        setState(() {
          _result = summary;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _result = "Xatolik yuz berdi: $e";
          _isLoading = false;
        });
      }
    }
  }

  void _copyToClipboard() {
    if (_result != null) {
      Clipboard.setData(ClipboardData(text: _result!));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Nusxa olindi!")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Konspekt Yordamchi", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Instructions
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.withOpacity(0.1)),
              ),
              child: Column(
                children: [
                   const Icon(Icons.auto_awesome, color: AppTheme.primaryBlue, size: 30),
                   const SizedBox(height: 8),
                   const Text(
                     "Uzun matn yoki fayllarni lo'nda konspektga aylantiring.",
                     textAlign: TextAlign.center,
                     style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.w600),
                   ),
                   const SizedBox(height: 4),
                   Text(
                     "Qo'llab-quvvatlanadi: PDF, DOCX, PPTX, Matn",
                     style: TextStyle(color: Colors.grey[600], fontSize: 12),
                   ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Input Area
            if (_selectedFile == null)
              TextField(
                controller: _textController,
                maxLines: 6,
                decoration: InputDecoration(
                  hintText: "Matnni shu yerga yozing yoki fayl yuklang...",
                  hintStyle: TextStyle(color: Colors.grey[400]),
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                  contentPadding: const EdgeInsets.all(16),
                ),
              ),

            // Selected File View
            if (_selectedFile != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.green.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(color: Colors.green.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                      child: const Icon(Icons.insert_drive_file, color: Colors.green),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _selectedFile!.path.split('/').last,
                            style: const TextStyle(fontWeight: FontWeight.bold),
                            maxLines: 1, overflow: TextOverflow.ellipsis,
                          ),
                          Text(
                            "Yuklashga tayyor",
                            style: TextStyle(color: Colors.grey[500], fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    IconButton(icon: const Icon(Icons.close, color: Colors.red), onPressed: _clearFile)
                  ],
                ),
              ),

            const SizedBox(height: 16),

            // Buttons Row
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _selectedFile == null ? _pickFile : null, // Disable if file already selected
                    icon: const Icon(Icons.upload_file),
                    label: const Text("Fayl tanlash"),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 2,
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : _generateKonspekt,
                    icon: _isLoading 
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.summarize, color: Colors.white),
                    label: Text(
                      _isLoading ? "Tahlil qilinmoqda..." : "Konspekt qilish",
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryBlue,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 0,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 30),

            // Result Area
            if (_result != null) ...[
               const Row(
                 mainAxisAlignment: MainAxisAlignment.spaceBetween,
                 children: [
                   Text("Natija:", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                 ],
               ),
               const SizedBox(height: 10),
               Container(
                 width: double.infinity,
                 padding: const EdgeInsets.all(16),
                 decoration: BoxDecoration(
                   color: Colors.white,
                   borderRadius: BorderRadius.circular(16),
                   boxShadow: [
                     BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4))
                   ],
                 ),
                 child: Column(
                   crossAxisAlignment: CrossAxisAlignment.stretch,
                   children: [
                     Text(
                       _result!, 
                       style: const TextStyle(fontSize: 15, height: 1.5),
                     ),
                     const SizedBox(height: 16),
                     Align(
                       alignment: Alignment.centerRight,
                       child: TextButton.icon(
                         onPressed: _copyToClipboard, 
                         icon: const Icon(Icons.copy, size: 18), 
                         label: const Text("Nusxa olish")
                       ),
                     )
                   ],
                 ),
               ),
               const SizedBox(height: 40),
            ],
          ],
        ),
      ),
    );
  }
}
