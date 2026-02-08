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
  final bool isPremium;
  final int balance;
  final bool trialUsed;
  final String? premiumExpiry; // Added string for simplicity
  final String? customBadge;
  final String? staffRole; // New field for Tutor/Staff roles

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
    this.staffRole,
  });

  factory Student.fromJson(Map<String, dynamic> json) {
    // Helper to get nested name safely
    String? getName(String key) {
      if (json[key] is Map) {
        return json[key]['name']?.toString();
      }
      return null;
    }

    // Helper to capitalize first letter
    String sentenceCase(String text) {
      if (text.isEmpty) return "";
      return text[0].toUpperCase() + text.substring(1).toLowerCase();
    }
    
    String fullName = "";
    String? jsonFullName = json['full_name'] ?? json['name'];
    String? firstName = json['first_name'] ?? json['short_name'] ?? json['firstname'];
    String? lastName = json['last_name'] ?? json['lastname'];
    String? patronymic = json['father_name'] ?? json['fathername'] ?? json['patronymic'];

    if (lastName != null && firstName != null) {
      if (patronymic != null) {
        fullName = "${sentenceCase(firstName)} ${sentenceCase(lastName)} ${sentenceCase(patronymic)}";
      } else {
        fullName = "${sentenceCase(firstName)} ${sentenceCase(lastName)}";
      }
    } else if (jsonFullName != null && jsonFullName.toString().trim().isNotEmpty && jsonFullName != "Talaba") {
      var parts = jsonFullName.toString().trim().split(' ');
      if (parts.length >= 2) {
        // Swap Last Name and First Name from the "Last First [Patronymic]" string
        String f = sentenceCase(parts[1]);
        String l = sentenceCase(parts[0]);
        String rest = parts.length > 2 ? " ${parts.sublist(2).map((p) => sentenceCase(p)).join(' ')}" : "";
        fullName = "$f $l$rest";
      } else {
        fullName = sentenceCase(jsonFullName.toString().trim());
      }
    } else if (firstName != null && firstName.toString().trim().isNotEmpty) {
      fullName = sentenceCase(firstName.toString().trim());
    } else {
      fullName = "Talaba";
    }
    
    if (fullName.trim().isEmpty || fullName == "Talaba") {
      if (json['short_name'] != null && json['short_name'].toString().length > 3) {
         fullName = json['short_name'].toString();
      } else {
         fullName = "Talaba";
      }
    }

    String? getPrettyName(String key) {
       String? val = getName(key);
       if (val != null) return sentenceCase(val);
       var direct = json["${key}_name"] ?? json[key];
       if (direct != null) return sentenceCase(direct.toString());
       return null;
    }

    return Student(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      fullName: fullName.trim(),
      hemisLogin: json['login'] ?? json['hemis_login'] ?? '',
      groupNumber: (getName('group') != null) ? getName('group')! : json['group_number']?.toString(),
      specialtyName: getPrettyName('specialty'),
      facultyName: getPrettyName('faculty'),
      semesterName: getPrettyName('semester'),
      universityName: json['university_name'] ?? getPrettyName('university') ?? "O‘zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti",
      imageUrl: json['image'] ?? json['image_url'],
      username: json['username'], 
      missedHours: json['missed_hours'] ?? 0,
      role: json['role_code'] ?? json['role'] ?? json['user_role'],
      isPremium: json['is_premium'] ?? false,
      balance: json['balance'] ?? 0,
      trialUsed: json['trial_used'] ?? false,
      premiumExpiry: json['premium_expiry']?.toString(),
      customBadge: json['custom_badge'],
      staffRole: json['staff_role'] ?? json['role_code'] ?? json['role'], // Map generic role to staffRole if needed, or specific field
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
      'staff_role': staffRole,
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
    String? staffRole,
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
      staffRole: staffRole ?? this.staffRole,
    );
  }
}
