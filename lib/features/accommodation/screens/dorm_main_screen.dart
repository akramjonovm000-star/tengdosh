import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import 'dorm_issue_screen.dart';
import 'dorm_roommate_screen.dart';
import 'dorm_details_widgets.dart';

class DormMainScreen extends StatelessWidget {
  const DormMainScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Yotoqxona"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      backgroundColor: AppTheme.backgroundWhite,
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Barcha xizmatlar",
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: 1.1,
                children: [
                  _buildCategoryCard(
                    context,
                    title: "Xonadoshlarim",
                    icon: Icons.people_alt_rounded,
                    color: Colors.blue,
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (context) => const DormRoommateScreen()));
                    },
                  ),
                  _buildCategoryCard(
                    context,
                    title: "Nosozliklar",
                    icon: Icons.build_circle_rounded,
                    color: Colors.orange,
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (context) => const DormIssueScreen()));
                    },
                  ),
                  _buildCategoryCard(
                    context,
                    title: "Navbatchilik",
                    icon: Icons.calendar_month_rounded,
                    color: Colors.green,
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (context) => const DormRosterScreen()));
                    },
                  ),
                  _buildCategoryCard(
                    context,
                    title: "Qoidalar",
                    icon: Icons.gavel_rounded,
                    color: Colors.redAccent,
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (context) => const DormRuleScreen()));
                    },
                  ),
                  _buildCategoryCard(
                    context,
                    title: "Oshxona menyusi",
                    icon: Icons.restaurant_menu_rounded,
                    color: Colors.amber,
                    onTap: () {
                      Navigator.push(context, MaterialPageRoute(builder: (context) => const DormMenuScreen()));
                    },
                  ),
                  _buildCategoryCard(
                    context,
                    title: "Tadbirlar",
                    icon: Icons.event_available_rounded,
                    color: Colors.indigo,
                    onTap: () {
                      // Navigator.push(context, MaterialPageRoute(builder: (context) => const DormEventsScreen()));
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCategoryCard(BuildContext context, {required String title, required IconData icon, required Color color, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.1),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
          border: Border.all(color: color.withOpacity(0.1), width: 1.5),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 40),
            const SizedBox(height: 12),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
