import 'package:talabahamkor_mobile/features/community/models/community_models.dart';

class Appeal {
  final int id;
  final String? title;
  final String? text;
  final String status;
  final String? recipient;
  final DateTime createdAt;
  final bool isAnonymous;
  final String? assignedRole;

  Appeal({
    required this.id,
    this.title,
    this.text,
    required this.status,
    this.recipient,
    required this.createdAt,
    this.isAnonymous = false,
    this.assignedRole,
  });

  factory Appeal.fromJson(Map<String, dynamic> json) {
    // Safe Date Parsing
    DateTime parsedDate;
    try {
      parsedDate = DateTime.parse(json['created_at'].toString());
    } catch (e) {
      parsedDate = DateTime.now(); // Fallback
    }

    return Appeal(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      title: json['title']?.toString() ?? "Murojaat #${json['id']}",
      text: json['text']?.toString(),
      status: json['status']?.toString() ?? 'pending',
      recipient: json['assigned_role']?.toString(), 
      createdAt: parsedDate,
      isAnonymous: json['is_anonymous'] == true || json['is_anonymous'] == "true",
      assignedRole: json['assigned_role']?.toString(),
    );
  }
  
  // Helper to format date
  String get formattedDate {
    return "${createdAt.day.toString().padLeft(2, '0')}.${createdAt.month.toString().padLeft(2, '0')}.${createdAt.year}";
  }
}

class AppealDetail {
  final int id;
  final String title;
  final String recipient;
  final String status;
  final String date;
  final bool isAnonymous;
  final List<AppealMessage> messages;

  AppealDetail({
    required this.id,
    required this.title,
    required this.recipient,
    required this.status,
    required this.date,
    required this.isAnonymous,
    required this.messages,
  });

  factory AppealDetail.fromJson(Map<String, dynamic> json) {
    var rawMessages = json['messages'] as List;
    List<AppealMessage> msgs = rawMessages.map((e) => AppealMessage.fromJson(e)).toList();

    return AppealDetail(
      id: json['id'],
      title: json['title'] ?? "Murojaat #${json['id']}",
      recipient: json['recipient'] ?? "General",
      status: json['status'],
      date: json['date'],
      isAnonymous: json['is_anonymous'] ?? false,
      messages: msgs,
    );
  }
}

class AppealMessage {
  final int id;
  final String sender; // 'me', 'staff', 'system'
  final String? text;
  final String time;
  final String? fileId;

  AppealMessage({
    required this.id,
    required this.sender,
    this.text,
    required this.time,
    this.fileId,
  });

  factory AppealMessage.fromJson(Map<String, dynamic> json) {
    return AppealMessage(
      id: json['id'],
      sender: json['sender'],
      text: json['text'],
      time: json['time'],
      fileId: json['file_id'],
    );
  }
}

class AppealStats {
  final int answered;
  final int pending;
  final int closed;

  AppealStats({
    required this.answered,
    required this.pending,
    required this.closed,
  });

  factory AppealStats.fromJson(Map<String, dynamic> json) {
    return AppealStats(
      answered: json['answered'] ?? 0,
      pending: json['pending'] ?? 0,
      closed: json['closed'] ?? 0,
    );
  }
}

class AppealsResponse {
  final List<Appeal> appeals;
  final AppealStats stats;

  AppealsResponse({
    required this.appeals,
    required this.stats,
  });

  factory AppealsResponse.fromJson(Map<String, dynamic> json) {
    var list = json['appeals'] as List;
    return AppealsResponse(
      appeals: list.map((i) => Appeal.fromJson(i)).toList(),
      stats: AppealStats.fromJson(json['stats']),
    );
  }
}
