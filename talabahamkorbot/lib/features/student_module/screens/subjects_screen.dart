import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import 'resources_screen.dart';

class SubjectsScreen extends StatefulWidget {
  const SubjectsScreen({super.key});

  @override
  State<SubjectsScreen> createState() => _SubjectsScreenState();
}

class _SubjectsScreenState extends State<SubjectsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _subjects = [];

  @override
  void initState() {
    super.initState();
    _loadSubjects();
  }

  Future<void> _loadSubjects() async {
    final data = await _dataService.getSubjects();
    if (mounted) {
      setState(() {
        _subjects = data;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Fanlar va Resurslar", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _subjects.isEmpty
              ? const Center(child: Text("Ma'lumot topilmadi"))
              : ListView.builder(
                  padding: const EdgeInsets.all(20),
                  itemCount: _subjects.length,
                  itemBuilder: (context, index) {
                    return _buildSubjectCard(_subjects[index]);
                  },
                ),
    );
  }

  Widget _buildSubjectCard(dynamic item) {
    final id = item['id']?.toString() ?? "";
    final name = item['name'] ?? "Fan nomi";
    final teachers = item['teachers'] as List? ?? [];
    final absentHours = item['absent_hours'] ?? 0;
    final grades = item['grades'] ?? {};
    
    final onVal = grades['ON']?['val_5'] ?? 0;
    final ynVal = grades['YN']?['val_5'] ?? 0;
    final ynRaw = grades['YN']?['raw'] ?? 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 24,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => ResourcesScreen(subjectId: id, subjectName: name),
              ),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Subject Name
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.blue.withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.library_books_rounded, color: Colors.blue, size: 20),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        name,
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF2D2D2D),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Teachers Section
                if (teachers.isNotEmpty) ...[
                  ...teachers.map((t) {
                    final role = t['role'];
                    final names = (t['names'] as List).join(", ");
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 4, left: 44),
                      child: Row(
                        children: [
                          const Icon(Icons.person_outline_rounded, size: 14, color: Colors.grey),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              "$role: $names",
                              style: const TextStyle(fontSize: 13, color: Colors.grey),
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                  const SizedBox(height: 12),
                ],

                // Footer: Grades & Attendance
                Padding(
                  padding: const EdgeInsets.only(left: 44),
                  child: Row(
                    children: [
                      // Grades
                      if ((grades['JN']?['raw'] ?? 0) > 0) ...[
                        _buildMiniScore("JN", grades['JN']?['val_5'] ?? 0, Colors.green),
                        const SizedBox(width: 8),
                        Text("·", style: TextStyle(color: Colors.grey.withOpacity(0.3))),
                        const SizedBox(width: 8),
                      ],
                      _buildMiniScore("ON", onVal, Colors.orange),
                      if (ynRaw > 0) ...[
                        const SizedBox(width: 8),
                        Text("·", style: TextStyle(color: Colors.grey.withOpacity(0.3))),
                        const SizedBox(width: 8),
                        _buildMiniScore("YN", ynVal, Colors.blue),
                      ],
                      const Spacer(),
                      // Attendance
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.red.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          "❌ $absentHours s",
                          style: const TextStyle(fontSize: 12, color: Colors.red, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMiniScore(String label, dynamic score, Color color) {
    return Row(
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(width: 4),
        Text(
          "$score/5",
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: color),
        ),
      ],
    );
  }
}
