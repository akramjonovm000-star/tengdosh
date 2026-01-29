import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_theme.dart';
import '../services/appeal_service.dart';
import '../models/appeal_model.dart';

class AppealsScreen extends StatefulWidget {
  const AppealsScreen({super.key});

  @override
  State<AppealsScreen> createState() => _AppealsScreenState();
}

class _AppealsScreenState extends State<AppealsScreen> with SingleTickerProviderStateMixin {
  final AppealService _appealService = AppealService();
  List<Appeal> _appeals = [];
  bool _isLoading = true;

  String _selectedCategory = "Barchasi";
  String _selectedStatus = "Barchasi";

  final List<String> _categories = ["Barchasi", "Rahbariyat", "Dekanat", "Tyutor", "Psixolog", "Buxgalteriya", "Boshqa"];
  final List<String> _statuses = ["Barchasi", "Javob berilgan", "Kutilmoqda", "Yopilgan"];

  @override
  void initState() {
    super.initState();
    _loadAppeals();
  }

  Future<void> _loadAppeals() async {
    setState(() => _isLoading = true);
    final appeals = await _appealService.getMyAppeals();
    if (mounted) {
      setState(() {
        _appeals = appeals;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Murojaatlar", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAppeals,
          )
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading 
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                      onRefresh: _loadAppeals,
                      child: CustomScrollView( // Using CustomScrollView to allow scrolling of the whole page if needed, or just Column inside generic ScrollView
                        slivers: [
                            SliverToBoxAdapter(
                                child: Padding(
                                    padding: const EdgeInsets.only(bottom: 16),
                                    child: _buildStatsHeader(),
                                ),
                            ),
                            SliverToBoxAdapter(
                                child: Padding(
                                    padding: const EdgeInsets.only(bottom: 16),
                                    child: _buildFilterBar(),
                                ),
                            ),
                            _getFilteredAppeals().isEmpty 
                            ? SliverFillRemaining(child: _buildEmptyState())
                            : SliverPadding(
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                sliver: SliverList(
                                    delegate: SliverChildBuilderDelegate(
                                        (context, index) {
                                            return AppealCard(
                                                appeal: _getFilteredAppeals()[index],
                                                onTap: () => _showAppealDetails(_getFilteredAppeals()[index].id),
                                            );
                                        },
                                        childCount: _getFilteredAppeals().length,
                                    ),
                                ),
                            ),
                        ],
                      ),
                  ),
          ),
          _buildBottomButton(),
        ],
      ),
    );
  }

  Widget _buildStatsHeader() {
    int answered = 0;
    int pending = 0;
    int closed = 0;

    for (var a in _getFilteredAppeals(ignoreStatus: true)) { // Filter by status should affect list, but header usually shows totals for current category
      // Logic: Stats usually show totals for the selected CATEGORY, but ignoring the STATUS filter itself (so you can see distribution)
      
      if (a.status == 'answered') answered++;
      else if (a.status == 'pending') pending++;
      else if (a.status == 'closed') closed++;
    }

    final stats = [
      {"label": "Javob berilgan", "count": answered, "color": Colors.green},
      {"label": "Kutilmoqda", "count": pending, "color": Colors.orange},
      {"label": "Yopilgan", "count": closed, "color": Colors.red}, // Using Red for Closed to match "Rejected" style
    ];

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: stats.map((item) {
          final isSelected = _selectedStatus == item['label'];
          final color = item['color'] as Color;
          
          return Expanded(
            child: GestureDetector(
              onTap: () {
                setState(() {
                  if (_selectedStatus == item['label']) {
                    _selectedStatus = "Barchasi";
                  } else {
                    _selectedStatus = item['label'] as String;
                  }
                });
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                margin: const EdgeInsets.symmetric(horizontal: 4),
                padding: const EdgeInsets.symmetric(vertical: 16),
                decoration: BoxDecoration(
                  color: isSelected ? color.withOpacity(0.1) : Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isSelected ? color : Colors.transparent,
                    width: 2
                  ),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4))
                  ],
                ),
                child: Column(
                  children: [
                    Text(
                      "${item['count']}", 
                      style: TextStyle(
                        fontSize: 22, 
                        fontWeight: FontWeight.bold, 
                        color: color
                      )
                    ),
                    const SizedBox(height: 4),
                    Text(
                      item['label'] as String, 
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 11, 
                        fontWeight: FontWeight.w600, 
                        color: Colors.grey[600]
                      )
                    ),
                  ],
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildFilterBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Expanded(
            child: _buildFilterButton(
              label: _selectedCategory == "Barchasi" ? "Kategoriya" : _selectedCategory,
              isSelected: _selectedCategory != "Barchasi",
              icon: Icons.category_outlined,
              onTap: () => _showFilterSheet(
                title: "Kategoriyani tanlang",
                options: _categories,
                selected: _selectedCategory,
                onSelect: (val) => setState(() => _selectedCategory = val),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _buildFilterButton(
              label: _selectedStatus == "Barchasi" ? "Status" : _selectedStatus,
              isSelected: _selectedStatus != "Barchasi",
              icon: Icons.filter_list_rounded,
              onTap: () => _showFilterSheet(
                title: "Statusni tanlang",
                options: _statuses,
                selected: _selectedStatus,
                onSelect: (val) => setState(() => _selectedStatus = val),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterButton({
    required String label, 
    required bool isSelected, 
    required IconData icon, 
    required VoidCallback onTap
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryBlue.withOpacity(0.1) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: isSelected ? AppTheme.primaryBlue : Colors.grey[300]!),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 18, color: isSelected ? AppTheme.primaryBlue : Colors.grey[600]),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: isSelected ? AppTheme.primaryBlue : Colors.grey[700],
              ),
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(width: 4),
            Icon(Icons.keyboard_arrow_down_rounded, size: 18, color: isSelected ? AppTheme.primaryBlue : Colors.grey[500]),
          ],
        ),
      ),
    );
  }

  void _showFilterSheet({
    required String title,
    required List<String> options,
    required String selected,
    required Function(String) onSelect,
  }) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            Divider(height: 1, color: Colors.grey[200]),
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: options.length,
                itemBuilder: (context, index) {
                  final option = options[index];
                  final isSel = option == selected;
                  return ListTile(
                    onTap: () {
                      onSelect(option);
                      Navigator.pop(context);
                    },
                    title: Text(option, style: TextStyle(
                      fontWeight: isSel ? FontWeight.bold : FontWeight.normal,
                      color: isSel ? AppTheme.primaryBlue : Colors.black87,
                    )),
                    trailing: isSel ? const Icon(Icons.check_rounded, color: AppTheme.primaryBlue) : null,
                  );
                },
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  List<Appeal> _getFilteredAppeals({bool ignoreStatus = false}) {
    return _appeals.where((a) {
      // Filter by Category (Recipient)
      if (_selectedCategory != "Barchasi") {
         String role = a.assignedRole?.toLowerCase() ?? "";
         if (role != _selectedCategory.toLowerCase()) {
            return false;
         }
      }
      
      // Filter by Status
      if (!ignoreStatus && _selectedStatus != "Barchasi") {
        if (_selectedStatus == "Javob berilgan") {
            if (a.status != "answered") return false;
        } else if (_selectedStatus == "Kutilmoqda") {
            if (a.status != "pending") return false;
        } else if (_selectedStatus == "Yopilgan") {
            if (a.status != "closed") return false;
        }
      }
      return true;
    }).toList();
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search_off_rounded, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            "Murojaatlar topilmadi",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey[700]),
          ),
          const SizedBox(height: 8),
          Text(
            "Filterlarni o'zgartirib ko'ring yoki\nyangi murojaat yuboring",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomButton() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 20,
            offset: const Offset(0, -5),
          )
        ],
      ),
      child: SafeArea(
        child: SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: _showCreateAppealSheet,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 0,
            ),
            child: const Text(
              "Murojaat yuborish", // Custom text
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ),
        ),
      ),
    );
  }

  void _showCreateAppealSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => CreateAppealSheet(onAppealCreated: _loadAppeals),
    );
  }

  void _showAppealDetails(int appealId) {
    Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => AppealDetailScreen(appealId: appealId))
    );
  }
}

