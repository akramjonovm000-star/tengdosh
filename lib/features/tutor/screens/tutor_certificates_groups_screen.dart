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
  String _searchQuery = "";

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
    List<dynamic> filtered = _stats.where((s) {
      return s['group_number'].toString().toLowerCase().contains(_searchQuery.toLowerCase());
    }).toList();

    int totalStudents = 0;
    int totalUploaded = 0;
    for (var s in _stats) {
      totalStudents += (s['total_students'] as num? ?? 0).toInt();
      totalUploaded += (s['uploaded_students'] as num? ?? 0).toInt();
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text("Guruhlar ro'yxati", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        foregroundColor: Colors.black87,
      ),
      body: Column(
        children: [
          // Header Stats
          if (!_isLoading && _stats.isNotEmpty)
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppTheme.primaryBlue, Color(0xFF1E40AF)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.primaryBlue.withOpacity(0.3),
                    blurRadius: 12,
                    offset: const Offset(0, 6),
                  ),
                ],
              ),
              child: Row(
                children: [
                  _buildHeaderStat("Jami talabalar", totalStudents.toString(), Icons.people_outline),
                  Container(width: 1, height: 40, color: Colors.white24),
                  _buildHeaderStat("Yuklangan", totalUploaded.toString(), Icons.document_scanner_outlined),
                  Container(width: 1, height: 40, color: Colors.white24),
                  _buildHeaderStat("Foiz", "${totalStudents > 0 ? (totalUploaded * 100 ~/ totalStudents) : 0}%", Icons.percent),
                ],
              ),
            ),
          
          // Search Bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: TextField(
              onChanged: (v) => setState(() => _searchQuery = v),
              decoration: InputDecoration(
                hintText: "Guruhni qidiring...",
                prefixIcon: const Icon(Icons.search, color: Colors.grey),
                filled: true,
                fillColor: Colors.white,
                contentPadding: const EdgeInsets.symmetric(vertical: 0),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide.none,
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(color: Colors.grey.withOpacity(0.1)),
                ),
              ),
            ),
          ),
          
          const SizedBox(height: 8),
          
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : filtered.isEmpty
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        onRefresh: _loadStats,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: filtered.length,
                          itemBuilder: (context, index) {
                            final item = filtered[index];
                            final total = item['total_students'] ?? 0;
                            final uploaded = item['uploaded_students'] ?? 0;
                            final percent = total > 0 ? (uploaded / total) : 0.0;

                            return Container(
                              margin: const EdgeInsets.only(bottom: 16),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: Colors.grey.withOpacity(0.08)),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.02),
                                    blurRadius: 10,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: Material(
                                color: Colors.transparent,
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
                                  borderRadius: BorderRadius.circular(20),
                                  child: Padding(
                                    padding: const EdgeInsets.all(16),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Container(
                                              padding: const EdgeInsets.all(10),
                                              decoration: BoxDecoration(
                                                color: AppTheme.primaryBlue.withOpacity(0.1),
                                                borderRadius: BorderRadius.circular(12),
                                              ),
                                              child: const Icon(Icons.class_rounded, color: AppTheme.primaryBlue, size: 24),
                                            ),
                                            const SizedBox(width: 12),
                                            Text(
                                              "Guruh: ${item['group_number']}",
                                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                                            ),
                                            const Spacer(),
                                            const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: Colors.grey),
                                          ],
                                        ),
                                        const SizedBox(height: 20),
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            Text(
                                              "Sertifikati borlar: $uploaded / $total",
                                              style: TextStyle(color: Colors.grey[600], fontSize: 13, fontWeight: FontWeight.w500),
                                            ),
                                            Text(
                                              "${(percent * 100).toInt()}%",
                                              style: TextStyle(
                                                color: percent == 1.0 ? Colors.green : Colors.amber[700],
                                                fontWeight: FontWeight.bold,
                                                fontSize: 14,
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 10),
                                        ClipRRect(
                                          borderRadius: BorderRadius.circular(10),
                                          child: LinearProgressIndicator(
                                            value: percent,
                                            backgroundColor: Color(0xFFEEF2F6),
                                            color: percent == 1.0 ? Colors.green : AppTheme.primaryBlue,
                                            minHeight: 8,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeaderStat(String label, String value, IconData icon) {
    return Expanded(
      child: Column(
        children: [
          Icon(icon, color: Colors.white, size: 20),
          const SizedBox(height: 8),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11)),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.folder_open_rounded, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          const Text("Guruhlar topilmadi", style: TextStyle(color: Colors.grey, fontSize: 16, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
