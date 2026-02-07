import 'package:flutter/material.dart';
import '../../../core/services/data_service.dart';
import 'level_groups_screen.dart';

class FacultyLevelsScreen extends StatefulWidget {
  final int facultyId;
  final String facultyName;

  const FacultyLevelsScreen({
    super.key,
    required this.facultyId,
    required this.facultyName,
  });

  @override
  State<FacultyLevelsScreen> createState() => _FacultyLevelsScreenState();
}

class _FacultyLevelsScreenState extends State<FacultyLevelsScreen> {
  final DataService _dataService = DataService();
  List<dynamic> _levels = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadLevels();
  }

  Future<void> _loadLevels() async {
    final levels = await _dataService.getManagementLevels(widget.facultyId);
    setState(() {
      _levels = levels;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(widget.facultyName),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _levels.isEmpty
              ? const Center(child: Text("Bosqichlar topilmadi"))
              : ListView.builder(
                  itemCount: _levels.length,
                  padding: const EdgeInsets.all(16),
                  itemBuilder: (context, index) {
                    final level = _levels[index];
                    return Card(
                      elevation: 0,
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: BorderSide(color: Colors.grey.shade200),
                      ),
                      child: ListTile(
                        title: Text("$level-kurs"),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => LevelGroupsScreen(
                                facultyId: widget.facultyId,
                                levelName: level.toString(),
                                facultyName: widget.facultyName,
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
