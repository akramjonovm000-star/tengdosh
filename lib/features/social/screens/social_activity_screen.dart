import 'dart:io';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:image_picker/image_picker.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/features/social/screens/social_activity_detail_screen.dart';

import 'package:talabahamkor_mobile/core/constants/api_constants.dart';

import 'package:talabahamkor_mobile/features/social/models/social_activity.dart';

class AddActivitySheet extends StatefulWidget {
  final List<String> categories;
  final Function(SocialActivity, String?) onSave;
  final SocialActivity? activity; // For Edit Mode

  const AddActivitySheet({super.key, required this.categories, required this.onSave, this.activity});

  @override
  State<AddActivitySheet> createState() => _AddActivitySheetState();
}

class _AddActivitySheetState extends State<AddActivitySheet> {
  int _step = 1; // 1 = Category, 2 = Form
  String? _selectedCategory;
  
  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  DateTime? _selectedDate;
  
  // NEW STATE
  String? _uploadSessionId;
  bool _isUploading = false; // Waiting for bot
  int _uploadedCount = 0; // Count of uploaded images
  Timer? _pollingTimer;

  @override
  void initState() {
    super.initState();
    if (widget.activity != null) {
      // Edit Mode Initialization
      _step = 2; // Direct to Form
      // Map category back to UI label if needed, or simple usage
      // Here assuming category is key, might need reverse mapping or just use capital
      // For simplicity, let's use the activity category directly, or try to match one from widget.categories
      _selectedCategory = _matchCategory(widget.activity!.category);
      
      _titleController.text = widget.activity!.title;
      _descController.text = widget.activity!.description;
      try {
        _selectedDate = DateFormat('dd.MM.yyyy').parse(widget.activity!.date);
      } catch (_) {
        _selectedDate = DateTime.now();
      }
      
      // Images for edit?
      // Currently API doesn't support adding/removing images in PATCH easily without complex logic.
      // We will disable image upload for Edit Mode in this MVP or show existing count.
      _uploadedCount = widget.activity!.imageUrls.length;
    }
  }

  String _matchCategory(String key) {
    // Simple reverse toggle or just Capitalize
    // Actually our UI uses specific labels ("To'garak", etc.)
    // We should try to find matching label from widget.categories
    // But widget.categories has "To'garak", "Yutuqlar" etc.
    // keys are "togarak", "yutuqlar"
    // Let's do a best effort match
    final map = {
      "togarak": "To'garak",
      "marifat": "Ma'rifat darslari",
      "madaniy": "Madaniy tashriflar",
      "sport": "Sport",
      "volontyorlik": "Volontyorlik",
      "yutuqlar": "Yutuqlar",
      "boshqa": "Boshqa"
    };
    return map[key.toLowerCase()] ?? "Boshqa";
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _titleController.dispose();
    _descController.dispose();
    super.dispose();
  }

