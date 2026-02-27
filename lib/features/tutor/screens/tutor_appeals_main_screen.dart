import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/core/constants/api_constants.dart';
import 'package:talabahamkor_mobile/features/tutor/screens/tutor_groups_screen.dart';
import 'package:talabahamkor_mobile/features/tutor/screens/tutor_appeal_chat_screen.dart';

class TutorAppealsMainScreen extends StatelessWidget {
  const TutorAppealsMainScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: AppTheme.backgroundWhite,
        appBar: AppBar(
          title: const Text(AppDictionary.tr(context, 'menu_appeals')),
          bottom: const TabBar(
            labelColor: AppTheme.primaryBlue,
            unselectedLabelColor: Colors.grey,
            indicatorColor: AppTheme.primaryBlue,
            tabs: [
              Tab(text: "Barcha murojaatlar"),
              Tab(text: "Guruhlar kesimida"),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            _AllAppealsTab(),
            TutorGroupsScreen(isAppealsMode: true, showAppBar: false),
          ],
        ),
      ),
    );
  }
}

class _AllAppealsTab extends StatefulWidget {
  const _AllAppealsTab();

  @override
  State<_AllAppealsTab> createState() => _AllAppealsTabState();
}

class _AllAppealsTabState extends State<_AllAppealsTab> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _appeals = [];
  String _currentFilter = "Barchasi"; // "Barchasi", "pending", "resolved"

  @override
  void initState() {
    super.initState();
    _loadAppeals();
  }

  Future<void> _loadAppeals() async {
    setState(() => _isLoading = true);
    String? statusParam;
    if (_currentFilter == "pending") statusParam = "pending";
    if (_currentFilter == "resolved") statusParam = "resolved";

    try {
      final appeals = await _dataService.getTutorAllAppeals(status: statusParam);
      if (mounted) {
        setState(() {
          _appeals = appeals;
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint("Error loading tutor appeals: $e");
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _onFilterChanged(String filter) {
    if (_currentFilter == filter) return;
    setState(() {
      _currentFilter = filter;
    });
    _loadAppeals();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Stats/Filter Header
        Container(
          padding: const EdgeInsets.all(16),
          color: Colors.white,
          child: Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: Colors.grey[200]!),
            ),
            child: Row(
              children: [
                Expanded(child: _buildSegmentButton("Barchasi", "Barchasi")),
                Expanded(child: _buildSegmentButton("Kutilmoqda", "pending")),
                Expanded(child: _buildSegmentButton("Hal qilingan", "resolved")),
              ],
            ),
          ),
        ),
        const Divider(height: 1),
        
        // List
        Expanded(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _appeals.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.mark_email_read_outlined, size: 80, color: Colors.grey[400]),
                          const SizedBox(height: 16),
                          Text("Murojaatlar topilmadi", style: TextStyle(color: Colors.grey[600], fontSize: 16)),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _loadAppeals,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _appeals.length,
                        itemBuilder: (context, index) {
                          return _buildAppealCard(_appeals[index]);
                        },
                      ),
                    ),
        ),
      ],
    );
  }

  Widget _buildSegmentButton(String label, String value) {
    final isSelected = _currentFilter == value;
    return GestureDetector(
      onTap: () => _onFilterChanged(value),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? Colors.white : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  )
                ]
              : [],
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? AppTheme.primaryBlue : Colors.grey[600],
              fontWeight: isSelected ? FontWeight.bold : FontWeight.w600,
              fontSize: 13,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ),
    );
  }

  Widget _buildAppealCard(dynamic appeal) {
    final isPending = appeal['status'] == 'pending';
    final isResolved = appeal['status'] == 'closed' || appeal['status'] == 'resolved';
    
    final studentName = appeal['student_name'] ?? "Noma'lum";
    final text = appeal['text'] ?? "";
    final date = _formatDate(appeal['created_at']);
    final fileId = appeal['file_id'];

    Color statusColor = isResolved ? Colors.green : (isPending ? Colors.orange : Colors.blue);
    String statusText = isResolved ? "Hal qilingan" : (isPending ? "Kutilmoqda" : "Javob berilgan");
    IconData statusIcon = isResolved ? Icons.check_circle_rounded : (isPending ? Icons.access_time_filled_rounded : Icons.mark_chat_read_rounded);

    return GestureDetector(
      onTap: () async {
        await Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => TutorAppealChatScreen(appealId: appeal['id'])),
        );
        _loadAppeals(); // Refresh after coming back
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
          border: Border.all(color: Colors.grey[100]!),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Avatar
                  CircleAvatar(
                    radius: 20,
                    backgroundColor: Colors.blue[50],
                    backgroundImage: appeal['student_image'] != null
                        ? NetworkImage(appeal['student_image'])
                        : null,
                    child: appeal['student_image'] == null
                        ? Text(studentName[0].toUpperCase(), style: TextStyle(color: Colors.blue[800], fontWeight: FontWeight.bold))
                        : null,
                  ),
                  const SizedBox(width: 12),
                  // Info
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          studentName,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          "${appeal['student_faculty']} • ${appeal['student_group']}",
                          style: TextStyle(color: Colors.grey[600], fontSize: 12),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  // Date
                  Text(date, style: TextStyle(color: Colors.grey[400], fontSize: 11)),
                ],
              ),
              const SizedBox(height: 12),
              
              // Text Content
              Text(
                text,
                style: const TextStyle(fontSize: 14, color: Colors.black87, height: 1.4),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),

              const SizedBox(height: 12),

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Attachment Indicator
                  if (fileId != null && fileId != "")
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.attachment_rounded, size: 14, color: Colors.grey[600]),
                          const SizedBox(width: 4),
                          Text("Fayl bor", style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                        ],
                      ),
                    )
                  else
                    const SizedBox.shrink(),

                  // Status Indicator
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Icon(statusIcon, size: 12, color: statusColor),
                        const SizedBox(width: 4),
                        Text(
                          statusText,
                          style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(String? iso) {
    if (iso == null) return "";
    try {
      final dt = DateTime.parse(iso).toLocal();
      final now = DateTime.now();
      if (dt.year == now.year && dt.month == now.month && dt.day == now.day) {
        return "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
      }
      return "${dt.day.toString().padLeft(2, '0')}.${dt.month.toString().padLeft(2, '0')}";
    } catch (_) {
      return "";
    }
  }
}
