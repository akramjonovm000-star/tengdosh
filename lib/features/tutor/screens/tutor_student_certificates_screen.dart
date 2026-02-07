import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';

class TutorStudentCertificatesScreen extends StatefulWidget {
  final int studentId;
  final String studentName;
  const TutorStudentCertificatesScreen({super.key, required this.studentId, required this.studentName});

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
    final data = await _dataService.getTutorStudentCertificates(widget.studentId);
    if (mounted) {
      setState(() {
        _certificates = data ?? [];
        _isLoading = false;
      });
    }
  }

  Future<void> _downloadCertificate(int certId) async {
    final success = await _dataService.sendTutorCertificateToMe(certId);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? "Sertifikat Telegramingizga yuborildi" : "Xatolik yuz berdi"),
          backgroundColor: success ? Colors.green : Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text(widget.studentName, style: const TextStyle(fontSize: 16)),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _certificates.isEmpty
              ? const Center(child: Text("Sertifikatlar yuklanmagan"))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _certificates.length,
                  itemBuilder: (context, index) {
                    final cert = _certificates[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                        side: BorderSide(color: Colors.grey[100]!),
                      ),
                      elevation: 0,
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                const Icon(Icons.workspace_premium_rounded, color: Colors.amber, size: 28),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    cert['title'] ?? "Sertifikat",
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              "Sana: ${cert['created_at'].toString().split('T')[0]}",
                              style: TextStyle(color: Colors.grey[500], fontSize: 13),
                            ),
                            const SizedBox(height: 16),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton.icon(
                                onPressed: () => _downloadCertificate(cert['id']),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.primaryBlue,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                  elevation: 0,
                                ),
                                icon: const Icon(Icons.telegram, size: 20),
                                label: const Text("Telegramda yuklab olish"),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
