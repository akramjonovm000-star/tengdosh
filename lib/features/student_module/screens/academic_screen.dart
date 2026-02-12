import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import 'attendance_screen.dart';
import 'schedule_screen.dart';
import 'grades_screen.dart';
import 'subjects_screen.dart';
import '../../academic/screens/survey_list_screen.dart';
import 'finance/subsidy_screen.dart';

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
      var data = await _dataService.getDashboardStats(refresh: forceRefresh);
      
      // AUTO-FIX: If GPA is 0.0, retry with force refresh
      double tempGpa = double.tryParse(data['gpa']?.toString() ?? '0.0') ?? 0.0;
      if (!forceRefresh && tempGpa == 0.0) {
         data = await _dataService.getDashboardStats(refresh: true);
      }
      
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
            _buildMenuItem(context, "So'rovnomalar", Icons.poll_rounded, Colors.indigo),
            _buildMenuItem(context, "Ijara - Subsidiya", Icons.monetization_on_rounded, Colors.tealAccent.shade700),
            // _buildMenuItem(context, "Ma'lumotlarni yangilash", Icons.person_outline, Colors.blueGrey),
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
            } else if (title == "So'rovnomalar") {
               await Navigator.push(context, MaterialPageRoute(builder: (_) => const SurveyListScreen()));
            } else if (title == "Ijara – Subsidiya") {
               await Navigator.push(context, MaterialPageRoute(builder: (_) => const SubsidyScreen()));
            } else if (title == "Ma'lumotlarni yangilash") {
               _showUpdateProfileDialog(context);
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

  void _showUpdateProfileDialog(BuildContext context) async {
    // 1. Show Loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );

    try {
      // 2. Fetch Profile
      // ensure we use the student profile endpoint
      final profile = await _dataService.getProfile();
      if (!mounted) return;
      Navigator.pop(context); // Close loading

      final TextEditingController phoneCtrl = TextEditingController(text: profile['phone'] ?? '');
      final TextEditingController emailCtrl = TextEditingController(text: profile['email'] ?? '');
      final TextEditingController passCtrl = TextEditingController();
      final TextEditingController confirmPassCtrl = TextEditingController();
      bool isSaving = false;

      // 3. Show Form
      showDialog(
        context: context,
        builder: (context) {
          return StatefulBuilder(
            builder: (context, setDialogState) {
              return AlertDialog(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                title: const Text("Ma'lumotlarni yangilash"),
                content: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                       const Text(
                        "Telefon va Emailni o'zgartirish uchun dekanatga murojaat qiling.",
                        style: TextStyle(fontSize: 12, color: Colors.orange, fontWeight: FontWeight.bold),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: phoneCtrl,
                        readOnly: true,
                        decoration: const InputDecoration(
                          labelText: "Telefon raqam",
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.phone),
                          filled: true,
                          fillColor: Color(0xFFF5F5F5),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: emailCtrl,
                        readOnly: true,
                        decoration: const InputDecoration(
                          labelText: "Email",
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.email),
                          filled: true,
                          fillColor: Color(0xFFF5F5F5),
                        ),
                      ),
                      const Divider(height: 24),
                      const Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          "Parolni o'zgartirish (ixtiyoriy)",
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: passCtrl,
                        decoration: const InputDecoration(
                          labelText: "Yangi parol",
                          hintText: "O'zgartirish uchun kiriting",
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.lock),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: confirmPassCtrl,
                        decoration: const InputDecoration(
                          labelText: "Parolni tasdiqlash",
                          hintText: "Parolni qayta kiriting",
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.lock_outline),
                        ),
                      ),
                      if (isSaving)
                        const Padding(
                          padding: EdgeInsets.only(top: 16),
                          child: Center(child: CircularProgressIndicator()),
                        ),
                    ],
                  ),
                ),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text("Bekor qilish", style: TextStyle(color: Colors.grey)),
                  ),
                  ElevatedButton(
                    onPressed: isSaving ? null : () async {
                      // Validation
                      if (passCtrl.text.isNotEmpty) {
                        if (passCtrl.text != confirmPassCtrl.text) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text("Parollar mos kelmadi"), backgroundColor: Colors.red),
                          );
                          return;
                        }
                        if (passCtrl.text.length < 6) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text("Parol kamida 6 belgidan iborat bo'lishi kerak"), backgroundColor: Colors.red),
                          );
                          return;
                        }
                      }

                      setDialogState(() => isSaving = true);
                      
                      try {
                        await _dataService.updateProfile(
                          phoneCtrl.text.trim(),
                          emailCtrl.text.trim(),
                          passCtrl.text.trim().isEmpty ? null : passCtrl.text.trim()
                        );
                        if (mounted) {
                          Navigator.pop(context);
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text("Ma'lumotlar muvaffaqiyatli yangilandi"), backgroundColor: Colors.green),
                          );
                        }
                      } catch (e) {
                        setDialogState(() => isSaving = false);
                        String error = e.toString().replaceAll("Exception:", "").trim();
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text("Xatolik: $error"), backgroundColor: Colors.red),
                        );
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryBlue,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    child: const Text("Saqlash"),
                  ),
                ],
              );
            }
          );
        },
      );
    } catch (e) {
      if (mounted) Navigator.pop(context); // Close loading if error
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Ma'lumotlarni yuklab bo'lmadi: $e")));
    }
  }
}
