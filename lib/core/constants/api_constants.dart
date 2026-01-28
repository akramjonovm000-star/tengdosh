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
  // FIXED: Point back to Backend Proxy to sync DB
  static const String profile = '$backendUrl/student/me';
  
  // Dashboard
  static const String dashboard = '$backendUrl/student/dashboard';
  
  // Data
  static const String gpaList = '$baseUrl/data/student-gpa-list';
  static const String taskList = '$baseUrl/data/subject-task-student-list';
  static const String documentList = '$baseUrl/data/student-certificate-list';
  static const String attendanceList = '$academic/attendance'; 
  static const String scheduleList = '$academic/schedule'; 
 
  // Extended Features (Backend)
  static const String activities = '$backendUrl/student/activities'; 
  static const String clubsMy = '$backendUrl/student/clubs/my';
  static const String feedback = '$backendUrl/student/feedback';
  static const String documents = '$backendUrl/student/documents';
  static const String academic = '$backendUrl/education';
  static const String grades = '$academic/grades'; 
  static const String subjects = '$academic/subjects'; 
  static const String resources = '$academic/resources'; 
  static const String aiChat = '$backendUrl/ai/chat';
  static const String documentsSend = '$backendUrl/documents/send';
  
  // Community
  static const String communityPosts = '$backendUrl/community/posts'; 

  // Subscription
  static const String subscription = '$backendUrl/subscription';
}
