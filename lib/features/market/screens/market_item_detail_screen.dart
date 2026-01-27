import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/market_item.dart';
import '../services/market_service.dart';

class MarketItemDetailScreen extends StatelessWidget {
  final MarketItem item;
  final MarketService _marketService = MarketService();

  MarketItemDetailScreen({super.key, required this.item});

  void _launchPhone(String phone) async {
    final uri = Uri.parse("tel:$phone");
    if (await canLaunchUrl(uri)) await launchUrl(uri);
  }

  void _launchTelegram(String username) async {
    final uri = Uri.parse("https://t.me/${username.replaceAll('@', '')}");
    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    // Increment view count on load
    _marketService.viewItem(item.id);

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("Batafsil", style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
             // Image
             Container(
               width: double.infinity,
               height: 300,
               color: Colors.grey[100],
               child: item.imageUrl != null 
                   ? Image.network(item.imageUrl!, fit: BoxFit.contain)
                   : Icon(Icons.shopping_bag, size: 80, color: Colors.grey[300]),
             ),
             
             Padding(
               padding: const EdgeInsets.all(16),
               child: Column(
                 crossAxisAlignment: CrossAxisAlignment.start,
                 children: [
                    Text(
                      item.title,
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, fontFamily: 'Serif'),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      item.price ?? "Kelishilgan",
                      style: const TextStyle(fontSize: 18, color: AppTheme.primaryBlue, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        const CircleAvatar(
                          radius: 16, 
                          backgroundColor: Colors.grey, 
                          child: Icon(Icons.person, color: Colors.white, size: 16)
                        ),
                        const SizedBox(width: 8),
                        Text(item.studentName, style: const TextStyle(fontWeight: FontWeight.w500)),
                        const Spacer(),
                        Text("${item.viewsCount} ko'rish", style: const TextStyle(color: Colors.grey)),
                      ],
                    ),
                    const Divider(height: 32),
                    const Text("Tavsif", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const SizedBox(height: 8),
                    Text(item.description, style: const TextStyle(fontSize: 15, height: 1.4, color: Colors.black87)),
                    const SizedBox(height: 100), // Space for bottom bar
                 ],
               ),
             )
          ],
        ),
      ),
      bottomSheet: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, -5))]
        ),
        child: Row(
          children: [
            if (item.contactPhone != null)
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _launchPhone(item.contactPhone!),
                  icon: const Icon(Icons.phone),
                  label: const Text("Qo'ng'iroq"),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.green, padding: const EdgeInsets.symmetric(vertical: 12)),
                ),
              ),
            if (item.contactPhone != null && item.telegramUsername != null)
              const SizedBox(width: 16),
            if (item.telegramUsername != null)
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _launchTelegram(item.telegramUsername!),
                  icon: const Icon(Icons.send), // Telegram icon substitute
                  label: const Text("Telegram"),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.blue, padding: const EdgeInsets.symmetric(vertical: 12)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// Add 'viewItem' to MarketService if missing
extension MarketServiceExt on MarketService {
    Future<void> viewItem(int id) async {
        // Implementation logic
        // We need to add this to the actual MarketService class, not extension potentially
    }
}