class AppealCard extends StatelessWidget {
  final Appeal appeal;
  final VoidCallback onTap;

  const AppealCard({super.key, required this.appeal, required this.onTap});

  @override
  Widget build(BuildContext context) {
    Color statusColor;
    String statusText;
    IconData statusIcon;

    switch (appeal.status) {
      case 'answered':
        statusColor = Colors.green;
        statusText = "Javob berilgan";
        statusIcon = Icons.check_circle_rounded;
        break;
      case 'closed':
        statusColor = Colors.red;
        statusText = "Yopilgan";
        statusIcon = Icons.lock_outline_rounded;
        break;
      case 'pending':
      default:
        statusColor = Colors.orange;
        statusText = "Kutilmoqda";
        statusIcon = Icons.access_time_rounded;
        break;
    }

    String recipientDisplay = appeal.assignedRole != null 
        ? appeal.assignedRole![0].toUpperCase() + appeal.assignedRole!.substring(1) 
        : "Rahbariyat";

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.06), 
              blurRadius: 15, 
              offset: const Offset(0, 8),
              spreadRadius: -4,
            )
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          children: [
            // Image Area (Placeholder for Appeal - sticking to UI request)
            Stack(
              children: [
                Container(
                  height: 180, // Slightly smaller than activity
                  width: double.infinity,
                  color: Colors.grey[100],
                  child: Center(
                      child: Icon(
                          _getIconForRole(appeal.assignedRole), 
                          size: 60, 
                          color: Colors.grey[300]
                      )
                  ),
                ),
                // Recipient Label
                Positioned(
                  top: 12,
                  left: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.95),
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 4)]
                    ),
                    child: Text(
                      recipientDisplay,
                      style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold, fontSize: 12)
                    ),
                  ),
                ),
                // Anonymity Tag
                if (appeal.isAnonymous)
                Positioned(
                  top: 12,
                  right: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.black87,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Row(
                        children: [
                            Icon(Icons.visibility_off, size: 12, color: Colors.white),
                            SizedBox(width: 4),
                            Text("ANONIM", style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                        ]
                    )
                  ),
                ),
              ],
            ),
            
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.calendar_today_rounded, size: 14, color: Colors.grey[500]),
                          const SizedBox(width: 6),
                          Text(appeal.formattedDate, style: TextStyle(color: Colors.grey[500], fontSize: 13, fontWeight: FontWeight.w500)),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: statusColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            Icon(statusIcon, size: 14, color: statusColor),
                            const SizedBox(width: 4),
                            Text(statusText, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 11)),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    appeal.text ?? "Murojaat matni mavjud emas", 
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Colors.black87, height: 1.2), 
                    maxLines: 2, 
                    overflow: TextOverflow.ellipsis
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  IconData _getIconForRole(String? role) {
      if (role == null) return Icons.chat_bubble_outline;
      switch(role.toLowerCase()) {
          case 'dekanat': return Icons.school;
          case 'tyutor': return Icons.supervisor_account;
          case 'buxgalteriya': return Icons.account_balance_wallet;
          case 'psixolog': return Icons.psychology;
          case 'rahbariyat': return Icons.account_balance;
          default: return Icons.chat_bubble_outline;
      }
  }
}

