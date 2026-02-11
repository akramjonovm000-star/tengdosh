import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'package:intl/intl.dart';

class ActivityReviewScreen extends StatefulWidget {
  final String? initialStatus;
  final String title;

  const ActivityReviewScreen({
    super.key, 
    this.initialStatus,
    required this.title,
  });

  @override
  State<ActivityReviewScreen> createState() => _ActivityReviewScreenState();
}

class _ActivityReviewScreenState extends State<ActivityReviewScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _activities = [];
  int _totalCount = 0;
  int _currentPage = 1;
  String? _selectedStatus;

  @override
  void initState() {
    super.initState();
    _selectedStatus = widget.initialStatus;
    _loadActivities();
  }

  Future<void> _loadActivities({bool refresh = false}) async {
    if (refresh) {
      setState(() {
        _currentPage = 1;
        _isLoading = true;
      });
    }

    try {
      final res = await _dataService.getManagementActivities(
        status: _selectedStatus == "Barchasi" ? null : _selectedStatus,
        page: _currentPage,
      );

      if (mounted) {
        setState(() {
          if (refresh) {
            _activities = res['data'] ?? [];
          } else {
            _activities.addAll(res['data'] ?? []);
          }
          _totalCount = res['total'] ?? 0;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Xatolik: $e")));
      }
    }
  }

  Future<void> _approve(int id) async {
    final success = await _dataService.approveActivity(id);
    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Faollik tasdiqlandi")));
      _loadActivities(refresh: true);
    }
  }

  Future<void> _reject(int id) async {
    String? comment;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        final controller = TextEditingController();
        return AlertDialog(
          title: const Text("Rad etish"),
          content: TextField(
            controller: controller,
            decoration: const InputDecoration(hintText: "Sababini kiriting (ixtiyoriy)"),
            maxLines: 3,
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("Bekor qilish")),
            ElevatedButton(
              onPressed: () {
                comment = controller.text;
                Navigator.pop(context, true);
              },
              child: const Text("Rad etish"),
            ),
          ],
        );
      }
    );

    if (confirmed == true) {
      final success = await _dataService.rejectActivity(id, comment);
      if (success && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Faollik rad etildi")));
        _loadActivities(refresh: true);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(widget.title),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: () => _loadActivities(refresh: true)),
        ],
      ),
      body: Column(
        children: [
          _buildFilterBar(),
          Expanded(
            child: _isLoading && _activities.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : _activities.isEmpty
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        onRefresh: () => _loadActivities(refresh: true),
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _activities.length + (_activities.length < _totalCount ? 1 : 0),
                          itemBuilder: (context, index) {
                            if (index == _activities.length) {
                              _currentPage++;
                              _loadActivities();
                              return const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()));
                            }
                            return _buildActivityCard(_activities[index]);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterBar() {
    final statuses = [
      {"label": "Barchasi", "value": "Barchasi"},
      {"label": "Kutilmoqda", "value": "pending"},
      {"label": "Tasdiqlangan", "value": "confirmed"},
      {"label": "Rad etilgan", "value": "rejected"},
    ];

    return Container(
      height: 60,
      color: Colors.white,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        itemCount: statuses.length,
        itemBuilder: (context, index) {
          final s = statuses[index];
          final isSelected = _selectedStatus == s['value'] || (_selectedStatus == null && s['value'] == "Barchasi");
          
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(s['label']!),
              selected: isSelected,
              onSelected: (val) {
                if (val) {
                  setState(() {
                    _selectedStatus = s['value'];
                    _isLoading = true;
                    _activities = [];
                  });
                  _loadActivities(refresh: true);
                }
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildActivityCard(dynamic item) {
    final status = item['status'] ?? 'pending';
    final int id = int.tryParse(item['id'].toString()) ?? 0;
    Color statusColor = Colors.orange;
    if (status == 'confirmed') statusColor = Colors.green;
    if (status == 'rejected') statusColor = Colors.red;

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ListTile(
            title: Text(item['name'] ?? "Nomsiz", style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text("${item['student_full_name']} • ${item['category']}"),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
              child: Text(status.toUpperCase(), style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold)),
            ),
          ),
          if (item['description'] != null && item['description'].toString().isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Text(item['description'], style: TextStyle(color: Colors.grey[700])),
            ),
          
          if (item['images'] != null && (item['images'] as List).isNotEmpty)
            SizedBox(
              height: 150,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemCount: (item['images'] as List).length,
                itemBuilder: (context, idx) {
                   final String imageUrl = item['images'][idx];
                   return Padding(
                     padding: const EdgeInsets.all(4.0),
                     child: GestureDetector(
                       onTap: () {
                         showDialog(
                           context: context,
                           builder: (_) => Dialog(
                             backgroundColor: Colors.transparent,
                             child: Stack(
                               alignment: Alignment.topRight,
                               children: [
                                 InteractiveViewer(child: Image.network(imageUrl)),
                                 IconButton(icon: const Icon(Icons.close, color: Colors.white), onPressed: () => Navigator.pop(context)),
                               ],
                             ),
                           )
                         );
                       },
                       child: ClipRRect(
                         borderRadius: BorderRadius.circular(12),
                         child: Image.network(
                           imageUrl,
                           width: 150,
                           height: 150,
                           fit: BoxFit.cover,
                           errorBuilder: (context, error, stackTrace) => Container(
                             width: 150,
                             height: 150,
                             color: Colors.grey[200],
                             child: const Icon(Icons.broken_image, color: Colors.grey),
                           ),
                         ),
                       ),
                     ),
                   );
                },
              ),
            ),
          
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(item['date'] ?? "", style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                if (status == 'pending')
                  Row(
                    children: [
                      TextButton(onPressed: () => _reject(id), child: const Text("Rad etish", style: TextStyle(color: Colors.red))),
                      const SizedBox(width: 8),
                      ElevatedButton(onPressed: () => _approve(id), child: const Text("Tasdiqlash")),
                    ],
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return const Center(child: Text("Hozircha ma'lumot yo'q"));
  }
}
