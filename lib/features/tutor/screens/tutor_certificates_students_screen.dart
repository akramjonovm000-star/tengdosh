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
    _loadStudents();
  }

  Future<void> _loadStudents() async {
    setState(() => _isLoading = true);
    final students = await _dataService.getTutorGroupCertificateDetails(widget.groupNumber);
    if (mounted) {
      setState(() {
        _students = students ?? [];
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    List<dynamic> filtered = _students.where((s) {
      final name = (s['full_name'] ?? "").toString().toLowerCase();
      final hemisId = (s['hemis_id'] ?? "").toString().toLowerCase();
      return name.contains(_searchQuery.toLowerCase()) || 
             hemisId.contains(_searchQuery.toLowerCase());
    }).toList();

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: Text("Guruh: ${widget.groupNumber}", style: const TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        foregroundColor: Colors.black87,
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              onChanged: (v) => setState(() => _searchQuery = v),
              decoration: InputDecoration(
                hintText: "Talaba ismini qidiring...",
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
          
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : filtered.isEmpty
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        onRefresh: _loadStudents,
                        child: ListView.separated(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          itemCount: filtered.length,
                          separatorBuilder: (context, index) => const SizedBox(height: 12),
                          itemBuilder: (context, index) {
                            final student = filtered[index];
                            final count = student['certificate_count'] ?? 0;
                            
                            return Container(
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(20),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.02),
                                    blurRadius: 10,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: ListTile(
                                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                                leading: Hero(
                                  tag: "student_${student['id']}",
                                  child: Container(
                                    width: 52,
                                    height: 52,
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      border: Border.all(color: AppTheme.primaryBlue.withOpacity(0.1), width: 2),
                                    ),
                                    child: CircleAvatar(
                                      backgroundColor: Colors.grey[100],
                                      backgroundImage: student['image'] != null
                                          ? CachedNetworkImageProvider(student['image'])
                                          : null,
                                      child: student['image'] == null
                                          ? Icon(Icons.person, color: Colors.grey[400])
                                          : null,
                                    ),
                                  ),
                                ),
                                title: Text(
                                  student['full_name'] ?? "",
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                ),
                                subtitle: Padding(
                                  padding: const EdgeInsets.only(top: 4),
                                  child: Text(
                                    "ID: ${student['hemis_id'] ?? student['id']}",
                                    style: TextStyle(color: Colors.grey[500], fontSize: 13),
                                  ),
                                ),
                                trailing: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: count > 0 ? Colors.green[50] : Colors.grey[50],
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        Icons.workspace_premium_rounded, 
                                        size: 14, 
                                        color: count > 0 ? Colors.green : Colors.grey[400]
                                      ),
                                      const SizedBox(width: 4),
                                      Text(
                                        count.toString(),
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          color: count > 0 ? Colors.green : Colors.grey[600]
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                  onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => TutorStudentCertificatesScreen(
                                        studentId: student['id'],
                                        studentName: student['full_name'] ?? "",
                                      ),
                                    ),
                                  ).then((_) => _loadStudents());
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

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.person_search_rounded, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          const Text("Talabalar topilmadi", style: TextStyle(color: Colors.grey, fontSize: 16, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
