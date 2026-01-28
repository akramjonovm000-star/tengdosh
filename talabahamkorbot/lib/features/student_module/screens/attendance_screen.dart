import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';
import '../../../core/models/attendance.dart';

class AttendanceScreen extends StatefulWidget {
  const AttendanceScreen({super.key});

  @override
  State<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends State<AttendanceScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<Attendance> _attendanceList = [];
  String _error = "";
  
  // Semester Handling
  final List<int> _semesters = [11, 12, 13, 14, 15, 16, 17, 18];
  int? _selectedSemester; // null = Default/Current

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  void _loadData() async {
    setState(() {
      _isLoading = true;
      _error = "";
    });

    try {
      final data = await _dataService.getAttendanceList(
        semester: _selectedSemester?.toString()
      );
      setState(() {
        _attendanceList = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    // Calculate Stats
    int excused = _attendanceList.where((a) => a.isExcused).fold(0, (sum, item) => sum + item.hours);
    int unexcused = _attendanceList.where((a) => !a.isExcused).fold(0, (sum, item) => sum + item.hours);
    int total = excused + unexcused;

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Davomat", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          // Semi-transparent dropdown container
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 0, vertical: 8),
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: Colors.grey.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<int>(
                value: _selectedSemester,
                hint: const Text("Semestr", style: TextStyle(fontSize: 14)),
                icon: const Icon(Icons.arrow_drop_down, color: Colors.black54),
                borderRadius: BorderRadius.circular(12),
                items: [
                   const DropdownMenuItem<int>(
                     value: null,
                     child: Text("Joriy", style: TextStyle(fontWeight: FontWeight.bold)),
                   ),
                   ..._semesters.map((s) {
                    return DropdownMenuItem<int>(
                      value: s,
                      child: Text("${s - 10}-semestr"),
                    );
                  }).toList(),
                ],
                onChanged: (val) {
                  setState(() {
                    _selectedSemester = val;
                  });
                  _loadData();
                },
              ),
            ),
          ),
          const SizedBox(width: 16),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: Colors.orange),
                      const SizedBox(height: 16),
                      Text("Ma'lumot topilmadi", style: TextStyle(color: Colors.grey[700])),
                      TextButton(onPressed: _loadData, child: const Text("Qayta urinish"))
                    ],
                  ),
                )
              : Column(
                  children: [
                    // Stats Cards
                    Container(
                      padding: const EdgeInsets.all(16),
                      color: Colors.white,
                      child: Row(
                        children: [
                          _buildStatCard("Sababli", excused, Colors.green),
                          const SizedBox(width: 12),
                          _buildStatCard("Sababsiz", unexcused, Colors.red),
                          const SizedBox(width: 12),
                          _buildStatCard("Jami", total, AppTheme.primaryBlue),
                        ],
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Detailed List
                    Expanded(
                      child: _attendanceList.isEmpty
                          ? const Center(child: Text("Qoldirilgan darslar yo'q 🎉"))
                          : ListView.builder(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              itemCount: _attendanceList.length,
                              itemBuilder: (context, index) {
                                final item = _attendanceList[index];
                                return Container(
                                  margin: const EdgeInsets.only(bottom: 12),
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(16),
                                    boxShadow: [
                                      BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 12, offset: const Offset(0, 4))
                                    ],
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Expanded(
                                            child: Text(
                                              item.subjectName,
                                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                            decoration: BoxDecoration(
                                              color: (item.isExcused ? Colors.green : Colors.red).withOpacity(0.1),
                                              borderRadius: BorderRadius.circular(8),
                                            ),
                                            child: Text(
                                              "${item.hours} soat",
                                              style: TextStyle(
                                                color: item.isExcused ? Colors.green : Colors.red,
                                                fontWeight: FontWeight.bold,
                                                fontSize: 14,
                                              ),
                                            ),
                                          )
                                        ],
                                      ),
                                      const SizedBox(height: 8),
                                      Row(
                                        children: [
                                          Icon(Icons.calendar_today_rounded, size: 14, color: Colors.grey[500]),
                                          const SizedBox(width: 6),
                                          Text(item.date, style: TextStyle(color: Colors.grey[600], fontSize: 13, fontWeight: FontWeight.w500)),
                                          const SizedBox(width: 12),
                                          Expanded(
                                            child: Text(
                                              item.lessonTheme,
                                              style: TextStyle(color: Colors.grey[800], fontSize: 13),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        item.isExcused ? "Sababli" : "Sababsiz",
                                        style: TextStyle(
                                          color: item.isExcused ? Colors.green : Colors.red,
                                          fontSize: 12,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      )
                                    ],
                                  ),
                                );
                              },
                            ),
                    ),
                  ],
                ),
    );
  }

  Widget _buildStatCard(String label, int value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.05),
          borderRadius: BorderRadius.circular(16),
          // Clean look without borders
        ),
        child: Column(
          children: [
            Text(
              "$value",
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(fontSize: 12, color: Colors.grey[700], fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }
}
