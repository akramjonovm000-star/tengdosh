import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart'; // [FIXED] Added Import

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
          onTap: () => _showClubDetails(club),
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
                      Text(
                        club['name'] ?? 'Klub nomi',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
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
                if (isJoined)
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

  void _showClubDetails(Map<String, dynamic> club) {
    final Color clubColor = _getColor(club['color']);
    final IconData clubIcon = _getIconData(club['icon']);
    final bool isJoined = club['is_joined'] ?? false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.6,
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          children: [
            const SizedBox(height: 8),
            Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        color: clubColor.withValues(alpha: 0.1), // [FIXED]
                        shape: BoxShape.circle,
                      ),
                      child: Icon(clubIcon, color: clubColor, size: 40),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      club['name'] ?? 'Klub nomi',
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      "${club['members_count'] ?? 0} ta ishtirokchi",
                      style: TextStyle(color: Colors.grey[500], fontSize: 14),
                    ),
                    const SizedBox(height: 24),
                    const Align(
                      alignment: Alignment.centerLeft,
                      child: Text("Klub haqida", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      club['description'] ?? 'Tavsif yo\'q',
                      style: TextStyle(color: Colors.grey[700], fontSize: 15, height: 1.5),
                    ),
                    const SizedBox(height: 30),
                  ],
                ),
              ),
            ),
            
            // Bottom Action
            Padding(
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                height: 50,
                child: isJoined
                  ? OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      style: OutlinedButton.styleFrom(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        side: BorderSide(color: Colors.grey[300]!)
                      ),
                      child: const Text("Yopish", style: TextStyle(color: Colors.black)),
                    )
                  : ElevatedButton(
                      onPressed: () {
                        Navigator.pop(context);
                        _showJoinProcess(club);
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryBlue,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        elevation: 0,
                      ),
                      child: const Text("A'zo bo'lish", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showJoinProcess(Map<String, dynamic> club) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text("Tasdiqlash", textAlign: TextAlign.center),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              "A'zo bo'lish uchun avval klubning Telegram kanaliga qo'shiling.",
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            ListTile(
              leading: const Icon(Icons.telegram, color: Colors.blue, size: 32),
              title: const Text("Telegram Kanal", style: TextStyle(fontWeight: FontWeight.bold)),
              subtitle: const Text("Linkni ochish"),
              onTap: () {
                 ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Telegramga o'tilmoqda... (Mock)"))
                );
              },
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(color: Colors.grey[200]!)
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Bekor qilish", style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              
              final success = await _dataService.joinClub(club['id']);
              
              if (success) {
                _loadClubs(); // Refresh list to show "A'zosiz"
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text("Tabriklaymiz! Siz ${club['name']} a'zosi bo'ldingiz"),
                      backgroundColor: Colors.green,
                    )
                  );
                }
              } else {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text("Klubga a'zo bo'lishda xatolik yuz berdi"),
                      backgroundColor: Colors.red,
                    )
                  );
                }
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text("A'zo bo'ldim"),
          ),
        ],
      ),
    );
  }
}
