import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import 'club_detail_screen.dart';

class ClubsScreen extends StatefulWidget {
  const ClubsScreen({super.key});

  @override
  State<ClubsScreen> createState() => _ClubsScreenState();
}

class _ClubsScreenState extends State<ClubsScreen> {
  final DataService _dataService = DataService();
  List<dynamic> _clubs = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadClubs();
  }

  Future<void> _loadClubs() async {
    try {
      final clubs = await _dataService.getClubs();
      if (mounted) {
        setState(() {
          _clubs = clubs;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Klublarni yuklashda xatolik yuz berdi")),
        );
      }
    }
  }

  IconData _getIconData(String? iconName) {
    // Basic mapping or default
    return Icons.groups_rounded;
  }

  Color _getColor(String? colorHex) {
    if (colorHex == null || colorHex.isEmpty) return AppTheme.primaryBlue;
    try {
      return Color(int.parse(colorHex.replaceFirst('#', '0xFF')));
    } catch (e) {
      return AppTheme.primaryBlue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Klublar", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator())
        : (_clubs.isEmpty 
           ? _buildEmptyState()
           : ListView.separated(
              padding: const EdgeInsets.all(20),
              itemCount: _clubs.length,
              separatorBuilder: (_, __) => const SizedBox(height: 16),
              itemBuilder: (context, index) {
                final club = _clubs[index];
                return _buildClubCard(club);
              },
            )),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.groups_outlined, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            "Hozircha klublar yo'q",
            style: TextStyle(color: Colors.grey[600], fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            "Tez orada yangi klublar qo'shiladi",
            style: TextStyle(color: Colors.grey[400], fontSize: 14),
          ),
        ],
      ),
    );
  }

  Widget _buildClubCard(Map<String, dynamic> club) {
    final bool isJoined = club['is_joined'] ?? false;
    final Color clubColor = _getColor(club['color']);
    final IconData clubIcon = _getIconData(club['icon']);
    
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04), // [FIXED] withOpacity -> withValues
            blurRadius: 15,
            offset: const Offset(0, 5),
          )
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => ClubDetailScreen(club: club)),
            ).then((_) => _loadClubs()); // reload on back
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                // Icon
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: clubColor.withValues(alpha: 0.1), // [FIXED]
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Icon(clubIcon, color: clubColor, size: 30),
                ),
                const SizedBox(width: 16),
                
                // Info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              club['name'] ?? 'Klub nomi',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          if (club['is_leader'] == true) ...[
                            const SizedBox(width: 4),
                            const Text("👑", style: TextStyle(fontSize: 14)),
                          ]
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "${club['members_count'] ?? 0} a'zo",
                        style: TextStyle(color: Colors.grey[500], fontSize: 12),
                      ),
                    ],
                  ),
                ),

                // Action / Status
                if (club['is_leader'] == true)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Text(
                      "Boshqarish",
                      style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  )
                else if (isJoined)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.green.withValues(alpha: 0.1), // [FIXED]
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Text(
                      "A'zosiz",
                      style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  )
                else
                  const Icon(Icons.arrow_forward_ios_rounded, color: Colors.grey, size: 16)
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Replaced bottom sheet logic completely.
}
