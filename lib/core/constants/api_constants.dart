class ApiConstants {
  // JMCU API (Japan Digital University / JMCU)
  static const String baseUrl = 'https://student.jmcu.uz/rest/v1'; 
  
  // Saved Admin/Client Token (Requested by User)
  static const String apiToken = 'LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW';

  // Backend API (Talaba Hamkor)
  static const String backendUrl = 'https://tengdosh.uzjoku.uz/api/v1';
  
  // Auth (Back to Backend Proxy)
  static const String authLogin = '$backendUrl/auth/hemis';
  
  // Account
  // Account
  // FIXED: Point back to Backend Proxy to sync DB
  static const String profile = '$backendUrl/student/me/';
  
  // Dashboard
  static const String dashboard = '$backendUrl/student/dashboard/';
  
  // Data
  static const String gpaList = '$baseUrl/data/student-gpa-list';
  static const String taskList = '$baseUrl/data/subject-task-student-list';
  static const String documentList = '$baseUrl/data/student-certificate-list';
  static const String attendanceList = '$academic/attendance'; // FIXED: No trailing slash
  static const String scheduleList = '$academic/schedule'; // FIXED: No trailing slash
 
  // Extended Features (Backend)
  static const String activities = '$backendUrl/student/activities/'; 
  static const String clubsMy = '$backendUrl/student/clubs/my/';
  static const String feedback = '$backendUrl/student/feedback/';
  static const String documents = '$backendUrl/student/documents/';
  static const String academic = '$backendUrl/education';
  static const String grades = '$academic/grades'; // FIXED: No trailing slash
  static const String subjects = '$academic/subjects'; // FIXED: No trailing slash
  static const String resources = '$academic/resources'; // FIXED: No trailing slash
  static const String aiChat = '$backendUrl/ai/chat/';
  static const String documentsSend = '$backendUrl/documents/send/';
  
  // Community
  static const String communityPosts = '$backendUrl/community/posts/'; // Caution: Query params might maintain slash? Usually /posts/?foo=bar is fine.

  // Subscription
  static const String subscription = '$backendUrl/subscription/';
}
