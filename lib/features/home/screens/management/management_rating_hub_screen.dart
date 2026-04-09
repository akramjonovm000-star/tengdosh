import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'create_management_survey_screen.dart';
import 'create_tutor_rating_survey_screen.dart';
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
  Map<String, dynamic>? _activeSurvey;

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  Future<void> _loadStatus() async {
    setState(() => _isLoading = true);
    final status = await _dataService.getManagementRatingStatus();
    final activeSurvey = await _dataService.getManagementActiveSurvey();
    
    if (mounted) {
      setState(() {
        _isActive = status;
        _activeSurvey = activeSurvey.isNotEmpty ? activeSurvey : null;
        _isLoading = false;
      });
    }
  }

  Future<void> _toggleStatus() async {
    setState(() => _isLoading = true);
    final Map<String, dynamic> result = await _dataService.toggleRatingActivation('tutor', !_isActive);
    
    if (result['success'] == true) {
      await _loadStatus();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? (_isActive ? "So'rovnoma to'xtatildi" : "So'rovnoma faollashtirildi")),
            backgroundColor: _isActive ? Colors.orange : Colors.green,
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
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator())
        : SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                const SizedBox(height: 10),
                // 1. Manage Survey Card
                _buildLargeButton(
                  context,
                  title: _activeSurvey == null ? "Yangi so'rovnoma yaratish" : "So'rovnomani boshqarish",
                  subtitle: "Savollar, variantlar va muddatlar",
                  icon: Icons.settings_suggest_rounded,
                  color: Colors.blue,
                  onTap: () {
                    _showCreateOptions(context);
                  },
                ),
                const SizedBox(height: 24),
                // 2. Stats & Analytics Card with Toggle inside
                _buildStatsCard(context),
              ],
            ),
          ),
    );
  }

  void _showCreateOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (BuildContext context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 24.0, horizontal: 16.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16.0),
                  child: Text(
                    "Tanlang",
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(height: 16),
                ListTile(
                  leading: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.quiz_outlined, color: Colors.blue),
                  ),
                  title: const Text("So'rovnoma yaratish", style: TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: const Text("Maxsus savollar va variantlar yaratish"),
                  onTap: () async {
                    Navigator.pop(context);
                    final result = await Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => CreateManagementSurveyScreen(initialData: _activeSurvey),
                      ),
                    );
                    if (result == true) {
                      _loadStatus();
                    }
                  },
                ),
                ListTile(
                  leading: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.star_outline_rounded, color: Colors.orange),
                  ),
                  title: const Text("Tyutor rating", style: TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: const Text("Tyutorni 1 dan 5 gacha baholash tizimi"),
                  onTap: () async {
                    Navigator.pop(context);
                    final result = await Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => CreateTutorRatingSurveyScreen(initialData: _activeSurvey),
                      ),
                    );
                    if (result == true) {
                      _loadStatus();
                    }
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildStatsCard(BuildContext context) {
    const Color color = Colors.indigo;
    return Container(
      width: double.infinity,
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
          InkWell(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const ManagementRatingStatsScreen()),
              );
            },
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.analytics_rounded, color: color, size: 48),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    "Natijalar va statistika",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      height: 1.2,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Tyutorlar reytingini ko'rish",
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const Divider(height: 1),
          // Toggle Action Part
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(
                      _isActive ? Icons.check_circle_outline_rounded : Icons.pause_circle_outline_rounded,
                      color: _isActive ? Colors.green : Colors.grey,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _isActive ? "Hozirda faol" : "To'xtatilgan",
                      style: TextStyle(
                        color: _isActive ? Colors.green : Colors.grey[600],
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                TextButton.icon(
                  onPressed: _toggleStatus,
                  icon: Icon(
                    _isActive ? Icons.stop_circle_outlined : Icons.play_circle_outline_rounded,
                    color: _isActive ? Colors.red : Colors.green,
                  ),
                  label: Text(
                    _isActive ? "To'xtatish" : "Faollashtirish",
                    style: TextStyle(
                      color: _isActive ? Colors.red : Colors.green,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  style: TextButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    backgroundColor: (_isActive ? Colors.red : Colors.green).withOpacity(0.1),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ],
            ),
          ),
        ],
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
