import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/features/student_module/screens/public_profile_screen.dart'; // Reuse existing public profile

class TutorStudentsScreen extends StatefulWidget {
  final String groupNumber;
  const TutorStudentsScreen({super.key, required this.groupNumber});

  @override
  State<TutorStudentsScreen> createState() => _TutorStudentsScreenState();
}

class _TutorStudentsScreenState extends State<TutorStudentsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _students = [];

  @override
  void initState() {
    super.initState();
    _loadStudents();
  }

  Future<void> _loadStudents() async {
    try {
      final students = await _dataService.getTutorStudents(group: widget.groupNumber);
      if (mounted) {
        setState(() {
          _students = students;
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint("Error loading students: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text("Guruh: ${widget.groupNumber}"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _students.isEmpty
              ? const Center(child: Text("Talabalar topilmadi"))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _students.length,
                  itemBuilder: (context, index) {
                    final student = _students[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 0,
                      color: Colors.white,
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundImage: student['image'] != null
                              ? CachedNetworkImageProvider(student['image'])
                              : null,
                          child: student['image'] == null
                              ? const Icon(Icons.person)
                              : null,
                        ),
                        title: Text(
                          student['full_name'] ?? 'Talaba',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        subtitle: Text(student['hemis_id'] ?? ""),
                        onTap: () {
                           if (student['id'] != null) {
                               // Assuming PublicProfileScreen takes studentId
                               // We might need to check its implementation
                               /*
                               Navigator.push(
                                  context, 
                                  MaterialPageRoute(builder: (_) => PublicProfileScreen(studentId: student['id']))
                               );
                               */
                           }
                        },
                      ),
                    );
                  },
                ),
    );
  }
}
