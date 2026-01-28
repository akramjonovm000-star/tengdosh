import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class ClubsScreen extends StatefulWidget {
  const ClubsScreen({super.key});

  @override
  State<ClubsScreen> createState() => _ClubsScreenState();
}

class _ClubsScreenState extends State<ClubsScreen> {
  // Mock Data
  final List<Map<String, dynamic>> _clubs = [
    {
      "id": 1,
      "name": "Zakovat Klubi",
      "description": "Universitetning intellektual salohiyatini oshirish maqsadi. Har haftalik o'yinlar.",
      "members": 124,
      "color": Colors.indigo,
      "icon": Icons.psychology_rounded,
      "joined": true,
    },
    {
      "id": 2,
      "name": "Kiber Sport",
      "description": "CS:GO, Dota 2 va PUBG bo'yicha turnirlar. Universitet terma jamoasi.",
      "members": 85,
      "color": Colors.orange,
      "icon": Icons.sports_esports_rounded,
      "joined": false,
    },
    {
      "id": 3,
      "name": "IT Club",
      "description": "Dasturlash, dizayn va startap loyihalar. Hackathonlar tashkil qilish.",
      "members": 210,
      "color": Colors.blue,
      "icon": Icons.code_rounded,
      "joined": false,
    },
    {
      "id": 4,
      "name": "Volontyorlar",
      "description": "Xayriya va jamoat ishlari. Universitet tadbirlarida yordam.",
      "members": 156,
      "color": Colors.red,
      "icon": Icons.favorite_rounded,
      "joined": true,
    },
    {
      "id": 5,
      "name": "Ingliz tili (Speaking)",
      "description": "Har kuni Speaking club. IELTS imtihoniga tayyorgarlik.",
      "members": 98,
      "color": Colors.teal,
      "icon": Icons.language_rounded,
      "joined": false,
    },
  ];

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
      body: ListView.separated(
        padding: const EdgeInsets.all(20),
        itemCount: _clubs.length,
        separatorBuilder: (_, __) => const SizedBox(height: 16),
        itemBuilder: (context, index) {
          final club = _clubs[index];
          return _buildClubCard(club);
        },
      ),
    );
  }

  Widget _buildClubCard(Map<String, dynamic> club) {
    final bool isJoined = club['joined'];
    
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
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
                    color: (club['color'] as Color).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Icon(club['icon'] as IconData, color: club['color'] as Color, size: 30),
                ),
                const SizedBox(width: 16),
                
                // Info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        club['name'],
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "${club['members']} a'zo",
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
                      color: Colors.green.withOpacity(0.1),
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
                        color: (club['color'] as Color).withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(club['icon'] as IconData, color: club['color'] as Color, size: 40),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      club['name'],
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      "${club['members']} ta ishtirokchi",
                      style: TextStyle(color: Colors.grey[500], fontSize: 14),
                    ),
                    const SizedBox(height: 24),
                    const Align(
                      alignment: Alignment.centerLeft,
                      child: Text("Klub haqida", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      club['description'],
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
                child: club['joined']
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
            onPressed: () {
              Navigator.pop(context);
              setState(() {
                club['joined'] = true;
                club['members'] += 1;
              });
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text("Tabriklaymiz! Siz ${club['name']} a'zosi bo'ldingiz"),
                  backgroundColor: Colors.green,
                )
              );
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
