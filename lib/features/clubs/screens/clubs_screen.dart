import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import '../../../../core/providers/auth_provider.dart';
import 'club_detail_screen.dart';
import 'club_create_screen.dart';

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
          const SnackBar(content: Text(AppDictionary.tr(context, 'msg_clubs_load_error'))),
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
      floatingActionButton: Provider.of<AuthProvider>(context).isYetakchi
          ? FloatingActionButton.extended(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ClubCreateScreen()),
                ).then((_) => _loadClubs());
              },
              backgroundColor: AppTheme.primaryBlue,
              icon: const Icon(Icons.add, color: Colors.white),
              label: const Text("Klub qo'shish", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            )
          : null,
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
                  const Icon(Icons.arrow_forward_ios_rounded, color: Colors.grey, size: 16),
                  
                if (Provider.of<AuthProvider>(context, listen: false).isYetakchi) ...[
                   const SizedBox(width: 8),
                   PopupMenuButton<String>(
                     icon: const Icon(Icons.more_vert, color: Colors.grey),
                     onSelected: (val) {
                       if (val == 'edit') {
                         _showEditClubSheet(club);
                       }
                     },
                     itemBuilder: (ctx) => [
                       const PopupMenuItem(
                         value: 'edit',
                         child: Row(
                           children: [
                             Icon(Icons.edit, size: 20, color: Colors.blue),
                             SizedBox(width: 8),
                             Text(AppDictionary.tr(context, 'btn_edit')),
                           ],
                         ),
                       ),
                     ],
                   ),
                ]
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Replaced bottom sheet logic completely.
  void _showEditClubSheet(Map<String, dynamic> club) {
    final TextEditingController nameCtl = TextEditingController(text: club['name']);
    final TextEditingController leaderCtl = TextEditingController(text: club['leader_login'] ?? ''); // Not all clubs return leader_login but they might
    final TextEditingController channelCtl = TextEditingController(text: club['channel_link'] ?? '');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        bool isSaving = false;
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Container(
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(context).viewInsets.bottom,
                left: 20, right: 20, top: 20
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 40, height: 4,
                        decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)),
                      ),
                    ),
                    const SizedBox(height: 20),
                    const Text("Klubni tahrirlash", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 16),
                    TextField(
                      controller: nameCtl,
                      decoration: InputDecoration(
                        labelText: "Klub nomi", 
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        filled: true,
                        fillColor: Colors.grey[50],
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: leaderCtl,
                      decoration: InputDecoration(
                        labelText: "Sardorning HEMIS logini (O'zgartirish uchun)", 
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        filled: true,
                        fillColor: Colors.grey[50],
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: channelCtl,
                      decoration: InputDecoration(
                        labelText: "Telegram kanal linki (ixtiyoriy)", 
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        filled: true,
                        fillColor: Colors.grey[50],
                      ),
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryBlue,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onPressed: isSaving ? null : () async {
                          setModalState(() => isSaving = true);
                          final data = <String, dynamic>{};
                          if (nameCtl.text.isNotEmpty) data['name'] = nameCtl.text;
                          if (leaderCtl.text.isNotEmpty) data['leader_login'] = leaderCtl.text;
                          if (channelCtl.text.isNotEmpty) data['channel_link'] = channelCtl.text;

                          final success = await _dataService.updateClub(club['id'], data);
                          setModalState(() => isSaving = false);
                          if (!context.mounted) return;
                          
                          if (success) {
                            Navigator.pop(context);
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text(AppDictionary.tr(context, 'msg_changes_saved')), backgroundColor: Colors.green));
                            _loadClubs();
                          } else {
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Xatolik yuz berdi. Sardor topilmagan bo'lishi mumkin."), backgroundColor: Colors.red));
                          }
                        },
                        child: isSaving ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Text("Saqlash", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            );
          }
        );
      }
    );
  }
}
