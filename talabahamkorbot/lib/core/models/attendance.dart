class Attendance {
  final int id;
  final String subjectName;
  final String date;
  final String lessonTheme;
  final int hours;
  final bool isExcused; // true = sababli (11), false = sababsiz (12)

  Attendance({
    required this.id,
    required this.subjectName,
    required this.date,
    required this.lessonTheme,
    required this.hours,
    required this.isExcused,
  });

  factory Attendance.fromJson(Map<String, dynamic> json) {
    // Parsing logic based on standard HEMIS response structure
    // structure: { "subject": {"name": "Matematika"}, "date": "12.01.2024", "lesson": {"name": "Integrallar"}, "absent_status": 12 }
    
    final subject = json['subject'] != null ? json['subject']['name'] ?? 'Noma\'lum fan' : 'Noma\'lum fan';
    final lesson = json['lesson'] != null ? json['lesson']['name'] ?? 'Mavzu kiritilmagan' : 'Mavzu kiritilmagan';
    final dateStr = json['details']?['date'] ?? json['date'] ?? ''; 
    final hourVal = json['hour'] != null ? int.tryParse(json['hour'].toString()) ?? 2 : 2;
    
    // Status 11 = Sababli, 12 = Sababsiz
    // Also checking "is_valid" field which sometimes indicates excused status
    final int status = json['absent_status'] ?? 0;
    final bool valid = json['is_valid'] == true;
    final bool excused = status == 11 || valid;

    return Attendance(
      id: json['id'] ?? 0,
      subjectName: subject,
      date: dateStr,
      lessonTheme: lesson,
      hours: hourVal,
      isExcused: excused,
    );
  }
}
