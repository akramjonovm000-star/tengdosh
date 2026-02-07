import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'group_students_screen.dart';

class LevelGroupsScreen extends StatefulWidget {
  final int facultyId;
  final String levelName;
  final String facultyName;

  const LevelGroupsScreen({
    super.key,
    required this.facultyId,
    required this.levelName,
    required this.facultyName,
  });

  @override
  State<LevelGroupsScreen> createState() => _LevelGroupsScreenState();
}

class _LevelGroupsScreenState extends State<LevelGroupsScreen> {
  final DataService _dataService = DataService();
  List<dynamic> _groups = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadGroups();
  }

  Future<void> _loadGroups() async {
    final groups = await _dataService.getManagementGroups(widget.facultyId, widget.levelName);
    setState(() {
      _groups = groups;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text("${widget.levelName}-kurs guruhlari"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _groups.isEmpty
              ? const Center(child: Text("Guruhlar topilmadi"))
              : ListView.builder(
                  itemCount: _groups.length,
                  padding: const EdgeInsets.all(16),
                  itemBuilder: (context, index) {
                    final group = _groups[index];
                    return Card(
                      elevation: 0,
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: BorderSide(color: Colors.grey.shade200),
                      ),
                      child: ListTile(
                        title: Text("Guruh: $group"),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => GroupStudentsScreen(
                                groupNumber: group.toString(),
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
