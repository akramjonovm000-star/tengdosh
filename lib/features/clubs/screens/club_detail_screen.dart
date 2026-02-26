import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';

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
        backgroundColor: AppTheme.backgroundWhite,
        appBar: AppBar(
          title: Text(widget.club['name'] ?? 'Klub', style: const TextStyle(color: Colors.black, fontSize: 18, fontWeight: FontWeight.bold)),
          backgroundColor: Colors.white,
          elevation: 0,
          iconTheme: const IconThemeData(color: Colors.black),
          bottom: TabBar(
            isScrollable: true,
            labelColor: AppTheme.primaryBlue,
            unselectedLabelColor: Colors.grey,
            indicatorColor: AppTheme.primaryBlue,
            indicatorWeight: 3,
            tabs: [
              const Tab(text: "Ma'lumot"),
              if (isLeader) const Tab(text: "A'zolar"),
              const Tab(text: "E'lonlar"),
              const Tab(text: "Tadbirlar"),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _InfoTab(club: widget.club, dataService: _dataService, onJoin: _handleJoin),
            if (isLeader) _MembersTab(clubId: widget.club['id'], dataService: _dataService),
            _AnnouncementsTab(clubId: widget.club['id'], isLeader: isLeader, dataService: _dataService),
            _EventsTab(clubId: widget.club['id'], isLeader: isLeader, isJoined: isJoined, dataService: _dataService),
          ],
        ),
      ),
    );
  }

  void _handleJoin() async {
    final success = await _dataService.joinClub(widget.club['id']);
    if (success) {
      if (mounted) {
        setState(() => isJoined = true);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("A'zo bo'ldingiz"), backgroundColor: Colors.green));
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Xatolik"), backgroundColor: Colors.red));
      }
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
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Text(club['name'] ?? '', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
          ),
          const SizedBox(height: 8),
          Center(
            child: Text("${club['members_count'] ?? 0} ta ishtirokchi", style: TextStyle(color: Colors.grey[500], fontSize: 14)),
          ),
          const SizedBox(height: 24),
          const Text("Klub haqida", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          Text(club['description'] ?? 'Tavsif yo\'q', style: TextStyle(color: Colors.grey[700], fontSize: 15, height: 1.5)),
          const SizedBox(height: 30),
          if (!isJoined && club['is_leader'] != true)
             SizedBox(
               width: double.infinity,
               height: 50,
               child: ElevatedButton(
                 onPressed: onJoin,
                 style: ElevatedButton.styleFrom(
                   backgroundColor: AppTheme.primaryBlue,
                   shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                 ),
                 child: const Text("A'zo bo'lish", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
      padding: const EdgeInsets.all(16),
      itemBuilder: (context, index) {
        final m = members[index];
        final isActive = m['status'] == 'active';
        return Card(
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.grey[200]!)),
          child: ListTile(
            title: Text(m['full_name'] ?? 'Noma\'lum', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text("${m['faculty_name'] ?? ''} - ${m['group_number'] ?? ''}", style: const TextStyle(fontSize: 12)),
                if (m['telegram_username'] != null)
                   Text("@${m['telegram_username']}", style: const TextStyle(fontSize: 12, color: AppTheme.primaryBlue)),
              ],
            ),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: isActive ? Colors.green.withValues(alpha: 0.1) : Colors.red.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(isActive ? "Active" : "Kanalda emas", style: TextStyle(color: isActive ? Colors.green : Colors.red, fontSize: 10, fontWeight: FontWeight.bold)),
            ),
          ),
        );
      },
    );
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
                 padding: const EdgeInsets.all(16),
                 itemBuilder: (context, index) {
                   final a = items[index];
                   return Card(
                     elevation: 0,
                     margin: const EdgeInsets.only(bottom: 12),
                     shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.grey[200]!)),
                     child: Padding(
                       padding: const EdgeInsets.all(16),
                       child: Column(
                         crossAxisAlignment: CrossAxisAlignment.start,
                         children: [
                           Row(
                             mainAxisAlignment: MainAxisAlignment.spaceBetween,
                             children: [
                               Text(a['author_name'] ?? 'Sardor', style: const TextStyle(fontWeight: FontWeight.bold)),
                               Text(a['created_at']?.toString().substring(0, 10) ?? '', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                             ],
                           ),
                           const SizedBox(height: 8),
                           Text(a['content'] ?? '', style: const TextStyle(height: 1.4)),
                           const SizedBox(height: 8),
                           Row(
                             mainAxisAlignment: MainAxisAlignment.end,
                             children: [
                               const Icon(Icons.remove_red_eye, size: 14, color: Colors.grey),
                               const SizedBox(width: 4),
                               Text("${a['views_count'] ?? 0}", style: const TextStyle(color: Colors.grey, fontSize: 12)),
                             ],
                           )
                         ],
                       ),
                     ),
                   );
                 },
               ),
      floatingActionButton: widget.isLeader
          ? FloatingActionButton.extended(
              onPressed: _showAddDialog,
              backgroundColor: AppTheme.primaryBlue,
              icon: const Icon(Icons.add),
              label: const Text("Yangi e'lon"),
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
    final dateCtrl = TextEditingController(); // Simple format logic for mock

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text("Yangi tadbir", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            TextField(controller: titleCtrl, decoration: InputDecoration(hintText: "Tadbir nomi", border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)))),
            const SizedBox(height: 12),
            TextField(controller: dateCtrl, decoration: InputDecoration(hintText: "Sana (2024-05-01T10:00:00Z)", border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)))),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryBlue, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                onPressed: () async {
                  if (titleCtrl.text.isEmpty || dateCtrl.text.isEmpty) return;
                  Navigator.pop(ctx);
                  final ok = await widget.dataService.createClubEvent(widget.clubId, {
                    "title": titleCtrl.text,
                    "event_date": dateCtrl.text,
                  });
                  if (ok) _loadData();
                },
                child: const Text("Yaratish", style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
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
                 padding: const EdgeInsets.all(16),
                 itemBuilder: (context, index) {
                   final a = items[index];
                   final isPart = a['is_participating'] == true;
                   return Card(
                     elevation: 0,
                     margin: const EdgeInsets.only(bottom: 12),
                     shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.grey[200]!)),
                     child: Padding(
                       padding: const EdgeInsets.all(16),
                       child: Column(
                         crossAxisAlignment: CrossAxisAlignment.start,
                         children: [
                           Text(a['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                           const SizedBox(height: 8),
                           Row(
                             children: [
                               const Icon(Icons.calendar_today, size: 14, color: Colors.grey),
                               const SizedBox(width: 4),
                               Text(a['event_date']?.toString().substring(0, 10) ?? '', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                             ],
                           ),
                           const SizedBox(height: 16),
                           Row(
                             mainAxisAlignment: MainAxisAlignment.spaceBetween,
                             children: [
                               Text("${a['participants_count'] ?? 0} ishtirokchi", style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold)),
                               if (widget.isJoined && !widget.isLeader)
                                 ElevatedButton(
                                   onPressed: () async {
                                      final b = await widget.dataService.participateInClubEvent(a['id']);
                                      if (b) _loadData();
                                   },
                                   style: ElevatedButton.styleFrom(
                                     backgroundColor: isPart ? Colors.red : AppTheme.primaryBlue,
                                     shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                   ),
                                   child: Text(isPart ? "Bekor qilish" : "Qatnashaman"),
                                 )
                               else if (widget.isLeader)
                                 OutlinedButton(
                                   onPressed: () => _viewParticipants(a['id']),
                                   child: const Text("Ishtirokchilar"),
                                 )
                             ],
                           )
                         ],
                       ),
                     ),
                   );
                 },
               ),
      floatingActionButton: widget.isLeader
          ? FloatingActionButton.extended(
              onPressed: _showAddDialog,
              backgroundColor: AppTheme.primaryBlue,
              icon: const Icon(Icons.add, color: Colors.white),
              label: const Text("Yangi tadbir", style: TextStyle(color: Colors.white)),
            )
          : null,
    );
  }

  void _viewParticipants(int eventId) async {
    showDialog(
      context: context,
      builder: (ctx) => const Center(child: CircularProgressIndicator()),
    );
    final parts = await widget.dataService.getClubEventParticipants(eventId);
    if (!mounted) return;
    Navigator.pop(context);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.7,
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Text("Tadbir ishtirokchilari", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            Expanded(
              child: parts.isEmpty
                ? const Center(child: Text("Hech kim ro'yxatdan o'tmagan"))
                : ListView.builder(
                    itemCount: parts.length,
                    itemBuilder: (ctx, i) {
                      final p = parts[i];
                      return ListTile(
                         leading: CircleAvatar(child: Text(p['full_name']?[0] ?? '?')),
                         title: Text(p['full_name'] ?? 'Nomlum'),
                         subtitle: Text("${p['faculty_name'] ?? ''} - ${p['group_number'] ?? ''}"),
                         trailing: Text(p['attendance_status'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                      );
                    },
                  )
            )
          ],
        ),
      )
    );
  }
}

