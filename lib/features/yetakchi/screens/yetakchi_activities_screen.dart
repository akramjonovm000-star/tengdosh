import 'dart:convert';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../services/yetakchi_service.dart';
import 'package:cached_network_image/cached_network_image.dart';

class YetakchiActivitiesScreen extends StatefulWidget {
  const YetakchiActivitiesScreen({Key? key}) : super(key: key);

  @override
  State<YetakchiActivitiesScreen> createState() => _YetakchiActivitiesScreenState();
}

class _YetakchiActivitiesScreenState extends State<YetakchiActivitiesScreen> with SingleTickerProviderStateMixin {
  final YetakchiService _service = YetakchiService();
  late TabController _tabController;
  
  List<dynamic> _activities = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(_handleTabSelection);
    _fetchActivities('pending');
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _handleTabSelection() {
    if (_tabController.indexIsChanging) {
      String status = ['pending', 'approved', 'rejected'][_tabController.index];
      _fetchActivities(status);
    }
  }

  Future<void> _fetchActivities(String status) async {
    setState(() => _isLoading = true);
    final results = await _service.getActivities(status: status, limit: 50);
    if (mounted) {
      setState(() {
        _activities = results;
        _isLoading = false;
      });
    }
  }

  Future<void> _reviewActivity(int activityId, String status, int points) async {
    // Optimistic UI Update
    setState(() {
      _activities.removeWhere((a) => a['id'] == activityId);
    });
    
    final success = await _service.reviewActivity(activityId, status, points);
    if (!success) {
      // Revert if failed (simple reload)
      _fetchActivities(['pending', 'approved', 'rejected'][_tabController.index]);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Xatolik yuz berdi. Qayta urinib ko'ring.")));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Faollik $status qilindi")));
    }
  }

  void _showReviewDialog(Map<String, dynamic> activity) {
     final TextEditingController pointsController = TextEditingController(text: "0");
     
     showDialog(
       context: context,
       builder: (ctx) {
         return AlertDialog(
           shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
           title: const Text("Faollik baholash", style: TextStyle(fontWeight: FontWeight.bold)),
           content: Column(
             mainAxisSize: MainAxisSize.min,
             children: [
               Text(activity['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.w600)),
               const SizedBox(height: 16),
               TextField(
                 controller: pointsController,
                 keyboardType: TextInputType.number,
                 decoration: InputDecoration(
                   labelText: "Ajratiladigan ball",
                   border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))
                 ),
               )
             ]
           ),
           actions: [
             TextButton(
               onPressed: () {
                 Navigator.pop(ctx);
                 _reviewActivity(activity['id'], "rejected", 0);
               },
               child: const Text("Rad etish", style: TextStyle(color: Colors.red)),
             ),
             ElevatedButton(
               onPressed: () {
                 Navigator.pop(ctx);
                 int pts = int.tryParse(pointsController.text) ?? 0;
                 _reviewActivity(activity['id'], "approved", pts);
               },
               style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
               child: const Text("Tasdiqlash", style: TextStyle(color: Colors.white)),
             )
           ],
         );
       }
     );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Faolliklar", style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppTheme.primaryBlue,
          unselectedLabelColor: Colors.grey,
          indicatorColor: AppTheme.primaryBlue,
          tabs: const [
            Tab(text: "Kutilayotgan"),
            Tab(text: "Tasdiqlangan"),
            Tab(text: "Rad etilgan"),
          ],
        ),
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator())
        : _activities.isEmpty 
            ? _buildEmptyState()
            : _buildList(),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inbox, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text("Ma'lumot topilmadi", style: TextStyle(color: Colors.grey[500], fontSize: 16))
        ],
      ),
    );
  }

  Widget _buildList() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _activities.length,
      itemBuilder: (context, index) {
        final item = _activities[index];
        final isPending = item['status'] == 'pending';
        
        // Parse Images if any
        List<String> imageUrls = [];
        if (item['images'] != null && item['images'].toString().isNotEmpty && item['images'] != 'null') {
           try {
              imageUrls = List<String>.from(json.decode(item['images']));
           } catch(e) {}
        }
        
        return Card(
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: Colors.grey[200]!)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                   mainAxisAlignment: MainAxisAlignment.spaceBetween,
                   children: [
                     Expanded(child: Text(item['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16))),
                     Container(
                       padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                       decoration: BoxDecoration(
                         color: isPending ? Colors.orange.withOpacity(0.1) : (item['status'] == 'approved' ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1)),
                         borderRadius: BorderRadius.circular(8)
                       ),
                       child: Text(item['status'].toString().toUpperCase(), 
                         style: TextStyle(
                           fontSize: 10, 
                           fontWeight: FontWeight.bold,
                           color: isPending ? Colors.orange : (item['status'] == 'approved' ? Colors.green : Colors.red)
                         ))
                     )
                   ],
                ),
                const SizedBox(height: 8),
                Text(item['description'] ?? 'Izoh yozilmagan', style: TextStyle(color: Colors.grey[700], fontSize: 13)),
                const SizedBox(height: 12),
                
                if (imageUrls.isNotEmpty)
                  SizedBox(
                    height: 80,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: imageUrls.length,
                      itemBuilder: (ctx, i) {
                        return Container(
                          margin: const EdgeInsets.only(right: 8),
                          width: 80,
                          decoration: BoxDecoration(
                             borderRadius: BorderRadius.circular(8),
                             image: DecorationImage(image: CachedNetworkImageProvider(imageUrls[i]), fit: BoxFit.cover)
                          ),
                        );
                      }
                    )
                  ),
                  
                const Divider(height: 24),
                
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.person, size: 16, color: Colors.indigo),
                        const SizedBox(width: 4),
                        Text(item['student_name'] ?? '', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
                      ],
                    ),
                    if (isPending)
                      ElevatedButton(
                        onPressed: () => _showReviewDialog(item),
                        style: ElevatedButton.styleFrom(
                           backgroundColor: AppTheme.primaryBlue,
                           foregroundColor: Colors.white,
                           elevation: 0,
                           padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0)
                        ),
                        child: const Text("Baholash", style: TextStyle(fontSize: 12)),
                      )
                    else 
                      Text("${item['points_awarded']} Ball", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.green))
                  ]
                )
              ]
            ),
          )
        );
      }
    );
  }
}
