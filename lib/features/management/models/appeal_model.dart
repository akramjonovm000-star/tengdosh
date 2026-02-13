class AppealStats {
  final int total;
  final Map<String, int> counts;
  final List<FacultyPerformance> facultyPerformance;
  final List<TopTarget> topTargets;

  AppealStats({
    required this.total,
    required this.counts,
    required this.facultyPerformance,
    required this.topTargets,
  });

  factory AppealStats.fromJson(Map<String, dynamic> json) {
    return AppealStats(
      total: json['total'] ?? 0,
      counts: Map<String, int>.from(json['counts'] ?? {}),
      facultyPerformance: (json['faculty_performance'] as List?)
              ?.map((e) => FacultyPerformance.fromJson(e))
              .toList() ??
          [],
      topTargets: (json['top_targets'] as List?)
              ?.map((e) => TopTarget.fromJson(e))
              .toList() ??
          [],
    );
  }
}

class FacultyPerformance {
  final int? id;
  final String faculty;
  final int total;
  final int resolved;
  final int pending;
  final int overdue;
  final double avgResponseTime;
  final double rate;
  final Map<String, int> topics;

  FacultyPerformance({
    this.id,
    required this.faculty,
    required this.total,
    required this.resolved,
    required this.pending,
    required this.overdue,
    required this.avgResponseTime,
    required this.rate,
    required this.topics,
  });

  factory FacultyPerformance.fromJson(Map<String, dynamic> json) {
    return FacultyPerformance(
      id: json['id'],
      faculty: json['faculty'] ?? "Noma'lum",
      total: json['total'] ?? 0,
      resolved: json['resolved'] ?? 0,
      pending: json['pending'] ?? 0,
      overdue: json['overdue'] ?? 0,
      avgResponseTime: (json['avg_response_time'] ?? 0).toDouble(),
      rate: (json['rate'] ?? 0).toDouble(),
      topics: Map<String, int>.from(json['topics'] ?? {}),
    );
  }
}

class TopTarget {
  final String role;
  final int count;

  TopTarget({required this.role, required this.count});

  factory TopTarget.fromJson(Map<String, dynamic> json) {
    return TopTarget(
      role: json['role'] ?? "Noma'lum",
      count: json['count'] ?? 0,
    );
  }
}

class Appeal {
  final int id;
  final String text;
  final String status;
  final String studentName;
  final String studentFaculty;
  final String? studentGroup;
  final String? studentPhone;
  final String? aiTopic;
  final String createdAt;
  final String assignedRole;
  final bool isAnonymous;

  Appeal({
    required this.id,
    required this.text,
    required this.status,
    required this.studentName,
    required this.studentFaculty,
    this.studentGroup,
    this.studentPhone,
    this.aiTopic,
    required this.createdAt,
    required this.assignedRole,
    this.isAnonymous = false,
  });

  factory Appeal.fromJson(Map<String, dynamic> json) {
    return Appeal(
      id: json['id'],
      text: json['text'] ?? "",
      status: json['status'] ?? "pending",
      studentName: json['student_name'] ?? "Noma'lum",
      studentFaculty: json['student_faculty'] ?? "Noma'lum",
      studentGroup: json['student_group'],
      studentPhone: json['student_phone'],
      aiTopic: json['ai_topic'],
      createdAt: json['created_at'] ?? "",
      assignedRole: json['assigned_role'] ?? "",
      isAnonymous: json['is_anonymous'] ?? false,
    );
  }
}
