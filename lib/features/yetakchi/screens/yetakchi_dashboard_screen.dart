import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../services/yetakchi_service.dart';
import 'yetakchi_students_screen.dart';
import 'yetakchi_activities_screen.dart';
import 'yetakchi_events_screen.dart';
import 'yetakchi_reports_screen.dart';
import 'yetakchi_announcements_screen.dart';
import 'yetakchi_documents_screen.dart';

class YetakchiDashboardScreen extends StatefulWidget {
  final Map<String, dynamic>? initialStats;

  const YetakchiDashboardScreen({Key? key, this.initialStats}) : super(key: key);

  @override
  State<YetakchiDashboardScreen> createState() => _YetakchiDashboardScreenState();
}

class _YetakchiDashboardScreenState extends State<YetakchiDashboardScreen> {
  final YetakchiService _service = YetakchiService();
  Map<String, dynamic>? _stats;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialStats != null) {
      _stats = widget.initialStats;
    } else {
      _loadStats();
    }
  }

  Future<void> _loadStats() async {
    setState(() => _isLoading = true);
    final stats = await _service.getDashboardStats();
    if (mounted) {
      setState(() {
        _stats = stats;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return _isLoading && _stats == null 
       ? const Center(child: CircularProgressIndicator()) 
       : _buildDashboard();
  }

  Widget _buildDashboard() {
    final s = _stats ?? {};
    final tStudents = s['total_students'] ?? 0;
    final aStudents = s['active_students'] ?? 0;
    final pActivities = s['pending_activities'] ?? 0;
    final tEvents = s['total_events'] ?? 0;

    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("Umumiy Holat", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            childAspectRatio: 1.4,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            children: [
              _buildStatCard("Jami talabalar", tStudents.toString(), Icons.groups, Colors.blue),
              _buildStatCard("Faol talabalar", aStudents.toString(), Icons.star_rounded, Colors.orange),
              _buildStatCard("Kutilayotgan faollik", pActivities.toString(), Icons.pending_actions, Colors.red),
              _buildStatCard("Tadbirlar", tEvents.toString(), Icons.event_available, Colors.green),
            ],
          ),
          
          const SizedBox(height: 24),
          const Text("Boshqaruv", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),

          _buildMenuTile(
            title: "Talabalar ro'yxati",
            subtitle: "Barcha talabalar qidiruvi va holati",
            icon: Icons.school,
            color: Colors.indigo,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const YetakchiStudentsScreen()))
          ),
          _buildMenuTile(
            title: "Faolliklarni tasdiqlash",
            subtitle: "Talabalar yuklagan ma'lumotlar ($pActivities kutilmoqda)",
            icon: Icons.checklist_rtl,
            color: Colors.deepOrange,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const YetakchiActivitiesScreen()))
          ),
          _buildMenuTile(
            title: "Tadbirlar",
            subtitle: "Yangi tadbir yaratish va ro'yxat",
            icon: Icons.celebration,
            color: Colors.teal,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const YetakchiEventsScreen()))
          ),
          _buildMenuTile(
            title: "Hisobotlar (PDF/Excel)",
            subtitle: "Oylik va haftalik hisobotlar",
            icon: Icons.bar_chart,
            color: AppTheme.primaryBlue,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const YetakchiReportsScreen()))
          ),
          _buildMenuTile(
            title: "E'lonlar va So'rovnomalar",
            subtitle: "Barcha talabalar uchun xabarnoma jo'natish",
            icon: Icons.campaign,
            color: Colors.purple,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const YetakchiAnnouncementsScreen()))
          ),
          _buildMenuTile(
            title: "Hujjatlar Arvixi",
            subtitle: "Barcha yuklangan fayl va ma'lumotlar ro'yxati",
            icon: Icons.folder,
            color: Colors.amber[700]!,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const YetakchiDocumentsScreen()))
          ),
          
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4))
        ]
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, color: color, size: 28),
              Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
            ],
          ),
          Text(title, style: TextStyle(color: Colors.grey[700], fontSize: 13, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _buildMenuTile({required String title, required String subtitle, required IconData icon, required Color color, required VoidCallback onTap}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
           BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 2))
        ]
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
          child: Icon(icon, color: color),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        subtitle: Text(subtitle, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
        trailing: const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.grey),
        onTap: onTap,
      ),
    );
  }
}
