import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/features/community/screens/user_profile_screen.dart';
import 'package:cached_network_image/cached_network_image.dart';

class TutorStudentsScreen extends StatefulWidget {
  final String? groupNumber;

  const TutorStudentsScreen({super.key, this.groupNumber});

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
        title: Text(widget.groupNumber != null ? "Guruh: ${widget.groupNumber}" : "Barcha Talabalar"),
        centerTitle: false,
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
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: BorderSide(color: Colors.grey.withOpacity(0.2)),
                      ),
                      child: InkWell(
                        onTap: () {
                          // Extract ID safely
                          String authId = "0";
                          if (student['id'] != null) authId = student['id'].toString();
                          
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => UserProfileScreen(
                                authorId: authId,
                                authorName: student['full_name'] ?? "Talaba",
                                authorUsername: student['full_name'] ?? "student", 
                                // Used full_name as fallback username for display
                                authorAvatar: student['image'] ?? "",
                                authorRole: "student",
                              ),
                            ),
                          );
                        },
                        borderRadius: BorderRadius.circular(12),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            children: [
                              CircleAvatar(
                                radius: 25,
                                backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                                child: student['image'] != null && student['image'].isNotEmpty
                                    ? ClipOval(
                                        child: CachedNetworkImage(
                                          imageUrl: student['image'],
                                          width: 50,
                                          height: 50,
                                          fit: BoxFit.cover,
                                          placeholder: (c, u) => const Icon(Icons.person, color: AppTheme.primaryBlue),
                                          errorWidget: (c, u, e) => const Icon(Icons.person, color: AppTheme.primaryBlue),
                                        ),
                                      )
                                    : const Icon(Icons.person, color: AppTheme.primaryBlue),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      student['full_name'] ?? "Ism Familiya",
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      "Guruh: ${student['group'] ?? 'Noma\'lum'}",
                                      style: TextStyle(color: Colors.grey[600], fontSize: 13),
                                    ),
                                  ],
                                ),
                              ),
                              const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Colors.grey),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
