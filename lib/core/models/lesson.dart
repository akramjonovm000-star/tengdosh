class Lesson {
  final int id;
  final String subjectName;
  final String startTime;
  final String endTime;
  final String auditorium;
  final String teacherName;
  final String trainingType;
  final int weekDay; // 1 = Monday, 6 = Saturday

  Lesson({
    required this.id,
    required this.subjectName,
    required this.startTime,
    required this.endTime,
    required this.auditorium,
    required this.teacherName,
    required this.trainingType,
    required this.weekDay,
  });

  factory Lesson.fromJson(Map<String, dynamic> json) {
    final subject = json['subject'] != null ? json['subject']['name'] ?? 'Noma\'lum fan' : (json['subject_name'] ?? 'Noma\'lum fan');
    
    final auditoriumData = json['auditorium'];
    final room = auditoriumData != null ? auditoriumData['name'] ?? '' : (json['auditorium_name'] ?? '');
    
    final employee = json['employee'];
    final teacher = employee != null ? employee['name'] ?? '' : (json['teacher_name'] ?? '');

    final training = json['trainingType'] != null ? json['trainingType']['name'] ?? 'Dars' : (json['training_type_name'] ?? 'Dars');

    // Time parsing
    final start = json['start_time'] ?? '';
    final end = json['end_time'] ?? '';
    
    // Weekday: 1=Mon ... 6=Sat
    int day = 1;
    if (json['week_day_id'] != null) {
       int val = int.tryParse(json['week_day_id'].toString()) ?? 1;
       day = (val > 10) ? val - 10 : val;
    } else if (json['day_of_week'] != null) {
       int val = int.tryParse(json['day_of_week'].toString()) ?? 1;
       day = (val > 10) ? val - 10 : val;
    } else if (json['week_day'] != null) {
       day = int.tryParse(json['week_day'].toString()) ?? 1;
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
    );
  }
}
