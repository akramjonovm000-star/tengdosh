// Last Updated: 2026-01-16 19:10
import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/features/feedback/screens/feedback_detail_screen.dart';
import 'package:talabahamkor_mobile/features/feedback/widgets/feedback_upload_dialog.dart';

class FeedbackScreen extends StatefulWidget {
  const FeedbackScreen({super.key});

  @override
  State<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends State<FeedbackScreen> {
  final DataService _dataService = DataService();
  List<dynamic> _feedbacks = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadFeedbacks();
  }

  Future<void> _loadFeedbacks() async {
    try {
      final data = await _dataService.getMyFeedback();
      setState(() {
        _feedbacks = data;
        _isLoading = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Xatolik: $e')),
        );
      }
    }
  }

  // Bot-aligned Hierarchy (Updated per user request)
  final List<Map<String, dynamic>> _recipientHierarchy = [
    {
      "label": "🏛 Rahbariyat",
      "id": "rahbariyat",
      "children": [
        {"label": "🎓 Rektor", "id": "rektor"},
        {"label": "👔 O'quv ishlari prorektori", "id": "prorektor"},
        {"label": "👔 Yoshlar ishlari prorektori", "id": "yoshlar_prorektor"},
        {"label": "🔬 Ilmiy ishlar bo'yicha prorektor", "id": "ilmiy_prorektor"},
        {"label": "🔍 Inspektor", "id": "inspektor"},
      ]
    },
    {
      "label": "🏫 Dekanat",
      "id": "dekanat",
      "children": [
        {"label": "👤 Dekan", "id": "dekan"},
        {"label": "👤 Dekan o'rinbosari", "id": "dekan_orinbosari"},
      ]
    },
    {"label": "💰 Buxgalteriya", "id": "buxgalter"},
    {"label": "🧠 Psixolog", "id": "psixolog"},
    {"label": "🧑‍🏫 Tyutor", "id": "tyutor"},
  ];

// ... existing code ...

  Color _getStatusColor(String? status) {
    switch (status) {
      case 'open': return Colors.blue;
      case 'process': return Colors.orange;
      case 'completed': return Colors.green;
      case 'cancelled': return Colors.red;
      default: return Colors.grey;
    }
  }

  String _getStatusText(String? status) {
    switch (status) {
      case 'open': return "Yangi";
      case 'process': return "Jarayonda";
      case 'completed': return "Bajarildi";
      case 'cancelled': return "Bekor qilingan";
      default: return "Noma'lum";
    }
  }

