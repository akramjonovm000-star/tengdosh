import 'package:talabahamkor_mobile/core/constants/api_constants.dart';

class BannerModel {
  final bool isActive;
  final String? imageFileId;
  final String? link;
  final String? createdAt;
  
  String get imageUrl => isActive && imageFileId != null 
      ? '${ApiConstants.fileProxy}/$imageFileId' 
      : '';

  BannerModel({
    required this.isActive,
    this.imageFileId,
    this.link,
    this.createdAt,
  });

  factory BannerModel.fromJson(Map<String, dynamic> json) {
    return BannerModel(
      isActive: json['active'] ?? false,
      imageFileId: json['image_file_id'],
      link: json['link'],
      created_at: json['created_at'],
    );
  }
}
