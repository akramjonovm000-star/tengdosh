class ApiConstants {
  // JMCU API (Japan Digital University / JMCU)
  static const String baseUrl = 'https://student.jmcu.uz/rest/v1'; 
  
  // Saved Admin/Client Token (Requested by User)
  static const String apiToken = 'LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW';

  // Backend API (Talaba Hamkor)
  static const String backendUrl = 'https://tengdosh.uzjoku.uz/api/v1';
  
  // Auth (Proxy via our Bot Backend)
  static const String authLogin = '$backendUrl/auth/hemis';
  // HEMIS OAuth Redirect (Opens browser)
  static const String hemisOAuth = '$backendUrl/auth/hemis/oauth/redirect?source=app';
  
  // Account
  // Account
  // FIXED: Point to our backend to get the enriched profile (with mapped Uni name & First Name)
  static const String profile = '$backendUrl/student/me';
  
  // Dashboard
  static const String dashboard = '$backendUrl/student/dashboard';
  
  // Data
  static const String gpaList = '$baseUrl/data/student-gpa-list';
  static const String taskList = '$baseUrl/data/subject-task-student-list';
  static const String documentList = '$baseUrl/data/student-certificate-list';
  // Extended Features (Backend)
  static const String academic = '$backendUrl/education';
  static const String activities = '$backendUrl/student/activities'; 
  static const String grades = '$academic/grades';
  static const String subjects = '$academic/subjects';
  static const String resources = '$academic/resources';
  static const String aiChat = '$backendUrl/ai/chat';
  static const String documentsSend = '$backendUrl/documents/send';
}
