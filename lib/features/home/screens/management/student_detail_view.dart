import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'student_items_list_screen.dart';

class StudentDetailView extends StatefulWidget {
  final int studentId;

  const StudentDetailView({super.key, required this.studentId});

  @override
  State<StudentDetailView> createState() => _StudentDetailViewState();
}

class _StudentDetailViewState extends State<StudentDetailView> {
  final DataService _dataService = DataService();
  Map<String, dynamic>? _data;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    final data = await _dataService.getStudentFullDetails(widget.studentId);
    setState(() {
      _data = data;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text("Talaba ma'lumotlari")),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_data == null || _data!['profile'] == null) {
      return Scaffold(
        appBar: AppBar(title: const Text("Xatolik")),
        body: const Center(child: Text("Ma'lumotlarni yuklab bo'lmadi")),
      );
    }

    final profile = _data!['profile'];

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Profil"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
        child: Column(
          children: [
            // 1. Profile Section (Centered)
            _buildCenteredProfile(profile),
            const SizedBox(height: 32),

            // 2. GPA Card
            _buildGPACard(profile['gpa']?.toString() ?? "0.00"),
            const SizedBox(height: 32),

            // 3. Info Grid
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              childAspectRatio: 1.1,
              children: [
                _buildCategoryCard(
                  title: "Murojaatlar",
                  count: (_data!['appeals'] as List).length,
                  icon: Icons.chat_bubble_outline_rounded,
                  color: Colors.blue,
                  onTap: () => _navigateToItems(
                    context,
                    _data!['appeals'],
                    "Murojaatlar",
                    "Murojaat",
                  ),
                ),
                _buildCategoryCard(
                  title: "Faolliklar",
                  count: (_data!['activities'] as List).length,
                  icon: Icons.local_activity_outlined,
                  color: Colors.orange,
                  onTap: () => _navigateToItems(
                    context,
                    _data!['activities'],
                    "Faolliklar",
                    "Faollik",
                  ),
                ),
                _buildCategoryCard(
                  title: "Sertifikatlar",
                  count: (_data!['certificates'] as List).length,
                  icon: Icons.card_membership_rounded,
                  color: Colors.purple,
                  onTap: () => _navigateToItems(
                    context,
                    _data!['certificates'],
                    "Sertifikatlar",
                    "Sertifikat",
                  ),
                ),
                _buildCategoryCard(
                  title: "Hujjatlar",
                  count: (_data!['documents'] as List).length,
                  icon: Icons.folder_copy_outlined,
                  color: Colors.teal,
                  onTap: () => _navigateToItems(
                    context,
                    _data!['documents'],
                    "Hujjatlar",
                    "Hujjat",
                  ),
                ),
              ],
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildCenteredProfile(dynamic profile) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: Colors.blue.withOpacity(0.2), width: 2),
          ),
          child: CircleAvatar(
            radius: 60,
            backgroundColor: Colors.grey[200],
            backgroundImage: profile['image_url'] != null ? NetworkImage(profile['image_url']) : null,
            child: profile['image_url'] == null ? const Icon(Icons.person, size: 60, color: Colors.grey) : null,
          ),
        ),
        const SizedBox(height: 20),
        Text(
          profile['full_name'] ?? "",
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.bold,
            color: Colors.black87,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          "ID: ${profile['hemis_id']} • ${profile['group_number']}",
          style: TextStyle(color: Colors.grey[600], fontSize: 14),
        ),
        const SizedBox(height: 4),
        Text(
          profile['faculty_name'] ?? "",
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey[500], fontSize: 13),
        ),
      ],
    );
  }

  Widget _buildGPACard(String gpa) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.indigo.shade600, Colors.indigo.shade800],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.indigo.withOpacity(0.3),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "O'rtacha GPA ko'rsatkichi",
                style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 4),
              Text(
                "Akademik o'zlashtirish darajasi",
                style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 12),
              ),
            ],
          ),
          Text(
            gpa,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 32,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryCard({
    required String title,
    required int count,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.grey.shade100),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(height: 12),
            Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            const SizedBox(height: 4),
            Text(
              "$count ta",
              style: TextStyle(color: Colors.grey[500], fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }

  void _navigateToItems(BuildContext context, List<dynamic> items, String title, String type) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => StudentItemsListScreen(
          items: items,
          title: title,
          itemType: type,
        ),
      ),
    );
  }
}