  void _showAddFeedbackSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: _FeedbackWizard(
          hierarchy: _recipientHierarchy,
          onSubmit: _submitFeedback,
        ),
      ),
    );
  }

  void _showTelegramUploadDialog(String text, String roleId, bool isAnonymous) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: FeedbackUploadDialog(
          text: text,
          role: roleId,
          isAnonymous: isAnonymous,
          onUploadSuccess: _loadFeedbacks,
        ),
      ),
    );
  }

  Future<void> _submitFeedback(String text, String roleId, bool isAnonymous, bool wantsFile) async {
    if (wantsFile) {
      _showTelegramUploadDialog(text, roleId, isAnonymous);
      return;
    }

    setState(() => _isLoading = true);
    final result = await _dataService.createFeedback(
      text: text,
      role: roleId,
      isAnonymous: isAnonymous,
    );
    
    if (result['status'] == 'success') {
      _loadFeedbacks();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Murojaat muvaffaqiyatli yuborildi!"), backgroundColor: Colors.green),
        );
      }
    } else {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(content: Text(result['message'] ?? "Xatolik yuz berdi"), backgroundColor: Colors.red),
        );
      }
    }
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Mening Murojaatlarim")),
      body: Column(
        children: [
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _feedbacks.isEmpty
                    ? const Center(child: Text("Murojaatlar mavjud emas"))
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _feedbacks.length,
                        itemBuilder: (context, index) {
                          final fb = _feedbacks[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            elevation: 2,
                            child: ListTile(
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => FeedbackDetailScreen(feedbackId: fb['id']),
                                  ),
                                );
                              },
                              leading: CircleAvatar(
                                backgroundColor: _getStatusColor(fb['status']).withOpacity(0.2),
                                child: Icon(Icons.message, color: _getStatusColor(fb['status'])),
                              ),
                              title: Text(
                                fb['text'] ?? "Matnsiz",
                                maxLines: 1, 
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text("Kimga: ${fb['assigned_role']?.toUpperCase() ?? 'Noma\'lum'}"),
                                  Text("Holati: ${_getStatusText(fb['status'])}"),
                                ],
                              ),
                              trailing: Text(
                                (fb['created_at'] as String).substring(0, 10),
                                style: const TextStyle(color: Colors.grey, fontSize: 12),
                              ),
                            ),
                          );
                        },
                      ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.1),
                  blurRadius: 10,
                  offset: const Offset(0, -5),
                )
              ],
            ),
            child: SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: _showAddFeedbackSheet,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0033FF), // Vibrant Blue
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  elevation: 0,
                ),
                child: const Text(
                  "Murojaat yuborish",
                  style: TextStyle(
                    color: Colors.white, 
                    fontSize: 16, 
                    fontWeight: FontWeight.bold
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FeedbackWizard extends StatefulWidget {
  final List<Map<String, dynamic>> hierarchy;
  final Function(String, String, bool, bool) onSubmit;

  const _FeedbackWizard({required this.hierarchy, required this.onSubmit});

  @override
  State<_FeedbackWizard> createState() => _FeedbackWizardState();
}

class _FeedbackWizardState extends State<_FeedbackWizard> {
  int _step = 0;
  Map<String, dynamic>? _selectedCategory;
  Map<String, dynamic>? _selectedSubCategory;
  bool _isAnonymous = false;
  bool _wantsFile = false;
  final TextEditingController _textController = TextEditingController();

  void _selectCategory(Map<String, dynamic> item) {
    setState(() {
      _selectedCategory = item;
      _selectedSubCategory = null; // Clear previous sub-selection
      if (item.containsKey('children')) {
        _step = 1;
      } else {
        _step = 2; // Direct to form
      }
    });
  }

  void _selectSubCategory(Map<String, dynamic> item) {
    setState(() {
      _selectedSubCategory = item;
      _step = 2;
    });
  }

  Widget _buildChip(Map<String, dynamic> item, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade200),
          boxShadow: [
             BoxShadow(
               color: Colors.grey.withOpacity(0.05),
               blurRadius: 10,
               offset: const Offset(0, 4),
             )
          ]
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              item['label'], 
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)
            ),
            const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: Colors.grey),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          // Handle bar
          Center(
            child: Container(
              width: 40, 
              height: 4, 
              decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))
            ),
          ),
          const SizedBox(height: 20),
          
          Expanded(
            child: _buildContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    if (_step == 0 || _step == 1) {
      final items = _step == 0 
          ? widget.hierarchy 
          : (_selectedCategory!['children'] as List).cast<Map<String, dynamic>>();

      final titleText = _step == 0 ? "Kimga yuborilsin?" : "${_selectedCategory!['label']} tarkibi:";

      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Stack(
            alignment: Alignment.center,
            children: [
              if (_step == 1)
                Align(
                  alignment: Alignment.centerLeft,
                  child: IconButton(
                    icon: const Icon(Icons.arrow_back),
                    onPressed: () => setState(() => _step = 0),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ),
              Padding(
                padding: EdgeInsets.symmetric(horizontal: _step == 1 ? 40.0 : 0),
                child: Text(
                  titleText,
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Expanded(
            child: Column(
              children: [
                Expanded(
                  child: ListView.separated(
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                       final item = items[index];
                       return _buildChip(item, () {
                         if (_step == 0) _selectCategory(item);
                         else _selectSubCategory(item);
                       });
                    },
                  ),
                ),
              ],
            ),
          ),
        ],
      );
    } else {
      // Form Step
      return SingleChildScrollView(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom + 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header with selected role
            Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back), 
                  onPressed: () => setState(() => _step = _selectedCategory!.containsKey('children') ? 1 : 0),
                ),
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryBlue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.person, size: 16, color: AppTheme.primaryBlue),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _selectedSubCategory?['label'] ?? _selectedCategory?['label'],
                            style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Anonymity Toggle
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade200),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.visibility_off_outlined, color: Colors.grey),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("Anonim yuborish", style: TextStyle(fontWeight: FontWeight.bold)),
                        Text("Ismingiz sir saqlanadi", style: TextStyle(color: Colors.grey, fontSize: 12)),
                      ],
                    ),
                  ),
                  Switch(
                    value: _isAnonymous,
                    onChanged: (v) => setState(() => _isAnonymous = v),
                    activeColor: AppTheme.primaryBlue,
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 20),
            
            // Text Input
            TextField(
              controller: _textController,
              maxLines: 6,
              decoration: InputDecoration(
                hintText: "Murojaatingizni batafsil yozing...",
                filled: true,
                fillColor: Colors.grey[50],
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.all(16),
              ),
            ),
            
            const SizedBox(height: 12),
            
            // File Attachment Toggle (Progress-based)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                border: Border.all(color: _wantsFile ? AppTheme.primaryBlue : Colors.grey.shade200),
                borderRadius: BorderRadius.circular(12),
                color: _wantsFile ? AppTheme.primaryBlue.withOpacity(0.05) : null,
              ),
              child: Row(
                children: [
                  Icon(Icons.telegram_rounded, color: _wantsFile ? AppTheme.primaryBlue : Colors.grey),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("Fayl biriktirish (Telegram)", style: TextStyle(fontWeight: FontWeight.bold)),
                        Text("Rasm, video yoki PDF yuborish", style: TextStyle(color: Colors.grey, fontSize: 12)),
                      ],
                    ),
                  ),
                  Switch(
                    value: _wantsFile,
                    onChanged: (v) => setState(() => _wantsFile = v),
                    activeColor: AppTheme.primaryBlue,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),
            
            // Submit Button
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: () {
                   final text = _textController.text.trim();
                   final roleId = _selectedSubCategory?['id'] ?? _selectedCategory?['id'];
                   
                   if (text.isEmpty) {
                     ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Iltimos, murojaat matnini yozing")));
                     return;
                   }
                   
                   Navigator.pop(context);
                   widget.onSubmit(text, roleId, _isAnonymous, _wantsFile);
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryBlue,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  elevation: 2,
                ),
                child: const Text("YUBORISH", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 1)),
              ),
            ),
          ],
        ),
      );
    }
  }

}
