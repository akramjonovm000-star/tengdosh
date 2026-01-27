class SubscriptionPlan {
  final String id;
  final String name;
  final int durationDays;
  final int priceUzs;
  final bool isActive;

  SubscriptionPlan({
    required this.id,
    required this.name,
    required this.durationDays,
    required this.priceUzs,
    required this.isActive,
  });

  factory SubscriptionPlan.fromJson(Map<String, dynamic> json) {
    return SubscriptionPlan(
      id: json['id'].toString(),
      name: json['name'],
      durationDays: json['duration_days'],
      priceUzs: json['price_uzs'],
      isActive: json['is_active'] ?? true,
    );
  }
}
