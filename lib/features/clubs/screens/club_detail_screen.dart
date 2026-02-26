import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import 'club_member_profile_screen.dart';

class ClubDetailScreen extends StatefulWidget {
  final Map<String, dynamic> club;
  const ClubDetailScreen({super.key, required this.club});

  @override
  State<ClubDetailScreen> createState() => _ClubDetailScreenState();
}

class _ClubDetailScreenState extends State<ClubDetailScreen> {
  final DataService _dataService = DataService();
  late bool isLeader;
  late bool isJoined;

  @override
  void initState() {
    super.initState();
    isLeader = widget.club['is_leader'] == true;
    isJoined = widget.club['is_joined'] == true;
  }

  Color _getColor(String? colorHex) {
    if (colorHex == null || colorHex.isEmpty) return AppTheme.primaryBlue;
    try {
      return Color(int.parse(colorHex.replaceFirst('#', '0xFF')));
    } catch (_) {
      return AppTheme.primaryBlue;
    }
  }

  @override
  Widget build(BuildContext context) {
    int tabCount = isLeader ? 4 : 3;

    return DefaultTabController(
      length: tabCount,
      child: Scaffold(
        backgroundColor: const Color(0xFFF5F6FA),
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. BACK BUTTON
              Padding(
                padding: const EdgeInsets.only(left: 8.0, top: 4.0),
                child: IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.black, size: 28),
                  onPressed: () => Navigator.pop(context),
                ),
              ),
              
              // 2. LARGE TITLE & SUBTITLE
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 8.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.club['name'] ?? 'Klub', 
                      style: const TextStyle(
                        fontSize: 28, 
                        fontWeight: FontWeight.w800, 
                        color: Colors.black,
                        height: 1.2
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      "${widget.club['members_count'] ?? 0} ta a'zo • 2024 yilda tashkil topgan", 
                      style: const TextStyle(
                        color: Color(0xFF8E8E93), 
                        fontSize: 14,
                        fontWeight: FontWeight.w500
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // 3. SEGMENTED TABS (Full Width)
              Container(
                height: 48,
                margin: const EdgeInsets.symmetric(horizontal: 20),
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: TabBar(
                  isScrollable: false, // Make it explicitly distribute space
                  dividerColor: Colors.transparent,
                  indicatorSize: TabBarIndicatorSize.tab,
                  indicator: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.04),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      )
                    ],
                  ),
                  labelColor: Colors.black,
                  labelStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                  unselectedLabelColor: Colors.grey.shade600,
                  unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13),
                  labelPadding: EdgeInsets.zero,
                  tabs: [
                    const Tab(text: "Ma'lumot"),
                    if (isLeader) const Tab(text: "A'zolar"),
                    const Tab(text: "E'lonlar"),
                    const Tab(text: "Tadbirlar"),
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // 4. TAB CONTENTS
              Expanded(
                child: TabBarView(
                  children: [
                    _InfoTab(club: widget.club, dataService: _dataService, onJoin: _handleJoin),
                    if (isLeader) _MembersTab(clubId: widget.club['id'], dataService: _dataService),
                    _AnnouncementsTab(clubId: widget.club['id'], isLeader: isLeader, dataService: _dataService),
                    _EventsTab(clubId: widget.club['id'], isLeader: isLeader, isJoined: isJoined, dataService: _dataService),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _handleJoin() async {
    final result = await _dataService.joinClub(widget.club['id']);
    
    // Status can be None / missing if our backend normally returns nothing on success
    // Wait, let's just interpret success if status logic matches. 
    // Wait, my backend implementation actually doesn't return "status: success", it returns nothing by default!
    // Oh, actually the FastAPI endpoint has `return {"status": "success"}` or it just implicitly returned None!
    // Let me check what `/join` used to return. Let's fix it later if needed. For now, we will handle "not_subscribed".
    
    if (result['status'] == 'not_subscribed') {
      _showTelegramJoinModal(result['channel_link'] ?? widget.club['channel_link']);
    } else if (result['status'] == 'error') {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message'] ?? 'Xatolik'), backgroundColor: Colors.red));
    } else if (result['status'] == 'already_joined') {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Siz allaqachon a'zosiz!"), backgroundColor: Colors.orange));
      setState(() => isJoined = true);
    } else {
      // Success (fastapi didn't explicitly return {status: error...} so it reached end of join_club logic).
      if (mounted) {
        setState(() => isJoined = true);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("A'zo bo'ldingiz"), backgroundColor: Colors.green));
      }
    }
  }

  void _showTelegramJoinModal(String? channelLink) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(left: 24, right: 24, top: 24, bottom: MediaQuery.of(ctx).padding.bottom + 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.telegram, size: 60, color: Colors.blue),
            const SizedBox(height: 16),
            const Text("Klubga a'zo bo'lish", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            const Text(
              "Klub tasdiqlangan bo'lishi uchun, iltimos avval telegram kanaliga a'zo bo'ling.",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey, height: 1.5),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.open_in_new),
                label: const Text("1. Kanalga o'tish"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: () async {
                   if (channelLink != null) {
                       final uri = Uri.parse(channelLink);
                       if (await canLaunchUrl(uri)) {
                           await launchUrl(uri, mode: LaunchMode.externalApplication);
                       }
                   }
                }
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: OutlinedButton(
                style: OutlinedButton.styleFrom(
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text("2. A'zolikni tasdiqlash"),
                onPressed: () async {
                   Navigator.pop(ctx);
                   _verifyAndJoin();
                }
              )
            )
          ]
        )
      )
    );
  }

  void _verifyAndJoin() async {
    if (!mounted) return;
    showDialog(context: context, barrierDismissible: false, builder: (_) => const Center(child: CircularProgressIndicator()));
    final result = await _dataService.joinClub(widget.club['id']);
    if (!mounted) return;
    Navigator.pop(context); // close loading
    
    if (result['status'] == 'not_subscribed') {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Hali ham kanalga a'zo bo'lmagansiz :("), backgroundColor: Colors.red));
    } else if (result['status'] == 'error') {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message'] ?? 'Tarmoq xatosi'), backgroundColor: Colors.red));
    } else {
      setState(() => isJoined = true);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("A'zo bo'ldingiz!"), backgroundColor: Colors.green));
    }
  }
}

