import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';

class TutorStudentCertificatesScreen extends StatefulWidget {
  final int studentId;
  final String studentName;
  const TutorStudentCertificatesScreen({
    super.key, 
    required this.studentId,
    required this.studentName,
  });

  @override
  State<TutorStudentCertificatesScreen> createState() => _TutorStudentCertificatesScreenState();
}

class _TutorStudentCertificatesScreenState extends State<TutorStudentCertificatesScreen> {
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
    final certs = await _dataService.getStudentCertificatesForTutor(widget.studentId);
    if (mounted) {
      setState(() {
        _certificates = certs ?? [];
        _isLoading = false;
      });
    }
  }

  Future<void> _downloadViaTelegram(int certId) async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Telegram botga yuborilmoqda...")),
    );
    
    final msg = await _dataService.downloadStudentCertificateForTutor(certId);
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
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Sertifikatlar", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(widget.studentName, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.normal, color: Colors.black54)),
          ],
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        foregroundColor: Colors.black87,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _certificates.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  onRefresh: _loadCertificates,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(20),
                    itemCount: _certificates.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 16),
                    itemBuilder: (context, index) {
                      final cert = _certificates[index];
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
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Row(
                            children: [
                              Container(
                                width: 50,
                                height: 50,
                                decoration: BoxDecoration(
                                  color: AppTheme.primaryBlue.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Icon(Icons.workspace_premium_rounded, color: AppTheme.primaryBlue),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      cert['title'] ?? "Sertifikat",
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      cert['created_at'] ?? "",
                                      style: TextStyle(color: Colors.grey[500], fontSize: 12),
                                    ),
                                  ],
                                ),
                              ),
                              ElevatedButton.icon(
                                onPressed: () => _downloadViaTelegram(cert['id']),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.primaryBlue,
                                  foregroundColor: Colors.white,
                                  elevation: 0,
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 0),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                icon: const Icon(Icons.telegram_rounded, size: 18),
                                label: const Text("Bot", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.workspace_premium_outlined, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          const Text("Sertifikatlar yuklanmagan", style: TextStyle(color: Colors.grey, fontSize: 16, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
