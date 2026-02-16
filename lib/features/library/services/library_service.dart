import 'package:flutter/foundation.dart';
import '../models/book_model.dart';
import '../models/reservation_model.dart';

class LibraryService {
  // Mock Data
  static final List<Book> _mockBooks = [
    Book(
      id: "1",
      title: "O'tkan kunlar",
      author: "Abdulla Qodiriy",
      genre: "Badiiy",
      description: "O'zbek adabiyotining klassik asari. Sevgi, sadoqat va tarixiy voqealarni o'z ichiga oladi.",
      coverUrl: "https://assets.asaxiy.uz/product/items/desktop/5e15bc9d9k.jpg",
      rating: 4.9,
      totalCopies: 5,
      availableCopies: 2,
      isEbookAvailable: true,
      ebookUrl: "https://example.com/ebook/otkan_kunlar.pdf",
      publishedDate: DateTime(1926, 1, 1),
    ),
    Book(
      id: "2",
      title: "Clean Code",
      author: "Robert C. Martin",
      genre: "Dasturlash",
      description: "Dasturchilar uchir muhim kitob. Kodni toza va tushunarli yozish qoidalari.",
      coverUrl: "https://m.media-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg",
      rating: 4.8,
      totalCopies: 3,
      availableCopies: 0,
      isEbookAvailable: false,
      publishedDate: DateTime(2008, 8, 1),
    ),
    Book(
      id: "3",
      title: "Sapiens: A Brief History of Humankind",
      author: "Yuval Noah Harari",
      genre: "Tarix",
      description: "Insoniyat tarixiga yangicha nazar.",
      coverUrl: "https://images-na.ssl-images-amazon.com/images/I/713jIoMO3UL.jpg",
      rating: 4.7,
      totalCopies: 10,
      availableCopies: 8,
      isEbookAvailable: true,
      ebookUrl: "https://example.com/ebook/sapiens.pdf",
      publishedDate: DateTime(2011, 1, 1),
    ),
    Book(
      id: "4",
      title: "Algorithm Design Manual",
      author: "Steven Skiena",
      genre: "Dasturlash",
      description: "Algoritmlarni o'rganish uchun ajoyib qo'llanma.",
      coverUrl: "https://m.media-amazon.com/images/I/51T5+i9yR5L.jpg",
      rating: 4.6,
      totalCopies: 2,
      availableCopies: 1,
      isEbookAvailable: true,
      ebookUrl: "https://example.com/ebook/algorithms.pdf",
      publishedDate: DateTime(2008, 1, 1),
    ),
    Book(
      id: "5",
      title: "Harry Potter and the Sorcerer's Stone",
      author: "J.K. Rowling",
      genre: "Badiiy",
      description: "Sehrgarlar olamiga sayohat.",
      coverUrl: "https://images-na.ssl-images-amazon.com/images/I/81iqZ2HHD-L.jpg",
      rating: 4.9,
      totalCopies: 7,
      availableCopies: 3,
      isEbookAvailable: true,
      ebookUrl: "https://example.com/ebook/harry_potter_1.pdf",
      publishedDate: DateTime(1997, 6, 26),
    ),
  ];

  Future<List<Book>> getBooks({
    String? query,
    String? category, // Genre
    bool? availableOnly,
    bool? ebookOnly,
    String? sortBy, // popular, new, alpha
  }) async {
    // Simulate API delay
    await Future.delayed(const Duration(milliseconds: 500));

    List<Book> results = List.from(_mockBooks);

    // Filter by Query (Title or Author)
    if (query != null && query.isNotEmpty) {
      final q = query.toLowerCase();
      results = results.where((book) {
        return book.title.toLowerCase().contains(q) ||
               book.author.toLowerCase().contains(q);
      }).toList();
    }

    // Filter by Genre
    if (category != null && category != "Barchasi") {
      results = results.where((book) => book.genre == category).toList();
    }

    // Filter by Availability
    if (availableOnly == true) {
      results = results.where((book) => book.availableCopies > 0).toList();
    }

    // Filter by E-book
    if (ebookOnly == true) {
      results = results.where((book) => book.isEbookAvailable).toList();
    }

    // Sort
    if (sortBy != null) {
      switch (sortBy) {
        case 'popular':
          results.sort((a, b) => b.rating.compareTo(a.rating));
          break;
        case 'new':
          results.sort((a, b) => b.publishedDate.compareTo(a.publishedDate));
          break;
        case 'alpha':
          results.sort((a, b) => a.title.compareTo(b.title));
          break;
      }
    }

    return results;
  }

  Future<Book?> getBookDetails(String id) async {
    await Future.delayed(const Duration(milliseconds: 300));
    try {
      return _mockBooks.firstWhere((b) => b.id == id);
    } catch (e) {
      return null;
    }
  }

  Future<List<String>> getCategories() async {
    // Unique Genres
    final genres = _mockBooks.map((b) => b.genre).toSet().toList();
    genres.sort();
    return ["Barchasi", ...genres];
  }

  // --- Reservation System ---

