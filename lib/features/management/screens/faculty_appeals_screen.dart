
import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import '../models/appeal_model.dart';
import '../services/appeal_service.dart';
import 'management_appeal_detail_screen.dart';

class FacultyAppealsScreen extends StatefulWidget {
  final FacultyPerformance facultyStats;

  const FacultyAppealsScreen({super.key, required this.facultyStats});

  @override
  State<FacultyAppealsScreen> createState() => _FacultyAppealsScreenState();
}

class _FacultyAppealsScreenState extends State<FacultyAppealsScreen> {
  final AppealService _service = AppealService();
  
  bool _isLoading = true;
  String? _error;
  List<Appeal> _appeals = [];
  String? _selectedTopic; // Null means "All"

  @override
  void initState() {
    super.initState();
    _loadAppeals();
  }

  Future<void> _loadAppeals() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final appeals = await _service.getAppeals(
        facultyId: widget.facultyStats.id, // Use ID for precise filtering
        aiTopic: _selectedTopic,
      );
      
      if (mounted) {
        setState(() {
          _appeals = appeals;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text(widget.facultyStats.faculty, style: const TextStyle(color: Colors.black, fontSize: 16)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Column(
        children: [
          // 1. Header Stats
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "${widget.facultyStats.total} Murojaat (${widget.facultyStats.pending} Kutilmoqda)",
                  style: const TextStyle(color: Colors.grey, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                // Smart Chips
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildTopicChip("Hammasi", null, widget.facultyStats.total),
                      ...widget.facultyStats.topics.entries.map((e) => 
                        _buildTopicChip(e.key, e.key, e.value)
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          // 2. List
          Expanded(
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator())
              : _error != null 
                  ? Center(child: Text("Xatolik: $_error"))
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _appeals.length,
                      itemBuilder: (context, index) => _buildAppealCard(_appeals[index]),
                    ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopicChip(String label, String? topicKey, int count) {
    final bool isSelected = _selectedTopic == topicKey;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text("$label ($count)"),
        selected: isSelected,
        onSelected: (bool selected) {
          setState(() {
            _selectedTopic = topicKey; // If re-selecting same, keep it active (or toggle off? let's keep active logic simpler)
          });
          _loadAppeals();
        },
        backgroundColor: Colors.grey[100],
        selectedColor: AppTheme.primaryBlue.withOpacity(0.2),
        labelStyle: TextStyle(
          color: isSelected ? AppTheme.primaryBlue : Colors.black87,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
        showCheckmark: false,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: isSelected ? AppTheme.primaryBlue : Colors.grey[300]!),
        ),
      ),
    );
  }

  Widget _buildAppealCard(Appeal appeal) {
    Color statusColor = Colors.grey;
    String statusLabel = appeal.status.toUpperCase();
    
    if (appeal.status == 'pending') {
      statusColor = Colors.orange;
      statusLabel = "KUTILMOQDA";
    } else if (appeal.status == 'processing') {
      statusColor = Colors.blue;
      statusLabel = "JARAYONDA";
    } else if (appeal.status == 'resolved' || appeal.status == 'replied') {
      statusColor = Colors.green;
      statusLabel = appeal.status == 'resolved' ? "HAL QILINDI" : "JAVOB BERILDI";
    }
    
    // Logic for Overdue Border (e.g. check created_at vs now, or use backend field if added to Appeal item)
    // For now simple visual
    
    return GestureDetector(
      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagementAppealDetailScreen(appealId: appeal.id))),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.transparent), // Add red border logic here if needed
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 8, offset: const Offset(0, 2))],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    appeal.aiTopic ?? "Umumiy", 
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                  child: Text(statusLabel, style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            const SizedBox(height: 8),
             Row(
              children: [
                Icon(Icons.access_time, size: 14, color: Colors.grey[500]),
                const SizedBox(width: 4),
                TextThemeUtils.timeAgo(appeal.createdAt), // Need util or simple parse
                const SizedBox(width: 12),
                Icon(Icons.person_outline, size: 14, color: Colors.grey[500]),
                const SizedBox(width: 4),
                Expanded(child: Text(appeal.studentName, style: TextStyle(fontSize: 12, color: Colors.grey[600]), overflow: TextOverflow.ellipsis)),
              ],
            ),
            const SizedBox(height: 8),
            Text(appeal.text, style: TextStyle(color: Colors.grey[800]), maxLines: 2, overflow: TextOverflow.ellipsis),
          ],
        ),
      ),
    );
  }
}

class TextThemeUtils {
  static Widget timeAgo(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      final diff = DateTime.now().difference(date);
      String text;
      if (diff.inDays > 0) text = "${diff.inDays} kun oldin";
      else if (diff.inHours > 0) text = "${diff.inHours} soat oldin";
      else text = "${diff.inMinutes} daqiqa oldin";
      return Text(text, style: TextStyle(fontSize: 12, color: Colors.grey[500]));
    } catch (e) {
      return Text(dateStr.split('T')[0], style: TextStyle(fontSize: 12, color: Colors.grey[500]));
    }
  }
}