  Future<void> _initUpload() async {
    final sessionId = DateTime.now().millisecondsSinceEpoch.toString();
    setState(() {
      _uploadSessionId = sessionId;
      _isUploading = true;
      _uploadedCount = 0;
    });

    try {
      await Provider.of<DataService>(context, listen: false).initUploadSession(
        sessionId,
        _selectedCategory ?? "Faollik"
      );
      
      // Start Polling
    _pollingTimer?.cancel();
    _checkStatus(sessionId); // Initial call
    _pollingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
       _checkStatus(sessionId);
    });
      
    } catch (e) {
      debugPrint("Upload Init Error: $e");
      setState(() => _isUploading = false);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Xatolik: $e")));
    }
  }
  
  Future<void> _checkStatus(String sessionId) async {
    try {
      final res = await Provider.of<DataService>(context, listen: false).checkUploadStatus(sessionId);
      if (res['status'] == 'uploaded') {
        final count = res['count'] ?? 0;
        
        if (mounted) {
          setState(() {
            _uploadedCount = count;
            if (count >= 5) {
               _pollingTimer?.cancel();
               _isUploading = false;
            }
          });
        }
      }
    } catch (e) {
      debugPrint("Polling Error: $e");
    }
  }



  @override
  Widget build(BuildContext context) {
    bool isEdit = widget.activity != null;

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          const SizedBox(height: 12),
          Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 20),
          
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Row(
              children: [
                if (_step == 2 && !isEdit) ...[
                  IconButton(
                    icon: const Icon(Icons.arrow_back), 
                    onPressed: () => setState(() => _step = 1),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                  const SizedBox(width: 12),
                ],
                Expanded(
                  child: Text(
                    isEdit 
                      ? "Faollikni tahrirlash"
                      : (_step == 1 ? "Kategoriyani tanlang" : "Ma'lumotlarni kiriting"),
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
          ),
          const Divider(),
          
          Expanded(
            child: _step == 1 ? _buildCategoryStep() : _buildFormStep(isEdit),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryStep() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: widget.categories.length,
      itemBuilder: (context, index) {
        final category = widget.categories[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: InkWell(
            onTap: () {
              setState(() {
                _selectedCategory = category;
                _step = 2;
              });
            },
            borderRadius: BorderRadius.circular(16),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey[50],
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey[200]!),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryBlue.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.category, color: AppTheme.primaryBlue, size: 20),
                  ),
                  const SizedBox(width: 16),
                  Text(category, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                  const Spacer(),
                  const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.grey),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildFormStep(bool isEdit) {
    String titleLabel = "Faollik nomi";
    String titleHint = "Nomini kiriting...";
    String descLabel = "Faollik tavsifi";
    String descHint = "Batafsil ma'lumot...";

    switch (_selectedCategory) {
      case "Ma'rifat darslari":
        titleLabel = "Ma'rifat darsi mavzusi";
        titleHint = "Mavzuni kiriting (masalan: Odob-axloq)";
        descLabel = "Ma'rifat darsi tavsifi";
        descHint = "Dars haqida qisqacha yozing...";
        break;
      case "To'garak":
        titleLabel = "To'garak nomi";
        titleHint = "Qaysi to'garakka qatnashdingiz?";
        descLabel = "To'garak tavsifi";
        descHint = "Mashg'ulot haqida ma'lumot...";
        break;
      case "Yutuqlar":
        titleLabel = "Yutuq nomi";
        titleHint = "Qanday yutuqqa erishdingiz?";
        descLabel = "Yutuq tavsifi";
        descHint = "Musobaqa yoki tadbir haqida...";
        break;
      case "Volontyorlik":
        titleLabel = "Volontyorlik nomi";
        titleHint = "Qanday ishda yordam berdingiz?";
        descLabel = "Volontyorlik tavsifi";
        descHint = "Bajarilgan ishlar haqida...";
        break;
      case "Madaniy tashriflar":
        titleLabel = "Tashrif nomi";
        titleHint = "Qayerga tashrif buyurdingiz?";
        descLabel = "Tashrif tavsifi";
        descHint = "Tashrifdan olgan taassurotlaringiz...";
        break;
      case "Sport":
        titleLabel = "Sport turi / Musobaqa nomi";
        titleHint = "Futbol, Shaxmat yoki musobaqa nomi...";
        descLabel = "Faollik tavsifi";
        descHint = "Musobaqa natijalari...";
        break;
      default:
        titleLabel = "Faollik nomi";
        titleHint = "Faollik nomini kiriting...";
        descLabel = "Faollik tavsifi";
        descHint = "Faollik haqida ma'lumot...";
    }

    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _selectedCategory ?? "",
                    style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(height: 24),
                
                TextField(
                  controller: _titleController,
                  decoration: InputDecoration(
                     labelText: titleLabel,
                     hintText: titleHint,
                     border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                
                TextField(
                  controller: _descController,
                  maxLines: 4,
                  decoration: InputDecoration(
                     labelText: descLabel,
                     hintText: descHint,
                     border: const OutlineInputBorder(),
                     alignLabelWithHint: true,
                  ),
                ),
                const SizedBox(height: 16),
                
                // Hide Image Upload block in Edit Mode (simplification)
                if (!isEdit) _buildImageUploadBlock()
                else 
                   Container(
                     padding: const EdgeInsets.all(12),
                     decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(8)),
                     child: const Row(children: [
                        Icon(Icons.info_outline, color: Colors.grey),
                        SizedBox(width: 8),
                        Expanded(child: Text("Rasmlarni tahrirlash uchun o'chirib qayta yarating."))
                     ]),
                   ),

                const SizedBox(height: 16),
                
                GestureDetector(
                  onTap: _pickDate,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey),
                      borderRadius: BorderRadius.circular(4),
                      color: Colors.transparent,
                    ),
                    child: Row(
                      children: [
                         const Icon(Icons.calendar_month, color: AppTheme.primaryBlue),
                         const SizedBox(width: 12),
                         Text(
                           _selectedDate == null 
                             ? "Sana, Oy, Yilni tanlang" 
                             : DateFormat('dd.MM.yyyy').format(_selectedDate!),
                           style: TextStyle(
                             color: _selectedDate == null ? Colors.grey[600] : Colors.black, 
                             fontSize: 16, 
                             fontWeight: _selectedDate == null ? FontWeight.normal : FontWeight.w500
                           ),
                         ),
                      ],
                    ),
                  ),
                ),
                
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
        
        // Stuck at bottom
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, -5))],
          ),
          child: SafeArea(
            child: SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: _saveActivity,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryBlue,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                child: Text(isEdit ? "Yangilash" : "Saqlash", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildImageUploadBlock() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_uploadedCount > 0)
           Container(
             width: double.infinity,
             padding: const EdgeInsets.symmetric(vertical: 24),
             decoration: BoxDecoration(
               color: Colors.green[50],
               borderRadius: BorderRadius.circular(12),
               border: Border.all(color: Colors.green[300]!),
             ),
             child: Column(
               children: [
                  const Icon(Icons.check_circle, color: Colors.green, size: 40),
                  const SizedBox(height: 8),
                  Text("$_uploadedCount/5 rasm yuklandi!", style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
                  if (_uploadedCount < 5)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text("Yana yuklashingiz mumkin (Bot orqali)", style: TextStyle(color: Colors.green[700], fontSize: 12)),
                    )
               ],
             ),
           )
        else if (_isUploading)
           Container(
             width: double.infinity,
             padding: const EdgeInsets.symmetric(vertical: 24),
             decoration: BoxDecoration(
               color: Colors.orange[50],
               borderRadius: BorderRadius.circular(12),
               border: Border.all(color: Colors.orange[300]!),
             ),
             child: const Column(
               children: [
                  CircularProgressIndicator(color: Colors.orange),
                  SizedBox(height: 12),
                  Text("Botga rasmni yuboring...", style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold)),
                  SizedBox(height: 4),
                  Text("Telegramdan xabar kutilyapti", style: TextStyle(color: Colors.grey, fontSize: 12)),
               ],
             ),
           )
        else
          GestureDetector(
            onTap: _initUpload,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 24),
              decoration: BoxDecoration(
                color: Colors.blue[50], // AppTheme.primaryBlue logic
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue[200]!),
              ),
              child: const Column(
                children: [
                   Icon(Icons.telegram, color: Colors.blue, size: 40),
                   SizedBox(height: 8),
                   Text(
                     "Rasm yuklash (Telegram orqali)", 
                     style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold)
                   ),
                   SizedBox(height: 4),
                   Text(
                     "Tugmani bosing va Botga rasm yuboring", 
                     style: TextStyle(color: Colors.grey, fontSize: 12)
                   ),
                ],
              ),
            ),
          ),
      ],
    );
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final firstDate = DateTime(2020);
    final lastDate = DateTime(2030);
    
    DateTime initialDate = _selectedDate ?? now;
    if (initialDate.isBefore(firstDate)) initialDate = firstDate;
    if (initialDate.isAfter(lastDate)) initialDate = lastDate;

    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: firstDate,
      lastDate: lastDate,
      locale: const Locale('uz', 'UZ'),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: AppTheme.primaryBlue,
              onPrimary: Colors.white, 
              surface: Colors.white,
              onSurface: Colors.black,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() => _selectedDate = picked);
    }
  }

  void _saveActivity() {
    if (_titleController.text.isEmpty || _descController.text.isEmpty || _selectedDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Barcha maydonlarni to'ldiring")));
      return;
    }
    
    // Check if image uploaded (ONLY FOR NEW)
    if (widget.activity == null && _uploadedCount == 0) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Iltimos, avval rasm yuklang!")));
      return;
    }

    final newActivity = SocialActivity(
      id: widget.activity?.id ?? "0", 
      category: _selectedCategory!,
      title: _titleController.text,
      description: _descController.text,
      date: DateFormat('dd.MM.yyyy').format(_selectedDate!),
      status: widget.activity?.status ?? "pending",
      imageUrls: widget.activity?.imageUrls ?? [],
    );

    widget.onSave(newActivity, _uploadSessionId);
    Navigator.pop(context);
  }
}

