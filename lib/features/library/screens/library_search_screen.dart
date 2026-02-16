import 'package:flutter/material.dart';
import '../models/book_model.dart';
import '../services/library_service.dart';
import '../widgets/book_card.dart';
import 'book_details_screen.dart';
import '../../../../core/theme/app_theme.dart';

class LibrarySearchScreen extends StatefulWidget {
  const LibrarySearchScreen({super.key});

  @override
  State<LibrarySearchScreen> createState() => _LibrarySearchScreenState();
}

class _LibrarySearchScreenState extends State<LibrarySearchScreen> {
  final LibraryService _libraryService = LibraryService();
  final TextEditingController _searchController = TextEditingController();
  
  // Data
  List<String> _genres = [];
  List<String> _authors = [];
  List<Book> _recommendedBooks = [];
  List<Book> _popularBooks = [];
  List<Book> _searchResults = [];
  
  bool _isLoading = true;
  bool _isSearching = false;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    
    final genres = await _libraryService.getCategories();
    final authors = await _libraryService.getAuthors();
    final recommended = await _libraryService.getRecommendedBooks();
    final popular = await _libraryService.getPopularBooks();

    if (mounted) {
      setState(() {
        _genres = genres.where((c) => c != "Barchasi").toList(); // Remove "All"
        _authors = authors;
        _recommendedBooks = recommended;
        _popularBooks = popular;
        _isLoading = false;
      });
    }
  }

  Future<void> _performSearch(String query) async {
    if (query.isEmpty) {
      setState(() {
        _isSearching = false;
        _searchResults = [];
      });
      return;
    }

    setState(() => _isSearching = true);
    
    // Simple debounce could be added here
    final results = await _libraryService.getBooks(query: query);
    
    if (mounted) {
      setState(() {
        _searchResults = results;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.black, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: Container(
          height: 40,
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(20),
          ),
          child: TextField(
            controller: _searchController,
            autofocus: true,
            onChanged: _performSearch,
            decoration: const InputDecoration(
              hintText: "Kitob, muallif, janr...",
              prefixIcon: Icon(Icons.search, color: Colors.grey),
              border: InputBorder.none,
              contentPadding: EdgeInsets.symmetric(vertical: 10),
            ),
          ),
        ),
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator())
        : _isSearching 
          ? _buildSearchResults()
          : _buildDiscoveryContent(),
    );
  }

  Widget _buildSearchResults() {
    if (_searchResults.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off_rounded, size: 64, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text("Natijalar topilmadi", style: TextStyle(color: Colors.grey[500], fontSize: 16)),
          ],
        ),
      );
    }
    
    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 0.65,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
      ),
      itemCount: _searchResults.length,
      itemBuilder: (context, index) {
        return BookCard(
          book: _searchResults[index], 
          onTap: () => _navigateToDetails(_searchResults[index]),
        );
      },
    );
  }

  Widget _buildDiscoveryContent() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Genres
          _buildSectionTitle("Janrlar"),
          _buildChipList(_genres, Icons.category_rounded, Colors.blue),
          
          const SizedBox(height: 24),
          
          // Authors
          _buildSectionTitle("Mualliflar"),
          _buildChipList(_authors, Icons.person_rounded, Colors.purple),

          const SizedBox(height: 32),
          
          // Recommended
          _buildSectionTitle("Sizga qiziq bo'lishi mumkin"),
          SizedBox(
            height: 240,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _recommendedBooks.length,
              physics: const BouncingScrollPhysics(),
              itemBuilder: (context, index) => Padding(
                padding: const EdgeInsets.only(right: 16),
                child: SizedBox(
                  width: 140,
                  child: BookCard(
                    book: _recommendedBooks[index], 
                    onTap: () => _navigateToDetails(_recommendedBooks[index]),
                  ),
                ),
              ),
            ),
          ),

          const SizedBox(height: 32),

          // Popular/Top Rated
          _buildSectionTitle("Eng ko'p o'qilgan"),
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _popularBooks.length,
            itemBuilder: (context, index) => _buildPopularBookItem(_popularBooks[index], index + 1),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87),
      ),
    );
  }

  Widget _buildChipList(List<String> items, IconData icon, Color color) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: items.map((item) {
        return ActionChip(
          avatar: Icon(icon, size: 16, color: color),
          label: Text(item),
          backgroundColor: Colors.white,
          elevation: 1,
          side: BorderSide(color: Colors.grey.withOpacity(0.1)),
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
          labelStyle: const TextStyle(fontWeight: FontWeight.w500, color: Colors.black87),
          onPressed: () {
            _searchController.text = item;
            _performSearch(item);
          },
        );
      }).toList(),
    );
  }

  Widget _buildPopularBookItem(Book book, int rank) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () => _navigateToDetails(book),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 8, offset: const Offset(0, 2))],
          ),
          child: Row(
            children: [
              Text(
                "#$rank",
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.900, color: Colors.grey),
              ),
              const SizedBox(width: 16),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.network(book.coverUrl, width: 40, height: 60, fit: BoxFit.cover),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(book.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    Text(book.author, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: Colors.grey[400]),
            ],
          ),
        ),
      ),
    );
  }

  void _navigateToDetails(Book book) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => BookDetailsScreen(book: book)),
    );
  }
}
