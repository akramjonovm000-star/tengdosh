import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/accommodation_listing.dart';
import '../../core/constants/api_constants.dart';
import '../../core/theme/app_theme.dart';
import 'package:intl/intl.dart';

class ListingDetailsScreen extends StatefulWidget {
  final AccommodationListing listing;

  const ListingDetailsScreen({super.key, required this.listing});

  @override
  State<ListingDetailsScreen> createState() => _ListingDetailsScreenState();
}

class _ListingDetailsScreenState extends State<ListingDetailsScreen> {
  int _currentImageIndex = 0;

  @override
  Widget build(BuildContext context) {
    final allImages = [...widget.listing.imageUrls];
    if (widget.listing.imageUrl != null && !allImages.contains(widget.listing.imageUrl)) {
      allImages.insert(0, widget.listing.imageUrl!);
    }

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 350,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              background: Stack(
                fit: StackFit.expand,
                children: [
                  PageView.builder(
                    itemCount: allImages.length,
                    onPageChanged: (i) => setState(() => _currentImageIndex = i),
                    itemBuilder: (context, index) {
                      final img = allImages[index];
                      final imageUrl = img.startsWith('http') 
                          ? img 
                          : '${ApiConstants.backendUrl}/files/$img';
                      
                      return Image.network(
                        imageUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => Container(
                          color: Colors.grey[200],
                          child: const Icon(Icons.broken_image_rounded, size: 50),
                        ),
                      );
                    },
                  ),
                  if (allImages.length > 1)
                     Positioned(
                      bottom: 20,
                      left: 0,
                      right: 0,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(
                          allImages.length,
                          (index) => Container(
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            width: _currentImageIndex == index ? 12 : 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: _currentImageIndex == index 
                                  ? Colors.white 
                                  : Colors.white.withOpacity(0.5),
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          widget.listing.title,
                          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                        ),
                      ),
                      if (widget.listing.price != null)
                        Text(
                          widget.listing.price!,
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: Colors.purple,
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (widget.listing.address != null)
                    Row(
                      children: [
                        const Icon(Icons.location_on_rounded, color: Colors.purple, size: 18),
                        const SizedBox(width: 6),
                        Text(
                          widget.listing.address!,
                          style: const TextStyle(fontSize: 15, color: Colors.purple, fontWeight: FontWeight.w500),
                        ),
                      ],
                    ),
                  const SizedBox(height: 24),
                  const Text(
                    "Ma'lumot:",
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    widget.listing.description,
                    style: const TextStyle(fontSize: 16, height: 1.5, color: Colors.black87),
                  ),
                  const SizedBox(height: 32),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.grey[200]!),
                    ),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 25,
                          backgroundColor: Colors.purple[50],
                          child: Text(
                            widget.listing.studentName[0],
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.purple),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                widget.listing.studentName,
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              Text(
                                widget.listing.universityName ?? "Talaba",
                                style: TextStyle(color: Colors.grey[600], fontSize: 13),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 100), // Spacing for buttons
                ],
              ),
            ),
          ),
        ],
      ),
      bottomSheet: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, -5)),
          ],
        ),
        child: Row(
          children: [
            if (widget.listing.contactPhone != null)
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _call(widget.listing.contactPhone!),
                  icon: const Icon(Icons.phone_rounded, color: Colors.white),
                  label: const Text("Qo'ng'iroq", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
            if (widget.listing.contactPhone != null && widget.listing.telegramUsername != null)
              const SizedBox(width: 12),
            if (widget.listing.telegramUsername != null)
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _openTelegram(widget.listing.telegramUsername!),
                  icon: const Icon(Icons.send_rounded, color: Colors.white),
                  label: const Text("Telegram", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _call(String phone) async {
    final url = Uri.parse("tel:$phone");
    if (await canLaunchUrl(url)) await launchUrl(url);
  }

  Future<void> _openTelegram(String username) async {
    final url = Uri.parse("https://t.me/$username");
    if (await canLaunchUrl(url)) await launchUrl(url, mode: LaunchMode.externalApplication);
  }
}