class SocialActivityScreen extends StatefulWidget {
  const SocialActivityScreen({super.key});

  @override
  State<SocialActivityScreen> createState() => _SocialActivityScreenState();
}

class _SocialActivityScreenState extends State<SocialActivityScreen> {
  String _selectedCategory = "Barchasi";
  String _selectedStatus = "Barchasi";
  bool _isLoading = false;
  
  // Registration Check
  bool _isRegisteredBot = false;
  bool _isCheckingReg = true;

  final List<String> _categories = ["Barchasi", "To'garak", "Yutuqlar", "Ma'rifat darslari", "Volontyorlik", "Madaniy tashriflar", "Sport", "Boshqa"];
  final List<String> _statuses = ["Barchasi", "Tasdiqlangan", "Kutilayotgan", "Rad etilgan"];

  List<SocialActivity> _activities = [];

  @override
  void initState() {
    super.initState();
    _loadActivities();
  }

  Future<void> _loadActivities() async {
    if (!mounted) return;
    setState(() => _isLoading = true);
    try {
      final rawData = await Provider.of<DataService>(context, listen: false).getActivities();
      
      // Check Registration
      final profile = await Provider.of<DataService>(context, listen: false).getProfile();
      
      if (!mounted) return;
      setState(() {
        _activities = rawData.map((e) => SocialActivity.fromJson(e)).toList();
        _isRegisteredBot = profile['is_registered_bot'] ?? false;
        _isCheckingReg = false;
      });
    } catch (e) {
      debugPrint("Load Error: $e");
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Ijtimoiy Faollik", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          IconButton(onPressed: _loadActivities, icon: const Icon(Icons.refresh))
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator()) 
        : Column(
        children: [
          _buildStatsHeader(),
          const SizedBox(height: 16),
          _buildFilterBar(),
          Expanded(
            child: _getFilteredActivities().isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: _getFilteredActivities().length,
                    itemBuilder: (context, index) {
                      return ActivityCard(
                        activity: _getFilteredActivities()[index],
                        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => SocialActivityDetailScreen(activity: _getFilteredActivities()[index]))),
                        onEdit: (act) => _showEditSheet(act),
                        onDelete: (act) => _deleteActivity(act),
                      );
                    },
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
            offset: const Offset(0, -5)
          )
        ],
      ),
      child: SafeArea(
        child: SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: () async {
               if (_isCheckingReg) return;
               
               if (!_isRegisteredBot) {
                 // Double check (User might have just registered)
                 setState(() => _isCheckingReg = true); 
                 
                 try {
                    final profile = await Provider.of<DataService>(context, listen: false).getProfile();
                    if (mounted) {
                       setState(() {
                          _isRegisteredBot = profile['is_registered_bot'] ?? false;
                          _isCheckingReg = false;
                       });
                       
                       if (_isRegisteredBot) {
                          _showAddActivitySheet();
                          return;
                       }
                    }
                 } catch (e) {
                    if (mounted) setState(() => _isCheckingReg = false);
                 }
                 
                 if (mounted && !_isRegisteredBot) {
                    _showRegistrationAlert();
                 }
               } else {
                 _showAddActivitySheet();
               }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 0,
            ),
            child: const Text(
              "Faollik qo'shish",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatsHeader() {
    int approved = 0;
    int pending = 0;
    int rejected = 0;

    for (var act in _activities) {
      // Filter by Category
      if (_selectedCategory != "Barchasi") {
         final requiredKey = _getCategoryKey(_selectedCategory);
         if (act.category.toLowerCase() != requiredKey.toLowerCase()) {
           continue; 
         }
      }

      // Count Statuses
      if (act.status == 'approved') approved++;
      else if (act.status == 'pending') pending++;
      else if (act.status == 'rejected') rejected++;
    }

    final stats = [
      {"label": "Tasdiqlangan", "count": approved, "color": Colors.green},
      {"label": "Kutilayotgan", "count": pending, "color": Colors.orange},
      {"label": "Rad etilgan", "count": rejected, "color": Colors.red},
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
                  // Toggle logic: if already selected, go back to "Barchasi", else select this status
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
                      style: TextStyle(
                        fontSize: 12, 
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

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search_off_rounded, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            "Hech narsa topilmadi",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey[700]),
          ),
          const SizedBox(height: 8),
          Text(
            "Filterlarni o'zgartirib ko'ring yoki\nyangi faollik qo'shing",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[500]),
          ),
        ],
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

  String _getCategoryKey(String uiLabel) {
    if (uiLabel == "To'garak") return "togarak";
    if (uiLabel == "Ma'rifat darslari") return "marifat";
    if (uiLabel == "Madaniy tashriflar") return "madaniy";
    if (uiLabel == "Sport") return "sport";
    if (uiLabel == "Volontyorlik") return "volontyorlik";
    if (uiLabel == "Yutuqlar") return "yutuqlar";
    if (uiLabel == "Boshqa") return "boshqa";
    return uiLabel.toLowerCase();
  }

  List<SocialActivity> _getFilteredActivities() {
    return _activities.where((a) {
      if (_selectedCategory == "Barchasi") {
         // Keep going
      } else {
         final requiredKey = _getCategoryKey(_selectedCategory);
         // Backend ensures lowercase, but let's be safe
         if (a.category.toLowerCase() != requiredKey.toLowerCase()) {
           return false;
         }
      }
      
      if (_selectedStatus != "Barchasi") {
        if (_selectedStatus == "Tasdiqlangan") {
            if (a.status != "approved") return false;
        } else if (_selectedStatus == "Kutilayotgan") {
            if (a.status != "pending") return false;
        } else if (_selectedStatus == "Rad etilgan") {
            if (a.status != "rejected") return false;
        }
      }
      return true;
    }).toList();
  }

  void _showRegistrationAlert() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Diqqat! 🔒"),
        content: const Text("Faollik qo'shish uchun avval Telegram botimizdan ro'yxatdan o'tishingiz kerak.\n\nBu sizning shaxsingizni tasdiqlash uchun zarur."),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Yopish", style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryBlue),
            onPressed: () async {
                Navigator.pop(ctx);
                final Uri url = Uri.parse("https://t.me/talabahamkorbot");
                if (await canLaunchUrl(url)) {
                  await launchUrl(url, mode: LaunchMode.externalApplication);
                } else {
                  if (ctx.mounted) {
                     ScaffoldMessenger.of(ctx).showSnackBar(const SnackBar(content: Text("Botni ochib bo'lmadi. @talabahamkorbot ni qidiring.")));
                  }
                }
            }, 
            child: const Text("Botga o'tish", style: TextStyle(color: Colors.white)),
          )
        ],
      ),
    );
  }

  void _showAddActivitySheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => AddActivitySheet(
        categories: _categories.where((c) => c != "Barchasi").toList(),
        onSave: (activity, sessionId) async {
          try {
             String apiCat = _getCategoryKey(activity.category);

             final newActivity = await Provider.of<DataService>(context, listen: false).addActivity(
               apiCat, 
               activity.title, 
               activity.description, 
               activity.date,
               sessionId: sessionId
             );
             
             if (!mounted) return;
             ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Faollik muvaffaqiyatli yuborildi! Xodim tasdiqlashini kuting. ⏳')),
             );
             
             if (newActivity != null) {
                setState(() {
                  _activities.insert(0, newActivity);
                });
             } else {
                _loadActivities();
             }
             
          } catch(e) {
             if (!mounted) return;
             ScaffoldMessenger.of(context).showSnackBar(
               SnackBar(content: Text('Xatolik: $e')),
             );
          }
        },
      ),
    );
  }
  void _showEditSheet(SocialActivity activity) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => AddActivitySheet(
        categories: _categories.where((c) => c != "Barchasi").toList(),
        activity: activity,
        onSave: (updatedActivity, _) async {
           try {
             String apiCat = _getCategoryKey(updatedActivity.category);
             
             final res = await Provider.of<DataService>(context, listen: false).editActivity(
                updatedActivity.id,
                apiCat,
                updatedActivity.title,
                updatedActivity.description,
                updatedActivity.date
             );
             
             if (!mounted) return;
             if (res != null) {
               ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Faollik yangilandi!')));
               // Update locally
               setState(() {
                 final index = _activities.indexWhere((a) => a.id == updatedActivity.id);
                 if (index != -1) {
                   _activities[index] = res; // Use returned object directly which has correct image urls etc
                 } else {
                   _loadActivities();
                 }
               });
             }
           } catch (e) {
             if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Xatolik: $e')));
           }
        },
      ),
    );
  }

  Future<void> _deleteActivity(SocialActivity activity) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("O'chirish"),
        content: const Text("Haqiqatan ham ushbu faollikni o'chirmoqchimisiz?"),
        actions: [
           TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Yo'q", style: TextStyle(color: Colors.grey))),
           TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("Ha, o'chirish", style: TextStyle(color: Colors.red))),
        ],
      )
    );
    
    if (confirm == true) {
      try {
        final success = await Provider.of<DataService>(context, listen: false).deleteActivity(activity.id);
        if (success) {
           setState(() {
             _activities.removeWhere((a) => a.id == activity.id);
           });
           if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("O'chirildi!")));
        } else {
           if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Xatolik yuz berdi")));
        }
      } catch (e) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Xatolik: $e")));
      }
    }
  }

}

