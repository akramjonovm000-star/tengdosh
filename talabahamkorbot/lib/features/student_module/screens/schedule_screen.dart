import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';
import '../../../core/models/lesson.dart';

class ScheduleScreen extends StatefulWidget {
  const ScheduleScreen({super.key});

  @override
  State<ScheduleScreen> createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<Lesson> _allLessons = [];
  int _selectedDay = 1; // 1 = Monday, 6 = Saturday

  final List<String> _weekDays = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"];

  @override
  void initState() {
    super.initState();
    _autoSelectDay();
    _loadData();
  }

  void _autoSelectDay() {
    final now = DateTime.now().weekday;
    if (now >= 1 && now <= 6) {
      _selectedDay = now;
    } else {
      _selectedDay = 1; // Default to Monday if Sunday
    }
  }

  Future<void> _loadData() async {
    try {
      final data = await _dataService.getSchedule();
      if (mounted) {
        setState(() {
          _allLessons = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  List<Lesson> _getFilteredLessons() {
    // 1. Filter by Selected Day
    final daysLessons = _allLessons.where((l) => l.weekDay == _selectedDay).toList();

    // 2. Deduplicate: Group by StartTime and keep only one
    final Map<String, Lesson> uniqueMap = {};
    for (var lesson in daysLessons) {
       // Key: StartTime. If collision, keep first (or logic to merge?)
       // HEMIS often sends duplicates for same subject/time.
       if (!uniqueMap.containsKey(lesson.startTime)) {
         uniqueMap[lesson.startTime] = lesson;
       }
    }

    final uniqueList = uniqueMap.values.toList();

    // 3. Sort by Time
    uniqueList.sort((a, b) => a.startTime.compareTo(b.startTime));
    
    return uniqueList;
  }

  @override
  Widget build(BuildContext context) {
    final displayLessons = _getFilteredLessons();

    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F7), // Light clean background
      appBar: AppBar(
        title: const Text("Dars Jadvali", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        centerTitle: true,
      ),
      body: Column(
        children: [
          // Custom Calendar Strip
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _weekDays[_selectedDay - 1], 
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.black87)
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: List.generate(6, (index) {
                    final dayNum = index + 1;
                    final isSelected = dayNum == _selectedDay;
                    return GestureDetector(
                      onTap: () => setState(() => _selectedDay = dayNum),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        width: 45,
                        height: 60,
                        decoration: BoxDecoration(
                          color: isSelected ? AppTheme.primaryBlue : Colors.grey[100],
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: isSelected 
                            ? [BoxShadow(color: AppTheme.primaryBlue.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 4))]
                            : [],
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              _weekDays[index].substring(0, 3), // "Dus", "Ses"
                              style: TextStyle(
                                fontSize: 12, 
                                fontWeight: FontWeight.w500,
                                color: isSelected ? Colors.white.withOpacity(0.8) : Colors.grey,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              "${index + 1}", // Simple number representation (optional, could be removed or changed to date if complex)
                              style: TextStyle(
                                fontSize: 16, 
                                fontWeight: FontWeight.bold,
                                color: isSelected ? Colors.white : Colors.black87,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
                ),
              ],
            ),
          ),
          
          // Lessons List
          Expanded(
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator())
              : displayLessons.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.weekend, size: 64, color: Colors.grey[300]),
                          const SizedBox(height: 16),
                          Text("Bugun dars yo'q, dam oling! ☕", style: TextStyle(color: Colors.grey[500], fontSize: 16)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: displayLessons.length,
                      itemBuilder: (context, index) {
                        return _buildLessonCard(displayLessons[index]);
                      },
                    ),
          ),
        ],
      ),
    );
  }

  Widget _buildLessonCard(Lesson lesson) {
    // Parse Time
    String startTime = lesson.startTime;
    if (int.tryParse(lesson.startTime) != null) {
       final dt = DateTime.fromMillisecondsSinceEpoch(int.parse(lesson.startTime) * 1000);
       startTime = "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
    }
    
    // Fallback for empty/null values
    final room = lesson.auditorium.isNotEmpty ? lesson.auditorium : "-";
    final type = lesson.trainingType.isNotEmpty ? lesson.trainingType : "Dars";
    final teacher = lesson.teacherName.isNotEmpty ? lesson.teacherName : "O'qituvchi tayinlanmagan";
    final number = lesson.lessonNumber.isNotEmpty ? lesson.lessonNumber : ""; 

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.withOpacity(0.2)),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 4, offset: const Offset(0, 2)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Subject Title (UPPERCASE) + Number
          Text(
            "${number.isNotEmpty ? '$number. ' : ''}${lesson.subjectName.toUpperCase()}",
            style: const TextStyle(
              fontSize: 14, 
              fontWeight: FontWeight.bold, 
              color: Color(0xFF333333)
            ),
          ),
          
          const SizedBox(height: 12),
          
          // 2. Details Row: Room | Type | Teacher ... Time
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              // Left Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                     // Room / Type / Teacher
                     RichText(
                       text: TextSpan(
                         style: const TextStyle(fontSize: 13, color: Colors.black54),
                         children: [
                            TextSpan(text: room, style: const TextStyle(fontWeight: FontWeight.w500)),
                            const TextSpan(text: "   /   ", style: TextStyle(color: Colors.black26)),
                            TextSpan(text: type, style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.w500)),
                            const TextSpan(text: "   /   ", style: TextStyle(color: Colors.black26)),
                            TextSpan(text: teacher),
                         ]
                       )
                     )
                  ],
                ),
              ),
              
              // Right Time
              Container(
                 margin: const EdgeInsets.only(left: 8),
                 child: Text(
                    startTime,
                    style: const TextStyle(
                      fontSize: 16, 
                      fontWeight: FontWeight.bold, 
                      color: Colors.black87
                    ),
                 ),
              )
            ],
          )
        ],
      ),
    );
  }
}
