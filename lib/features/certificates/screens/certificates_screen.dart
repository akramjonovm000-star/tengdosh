import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

import '../../../core/services/data_service.dart';

class CertificatesScreen extends StatefulWidget {
  const CertificatesScreen({super.key});

  @override
  State<CertificatesScreen> createState() => _CertificatesScreenState();
}

class _CertificatesScreenState extends State<CertificatesScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _certificates = [];

  @override
  void initState() {
    super.initState();
    _loadCertificates();
  }

  Future<void> _loadCertificates() async {
    setState(() => _isLoading = true);
    final docs = await _dataService.getCertificates();
    if (mounted) {
      setState(() {
        _certificates = docs;
        _isLoading = false;
      });
    }
  }

  Future<bool> _initiateUpload(String title) async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Botga yuklash so'rovi yuborilmoqda...")),
    );
    
    final msg = await _dataService.initiateCertificateUpload(title);
    if (mounted && msg != null) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg),
          backgroundColor: msg.toLowerCase().contains("xato") ? Colors.red : AppTheme.primaryBlue,
          duration: const Duration(seconds: 4),
        ),
      );
      return !msg.toLowerCase().contains("xato");
    }
    return false;
  }

  void _showUploadForm() {
    final TextEditingController titleController = TextEditingController();
    bool isSubmitting = false;
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => StatefulBuilder(
        builder: (context, setModalState) => Padding(
          padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
          child: Container(
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            ),
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("Sertifikat yuklash", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 20),
                TextField(
                  controller: titleController,
                  enabled: !isSubmitting,
                  decoration: InputDecoration(
                    labelText: "Sertifikat nomi",
                    hintText: "Masalan: IELTS Certificate",
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    prefixIcon: const Icon(Icons.workspace_premium_rounded),
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 54,
                  child: OutlinedButton.icon(
                    onPressed: isSubmitting ? null : () async {
                      if (titleController.text.trim().isEmpty) {
                         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Iltimos, sertifikat nomini kiriting")));
                         return;
                      }
                      
                      setModalState(() => isSubmitting = true);
                      final success = await _initiateUpload(titleController.text.trim());
                      if (mounted) {
                        if (success) {
                           Navigator.pop(context);
                        } else {
                           setModalState(() => isSubmitting = false);
                        }
                      }
                    },
                    icon: isSubmitting 
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primaryBlue))
                      : const Icon(Icons.telegram_rounded, color: AppTheme.primaryBlue),
                    label: Text(isSubmitting ? "Yuborilmoqda..." : "Telegram orqali yuklash"),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: AppTheme.primaryBlue),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  height: 54,
                  child: ElevatedButton(
                    onPressed: isSubmitting ? null : () {
                      Navigator.pop(context);
                      _loadCertificates();
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: const Text("Ro'yxatni yangilash", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _confirmDelete(int certId, String title) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Sertifikatni o'chirish"),
        content: Text("Rostdan ham '$title' sertifikatini o'chirmoqchimisiz?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("Bekor qilish")),
          TextButton(
            onPressed: () => Navigator.pop(context, true), 
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text("O'chirish"),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _deleteCert(certId);
    }
  }

  Future<void> _deleteCert(int certId) async {
    final success = await _dataService.deleteCertificate(certId);
    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Sertifikat muvaffaqiyatli o'chirildi"), backgroundColor: Colors.green));
        _loadCertificates();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("O'chirishda xatolik yuz berdi"), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _sendToBot(int certId) async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Sertifikat botga yuborilmoqda...")),
    );
    
    final msg = await _dataService.sendCertificateToBot(certId);
    if (mounted && msg != null) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg),
          backgroundColor: msg.toLowerCase().contains("xato") ? Colors.red : Colors.green,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Sertifikatlar", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: RefreshIndicator(
        onRefresh: _loadCertificates,
        color: AppTheme.primaryBlue,
        child: _isLoading && _certificates.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_certificates.isEmpty) {
      return Stack(
        children: [
          ListView(), // For pull-to-refresh
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.workspace_premium_outlined, size: 80, color: Colors.grey[200]),
                const SizedBox(height: 16),
                Text(
                  "Sertifikatlar yo'q",
                  style: TextStyle(color: Colors.grey[400], fontSize: 16, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                Text(
                  "Hali hech qanday sertifikat yuklanmagan",
                  style: TextStyle(color: Colors.grey[400], fontSize: 13),
                ),
              ],
            ),
          ),
          Positioned(bottom: 0, left: 0, right: 0, child: _buildBottomButton()),
        ],
      );
    }

    return Column(
      children: [
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.all(20),
            itemCount: _certificates.length,
            separatorBuilder: (context, index) => const SizedBox(height: 16),
            itemBuilder: (context, index) => _buildCertificateCard(_certificates[index]),
          ),
        ),
        _buildBottomButton(),
      ],
    );
  }

  Widget _buildCertificateCard(dynamic cert) {
    // Generate a consistent color based on title hash for variety
    final colorIndex = (cert['id'] ?? 0) as int;
    final colors = [Colors.blue, Colors.green, Colors.orange, Colors.purple, Colors.red];
    final color = colors[colorIndex % colors.length];

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 15,
            offset: const Offset(0, 5),
          )
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () => _sendToBot(cert['id']),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Icon(Icons.workspace_premium_rounded, color: color, size: 30),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        cert['title'] ?? "Sertifikat",
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Icon(Icons.calendar_today_rounded, size: 12, color: Colors.grey[500]),
                          const SizedBox(width: 4),
                          Text(
                            cert['created_at'] ?? "",
                            style: TextStyle(color: Colors.grey[500], fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.red[50],
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: IconButton(
                        icon: const Icon(Icons.delete_outline_rounded, color: Colors.redAccent),
                        onPressed: () => _confirmDelete(cert['id'], cert['title'] ?? "Sertifikat"),
                        tooltip: "O'chirish",
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.blue[50], 
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: IconButton(
                        icon: const Icon(Icons.telegram_rounded, color: AppTheme.primaryBlue),
                        onPressed: () => _sendToBot(cert['id']),
                        tooltip: "Botda ko'rish",
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBottomButton() {
    return Container(
      padding: const EdgeInsets.all(20),
      color: Colors.transparent,
      child: SafeArea(
        child: SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: _showUploadForm,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 4,
              shadowColor: AppTheme.primaryBlue.withOpacity(0.3),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.add_task_rounded, color: Colors.white),
                SizedBox(width: 10),
                Text(
                  "Sertifikat yuklash",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
