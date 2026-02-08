import 'package:talabahamkor_mobile/core/constants/api_constants.dart';

class BannerModel {
  final int? id;
  final bool isActive;
  final String? imageFileId;
  final String? link;
  final String? createdAt;
  
  String get imageUrl => isActive && imageFileId != null 
      ? '${ApiConstants.fileProxy}/$imageFileId' 
      : '';

  BannerModel({
    this.id,
    required this.isActive,
    this.imageFileId,
    this.link,
    this.createdAt,
  });

  factory BannerModel.fromJson(Map<String, dynamic> json) {
    return BannerModel(
      id: json['id'],
      isActive: json['active'] ?? false,
      imageFileId: json['image_file_id'],
      link: json['link'],
      createdAt: json['created_at'],
    );
  }
}
