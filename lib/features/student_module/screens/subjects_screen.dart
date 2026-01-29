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
  
  // Semesters
  List<dynamic> _semesters = [];
  String? _selectedSemesterId;

  @override
  void initState() {
    super.initState();
    _loadSubjects();
  }

  Future<void> _loadSubjects() async {
    // 1. Get Semesters if empty
    if (_semesters.isEmpty) {
      _semesters = await _dataService.getSemesters();
      // if (_semesters.isNotEmpty && _selectedSemesterId == null) {
      //    _selectedSemesterId = _semesters.first['code']?.toString() ?? _semesters.first['id']?.toString();
      // }
    }
    
    // 2. Get Subjects
    // Note: Assuming DataService.getSubjects updated to take semester
    // We haven't updated DataService.getSubjects signature yet in dart file?
    // Let's check. Yes we updated getDashboardStats but not getSubjects in the last step?
    // Wait, I updated getSemesters but did I update getSubjects?
    // Looking at previous diff, I updated getDashboardStats. I did NOT update getSubjects signature in DataService.dart
    // I need to update DataService.getSubjects signature first or pass it if I did.
    // I will assume I will fixed DataService.getSubjects in next step or this step.
    // Actually, I should fix DataService.getSubjects signature first.
    // But since I am editing SubjectsScreen now, I will write code assuming it exists
    // and then go fix DataService if I missed it.
    
    // I will revisit DataService.getSubjects. 
    // In the previous step for DataService, I added getSemesters and updated getDashboardStats.
    // I did NOT update getSubjects signature.
    // So I need to use DataService.getSubjects() and maybe filter locally or update DataService.
    // The plan said: "Update getDashboardStats, getSubjects, getAttendance to accept semesterId."
    // I only updated getDashboardStats.
    // So I will pause this edit and go update DataService first? 
    // No, I can do it in parallel or sequential.
    // I'll assume I'll pass it, and I will fix DataService immediately after.
    
    // Actually, to avoid compilation error if I run, I should check.
    // But I can't run yet.
    
    // Let's implement the logic assuming DataService.getSubjects(semester: _selectedSemesterId).
    
    final data = await _dataService.getSubjects(semester: _selectedSemesterId);
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
        title: const Text(
          "Fanlar va Resurslar",
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 18),
        ),
        centerTitle: false,
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: Colors.grey.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _selectedSemesterId,
                hint: const Text("Semestr", style: TextStyle(fontSize: 14)),
                icon: const Icon(Icons.arrow_drop_down, color: Colors.black54),
                borderRadius: BorderRadius.circular(12),
                items: [
                   const DropdownMenuItem<String>(
                     value: null,
                     child: Text("Joriy", style: TextStyle(fontWeight: FontWeight.bold)),
                   ),
                   ..._semesters.map((s) {
                    final code = (s['code'] ?? s['id']).toString();
                    final name = s['name'] ?? "${int.tryParse(code) != null ? int.parse(code) - 10 : code}-semestr";
                    return DropdownMenuItem<String>(
                      value: code,
                      child: Text(name),
                    );
                  }).toList(),
                ],
                onChanged: (val) {
                  setState(() {
                    _selectedSemesterId = val;
                    _isLoading = true;
                  });
                  _loadSubjects();
                },
              ),
            ),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () async => _loadSubjects(forceRefresh: true),
              child: _subjects.isEmpty
                  ? SingleChildScrollView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      child: Container(
                        height: MediaQuery.of(context).size.height * 0.7,
                        alignment: Alignment.center,
                        child: const Text("Ma'lumot topilmadi"),
                      ),
                    )
                  : ListView.builder(
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.all(20),
                      itemCount: _subjects.length,
                      itemBuilder: (context, index) {
                        return _buildSubjectCard(_subjects[index]);
                      },
                    ),
            ),
    );
  }

  Future<void> _loadSubjects({bool forceRefresh = false}) async {
    // 1. Get Semesters if empty
    if (_semesters.isEmpty) {
      _semesters = await _dataService.getSemesters();
      // Only set default if it's the very first load and we don't have "Joriy" concept
      // But now we want Joriy (null) as default. So we don't force select first.
    }
    
    // 2. Get Subjects
    final data = await _dataService.getSubjects(
      semester: _selectedSemesterId, 
      refresh: forceRefresh
    );
    
    if (mounted) {
      setState(() {
        _subjects = data;
        _isLoading = false;
      });
    }
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