class ActivityCard extends StatefulWidget {
  final SocialActivity activity;
  final VoidCallback onTap;
  final Function(SocialActivity) onEdit;
  final Function(SocialActivity) onDelete;

  const ActivityCard({
    super.key, 
    required this.activity, 
    required this.onTap,
    required this.onEdit,
    required this.onDelete
  });

  @override
  State<ActivityCard> createState() => _ActivityCardState();
}

class _ActivityCardState extends State<ActivityCard> {
  int _currentIndex = 0;
  Timer? _timer;
  late PageController _pageController;
  int _virtualIndex = 0;

  @override
  void initState() {
    super.initState();
    // Start in the middle for infinite scrolling feel
    _virtualIndex = widget.activity.imageUrls.length > 1 ? 5000 : 0;
    _pageController = PageController(initialPage: _virtualIndex);
    
    _startAutoSlide();
  }

  void _startAutoSlide() {
    if (widget.activity.imageUrls.length > 1) {
      _timer?.cancel();
      _timer = Timer.periodic(const Duration(seconds: 4), (timer) {
        if (!mounted) return;
        _virtualIndex++;
        _pageController.animateToPage(
          _virtualIndex,
          duration: const Duration(milliseconds: 600),
          curve: Curves.easeInOut,
        );
      });
    }
  }