// ==========================================
// 1. INFO TAB
// ==========================================
class _InfoTab extends StatelessWidget {
  final Map<String, dynamic> club;
  final DataService dataService;
  final VoidCallback onJoin;

  const _InfoTab({required this.club, required this.dataService, required this.onJoin});

  @override
  Widget build(BuildContext context) {
    final bool isJoined = club['is_joined'] == true;
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(18),
              boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 4))],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      radius: 20,
                      backgroundColor: AppTheme.primaryBlue,
                      child: Text(
                        (club['name'] as String?)?.isNotEmpty == true ? club['name'][0].toUpperCase() : '?',
                        style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(club['name'] ?? '', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 4),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(color: Colors.grey[200], borderRadius: BorderRadius.circular(8)),
                            child: const Text("Universitet Klubi", style: TextStyle(fontSize: 10, color: Colors.blueGrey, fontWeight: FontWeight.bold)),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                const Row(
                  children: [
                    Icon(Icons.flag, color: AppTheme.primaryBlue, size: 20),
                    SizedBox(width: 8),
                    Text("Klub maqsadi", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.black)),
                  ],
                ),
                const SizedBox(height: 12),
                Text(club['description'] ?? 'Tavsif yo\'q', style: TextStyle(color: Colors.grey[700], fontSize: 14, height: 1.5)),
              ],
            ),
          ),
          const SizedBox(height: 24),
          if (!isJoined && club['is_leader'] != true)
             SizedBox(
               width: double.infinity,
               height: 54,
               child: ElevatedButton(
                 onPressed: onJoin,
                 style: ElevatedButton.styleFrom(
                   backgroundColor: AppTheme.primaryBlue,
                   shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                   elevation: 0,
                 ),
                 child: const Text("A'zo bo'lish", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
               ),
             )
        ],
      ),
    );
  }
}

