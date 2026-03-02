import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:intl/intl.dart';

class SubjectGradesScreen extends StatefulWidget {
  final int subjectId;
  final String subjectName;
  final String? semesterId;

  const SubjectGradesScreen({
    super.key,
    required this.subjectId,
    required this.subjectName,
    this.semesterId,
  });

  @override
  State<SubjectGradesScreen> createState() => _SubjectGradesScreenState();
}

class _SubjectGradesScreenState extends State<SubjectGradesScreen> {
  bool _isLoading = true;
  List<dynamic> _grades = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadGrades();
  }

  Future<void> _loadGrades() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final dataService = DataService();
      // Fetch performance (all daily grades)
      print("DEBUG: Requesting performance for semesterId = ${widget.semesterId}");
      final allGrades = await dataService.getStudentPerformance(semesterId: widget.semesterId);
      print("DEBUG: Received ${allGrades.length} performance records.");
      print("DEBUG: Target subjectId=${widget.subjectId}, subjectName=${widget.subjectName}");
      
      // Filter out grades strictly for this subject
      // In Hemis API, subject['id'] is what we compare
      final subjectGrades = allGrades.where((item) {
          final s = item['subject'];
          if (s == null) return false;
          // Compare as strings just in case Int/String parsing varies
          bool idMatch = s['id']?.toString() == widget.subjectId.toString();
          bool nameMatch = (s['name']?.toString().trim().toLowerCase() ?? "") == widget.subjectName.trim().toLowerCase();
          
          if (idMatch || nameMatch) {
              print("DEBUG: Matched grade: ${item}");
          }
          
          return idMatch || nameMatch;
      }).toList();

      // Sort by date descending
      subjectGrades.sort((a, b) {
         final dateA = a['lesson_date'] ?? 0;
         final dateB = b['lesson_date'] ?? 0;
         return dateB.compareTo(dateA);
      });

      if (mounted) {
        setState(() {
          _grades = subjectGrades;
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

  String _formatDate(dynamic timestamp) {
     if (timestamp == null) return "Boma'lum";
     try {
       // Hemis often sends seconds
       final dt = DateTime.fromMillisecondsSinceEpoch(timestamp * 1000);
       return DateFormat('dd.MM.yyyy').format(dt);
     } catch (_) {
       return "$timestamp";
     }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        title: Text(
          widget.subjectName,
          style: const TextStyle(
            color: Colors.black87,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
          maxLines: 2,
          textAlign: TextAlign.center,
        ),
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue));
    }
    
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 60),
            const SizedBox(height: 16),
            Text("Xatolik: $_error", textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadGrades,
              child: const Text("Qayta urinish"),
            )
          ],
        ),
      );
    }
    
    if (_grades.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.assignment_outlined, color: Colors.grey[300], size: 80),
            const SizedBox(height: 16),
            Text(
              "Hozircha kunlik baholar yo'q",
              style: TextStyle(color: Colors.grey[600], fontSize: 16),
            )
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadGrades,
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _grades.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final gradeData = _grades[index];
          final score = gradeData['grade']?.toString() ?? "0";
          final typeObj = gradeData['trainingType'] ?? {};
          final typeName = typeObj['name']?.toString() ?? "Boshqa";
          final dateStr = _formatDate(gradeData['lesson_date']);
          
          Color scoreColor = Colors.grey;
          // Some logic to colorize grades: 5 -> green, 4 -> blue, 3 -> orange, <3 -> red
          try {
             double s = double.parse(score);
             if (s >= 4.5) scoreColor = Colors.green;
             else if (s >= 3.5) scoreColor = AppTheme.primaryBlue;
             else if (s >= 2.5) scoreColor = Colors.orange;
             else scoreColor = Colors.red;
          } catch (_) {}

          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey[50],
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey.shade200)
            ),
            child: Row(
              children: [
                 // Left side (Date & Type)
                 Expanded(
                   child: Column(
                     crossAxisAlignment: CrossAxisAlignment.start,
                     children: [
                       Row(
                         children: [
                            Icon(Icons.calendar_today, size: 14, color: Colors.grey[600]),
                            const SizedBox(width: 6),
                            Text(dateStr, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14, color: Colors.black87)),
                         ]
                       ),
                       const SizedBox(height: 8),
                       Container(
                         padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                         decoration: BoxDecoration(
                           color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                           borderRadius: BorderRadius.circular(8)
                         ),
                         child: Text(
                           typeName, 
                           style: const TextStyle(color: AppTheme.primaryBlue, fontSize: 12, fontWeight: FontWeight.bold)
                         ),
                       )
                     ],
                   )
                 ),
                 
                 // Right side (Score)
                 Container(
                   width: 50,
                   height: 50,
                   alignment: Alignment.center,
                   decoration: BoxDecoration(
                     shape: BoxShape.circle,
                     color: scoreColor.withValues(alpha: 0.1),
                     border: Border.all(color: scoreColor.withValues(alpha: 0.3), width: 2)
                   ),
                   child: Text(
                     score,
                     style: TextStyle(
                       color: scoreColor,
                       fontSize: 20,
                       fontWeight: FontWeight.bold
                     ),
                   )
                 )
              ],
            )
          );
        },
      ),
    );
  }
}
