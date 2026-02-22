import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'package:talabahamkor_mobile/features/home/screens/management/student_detail_view.dart';

class TutorGroupStudentsScreen extends StatefulWidget {
  final String groupNumber;

  const TutorGroupStudentsScreen({
    super.key,
    required this.groupNumber,
  });

  @override
  State<TutorGroupStudentsScreen> createState() => _TutorGroupStudentsScreenState();
}

class _TutorGroupStudentsScreenState extends State<TutorGroupStudentsScreen> {
  final DataService _dataService = DataService();
  List<dynamic> _students = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadStudents();
  }

  Future<void> _loadStudents() async {
    final students = await _dataService.getTutorStudents(group: widget.groupNumber);
    if (mounted) {
      setState(() {
        _students = students;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    int totalCount = _students.length;
    int registeredCount = _students.where((s) => s['is_registered'] == true).length;
    double percentage = totalCount > 0 ? (registeredCount / totalCount) * 100 : 0;

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text("${widget.groupNumber} talabalari"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _students.isEmpty
              ? const Center(child: Text("Talabalar topilmadi"))
              : Column(
                  children: [
                    // --- STATISTICS HEADER ---
                    Container(
                      padding: const EdgeInsets.all(16),
                      margin: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Colors.indigo.shade600, Colors.indigo.shade800],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.indigo.withValues(alpha: 0.3),
                            blurRadius: 10,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Column(
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text(
                                "Ro'yxatdan o'tganlar",
                                style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.2),
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: Text(
                                  "${percentage.toStringAsFixed(0)}%",
                                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: LinearProgressIndicator(
                              value: percentage / 100,
                              backgroundColor: Colors.white.withValues(alpha: 0.1),
                              valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
                              minHeight: 10,
                            ),
                          ),
                          const SizedBox(height: 16),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text("Faol Talabalar", style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 12)),
                                  Text("$registeredCount", style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                                ],
                              ),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Text("Jami Talabalar", style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 12)),
                                  Text("$totalCount", style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                                ],
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    // --- LIST VIEW ---
                    Expanded(
                      child: ListView.builder(
                        itemCount: _students.length,
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        itemBuilder: (context, index) {
                          final s = _students[index];
                          final isRegistered = s['is_registered'] == true;
                          
                          return Card(
                            elevation: 0,
                            margin: const EdgeInsets.only(bottom: 12),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                              side: BorderSide(color: Colors.grey.shade200),
                            ),
                            child: ListTile(
                              leading: Stack(
                                children: [
                                  CircleAvatar(
                                    backgroundColor: Colors.indigo.shade50,
                                    backgroundImage: s['image_url'] != null ? NetworkImage(s['image_url']) : null,
                                    child: s['image_url'] == null ? const Icon(Icons.person, color: Colors.indigo) : null,
                                  ),
                                  if (isRegistered)
                                    Positioned(
                                      bottom: 0,
                                      right: 0,
                                      child: Container(
                                        padding: const EdgeInsets.all(2),
                                        decoration: const BoxDecoration(color: Colors.green, shape: BoxShape.circle),
                                        child: const Icon(Icons.check, size: 12, color: Colors.white),
                                      ),
                                    ),
                                ],
                              ),
                              title: Text(s['full_name'] ?? "", style: const TextStyle(fontWeight: FontWeight.w500)),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text("ID: ${s['hemis_login'] ?? s['hemis_id'] ?? ""}", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                                  const SizedBox(height: 4),
                                  Text(
                                    isRegistered ? "Ilovaga ulangan" : "Ro'yxatdan o'tmagan",
                                    style: TextStyle(
                                      color: isRegistered ? Colors.green[700] : Colors.grey[500],
                                      fontSize: 12,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ],
                              ),
                              trailing: const Icon(Icons.chevron_right, color: Colors.indigo),
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) => StudentDetailView(
                                      studentId: s['id'],
                                    ),
                                  ),
                                );
                              },
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
    );
  }
}