  // Mock Reservations
  static final List<Reservation> _mockReservations = [
    // Example: Reserved Book
    Reservation(
      id: "res_101",
      bookId: "1",
      bookTitle: "O'tkan kunlar",
      author: "Abdulla Qodiriy",
      coverUrl: "https://assets.asaxiy.uz/product/items/desktop/5e15bc9d9k.jpg",
      status: "reserved",
      reserveDate: DateTime.now().subtract(const Duration(hours: 4)),
      pickupDeadline: DateTime.now().add(const Duration(days: 3)),
    ),
    // Example: In Queue
    Reservation(
      id: "res_102",
      bookId: "2",
      bookTitle: "Clean Code",
      author: "Robert C. Martin",
      coverUrl: "https://m.media-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg",
      status: "queue",
      queuePosition: 2,
    ),
  ];

  static final List<Reservation> _mockBorrowings = [
    Reservation(
      id: "borrow_201",
      bookId: "3",
      bookTitle: "Sapiens: A Brief History of Humankind",
      author: "Yuval Noah Harari",
      coverUrl: "https://images-na.ssl-images-amazon.com/images/I/713jIoMO3UL.jpg",
      status: "borrowed",
      pickupDeadline: DateTime.now().subtract(const Duration(days: 5)),
      returnDeadLine: DateTime.now().add(const Duration(days: 5)), // 5 days left
    ),
    Reservation(
      id: "borrow_202",
      bookId: "4",
      bookTitle: "Algorithm Design Manual",
      author: "Steven Skiena",
      coverUrl: "https://m.media-amazon.com/images/I/51T5+i9yR5L.jpg",
      status: "overdue",
      pickupDeadline: DateTime.now().subtract(const Duration(days: 15)),
      returnDeadLine: DateTime.now().subtract(const Duration(days: 1)), // Overdue by 1 day
    ),
  ];

  static final List<Reservation> _mockReadingList = [
    Reservation(
      id: "read_301",
      bookId: "5",
      bookTitle: "Harry Potter and the Sorcerer's Stone",
      author: "J.K. Rowling",
      coverUrl: "https://images-na.ssl-images-amazon.com/images/I/81iqZ2HHD-L.jpg",
      status: "reading",
      progress: 0.75, // 75%
      totalPageCount: 320,
      readPageCount: 240,
      lastReadDate: DateTime.now().subtract(const Duration(hours: 2)),
    ),
    Reservation(
      id: "read_302",
      bookId: "1",
      bookTitle: "O'tkan kunlar",
      author: "Abdulla Qodiriy",
      coverUrl: "https://assets.asaxiy.uz/product/items/desktop/5e15bc9d9k.jpg",
      status: "completed",
      progress: 1.0,
      totalPageCount: 280,
      readPageCount: 280,
      lastReadDate: DateTime.now().subtract(const Duration(days: 10)),
    ),
  ];

  Future<List<Reservation>> getReservations() async {
    await Future.delayed(const Duration(milliseconds: 600));
    return _mockReservations;
  }

  Future<List<Reservation>> getBorrowedBooks() async {
    await Future.delayed(const Duration(milliseconds: 600));
    return _mockBorrowings;
  }

  Future<List<Reservation>> getReadingList() async {
    await Future.delayed(const Duration(milliseconds: 600));
    return _mockReadingList;
  }

  Future<List<Reservation>> getHistory() async {
    await Future.delayed(const Duration(milliseconds: 800));
    // Combine all and some mocked past history
    final all = [
      ..._mockReservations,
      ..._mockBorrowings,
      ..._mockReadingList,
      Reservation(
        id: "hist_401",
        bookId: "2",
        bookTitle: "Clean Code",
        author: "Robert C. Martin",
        coverUrl: "https://m.media-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg",
        status: "returned",
        returnDeadLine: DateTime.now().subtract(const Duration(days: 30)),
      ),
       Reservation(
        id: "hist_402",
        bookId: "3",
        bookTitle: "Sapiens",
        author: "Yuval Noah Harari",
        coverUrl: "https://images-na.ssl-images-amazon.com/images/I/713jIoMO3UL.jpg",
        status: "cancelled",
        reserveDate: DateTime.now().subtract(const Duration(days: 40)),
      ),
    ];
    return all;
  }

  Future<Reservation> reserveBook(String bookId) async {
    // Simulate check
    await Future.delayed(const Duration(seconds: 1));
    
    // In real backend, this would check stock atomically
    final book = _mockBooks.firstWhere((b) => b.id == bookId);
    
    if (book.availableCopies <= 0) {
      throw Exception("Kitob mavjud emas");
    }

    final newRes = Reservation(
      id: "res_${DateTime.now().millisecondsSinceEpoch}",
      bookId: book.id,
      bookTitle: book.title,
      author: book.author,
      coverUrl: book.coverUrl,
      status: "reserved",
      reserveDate: DateTime.now(),
      pickupDeadline: DateTime.now().add(const Duration(days: 3)),
    );
    
    // Add to mock local list for session
    _mockReservations.insert(0, newRes);
    return newRes;
  }

  Future<Reservation> addToQueue(String bookId) async {
    await Future.delayed(const Duration(seconds: 1));
    final book = _mockBooks.firstWhere((b) => b.id == bookId);

    final newRes = Reservation(
      id: "q_${DateTime.now().millisecondsSinceEpoch}",
      bookId: book.id,
      bookTitle: book.title,
      author: book.author,
      coverUrl: book.coverUrl,
      status: "queue",
      queuePosition: 5, // Mock position
    );

    _mockReservations.insert(0, newRes);
    return newRes;
  }
}