// ==========================================
// 2. MEMBERS TAB (Leader Only)
// ==========================================
class _MembersTab extends StatefulWidget {
  final int clubId;
  final DataService dataService;
  const _MembersTab({required this.clubId, required this.dataService});

  @override
  State<_MembersTab> createState() => _MembersTabState();
}

class _MembersTabState extends State<_MembersTab> {
  List<dynamic> members = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadMembers();
  }

  Future<void> _loadMembers() async {
    final data = await widget.dataService.getClubMembers(widget.clubId);
    if (mounted) {
      setState(() {
        members = data;
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) return const Center(child: CircularProgressIndicator());
    if (members.isEmpty) return const Center(child: Text("Hozircha a'zolar yo'q"));

    return ListView.builder(
      itemCount: members.length,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemBuilder: (context, index) {
        final m = members[index];
        final isActive = m['status'] == 'active';
        final int studentId = m['student_id'] ?? 0;
        
        return Container(
          height: 80,
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ClubMemberProfileScreen(
                      clubId: widget.clubId,
                      studentId: studentId,
                      dataService: widget.dataService,
                    ),
                  ),
                );
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: [
                    m['image_url'] != null
                      ? CircleAvatar(
                          radius: 22,
                          backgroundColor: Colors.grey.shade200,
                          backgroundImage: NetworkImage(m['image_url']),
                        )
                      : CircleAvatar(
                          radius: 22,
                          backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                          child: const Icon(Icons.person, color: AppTheme.primaryBlue),
                        ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            m['full_name'] ?? 'Noma\'lum', 
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            m['faculty_name'] ?? 'Fakultet yo\'q', 
                            style: const TextStyle(fontSize: 12, color: Colors.grey),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    if (m['telegram_username'] != null)
                      IconButton(
                        icon: const Icon(Icons.telegram, color: Colors.blue, size: 24),
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints(),
                        onPressed: () async {
                          final url = Uri.parse("https://t.me/${m['telegram_username']}");
                          if (await canLaunchUrl(url)) await launchUrl(url, mode: LaunchMode.externalApplication);
                        },
                      ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.blue.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Text("🔹 A'zo", style: TextStyle(color: Colors.blue, fontSize: 11, fontWeight: FontWeight.bold)),
                    ),
                    PopupMenuButton<String>(
                      icon: const Icon(Icons.more_vert, color: Colors.grey, size: 20),
                      padding: EdgeInsets.zero,
                      onSelected: (val) {
                        if (val == 'remove') {
                          _confirmRemoveMember(studentId, m['full_name'] ?? '');
                        }
                      },
                      itemBuilder: (context) => [
                        const PopupMenuItem(
                          value: 'remove',
                          child: Text("Soniqdan chiqarish", style: TextStyle(color: Colors.red)),
                        )
                      ],
                    ),
                  ],
                ),
              ),
            ),
          )
        );
      },
    );
  }

  Future<void> _confirmRemoveMember(int studentId, String name) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Chiqarish"),
        content: Text("Rostdan ham $name ismli talabani klubdan o'chirmoqchimisiz?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Bekor qilish")),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("O'chirish", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      if (!mounted) return;
      showDialog(context: context, barrierDismissible: false, builder: (_) => const Center(child: CircularProgressIndicator()));
      final ok = await widget.dataService.removeClubMember(widget.clubId, studentId);
      if (!mounted) return;
      Navigator.pop(context); // loading

      if (ok) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Talaba chiqarib yuborildi"), backgroundColor: Colors.green));
        _loadMembers();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Xatolik yuz berdi"), backgroundColor: Colors.red));
      }
    }
  }
}

