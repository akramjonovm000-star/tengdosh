import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'tutor_certificates_students_screen.dart';

class TutorCertificatesGroupsScreen extends StatefulWidget {
  const TutorCertificatesGroupsScreen({super.key});

  @override
  State<TutorCertificatesGroupsScreen> createState() => _TutorCertificatesGroupsScreenState();
}

class _TutorCertificatesGroupsScreenState extends State<TutorCertificatesGroupsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _stats = [];

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() => _isLoading = true);
    final stats = await _dataService.getTutorCertificateStats();
    if (mounted) {
      setState(() {
        _stats = stats ?? [];
        _isLoading = false;
      });
      
      if (stats == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Xatolik: Ma'lumotlarni yuklab bo'lmadi"), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Sertifikatlar statistikasi"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _stats.isEmpty
              ? const Center(child: Text("Sizga biriktirilgan guruhlar yo'q"))
              : RefreshIndicator(
                  onRefresh: _loadStats,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _stats.length,
                    itemBuilder: (context, index) {
                      final item = _stats[index];
                      final total = item['total_students'] ?? 0;
                      final uploaded = item['uploaded_students'] ?? 0;
                      final percent = total > 0 ? (uploaded / total) : 0.0;

                      return Card(
                        margin: const EdgeInsets.only(bottom: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                          side: BorderSide(color: Colors.grey.withOpacity(0.2)),
                        ),
                        elevation: 0,
                        child: InkWell(
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => TutorCertificatesStudentsScreen(
                                  groupNumber: item['group_number'],
                                ),
                              ),
                            ).then((_) => _loadStats());
                          },
                          borderRadius: BorderRadius.circular(16),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      "Guruh: ${item['group_number']}",
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                                    ),
                                    const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Colors.grey),
                                  ],
                                ),
                                const SizedBox(height: 16),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      "Sertifikati borlar: $uploaded / $total",
                                      style: TextStyle(color: Colors.grey[700], fontWeight: FontWeight.w500),
                                    ),
                                    Text(
                                      "${(percent * 100).toInt()}%",
                                      style: const TextStyle(color: Colors.amber, fontWeight: FontWeight.bold),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(8),
                                  child: LinearProgressIndicator(
                                    value: percent,
                                    backgroundColor: Colors.grey[200],
                                    color: percent == 1.0 ? Colors.green : Colors.amber,
                                    minHeight: 8,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
