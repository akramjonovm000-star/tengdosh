import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/features/feedback/screens/feedback_screen.dart';
import 'package:provider/provider.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/core/providers/auth_provider.dart';
import 'package:talabahamkor_mobile/features/profile/screens/profile_screen.dart';
import 'package:talabahamkor_mobile/features/community/screens/community_screen.dart';
import 'package:talabahamkor_mobile/features/student_module/screens/student_module_screen.dart';
import 'package:talabahamkor_mobile/features/ai/screens/ai_screen.dart';
import 'package:talabahamkor_mobile/features/student_module/widgets/student_dashboard_widgets.dart';
import 'package:talabahamkor_mobile/features/student_module/screens/academic_screen.dart';
import 'package:talabahamkor_mobile/features/social/screens/social_activity_screen.dart';
import 'package:talabahamkor_mobile/features/documents/screens/documents_screen.dart';
import '../../certificates/screens/certificates_screen.dart';
import '../../clubs/screens/clubs_screen.dart';
import '../../appeals/screens/appeals_screen.dart';
import '../../auth/widgets/password_update_dialog.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final DataService _dataService = DataService();
  Map<String, dynamic>? _profile;
  Map<String, dynamic>? _dashboard;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    // Use WidgetsBinding to avoid blocking the initial build frame
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadData();
    });
  }

  Future<void> _loadData() async {
    try {
      // Fetch profile and dashboard concurrently for speed
      final results = await Future.wait([
        _dataService.getProfile(),
        _dataService.getDashboardStats(),
      ]);
      
      if (mounted) {
        setState(() {
          _profile = results[0];
          _dashboard = results[1];
          _isLoading = false;
        });
        
        // SYNC: Update Global Auth State so Profile Screen gets new data immediately
        if (_profile != null) {
           Provider.of<AuthProvider>(context, listen: false).updateUser(_profile!);
        }
      }
    } catch (e) {
      print("Error loading home data: $e");
      if (mounted) {
        setState(() => _isLoading = false); // Still stop loading to show empty UI
      }
    }
  }

  void _logout() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Chiqish"),
        content: const Text("Tizimdan chiqmoqchimisiz?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Yo'q"),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              _dataService.clearCache(); // Clear local cache
              Provider.of<AuthProvider>(context, listen: false).logout();
            },
            child: const Text("Ha", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Watch for Auth Update Required
    final isAuthUpdateRequired = context.watch<AuthProvider>().isAuthUpdateRequired;
    if (isAuthUpdateRequired) {
      Future.microtask(() {
        if (mounted) {
           showDialog(
             context: context,
             barrierDismissible: false, // Force them to update or click 'later'
             builder: (context) => const PasswordUpdateDialog(),
           );
        }
      });
    }

    // Screens for BottomNav
    final List<Widget> screens = [
      _buildHomeContent(),           // 0: Home (Dashboard)
      const StudentModuleScreen(),   // 1: Yangiliklar (Ex-Talaba)
      const AiScreen(),              // 2: AI
      const CommunityScreen(),       // 3: Choyxona
      const ProfileScreen(),         // 4: Profile
    ];

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite, 
      body: SafeArea(
        child: screens[_currentIndex],
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10)],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          selectedItemColor: AppTheme.primaryBlue,
          unselectedItemColor: Colors.grey,
          showUnselectedLabels: true,
          type: BottomNavigationBarType.fixed,
          backgroundColor: Colors.white,
          elevation: 0,
          onTap: (index) => setState(() => _currentIndex = index),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.grid_view_rounded), label: "Asosiy"),
            BottomNavigationBarItem(icon: Icon(Icons.shopping_bag_rounded), label: "Bozor"),
            BottomNavigationBarItem(icon: Icon(Icons.smart_toy_rounded), label: "AI"),
            BottomNavigationBarItem(icon: Icon(Icons.forum_rounded), label: "Choyxona"),
            BottomNavigationBarItem(icon: Icon(Icons.person_rounded), label: "Profil"),
          ],
        ),
      ),
    );
  }

  Widget _buildHomeContent() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Header (Avatar + Name + Status)
          Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: Colors.grey[200],
                child: const Icon(Icons.person, color: Colors.grey),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Salom, ${() {
                      final firstName = _profile?['first_name'] ?? _profile?['short_name'];
                      if (firstName != null && firstName.toString().isNotEmpty) {
                        return firstName.toString();
                      }
                      
                      // Fallback logic
                      final name = _profile?['full_name'] ?? 'Talaba';
                      
                      // Logic: If ALL CAPS "SURNAME FIRSTNAME FATHERNAME"
                      final parts = name.split(' ');
                      if (parts.length >= 2) {
                         // Standard Uzbek: Last First Father (e.g. Akramjonov Muxammadali Ulug'bek)
                         // Return 2nd word
                         final first = parts[1];
                         return first[0].toUpperCase() + first.substring(1).toLowerCase();
                      }
                      return name;
                    }()}!",
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  Row(
                    children: [
                      Container(width: 8, height: 8, decoration: const BoxDecoration(color: AppTheme.accentGreen, shape: BoxShape.circle)),
                      const SizedBox(width: 6),
                      Text("Online", style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                    ],
                  ),
                ],
              ),
              const Spacer(),
              Stack(
                children: [
                  IconButton(icon: const Icon(Icons.notifications_none_rounded, size: 28), onPressed: () {}),
                  Positioned(right: 12, top: 12, child: Container(width: 8, height: 8, decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle))),
                ],
              ),
              IconButton(
                icon: const Icon(Icons.logout_rounded, color: Colors.redAccent),
                onPressed: _logout,
                tooltip: "Chiqish",
              ),
            ],
          ),
          const SizedBox(height: 24),

          // 2. GPA Module (Full Width)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppTheme.primaryBlue, Color(0xFF0052CC)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(color: AppTheme.primaryBlue.withOpacity(0.3), blurRadius: 20, offset: const Offset(0, 10)),
              ],
            ),
            child: Row(
              children: [
                SizedBox(
                  width: 80,
                  height: 80,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      CircularProgressIndicator(
                        value: (_dashboard?['gpa'] ?? 0.0) / 5.0,
                        strokeWidth: 8,
                        color: AppTheme.accentGreen,
                        backgroundColor: Colors.white.withOpacity(0.2),
                      ),
                      Text(
                        "${_dashboard?['gpa'] ?? '0.0'}", 
                        style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 20),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Joriy Semestr", 
                        style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 14)
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        "A'lo natija! 🏆", 
                        style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)
                      ),
                      Text(
                        "Guruh: ${_profile?['group_number'] ?? '...'}", 
                        style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12)
                      ),
                    ],
                  ),
                )
              ],
            ),
          ),
          const SizedBox(height: 24),

          // 3. Module Grid (Dashboard)
          const Text(
            "Xizmatlar",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87),
          ),
          const SizedBox(height: 16),
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            childAspectRatio: 1.1,
            children: [
              DashboardCard(
                title: "Akademik bo'lim",
                icon: Icons.school_rounded,
                color: Colors.green,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => AcademicScreen())),
              ),
              DashboardCard(
                title: "Ijtimoiy Faollik",
                icon: Icons.star_rounded,
                color: Colors.orange,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SocialActivityScreen())),
              ),
              DashboardCard(
                title: "Hujjatlar",
                icon: Icons.folder_copy_rounded,
                color: Colors.blue,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const DocumentsScreen())),
              ),
              DashboardCard(
                title: "Sertifikatlar",
                icon: Icons.workspace_premium_rounded,
                color: Colors.orange,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CertificatesScreen())),
              ),
              DashboardCard(
          title: "Klublar",
          icon: Icons.groups_rounded,
          color: Colors.teal,
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ClubsScreen())),
        ),
                DashboardCard(
                  title: "Murojaatlar",
                  icon: Icons.chat_bubble_outline_rounded,
                  color: Colors.redAccent,
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FeedbackScreen())),
                ),
            ],
          ),
        ],
      ),
    );
  }

  void _showMock(String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("$feature bo'limi tez orada ishga tushadi!")),
    );
  }
}
