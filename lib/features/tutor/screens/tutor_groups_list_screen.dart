import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/features/tutor/screens/tutor_students_screen.dart';
import 'package:talabahamkor_mobile/core/localization/app_dictionary.dart';

class TutorGroupsListScreen extends StatefulWidget {
  const TutorGroupsListScreen({super.key});

  @override
  State<TutorGroupsListScreen> createState() => _TutorGroupsListScreenState();
}

class _TutorGroupsListScreenState extends State<TutorGroupsListScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _groups = [];

  @override
  void initState() {
    super.initState();
    _loadGroups();
  }

  Future<void> _loadGroups() async {
    try {
      final groups = await _dataService.getTutorGroups();
      if (mounted) {
        setState(() {
          _groups = groups;
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint("Error loading groups: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text(AppDictionary.tr(context, 'lbl_my_groups')),
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _groups.isEmpty
              ? Center(child: Text(AppDictionary.tr(context, 'msg_no_assigned_groups')))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _groups.length,
                  itemBuilder: (context, index) {
                    final group = _groups[index];
                    final String fullGroup = group['group_number']?.toString() ?? "Noma'lum";
                    final List<String> groupParts = fullGroup.split(" ");
                    final String groupCode = groupParts.isNotEmpty ? groupParts[0] : "";
                    final String groupDirection = groupParts.length > 1 ? groupParts.sublist(1).join(" ") : "";
                    
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: BorderSide(color: Colors.grey.withOpacity(0.2)),
                      ),
                      child: InkWell(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => TutorStudentsScreen(
                                groupNumber: group['group_number'],
                              ),
                            ),
                          );
                        },
                        borderRadius: BorderRadius.circular(12),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                          child: Row(
                            children: [
                              CircleAvatar(
                                backgroundColor: Colors.orange.withOpacity(0.1),
                                child: const Icon(Icons.class_rounded, color: Colors.orange),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      groupCode.isNotEmpty ? "Guruh: $groupCode" : "Noma'lum",
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                    ),
                                    if (groupDirection.isNotEmpty)
                                      Padding(
                                        padding: const EdgeInsets.only(top: 4.0),
                                        child: Text(
                                          groupDirection,
                                          style: TextStyle(color: Colors.grey[600], fontSize: 13, fontWeight: FontWeight.w500),
                                        ),
                                      ),
                                    if (group['faculty_id'] != null)
                                      Padding(
                                        padding: const EdgeInsets.only(top: 4.0),
                                        child: Text(
                                          "Fakultet ID: ${group['faculty_id']}",
                                          style: TextStyle(color: Colors.grey[500], fontSize: 12),
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                              const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Colors.grey),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
