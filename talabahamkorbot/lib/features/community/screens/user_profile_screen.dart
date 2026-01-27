import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';
import '../widgets/post_card.dart';

class UserProfileScreen extends StatefulWidget {
  final String authorName;
  final String authorUsername;
  final String authorAvatar;
  final String authorRole;

  const UserProfileScreen({
    super.key,
    required this.authorName,
    required this.authorUsername,
    required this.authorAvatar,
    required this.authorRole,
  });

  @override
  State<UserProfileScreen> createState() => _UserProfileScreenState();
}

class _UserProfileScreenState extends State<UserProfileScreen> {
  final CommunityService _service = CommunityService();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text(widget.authorUsername, style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 20),
            // Avatar
            CircleAvatar(
              radius: 40,
              backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
              backgroundImage: widget.authorAvatar.isNotEmpty ? NetworkImage(widget.authorAvatar) : null,
              child: widget.authorAvatar.isEmpty 
                 ? Text(widget.authorName[0], style: const TextStyle(fontSize: 32, color: AppTheme.primaryBlue, fontWeight: FontWeight.bold))
                 : null,
            ),
            const SizedBox(height: 12),
            // Names
            Text(widget.authorName, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            Text(widget.authorRole, style: TextStyle(fontSize: 14, color: Colors.grey[600])),
            
            const SizedBox(height: 20),
            
            // Stats (Mock)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildStat("Postlar", "12"),
                _buildStat("Kuzatuvchilar", "345"),
                _buildStat("Obuna", "120"),
              ],
            ),
            
            const SizedBox(height: 20),
            
            // Actions
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton(
                  onPressed: () {},
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlue,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                    padding: const EdgeInsets.symmetric(horizontal: 32)
                  ),
                  child: const Text("Kuzatish", style: TextStyle(color: Colors.white)),
                ),
                const SizedBox(width: 12),
                OutlinedButton(
                  onPressed: () {},
                  style: OutlinedButton.styleFrom(
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  ),
                  child: const Text("Xabar yozish"),
                )
              ],
            ),
            
            const SizedBox(height: 20),
            const Divider(thickness: 1),
            
            // Posts Grid (Mock: Reusing PostCard list)
            FutureBuilder<List<Post>>(
              future: _service.getPosts(scope: "university"),
              builder: (context, snapshot) {
                if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
                return ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: snapshot.data!.length,
                  itemBuilder: (ctx, i) => PostCard(post: snapshot.data![i]),
                );
              },
            )
          ],
        ),
      ),
    );
  }

  Widget _buildStat(String label, String value) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        Text(label, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
      ],
    );
  }
}
