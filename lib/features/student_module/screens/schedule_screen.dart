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
                          color: isSelected ? const Color(0xFFD81B60) : Colors.grey[100],
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: isSelected 
                            ? [BoxShadow(color: const Color(0xFFD81B60).withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 4))]
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
    // Colors based on user design
    const primaryPink = Color(0xFFC2185B);
    const bgPink = Color(0xFFFCE4EC);
    const accentPink = Color(0xFFD81B60);

    // Format Times
    String startTime = lesson.startTime;
    if (int.tryParse(lesson.startTime) != null) {
       final dt = DateTime.fromMillisecondsSinceEpoch(int.parse(lesson.startTime) * 1000);
       startTime = "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
    }

    String endTime = lesson.endTime;
    if (int.tryParse(lesson.endTime) != null) {
       final dt = DateTime.fromMillisecondsSinceEpoch(int.parse(lesson.endTime) * 1000);
       endTime = "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
    }
    
    final timeRange = endTime.isNotEmpty ? "$startTime - $endTime" : startTime;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: bgPink,
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: IntrinsicHeight(
        child: Row(
          children: [
            // Left Accent Border
            Container(
              width: 4,
              decoration: const BoxDecoration(
                color: accentPink,
                borderRadius: BorderRadius.horizontal(left: Radius.circular(8)),
              ),
            ),
            // Main Content
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Subject Name (Uppercase, bold)
                    Text(
                      lesson.subjectName.toUpperCase(),
                      style: const TextStyle(
                        color: accentPink,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        letterSpacing: 0.5,
                      ),
                    ),
                    const SizedBox(height: 8),
                    // Type & Teacher
                    Text(
                      "${lesson.trainingType}  (${lesson.teacherName})",
                      style: const TextStyle(
                        color: primaryPink,
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 12),
                    // Footer: Time and Room
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          "$timeRange  ",
                          style: const TextStyle(
                            color: accentPink,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Text(
                          lesson.auditorium.isNotEmpty ? lesson.auditorium : "",
                          style: const TextStyle(
                            color: accentPink,
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            // Right Side Decoration (Checkmark and Track)
            Container(
              width: 40,
              padding: const EdgeInsets.only(bottom: 8),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Vertical "Track" indicator
                  Positioned(
                    top: 8,
                    right: 8,
                    bottom: 8,
                    child: Container(
                      width: 4,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.5),
                        borderRadius: BorderRadius.circular(2),
                      ),
                      child: Stack(
                        children: [
                          Positioned(
                            top: 0,
                            right: 0,
                            left: 0,
                            height: 20,
                            child: Container(
                              decoration: BoxDecoration(
                                color: accentPink.withOpacity(0.3),
                                borderRadius: BorderRadius.circular(2),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  // Progress indicator dot/arrow (top right)
                  const Positioned(
                    top: 12,
                    right: 8,
                    child: Icon(Icons.arrow_drop_up, color: accentPink, size: 16),
                  ),
                  // Checkmark in bottom right
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.8),
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.green.withOpacity(0.3), width: 2),
                      ),
                      child: const Icon(
                        Icons.check,
                        color: Colors.green,
                        size: 18,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
