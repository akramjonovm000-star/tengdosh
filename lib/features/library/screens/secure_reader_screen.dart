import 'package:flutter/material.dart';
import '../models/book_model.dart';
import '../../../../core/theme/app_theme.dart';

class SecureReaderScreen extends StatefulWidget {
  final Book book;

  const SecureReaderScreen({super.key, required this.book});

  @override
  State<SecureReaderScreen> createState() => _SecureReaderScreenState();
}

class _SecureReaderScreenState extends State<SecureReaderScreen> {
  // Placeholder pages content
  final List<String> _pages = [
    "1-mavzu. Kirish.\n\nBugungi kunda axborot texnologiyalari...",
    "2-mavzu. Asosiy tushunchalar.\n\nAlgoritm bu - ketma-ketlik...",
    "3-mavzu. Dasturlash tillari.\n\nPython, Java, C++...",
    // Add more mock pages
  ];

  int _currentPage = 0;
  bool _isDarkMode = false;

  @override
  void initState() {
    super.initState();
    // In a real app, we would add FLAG_SECURE here using platform channel
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _isDarkMode ? const Color(0xFF1E1E1E) : Colors.white,
      appBar: AppBar(
        title: Text(widget.book.title, style: TextStyle(color: _isDarkMode ? Colors.white : Colors.black, fontSize: 16)),
        backgroundColor: _isDarkMode ? Colors.black : Colors.white,
        elevation: 0,
        iconTheme: IconThemeData(color: _isDarkMode ? Colors.white : Colors.black),
        actions: [
          IconButton(
            icon: Icon(_isDarkMode ? Icons.light_mode : Icons.dark_mode),
            onPressed: () => setState(() => _isDarkMode = !_isDarkMode),
          ),
        ],
      ),
      body: Stack(
        children: [
          // Content
          Column(
            children: [
              Expanded(
                child: PageView.builder(
                  itemCount: _pages.length,
                  onPageChanged: (index) => setState(() => _currentPage = index),
                  itemBuilder: (context, index) {
      return Container(
                        padding: const EdgeInsets.all(24),
                        alignment: Alignment.center,
                        child: SingleChildScrollView(
                          child: Text(
                            _pages[index], // No Copy/Paste allowed by default on Text widget
                            style: TextStyle(
                              fontSize: 18,
                              height: 1.6,
                              fontFamily: 'Serif',
                              color: _isDarkMode ? Colors.grey[300] : Colors.black87,
      ),
      ),
      ),
      );
                  },
                ),
              ),
              // Pagination controls
              Container(
                padding: const EdgeInsets.all(16),
                color: _isDarkMode ? Colors.black : Colors.grey[100],
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      "${_currentPage + 1} / ${_pages.length}",
                      style: TextStyle(color: _isDarkMode ? Colors.white : Colors.black),
                    ),
                    const Text("Protected Mode", style: TextStyle(color: Colors.red, fontSize: 10, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ],
          ),

          // Watermark Overlay (PointerEvents locked to allow scroll through)
          IgnorePointer(
            child: Container(
              width: double.infinity,
              height: double.infinity,
              color: Colors.transparent,
              child: GridView.count(
                crossAxisCount: 2,
                children: List.generate(
                  6,
                  (index) => Center(
                    child: Transform.rotate(
                      angle: -0.5,
                      child: Opacity(
                        opacity: 0.05,
                        child: Text(
                          "USER ID: 12345", // Mock User ID
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: _isDarkMode ? Colors.white : Colors.black,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
