class Reservation {
  final String id;
  final String bookId;
  final String bookTitle;
  final String author;
  final String coverUrl;
  final String status; // 'reserved', 'queue', 'borrowed', 'overdue', 'returned', 'reading', 'completed', 'cancelled'
  final int? queuePosition;
  final DateTime? reserveDate;
  final DateTime? pickupDeadline;
  final DateTime? returnDeadLine;
  
  // Reading specific fields
  final double? progress;
  final int? totalPageCount;
  final int? readPageCount;
  final DateTime? lastReadDate;

  Reservation({
    required this.id,
    required this.bookId,
    required this.bookTitle,
    required this.author,
    required this.coverUrl,
    required this.status,
    this.queuePosition,
    this.reserveDate,
    this.pickupDeadline,
    this.returnDeadLine,
    this.progress,
    this.totalPageCount,
    this.readPageCount,
    this.lastReadDate,
  });

  factory Reservation.fromJson(Map<String, dynamic> json) {
    return Reservation(
      id: json['id'],
      bookId: json['book_id'],
      bookTitle: json['book_title'],
      author: json['author'] ?? "Noma'lum",
      coverUrl: json['cover_url'],
      status: json['status'],
      queuePosition: json['queue_position'],
      reserveDate: json['reserve_date'] != null ? DateTime.parse(json['reserve_date']) : null,
      pickupDeadline: json['pickup_deadline'] != null ? DateTime.parse(json['pickup_deadline']) : null,
      returnDeadLine: json['return_deadline'] != null ? DateTime.parse(json['return_deadline']) : null,
      progress: json['progress']?.toDouble(),
      totalPageCount: json['total_page_count'],
      readPageCount: json['read_page_count'],
      lastReadDate: json['last_read_date'] != null ? DateTime.parse(json['last_read_date']) : null,
    );
  }
}
