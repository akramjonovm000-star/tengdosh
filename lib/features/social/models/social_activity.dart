import 'package:talabahamkor_mobile/core/constants/api_constants.dart';

class SocialActivity {
  final String id;
  final String category;
  final String title;
  final String description;
  final String date;
  final String status; // 'approved', 'pending', 'rejected'
  final List<String> imageUrls;

  SocialActivity({
    required this.id,
    required this.category,
    required this.title,
    required this.description,
    required this.date,
    required this.status,
    required this.imageUrls,
  });

  factory SocialActivity.fromJson(Map<String, dynamic> json) {
    List<String> images = [];
    if (json['images'] != null) {
      for (var img in json['images']) {
        String fileId = img['file_id'] ?? "";
        if (fileId.isNotEmpty) {
          // Construct Proxy URL (The app will cache this result)
          images.add("${ApiConstants.backendUrl}/files/$fileId");
        }
      }
      print("SOCIAL ACTIVITY IMAGES: $images"); // DEBUG LOG
    }
    return SocialActivity(
      id: json['id'].toString(),
      category: (json['category'] ?? "Boshqa").toString().toLowerCase(),
      title: json['name'] ?? "Nomsiz",
      description: json['description'] ?? "",
      date: json['date'] ?? "",
      status: json['status'] ?? "pending",
      imageUrls: images,
    );
  }
}
