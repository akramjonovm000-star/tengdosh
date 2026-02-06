import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:cached_network_image/cached_network_image.dart';

class GroupActivitiesScreen extends StatefulWidget {
  final String groupNumber;
  const GroupActivitiesScreen({super.key, required this.groupNumber});

  @override
  State<GroupActivitiesScreen> createState() => _GroupActivitiesScreenState();
}

class _GroupActivitiesScreenState extends State<GroupActivitiesScreen> with SingleTickerProviderStateMixin {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _activities = [];
  
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadActivities();
  }
  
  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadActivities({bool showLoading = true}) async {
    if (showLoading) {
      setState(() => _isLoading = true);
    }
    final acts = await _dataService.getGroupActivities(widget.groupNumber);
    if (mounted) {
      setState(() {
        _activities = acts ?? [];
        _isLoading = false;
      });
      
      if (acts == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Ma'lumotlarni yuklashda xatolik yuz berdi (Timeout)"),
            backgroundColor: Colors.red,
          )
        );
      }
    }
  }
  
  Future<void> _handleReview(int id, String status) async {
    // Optimistic Update: Remove from list immediately
    final index = _activities.indexWhere((a) => a['id'] == id);
    if (index != -1) {
       setState(() {
         // Create a modified copy of activity with new status
         final activity = Map<String, dynamic>.from(_activities[index]);
         activity['status'] = status;
         _activities[index] = activity;
       });
    }

    // Call API in background
    final success = await _dataService.reviewActivity(id, status);
    
    if (success) {
      // Ideally refresh completely to sync data, but silently
      _loadActivities(showLoading: false);
      
      if (mounted) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(status == "accepted" ? "Faollik qabul qilindi" : "Faollik rad etildi"),
            backgroundColor: status == "accepted" ? Colors.green : Colors.red,
            duration: const Duration(milliseconds: 1500),
            behavior: SnackBarBehavior.floating,
          )
        );
      }
    } else {
      // Revert on failure (optional, but good practice)
      _loadActivities(showLoading: false); 
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Xatolik yuz berdi"), backgroundColor: Colors.red)
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // Split into Pending and Others (Accepted/Rejected)
    final pending = _activities.where((a) => a['status'] == "pending").toList();
    final history = _activities.where((a) => a['status'] != "pending").toList();

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text("Barcha Faolliklar: ${widget.groupNumber}"),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: "Kutayotgan"),
            Tab(text: "Tarix"),
          ],
        ),
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildList(pending, isPending: true),
                _buildList(history, isPending: false),
              ],
            ),
    );
  }
  
  Widget _buildList(List<dynamic> list, {required bool isPending}) {
    if (list.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox, size: 64, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(isPending ? "Kutayotgan faolliklar yo'q" : "Tarix bo'sh", style: TextStyle(color: Colors.grey[600])),
          ],
        ),
      );
    }
    
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: list.length,
      itemBuilder: (context, index) {
        final item = list[index];
        final student = item['student'] ?? {};
        
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
                Row(
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
                          Text(item['created_at'] != null ? item['created_at'].toString().split('T')[0] : "", style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                        ],
                      ),
                    ),
                    _buildStatusChip(item['status']),
                  ],
                ),
                const Divider(height: 24),
                
                // Content
                Text(item['name'] ?? "Faollik", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 4),
                Text(item['category'] ?? "", style: const TextStyle(color: AppTheme.primaryBlue, fontSize: 12, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                if (item['description'] != null)
                  Text(item['description'], style: const TextStyle(color: Colors.black87)),
                  
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
                          child: const Text("Rad etish"),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () => _handleReview(item['id'], "accepted"),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            elevation: 0
                          ),
                          child: const Text("Tasdiqlash"),
                        ),
                      ),
                    ],
                  )
                ]
              ],
            ),
          ),
        );
      },
    );
  }
  
  Widget _buildStatusChip(String status) {
    Color color = Colors.grey;
    String label = status;
    
    switch (status) {
      case 'accepted': color = Colors.green; label = "Tasdiqlangan"; break;
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
}
