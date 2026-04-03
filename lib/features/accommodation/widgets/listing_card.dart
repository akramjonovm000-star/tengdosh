import 'package:flutter/material.dart';
import '../models/accommodation_listing.dart';
import '../../core/constants/api_constants.dart';
import 'package:intl/intl.dart';

class ListingCard extends StatefulWidget {
  final AccommodationListing listing;
  final VoidCallback onTap;

  const ListingCard({
    super.key,
    required this.listing,
    required this.onTap,
  });

  @override
  State<ListingCard> createState() => _ListingCardState();
}

class _ListingCardState extends State<ListingCard> {
  int _currentPage = 0;

  @override
  Widget build(BuildContext context) {
    // Combine old imageUrl and new imageUrls for backward compatibility
    final allImages = [...widget.listing.imageUrls];
    if (widget.listing.imageUrl != null && !allImages.contains(widget.listing.imageUrl)) {
      allImages.insert(0, widget.listing.imageUrl!);
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 15,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image Gallery (Swipeable)
            Stack(
              children: [
                SizedBox(
                  height: 220,
                  width: double.infinity,
                  child: allImages.isEmpty
                      ? _buildPlaceholder()
                      : PageView.builder(
                          itemCount: allImages.length,
                          onPageChanged: (index) {
                            setState(() => _currentPage = index);
                          },
                          itemBuilder: (context, index) {
                            final img = allImages[index];
                            // If it's a Telegram File ID (doesn't start with http), proxy it
                            final imageUrl = img.startsWith('http') 
                                ? img 
                                : '${ApiConstants.backendUrl}/files/$img';
                            
                            return Image.network(
                              imageUrl,
                              fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) => _buildPlaceholder(),
                            );
                          },
                        ),
                ),
                // Price Tag
                if (widget.listing.price != null)
                  Positioned(
                    top: 16,
                    right: 16,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.7),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        widget.listing.price!,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ),
                // Dot Indicator
                if (allImages.length > 1)
                  Positioned(
                    bottom: 12,
                    left: 0,
                    right: 0,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(
                        allImages.length,
                        (index) => Container(
                          margin: const EdgeInsets.symmetric(horizontal: 3),
                          width: _currentPage == index ? 10 : 6,
                          height: 6,
                          decoration: BoxDecoration(
                            color: _currentPage == index 
                                ? Colors.white 
                                : Colors.white.withOpacity(0.5),
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            
            // Text Content (Clickable)
            InkWell(
              onTap: widget.onTap,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.listing.title,
                      style: const TextStyle(
                        fontSize: 19,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 8),
                    if (widget.listing.address != null)
                      Row(
                        children: [
                          const Icon(Icons.location_on_rounded, size: 16, color: Colors.purple),
                          const SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              widget.listing.address!,
                              style: const TextStyle(
                                fontSize: 13,
                                color: Colors.purple,
                                fontWeight: FontWeight.w500,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    const SizedBox(height: 8),
                    Text(
                      widget.listing.description,
                      style: TextStyle(color: Colors.grey[600], fontSize: 14, height: 1.4),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        CircleAvatar(
                          radius: 14,
                          backgroundColor: Colors.purple[100],
                          child: Text(
                            widget.listing.studentName[0],
                            style: const TextStyle(fontSize: 11, color: Colors.purple, fontWeight: FontWeight.bold),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                widget.listing.studentName,
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              Text(
                                widget.listing.universityName ?? "Talaba",
                                style: TextStyle(fontSize: 11, color: Colors.grey[500]),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          DateFormat('dd.MM.yyyy').format(widget.listing.createdAt),
                          style: TextStyle(fontSize: 12, color: Colors.grey[400]),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlaceholder() {
    return Container(
      color: Colors.grey[100],
      child: const Center(
        child: Icon(Icons.broken_image_rounded, size: 50, color: Colors.grey),
      ),
    );
  }
}
