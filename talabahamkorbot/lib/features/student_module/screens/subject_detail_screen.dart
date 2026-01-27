
import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';

class SubjectDetailScreen extends StatefulWidget {
  final String subjectId;
  final String subjectName;

  const SubjectDetailScreen({
    super.key,
    required this.subjectId,
    required this.subjectName,
  });

  @override
  State<SubjectDetailScreen> createState() => _SubjectDetailScreenState();
}

class _SubjectDetailScreenState extends State<SubjectDetailScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  Map<String, dynamic>? _details;

  @override
  void initState() {
    super.initState();
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    final data = await _dataService.getSubjectDetails(widget.subjectId);
    if (mounted) {
      setState(() {
        _details = data;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    // Info extraction
    final subj = _details?['subject'] ?? {};
    final teachers = (_details?['teachers'] as List?)?.join(", ") ?? "Biriktirilmagan";
    final totalHours = subj['total_hours'] ?? 0;
    final type = subj['type'] ?? "Majburiy";
    
    // Attendance
    final attData = _details?['attendance'] ?? {};
    final missed = attData['total_missed'] ?? 0;
    final percent = attData['percent'] ?? 0.0;
    final list = attData['details'] as List? ?? [];

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text(widget.subjectName, style: const TextStyle(color: Colors.black, fontSize: 16, fontWeight: FontWeight.bold), maxLines: 2),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _details == null
              ? const Center(child: Text("Ma'lumot topilmadi"))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      // 1. Info Card
                      _buildInfoCard(teachers, totalHours, type),
                      const SizedBox(height: 20),
                      
                      // 2. Grades Card (NEW)
                      _buildGradesCard(subj['grades']),
                      const SizedBox(height: 20),
                      
                      // 3. Attendance Stat Card
                      _buildAttendanceCard(missed, percent, totalHours),
                      const SizedBox(height: 20),
                      
                      // 3. Attendance List
                      if (list.isNotEmpty) ...[
                        const Align(
                          alignment: Alignment.centerLeft,
                          child: Text("Davomat tarixi", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        ),
                        const SizedBox(height: 12),
                        ...list.map((item) => _buildAttendanceItem(item)).toList(),
                      ] else 
                        const Text("Qoldirilgan darslar yo'q ✅", style: TextStyle(color: Colors.green, fontWeight: FontWeight.w500)),
                        
                      const SizedBox(height: 30),
                    ],
                  ),
                ),
    );
  }

  Widget _buildInfoCard(String teachers, int totalHours, String type) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 15, offset: const Offset(0, 5))],
      ),
      child: Column(
        children: [
          _buildInfoRow(Icons.person, "O'qituvchi", teachers),
          const Divider(height: 24),
          _buildInfoRow(Icons.access_time_filled, "Umumiy yuklama", "$totalHours soat"),
          const Divider(height: 24),
          _buildInfoRow(Icons.category, "Fan turi", type),
        ],
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(color: Colors.blue.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
          child: Icon(icon, color: Colors.blue, size: 20),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 13)),
              const SizedBox(height: 2),
              Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildGradesCard(dynamic grades) {
    if (grades == null) return const SizedBox();
    
    final overall = grades['overall'] ?? 0;
    final jn = grades['JN']?['val_5'] ?? 0;
    final jnRaw = grades['JN']?['raw'] ?? 0;
    final on = grades['ON']?['val_5'] ?? 0;
    final yn = grades['YN']?['val_5'] ?? 0;
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 15, offset: const Offset(0, 5))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("O'zlashtirish", style: TextStyle(color: Colors.grey, fontSize: 13)),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildGradeItem("Joriy Baho", "$overall", isMain: true),
              Container(width: 1, height: 40, color: Colors.grey.withOpacity(0.2)),
              if (jnRaw > 0) ...[
                _buildGradeItem("JN", "$jn"),
                Container(width: 1, height: 40, color: Colors.grey.withOpacity(0.2)),
              ],
              _buildGradeItem("ON", "$on"),
              Container(width: 1, height: 40, color: Colors.grey.withOpacity(0.2)),
              _buildGradeItem("YN", "$yn"),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildGradeItem(String label, String val, {bool isMain = false}) {
    return Column(
      children: [
        Text(val, style: TextStyle(
          fontWeight: FontWeight.bold, 
          fontSize: isMain ? 24 : 18, 
          color: isMain ? AppTheme.primaryBlue : Colors.black87
        )),
        Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
      ],
    );
  }

  Widget _buildAttendanceCard(dynamic missed, dynamic percent, int totalHours) {
    // Color logic
    Color color = Colors.green;
    if (percent > 20) color = Colors.red;
    else if (percent > 10) color = Colors.orange;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 15, offset: const Offset(0, 5))],
      ),
      child: Row(
        children: [
          // Circular Percent
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: color.withOpacity(0.2), width: 8),
            ),
            child: Center(
              child: Text(
                "$percent%",
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: color),
              ),
            ),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("Davomat", style: TextStyle(color: Colors.grey[600], fontSize: 14)),
                const SizedBox(height: 6),
                Text("$missed soat qoldirilgan", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                Text("Jami $totalHours soatdan", style: const TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAttendanceItem(Map<String, dynamic> item) {
    final date = item['date'] ?? "";
    final hours = item['hours'] ?? 2;
    final isExcused = item['is_excused'] ?? false;
    final type = item['type'] ?? "Dars";

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.withOpacity(0.1)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: isExcused ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              date,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: isExcused ? Colors.green : Colors.red,
                fontSize: 13
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(type, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                Text(isExcused ? "Sababli" : "Sababsiz", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
              ],
            ),
          ),
          Text(
            "$hours soat",
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
          ),
        ],
      ),
    );
  }
}
