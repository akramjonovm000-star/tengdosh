import 'package:flutter/material.dart';
import '../../student_module/widgets/student_dashboard_widgets.dart';

class ManagementDashboard extends StatelessWidget {
  final Map<String, dynamic>? stats;

  const ManagementDashboard({super.key, this.stats});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Top Stats Row
        Row(
          children: [
            Expanded(
              child: _StatCard(
                title: "Talabalar",
                value: "${stats?['student_count'] ?? '3,450'}",
                icon: Icons.people_alt_rounded,
                color: Colors.blue,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _StatCard(
                title: "Xodimlar",
                value: "${stats?['staff_count'] ?? '184'}",
                icon: Icons.business_center_rounded,
                color: Colors.orange,
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
              title: "Tizim Analitikasi",
              icon: Icons.insights_rounded,
              color: Colors.indigo,
              onTap: () => _showNotImplemented(context, "Analitika"),
            ),
            DashboardCard(
              title: "Xodimlar Monitoringi",
              icon: Icons.manage_accounts_rounded,
              color: Colors.deepPurple,
              onTap: () => _showNotImplemented(context, "Monitoring"),
            ),
            DashboardCard(
              title: "Murojaatlar (Umumiy)",
              icon: Icons.all_inbox_rounded,
              color: Colors.teal,
              onTap: () => _showNotImplemented(context, "Murojaatlar"),
            ),
            DashboardCard(
              title: "Hujjatlar Arshivi",
              icon: Icons.inventory_2_rounded,
              color: Colors.blueGrey,
              onTap: () => _showNotImplemented(context, "Arxiv"),
            ),
            DashboardCard(
              title: "KPI Reytinglari",
              icon: Icons.military_tech_rounded,
              color: Colors.amber,
              onTap: () => _showNotImplemented(context, "KPI"),
            ),
            DashboardCard(
              title: "Moliyaviy Holat",
              icon: Icons.account_balance_wallet_rounded,
              color: Colors.cyan,
              onTap: () => _showNotImplemented(context, "Moliya"),
            ),
          ],
        ),
        const SizedBox(height: 32),
      ],
    );
  }

  void _showNotImplemented(BuildContext context, String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("$feature bo'limi hozirda ishlab chiqilmoqda.")),
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
