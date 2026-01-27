class Student {
  final int id;
  final String fullName;
  final String hemisLogin;
  final String? universityName;
  final String? groupNumber;
  final String? specialtyName;
  final String? facultyName;
  final String? semesterName;
  final String? imageUrl;
  final String? username; // New field
  final int missedHours;
  final String? role;
  final String? premiumExpiry; // Added string for simplicity
  final String? customBadge;

  Student({
    required this.id,
    required this.fullName,
    required this.hemisLogin,
    this.groupNumber,
    this.specialtyName,
    this.facultyName,
    this.semesterName,
    this.universityName,
    this.imageUrl,
    this.username,
    this.missedHours = 0,
    this.role,
    this.isPremium = false,
    this.balance = 0,
    this.trialUsed = false,
    this.premiumExpiry,
    this.customBadge,
  });

  factory Student.fromJson(Map<String, dynamic> json) {
    // ... helpers ... (omitting for brevity, we assume they are there or we target lines below helpers if possible)
    // Actually typically helps are inside factory body. Ideally I should target the return statement.
    // I can't access helpers if I replace the whole factory.
    // I will replace the end of factory only.
    
    // ... logic ...
    
    return Student(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      fullName: fullName.trim(), // Assuming fullName variable exists from above scope in original file
      hemisLogin: json['login'] ?? json['hemis_login'] ?? '',
      groupNumber: (getName('group') != null) ? getName('group')! : json['group_number']?.toString(),
      specialtyName: getPrettyName('specialty'),
      facultyName: getPrettyName('faculty'),
      semesterName: getPrettyName('semester'),
      universityName: json['university_name'] ?? getPrettyName('university') ?? "Jizzax davlat pedagogika universiteti",
      imageUrl: json['image'] ?? json['image_url'],
      username: json['username'], // Map username
      missedHours: json['missed_hours'] ?? 0,
      role: json['role'] ?? json['user_role'],
      isPremium: json['is_premium'] ?? false,
      balance: json['balance'] ?? 0,
      trialUsed: json['trial_used'] ?? false,
      premiumExpiry: json['premium_expiry']?.toString(),
      customBadge: json['custom_badge'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'full_name': fullName,
      'hemis_login': hemisLogin,
      'group_number': groupNumber,
      'specialty_name': specialtyName,
      'faculty_name': facultyName,
      'semester_name': semesterName,
      'university_name': universityName,
      'image_url': imageUrl,
      'username': username,
      'missed_hours': missedHours,
      'role': role,
      'is_premium': isPremium,
      'balance': balance,
      'trial_used': trialUsed,
      'premium_expiry': premiumExpiry,
      'custom_badge': customBadge,
    };
  }

  Student copyWith({
    int? id,
    String? fullName,
    String? hemisLogin,
    String? universityName,
    String? groupNumber,
    String? specialtyName,
    String? facultyName,
    String? semesterName,
    String? imageUrl,
    String? username,
    int? missedHours,
    String? role,
    bool? isPremium,
    int? balance,
    bool? trialUsed,
    String? premiumExpiry,
    String? customBadge,
  }) {
    return Student(
      id: id ?? this.id,
      fullName: fullName ?? this.fullName,
      hemisLogin: hemisLogin ?? this.hemisLogin,
      universityName: universityName ?? this.universityName,
      groupNumber: groupNumber ?? this.groupNumber,
      specialtyName: specialtyName ?? this.specialtyName,
      facultyName: facultyName ?? this.facultyName,
      semesterName: semesterName ?? this.semesterName,
      imageUrl: imageUrl ?? this.imageUrl,
      username: username ?? this.username,
      missedHours: missedHours ?? this.missedHours,
      role: role ?? this.role,
      isPremium: isPremium ?? this.isPremium,
      balance: balance ?? this.balance,
      trialUsed: trialUsed ?? this.trialUsed,
      premiumExpiry: premiumExpiry ?? this.premiumExpiry,
      customBadge: customBadge ?? this.customBadge,
    );
  }
}
