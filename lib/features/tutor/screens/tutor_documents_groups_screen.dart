import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/features/tutor/screens/group_documents_screen.dart';
import 'package:talabahamkor_mobile/core/localization/app_dictionary.dart';

class TutorDocumentsGroupsScreen extends StatefulWidget {
  const TutorDocumentsGroupsScreen({super.key});

  @override
  State<TutorDocumentsGroupsScreen> createState() => _TutorDocumentsGroupsScreenState();
}

class _TutorDocumentsGroupsScreenState extends State<TutorDocumentsGroupsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _stats = [];

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() => _isLoading = true);
    final stats = await _dataService.getTutorDocumentStats();
    if (mounted) {
      setState(() {
        _stats = stats ?? [];
        _isLoading = false;
      });
      
      if (stats == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Xatolik: Ma'lumotlarni yuklab bo'lmadi"), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text(AppDictionary.tr(context, 'lbl_docs_stats')),
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _stats.isEmpty
              ? Center(child: Text(AppDictionary.tr(context, 'msg_no_assigned_groups')))
              : RefreshIndicator(
                  onRefresh: _loadStats,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _stats.length,
                    itemBuilder: (context, index) {
                      final item = _stats[index];
                      final total = item['total_students'] ?? 0;
                      final uploaded = item['uploaded_students'] ?? 0;
                      final percent = total > 0 ? (uploaded / total) : 0.0;
                      
                      final String fullGroup = item['group_number']?.toString() ?? "";
                      final List<String> groupParts = fullGroup.split(" ");
                      final String groupCode = groupParts.isNotEmpty ? groupParts[0] : "";
                      final String groupDirection = groupParts.length > 1 ? groupParts.sublist(1).join(" ") : "";

                      return Card(
                        margin: const EdgeInsets.only(bottom: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                          side: BorderSide(color: Colors.grey.withOpacity(0.2)),
                        ),
                        elevation: 0,
                        child: InkWell(
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => GroupDocumentsScreen(
                                  groupNumber: item['group_number'],
                                ),
                              ),
                            ).then((_) => _loadStats());
                          },
                          borderRadius: BorderRadius.circular(16),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            "Guruh: $groupCode",
                                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                                          ),
                                          if (groupDirection.isNotEmpty)
                                            Padding(
                                              padding: const EdgeInsets.only(top: 4.0),
                                              child: Text(
                                                groupDirection,
                                                style: TextStyle(color: Colors.grey[600], fontSize: 13, fontWeight: FontWeight.w500),
                                              ),
                                            ),
                                        ],
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Colors.grey),
                                  ],
                                ),
                                const SizedBox(height: 16),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      "Yuklaganlar: $uploaded / $total",
                                      style: TextStyle(color: Colors.grey[700], fontWeight: FontWeight.w500),
                                    ),
                                    Text(
                                      "${(percent * 100).toInt()}%",
                                      style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(8),
                                  child: LinearProgressIndicator(
                                    value: percent,
                                    backgroundColor: Colors.grey[200],
                                    color: percent == 1.0 ? Colors.green : AppTheme.primaryBlue,
                                    minHeight: 8,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
