import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import 'attendance_screen.dart';
import 'schedule_screen.dart';
import 'grades_screen.dart';
import 'subjects_screen.dart';

class AcademicScreen extends StatefulWidget {
  const AcademicScreen({super.key});

  @override
  State<AcademicScreen> createState() => _AcademicScreenState();
}

class _AcademicScreenState extends State<AcademicScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  double _gpa = 0.0;
  int _missedHours = 0;
  int _excusedHours = 0;
  int _unexcusedHours = 0;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData({bool forceRefresh = false}) async {
    if (!forceRefresh) setState(() => _isLoading = true);
    
    try {
      final data = await _dataService.getDashboardStats(refresh: forceRefresh);
      if (mounted) {
        setState(() {
          _gpa = double.tryParse(data['gpa']?.toString() ?? '0.0') ?? 0.0;
          _missedHours = int.tryParse(data['missed_hours']?.toString() ?? '0') ?? 0;
          _excusedHours = int.tryParse(data['missed_hours_excused']?.toString() ?? '0') ?? 0;
          _unexcusedHours = int.tryParse(data['missed_hours_unexcused']?.toString() ?? '0') ?? 0;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Akademik bo'lim", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: RefreshIndicator(
        onRefresh: () => _loadData(forceRefresh: true),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
            // Stats Box
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Column(
                children: [
                  // GPA Section
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        width: 100,
                        height: 100,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: AppTheme.primaryBlue, width: 8),
                          color: Colors.white,
                        ),
                        alignment: Alignment.center,
                        child: _isLoading 
                          ? const CircularProgressIndicator(color: AppTheme.primaryBlue)
                          : Text(
                              "$_gpa",
                          style: const TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.primaryBlue,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    "Joriy GPA Ko'rsatkichi",
                    style: TextStyle(fontSize: 16, color: Colors.grey, fontWeight: FontWeight.w500),
                  ),
                  const SizedBox(height: 32),
                  
                  // Attendance Breakdown
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      "Davomat statistikasi (soatlar)",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  _isLoading
                      ? const SizedBox()
                      : Column(
                          children: [
                            _buildStatRow("Sababsiz", "$_unexcusedHours soat", Colors.red),
                            const Divider(height: 24),
                            _buildStatRow("Sababli", "$_excusedHours soat", Colors.orange),
                            const Divider(height: 24),
                            _buildStatRow("Jami", "$_missedHours soat", Colors.blue),
                          ],
                        ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Menu List
            _buildMenuItem(context, "Davomat", Icons.calendar_month_rounded, Colors.green),
            _buildMenuItem(context, "Dars jadvali", Icons.schedule_rounded, Colors.blue),
            _buildMenuItem(context, "Fanlar va resurslar", Icons.library_books_rounded, Colors.orange),
            _buildMenuItem(context, "O'zlashtirish", Icons.grade_rounded, Colors.purple),
            _buildMenuItem(context, "Imtihonlar", Icons.edit_document, Colors.redAccent),
            _buildMenuItem(context, "Reyting Daftarchasi", Icons.history_edu_rounded, Colors.teal),
          ],
        ), // Column
      ), // SingleChildScrollView
    ), // RefreshIndicator
  );
}

  bool _navigationLock = false;

  Widget _buildMenuItem(BuildContext context, String title, IconData icon, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color),
        ),
        title: Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Colors.grey),
        onTap: () async {
          if (_navigationLock) return;
          
          setState(() => _navigationLock = true);
          
          try {
            if (title == "Davomat") {
               await Navigator.push(context, MaterialPageRoute(builder: (_) => const AttendanceScreen()));
            } else if (title == "Dars jadvali") {
               await Navigator.push(context, MaterialPageRoute(builder: (_) => const ScheduleScreen()));
            } else if (title == "O'zlashtirish") { 
               await Navigator.push(context, MaterialPageRoute(builder: (_) => const GradesScreen()));
            } else if (title == "Fanlar va resurslar") {
               await Navigator.push(context, MaterialPageRoute(builder: (_) => const SubjectsScreen()));
            } else {
               ScaffoldMessenger.of(context).showSnackBar(
                 SnackBar(content: Text("$title bo'limi tez orada ishga tushadi")),
               );
            }
          } finally {
            // Ensure lock is released even if navigation fails or returns
            if (mounted) {
               setState(() => _navigationLock = false);
            }
          }
        },
      ),
    );
  }

  Widget _buildStatRow(String label, String value, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(color: color, shape: BoxShape.circle),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: Colors.black87),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
        Text(
          value,
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color),
        ),
      ],
    );
  }
}
