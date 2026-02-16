import 'package:flutter/material.dart';
import '../models/book_model.dart';
import '../services/library_service.dart';
import '../widgets/book_card.dart';
import 'book_details_screen.dart';
import 'library_search_screen.dart';
import '../../../../core/theme/app_theme.dart';
import 'my_books/my_books_screen.dart';

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  final LibraryService _libraryService = LibraryService();
  
  // State
  Map<String, List<Book>> _booksByGenre = {};
  List<String> _genres = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    
    // Fetch all categories
    final allCategories = await _libraryService.getCategories();
    // Remove "Barchasi" as we want specific sections
    final genres = allCategories.where((c) => c != "Barchasi").toList();

    Map<String, List<Book>> genreUpdates = {};
    
    // In a real app, this should be an optimized batch query
    for (var genre in genres) {
      final books = await _libraryService.getBooks(category: genre);
      if (books.isNotEmpty) {
        genreUpdates[genre] = books;
      }
    }

    if (mounted) {
      setState(() {
        _genres = genreUpdates.keys.toList();
        _booksByGenre = genreUpdates;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        title: const Text("Kutubxona", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.search_rounded, color: Colors.black87),
            onPressed: () {
               Navigator.push(
                context, 
                MaterialPageRoute(builder: (_) => const LibrarySearchScreen())
              );
            },
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: IconButton(
              icon: const Icon(Icons.person_outline_rounded, color: Colors.black87),
              onPressed: () {
                 Navigator.push(
                  context, 
                  MaterialPageRoute(builder: (_) => const MyBooksScreen())
                );
              },
            ),
          ),
        ],
      ),
      body: _buildContent(),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_genres.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off_rounded, size: 64, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text("Hech narsa topilmadi", style: TextStyle(color: Colors.grey[500], fontSize: 16)),
          ],
        ),
      );
    }

    // Use ListView for Genre Sections
    return RefreshIndicator(
      onRefresh: _loadInitialData,
      child: ListView.builder(
        padding: const EdgeInsets.only(bottom: 20),
        itemCount: _genres.length,
        itemBuilder: (context, index) {
          final genre = _genres[index];
          final books = _booksByGenre[genre] ?? [];
          return _buildGenreSection(genre, books);
        },
      ),
    );
  }

  Widget _buildGenreSection(String title, List<Book> books) {
    if (books.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.black87),
              ),
              GestureDetector(
                onTap: () {
                  // Navigate to a "See All" screen for this genre
                  // For now, we interactively just show a toast or simplified action
                },
                child: const Row(
                  children: [
                    Text("Barchasi", style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.w600, fontSize: 14)),
                    SizedBox(width: 4),
                    Icon(Icons.arrow_forward_ios_rounded, size: 12, color: AppTheme.primaryBlue),
                  ],
                ),
              ),
            ],
          ),
        ),
        SizedBox(
          height: 280, // Height for horizontal list
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            scrollDirection: Axis.horizontal,
            itemCount: books.length,
            physics: const BouncingScrollPhysics(),
            itemBuilder: (context, index) {
              return Padding(
                padding: const EdgeInsets.only(right: 16),
                child: SizedBox(
                  width: 160, // Fixed width for each card in horizontal list
                  child: BookCard(
                    book: books[index],
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => BookDetailsScreen(book: books[index])),
                      );
                    },
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
