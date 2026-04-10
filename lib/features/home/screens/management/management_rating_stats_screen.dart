import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'survey_detail_analytics_screen.dart';

class ManagementRatingStatsScreen extends StatefulWidget {
  const ManagementRatingStatsScreen({super.key});

  @override
  State<ManagementRatingStatsScreen> createState() => _ManagementRatingStatsScreenState();
}

class _ManagementRatingStatsScreenState extends State<ManagementRatingStatsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _surveys = [];

  @override
  void initState() {
    super.initState();
    _loadSurveys();
  }

  Future<void> _loadSurveys() async {
    setState(() => _isLoading = true);
    final surveys = await _dataService.getManagementSurveys();
    
    if (mounted) {
      setState(() {
        _surveys = surveys;
        _isLoading = false;
      });
    }
  }

  Future<void> _toggleSurveyStatus(int id, String roleType, bool currentStatus) async {
    setState(() => _isLoading = true);
    final result = await _dataService.createManagementSurvey({
      "id": id,
      "role_type": roleType,
      "is_active": !currentStatus,
    });
    
    if (mounted) {
      if (result['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(currentStatus ? "So'rovnoma to'xtatildi" : "So'rovnoma aktivlashtirildi"), backgroundColor: Colors.green)
        );
        _loadSurveys();
      } else {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? "Xatolik yuz berdi"), backgroundColor: Colors.red)
        );
      }
    }
  }

  void _editSurvey(dynamic survey) async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => CreateManagementSurveyScreen(initialData: survey),
      ),
    );
    if (result == true) {
      _loadSurveys();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Boshqaruv va statistika"),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        actions: [
          IconButton(
            onPressed: _loadSurveys,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _surveys.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  onRefresh: _loadSurveys,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _surveys.length,
                    itemBuilder: (context, index) {
                      final survey = _surveys[index];
                      return _SurveyListItem(
                        survey: survey,
                        onEdit: () => _editSurvey(survey),
                        onToggle: () => _toggleSurveyStatus(
                          survey['id'], 
                          survey['role_type'] ?? 'tutor', 
                          survey['is_active'] ?? false
                        ),
                      );
                    },
                  ),
                ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.assignment_outlined, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            "So'rovnomalar topilmadi",
            style: TextStyle(fontSize: 18, color: Colors.grey[600], fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}

class _SurveyListItem extends StatelessWidget {
  final dynamic survey;
  final VoidCallback onToggle;
  final VoidCallback onEdit;
  const _SurveyListItem({required this.survey, required this.onToggle, required this.onEdit});

  @override
  Widget build(BuildContext context) {
    final String status = survey['status'] ?? 'pending';
    final Color statusColor = _getStatusColor(status);
    final String statusText = _getStatusText(status);
    final bool isActive = survey['is_active'] ?? false;

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 4,
      shadowColor: Colors.black12,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(color: statusColor, shape: BoxShape.circle),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        statusText,
                        style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                Text(
                  "${survey['total_votes']} ta ovoz",
                  style: TextStyle(color: Colors.grey[600], fontSize: 13, fontWeight: FontWeight.w500),
                ),
              ],
            ),
            const SizedBox(height: 16),
            InkWell(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => SurveyDetailAnalyticsScreen(surveyId: survey['id'], title: survey['title']),
                  ),
                );
              },
              child: Text(
                survey['title'] ?? 'Nomsiz so\'rovnoma',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.calendar_today_outlined, size: 14, color: Colors.grey[600]),
                const SizedBox(width: 8),
                Text(
                  "${survey['start_at'].substring(0, 10)} - ${survey['end_at'].substring(0, 10)}",
                  style: TextStyle(color: Colors.grey[600], fontSize: 13),
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed: onEdit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue[50],
                    foregroundColor: Colors.blue[700],
                    elevation: 0,
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: const Text("Tahrirlash", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: onToggle,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isActive ? Colors.grey[200] : Colors.green[600],
                    foregroundColor: isActive ? Colors.black87 : Colors.white,
                    elevation: 0,
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: Text(isActive ? "To'xtatish" : "Aktiv qilish", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'active': return Colors.green;
      case 'finished': return Colors.red;
      case 'pending': return Colors.orange;
      default: return Colors.grey;
    }
  }

  String _getStatusText(String status) {
    switch (status) {
      case 'active': return "Faol";
      case 'finished': return "Tugagan";
      case 'pending': return "Kutilayotgan";
      default: return "Noma'lum";
    }
  }
}
