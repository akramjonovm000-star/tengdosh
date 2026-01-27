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
    // Format Start Time
    String startTime = lesson.startTime;
    if (int.tryParse(lesson.startTime) != null) {
       final dt = DateTime.fromMillisecondsSinceEpoch(int.parse(lesson.startTime) * 1000);
       startTime = "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
    }
    
    // Format End Time (if empty, assume +80 mins or similar, but let's just show start for now or calculate)
    // Often HEMIS sends pairs.
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 12, offset: const Offset(0, 4)),
        ],
      ),
      child: IntrinsicHeight(
        child: Row(
          children: [
            // Left Stripe & Time
            Container(
              width: 80,
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.horizontal(left: Radius.circular(20)),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    startTime,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryBlue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      "Dars", 
                      style: TextStyle(fontSize: 10, color: AppTheme.primaryBlue, fontWeight: FontWeight.bold),
                    ),
                  )
                ],
              ),
            ),
            
            VerticalDivider(width: 1, thickness: 1, color: Colors.grey[100]),
            
            // Content
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      lesson.subjectName,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black87),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(Icons.room, size: 14, color: Colors.grey[500]),
                        const SizedBox(width: 4),
                        Text(
                          lesson.auditorium.isNotEmpty ? lesson.auditorium : "Xona yo'q",
                          style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                        ),
                        const SizedBox(width: 12),
                        Icon(Icons.person, size: 14, color: Colors.grey[500]),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            lesson.teacherName,
                            style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
