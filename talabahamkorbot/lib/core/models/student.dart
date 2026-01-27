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
  final String? username; // New Field 
  final int missedHours;

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
    // Helper to capitalize first letter (Sentence case)
    String sentenceCase(String text) {
      if (text.isEmpty) return "";
      return text[0].toUpperCase() + text.substring(1).toLowerCase();
    }

    String fullName = "";
    if (json['lastname'] != null && json['firstname'] != null) {
      fullName = "${sentenceCase(json['lastname'].toString())} ${sentenceCase(json['firstname'].toString())}";
    } else {
      String raw = json['full_name'] ?? "Talaba";
      var parts = raw.split(' ');
      if (parts.length >= 2) {
        fullName = "${sentenceCase(parts[0])} ${sentenceCase(parts[1])}";
      } else {
        fullName = sentenceCase(raw);
      }
    }

    // Helper to extract and prettify
    String? getPrettyName(String key) {
      String? val = getName(key); // getName extracts from map
      if (val != null) return sentenceCase(val);
      // Try direct key fallback
      var direct = json["${key}_name"] ?? json[key];
      if (direct != null) return sentenceCase(direct.toString());
      return null;
    }

    return Student(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      fullName: fullName.trim(),
      hemisLogin: json['login'] ?? json['hemis_login'] ?? '',
      groupNumber: (getName('group') != null) 
          ? getName('group')! 
          : json['group_number']?.toString(),
      specialtyName: getPrettyName('specialty'),
      facultyName: getPrettyName('faculty'),
      semesterName: getPrettyName('semester'),
      universityName: json['university_name'] ?? getPrettyName('university') ?? "Jizzax davlat pedagogika universiteti",
      imageUrl: json['image'] ?? json['image_url'],
      username: json['username'],
      missedHours: json['missed_hours'] ?? 0,
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
    };
  }
}
