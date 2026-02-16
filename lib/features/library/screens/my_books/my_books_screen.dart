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
  
  // Data Lists
  List<Reservation> _readingList = [];
  List<Reservation> _reservations = [];
  List<Reservation> _borrowed = [];
  List<Reservation> _history = [];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadAllData();
  }

  Future<void> _loadAllData() async {
    setState(() => _isLoading = true);
    try {
      final results = await Future.wait([
        _libraryService.getReadingList(),
        _libraryService.getReservations(),
        _libraryService.getBorrowedBooks(),
        _libraryService.getHistory(),
      ]);

      if (mounted) {
        setState(() {
          _readingList = results[0];
          _reservations = results[1];
          _borrowed = results[2];
          _history = results[3];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
         setState(() => _isLoading = false);
      }
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
          isScrollable: true,
          tabs: const [
            Tab(text: "O'qilayotgan"),
            Tab(text: "Bron qilingan"),
            Tab(text: "Olingan"),
            Tab(text: "Tarix"),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadAllData,
              child: Column(
                children: [
                   _buildStatsHeader(),
                   Expanded(
                     child: TabBarView(
                      controller: _tabController,
                      children: [
                        _buildReadingList(),
                        _buildReservationList(),
                        _buildBorrowedList(),
                        _buildHistoryList(),
                      ],
                                       ),
                   ),
                ],
              ),
            ),
    );
  }

  Widget _buildStatsHeader() {
    final readingCount = _readingList.length;
    final borrowedCount = _borrowed.length;
    final reservedCount = _reservations.length;

    return Container( // Stats container
        color: Colors.white,
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
        margin: const EdgeInsets.only(bottom: 8),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _buildStatItem(Icons.menu_book, "$readingCount", "O'qilmoqda"),
            _buildStatItem(Icons.bookmark_added, "$reservedCount", "Bron"),
            _buildStatItem(Icons.local_library, "$borrowedCount", "Olingan"),
          ],
        ),
    );
  }

  Widget _buildStatItem(IconData icon, String count, String label) {
    return Column(
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 18, color: AppTheme.primaryBlue),
            const SizedBox(width: 6),
            Text(count, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          ],
        ),
        Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
      ],
    );
  }

  Widget _buildReadingList() {
    if (_readingList.isEmpty) return _buildEmptyState("Hozircha elektron kitob o'qimayapsiz");
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _readingList.length,
      itemBuilder: (context, index) {
        final item = _readingList[index];
        return _buildReadingCard(item);
      },
    );
  }

  Widget _buildReadingCard(Reservation item) {
    final progress = item.progress ?? 0.0;
    final percent = (progress * 100).toInt();

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: CachedNetworkImage(
              imageUrl: item.coverUrl,
              width: 70,
              height: 100,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.bookTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16), maxLines: 1, overflow: TextOverflow.ellipsis),
                Text(item.author, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                     Text("$percent%", style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue)),
                     Text("${item.readPageCount}/${item.totalPageCount} bet", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
                const SizedBox(height: 6),
                LinearProgressIndicator(
                  value: progress,
                  backgroundColor: Colors.grey[200],
                  valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryBlue),
                  minHeight: 6,
                  borderRadius: BorderRadius.circular(3),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  height: 36,
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: () {}, // Navigate to reader
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.primaryBlue,
                      side: const BorderSide(color: AppTheme.primaryBlue),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    child: const Text("Davom ettirish"),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReservationList() {
    if (_reservations.isEmpty) return _buildEmptyState("Bron qilingan kitoblar yo'q");
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _reservations.length,
      itemBuilder: (context, index) => _buildReservationCard(_reservations[index]),
    );
  }

  Widget _buildReservationCard(Reservation item) {
    final isQueue = item.status == 'queue';
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: Column(
        children: [
          Row(
            children: [
              ClipRRect(borderRadius: BorderRadius.circular(8), child: CachedNetworkImage(imageUrl: item.coverUrl, width: 50, height: 75, fit: BoxFit.cover)),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                     Row(
                       mainAxisAlignment: MainAxisAlignment.spaceBetween,
                       children: [
                         Expanded(child: Text(item.bookTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16), maxLines: 1)),
                         _buildStatusBadge(item.status),
                       ],
                     ),
                     const SizedBox(height: 4),
                     Text(item.author, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                     const SizedBox(height: 8),
                     if (isQueue) 
                        Text("Navbatda: ${item.queuePosition}-o'rin", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.purple))
                     else 
                        Text("Olib ketish: ${item.pickupDeadline!.difference(DateTime.now()).inHours} soat qoldi", style: const TextStyle(color: Colors.orange, fontWeight: FontWeight.bold, fontSize: 12)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(child: OutlinedButton(onPressed: () {}, child: const Text("Bekor qilish", style: TextStyle(color: Colors.red)))),
              const SizedBox(width: 12),
              Expanded(child: ElevatedButton(onPressed: () {}, style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryBlue), child: const Text("Batafsil", style: TextStyle(color: Colors.white)))),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildBorrowedList() {
    if (_borrowed.isEmpty) return _buildEmptyState("Olingan kitoblar mavjud emas");
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _borrowed.length,
      itemBuilder: (context, index) => _buildBorrowedCard(_borrowed[index]),
    );
  }

  Widget _buildBorrowedCard(Reservation item) {
    final daysLeft = item.returnDeadLine?.difference(DateTime.now()).inDays ?? 0;
    final isOverdue = daysLeft < 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: isOverdue ? Border.all(color: Colors.red.withOpacity(0.5), width: 1) : null,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: Row(
        children: [
           ClipRRect(borderRadius: BorderRadius.circular(8), child: CachedNetworkImage(imageUrl: item.coverUrl, width: 60, height: 90, fit: BoxFit.cover)),
           const SizedBox(width: 16),
           Expanded(
             child: Column(
               crossAxisAlignment: CrossAxisAlignment.start,
               children: [
                 Text(item.bookTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                 const SizedBox(height: 4),
                 Text(item.author, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                 const SizedBox(height: 8),
                 Container(
                   padding: const EdgeInsets.all(8),
                   decoration: BoxDecoration(
                     color: isOverdue ? Colors.red.withOpacity(0.1) : Colors.green.withOpacity(0.1),
                     borderRadius: BorderRadius.circular(8),
                   ),
                   child: Row(
                     mainAxisSize: MainAxisSize.min,
                     children: [
                       Icon(Icons.access_time, size: 14, color: isOverdue ? Colors.red : Colors.green),
                       const SizedBox(width: 4),
                       Text(
                         isOverdue ? "${daysLeft.abs()} kun kechikdi" : "$daysLeft kun qoldi",
                         style: TextStyle(color: isOverdue ? Colors.red : Colors.green, fontWeight: FontWeight.bold, fontSize: 12),
                       ),
                     ],
                   ),
                 ),
               ],
             ),
           ),
        ],
      ),
    );
  }

  Widget _buildHistoryList() {
     if (_history.isEmpty) return _buildEmptyState("Tarix bo'sh");
     return ListView.builder(
       padding: const EdgeInsets.all(16),
       itemCount: _history.length,
       itemBuilder: (context, index) => _buildHistoryCard(_history[index]),
     );
  }

  Widget _buildHistoryCard(Reservation item) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
      child: Row(
        children: [
           ClipRRect(borderRadius: BorderRadius.circular(6), child: CachedNetworkImage(imageUrl: item.coverUrl, width: 40, height: 60, fit: BoxFit.cover)),
           const SizedBox(width: 12),
           Expanded(
             child: Column(
               crossAxisAlignment: CrossAxisAlignment.start,
               children: [
                 Text(item.bookTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                 Text(item.author, style: const TextStyle(color: Colors.grey, fontSize: 12)),
               ],
             ),
           ),
           _buildStatusBadge(item.status),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color color = Colors.grey;
    String text = status;

    switch (status) {
      case 'reserved': color = Colors.orange; text = "Bron"; break;
      case 'queue': color = Colors.purple; text = "Navbat"; break;
      case 'borrowed': color = Colors.blue; text = "Olingan"; break;
      case 'returned': color = Colors.green; text = "Qaytarildi"; break;
      case 'overdue': color = Colors.red; text = "Qarzdor"; break;
      case 'cancelled': color = Colors.red; text = "Bekor"; break;
      case 'reading': color = Colors.blue; text = "O'qilmoqda"; break;
      case 'completed': color = Colors.teal; text = "Tugatildi"; break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(6)),
      child: Text(text, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildEmptyState(String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inbox_rounded, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(message, style: TextStyle(color: Colors.grey[500], fontSize: 16)),
        ],
      ),
    );
  }
}
