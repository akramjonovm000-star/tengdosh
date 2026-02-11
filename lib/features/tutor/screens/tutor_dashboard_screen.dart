import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/features/home/screens/management/student_search_screen.dart'; // [FIXED PATH]
import 'package:talabahamkor_mobile/features/home/screens/management/staff_search_screen.dart'; // [FIXED PATH]
import 'package:talabahamkor_mobile/features/student_module/widgets/student_dashboard_widgets.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';

// Import Tutor specific screens (will create stubs if needed)
import 'package:talabahamkor_mobile/features/tutor/screens/tutor_groups_screen.dart'; 
import 'package:talabahamkor_mobile/features/tutor/screens/tutor_activity_groups_screen.dart';
import 'package:talabahamkor_mobile/features/tutor/screens/tutor_documents_groups_screen.dart';
import 'package:talabahamkor_mobile/features/tutor/screens/tutor_certificates_groups_screen.dart';


class TutorDashboardScreen extends StatelessWidget {
  final Map<String, dynamic>? stats;

  const TutorDashboardScreen({super.key, this.stats});

  @override
  Widget build(BuildContext context) {
    final Map<String, dynamic> data = stats ?? {};
    // Tutor specific stats map keys might change, but for now reuse logic
    final int studentCount = data['student_count'] ?? 0; 
    final int groupCount = data['group_count'] ?? 0;

    return SingleChildScrollView(
        child: Padding(
            padding: const EdgeInsets.all(0.0), // Remove padding to match ManagementDashboard usage (it's called inside Padding in HomeScreen... wait ManagementDashboard has no padding?)
            // ManagementDashboard used inside Column with padding in HomeScreen. 
            // Better to keep structure identical.
            // Let's check HomeScreen: used inside Column inside SingleChildScrollView with padding 20.
            // So we don't need padding here? 
            // ManagementDashboard returns Column.
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. Big Feature Card (Replica of Platform Usage)
                _buildGroupAttendanceCard(studentCount, groupCount),
                const SizedBox(height: 24),

                // 2. Small Stats Row (Replica of Talabalar/Xodimlar)
                Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () {
                           Navigator.push(context, MaterialPageRoute(builder: (_) => const StudentSearchScreen()));
                        },
                        borderRadius: BorderRadius.circular(16),
                        child: _StatCard(
                          title: "Talabalarim",
                          value: "$studentCount",
                          icon: Icons.people_alt_rounded,
                          color: Colors.blue,
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: InkWell(
                        onTap: () {
                           Navigator.push(context, MaterialPageRoute(builder: (_) => const TutorGroupsScreen()));
                        },
                        borderRadius: BorderRadius.circular(16),
                        child: _StatCard(
                          title: "Guruhlarim",
                          value: "$groupCount",
                          icon: Icons.class_rounded,
                          color: Colors.orange,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                const Text(
                  "Tyutor Menyu",
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
                      title: "Murojaatlar",
                      icon: Icons.mark_chat_unread_rounded,
                      color: Colors.indigo,
                      onTap: () {
                         Navigator.push(context, MaterialPageRoute(builder: (_) => const TutorGroupsScreen()));
                      },
                    ),
                    DashboardCard(
                      title: "Faolliklar",
                      icon: Icons.accessibility_new_rounded,
                      color: Colors.deepPurple,
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const TutorActivityGroupsScreen()));
                      },
                    ),
                    DashboardCard(
                      title: "Hujjatlar",
                      icon: Icons.folder_shared_rounded,
                      color: Colors.blueGrey,
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const TutorDocumentsGroupsScreen()));
                      },
                    ),
                    DashboardCard(
                      title: "Sertifikatlar",
                      icon: Icons.workspace_premium_rounded,
                      color: Colors.amber,
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const TutorCertificatesGroupsScreen()));
                      },
                    ),
                    DashboardCard(
                      title: "Klublar",
                      icon: Icons.groups_rounded, 
                      color: Colors.teal,
                      onTap: () => _showNotImplemented(context, "Klublar (Guruh)"),
                    ),
                    DashboardCard(
                      title: "Davomat",
                      icon: Icons.verified_user_rounded,
                      color: Colors.redAccent,
                      onTap: () => _showNotImplemented(context, "Davomat"),
                    ),
                  ],
                ),
                const SizedBox(height: 32),
              ],
            )
        )
    );
  }

  Widget _buildGroupAttendanceCard(int studentCount, int groupCount) {
    // Mock Percentage for now, or calc from data
    int percentage = 85; 
    
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.indigo.shade700, Colors.indigo.shade900],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.indigo.withOpacity(0.3),
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
                "Davomat Ko'rsatkichi",
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
                  Text("Faol Guruhlar", style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12)),
                  const SizedBox(height: 4),
                  Text("$groupCount", style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text("Jami Talabalar", style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12)),
                  const SizedBox(height: 4),
                  Text("$studentCount", style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                ],
              ),
            ],
          ),
        ],
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
