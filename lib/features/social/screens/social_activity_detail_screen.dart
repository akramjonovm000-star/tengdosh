import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/features/social/models/social_activity.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:talabahamkor_mobile/core/utils/uzbek_name_formatter.dart';

class SocialActivityDetailScreen extends StatelessWidget {
  final SocialActivity activity;

  const SocialActivityDetailScreen({super.key, required this.activity});

  @override
  Widget build(BuildContext context) {
    Color statusColor;
    String statusText;
    IconData statusIcon;

    switch(activity.status) {
      case "approved":
        statusColor = Colors.green;
        statusText = "Tasdiqlangan";
        statusIcon = Icons.check_circle_rounded;
        break;
      case "rejected":
        statusColor = Colors.red;
        statusText = "Rad etilgan";
        statusIcon = Icons.cancel_rounded;
        break;
      default:
        statusColor = Colors.orange;
        statusText = "Kutilmoqda";
        statusIcon = Icons.access_time_rounded;
    }

    return Scaffold(
      backgroundColor: Colors.white,
      body: CustomScrollView(
        slivers: [
          // 1. App Bar with Image
          SliverAppBar(
            expandedHeight: 300,
            pinned: true,
            automaticallyImplyLeading: true, // Standard back button
            flexibleSpace: FlexibleSpaceBar(
              background: Stack(
                fit: StackFit.expand,
                children: [
                   activity.imageUrls.isNotEmpty 
                    ? PageView.builder(
                        itemCount: activity.imageUrls.length > 1 ? 10000 : 1, // Infinite loop if > 1
                        onPageChanged: (index) {}, // Optional: Add indicator logic if needed
                        itemBuilder: (context, index) {
                          final imgIndex = index % activity.imageUrls.length;
                          return CachedNetworkImage(
                            imageUrl: activity.imageUrls[imgIndex],
                            fit: BoxFit.cover,
                            placeholder: (context, url) => const Center(child: CircularProgressIndicator()),
                            errorWidget: (context, url, error) => const Center(child: Icon(Icons.broken_image, color: Colors.grey)),
                          );
                        },
                      )
                    : Container(color: Colors.grey[300], child: const Icon(Icons.image, size: 50, color: Colors.grey)),
                ],
              ),
            ),
          ),

          // 2. Content
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Category & Status
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Chip(
                        label: Text(
                          UzbekNameFormatter.format(activity.category)
                        ),
                        backgroundColor: Colors.blue[50],
                        labelStyle: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: statusColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          children: [
                            Icon(statusIcon, color: statusColor, size: 18),
                            const SizedBox(width: 6),
                            Text(statusText, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Title
                  Text(
                    activity.title,
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, height: 1.3),
                  ),
                  const SizedBox(height: 8),
                  
                  // Date
                  Row(
                    children: [
                      Icon(Icons.calendar_today_rounded, size: 16, color: Colors.grey[600]),
                      const SizedBox(width: 6),
                      Text(activity.date, style: TextStyle(color: Colors.grey[600], fontSize: 14)),
                    ],
                  ),
                  const SizedBox(height: 24),
                  const Divider(),
                  const SizedBox(height: 24),

                  // Description
                  const Text(
                    "Tavsif",
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    activity.description,
                    style: TextStyle(fontSize: 16, color: Colors.grey[800], height: 1.6),
                  ),
                  
                  // Images Count Indicator if multiple
                  if (activity.imageUrls.length > 1) ...[
                    const SizedBox(height: 32),
                    Text(
                      "${activity.imageUrls.length} ta rasm yuklangan",
                      style: const TextStyle(color: Colors.grey, fontStyle: FontStyle.italic),
                    ),
                  ],

                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
