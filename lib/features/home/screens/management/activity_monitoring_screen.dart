import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart'; // Ensure this package is available or mock charts
import '../../../../core/services/data_service.dart';
import '../../widgets/management_dashboard.dart';

class ActivityMonitoringScreen extends StatefulWidget {
  const ActivityMonitoringScreen({super.key});

  @override
  State<ActivityMonitoringScreen> createState() => _ActivityMonitoringScreenState();
}

class _ActivityMonitoringScreenState extends State<ActivityMonitoringScreen> {
  bool _isLoading = true;
  Map<String, dynamic>? _dashboardStats;
  List<dynamic> _activityTrend = [];
  List<dynamic> _facultyStats = [];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final stats = await DataService().getAnalyticsDashboard();
      final trend = await DataService().getActivityTrend();
      final faculties = await DataService().getFacultyActivityStats();
      
      setState(() {
        _dashboardStats = stats;
        _activityTrend = trend;
        _facultyStats = faculties;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      // Handle error
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Faollik Monitoringi"),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
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
                    
                    // 2. Trend Chart
                    const Text(
                      "So'nggi 30 kun faolligi",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    _buildTrendChart(),
                    const SizedBox(height: 24),
                    
                    // 3. Faculty List
                    const Text(
                      "Fakultetlar Kesimida",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    _buildFacultyList(),
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
      childAspectRatio: 1.4,
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      children: [
        _buildStatCard("Jami Talabalar", "${_dashboardStats!['total_students']}", Icons.people, Colors.blue),
        _buildStatCard("Faol (7 kun)", "${_dashboardStats!['active_students_7d']}", Icons.trending_up, Colors.green),
        _buildStatCard("Bugungi Faollik", "${_dashboardStats!['total_activities_today']}", Icons.today, Colors.orange),
        _buildStatCard("Faollik Darajasi", "${_dashboardStats!['active_percentage']}%", Icons.speed, Colors.purple),
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
          Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          Text(title, style: TextStyle(color: Colors.grey[600], fontSize: 12), textAlign: TextAlign.center),
        ],
      ),
    );
  }

  Widget _buildTrendChart() {
    // Placeholder for Chart - assumes standard container for now
    // Implementing actual LineChart requires fl_chart parsing logic
    return Container(
      height: 200,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: const Center(
        child: Text("Faollik Grafigi (Line Chart)", style: TextStyle(color: Colors.grey)),
      ),
    );
  }

  Widget _buildFacultyList() {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _facultyStats.length,
      itemBuilder: (context, index) {
        final f = _facultyStats[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          elevation: 0,
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: Colors.grey.shade200)),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: Colors.blue.withOpacity(0.1),
              child: Text("${index + 1}", style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold)),
            ),
            title: Text(f['name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            subtitle: Text("${f['student_count']} talaba • O'rtacha: ${f['avg_activity']}"),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                "${f['activity_count']}",
                style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        );
      },
    );
  }
}