// Keeping the CreateAppealSheet and DetailScreen classes (previously defined) but ensuring they are available.
// Since we are replacing the file content, I must include them here too, unchanged.

class CreateAppealSheet extends StatefulWidget {
  final VoidCallback onAppealCreated;
  const CreateAppealSheet({super.key, required this.onAppealCreated});

  @override
  State<CreateAppealSheet> createState() => _CreateAppealSheetState();
}

class _CreateAppealSheetState extends State<CreateAppealSheet> {
  String? _selectedRecipient;
  bool _isAnonymous = false;
  bool _isSubmitting = false;
  final TextEditingController _textController = TextEditingController();
  final AppealService _service = AppealService();

  final List<String> _recipients = ["Rahbariyat", "Dekanat", "Tyutor", "Psixolog", "Buxgalteriya"];

  String _mapRoleToKey(String display) {
      return display.toLowerCase();
  }

  Future<void> _submit() async {
      if (_selectedRecipient == null || _textController.text.isEmpty) return;
      
      setState(() => _isSubmitting = true);
      
      final success = await _service.createAppeal(
          text: _textController.text,
          role: _mapRoleToKey(_selectedRecipient!),
          isAnonymous: _isAnonymous
      );
      
      if (mounted) {
          setState(() => _isSubmitting = false);
          if (success) {
            Navigator.pop(context);
            widget.onAppealCreated();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text("Murojaat muvaffaqiyatli yuborildi!"), backgroundColor: Colors.green)
            );
          } else {
             ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text("Xatolik yuz berdi. Qaytadan urinib ko'ring."), backgroundColor: Colors.red)
            );
          }
      }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        left: 20, 
        right: 20, 
        top: 20, 
        bottom: MediaQuery.of(context).viewInsets.bottom + 20
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
          ),
          const SizedBox(height: 20),
          const Text("Yangi murojaat", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          
          const Text("Kimga yuborilsin?", style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: _recipients.map((recipient) {
              final isSelected = _selectedRecipient == recipient;
              return ChoiceChip(
                label: Text(recipient),
                selected: isSelected,
                onSelected: (selected) => setState(() => _selectedRecipient = selected ? recipient : null),
                selectedColor: AppTheme.primaryBlue,
                labelStyle: TextStyle(color: isSelected ? Colors.white : Colors.black),
              );
            }).toList(),
          ),
          
          const SizedBox(height: 20),
          
          const Text("Maxfiylik", style: TextStyle(fontWeight: FontWeight.w600)),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text("Anonim yuborish"),
            subtitle: const Text("Ism-familiyangiz ko'rinmaydi"),
            value: _isAnonymous,
            onChanged: (val) => setState(() => _isAnonymous = val),
            activeColor: AppTheme.primaryBlue,
          ),

          const SizedBox(height: 10),
          
          Expanded(
            child: TextField(
              controller: _textController,
              maxLines: null,
              expands: true,
              textAlignVertical: TextAlignVertical.top,
              decoration: InputDecoration(
                hintText: "Murojaat matnini yozing...",
                filled: true,
                fillColor: Colors.grey[50],
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                contentPadding: const EdgeInsets.all(16),
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: _isSubmitting ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryBlue,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: _isSubmitting 
                  ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Text("Yuborish", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
            ),
          ),
        ],
      ),
    );
  }
}

