class MarketItem {
  final int id;
  final String title;
  final String description;
  final String? price;
  final String category;
  final String? imageUrl;
  final int viewsCount;
  final DateTime createdAt;
  final bool isMy;
  final String studentName;
  final String? contactPhone;
  final String? telegramUsername;

  MarketItem({
    required this.id,
    required this.title,
    required this.description,
    this.price,
    required this.category,
    this.imageUrl,
    required this.viewsCount,
    required this.createdAt,
    this.isMy = false,
    required this.studentName,
    this.contactPhone,
    this.telegramUsername,
  });

  factory MarketItem.fromJson(Map<String, dynamic> json) {
    return MarketItem(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      price: json['price'],
      category: json['category'],
      imageUrl: json['image_url'],
      viewsCount: json['views_count'] ?? 0,
      createdAt: DateTime.parse(json['created_at']),
      isMy: json['is_my'] ?? false,
      studentName: json['student_name'] ?? 'Talaba',
      contactPhone: json['contact_phone'],
      telegramUsername: json['telegram_username'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'description': description,
      'price': price,
      'category': category,
      'image_url': imageUrl,
      'contact_phone': contactPhone,
      'telegram_username': telegramUsername,
    };
  }
}
