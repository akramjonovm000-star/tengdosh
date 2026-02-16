import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../services/library_service.dart';
import '../../models/reservation_model.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../book_details_screen.dart';

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

  Future<void> _handleCancel(Reservation item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Bekor qilish"),
        content: Text("${item.bookTitle} ni bekor qilishni xohlaysizmi?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("Yo'q")),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text("Ha", style: TextStyle(color: Colors.red))),
        ],
      ),
    );

    if (confirmed == true) {
      // Simulate API call
      setState(() => _isLoading = true);
      await Future.delayed(const Duration(seconds: 1));
      
      // In real app, call service.cancelReservation(item.id)
      // updating local list for now
      setState(() {
        _reservations.remove(item);
        _isLoading = false;
      });
       if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Bekor qilindi")));
      }
    }
  }

  void _navigateToDetails(Reservation item) async { // Using BookId to fetch
      // For simplicity in this mock version, we aren't fetching the full book object if we don't have it.
      // But let's try to fetch it from service mock
      setState(() => _isLoading = true);
      final book = await _libraryService.getBookDetails(item.bookId);
      setState(() => _isLoading = false);

      if (mounted && book != null) {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => BookDetailsScreen(book: book)),
        );
      } else if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Kitob topilmadi")));
      }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA), // Soft gray-blue background
      appBar: AppBar(
        title: const Text("Mening Kitoblarim", style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold, fontSize: 22)),
        centerTitle: false,
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadAllData,
              child: Column(
                children: [
                   _buildStatsHeader(),
                   const SizedBox(height: 16),
                   _buildRoundedTabBar(),
                   const SizedBox(height: 16),
                   Expanded(
                     child: TabBarView(
                      controller: _tabController,
                      physics: const BouncingScrollPhysics(),
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

  Widget _buildRoundedTabBar() {
    return Container(
      height: 45,
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(25),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: TabBar(
        controller: _tabController,
        labelColor: Colors.white,
        unselectedLabelColor: Colors.grey[500],
        indicator: BoxDecoration(
          borderRadius: BorderRadius.circular(25),
          color: AppTheme.primaryBlue,
          boxShadow: [
            BoxShadow(color: AppTheme.primaryBlue.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 2)),
          ],
        ),
        indicatorSize: TabBarIndicatorSize.tab,
        dividerColor: Colors.transparent,
        labelPadding: EdgeInsets.zero, // Reduce padding to fit 4 tabs
        labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13), // Slightly smaller font
        tabs: const [
          Tab(text: "O'qish"),
          Tab(text: "Bron"),
          Tab(text: "Qo'lda"),
          Tab(text: "Tarix"),
        ],
      ),
    );
  }

  Widget _buildStatsHeader() {
    final readingCount = _readingList.length;
    final borrowedCount = _borrowed.length;
    final reservedCount = _reservations.length;

    return Container(
        margin: const EdgeInsets.symmetric(horizontal: 16),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [AppTheme.primaryBlue, AppTheme.primaryBlue.withOpacity(0.8)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(30),
          boxShadow: [
            BoxShadow(color: AppTheme.primaryBlue.withOpacity(0.3), blurRadius: 12, offset: const Offset(0, 6)),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildStatItem(Icons.menu_book_rounded, "$readingCount", "O'qilmoqda", Colors.white),
            Container(width: 1, height: 40, color: Colors.white.withOpacity(0.2)),
            _buildStatItem(Icons.bookmark_rounded, "$reservedCount", "Bron", Colors.white),
            Container(width: 1, height: 40, color: Colors.white.withOpacity(0.2)),
            _buildStatItem(Icons.local_library_rounded, "$borrowedCount", "Qo'lda", Colors.white),
          ],
        ),
    );
  }

  Widget _buildStatItem(IconData icon, String count, String label, Color color) {
    return Column(
      children: [
        Text(count, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 24, color: color)),
        const SizedBox(height: 4),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: color.withOpacity(0.8)),
            const SizedBox(width: 4),
            Text(label, style: TextStyle(color: color.withOpacity(0.8), fontSize: 12, fontWeight: FontWeight.w500)),
          ],
        ),
      ],
    );
  }

  Widget _buildReadingList() {
    if (_readingList.isEmpty) return _buildEmptyState("Hozircha elektron kitob o'qimayapsiz");
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
      physics: const BouncingScrollPhysics(),
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
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 15, offset: const Offset(0, 8))],
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Hero(
                  tag: 'cover_${item.id}',
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 8, offset: const Offset(0, 4))],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: CachedNetworkImage(
                        imageUrl: item.coverUrl,
                        width: 80,
                        height: 120,
                        fit: BoxFit.cover,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 20),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 4),
                      Text(item.bookTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17, color: Colors.black87), maxLines: 2, overflow: TextOverflow.ellipsis),
                      const SizedBox(height: 6),
                      Text(item.author, style: TextStyle(color: Colors.grey[600], fontSize: 13, fontWeight: FontWeight.w500)),
                      const SizedBox(height: 20),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                           Text("$percent%", style: const TextStyle(fontWeight: FontWeight.w800, color: AppTheme.primaryBlue, fontSize: 16)),
                           Text("${item.readPageCount}/${item.totalPageCount} bet", style: TextStyle(fontSize: 12, color: Colors.grey[500], fontWeight: FontWeight.w600)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: LinearProgressIndicator(
                          value: progress,
                          backgroundColor: Colors.grey[100],
                          valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryBlue),
                          minHeight: 8,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withOpacity(0.03),
              borderRadius: const BorderRadius.vertical(bottom: Radius.circular(24)),
            ),
            child: ElevatedButton(
              onPressed: () {}, // Navigate to reader
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryBlue,
                foregroundColor: Colors.white,
                elevation: 0,
                shadowColor: AppTheme.primaryBlue.withOpacity(0.4),
                shape: const StadiumBorder(),
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
              child: const Text("Davom ettirish", style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReservationList() {
    if (_reservations.isEmpty) return _buildEmptyState("Bron qilingan kitoblar yo'q");
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
      physics: const BouncingScrollPhysics(),
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
        borderRadius: BorderRadius.circular(24),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 15, offset: const Offset(0, 5))],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                 decoration: BoxDecoration(
                   borderRadius: BorderRadius.circular(12),
                   boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 5)],
                 ),
                 child: ClipRRect(borderRadius: BorderRadius.circular(12), child: CachedNetworkImage(imageUrl: item.coverUrl, width: 60, height: 90, fit: BoxFit.cover))
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                     Row(
                       mainAxisAlignment: MainAxisAlignment.spaceBetween,
                       crossAxisAlignment: CrossAxisAlignment.start,
                       children: [
                         Expanded(child: Text(item.bookTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, height: 1.2), maxLines: 2)),
                         const SizedBox(width: 8),
                         _buildStatusBadge(item.status),
                       ],
                     ),
                     const SizedBox(height: 6),
                     Text(item.author, style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                     const SizedBox(height: 10),
                     Container(
                       padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                       decoration: BoxDecoration(
                         color: isQueue ? Colors.purple.withOpacity(0.1) : Colors.orange.withOpacity(0.1),
                         borderRadius: BorderRadius.circular(10),
                       ),
                       child: Row(
                         mainAxisSize: MainAxisSize.min,
                         children: [
                           Icon(isQueue ? Icons.people_outline : Icons.access_time_rounded, size: 14, color: isQueue ? Colors.purple : Colors.orange),
                           const SizedBox(width: 6),
                           Text(
                             isQueue ? "${item.queuePosition}-o'rinda" : "3 soat qoldi", // Mock
                             style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12, color: isQueue ? Colors.purple : Colors.orange),
                           ),
                         ],
                       ),
                     ),
                      ),
                   ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextButton(
                  onPressed: () => _handleCancel(item), 
                  style: TextButton.styleFrom(
                    foregroundColor: Colors.red[400],
                    shape: const StadiumBorder(),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: const Text("Bekor qilish"),
                )
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    // Navigate to details if we can fetch the book
                    // For mock, we simply find the book in service or show unavailable
                    _navigateToDetails(item);
                  }, 
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFF0F5FF),
                    foregroundColor: AppTheme.primaryBlue,
                    elevation: 0,
                    shape: const StadiumBorder(),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: const Text("Batafsil"),
                )
              ),
            ],
          )
        ],
      ),
    );
  }

  void _navigateToDetails(Reservation item) async {
    // In real app, we might need to fetch full book details.
    // Here we use service to get book by ID.
    final book = await _libraryService.getBookDetails(item.bookId);
    if (mounted && book != null) {
       // We need to import BookDetailsScreen
       // Assuming it is accessible or needs import
    }
  }

  Widget _buildBorrowedList() {
    if (_borrowed.isEmpty) return _buildEmptyState("Olingan kitoblar mavjud emas");
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
      physics: const BouncingScrollPhysics(),
      itemCount: _borrowed.length,
      itemBuilder: (context, index) => _buildBorrowedCard(_borrowed[index]),
    );
  }

  Widget _buildBorrowedCard(Reservation item) {
    final daysLeft = item.returnDeadLine?.difference(DateTime.now()).inDays ?? 0;
    final isOverdue = daysLeft < 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: isOverdue ? Border.all(color: Colors.red.withOpacity(0.3), width: 1.5) : null,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 15, offset: const Offset(0, 5))],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
             Container(
               decoration: BoxDecoration(
                 borderRadius: BorderRadius.circular(12),
                 boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 5)],
               ),
               child: ClipRRect(borderRadius: BorderRadius.circular(12), child: CachedNetworkImage(imageUrl: item.coverUrl, width: 60, height: 90, fit: BoxFit.cover))
             ),
             const SizedBox(width: 16),
             Expanded(
               child: Column(
                 crossAxisAlignment: CrossAxisAlignment.start,
                 children: [
                   Text(item.bookTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                   const SizedBox(height: 4),
                   Text(item.author, style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                   const SizedBox(height: 12),
                   Container(
                     padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                     decoration: BoxDecoration(
                       color: isOverdue ? Colors.red.withOpacity(0.1) : Colors.green.withOpacity(0.1),
                       borderRadius: BorderRadius.circular(30),
                     ),
                     child: Row(
                       mainAxisSize: MainAxisSize.min,
                       children: [
                         Icon(isOverdue ? Icons.warning_amber_rounded : Icons.calendar_today_rounded, size: 14, color: isOverdue ? Colors.red : Colors.green),
                         const SizedBox(width: 6),
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
      ),
    );
  }

  Widget _buildHistoryList() {
     if (_history.isEmpty) return _buildEmptyState("Tarix bo'sh");
     return ListView.builder(
       padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
       physics: const BouncingScrollPhysics(),
       itemCount: _history.length,
       itemBuilder: (context, index) => _buildHistoryCard(_history[index]),
     );
  }

  Widget _buildHistoryCard(Reservation item) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 8, offset: const Offset(0, 2))],
      ),
      child: Row(
        children: [
           ClipRRect(borderRadius: BorderRadius.circular(10), child: CachedNetworkImage(imageUrl: item.coverUrl, width: 40, height: 60, fit: BoxFit.cover)),
           const SizedBox(width: 16),
           Expanded(
             child: Column(
               crossAxisAlignment: CrossAxisAlignment.start,
               children: [
                 Text(item.bookTitle, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
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
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(20)),
      child: Text(text, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildEmptyState(String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: Colors.grey.withOpacity(0.1), blurRadius: 20)],
            ),
            child: Icon(Icons.auto_stories_outlined, size: 50, color: Colors.grey[300]),
          ),
          const SizedBox(height: 24),
          Text(message, style: TextStyle(color: Colors.grey[500], fontSize: 16, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
