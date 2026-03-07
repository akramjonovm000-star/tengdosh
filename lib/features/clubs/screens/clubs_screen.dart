import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import '../../../../core/providers/auth_provider.dart';
import 'club_detail_screen.dart';
import 'club_create_screen.dart';
import 'package:talabahamkor_mobile/core/localization/app_dictionary.dart';

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
          SnackBar(content: Text(AppDictionary.tr(context, 'msg_clubs_load_error'))),
        );
      }
    }
  }

  IconData _getIconData(String? iconName, String clubName) {
    if (iconName != null && iconName != 'groups_rounded' && iconName.isNotEmpty && iconName != 'psychology') {
      // You can add more mapping here if needed in the future
      // return Icons.groups_rounded;
    }
    
    final lowerName = clubName.toLowerCase();
    
    // Books & Reading
    if (lowerName.contains('book') || lowerName.contains('kitob') || lowerName.contains('mutolaa') || lowerName.contains('read') || lowerName.contains('kutubxona')) return Icons.menu_book;
    
    // Language & International
    if (lowerName.contains('language') || lowerName.contains('til') || lowerName.contains('english') || lowerName.contains('xorijiy') || lowerName.contains('international')) return Icons.language;
    
    // Art, Painting, Creativity, Vision
    if (lowerName.contains('art') || lowerName.contains("san'at") || lowerName.contains('vision') || lowerName.contains('rassom') || lowerName.contains('dizayn') || lowerName.contains('creative')) return Icons.palette;
    
    // Career, Business, Academy
    if (lowerName.contains('karyera') || lowerName.contains('career') || lowerName.contains('academy') || lowerName.contains('pragmatic') || lowerName.contains('biznes') || lowerName.contains('business') || lowerName.contains('tadbirkor') || lowerName.contains('maktabi') || lowerName.contains('lider')) return Icons.business_center;
    
    // E-sports & Gaming
    if (lowerName.contains('esport') || lowerName.contains('cyber') || lowerName.contains('kiber') || lowerName.contains('cybersport')) return Icons.sports_esports;
    
    // Specific Sports
    if (lowerName.contains('shaxmat') || lowerName.contains('chess') || lowerName.contains('shashka')) return Icons.extension;
    if (lowerName.contains('tennis') || lowerName.contains('badminton') || lowerName.contains('stol')) return Icons.sports_tennis;
    if (lowerName.contains('sport') || lowerName.contains('futbol') || lowerName.contains('football') || lowerName.contains('volleyball') || lowerName.contains('voleybol')) return Icons.sports_soccer;
    
    // Theater, Comedy, Shows
    if (lowerName.contains('teatr') || lowerName.contains('theater') || lowerName.contains('drama') || lowerName.contains('shou') || lowerName.contains('show') || lowerName.contains('quvnoq')) return Icons.theater_comedy;
    
    // Music & Dance
    if (lowerName.contains('dance') || lowerName.contains('raqs') || lowerName.contains('music') || lowerName.contains('musiqa')) return Icons.music_note;
    
    // Media, Photography, Video, Journalism, Radio
    if (lowerName.contains('radio') || lowerName.contains('mic') || lowerName.contains('ovoz')) return Icons.mic;
    if (lowerName.contains('photo') || lowerName.contains('kamera') || lowerName.contains('kino') || lowerName.contains('video')) return Icons.camera_alt;
    if (lowerName.contains('media') || lowerName.contains('jurnalistika') || lowerName.contains('pressa')) return Icons.article;
    
    // IT, Tech, Code
    if (lowerName.contains('dastur') || lowerName.contains('it') || lowerName.contains('kompyuter') || lowerName.contains('computer') || lowerName.contains('code') || lowerName.contains('tech')) return Icons.computer;
    
    // Science, Debate, Intellect
    if (lowerName.contains('fan') || lowerName.contains('olim') || lowerName.contains('ilmiy') || lowerName.contains('science') || lowerName.contains('zakovat') || lowerName.contains('debate') || lowerName.contains('munozara')) return Icons.science;

    // Eco, Nature
    if (lowerName.contains('eco') || lowerName.contains('eko') || lowerName.contains('tabiat') || lowerName.contains('hayot')) return Icons.eco;
    
    // Girls, Ladies
    if (lowerName.contains('qizlar') || lowerName.contains('ayollar') || lowerName.contains('ladies') || lowerName.contains('women')) return Icons.face_3;
    
    // Default missing
    return Icons.groups_rounded;
  }

  Color _getColor(String? colorHex, String clubName) {
    if (colorHex == null || colorHex.isEmpty || colorHex.toUpperCase() == '#4A90E2') {
      final colors = [
        Colors.blue, Colors.red, Colors.green, Colors.orange,
        Colors.purple, Colors.teal, Colors.pink, Colors.indigo,
        Colors.amber, Colors.cyan, Colors.deepOrange, Colors.brown
      ];
      int hash = 0;
      for (int i = 0; i < clubName.length; i++) {
         hash = clubName.codeUnitAt(i) + ((hash << 5) - hash);
      }
      return colors[hash.abs() % colors.length];
    }
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
              label: Text(AppDictionary.tr(context, 'btn_add_club'), style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
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
    final String clubName = club['name'] ?? 'Klub';
    final Color clubColor = _getColor(club['color'], clubName);
    final IconData clubIcon = _getIconData(club['icon'], clubName);
    
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
                      Text(
                        club['name'] ?? 'Klub nomi',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (club['department'] != null && club['department'].toString().trim().isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          club['department'],
                          style: TextStyle(color: Colors.blueGrey[400], fontSize: 13, fontWeight: FontWeight.w500),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Text(
                            "${club['members_count'] ?? 0} a'zo",
                            style: TextStyle(color: Colors.grey[500], fontSize: 12),
                          ),
                          if (club['is_primary_leader'] == true) ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text(
                                "👑 Sardor",
                                style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold, fontSize: 11),
                              ),
                            )
                          ] else if (club['is_leader'] == true) ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.purple.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text(
                                "🛡 Boshqaruvchi",
                                style: TextStyle(color: Colors.purple, fontWeight: FontWeight.bold, fontSize: 11),
                              ),
                            )
                          ] else if (isJoined) ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.green.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text(
                                "A'zosiz",
                                style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 11),
                              ),
                            )
                          ]
                        ],
                      ),
                    ],
                  ),
                ),

                const SizedBox(width: 8),
                if (!Provider.of<AuthProvider>(context, listen: false).isYetakchi)
                  const Icon(Icons.arrow_forward_ios_rounded, color: Colors.grey, size: 16),
                  
                if (Provider.of<AuthProvider>(context, listen: false).isYetakchi) ...[
                   const SizedBox(width: 8),
                   Builder(builder: (menuCtx) {
                     final editStr = AppDictionary.tr(context, 'btn_edit');
                     return PopupMenuButton<String>(

                     icon: const Icon(Icons.more_vert, color: Colors.grey),
                     onSelected: (val) {
                       if (val == 'edit') {
                         _showEditClubSheet(club);
                       } else if (val == 'delete') {
                         _showDeleteConfirmation(club);
                       }
                     },
                     itemBuilder: (ctx) => [
                       PopupMenuItem(
                         value: 'edit',
                         child: Row(
                           children: [
                             Icon(Icons.edit, size: 20, color: Colors.blue),
                             SizedBox(width: 8),
                             Text(editStr),
                           ],
                         ),
                       ),
                       const PopupMenuItem(
                         value: 'delete',
                         child: Row(
                           children: [
                             Icon(Icons.delete, size: 20, color: Colors.red),
                             SizedBox(width: 8),
                             Text("O'chirish", style: TextStyle(color: Colors.red)),
                           ],
                         ),
                       ),
                     ],
                   );
                 }),
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
    final TextEditingController descCtl = TextEditingController(text: club['description'] ?? '');
    final TextEditingController leaderCtl = TextEditingController(text: club['leader_login'] ?? ''); // Not all clubs return leader_login but they might
    
    String initialChannel = club['channel_link'] ?? '';
    if (initialChannel.startsWith('https://t.me/')) {
        initialChannel = initialChannel.substring('https://t.me/'.length);
    } else if (initialChannel.startsWith('http://t.me/')) {
        initialChannel = initialChannel.substring('http://t.me/'.length);
    } else if (initialChannel.startsWith('t.me/')) {
        initialChannel = initialChannel.substring('t.me/'.length);
    } else if (initialChannel.startsWith('@')) {
        initialChannel = initialChannel.substring(1);
    }
    final TextEditingController channelCtl = TextEditingController(text: initialChannel);

    final editClubTitle = AppDictionary.tr(context, 'btn_edit_club');
    final clubNameLabel = AppDictionary.tr(context, 'lbl_club_name');
    final successMsg = AppDictionary.tr(context, 'msg_changes_saved');

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
                    Text(editClubTitle, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 16),
                    TextField(
                      controller: nameCtl,
                      decoration: InputDecoration(
                        labelText: clubNameLabel, 
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        filled: true,
                        fillColor: Colors.grey[50],
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: descCtl,
                      maxLines: 3,
                      decoration: InputDecoration(
                        labelText: "Klub tavsifi", 
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
                        labelText: "Telegram kanal linki yoki username", 
                        prefixText: 'https://t.me/',
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
                          if (descCtl.text.isNotEmpty) data['description'] = descCtl.text;
                          if (leaderCtl.text.isNotEmpty) data['leader_login'] = leaderCtl.text;
                          if (channelCtl.text.isNotEmpty) {
                            String chLink = channelCtl.text.trim();
                            if (chLink.startsWith('https://t.me/')) chLink = chLink.substring('https://t.me/'.length);
                            else if (chLink.startsWith('http://t.me/')) chLink = chLink.substring('http://t.me/'.length);
                            else if (chLink.startsWith('t.me/')) chLink = chLink.substring('t.me/'.length);
                            else if (chLink.startsWith('@')) chLink = chLink.substring(1);
                            
                            data['channel_link'] = 'https://t.me/$chLink';
                          }

                          final success = await _dataService.updateClub(club['id'], data);
                          setModalState(() => isSaving = false);
                          if (!context.mounted) return;
                          
                          if (success) {
                            Navigator.pop(context);
                            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(successMsg), backgroundColor: Colors.green));
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

  void _showDeleteConfirmation(Map<String, dynamic> club) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Klubni o'chirish"),
        content: Text("${club['name'] ?? 'Klub'}ni o'chirishni xohlaysizmi? Bu amalni ortga qaytarib bo'lmaydi."),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Bekor qilish", style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () async {
              Navigator.pop(ctx); // close dialog
              setState(() => _isLoading = true);
              final success = await _dataService.deleteClub(club['id']);
              if (!mounted) return;
              if (success) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Klub muvaffaqiyatli o'chirildi"), backgroundColor: Colors.green),
                );
                _loadClubs();
              } else {
                setState(() => _isLoading = false);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Xatolik yuz berdi"), backgroundColor: Colors.red),
                );
              }
            },
            child: const Text("O'chirish", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
