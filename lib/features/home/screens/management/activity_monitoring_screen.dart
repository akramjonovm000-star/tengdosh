import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import '../../widgets/management_dashboard.dart';
import 'student_search_screen.dart';

class ActivityMonitoringScreen extends StatefulWidget {
  const ActivityMonitoringScreen({super.key});

  @override
  State<ActivityMonitoringScreen> createState() => _ActivityMonitoringScreenState();
}

class _ActivityMonitoringScreenState extends State<ActivityMonitoringScreen> {
  bool _isLoading = true;
  Map<String, dynamic>? _dashboardStats;
  List<dynamic> _recentSubmissions = [];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final stats = await DataService().getAnalyticsDashboard();
      final recent = await DataService().getRecentActivitySubmissions();
      
      setState(() {
        _dashboardStats = stats;
        _recentSubmissions = recent;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      debugPrint("Error loading activity data: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Ijtimoiy Faolliklar"),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const StudentSearchScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          )
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadData,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. KPI Cards
                    _buildKPIGrid(),
                    const SizedBox(height: 24),
                    
                    // 2. Category Breakdown
                    const Text(
                      "Kategoriyalar Bo'yicha",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    _buildCategoryBreakdown(),
                    const SizedBox(height: 24),
                    
                    // 3. Recent Submissions
                    const Text(
                      "So'nggi Yuklanganlar",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    _buildRecentSubmissions(),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildKPIGrid() {
    if (_dashboardStats == null) return const SizedBox.shrink();
    
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      childAspectRatio: 1.5,
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      children: [
        _buildStatCard("Jami Faolliklar", "${_dashboardStats!['total_activities']}", Icons.local_activity, Colors.blue),
        _buildStatCard("Kutilmoqda", "${_dashboardStats!['pending_count']}", Icons.hourglass_empty, Colors.orange),
        _buildStatCard("Tasdiqlangan", "${_dashboardStats!['approved_count']}", Icons.check_circle, Colors.green),
        _buildStatCard("Bu Oy", "${_dashboardStats!['activities_this_month']}", Icons.calendar_today, Colors.purple),
      ],
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: color.withOpacity(0.1), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          Text(title, style: TextStyle(color: Colors.grey[600], fontSize: 13), textAlign: TextAlign.center),
        ],
      ),
    );
  }

  Widget _buildCategoryBreakdown() {
    if (_dashboardStats == null || _dashboardStats!['category_breakdown'] == null) {
      return const SizedBox.shrink();
    }

    final categories = Map<String, int>.from(_dashboardStats!['category_breakdown']);
    if (categories.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white, 
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade200)
        ),
        child: const Center(child: Text("Hozircha ma'lumot yo'q", style: TextStyle(color: Colors.grey))),
      );
    }
    
    // Sort logic removed for simplicity or add: 
    // var sortedKeys = categories.keys.toList()..sort((a,b) => categories[b]!.compareTo(categories[a]!));

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        children: categories.entries.map((e) {
          final total = _dashboardStats!['total_activities'] as int;
          final percent = total > 0 ? (e.value / total) : 0.0;
          return Padding(
            padding: const EdgeInsets.only(bottom: 12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(e.key.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    Text("${e.value} ta (${(percent * 100).toStringAsFixed(1)}%)", style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                  ],
                ),
                const SizedBox(height: 6),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: percent,
                    backgroundColor: Colors.grey[100],
                    valueColor: AlwaysStoppedAnimation<Color>(_getColorForCategory(e.key)),
                    minHeight: 8,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
  
  Color _getColorForCategory(String category) {
    switch (category.toLowerCase()) {
      case 'sport': return Colors.green;
      case 'zakovat': return Colors.blue;
      case 'volontyorlik': return Colors.orange;
      case 'ijod': return Colors.purple;
      default: return Colors.blueGrey;
    }
  }

  Widget _buildRecentSubmissions() {
    if (_recentSubmissions.isEmpty) {
      return const Center(child: Text("So'nggi arizalar mavjud emas", style: TextStyle(color: Colors.grey)));
    }

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _recentSubmissions.length,
      itemBuilder: (context, index) {
        final item = _recentSubmissions[index];
        final status = item['status'] ?? 'pending';
        Color statusColor = Colors.orange;
        IconData statusIcon = Icons.hourglass_empty;
        
        if (status == 'confirmed' || status == 'approved') {
          statusColor = Colors.green;
          statusIcon = Icons.check_circle;
        } else if (status == 'rejected') {
          statusColor = Colors.red;
          statusIcon = Icons.cancel;
        }

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          elevation: 0,
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: Colors.grey.shade200)),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: CircleAvatar(
              backgroundColor: _getColorForCategory(item['category'] ?? '').withOpacity(0.1),
              child: Icon(Icons.star, color: _getColorForCategory(item['category'] ?? ''), size: 20),
            ),
            title: Text(item['name'] ?? "Nomsiz", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text("${item['student_name']} • ${item['category']}", style: TextStyle(fontSize: 12)),
                Text(item['date'] ?? "", style: TextStyle(color: Colors.grey[500], fontSize: 11)),
              ],
            ),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: statusColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8)
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(statusIcon, color: statusColor, size: 14),
                  const SizedBox(width: 4),
                  Text(status.toUpperCase(), style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
