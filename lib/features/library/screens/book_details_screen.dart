import 'package:flutter/material.dart';
import '../models/book_model.dart';
import '../../../../core/theme/app_theme.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'secure_reader_screen.dart';
import '../services/library_service.dart';

class BookDetailsScreen extends StatelessWidget {
  final Book book;

  const BookDetailsScreen({super.key, required this.book});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 320,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              background: Stack(
                fit: StackFit.expand,
                children: [
                  CachedNetworkImage(
                    imageUrl: book.coverUrl,
                    fit: BoxFit.cover,
                    placeholder: (context, url) => Container(color: Colors.grey[200]),
                  ),
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          Colors.transparent,
                          Colors.black.withOpacity(0.8),
                        ],
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 20,
                    left: 20,
                    right: 20,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          book.title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          book.author,
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.9),
                            fontSize: 16,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            backgroundColor: AppTheme.primaryBlue,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back, color: Colors.white),
              onPressed: () => Navigator.pop(context),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Meta Info Row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildMetaItem(Icons.star, "${book.rating}", "Reyting", Colors.amber),
                      _buildMetaItem(Icons.category, book.genre, "Janr", Colors.blue),
                      _buildMetaItem(
                        Icons.library_books,
                        "${book.availableCopies}/${book.totalCopies}",
                        "Mavjud",
                        book.availableCopies > 0 ? Colors.green : Colors.red,
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  
                  // Action Button
                  if (book.isEbookAvailable)
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton.icon(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => SecureReaderScreen(book: book)),
                          );
                        },
                        icon: const Icon(Icons.menu_book),
                        label: const Text("Elektron o'qish"),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryBlue,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          elevation: 2,
                        ),
                      ),
                    )
                  else
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.orange.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.orange.withOpacity(0.3)),
                      ),
                      child: const Center(
                        child: Text(
                          "Elektron variant mavjud emas",
                          style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  
                  const SizedBox(height: 24),
                  
                  const Text(
                    "Tavsif",
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    book.description,
                    style: TextStyle(fontSize: 15, height: 1.6, color: Colors.grey[800]),
                  ),
                  const SizedBox(height: 30),
                  
                  // Additional Metadata
                  _buildDetailRow("Nashr qilingan sana", "${book.publishedDate.year}"),
                  _buildDetailRow("ISBN", "978-3-16-148410-0"), // Mock
                  _buildDetailRow("Sahifalar soni", "320"), // Mock
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetaItem(IconData icon, String value, String label, Color color) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 24),
        ),
        const SizedBox(height: 8),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
      ],
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 14)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        ],
      ),
    );
  }

  void _handleReservation(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) => _ReservationSheet(book: book),
    );
  }
}

class _ReservationSheet extends StatefulWidget {
  final Book book;

  const _ReservationSheet({required this.book});

  @override
  State<_ReservationSheet> createState() => _ReservationSheetState();
}

class _ReservationSheetState extends State<_ReservationSheet> {
  final LibraryService _libraryService = LibraryService();
  bool _isLoading = false;
  bool _isSuccess = false;

  void _submit() async {
    setState(() => _isLoading = true);
    try {
      if (widget.book.availableCopies > 0) {
        await _libraryService.reserveBook(widget.book.id);
      } else {
        await _libraryService.addToQueue(widget.book.id);
      }
      
      setState(() {
        _isLoading = false;
        _isSuccess = true;
      });

      // Close after delay
      await Future.delayed(const Duration(seconds: 2));
      if (mounted) Navigator.pop(context);

    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Xatolik: $e")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isAvailable = widget.book.availableCopies > 0;

    if (_isSuccess) {
      return Container(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check_circle_outline_rounded, size: 80, color: Colors.green),
            const SizedBox(height: 20),
            Text(
              isAvailable ? "Muvaffaqiyatli bron qilindi!" : "Navbatga yozildingiz!",
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            const Text(
              "Mening kitoblarim bo'limida ko'rishingiz mumkin",
              style: TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            isAvailable ? "Bron qilishni tasdiqlang" : "Navbatga yozilish",
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: CachedNetworkImage(
                  imageUrl: widget.book.coverUrl,
                  width: 50,
                  height: 75,
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(widget.book.title, style: const TextStyle(fontWeight: FontWeight.bold)),
                    Text(widget.book.author, style: const TextStyle(color: Colors.grey)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          if (isAvailable) ...[
             _buildInfoRow(Icons.calendar_today, "Olib ketish muddati", "3 kun ichida"),
             const SizedBox(height: 12),
             _buildInfoRow(Icons.update, "Qaytarish muddati", "14 kun"),
          ] else
             const Text(
               "Hozirda barcha nusxalar band. Navbatga yozilsangiz, kitob qaytishi bilan sizga habar beramiz.",
               style: TextStyle(color: Colors.grey, height: 1.5),
             ),
          
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: isAvailable ? Colors.orange : Colors.indigo,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: _isLoading 
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : Text(isAvailable ? "Tasdiqlash" : "Navbatga yozilish", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, size: 20, color: Colors.blueGrey),
        const SizedBox(width: 12),
        Expanded(child: Text(label, style: const TextStyle(color: Colors.black87))),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
      ],
    );
  }
}
