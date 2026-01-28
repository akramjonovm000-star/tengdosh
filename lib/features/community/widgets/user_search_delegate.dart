import 'package:flutter/material.dart';
import '../services/community_service.dart';
import '../../../../core/models/student.dart';
import '../../../../core/theme/app_theme.dart';
import '../screens/user_profile_screen.dart';

class UserSearchDelegate extends SearchDelegate {
  final CommunityService _service = CommunityService();
  final Function(Student)? onUserSelected; 
  final String historyKey; // NEW

  UserSearchDelegate({this.onUserSelected, this.historyKey = 'recent_users'}); // NEW

  @override
  String get searchFieldLabel => "Talabalarni qidirish...";

  @override
  List<Widget>? buildActions(BuildContext context) {
    return [
      if (query.isNotEmpty)
        IconButton(
          icon: const Icon(Icons.clear),
          onPressed: () {
            query = '';
            showSuggestions(context);
          },
        ),
    ];
  }

  @override
  Widget? buildLeading(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.arrow_back),
      onPressed: () => close(context, null),
    );
  }

  @override
  Widget buildResults(BuildContext context) {
    return _buildSearchList();
  }

  @override
  Widget buildSuggestions(BuildContext context) {
    if (query.length < 2) {
       return FutureBuilder<List<Student>>(
         future: _service.getRecentUsers(key: historyKey), // Use key
         builder: (context, snapshot) {
           final history = snapshot.data ?? [];
           
           if (history.isEmpty) {
             return Container(
               color: Colors.white,
               child: const Center(
                 child: Column(
                   mainAxisAlignment: MainAxisAlignment.center,
                   children: [
                     Icon(Icons.search, size: 64, color: Colors.grey),
                     SizedBox(height: 16),
                     Text("Username yoki ism kiriting\n(kamida 2 ta harf)", textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
                   ],
                 ),
               ),
             );
           }
           
           return Column(
             crossAxisAlignment: CrossAxisAlignment.start,
             children: [
               Padding(
                 padding: const EdgeInsets.all(16),
                 child: Row(
                   mainAxisAlignment: MainAxisAlignment.spaceBetween,
                   children: [
                     const Text("So'nggi qidiruvlar", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                     TextButton(
                       onPressed: () async {
                         await _service.clearSearchHistory(key: historyKey); // Use key
                         showSuggestions(context); 
                       }, 
                       child: const Text("Tozalash", style: TextStyle(color: Colors.red))
                     )
                   ],
                 ),
               ),
               Expanded(
                 child: ListView.separated(
                   itemCount: history.length,
                   separatorBuilder: (ctx, i) => const Divider(height: 1, indent: 72),
                   itemBuilder: (context, index) {
                     return _buildUserTile(context, history[index], isHistory: true);
                   },
                 ),
               ),
             ],
           );
         }
       );
    }
    return _buildSearchList();
  }

  Widget _buildSearchList() {
    return FutureBuilder<List<Student>>(
      future: _service.searchStudents(query),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
           return const Center(child: Text("Xatolik yuz berdi"));
        }
        
        final students = snapshot.data ?? [];
        
        if (students.isEmpty) {
           return const Center(child: Text("Hech kim topilmadi"));
        }

        return ListView.separated(
          itemCount: students.length,
          separatorBuilder: (ctx, i) => const Divider(height: 1, indent: 72),
          itemBuilder: (context, index) {
            return _buildUserTile(context, students[index]);
          },
        );
      },
    );
  }

  Widget _buildUserTile(BuildContext context, Student student, {bool isHistory = false}) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: CircleAvatar(
        radius: 24,
        backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
        backgroundImage: student.imageUrl != null && student.imageUrl!.isNotEmpty
            ? NetworkImage(student.imageUrl!)
            : null,
        child: (student.imageUrl == null || student.imageUrl!.isEmpty)
            ? Text(student.fullName.isNotEmpty ? student.fullName[0] : "?", style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold, fontSize: 18))
            : null,
      ),
      title: Row(
       children: [
         Text(student.fullName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
         if (student.isPremium) ...[
           const SizedBox(width: 4),
           student.customBadge != null 
               ? Text(student.customBadge!, style: const TextStyle(fontSize: 16))
               : const Icon(Icons.verified, color: Colors.blue, size: 16),
         ]
       ],
      ),
      subtitle: Text("@${student.username ?? 'usernamesiz'}", style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.w500)),
      trailing: isHistory ? const Icon(Icons.history, color: Colors.grey, size: 20) : null,
      onTap: () {
         // Save to history (Move to top)
         _service.saveRecentUser(student, key: historyKey);
         
         if (onUserSelected != null) {
           onUserSelected!(student);
           close(context, null); // Close immediately so ListScreen can push
           return; 
         }

        // Navigate to Profile
        Navigator.push(context, MaterialPageRoute(builder: (_) => UserProfileScreen(
          authorName: student.fullName,
          authorId: student.id.toString(),
          authorUsername: student.username ?? "",
          authorAvatar: student.imageUrl ?? "",
          authorRole: student.role ?? "student", 
          authorIsPremium: student.isPremium,
        )));
      },
    );
  }
}
