import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

import 'package:provider/provider.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/core/providers/auth_provider.dart';
import 'package:talabahamkor_mobile/features/profile/screens/profile_screen.dart';
import 'package:talabahamkor_mobile/features/community/screens/community_screen.dart';
import 'package:talabahamkor_mobile/features/home/models/announcement_model.dart';
import 'package:talabahamkor_mobile/features/home/models/banner_model.dart'; // [NEW]
import 'package:talabahamkor_mobile/features/student_module/screens/student_module_screen.dart';
import 'package:talabahamkor_mobile/features/ai/screens/ai_screen.dart';
import 'package:talabahamkor_mobile/features/ai/screens/management_ai_screen.dart'; // [NEW]
import 'package:talabahamkor_mobile/features/student_module/widgets/student_dashboard_widgets.dart';
import 'package:talabahamkor_mobile/features/student_module/screens/academic_screen.dart';
import 'package:talabahamkor_mobile/features/student_module/screens/election_screen.dart';
import 'package:talabahamkor_mobile/features/social/screens/social_activity_screen.dart';
import 'package:talabahamkor_mobile/features/documents/screens/documents_screen.dart';
import 'package:talabahamkor_mobile/core/services/permission_service.dart'; // [NEW]
import '../../certificates/screens/certificates_screen.dart';
import 'package:talabahamkor_mobile/features/home/widgets/management_dashboard.dart';
import 'package:talabahamkor_mobile/features/tutor/screens/tutor_dashboard_screen.dart'; // [NEW]
import 'package:talabahamkor_mobile/features/profile/screens/subscription_screen.dart';
import '../../clubs/screens/clubs_screen.dart';
import '../../appeals/screens/appeals_screen.dart';
import 'package:talabahamkor_mobile/features/notifications/screens/notifications_screen.dart';
import 'package:talabahamkor_mobile/core/providers/notification_provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:async';

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
  // bool _isLoading = true; // [REMOVED unused]
  // Timer? _refreshTimer; // [REMOVED unused]

  List<AnnouncementModel> _announcements = [];
  List<BannerModel> _banners = []; // [MODIFIED] List instead of single
  final PageController _pageController = PageController();
  
  // Banner Carousel
  final PageController _bannerController = PageController();
  int _currentBannerIndex = 0;
  Timer? _bannerTimer;

  // Semester Handling
  List<dynamic> _semesters = [];
  String? _selectedSemesterId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadData();
      // PermissionService.requestInitialPermissions(); // [DEBUG] Disabled to fix build error
    });
  }

  @override
  void dispose() {
    _bannerTimer?.cancel(); // [NEW] Dispose timer
    _bannerController.dispose();
    super.dispose();
  }

  Future<void> _loadData({bool refresh = false}) async {
    try {
      final auth = Provider.of<AuthProvider>(context, listen: false);
      final isTutor = auth.isTutor;

      // Fetch profile and semesters first
      final results = await Future.wait([
        _dataService.getProfile(),
        _dataService.getSemesters(),
      ]);
      
      _profile = results[0] as Map<String, dynamic>?;
      _semesters = results[1] as List<dynamic>? ?? [];
      
      if (_semesters.isNotEmpty && _selectedSemesterId == null) {
        final first = _semesters.first;
        _selectedSemesterId = first['code']?.toString() ?? first['id']?.toString();
      }
      
      // Fetch Dashboard Stats based on Role
      if (isTutor) {
         _dashboard = await _dataService.getTutorDashboard();
      } else if (auth.isManagement) {
         final dash = await _dataService.getManagementDashboard(refresh: refresh);
         if (mounted) {
           setState(() {
             _dashboard = dash;
           });
         }
      } else {
          final dashResult = await _dataService.getDashboardStats(refresh: refresh);
          final announcements = await _dataService.getAnnouncementModels();
          final banners = await _dataService.getActiveBanners(); // [MODIFIED]

          if (mounted) {
            setState(() {
               _dashboard = dashResult;
               _announcements = announcements;
               _banners = banners;
            });
            _startBannerTimer(); // [NEW]
          }
         
         if (!refresh && (_dashboard?['gpa'] == 0 || _dashboard?['gpa'] == 0.0)) {
            print("Zero GPA detected, forcing dashboard refresh...");
            final freshDash = await _dataService.getDashboardStats(refresh: true);
            if (mounted) setState(() => _dashboard = freshDash);
         }
      }
      
      if (mounted) {
        if (_profile != null) {
           Provider.of<AuthProvider>(context, listen: false).updateUser(_profile!);
        }
      }
    } catch (e) {
      print("Error loading home data: $e");
    }
  }

  void _startBannerTimer() {
    _bannerTimer?.cancel();
    if (_banners.length > 1) {
      _bannerTimer = Timer.periodic(const Duration(seconds: 5), (timer) {
        if (_bannerController.hasClients) {
          final nextPage = (_currentBannerIndex + 1) % _banners.length;
          _bannerController.animateToPage(
            nextPage, 
            duration: const Duration(milliseconds: 500), 
            curve: Curves.easeInOut
          );
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    // 1. Get Auth Provider at the top level of build
    final auth = Provider.of<AuthProvider>(context);

    // Screens for BottomNav
    final List<Widget> screens = [
      _buildHomeContent(),           // 0: Home (Dashboard)
      const StudentModuleScreen(),   // 1: Yangiliklar
      auth.isManagement ? const ManagementAiScreen() : const AiScreen(), // 2: AI (Different for Management)
      const CommunityScreen(),       // 3: Choyxona
      const ProfileScreen(),         // 4: Profile
    ];

    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        return Stack(
          children: [
            Scaffold(
              backgroundColor: AppTheme.backgroundWhite, 
              body: SafeArea(
                child: screens[_currentIndex],
              ),
              bottomNavigationBar: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10)],
                ),
                child: BottomNavigationBar(
                  currentIndex: _currentIndex,
                  selectedItemColor: AppTheme.primaryBlue,
                  unselectedItemColor: Colors.grey,
                  showUnselectedLabels: true,
                  type: BottomNavigationBarType.fixed,
                  backgroundColor: Colors.white,
                  elevation: 0,
                  onTap: (index) {
                    final isPremium = auth.currentUser?.isPremium ?? false;
                    
                    // Guard Market (1)
                    if (index == 1) {
                      ScaffoldMessenger.of(context).hideCurrentSnackBar();
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text("Bozor bo'limi tez kunda ishga tushadi"),
                          duration: Duration(seconds: 2),
                          behavior: SnackBarBehavior.floating,
                        ),
                      );
                      return;
                    }

                    // Guard AI (2)
                    if (index == 2 && !auth.isManagement && !isPremium) {
                      _showPremiumDialog();
                      return;
                    }
                    setState(() => _currentIndex = index);
                  },
                  items: const [
                    BottomNavigationBarItem(icon: Icon(Icons.grid_view_rounded), label: "Asosiy"),
                    BottomNavigationBarItem(icon: Icon(Icons.shopping_bag_rounded), label: "Bozor"),
                    BottomNavigationBarItem(icon: Icon(Icons.smart_toy_rounded), label: "AI"),
                    BottomNavigationBarItem(icon: Icon(Icons.forum_rounded), label: "Choyxona"),
                    BottomNavigationBarItem(icon: Icon(Icons.person_rounded), label: "Profil"),
                  ],
                ),
              ),
            ),
// DISCONNECTION FIX: Removed PasswordUpdateDialog to prevent blocking UI
            // if (auth.isAuthUpdateRequired)
            //   const PasswordUpdateDialog(),
          ],
        );
      },
    );
  }

  Widget _buildHomeContent() {
    final auth = Provider.of<AuthProvider>(context);
    final student = auth.currentUser;
    final isTutor = auth.isTutor;
    
    return RefreshIndicator(
      onRefresh: () async => _loadData(refresh: true),
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                GestureDetector(
                  onTap: () {
                    setState(() {
                      _currentIndex = 4; // Switch to Profile Screen
                    });
                  },
                  child: CircleAvatar(
                    radius: 24,
                    backgroundColor: Colors.grey[200],
                    child: () {
                       final url = student?.imageUrl;
                       if (url != null && url.isNotEmpty) {
                         return ClipOval(
                           child: CachedNetworkImage(
                             imageUrl: url,
                             width: 48,
                             height: 48,
                             fit: BoxFit.cover,
                             placeholder: (context, url) => const Icon(Icons.person, color: Colors.grey),
                             errorWidget: (context, url, error) => const Icon(Icons.person, color: Colors.grey),
                           ),
                         );
                       }
                       return const Icon(Icons.person, color: Colors.grey);
                    }(),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              "Salom, ${() {
                                if (student == null) return "Foydalanuvchi";
                                
                                final fullName = student.fullName;
                                if (fullName == "Talaba") return "Foydalanuvchi";

                                final parts = fullName.split(' ');
                                if (parts.length >= 2) {
                                   String name = parts[1];
                                   return name.isNotEmpty ? name[0].toUpperCase() + name.substring(1).toLowerCase() : name;
                                } else if (parts.isNotEmpty) {
                                   String first = parts[0];
                                   return first.isNotEmpty ? first[0].toUpperCase() + first.substring(1).toLowerCase() : first;
                                }
                                
                                return fullName;
                              }()}!",
                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                            ),
                          ),
                          if (student?.isPremium == true) ...[
                            const SizedBox(width: 6),
                            GestureDetector(
                              onTap: () {
                                 Navigator.push(context, MaterialPageRoute(builder: (_) => const SubscriptionScreen()));
                              },
                              child: student?.customBadge != null
                                  ? Text(student!.customBadge!, style: const TextStyle(fontSize: 20))
                                  : const Icon(Icons.verified, color: Colors.blue, size: 20),
                            ),
                          ]
                        ],
                      ),
                      Row(
                        children: [
                          Container(width: 8, height: 8, decoration: const BoxDecoration(color: AppTheme.accentGreen, shape: BoxShape.circle)),
                          const SizedBox(width: 6),
                          Text(
                            auth.isManagement ? "Rahbariyat" : (isTutor ? "Tyutor" : "Online"), 
                            style: TextStyle(color: Colors.grey[600], fontSize: 12)
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                Consumer<NotificationProvider>(
                  builder: (context, notificationProvider, _) => Stack(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.notifications_none_rounded, size: 28),
                        onPressed: () async {
                          await Navigator.push(context, MaterialPageRoute(builder: (_) => NotificationsScreen()));
                          notificationProvider.refreshUnreadCount();
                        },
                      ),
                      if (notificationProvider.unreadCount > 0)
                        Positioned(
                          right: 12,
                          top: 12,
                          child: IgnorePointer(
                            child: Container(
                              width: 8, 
                              height: 8, 
                              decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle)
                            ),
                          )
                        ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            if (auth.isManagement)
               ManagementDashboard(stats: _dashboard)
            else if (isTutor) 
               TutorDashboardScreen(stats: _dashboard)
            else
               _buildStudentDashboard(),
          ],
        ),
      ),
    );
  }

  Widget _buildStudentDashboard() {
    return Column(
      children: [
            // 2. GPA/AnnouncementModel Module (Full Width)
            SizedBox(
              height: 180,
              child: PageView.builder(
                controller: _pageController,
                scrollDirection: Axis.vertical,
                itemCount: _announcements.length + 1 + (_banners.isNotEmpty ? 1 : 0),
                itemBuilder: (context, index) {
                  // 1. Announcements
                  if (index < _announcements.length) {
                    return _buildAnnouncementModelCard(_announcements[index]);
                  }
                  
                  // 2. Banners (Carousel)
                  if (_banners.isNotEmpty && index == _announcements.length) {
                     return _buildBannerCarousel();
                  }
                  
                  // 3. GPA Card (Always last)
                  return _buildGpaCard();
                },
              ),
            ),
            const SizedBox(height: 24),
            
            // ... [rest of method unchanged] ...
            if (_dashboard?['has_active_election'] == true)
              Container(
                margin: const EdgeInsets.only(bottom: 24),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.amber[50],
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.amber[200]!),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.how_to_vote_rounded, color: Colors.amber, size: 32),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "Faol saylov!",
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          Text(
                            "O'zingiz tanlagan nomzodga ovoz bering",
                            style: TextStyle(color: Colors.grey[700], fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                    ElevatedButton(
                      onPressed: () {
                         final electionId = _dashboard?['active_election_id'];
                         if (electionId != null) {
                            Navigator.push(
                              context, 
                              MaterialPageRoute(builder: (_) => ElectionScreen(electionId: electionId))
                            );
                         }
                      },
                      style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryBlue,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      elevation: 0,
                    ),
                    child: const Text("Ovoz berish"),
                  )
                ],
              ),
            ),

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
                  onTap: () {
                    final isPremium = Provider.of<AuthProvider>(context, listen: false).currentUser?.isPremium ?? false;
                    if (!isPremium) {
                       _showPremiumDialog();
                       return;
                    }
                    Navigator.push(context, MaterialPageRoute(builder: (_) => SocialActivityScreen()));
                  },
                ),
                DashboardCard(
                  title: "Hujjatlar",
                  icon: Icons.folder_copy_rounded,
                  color: Colors.blue,
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => DocumentsScreen())),
                ),
                DashboardCard(
                  title: "Sertifikatlar",
                  icon: Icons.workspace_premium_rounded,
                  color: Colors.orange,
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => CertificatesScreen())),
                ),
                DashboardCard(
                  title: "Klublar",
                  icon: Icons.groups_rounded,
                  color: Colors.teal,
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ClubsScreen())),
                ),
                DashboardCard(
                  title: "Murojaatlar",
                  icon: Icons.chat_bubble_outline_rounded,
                  color: Colors.redAccent,
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => AppealsScreen())),
                ),
              ],
            ),
      ],
    );
  }

  Widget _buildGpaCard() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 4),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 15,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Row(
          children: [
            Stack(
              alignment: Alignment.center,
              children: [
                SizedBox(
                  width: 80,
                  height: 80,
                  child: CircularProgressIndicator(
                    value: (_dashboard?['gpa'] ?? 0.0) / 5.0,
                    strokeWidth: 8,
                    strokeCap: StrokeCap.round,
                    valueColor: const AlwaysStoppedAnimation(AppTheme.primaryBlue),
                    backgroundColor: Colors.grey[100],
                  ),
                ),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      "${_dashboard?['gpa']?.toStringAsFixed(1) ?? '0.0'}",
                      style: const TextStyle(
                        color: Colors.black87,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        height: 1.0,
                      ),
                    ),
                    Text(
                      "GPA",
                      style: TextStyle(
                        color: Colors.grey[500],
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                )
              ],
            ),
            const SizedBox(width: 24),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    "O'zlashtirish",
                    style: TextStyle(
                      color: Colors.grey[500],
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    (_dashboard?['gpa'] ?? 0.0) >= 4.5 ? "A'lo natija! 🏆" :
                    (_dashboard?['gpa'] ?? 0.0) >= 4.0 ? "Yaxshi natija! 👏" :
                    (_dashboard?['gpa'] ?? 0.0) >= 3.0 ? "Yomon emas 👍" : "Harakat qiling 💪",
                    style: const TextStyle(
                      color: Colors.black87,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildAnnouncementModelCard(AnnouncementModel announcement) {
    return GestureDetector(
      onTap: () async {
        if (announcement.link != null) {
          final uri = Uri.parse(announcement.link!);
          final success = await _dataService.markAnnouncementModelAsRead(announcement.id);
          
          if (success) {
            setState(() {
              _announcements.removeWhere((a) => a.id == announcement.id);
            });
            // Auto scroll to next or GPA if empty
            if (_pageController.hasClients) {
               _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
            }
          }
          
          await launchUrl(uri, mode: LaunchMode.externalApplication);
        }
      },
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.symmetric(horizontal: 4),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: AppTheme.primaryBlue.withValues(alpha: 0.2)),
          image: announcement.imageUrl != null ? DecorationImage(
            image: CachedNetworkImageProvider(announcement.imageUrl!),
            fit: BoxFit.cover,
            colorFilter: ColorFilter.mode(Colors.black.withValues(alpha: 0.4), BlendMode.darken),
          ) : null,
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, 4)),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Text(
                announcement.title,
                style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              if (announcement.content != null) ...[
                const SizedBox(height: 4),
                Text(
                  announcement.content!,
                  style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 13),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  // [NEW] Banner Carousel Widget
  Widget _buildBannerCarousel() {
    return Stack(
      children: [
        PageView.builder(
          controller: _bannerController,
          itemCount: _banners.length,
          onPageChanged: (index) {
             setState(() => _currentBannerIndex = index);
          },
          itemBuilder: (context, index) {
            return _buildBannerItem(_banners[index]);
          },
        ),
        // Indicators
        if (_banners.length > 1)
          Positioned(
            bottom: 16,
            right: 16,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: List.generate(_banners.length, (index) {
                return Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.symmetric(horizontal: 3),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _currentBannerIndex == index 
                        ? Colors.white 
                        : Colors.white.withValues(alpha: 0.5),
                  ),
                );
              }),
            ),
          ),
      ],
    );
  }

  Widget _buildBannerItem(BannerModel banner) {
    return GestureDetector(
      onTap: () async {
        if (banner.id != null) {
          _dataService.trackBannerClick(banner.id!);
        }
        if (banner.link != null && banner.link!.isNotEmpty) {
           final uri = Uri.parse(banner.link!);
           await launchUrl(uri, mode: LaunchMode.externalApplication);
        }
      },
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.symmetric(horizontal: 4),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          image: DecorationImage(
            image: CachedNetworkImageProvider(banner.imageUrl),
            fit: BoxFit.cover,
          ),
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, 4)),
          ],
        ),
      ),
    );
  }

  void _showPremiumDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Row(
          children: [
            Icon(Icons.workspace_premium, color: Colors.amber),
            SizedBox(width: 10),
            Text("Premium kerak"),
          ],
        ),
        content: const Text(
          "Bu bo'limdan foydalanish uchun Premium obunangiz bo'lishi lozim. "
          "Premium orqali barcha cheklovlarni olib tashlang!",
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text("Keyinroq", style: TextStyle(color: Colors.grey[600])),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.push(context, MaterialPageRoute(builder: (_) => SubscriptionScreen()));
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            child: const Text("Premiumga o'tish", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
// Trigger analysis update
