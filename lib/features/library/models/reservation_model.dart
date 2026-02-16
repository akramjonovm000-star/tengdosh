class Reservation {
  final String id;
  final String bookId;
  final String bookTitle;
  final String coverUrl;
  final String status; // 'reserved', 'queue', 'borrowed', 'overdue', 'returned'
  final int? queuePosition;
  final DateTime? reserveDate;
  final DateTime? pickupDeadline;
  final DateTime? returnDeadLine;

  Reservation({
    required this.id,
    required this.bookId,
    required this.bookTitle,
    required this.coverUrl,
    required this.status,
    this.queuePosition,
    this.reserveDate,
    this.pickupDeadline,
    this.returnDeadLine,
  });

  factory Reservation.fromJson(Map<String, dynamic> json) {
    return Reservation(
      id: json['id'],
      bookId: json['book_id'],
      bookTitle: json['book_title'],
      coverUrl: json['cover_url'],
      status: json['status'],
      queuePosition: json['queue_position'],
      reserveDate: json['reserve_date'] != null ? DateTime.parse(json['reserve_date']) : null,
      pickupDeadline: json['pickup_deadline'] != null ? DateTime.parse(json['pickup_deadline']) : null,
      returnDeadLine: json['return_deadline'] != null ? DateTime.parse(json['return_deadline']) : null,
    );
  }
}