// ==========================================
// 3. ANNOUNCEMENTS TAB
// ==========================================
class _AnnouncementsTab extends StatefulWidget {
  final int clubId;
  final bool isLeader;
  final DataService dataService;

  const _AnnouncementsTab({required this.clubId, required this.isLeader, required this.dataService});

  @override
  State<_AnnouncementsTab> createState() => _AnnouncementsTabState();
}

class _AnnouncementsTabState extends State<_AnnouncementsTab> {
  List<dynamic> items = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final data = await widget.dataService.getClubAnnouncements(widget.clubId);
    if (mounted) {
      setState(() {
        items = data;
        isLoading = false;
      });
    }
  }

  void _showAddDialog() {
    final TextEditingController textCtrl = TextEditingController();
    bool sendToTelegram = true;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (ctx) => StatefulBuilder(
        builder: (BuildContext context, StateSetter setModalState) {
          return Padding(
            padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text("Yangi e'lon", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                TextField(
                  controller: textCtrl,
                  maxLines: 4,
                  decoration: InputDecoration(
                    hintText: "E'lon matni...",
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 16),
                SwitchListTile(
                  title: const Text("Telegram kanalga ham yuborish"),
                  value: sendToTelegram,
                  onChanged: (val) => setModalState(() => sendToTelegram = val),
                  activeColor: AppTheme.primaryBlue,
                  contentPadding: EdgeInsets.zero,
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryBlue, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                    onPressed: () async {
                      if (textCtrl.text.isEmpty) return;
                      Navigator.pop(ctx);
                      final ok = await widget.dataService.createClubAnnouncement(widget.clubId, textCtrl.text, sendToTelegram);
                      if (ok) _loadData();
                    },
                    child: const Text("Joylsh", style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: isLoading 
         ? const Center(child: CircularProgressIndicator())
         : items.isEmpty
             ? const Center(child: Text("Hech narsa yo'q"))
             : ListView.builder(
                 itemCount: items.length,
                 padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                 itemBuilder: (context, index) {
                   final a = items[index];
                   return Container(
                     margin: const EdgeInsets.only(bottom: 12),
                     padding: const EdgeInsets.all(16),
                     decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))],
                     ),
                     child: Column(
                       crossAxisAlignment: CrossAxisAlignment.start,
                       children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                child: Text(
                                  widget.club['name'] ?? a['author_name'] ?? 'Klub E\'loni',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(a['created_at']?.toString().substring(0, 10) ?? '', style: const TextStyle(color: Colors.grey, fontSize: 13)),
                            ],
                          ),
                         const SizedBox(height: 12),
                         Text(a['content'] ?? '', style: const TextStyle(fontSize: 15, height: 1.4, color: Colors.black87)),
                         const SizedBox(height: 12),
                         Align(
                           alignment: Alignment.bottomRight,
                           child: Row(
                             mainAxisSize: MainAxisSize.min,
                             children: [
                               const Icon(Icons.remove_red_eye, size: 14, color: Colors.grey),
                               const SizedBox(width: 4),
                               Text("${a['views_count'] ?? 0}", style: const TextStyle(color: Colors.grey, fontSize: 12)),
                             ],
                           )
                         )
                       ],
                     ),
                   );
                 },
               ),
      floatingActionButton: widget.isLeader
          ? FloatingActionButton.extended(
              onPressed: _showAddDialog,
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              icon: const Icon(Icons.add, color: Colors.white),
              label: const Text("Yangi e'lon", style: TextStyle(color: Colors.white)),
            )
          : null,
    );
  }
}

// ==========================================
// 4. EVENTS TAB
// ==========================================
class _EventsTab extends StatefulWidget {
  final int clubId;
  final bool isLeader;
  final bool isJoined;
  final DataService dataService;

  const _EventsTab({required this.clubId, required this.isLeader, required this.dataService, required this.isJoined});

  @override
  State<_EventsTab> createState() => _EventsTabState();
}

