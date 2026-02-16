import 'package:flutter/material.dart';
import '../models/book_model.dart';
import '../services/library_service.dart';
import '../widgets/book_card.dart';
import '../widgets/library_filter_sheet.dart';
import 'book_details_screen.dart';
import '../../../../core/theme/app_theme.dart';
import 'my_books/my_books_screen.dart';

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  final LibraryService _libraryService = LibraryService();
  final TextEditingController _searchController = TextEditingController();
  
  // State
  List<Book> _books = [];
  List<String> _categories = ["Barchasi"];
  bool _isLoading = true;

  // Filters
  String _selectedCategory = "Barchasi";
  bool _availableOnly = false;
  bool _ebookOnly = false;
  String _sortBy = "popular";
  String _searchQuery = "";

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    final cats = await _libraryService.getCategories();
    if (mounted) {
      setState(() {
        _categories = cats;
      });
      _loadBooks();
    }
  }

  Future<void> _loadBooks() async {
    setState(() => _isLoading = true);
    try {
      final books = await _libraryService.getBooks(
        query: _searchQuery,
        category: _selectedCategory,
        availableOnly: _availableOnly,
        ebookOnly: _ebookOnly,
        sortBy: _sortBy,
      );
      if (mounted) {
        setState(() {
          _books = books;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Xatolik: $e")),
        );
      }
    }
  }

  void _onSearchChanged(String query) {
    // Debounce handled by Stream or simple delay in real app
    // For mock, just set state
    if (_searchQuery != query) {
      setState(() {
        _searchQuery = query;
      });
      _loadBooks();
    }
  }

  void _openFilterSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => LibraryFilterSheet(
        categories: _categories,
        initialCategory: _selectedCategory,
        initialAvailableOnly: _availableOnly,
        initialEbookOnly: _ebookOnly,
        initialSortBy: _sortBy,
        onApply: (cat, avail, ebook, sort) {
          setState(() {
            _selectedCategory = cat;
            _availableOnly = avail;
            _ebookOnly = ebook;
            _sortBy = sort;
          });
          _loadBooks();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Kutubxona", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          IconButton(
            icon: const Icon(Icons.bookmark_border_rounded),
            onPressed: () {
               Navigator.push(
                context, 
                MaterialPageRoute(builder: (_) => const MyBooksScreen())
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.filter_list_rounded),
            onPressed: _openFilterSheet,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildSearchBar(),
          _buildCategories(),
          Expanded(child: _buildContent()),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 10),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: TextField(
          controller: _searchController,
          onChanged: _onSearchChanged,
          decoration: const InputDecoration(
            hintText: "Kitob, muallif yoki janr...",
            prefixIcon: Icon(Icons.search, color: Colors.grey),
            border: InputBorder.none,
            contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 15),
          ),
        ),
      ),
    );
  }

  Widget _buildCategories() {
    return Container(
      height: 50,
      margin: const EdgeInsets.only(bottom: 10),
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        scrollDirection: Axis.horizontal,
        itemCount: _categories.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final cat = _categories[index];
          final isSelected = _selectedCategory == cat;
          return ChoiceChip(
            label: Text(cat),
            selected: isSelected,
            onSelected: (val) {
              setState(() {
                _selectedCategory = cat;
              });
              _loadBooks();
            },
            selectedColor: AppTheme.primaryBlue,
            backgroundColor: Colors.white,
            labelStyle: TextStyle(
              color: isSelected ? Colors.white : Colors.black87,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
            elevation: isSelected ? 2 : 0,
            pressElevation: 1,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
              side: BorderSide(color: isSelected ? Colors.transparent : Colors.grey[200]!),
            ),
          );
        },
      ),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_books.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.menu_book_rounded, size: 64, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              "Kitoblar topilmadi",
              style: TextStyle(fontSize: 18, color: Colors.grey[600], fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              "Qidiruvni o'zgartirib ko'ring",
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadBooks,
      child: GridView.builder(
        padding: const EdgeInsets.all(20),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          crossAxisSpacing: 16,
          mainAxisSpacing: 20,
          childAspectRatio: 0.62, // Adjusted for BookCard height
        ),
        itemCount: _books.length,
        itemBuilder: (context, index) {
          return BookCard(
            book: _books[index],
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => BookDetailsScreen(book: _books[index])),
              );
            },
          );
        },
      ),
    );
  }
}
