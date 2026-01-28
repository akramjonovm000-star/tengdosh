import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';
import '../../../core/models/lesson.dart';
import '../../../core/models/attendance.dart';
import 'package:intl/intl.dart';

class ScheduleScreen extends StatefulWidget {
  const ScheduleScreen({super.key});

  @override
  State<ScheduleScreen> createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<Lesson> _allLessons = [];
  List<Attendance> _attendance = [];
  int _selectedDay = 1; // 1 = Monday, 6 = Saturday

  final List<String> _weekDays = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"];
  final List<String> _months = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
  ];

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
      final Future<List<Lesson>> scheduleFuture = _dataService.getSchedule();
      final Future<List<Attendance>> attendanceFuture = _dataService.getAttendanceList(); // Fetch all attendance for cross-ref

      final List<dynamic> results = await Future.wait([scheduleFuture, attendanceFuture]);
      
      if (mounted) {
        setState(() {
          _allLessons = results[0] as List<Lesson>;
          _attendance = results[1] as List<Attendance>;
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

    // 2. Sort by Time and Subject Name (to keep stable order)
    daysLessons.sort((a, b) {
      int timeComp = a.startTime.compareTo(b.startTime);
      if (timeComp != 0) return timeComp;
      return a.subjectName.compareTo(b.subjectName);
    });
    
    return daysLessons;
  }

  @override
  Widget build(BuildContext context) {
    final displayLessons = _getFilteredLessons();

    final now = DateTime.now();
    final firstDayOfWeek = now.subtract(Duration(days: now.weekday - 1));
    final selectedDate = firstDayOfWeek.add(Duration(days: _selectedDay - 1));

    return Scaffold(
      backgroundColor: Colors.white,
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
                  "${_weekDays[_selectedDay - 1]}, ${selectedDate.day}-${_months[selectedDate.month - 1]}", 
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.black87)
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: List.generate(6, (index) {
                    final dayNum = index + 1;
                    final isSelected = dayNum == _selectedDay;
                    final dateForIndex = firstDayOfWeek.add(Duration(days: index));
                    
                    return GestureDetector(
                      onTap: () => setState(() => _selectedDay = dayNum),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        width: 45,
                        height: 55,
                        decoration: BoxDecoration(
                          color: isSelected ? Colors.black : Colors.grey[50],
                          borderRadius: BorderRadius.circular(15),
                          border: isSelected ? null : Border.all(color: Colors.grey[200]!),
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              _weekDays[index].substring(0, 3), // "Dus", "Ses"
                              style: TextStyle(
                                fontSize: 11, 
                                fontWeight: FontWeight.w500,
                                color: isSelected ? Colors.white.withOpacity(0.7) : Colors.grey[400],
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              "${dateForIndex.day}", 
                              style: TextStyle(
                                fontSize: 15, 
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
          const Divider(height: 1, thickness: 1, color: Color(0xFFF0F0F0)),
          
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
    // 1. Determine Status
    final now = DateTime.now();
    bool isPast = false;
    
    // Parse lesson date and time
    if (lesson.lessonDate != null) {
      final lessonDt = DateTime.fromMillisecondsSinceEpoch(lesson.lessonDate! * 1000);
      
      // Assume end time is 80 mins after start if not provided
      // If start is e.g. "08:30"
      if (lesson.startTime.contains(":")) {
        final parts = lesson.startTime.split(":");
        final startDt = DateTime(lessonDt.year, lessonDt.month, lessonDt.day, int.parse(parts[0]), int.parse(parts[1]));
        isPast = now.isAfter(startDt.add(const Duration(minutes: 80)));
      } else {
        // Fallback for non-time strings
        isPast = now.isAfter(lessonDt.add(const Duration(hours: 18))); // End of day fallback
      }
    } else {
       // Calculation based on day only if timestamp missing
       isPast = DateTime.now().weekday > lesson.weekDay || (DateTime.now().weekday == lesson.weekDay && now.hour > 18);
    }

    // 2. Check for Absence record
    // Match by Subject Name (approx) and Date
    bool hasAbsence = false;
    if (isPast) {
       final lessonDateStr = lesson.lessonDate != null 
          ? DateFormat('yyyy-MM-dd').format(DateTime.fromMillisecondsSinceEpoch(lesson.lessonDate! * 1000)) 
          : "";
          
       hasAbsence = _attendance.any((a) => 
          (a.subjectName.toLowerCase().contains(lesson.subjectName.toLowerCase()) || 
           lesson.subjectName.toLowerCase().contains(a.subjectName.toLowerCase())) &&
          (lessonDateStr.isEmpty || a.date == lessonDateStr)
       );
    }

    Color statusColor = Colors.blue; 
    IconData? statusIcon;
    Color iconColor = Colors.white;

    if (!isPast) {
       statusColor = Colors.blue[400]!;
    } else if (hasAbsence) {
       statusColor = Colors.red[500]!;
       statusIcon = Icons.close;
       iconColor = Colors.red;
    } else {
       statusColor = Colors.green[500]!;
       statusIcon = Icons.check;
       iconColor = Colors.green;
    }

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[100]!),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: IntrinsicHeight(
          child: Row(
            children: [
              // Left Accent Border (Status based)
              Container(width: 4, color: statusColor),
              // Main Content
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Subject Name (Uppercase, bold)
                      Text(
                        lesson.subjectName,
                        style: const TextStyle(
                          color: Colors.black87,
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 4),
                      // Lesson Topic
                      if (lesson.lessonTopic != "Mavzu kiritilmagan")
                        Text(
                          lesson.lessonTopic,
                          style: TextStyle(
                            color: Colors.grey[700],
                            fontSize: 13,
                            fontStyle: FontStyle.italic,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      const SizedBox(height: 6),
                      // Type & Teacher
                      Text(
                        "${lesson.trainingType}  •  ${lesson.teacherName}",
                        style: TextStyle(
                          color: Colors.grey[600],
                          fontSize: 13,
                        ),
                      ),
                      const SizedBox(height: 12),
                      // Footer: Time and Room
                      Row(
                        children: [
                          Icon(Icons.access_time_filled, size: 14, color: Colors.grey[400]),
                          const SizedBox(width: 4),
                          Text(
                            "${lesson.startTime}${lesson.endTime.isNotEmpty ? ' - ${lesson.endTime}' : ''}",
                            style: TextStyle(
                              color: Colors.grey[700],
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const Spacer(),
                          Text(
                            lesson.auditorium.isNotEmpty ? lesson.auditorium : "",
                            style: const TextStyle(
                              color: Colors.black54,
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              // Right Side Icon (Status based)
              if (statusIcon != null)
                Container(
                  width: 40,
                  alignment: Alignment.centerRight,
                  padding: const EdgeInsets.only(right: 12),
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: iconColor.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(statusIcon, color: iconColor, size: 18),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