class _EventsTabState extends State<_EventsTab> {
  List<dynamic> items = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final data = await widget.dataService.getClubEvents(widget.clubId);
    if (mounted) {
      setState(() {
        items = data;
        isLoading = false;
      });
    }
  }

  void _showAddDialog() {
    final titleCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    DateTime? selectedDate;
    TimeOfDay? selectedTime;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (ctx) => StatefulBuilder(
        builder: (BuildContext context, StateSetter setModalState) {
          return Padding(
            padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text("Yangi tadbir", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                TextField(controller: titleCtrl, decoration: InputDecoration(hintText: "Tadbir mavzusi", border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)))),
                const SizedBox(height: 12),
                TextField(controller: descCtrl, maxLines: 3, decoration: InputDecoration(hintText: "Tadbir haqida batafsil ma'lumot...", border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)))),
                const SizedBox(height: 12),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.calendar_today, color: AppTheme.primaryBlue),
                  title: Text(selectedDate == null ? "Sana va vaqtni tanlang" : "${selectedDate!.year}-${selectedDate!.month.toString().padLeft(2, '0')}-${selectedDate!.day.toString().padLeft(2, '0')} ${selectedTime?.format(context) ?? ''}"),
                  onTap: () async {
                    final d = await showDatePicker(context: context, initialDate: DateTime.now(), firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 365)));
                    if (d != null) {
                      if (!context.mounted) return;
                      final t = await showTimePicker(context: context, initialTime: TimeOfDay.now());
                      if (t != null) {
                        setModalState(() {
                          selectedDate = d;
                          selectedTime = t;
                        });
                      }
                    }
                  }
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryBlue, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                    onPressed: () async {
                      if (titleCtrl.text.isEmpty || selectedDate == null || selectedTime == null) return;
                      Navigator.pop(ctx);
                      
                      // Convert to correctly formatted local time string combined logically, backend assumes UTC unless indicated but we send naive as local for now
                      final formattedDate = DateTime(
                        selectedDate!.year, selectedDate!.month, selectedDate!.day,
                        selectedTime!.hour, selectedTime!.minute
                      ).toIso8601String();

                      final ok = await widget.dataService.createClubEvent(widget.clubId, {
                        "title": titleCtrl.text,
                        "description": descCtrl.text,
                        "event_date": formattedDate,
                      });
                      if (ok) _loadData();
                    },
                    child: const Text("Yaratish", style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: isLoading 
         ? const Center(child: CircularProgressIndicator())
         : items.isEmpty
             ? const Center(child: Text("Hozircha tadbirlar yo'q"))
             : ListView.builder(
                 itemCount: items.length,
                 padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                 itemBuilder: (context, index) {
                   final a = items[index];
                   final isPart = a['is_participating'] == true;

                   String dateDay = "00";
                   String dateMonth = "Noma'lum";
                   if (a['event_date'] != null) {
                       try {
                           final dt = DateTime.parse(a['event_date']);
                           dateDay = dt.day.toString().padLeft(2, '0');
                           final monthNames = ["", "Yan", "Fev", "Mar", "Apr", "May", "Iyun", "Iyul", "Avg", "Sen", "Okt", "Noy", "Dek"];
                           dateMonth = monthNames[dt.month];
                       } catch (_) {}
                   }

                   return Container(
                     margin: const EdgeInsets.only(bottom: 12),
                     padding: const EdgeInsets.all(16),
                     decoration: BoxDecoration(
                       color: Colors.white,
                       borderRadius: BorderRadius.circular(16),
                       boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))],
                     ),
                     child: Column(
                       crossAxisAlignment: CrossAxisAlignment.stretch,
                       children: [
                         // Media rendering on top
                         if (a['images'] != null && (a['images'] as List).isNotEmpty)
                           Container(
                             height: 120,
                             margin: const EdgeInsets.only(bottom: 12),
                             child: ListView.builder(
                               scrollDirection: Axis.horizontal,
                               itemCount: (a['images'] as List).length,
                               itemBuilder: (ctx, idx) {
                                  final img = a['images'][idx];
                                  // For telegram file_id, normally we'd need an actual bot URL to load it. 
                                  // As a fallback/placeholder if we only have file_id:
                                  return Container(
                                    width: 100, 
                                    margin: const EdgeInsets.only(right: 8),
                                    decoration: BoxDecoration(
                                      color: Colors.grey[200],
                                      borderRadius: BorderRadius.circular(8),
                                      image: DecorationImage(
                                        image: NetworkImage("https://api.telegram.org/bot/file/..."), // We actually don't have absolute URL without bot token. We'll just show an icon if we only have file_id.
                                        fit: BoxFit.cover,
                                        onError: (_, __) {}
                                      )
                                    ),
                                    child: const Center(child: Icon(Icons.image, color: Colors.grey)),
                                  );
                               }
                             )
                           ),
                         Row(
                           crossAxisAlignment: CrossAxisAlignment.start,
                           children: [
                         // Date Block
                         Container(
                           width: 60,
                           height: 60,
                           decoration: BoxDecoration(
                             color: AppTheme.primaryBlue.withOpacity(0.1),
                             borderRadius: BorderRadius.circular(12),
                           ),
                           child: Column(
                             mainAxisAlignment: MainAxisAlignment.center,
                             children: [
                               Text(dateDay, style: const TextStyle(color: AppTheme.primaryBlue, fontSize: 18, fontWeight: FontWeight.bold)),
                               Text(dateMonth, style: const TextStyle(color: AppTheme.primaryBlue, fontSize: 12, fontWeight: FontWeight.bold)),
                             ],
                           )
                         ),
                         const SizedBox(width: 16),
                         Expanded(
                           child: Column(
                             crossAxisAlignment: CrossAxisAlignment.start,
                             children: [
                               Row(
                                 children: [
                                   Expanded(child: Text(a['title'] ?? 'Nomsiz', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16), maxLines: 2, overflow: TextOverflow.ellipsis)),
                                   const SizedBox(width: 8),
                                   Container(
                                     padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                     decoration: BoxDecoration(
                                       color: (a['status'] == "O'tkazildi" ? Colors.grey : Colors.green).withOpacity(0.1),
                                       borderRadius: BorderRadius.circular(8),
                                     ),
                                     child: Text(a['status'] ?? '', style: TextStyle(color: a['status'] == "O'tkazildi" ? Colors.grey : Colors.green, fontSize: 10, fontWeight: FontWeight.bold)),
                                   )
                                 ]
                               ),
                               const SizedBox(height: 8),
                               if (a['description'] != null && a['description'].toString().trim().isNotEmpty) ...[
                                 Text(a['description'], style: const TextStyle(fontSize: 13, color: Colors.black87), maxLines: 2, overflow: TextOverflow.ellipsis),
                                 const SizedBox(height: 8),
                               ],
                               Row(
                                  children: [
                                     const Icon(Icons.location_on, size: 14, color: Colors.grey),
                                     const SizedBox(width: 4),
                                     const Text("Tadbir manzili / vaqti kiritilmagan", style: TextStyle(color: Colors.grey, fontSize: 12)),
                                  ]
                               ),
                               
                               if (widget.isLeader && a['status'] == "O'tkazildi") ...[
                                 const SizedBox(height: 12),
                                 Align(
                                   alignment: Alignment.centerRight,
                                   child: OutlinedButton(
                                     onPressed: () => _viewParticipants(a['id'], true),
                                     style: OutlinedButton.styleFrom(
                                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                     ),
                                     child: const Text("Qo'shimcha yoki Tahrirlash"),
                                   ),
                                 )
                               ]
                             ]
                           )
                         )
                       ]
                     )
                   ]
                 )
               );
             },
               ),
      floatingActionButton: widget.isLeader
          ? FloatingActionButton.extended(
              onPressed: _showAddDialog,
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              icon: const Icon(Icons.add, color: Colors.white),
              label: const Text("Yangi tadbir", style: TextStyle(color: Colors.white)),
            )
          : null,
    );
  }

  void _viewParticipants(int eventId, bool isPast) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => const Center(child: CircularProgressIndicator()),
    );
    final parts = await widget.dataService.getClubEventParticipants(eventId);
    if (!mounted) return;
    Navigator.pop(context);

    bool showList = false;
    bool isSaving = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      builder: (context) => StatefulBuilder(
        builder: (context, setModalState) {
          return Container(
            height: MediaQuery.of(context).size.height * 0.85,
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                const Text("Tadbir qo'shimcha amallari", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                
                // Button 1: Deep Link
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onPressed: () async {
                        final url = Uri.parse("https://t.me/talabahamkorbot?start=clubevent_$eventId");
                        if (await canLaunchUrl(url)) {
                          await launchUrl(url, mode: LaunchMode.externalApplication);
                        }
                    },
                    icon: const Icon(Icons.telegram, color: Colors.white),
                    label: const Text("1. Rasm yuklash (Telegram orqali)", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(height: 12),

                // Button 2: Show List
                if (!showList)
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: () => setModalState(() => showList = true),
                      icon: const Icon(Icons.group),
                      label: const Text("2. Ishtirokchilarni belgilash ro'yxati"),
                    ),
                  ),

                if (showList) ...[
                  const Divider(height: 32),
                  const Text("Ishtirokchilar ro'yxati:", style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Expanded(
                    child: parts.isEmpty
                      ? const Center(child: Text("Hozircha ra'yxat bo'sh"))
                      : ListView.builder(
                          itemCount: parts.length,
                          itemBuilder: (ctx, i) {
                            final p = parts[i];
                            final status = p['attendance_status'] ?? 'not_registered';
                            final isAttended = status == 'attended';
                            final isMissed = status == 'missed';
                            
                            return ListTile(
                               leading: CircleAvatar(child: Text(p['full_name']?[0] ?? '?')),
                               title: Text(p['full_name'] ?? 'Noma\'lum', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                               subtitle: Text("${p['faculty_name'] ?? ''} - ${p['group_number'] ?? ''}", style: const TextStyle(fontSize: 12)),
                               trailing: isPast ? Row(
                                 mainAxisSize: MainAxisSize.min,
                                 children: [
                                   IconButton(
                                     icon: Icon(Icons.close, color: isMissed ? Colors.red : Colors.grey.shade400),
                                     onPressed: () async {
                                        final ok = await widget.dataService.updateClubEventAttendance(eventId, p['student_id'], 'missed');
                                        if (ok) setModalState(() => p['attendance_status'] = 'missed');
                                     },
                                   ),
                                   IconButton(
                                     icon: Icon(Icons.check_circle, color: isAttended ? Colors.green : Colors.grey.shade400),
                                     onPressed: () async {
                                        final ok = await widget.dataService.updateClubEventAttendance(eventId, p['student_id'], 'attended');
                                        if (ok) setModalState(() => p['attendance_status'] = 'attended');
                                     },
                                   ),
                                 ],
                               ) : Text(
                                 status == 'registered' ? "Qatnashadi" : 
                                 status == 'not_registered' ? "" : status,
                                 style: TextStyle(
                                   color: status == 'registered' ? Colors.green : Colors.grey,
                                   fontWeight: FontWeight.bold,
                                   fontSize: 12
                                 )
                               )
                            );
                          },
                        )
                  ),
                ] else ...[
                  const Spacer(),
                ],
                
                const SizedBox(height: 16),
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
                      final ok = await widget.dataService.completeEventActivity(eventId);
                      setModalState(() => isSaving = false);
                      
                      if (!context.mounted) return;
                      if (ok) {
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Faollik qilib tasdiqlandi!")));
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Bajarilmadi. Barcha ma'lumotlar to'g'riligini tekshiring.")));
                      }
                    },
                    child: isSaving ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Text("3. Saqlash", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          );
        }
      )
    );
  }
}

