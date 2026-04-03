class AccommodationListing {
  final int id;
  final String title;
  final String description;
  final String? price;
  final String category;
  final String? imageUrl;
  final List<String> imageUrls;
  final String? address;
  final int viewsCount;
  final DateTime createdAt;
  final bool isMy;
  final String studentName;
  final String? contactPhone;
  final String? telegramUsername;
  final String? universityName;

  AccommodationListing({
    required this.id,
    required this.title,
    required this.description,
    this.price,
    required this.category,
    this.imageUrl,
    this.imageUrls = const [],
    this.address,
    required this.viewsCount,
    required this.createdAt,
    required this.isMy,
    required this.studentName,
    this.contactPhone,
    this.telegramUsername,
    this.universityName,
  });

  factory AccommodationListing.fromJson(Map<String, dynamic> json) {
    return AccommodationListing(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      price: json['price'],
      category: json['category'],
      imageUrl: json['image_url'],
      imageUrls: List<String>.from(json['image_urls'] ?? []),
      address: json['address'],
      viewsCount: json['views_count'] ?? 0,
      createdAt: DateTime.parse(json['created_at']),
      isMy: json['is_my'] ?? false,
      studentName: json['student_name'] ?? 'Noma\'lum',
      contactPhone: json['contact_phone'],
      telegramUsername: json['telegram_username'],
      universityName: json['university_name'],
    );
  }
}
