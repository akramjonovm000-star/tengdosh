
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
      backgroundColor: const Color(0xFFF5F5F7), // iOS-like light grey
      appBar: AppBar(
        title: Text(widget.facultyStats.faculty, style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 17)),
        backgroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 20, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Column(
        children: [
          // 1. Premium Header Stats
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: const BorderRadius.vertical(bottom: Radius.circular(24)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryBlue.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(Icons.analytics_outlined, color: AppTheme.primaryBlue, size: 24),
                    ),
                    const SizedBox(width: 16),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Umumiy Holat",
                          style: TextStyle(fontSize: 13, color: Colors.grey[500], fontWeight: FontWeight.w500),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Text(
                              "${widget.facultyStats.total}",
                              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.black),
                            ),
                            const SizedBox(width: 6),
                             Text(
                              "murojaat",
                              style: TextStyle(fontSize: 14, color: Colors.grey[600], height: 1.5),
                            ),
                            const SizedBox(width: 12),
                            Container(
                               height: 4, width: 4, decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.grey[300])),
                            const SizedBox(width: 12),
                            Text(
                              "${widget.facultyStats.pending} kutilmoqda",
                              style: const TextStyle(fontSize: 14, color: Colors.orange, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                      ],
                    )
                  ],
                ),
                const SizedBox(height: 24),
                
                // Smart Chips Scroll
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  physics: const BouncingScrollPhysics(),
                  child: Row(
                    children: [
                      _buildModernChip("Hammasi", null, widget.facultyStats.total),
                      ...widget.facultyStats.topics.entries.map((e) => 
                        _buildModernChip(e.key, e.key, e.value)
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
                      padding: const EdgeInsets.only(top: 20, left: 16, right: 16, bottom: 40),
                      physics: const BouncingScrollPhysics(),
                      itemCount: _appeals.length,
                      itemBuilder: (context, index) => _buildAppealCard(_appeals[index]),
                    ),
          ),
        ],
      ),
    );
  }

  Widget _buildModernChip(String label, String? topicKey, int count) {
    final bool isSelected = _selectedTopic == topicKey;
    
    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedTopic = topicKey;
        });
        _loadAppeals();
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(right: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? Colors.black : Colors.grey[100],
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? Colors.transparent : Colors.grey[200]!,
            width: 1
          ),
          boxShadow: isSelected ? [
            BoxShadow(
              color: Colors.black.withOpacity(0.2),
              blurRadius: 8,
              offset: const Offset(0, 4)
            )
          ] : [],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : Colors.black87,
                fontSize: 14,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: isSelected ? Colors.white.withOpacity(0.2) : Colors.white,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                "$count",
                style: TextStyle(
                  color: isSelected ? Colors.white : Colors.black54,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
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
