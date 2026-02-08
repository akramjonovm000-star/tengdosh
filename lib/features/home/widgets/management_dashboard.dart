import 'package:flutter/material.dart';
import '../screens/management/hemis/hemis_dashboard_screen.dart';
import '../screens/management/student_search_screen.dart';
import '../screens/management/staff_search_screen.dart';
import '../../student_module/widgets/student_dashboard_widgets.dart';
import '../../../../core/services/data_service.dart';
import '../../management/screens/management_archive_screen.dart';
import '../../management/screens/management_appeals_screen.dart';

class ManagementDashboard extends StatelessWidget {
  final Map<String, dynamic>? stats;

  const ManagementDashboard({super.key, this.stats});

  @override
  Widget build(BuildContext context) {
    final Map<String, dynamic> data = stats ?? {};
    final int studentCount = data['student_count'] ?? 0;
    final int platformUsers = data['platform_users'] ?? 0;
    final int usagePercentage = data['usage_percentage'] ?? 0;
    final int staffCount = data['staff_count'] ?? 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 1. Platform Usage Card (NEW & PROMINENT)
        _buildPlatformUsageCard(studentCount, platformUsers, usagePercentage),
        const SizedBox(height: 24),

        // 2. Small Stats Row
        Row(
          children: [
            Expanded(
              child: InkWell(
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const StudentSearchScreen()),
                  );
                },
                borderRadius: BorderRadius.circular(16),
                child: _StatCard(
                  title: "Talaba qidirish",
                  value: studentCount.toString(),
                  icon: Icons.people_alt_rounded,
                  color: Colors.blue,
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: InkWell(
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const StaffSearchScreen()),
                  );
                },
                borderRadius: BorderRadius.circular(16),
                child: _StatCard(
                  title: "Xodimlar",
                  value: staffCount.toString(),
                  icon: Icons.business_center_rounded,
                  color: Colors.orange,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),

        const Text(
          "Boshqaruv Paneli",
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
              title: "HEMIS",
              icon: Icons.military_tech_rounded,
              color: Colors.amber,
              onTap: () => _showHemisSubmenu(context),
            ),
            DashboardCard(
              title: "Xodimlar Monitoringi",
              icon: Icons.manage_accounts_rounded,
              color: Colors.deepPurple,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const StaffSearchScreen()),
                );
              },
            ),
            DashboardCard(
              title: "Murojaatlar (Umumiy)",
              icon: Icons.all_inbox_rounded,
              color: Colors.teal,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const ManagementAppealsScreen()),
                );
              },
            ),
            DashboardCard(
              title: "Hujjatlar Arxivi",
              icon: Icons.inventory_2_rounded,
              color: Colors.blueGrey,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const ManagementArchiveScreen()),
                );
              },
            ),
            DashboardCard(
              title: "Tizim Analitikasi",
              icon: Icons.insights_rounded,
              color: Colors.indigo,
              onTap: () => _showNotImplemented(context, "Analitika"),
            ),
          ],
        ),
        const SizedBox(height: 32),
      ],
    );
  }

  Widget _buildPlatformUsageCard(int total, int active, int percentage) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.blue.shade700, Colors.blue.shade900],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.blue.withOpacity(0.3),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "Platforma aktivligi",
                style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  "$percentage%",
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: percentage / 100,
              backgroundColor: Colors.white.withOpacity(0.1),
              valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
              minHeight: 12,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Faol Talabalar", style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12)),
                  const SizedBox(height: 4),
                  Text("$active", style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text("Jami Talabalar", style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12)),
                  const SizedBox(height: 4),
                  Text("$total", style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showNotImplemented(BuildContext context, String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("$feature bo'limi hozirda ishlab chiqilmoqda.")),
    );
  }

  void _showHemisSubmenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "HEMIS Bo'limi",
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const SizedBox(height: 24),
            _buildSubmenuItem(
              context,
              title: "HEMIS Monitoring",
              icon: Icons.military_tech_rounded,
              color: Colors.amber,
              onTap: () => _showNotImplemented(context, "HEMIS"),
            ),
            const SizedBox(height: 12),
            _buildSubmenuItem(
              context,
              title: "Moliyaviy Holat",
              icon: Icons.account_balance_wallet_rounded,
              color: Colors.cyan,
              onTap: () => _showNotImplemented(context, "Moliya"),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildSubmenuItem(BuildContext context, {required String title, required IconData icon, required Color color, required VoidCallback onTap}) {
    return InkWell(
      onTap: () {
        Navigator.pop(context);
        onTap();
      },
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.05),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.1)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 16),
            Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
            const Spacer(),
            const Icon(Icons.chevron_right, color: Colors.grey, size: 20),
          ],
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.08),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
        border: Border.all(color: color.withOpacity(0.1), width: 1),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 32),
          const SizedBox(height: 12),
          Text(
            value,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          Text(
            title,
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[600], fontSize: 11),
          ),
        ],
      ),
    );
  }
}
