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
    return Appeal(
      id: json['id'],
      title: json['title'], // Backend might not send this yet on list view, but detail does
      text: json['text'],
      status: json['status'] ?? 'pending',
      recipient: json['assigned_role'], // Mapping assigned_role to recipient for UI
      createdAt: DateTime.parse(json['created_at']),
      isAnonymous: json['is_anonymous'] ?? false,
      assignedRole: json['assigned_role'],
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
