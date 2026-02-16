class Book {
  final String id;
  final String title;
  final String author;
  final String genre;
  final String description;
  final String coverUrl;
  final double rating;
  final int totalCopies;
  final int availableCopies;
  final bool isEbookAvailable;
  final String? ebookUrl; // Should be secure link or tokenized
  final DateTime publishedDate;

  Book({
    required this.id,
    required this.title,
    required this.author,
    required this.genre,
    required this.description,
    required this.coverUrl,
    required this.rating,
    required this.totalCopies,
    required this.availableCopies,
    required this.isEbookAvailable,
    this.ebookUrl,
    required this.publishedDate,
  });

  // Mock factory or fromJson
  factory Book.fromJson(Map<String, dynamic> json) {
    return Book(
      id: json['id'],
      title: json['title'],
      author: json['author'],
      genre: json['genre'],
      description: json['description'] ?? '',
      coverUrl: json['cover_url'],
      rating: (json['rating'] as num).toDouble(),
      totalCopies: json['total_copies'] ?? 0,
      availableCopies: json['available_copies'] ?? 0,
      isEbookAvailable: json['is_ebook_available'] ?? false,
      ebookUrl: json['ebook_url'],
      publishedDate: DateTime.parse(json['published_date']),
    );
  }
}
