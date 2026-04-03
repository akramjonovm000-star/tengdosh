import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'management_rating_stats_screen.dart';

class ManagementRatingHubScreen extends StatefulWidget {
  const ManagementRatingHubScreen({super.key});

  @override
  State<ManagementRatingHubScreen> createState() => _ManagementRatingHubScreenState();
}

class _ManagementRatingHubScreenState extends State<ManagementRatingHubScreen> {
  final DataService _dataService = DataService();
  bool _isActive = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  Future<void> _loadStatus() async {
    final status = await _dataService.getManagementRatingStatus();
    if (mounted) {
      setState(() {
        _isActive = status;
        _isLoading = false;
      });
    }
  }

  Future<void> _toggleStatus() async {
    setState(() => _isLoading = true);
    final result = await _dataService.toggleRatingActivation('tutor', !_isActive);
    if (result['success'] == true) {
      await _loadStatus();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_isActive ? "So'rovnoma faollashtirildi" : "So'rovnoma to'xtatildi"),
            backgroundColor: _isActive ? Colors.green : Colors.orange,
          ),
        );
      }
    } else {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? "Xatolik yuz berdi"),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Tyutor Rating"),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            const SizedBox(height: 20),
            _buildLargeButton(
              context,
              title: "Tyutorlarni baholash so'rovnomasini yaratish",
              subtitle: _isActive ? "Hozirda faol" : "Hozirda to'xtatilgan",
              icon: Icons.add_task_rounded,
              color: _isActive ? Colors.green : Colors.blue,
              isLoading: _isLoading,
              onTap: _toggleStatus,
            ),
            const SizedBox(height: 24),
            _buildLargeButton(
              context,
              title: "Mavjud so'rovnomalar bo'yicha statistika",
              subtitle: "Natijalarni ko'rish",
              icon: Icons.analytics_rounded,
              color: Colors.indigo,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const ManagementRatingStatsScreen()),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLargeButton(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
    bool isLoading = false,
  }) {
    return InkWell(
      onTap: isLoading ? null : onTap,
      borderRadius: BorderRadius.circular(24),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(32),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.1),
              blurRadius: 20,
              offset: const Offset(0, 10),
            ),
          ],
          border: Border.all(color: color.withOpacity(0.1), width: 2),
        ),
        child: Column(
          children: [
            if (isLoading)
              const SizedBox(
                height: 48,
                width: 48,
                child: CircularProgressIndicator(strokeWidth: 3),
              )
            else
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: color, size: 48),
              ),
            const SizedBox(height: 24),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                height: 1.2,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              style: TextStyle(
                color: Colors.grey[600],
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
