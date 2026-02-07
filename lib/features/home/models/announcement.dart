class Announcement {
  final int id;
  final String title;
  final String? content;
  final String? imageUrl;
  final String? link;
  final int priority;
  final DateTime createdAt;

  Announcement({
    required this.id,
    required this.title,
    this.content,
    this.imageUrl,
    this.link,
    required this.priority,
    required this.createdAt,
  });

  factory Announcement.fromJson(Map<String, dynamic> json) {
    return Announcement(
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
