import 'package:flutter/material.dart';
import '../../../../core/models/student.dart';
import '../../../../core/theme/app_theme.dart';
import '../services/community_service.dart';
import 'user_profile_screen.dart';

enum UserListType { followers, following }

class UserListScreen extends StatefulWidget {
  final String userId;
  final UserListType type;

  const UserListScreen({
    super.key,
    required this.userId,
    required this.type,
  });

  @override
  State<UserListScreen> createState() => _UserListScreenState();
}

class _UserListScreenState extends State<UserListScreen> {
  final CommunityService _service = CommunityService();
  bool _isLoading = true;
  List<Student> _users = [];

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  Future<void> _loadUsers() async {
    setState(() => _isLoading = true);
    try {
      List<Student> users = [];
      if (widget.type == UserListType.followers) {
        users = await _service.getFollowers(widget.userId);
      } else {
        users = await _service.getFollowing(widget.userId);
      }
      
      if (mounted) {
        setState(() {
          _users = users;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.type == UserListType.followers ? "Kuzatuvchilar" : "Obunalar";
    
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text(title, style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _users.isEmpty
              ? Center(child: Text("$title yo'q", style: const TextStyle(color: Colors.grey)))
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: _users.length,
                  separatorBuilder: (ctx, i) => const Divider(height: 1, indent: 72),
                  itemBuilder: (context, index) {
                    final student = _users[index];
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
                            const Icon(Icons.verified, color: Colors.blue, size: 16),
                          ]
                        ],
                      ),
                      subtitle: Text("@${student.username ?? 'usernamesiz'}", style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.w500)),
                      onTap: () {
                        // Navigate to their profile
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
                  },
                ),
    );
  }
}
