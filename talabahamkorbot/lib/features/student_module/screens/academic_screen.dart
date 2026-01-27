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

  Future<void> _loadData() async {
    try {
      final data = await _dataService.getDashboardStats();
      if (mounted) {
        setState(() {
          _gpa = (data['gpa'] ?? 0.0).toDouble();
          _missedHours = (data['missed_hours'] ?? 0).toInt();
          _excusedHours = (data['missed_hours_excused'] ?? 0).toInt();
          _unexcusedHours = (data['missed_hours_unexcused'] ?? 0).toInt();
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
      body: SingleChildScrollView(
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
                      "Davomat Statistikasi (Soatlar)",
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
            _buildMenuItem(context, "Dars Jadvali", Icons.schedule_rounded, Colors.blue),
            _buildMenuItem(context, "Fanlar va Resurslar", Icons.library_books_rounded, Colors.orange),
            _buildMenuItem(context, "O'zlashtirish", Icons.grade_rounded, Colors.purple),
            _buildMenuItem(context, "Imtihonlar", Icons.edit_document, Colors.redAccent),
            _buildMenuItem(context, "Reyting Daftarchasi", Icons.history_edu_rounded, Colors.teal),
          ],
        ),
      ),
    );
  }

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
        onTap: () {
          if (title == "Davomat") {
             Navigator.push(context, MaterialPageRoute(builder: (_) => const AttendanceScreen()));
             return;
          }
          if (title == "Dars Jadvali") {
             Navigator.push(context, MaterialPageRoute(builder: (_) => const ScheduleScreen()));
             return;
          }
          if (title == "O'zlashtirish") { 
             Navigator.push(context, MaterialPageRoute(builder: (_) => const GradesScreen()));
             return;
          }
          if (title == "Fanlar va Resurslar") {
             Navigator.push(context, MaterialPageRoute(builder: (_) => const SubjectsScreen()));
             return;
          }
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("$title bo'limi tez orada ishga tushadi")),
          );
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