class AppealDetailScreen extends StatefulWidget {
  final int appealId;
  const AppealDetailScreen({super.key, required this.appealId});

  @override
  State<AppealDetailScreen> createState() => _AppealDetailScreenState();
}

class _AppealDetailScreenState extends State<AppealDetailScreen> {
  AppealDetail? _detail;
  bool _isLoading = true;
  final AppealService _service = AppealService();

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  Future<void> _loadDetail() async {
      setState(() => _isLoading = true);
      final detail = await _service.getAppealDetail(widget.appealId);
      if (mounted) {
          setState(() {
              _detail = detail;
              _isLoading = false;
          });
      }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
        return const Scaffold(
            backgroundColor: AppTheme.backgroundWhite,
            body: Center(child: CircularProgressIndicator())
        );
    }

    if (_detail == null) {
        return Scaffold(
             backgroundColor: AppTheme.backgroundWhite,
             appBar: AppBar(title: const Text("Xatolik")),
             body: const Center(child: Text("Murojaat topilmadi"))
        );
    }
    
    String statusDisplay = _detail!.status == 'pending' ? "Kutilmoqda" 
                       : _detail!.status == 'answered' ? "Javob berilgan" 
                       : _detail!.status == 'closed' ? "Yopilgan" : _detail!.status;
                       
