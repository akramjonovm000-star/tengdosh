import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/features/tutor/screens/group_activities_screen.dart';
import 'package:talabahamkor_mobile/core/localization/app_dictionary.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:talabahamkor_mobile/core/constants/api_constants.dart';

class TutorActivityGroupsScreen extends StatefulWidget {
  const TutorActivityGroupsScreen({super.key});

  @override
  State<TutorActivityGroupsScreen> createState() => _TutorActivityGroupsScreenState();
}

class _TutorActivityGroupsScreenState extends State<TutorActivityGroupsScreen> with SingleTickerProviderStateMixin {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _groupsStats = [];
  List<dynamic> _recentActivities = [];
  Map<String, dynamic> _aggregateStats = {"pending": 0, "today": 0};
  
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }
  
  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    
    // Load groups
    final groupsStats = await _dataService.getTutorActivityStats();
    
    // Load recent activities
    final recentData = await _dataService.getTutorRecentActivities();
    
    if (mounted) {
      setState(() {
        _groupsStats = groupsStats ?? [];
        if (recentData != null) {
          _recentActivities = recentData['data'] ?? [];
          _aggregateStats = recentData['stats'] ?? {"pending": 0, "today": 0};
        }
        _isLoading = false;
      });
      
      if (groupsStats == null || recentData == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Ma'lumotlarni yuklashda xatolik yuz berdi"),
            backgroundColor: Colors.red,
          )
        );
      }
    }
  }

  Future<void> _handleReview(int id, String status) async {
    // Optimistic Update: Remove from list immediately
    final index = _recentActivities.indexWhere((a) => a['id'] == id);
    if (index != -1) {
       setState(() {
         final activity = Map<String, dynamic>.from(_recentActivities[index]);
         activity['status'] = status;
         _recentActivities[index] = activity;
         
         // Update aggregated stats optimistically if needed
         if (status == 'approved' && _aggregateStats['pending'] > 0) {
            _aggregateStats['pending']--;
         } else if (status == 'rejected' && _aggregateStats['pending'] > 0) {
            _aggregateStats['pending']--;
         }
       });
    }

    // Call API in background
    final success = await _dataService.reviewActivity(id, status);
    
    if (success) {
      if (mounted) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(status == "approved" ? "Faollik qabul qilindi" : "Faollik rad etildi"),
            backgroundColor: status == "approved" ? Colors.green : Colors.red,
            duration: const Duration(milliseconds: 1500),
            behavior: SnackBarBehavior.floating,
          )
        );
      }
    } else {
      _loadData(); // Revert
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppDictionary.tr(context, 'msg_error_occurred')), backgroundColor: Colors.red)
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text(AppDictionary.tr(context, 'lbl_activity_stats')),
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.black,
          unselectedLabelColor: Colors.grey,
          indicatorColor: AppTheme.primaryBlue,
          tabs: const [
            Tab(text: "So'nggi faolliklar"),
            Tab(text: "Guruhlar"),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildRecentActivitiesTab(),
                _buildGroupsTab(),
              ],
            ),
    );
  }

  Widget _buildRecentActivitiesTab() {
    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Aggregated Stats Card
          Row(
             children: [
               Expanded(
                 child: _buildStatCard(
                   title: "Kutmoqda", 
                   count: _aggregateStats['pending'] ?? 0, 
                   color: Colors.orange, 
                   icon: Icons.pending_actions
                 )
               ),
               const SizedBox(width: 12),
               Expanded(
                 child: _buildStatCard(
                   title: "Bugun", 
                   count: _aggregateStats['today'] ?? 0, 
                   color: Colors.green, 
                   icon: Icons.today
                 )
               ),
             ]
          ),
          const SizedBox(height: 24),
          const Text("Eng so'nggi faolliklar", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          
          if (_recentActivities.isEmpty)
             Padding(
               padding: const EdgeInsets.only(top: 40),
               child: Center(
                 child: Column(
                   children: [
                     Icon(Icons.inbox, size: 64, color: Colors.grey[300]),
                     const SizedBox(height: 16),
                     Text("So'nggi faolliklar yo'q", style: TextStyle(color: Colors.grey[600])),
                   ],
                 )
               ),
             )
          else
             ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _recentActivities.length,
                itemBuilder: (context, index) {
                   return _buildActivityCard(_recentActivities[index]);
                }
             )
        ],
      )
    );
  }
  
  Widget _buildActivityCard(dynamic item) {
    final student = item['student'] ?? {};
    final isPending = item['status'] == "pending";
    
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            InkWell(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => UserProfileScreen(
                      authorId: item['student_id']?.toString() ?? "0", // if available
                      authorName: student['full_name'] ?? "Talaba",
                      authorUsername: "",
                      authorAvatar: student['image'] ?? "",
                      authorRole: "student",
                    ),
                  ),
                );
              },
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4.0),
                child: Row(
                  children: [
                    CircleAvatar(
                      backgroundImage: student['image'] != null 
                          ? CachedNetworkImageProvider(student['image'])
                          : null,
                      child: student['image'] == null ? const Icon(Icons.person) : null,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(student['full_name'] ?? "Talaba", style: const TextStyle(fontWeight: FontWeight.bold)),
                          Text('${student['group_number'] ?? ""} • ${item['created_at'] != null ? item['created_at'].toString().split('T')[0] : ""}', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                        ],
                      ),
                    ),
                    _buildStatusChip(item['status']),
                  ],
                ),
              ),
            ),
            const Divider(height: 24),
            
            // Content
            Text(item['name'] ?? "Faollik", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 4),
            Text(item['category'] ?? "", style: const TextStyle(color: AppTheme.primaryBlue, fontSize: 12, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (item['description'] != null)
              Text(item['description'], style: const TextStyle(color: Colors.black87)),
              
            if (item['images'] != null && (item['images'] as List).isNotEmpty) ...[
              const SizedBox(height: 12),
              SizedBox(
                height: 120,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: item['images'].length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (context, idx) {
                    final imgFileId = item['images'][idx]['file_id'];
                    final imageUrl = "${ApiConstants.backendUrl}/api/v1/files/$imgFileId";
                    return GestureDetector(
                      onTap: () {
                        showDialog(
                          context: context,
                          builder: (context) => Dialog(
                            backgroundColor: Colors.black.withOpacity(0.9),
                            insetPadding: EdgeInsets.zero,
                            child: Stack(
                              alignment: Alignment.center,
                              children: [
                                InteractiveViewer(
                                  minScale: 0.5,
                                  maxScale: 4.0,
                                  child: ConstrainedBox(
                                    constraints: BoxConstraints(
                                      maxWidth: MediaQuery.of(context).size.width,
                                      maxHeight: MediaQuery.of(context).size.height,
                                    ),
                                    child: CachedNetworkImage(
                                      imageUrl: imageUrl,
                                      fit: BoxFit.contain,
                                      placeholder: (context, url) => const Center(child: CircularProgressIndicator(color: Colors.white)),
                                      errorWidget: (context, url, err) => const Icon(Icons.broken_image, color: Colors.white, size: 50),
                                    ),
                                  ),
                                ),
                                Positioned(
                                  top: 40,
                                  right: 20,
                                  child: IconButton(
                                    icon: const Icon(Icons.close, color: Colors.white, size: 32),
                                    onPressed: () => Navigator.pop(context),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: CachedNetworkImage(
                          imageUrl: imageUrl,
                          width: 120,
                          fit: BoxFit.cover,
                          placeholder: (context, url) => Container(
                            width: 120, 
                            color: Colors.grey[200], 
                            child: const Icon(Icons.image, color: Colors.grey)
                          ),
                          errorWidget: (context, url, err) => Container(
                            width: 120, 
                            color: Colors.grey[200], 
                            child: const Icon(Icons.broken_image, color: Colors.grey)
                          ),
                        ),
                      ),
                    );
                  }
                ),
              ),
            ],
              
            // Actions
            if (isPending) ...[
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => _handleReview(item['id'], "rejected"),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.red,
                        side: const BorderSide(color: Colors.red),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))
                      ),
                      child: Text(AppDictionary.tr(context, 'btn_reject')),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () => _handleReview(item['id'], "approved"),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        elevation: 0
                      ),
                      child: Text(AppDictionary.tr(context, 'btn_confirm')),
                    ),
                  ),
                ],
              )
            ]
          ],
        ),
      ),
    );
  }
  
  Widget _buildStatusChip(String status) {
    Color color = Colors.grey;
    String label = status;
    
    switch (status) {
      case 'approved': color = Colors.green; label = "Tasdiqlangan"; break;
      case 'rejected': color = Colors.red; label = "Rad etilgan"; break;
      case 'pending': color = Colors.orange; label = "Kutmoqda"; break;
    }
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3))
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildStatCard({required String title, required int count, required Color color, required IconData icon}) {
     return Container(
       padding: const EdgeInsets.all(16),
       decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.3))
       ),
       child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
             Icon(icon, color: color),
             const SizedBox(height: 12),
             Text(count.toString(), style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
             const SizedBox(height: 4),
             Text(title, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: color.withOpacity(0.8))),
          ]
       )
     );
  }

  Widget _buildGroupsTab() {
    if (_groupsStats.isEmpty) {
       return Center(child: Text(AppDictionary.tr(context, 'msg_no_assigned_groups')));
    }
    
    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _groupsStats.length,
        itemBuilder: (context, index) {
          final item = _groupsStats[index];
          final pending = item['pending_count'] ?? 0;
          final today = item['today_count'] ?? 0;

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: Colors.grey.withOpacity(0.2)),
            ),
            child: InkWell(
              onTap: () async {
                await Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => GroupActivitiesScreen(
                      groupNumber: item['group_number'],
                    ),
                  ),
                );
                _loadData(); // Refresh on return
              },
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: Colors.deepPurple.withOpacity(0.1),
                      child: const Icon(Icons.accessibility_new_rounded, color: Colors.deepPurple),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Guruh: ${item['group_number']}",
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              if (pending > 0)
                                Container(
                                  margin: const EdgeInsets.only(right: 8),
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: Colors.orange.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: Colors.orange.withOpacity(0.3))
                                  ),
                                  child: Text(
                                    "Kutmoqda: $pending",
                                    style: const TextStyle(color: Colors.orange, fontSize: 12, fontWeight: FontWeight.bold),
                                  ),
                                ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: Colors.green.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(color: Colors.green.withOpacity(0.3))
                                ),
                                child: Text(
                                  "Bugun: $today",
                                  style: const TextStyle(color: Colors.green, fontSize: 12, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          )
                        ],
                      ),
                    ),
                    const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Colors.grey),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
