import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../services/library_service.dart';
import '../../models/reservation_model.dart';
import 'package:cached_network_image/cached_network_image.dart';

class MyBooksScreen extends StatefulWidget {
  const MyBooksScreen({super.key});

  @override
  State<MyBooksScreen> createState() => _MyBooksScreenState();
}

class _MyBooksScreenState extends State<MyBooksScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final LibraryService _libraryService = LibraryService();
  bool _isLoading = true;
  List<Reservation> _reservations = [];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadReservations();
  }

  Future<void> _loadReservations() async {
    setState(() => _isLoading = true);
    // Note: getReservations in LibraryService now returns mock Reservations
    final data = await _libraryService.getReservations();
    if (mounted) {
      setState(() {
        _reservations = data;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Mening Kitoblarim", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppTheme.primaryBlue,
          unselectedLabelColor: Colors.grey,
          indicatorColor: AppTheme.primaryBlue,
          tabs: const [
            Tab(text: "Bron"),
            Tab(text: "Navbat"),
            Tab(text: "Tarix"),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildList("reserved"),
                _buildList("queue"),
                _buildList("returned"),
              ],
            ),
    );
  }

  Widget _buildList(String filterStatus) {
    final filtered = _reservations.where((res) {
      if (filterStatus == "reserved") {
        return res.status == "reserved" || res.status == "borrowed" || res.status == "overdue";
      }
      return res.status == filterStatus;
    }).toList();

    if (filtered.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.bookmark_outline, size: 64, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              "Hozircha bo'sh",
              style: TextStyle(color: Colors.grey[600], fontSize: 16),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: filtered.length,
      itemBuilder: (context, index) {
        return _buildItemCard(filtered[index]);
      },
    );
  }

  Widget _buildItemCard(Reservation item) {
    Color statusColor = Colors.grey;
    String statusText = "";

    switch (item.status) {
      case 'reserved':
        statusColor = Colors.orange;
        statusText = "Bron qilingan";
        break;
      case 'borrowed':
        statusColor = Colors.green;
        statusText = "Olib ketilgan";
        break;
      case 'overdue':
        statusColor = Colors.red;
        statusText = "Muddati o'tgan";
        break;
      case 'queue':
        statusColor = Colors.purple;
        statusText = "Navbatda: ${item.queuePosition}-o'rin";
        break;
      case 'returned':
        statusColor = Colors.blueGrey;
        statusText = "Qaytarilgan";
        break;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: CachedNetworkImage(
                imageUrl: item.coverUrl,
                width: 60,
                height: 90,
                fit: BoxFit.cover,
                placeholder: (c, u) => Container(color: Colors.grey[200]),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.bookTitle,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      statusText,
                      style: TextStyle(color: statusColor, fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (item.status == 'reserved' && item.pickupDeadline != null)
                    Text(
                      "Olib ketish: ${item.pickupDeadline!.day}.${item.pickupDeadline!.month} gacha",
                      style: const TextStyle(color: Colors.grey, fontSize: 11),
                    ),
                  if (item.status == 'borrowed' && item.returnDeadLine != null)
                    Text(
                      "Qaytarish: ${item.returnDeadLine!.day}.${item.returnDeadLine!.month} gacha",
                      style: const TextStyle(color: Colors.grey, fontSize: 11),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
