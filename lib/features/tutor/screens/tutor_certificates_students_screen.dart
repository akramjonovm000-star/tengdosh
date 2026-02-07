import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'tutor_student_certificates_screen.dart';

class TutorCertificatesStudentsScreen extends StatefulWidget {
  final String groupNumber;
  const TutorCertificatesStudentsScreen({super.key, required this.groupNumber});

  @override
  State<TutorCertificatesStudentsScreen> createState() => _TutorCertificatesStudentsScreenState();
}

class _TutorCertificatesStudentsScreenState extends State<TutorCertificatesStudentsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _students = [];
  String _searchQuery = "";

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final data = await _dataService.getTutorGroupCertificateDetails(widget.groupNumber);
    if (mounted) {
      setState(() {
        _students = data ?? [];
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    List<dynamic> filtered = _students.where((s) {
      return s['full_name'].toString().toLowerCase().contains(_searchQuery.toLowerCase());
    }).toList();

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text("Guruh: ${widget.groupNumber}", style: const TextStyle(fontSize: 18)),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              decoration: InputDecoration(
                hintText: "Talaba ismini qidiring...",
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Colors.grey[300]!),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Colors.grey[200]!),
                ),
                filled: true,
                fillColor: Colors.white,
              ),
              onChanged: (v) => setState(() => _searchQuery = v),
            ),
          ),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : filtered.isEmpty
                    ? const Center(child: Text("Talabalar topilmadi"))
                    : RefreshIndicator(
                        onRefresh: _loadData,
                        child: ListView.builder(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          itemCount: filtered.length,
                          itemBuilder: (context, index) {
                            final s = filtered[index];
                            final certCount = s['certificate_count'] ?? 0;

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                                side: BorderSide(color: Colors.grey[100]!),
                              ),
                              elevation: 0,
                              child: ListTile(
                                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                leading: CircleAvatar(
                                  radius: 24,
                                  backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                                  backgroundImage: s['image'] != null && s['image'].toString().isNotEmpty 
                                      ? CachedNetworkImageProvider(s['image']) 
                                      : null,
                                  child: (s['image'] == null || s['image'].toString().isEmpty) 
                                      ? const Icon(Icons.person, color: AppTheme.primaryBlue) 
                                      : null,
                                ),
                                title: Text(s['full_name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                subtitle: Text("Sertifikatlar: $certCount", style: TextStyle(color: (certCount > 0 ? Colors.green : Colors.grey), fontWeight: FontWeight.w500)),
                                trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Colors.grey),
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => TutorStudentCertificatesScreen(
                                        studentId: s['id'],
                                        studentName: s['full_name'],
                                      ),
                                    ),
                                  ).then((_) => _loadData());
                                },
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
}