  void _stopAutoSlide() {
    _timer?.cancel();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    Color statusColor;
    String statusText;
    IconData statusIcon;

    switch(widget.activity.status) {
      case "approved":
        statusColor = Colors.green;
        statusText = "Tasdiqlangan";
        statusIcon = Icons.check_circle_rounded;
        break;
      case "rejected":
        statusColor = Colors.red;
        statusText = "Rad etilgan";
        statusIcon = Icons.cancel_rounded;
        break;
      default:
        statusColor = Colors.orange;
        statusText = "Kutilayotgan";
        statusIcon = Icons.access_time_rounded;
    }

    bool hasValidImage = widget.activity.imageUrls.isNotEmpty && widget.activity.imageUrls.first.startsWith("http");
    int imageCount = widget.activity.imageUrls.length;

    return GestureDetector(
      onTap: widget.onTap,
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
            Stack(
              children: [
                Container(
                  height: 200,
                  width: double.infinity,
                  color: Colors.grey[200],
                  child: hasValidImage
                      ? Listener(
                          onPointerDown: (_) => _stopAutoSlide(),
                          onPointerUp: (_) => _startAutoSlide(),
                          onPointerCancel: (_) => _startAutoSlide(),
                          child: PageView.builder(
                            controller: _pageController,
                            // Enable manual swipe (default physics)
                            itemCount: imageCount > 1 ? 10000 : 1, 
                            onPageChanged: (index) {
                               setState(() {
                                 _virtualIndex = index;
                                 _currentIndex = index % imageCount;
                               });
                            },
                            itemBuilder: (context, index) {
                               final realIndex = index % imageCount;
                               return CachedNetworkImage(
                                 imageUrl: widget.activity.imageUrls[realIndex],
                                 fit: BoxFit.cover,
                                 placeholder: (context, url) => const Center(child: CircularProgressIndicator()),
                                 errorWidget: (context, url, error) => const Center(child: Icon(Icons.broken_image, color: Colors.grey)),
                               );
                            },
                          ),
                        )
                      : const Center(child: Icon(Icons.image, color: Colors.grey, size: 40)),
                ),
                // Category Label
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
                      widget.activity.category.isNotEmpty 
                        ? "${widget.activity.category[0].toUpperCase()}${widget.activity.category.substring(1)}"
                        : widget.activity.category, 
                      style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold, fontSize: 12)
                    ),
                  ),
                ),
                // Pagination Dots (if multiple)
                if (imageCount > 1)
                  Positioned(
                    bottom: 12,
                    left: 0,
                    right: 0,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(imageCount, (index) {
                        return AnimatedContainer(
                          duration: const Duration(milliseconds: 300),
                          margin: const EdgeInsets.symmetric(horizontal: 3),
                          height: 6,
                          width: _currentIndex == index ? 16 : 6,
                          decoration: BoxDecoration(
                            color: _currentIndex == index ? Colors.white : Colors.white.withOpacity(0.5),
                            borderRadius: BorderRadius.circular(3),
                          ),
                        );
                      }),
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
                          Text(widget.activity.date, style: TextStyle(color: Colors.grey[500], fontSize: 13, fontWeight: FontWeight.w500)),
                        ],
                      ),
                      
                      // Status Badge & Menu
                      Row(
                        children: [
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
                          const SizedBox(width: 8),
                          
                          // 3-DOT MENU
                          Container(
                            width: 32,
                            height: 32,
                            margin: const EdgeInsets.only(left: 4),
                            child: PopupMenuButton<String>(
                              padding: EdgeInsets.zero,
                              icon: const Icon(Icons.more_vert, size: 22, color: Colors.black),
                              onSelected: (value) {
                                if (value == 'edit') {
                                  widget.onEdit(widget.activity);
                                } else if (value == 'delete') {
                                  widget.onDelete(widget.activity);
                                }
                              },
                              itemBuilder: (BuildContext context) => <PopupMenuEntry<String>>[
                                const PopupMenuItem<String>(
                                  value: 'edit',
                                  child: Row(
                                    children: [
                                      Icon(Icons.edit, color: Colors.blue, size: 20),
                                      SizedBox(width: 8),
                                      Text('Tahrirlash'),
                                    ],
                                  ),
                                ),
                                const PopupMenuItem<String>(
                                  value: 'delete',
                                  child: Row(
                                    children: [
                                      Icon(Icons.delete, color: Colors.red, size: 20),
                                      SizedBox(width: 8),
                                      Text("O'chirish"),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          )
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    widget.activity.title, 
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
}
