class AnnouncementModel {
  final int id;
  final String title;
  final String? content;
  final String? imageUrl;
  final String? link;
  final int priority;
  final DateTime createdAt;

  AnnouncementModel({
    required this.id,
    required this.title,
    this.content,
    this.imageUrl,
    this.link,
    required this.priority,
    required this.createdAt,
  });

  factory AnnouncementModel.fromJson(Map<String, dynamic> json) {
    return AnnouncementModel(
      id: json['id'],
      title: json['title'],
      content: json['content'],
      imageUrl: json['image_url'],
      link: json['link'],
      priority: json['priority'] ?? 0,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
