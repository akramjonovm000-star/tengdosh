import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import 'package:cached_network_image/cached_network_image.dart';

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  final TextEditingController _searchController = TextEditingController();
  String _selectedCategory = "Barchasi";

  final List<String> _categories = [
    "Barchasi",
    "Darsliklar",
    "O'quv qo'llanma",
    "Badiiy",
    "Lug'atlar"
  ];

  final List<Map<String, dynamic>> _mockBooks = [
    {
      "title": "O'zbek tili",
      "author": "A. Ergashev",
      "category": "Darsliklar",
      "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRz-Mh-4f6z_S0u93L-q1X_D9zXj9_C1Q&s",
      "rating": 4.8
    },
    {
      "title": "Matematika",
      "author": "Sh. Alimov",
      "category": "Darsliklar",
      "image": "https://lh3.googleusercontent.com/proxy/k6v-J04m6c7R-l3v-K4C1q-r7x_z_X5Zf_c_X5Zf_c",
      "rating": 4.5
    },
    {
      "title": "O'tkan kunlar",
      "author": "Abdulla Qodiriy",
      "category": "Badiiy",
      "image": "https://hilolnashr.uz/image/cache/catalog/1/Otkan-kunlar-500x500.jpg",
      "rating": 5.0
    },
    {
      "title": "Ingliz tili lug'ati",
      "author": "Oxford",
      "category": "Lug'atlar",
      "image": "https://m.media-amazon.com/images/I/71Y-tL-P2tL.jpg",
      "rating": 4.9
    }
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Kutubxona", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Column(
        children: [
          _buildSearchBar(),
          _buildCategories(),
          Expanded(child: _buildBookGrid()),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))
          ],
        ),
        child: TextField(
          controller: _searchController,
          decoration: const InputDecoration(
            hintText: "Kitob nomi yoki muallifni qidiring...",
            prefixIcon: Icon(Icons.search, color: Colors.grey),
            border: InputBorder.none,
            contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 15),
          ),
        ),
      ),
    );
  }

  Widget _buildCategories() {
    return SizedBox(
      height: 40,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.all(0),
        itemCount: _categories.length,
        itemBuilder: (context, index) {
          final cat = _categories[index];
          final isSelected = _selectedCategory == cat;
          return GestureDetector(
            onTap: () => setState(() => _selectedCategory = cat),
            child: Container(
              margin: EdgeInsets.only(left: 20, right: index == _categories.length - 1 ? 20 : 0),
              padding: const EdgeInsets.symmetric(horizontal: 20),
              decoration: BoxDecoration(
                color: isSelected ? AppTheme.primaryBlue : Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: isSelected ? Colors.transparent : Colors.grey[200]!),
              ),
              alignment: Alignment.center,
              child: Text(
                cat,
                style: TextStyle(
                  color: isSelected ? Colors.white : Colors.black87,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildBookGrid() {
    final filteredBooks = _mockBooks.where((b) {
      if (_selectedCategory == "Barchasi") return true;
      return b['category'] == _selectedCategory;
    }).toList();

    return GridView.builder(
      padding: const EdgeInsets.all(20),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 16,
        mainAxisSpacing: 20,
        childAspectRatio: 0.65,
      ),
      itemCount: filteredBooks.length,
      itemBuilder: (context, index) {
        final book = filteredBooks[index];
        return _buildBookCard(book);
      },
    );
  }

  Widget _buildBookCard(Map<String, dynamic> book) {
    return GestureDetector(
      onTap: () {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("${book['title']} tez orada qo'shiladi")),
        );
      },
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 10, offset: const Offset(0, 4))
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: CachedNetworkImage(
                  imageUrl: book['image'],
                  fit: BoxFit.cover,
                  width: double.infinity,
                  placeholder: (context, url) => Container(color: Colors.grey[200]),
                  errorWidget: (context, url, error) => Container(
                    color: Colors.grey[200],
                    child: const Icon(Icons.book, color: Colors.grey),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            book['title'],
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          Text(
            book['author'],
            style: TextStyle(color: Colors.grey[600], fontSize: 12),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              const Icon(Icons.star, color: Colors.amber, size: 14),
              const SizedBox(width: 4),
              Text(
                "${book['rating']}",
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
