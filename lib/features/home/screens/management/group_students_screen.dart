import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'student_detail_view.dart';

class GroupStudentsScreen extends StatefulWidget {
  final String groupNumber;

  const GroupStudentsScreen({
    super.key,
    required this.groupNumber,
  });

  @override
  State<GroupStudentsScreen> createState() => _GroupStudentsScreenState();
}

class _GroupStudentsScreenState extends State<GroupStudentsScreen> {
  final DataService _dataService = DataService();
  List<dynamic> _students = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadStudents();
  }

  Future<void> _loadStudents() async {
    final students = await _dataService.getManagementGroupStudents(widget.groupNumber);
    setState(() {
      _students = students;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
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
              : ListView.builder(
                  itemCount: _students.length,
                  padding: const EdgeInsets.all(16),
                  itemBuilder: (context, index) {
                    final s = _students[index];
                    return Card(
                      elevation: 0,
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: BorderSide(color: Colors.grey.shade200),
                      ),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundImage: s['image_url'] != null ? NetworkImage(s['image_url']) : null,
                          child: s['image_url'] == null ? const Icon(Icons.person) : null,
                        ),
                        title: Text(s['full_name'] ?? ""),
                        subtitle: Text("ID: ${s['hemis_login'] ?? s['hemis_id'] ?? ""}"),
                        trailing: const Icon(Icons.chevron_right),
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
    );
  }
}
