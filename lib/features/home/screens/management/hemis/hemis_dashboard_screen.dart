import 'package:flutter/material.dart';
import '../dormitory/dormitory_dashboard_screen.dart';

class HemisDashboardScreen extends StatelessWidget {
  const HemisDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F7),
      appBar: AppBar(
        title: const Text(
          "HEMIS",
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.black, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildHemisCard(
              context,
              title: "HEMIS Monitoring",
              icon: Icons.military_tech_rounded,
              color: Colors.amber,
              onTap: () => _showNotImplemented(context, "HEMIS Monitoring"),
            ),
            const SizedBox(height: 16),
            _buildHemisCard(
              context,
              title: "Moliyaviy Holat",
              icon: Icons.account_balance_wallet_rounded,
              color: Colors.cyan,
              onTap: () => _showNotImplemented(context, "Moliya"),
            ),
            const SizedBox(height: 16),
            _buildHemisCard(
              context,
              title: "Yotoqxona",
              icon: Icons.bedroom_parent_rounded,
              color: Colors.blue,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const DormitoryDashboardScreen()),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHemisCard(BuildContext context, {
    required String title,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.08),
              blurRadius: 15,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(width: 20),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.grey.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.chevron_right, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  void _showNotImplemented(BuildContext context, String feature) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("$feature bo'limi hozirda ishlab chiqilmoqda.")),
    );
  }
}