    final messages = _detail!.messages;

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Column(
          children: [
             Text("Murojaat #${_detail!.id}", style: const TextStyle(color: Colors.black, fontSize: 16, fontWeight: FontWeight.bold)),
             Text(statusDisplay, style: const TextStyle(color: Colors.grey, fontSize: 12)),
          ]
        ),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 1,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final msg = messages[index];
                final isMe = msg.sender == 'me';
                final isSystem = msg.sender == 'system';
                
                if (isSystem) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Text(msg.text ?? "", style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                    ),
                  );
                }

                return Align(
                  alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(12),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: isMe ? AppTheme.primaryBlue : Colors.white,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(16),
                        topRight: const Radius.circular(16),
                        bottomLeft: isMe ? const Radius.circular(16) : const Radius.circular(4),
                        bottomRight: isMe ? const Radius.circular(4) : const Radius.circular(16),
                      ),
                      boxShadow: isMe ? [] : [
                        BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 5, offset: const Offset(0, 2))
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          msg.text ?? "[Fayl]", 
                          style: TextStyle(color: isMe ? Colors.white : Colors.black87),
                        ),
                        if (msg.fileId != null)
                             const Padding(
                               padding: EdgeInsets.only(top: 4.0),
                               child: Row(children: [Icon(Icons.attachment, size: 12, color: Colors.grey), SizedBox(width: 4), Text("Fayl biriktirilgan", style: TextStyle(fontSize: 10,  fontStyle: FontStyle.italic))]),
                             ),

                        const SizedBox(height: 4),
                        Align(
                          alignment: Alignment.bottomRight,
                          child: Text(
                            msg.time,
                            style: TextStyle(
                              color: isMe ? Colors.white.withOpacity(0.7) : Colors.grey[500],
                              fontSize: 10
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          if (_detail!.status != 'closed')
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: "Javob yozish...",
                        filled: true,
                        fillColor: Colors.grey[100],
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  CircleAvatar(
                    backgroundColor: AppTheme.primaryBlue,
                    child: IconButton(
                      icon: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                      onPressed: () {},
                    ),
                  )
                ],
              ),
            ),
          )
        ],
      ),
    );
  }
}
  const AppealsScreen({super.key});

  @override
  State<AppealsScreen> createState() => _AppealsScreenState();
}

class _AppealsScreenState extends State<AppealsScreen> with SingleTickerProviderStateMixin {
  final AppealService _appealService = AppealService();
  List<Appeal> _appeals = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAppeals();
  }

  Future<void> _loadAppeals() async {
    setState(() => _isLoading = true);
    final appeals = await _appealService.getMyAppeals();
    if (mounted) {
      setState(() {
        _appeals = appeals;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Murojaatlar", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAppeals,
          )
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading 
                ? const Center(child: CircularProgressIndicator())
                : _appeals.isEmpty
                  ? _buildEmptyState()
                  : RefreshIndicator(
                      onRefresh: _loadAppeals,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(20),
                        itemCount: _appeals.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 16),
                        itemBuilder: (context, index) => _buildAppealCard(_appeals[index]),
                      ),
                    ),
          ),
          _buildBottomButton(),
        ],
      ),
    );
  }

  Widget _buildBottomButton() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 20,
            offset: const Offset(0, -5),
          )
        ],
      ),
      child: SafeArea(
        child: SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: _showCreateAppealSheet,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 0,
            ),
            child: const Text(
              "Yangi murojaat",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.chat_bubble_outline_rounded, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            "Murojaatlar mavjud emas",
            style: TextStyle(color: Colors.grey[500], fontSize: 16, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildAppealCard(Appeal appeal) {
    Color statusColor;
    String statusText;
    IconData statusIcon;

    switch (appeal.status) {
      case 'answered':
        statusColor = Colors.green;
        statusText = "Javob berilgan";
        statusIcon = Icons.check_circle_outline_rounded;
        break;
      case 'closed':
        statusColor = Colors.grey;
        statusText = "Yopilgan";
        statusIcon = Icons.lock_outline_rounded;
        break;
      case 'pending':
      default:
        statusColor = Colors.orange;
        statusText = "Kutilmoqda";
        statusIcon = Icons.schedule_rounded;
        break;
    }
    
    // Capitalize recipient
    String recipientDisplay = appeal.assignedRole != null 
        ? appeal.assignedRole![0].toUpperCase() + appeal.assignedRole!.substring(1) 
        : "Rahbariyat";

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
          onTap: () => _showAppealDetails(appeal.id),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: statusColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(statusIcon, size: 14, color: statusColor),
                          const SizedBox(width: 4),
                          Text(
                            statusText,
                            style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    Text(
                      appeal.formattedDate,
                      style: TextStyle(color: Colors.grey[500], fontSize: 12),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  appeal.text ?? "Mavzusiz", 
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Icon(Icons.person_pin_circle_rounded, size: 14, color: Colors.grey[600]),
                    const SizedBox(width: 4),
                    Text(
                      "Qabul qiluvchi: $recipientDisplay",
                      style: TextStyle(color: Colors.grey[600], fontSize: 13),
                    ),
                    if (appeal.isAnonymous) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(color: Colors.black87, borderRadius: BorderRadius.circular(4)),
                        child: const Text("ANONIM", style: TextStyle(color: Colors.white, fontSize: 10)),
                      )
                    ]
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showCreateAppealSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => CreateAppealSheet(onAppealCreated: _loadAppeals),
    );
  }

  void _showAppealDetails(int appealId) {
    Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => AppealDetailScreen(appealId: appealId))
    );
  }
}

