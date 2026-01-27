class Lesson {
  final int id;
  final String subjectName;
  final String startTime;
  final String endTime;
  final String auditorium;
  final String teacherName;
  final int weekDay; // 1 = Monday, 6 = Saturday

  Lesson({
    required this.id,
    required this.subjectName,
    required this.startTime,
    required this.endTime,
    required this.auditorium,
    required this.teacherName,
    required this.weekDay,
  });

  factory Lesson.fromJson(Map<String, dynamic> json) {
    // Expected structure based on typical HEMIS '/education/schedule'
    // { "lesson_date": 1705234234, "subject": { "name": "..." }, "auditorium": { "name": "..." }, ... }
    // OR directly "start_time", "end_time"
    
    // We will assume a flexible structure and add safety checks
    
    final subject = json['subject'] != null ? json['subject']['name'] ?? 'Noma\'lum fan' : 'Noma\'lum fan';
    
    final auditoriumData = json['auditorium'];
    final room = auditoriumData != null ? auditoriumData['name'] ?? '' : '';
    
    final employee = json['employee'];
    final teacher = employee != null ? employee['name'] ?? '' : '';

    // Time parsing
    // Sometimes returns unix timestamp, sometimes "14:00"
    // For now assuming string or constructing from hour
    final start = json['start_time'] ?? '';
    final end = json['end_time'] ?? '';
    
    // Weekday: 1=Mon ... 6=Sat
    // If not provided, might need to derive from date
    int day = 1;
    if (json['week_day_id'] != null) {
       int val = int.tryParse(json['week_day_id'].toString()) ?? 1;
       // HEMIS often uses 11=Mon, 12=Tue... Normalize to 1-6
       day = (val > 10) ? val - 10 : val;
    } else if (json['day_of_week'] != null) {
       int val = int.tryParse(json['day_of_week'].toString()) ?? 1;
       day = (val > 10) ? val - 10 : val;
    }

    return Lesson(
      id: json['id'] ?? 0,
      subjectName: subject,
      startTime: start,
      endTime: end,
      auditorium: room,
      teacherName: teacher,
      weekDay: day,
    );
  }
}
