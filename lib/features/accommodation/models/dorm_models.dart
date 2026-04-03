class DormRoommate {
  final int id;
  final String fullName;
  final String? groupNumber;
  final String? imageUrl;

  DormRoommate({
    required this.id,
    required this.fullName,
    this.groupNumber,
    this.imageUrl,
  });

  factory DormRoommate.fromJson(Map<String, dynamic> json) {
    return DormRoommate(
      id: json['id'],
      fullName: json['full_name'],
      groupNumber: json['group_number'],
      imageUrl: json['image_url'],
    );
  }
}

class DormIssue {
  final int id;
  final String category;
  final String description;
  final List<String> imageUrls;
  final String status;
  final DateTime createdAt;

  DormIssue({
    required this.id,
    required this.category,
    required this.description,
    required this.imageUrls,
    required this.status,
    required this.createdAt,
  });

  factory DormIssue.fromJson(Map<String, dynamic> json) {
    return DormIssue(
      id: json['id'],
      category: json['category'],
      description: json['description'],
      imageUrls: List<String>.from(json['image_urls'] ?? []),
      status: json['status'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class DormRule {
  final int id;
  final String title;
  final String content;
  final String importance;

  DormRule({
    required this.id,
    required this.title,
    required this.content,
    required this.importance,
  });

  factory DormRule.fromJson(Map<String, dynamic> json) {
    return DormRule(
      id: json['id'],
      title: json['title'],
      content: json['content'],
      importance: json['importance'],
    );
  }
}

class DormMenu {
  final int id;
  final String dayName;
  final String? breakfast;
  final String? lunch;
  final String? dinner;

  DormMenu({
    required this.id,
    required this.dayName,
    this.breakfast,
    this.lunch,
    this.dinner,
  });

  factory DormMenu.fromJson(Map<String, dynamic> json) {
    return DormMenu(
      id: json['id'],
      dayName: json['day_name'],
      breakfast: json['breakfast'],
      lunch: json['lunch'],
      dinner: json['dinner'],
    );
  }
}

class DormRoster {
  final int id;
  final String studentName;
  final String dayOfWeek;
  final String dutyType;

  DormRoster({
    required this.id,
    required this.studentName,
    required this.dayOfWeek,
    required this.dutyType,
  });

  factory DormRoster.fromJson(Map<String, dynamic> json) {
    return DormRoster(
      id: json['id'],
      studentName: json['student_name'],
      dayOfWeek: json['day_of_week'],
      dutyType: json['duty_type'],
    );
  }
}