class CreateAppealSheet extends StatefulWidget {
  final VoidCallback onAppealCreated;
  const CreateAppealSheet({super.key, required this.onAppealCreated});

  @override
  State<CreateAppealSheet> createState() => _CreateAppealSheetState();
}

class _CreateAppealSheetState extends State<CreateAppealSheet> {
  String? _selectedRecipient;
  bool _isAnonymous = false;
  bool _isSubmitting = false;
  final TextEditingController _textController = TextEditingController();
  final AppealService _service = AppealService();

  final List<String> _recipients = ["Rahbariyat", "Dekanat", "Tyutor", "Psixolog", "Buxgalteriya"];

  // Map display names to backend keys
  String _mapRoleToKey(String display) {
      return display.toLowerCase();
  }

  Future<void> _submit() async {
      if (_selectedRecipient == null || _textController.text.isEmpty) return;
      
      setState(() => _isSubmitting = true);
      
      final success = await _service.createAppeal(
          text: _textController.text,
          role: _mapRoleToKey(_selectedRecipient!),
          isAnonymous: _isAnonymous
      );
      
      if (mounted) {
          setState(() => _isSubmitting = false);
          if (success) {
            Navigator.pop(context);
            widget.onAppealCreated();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text("Murojaat muvaffaqiyatli yuborildi!"), backgroundColor: Colors.green)
            );
          } else {
             ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text("Xatolik yuz berdi. Qaytadan urinib ko'ring."), backgroundColor: Colors.red)
            );
          }
      }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        left: 20, 
        right: 20, 
        top: 20, 
        bottom: MediaQuery.of(context).viewInsets.bottom + 20
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
          ),
          const SizedBox(height: 20),
          const Text("Yangi murojaat", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          
          // Recipient
          const Text("Kimga yuborilsin?", style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: _recipients.map((recipient) {
              final isSelected = _selectedRecipient == recipient;
              return ChoiceChip(
                label: Text(recipient),
                selected: isSelected,
                onSelected: (selected) => setState(() => _selectedRecipient = selected ? recipient : null),
                selectedColor: AppTheme.primaryBlue,
                labelStyle: TextStyle(color: isSelected ? Colors.white : Colors.black),
              );
            }).toList(),
          ),
          
          const SizedBox(height: 20),
          
          // Anonymity
          const Text("Maxfiylik", style: TextStyle(fontWeight: FontWeight.w600)),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text("Anonim yuborish"),
            subtitle: const Text("Ism-familiyangiz ko'rinmaydi"),
            value: _isAnonymous,
            onChanged: (val) => setState(() => _isAnonymous = val),
            activeColor: AppTheme.primaryBlue,
          ),

          const SizedBox(height: 10),
          
          // Content
          Expanded(
            child: TextField(
              controller: _textController,
              maxLines: null,
              expands: true,
              textAlignVertical: TextAlignVertical.top,
              decoration: InputDecoration(
                hintText: "Murojaat matnini yozing...",
                filled: true,
                fillColor: Colors.grey[50],
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                contentPadding: const EdgeInsets.all(16),
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: _isSubmitting ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryBlue,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: _isSubmitting 
                  ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Text("Yuborish", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
            ),
          ),
        ],
      ),
    );
  }
}

