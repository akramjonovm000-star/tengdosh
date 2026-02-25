import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../services/yetakchi_service.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

class YetakchiAnnouncementsScreen extends StatefulWidget {
  const YetakchiAnnouncementsScreen({Key? key}) : super(key: key);

  @override
  State<YetakchiAnnouncementsScreen> createState() => _YetakchiAnnouncementsScreenState();
}

class _YetakchiAnnouncementsScreenState extends State<YetakchiAnnouncementsScreen> {
  final YetakchiService _service = YetakchiService();
  final TextEditingController _contentCtrl = TextEditingController();
  File? _imageFile;
  bool _isSubmitting = false;

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);
    if (pickedFile != null) {
      setState(() {
        _imageFile = File(pickedFile.path);
      });
    }
  }

  Future<void> _submitAnnouncement() async {
    if (_contentCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("E'lon matnini kiriting!")));
      return;
    }

    setState(() => _isSubmitting = true);
    final success = await _service.createAnnouncement(_contentCtrl.text.trim(), imagePath: _imageFile?.path);
    
    setState(() => _isSubmitting = false);
    
    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("E'lon muvaffaqiyatli yuborildi!")));
      Navigator.pop(context);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("E'lon yuborishda xatolik yuz berdi.")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Yangi E'lon", style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      backgroundColor: Colors.grey[50],
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Talabalar uchun yangiliklar markazi", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 16),
            
            TextField(
              controller: _contentCtrl,
              maxLines: 6,
              decoration: InputDecoration(
                hintText: "E'lon haqida batafsil ma'lumot kiriting...",
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey[300]!)),
              ),
            ),
            const SizedBox(height: 16),
            
            _imageFile != null
                ? Stack(
                    children: [
                      Container(
                        height: 200,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12),
                          image: DecorationImage(image: FileImage(_imageFile!), fit: BoxFit.cover),
                        ),
                      ),
                      Positioned(
                        top: 8,
                        right: 8,
                        child: IconButton(
                          icon: const Icon(Icons.close, color: Colors.black),
                          style: IconButton.styleFrom(backgroundColor: Colors.white),
                          onPressed: () => setState(() => _imageFile = null),
                        )
                      )
                    ],
                  )
                : OutlinedButton.icon(
                    onPressed: _pickImage,
                    icon: const Icon(Icons.image),
                    label: const Text("Rasm qo'shish (ixtiyoriy)"),
                    style: OutlinedButton.styleFrom(
                       padding: const EdgeInsets.all(16),
                       shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  
            const SizedBox(height: 32),
            
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isSubmitting ? null : _submitAnnouncement,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryBlue,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))
                ),
                child: _isSubmitting 
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text("Yuborish", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            )
          ]
        )
      )
    );
  }
}
