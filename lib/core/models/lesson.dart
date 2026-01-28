class Lesson {
  final int id;
  final String subjectName;
  final String startTime;
  final String endTime;
  final String auditorium;
  final String teacherName;
  final String trainingType;
  final int weekDay; // 1 = Monday, 6 = Saturday
  final int? lessonDate; // Unix timestamp

  Lesson({
    required this.id,
    required this.subjectName,
    required this.startTime,
    required this.endTime,
    required this.auditorium,
    required this.teacherName,
    required this.trainingType,
    required this.weekDay,
    this.lessonDate,
  });

  factory Lesson.fromJson(Map<String, dynamic> json) {
    final subject = json['subject'] != null ? json['subject']['name'] ?? 'Noma\'lum fan' : (json['subject_name'] ?? 'Noma\'lum fan');
    
    final auditoriumData = json['auditorium'];
    final room = auditoriumData != null ? auditoriumData['name'] ?? '' : (json['auditorium_name'] ?? '');
    
    final employee = json['employee'];
    final teacher = employee != null ? employee['name'] ?? '' : (json['teacher_name'] ?? '');

    final training = json['trainingType'] != null ? json['trainingType']['name'] ?? 'Dars' : (json['training_type_name'] ?? 'Dars');

    // Time parsing - Try multiple common HEMIS locations
    String start = json['start_time'] ?? '';
    String end = json['end_time'] ?? '';
    
    final lessonPair = json['lessonPair'];
    if (lessonPair != null && lessonPair is Map) {
      if (start.isEmpty) start = (lessonPair['start_time'] ?? '').toString();
      if (end.isEmpty) end = (lessonPair['end_time'] ?? '').toString();
    }

    // Weekday: 1=Mon ... 6=Sat
    int day = 1;
    int? lessonTs;

    // 1. Try to derive from lesson_date (timestamp)
    final timestamp = json['lesson_date'];
    if (timestamp != null) {
      try {
        final ts = int.parse(timestamp.toString());
        if (ts > 5000000) { // Basic sanity check for unix timestamp
           lessonTs = ts;
           day = DateTime.fromMillisecondsSinceEpoch(ts * 1000).weekday;
        }
      } catch (_) {}
    }

    // 2. Fallback to explicit day IDs
    if (json['week_day_id'] != null) {
       int val = int.tryParse(json['week_day_id'].toString()) ?? day;
       day = (val > 10) ? val - 10 : val;
    } else if (json['day_of_week'] != null) {
       int val = int.tryParse(json['day_of_week'].toString()) ?? day;
       day = (val > 10) ? val - 10 : val;
    } else if (json['week_day'] != null && json['week_day'] is! Map) {
       day = int.tryParse(json['week_day'].toString()) ?? day;
    }

    return Lesson(
      id: json['id'] ?? 0,
      subjectName: subject,
      startTime: start,
      endTime: end,
      auditorium: room,
      teacherName: teacher,
      trainingType: training,
      weekDay: day,
      lessonDate: lessonTs,
    );
  }
}