class AppealDetailScreen extends StatefulWidget {
  final int appealId;
  const AppealDetailScreen({super.key, required this.appealId});

  @override
  State<AppealDetailScreen> createState() => _AppealDetailScreenState();
}

class _AppealDetailScreenState extends State<AppealDetailScreen> {
  AppealDetail? _detail;
  bool _isLoading = true;
  final AppealService _service = AppealService();

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  Future<void> _loadDetail() async {
      setState(() => _isLoading = true);
      final detail = await _service.getAppealDetail(widget.appealId);
      if (mounted) {
          setState(() {
              _detail = detail;
              _isLoading = false;
          });
      }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
        return const Scaffold(
            backgroundColor: AppTheme.backgroundWhite,
            body: Center(child: CircularProgressIndicator())
        );
    }

    if (_detail == null) {
        return Scaffold(
             backgroundColor: AppTheme.backgroundWhite,
             appBar: AppBar(title: const Text("Xatolik")),
             body: const Center(child: Text("Murojaat topilmadi"))
        );
    }
    
    // Capitalize status
    String statusDisplay = _detail!.status == 'pending' ? "Kutilmoqda" 
                       : _detail!.status == 'answered' ? "Javob berilgan" 
                       : _detail!.status == 'closed' ? "Yopilgan" : _detail!.status;
                       
    final messages = _detail!.messages;

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Column(
          children: [
             Text("Murojaat #${_detail!.id}", style: const TextStyle(color: Colors.black, fontSize: 16, fontWeight: FontWeight.bold)),
             Text(statusDisplay, style: const TextStyle(color: Colors.grey, fontSize: 12)),
          ]
        ),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 1,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final msg = messages[index];
                final isMe = msg.sender == 'me';
                final isSystem = msg.sender == 'system';
                
                if (isSystem) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Text(msg.text ?? "", style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                    ),
                  );
                }

                return Align(
                  alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(12),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: isMe ? AppTheme.primaryBlue : Colors.white,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(16),
                        topRight: const Radius.circular(16),
                        bottomLeft: isMe ? const Radius.circular(16) : const Radius.circular(4),
                        bottomRight: isMe ? const Radius.circular(4) : const Radius.circular(16),
                      ),
                      boxShadow: isMe ? [] : [
                        BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 5, offset: const Offset(0, 2))
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          msg.text ?? "[Fayl]", // Handle empty text (e.g. just file)
                          style: TextStyle(color: isMe ? Colors.white : Colors.black87),
                        ),
                        if (msg.fileId != null)
                             const Padding(
                               padding: EdgeInsets.only(top: 4.0),
                               child: Row(children: [Icon(Icons.attachment, size: 12, color: Colors.grey), SizedBox(width: 4), Text("Fayl biriktirilgan", style: TextStyle(fontSize: 10,  fontStyle: FontStyle.italic))]),
                             ),

                        const SizedBox(height: 4),
                        Align(
                          alignment: Alignment.bottomRight,
                          child: Text(
                            msg.time,
                            style: TextStyle(
                              color: isMe ? Colors.white.withOpacity(0.7) : Colors.grey[500],
                              fontSize: 10
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          if (_detail!.status != 'closed')
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: "Javob yozish...",
                        filled: true,
                        fillColor: Colors.grey[100],
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  CircleAvatar(
                    backgroundColor: AppTheme.primaryBlue,
                    child: IconButton(
                      icon: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                      onPressed: () {},
                    ),
                  )
                ],
              ),
            ),
          )
        ],
      ),
    );
  }
}
