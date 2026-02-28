import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/core/localization/app_dictionary.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:talabahamkor_mobile/core/constants/api_constants.dart';

class AddGroupActivitySheet extends StatefulWidget {
  final VoidCallback onSaved;

  const AddGroupActivitySheet({Key? key, required this.onSaved}) : super(key: key);

  @override
  State<AddGroupActivitySheet> createState() => _AddGroupActivitySheetState();
}

class _AddGroupActivitySheetState extends State<AddGroupActivitySheet> {
  final _pageController = PageController();
  int _currentPage = 0;

  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  final _dateController = TextEditingController();
  
  String _selectedCategory = "Faollik";
  DateTime _selectedDate = DateTime.now();
  
  final List<String> _categories = [
    "Faollik", "Sport", "Madaniyat", "Ma'naviyat", "Zakovot", "Ilmiy", "Boshqa"
  ];

  String? _uploadSessionId;
  bool _isUploading = false;
  int _uploadedCount = 0;
  Timer? _pollingTimer;

  bool _isLoading = true;
  bool _isSaving = false;
  List<dynamic> _groups = [];
  Map<String, List<dynamic>> _groupStudents = {};
  
  // Track selected students by their ID
  final Set<int> _selectedStudentIds = {};
  
  // Track currently viewed group
  String? _activeGroup;

  @override
  void initState() {
    super.initState();
    _dateController.text = "${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}";
    _loadGroupsAndStudents();
  }

  @override
  void dispose() {
    _pageController.dispose();
    _pollingTimer?.cancel();
    _titleController.dispose();
    _descController.dispose();
    _dateController.dispose();
    super.dispose();
  }

  Future<void> _loadGroupsAndStudents() async {
    setState(() => _isLoading = true);
    try {
      final groupsStats = await Provider.of<DataService>(context, listen: false).getTutorActivityStats();
      if (groupsStats != null) {
        _groups = groupsStats;
        for (var group in groupsStats) {
           String gName = group['group_number'].toString();
           final res = await Provider.of<DataService>(context, listen: false).getGroupDocumentDetails(gName);
           if (res != null) {
             _groupStudents[gName] = res;
           }
        }
      }
    } catch (e) {
      debugPrint("Error loading groups: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _initUpload(String sessionId) async {
    setState(() {
      _uploadSessionId = sessionId;
      _isUploading = true;
      _uploadedCount = 0;
    });

    try {
      final res = await Provider.of<DataService>(context, listen: false).tutorInitUploadSession(
        sessionId,
        _selectedCategory
      );
      
      if (res['success'] == true || res['requires_auth'] == true) {
         String urlToLaunch = res['requires_auth'] == true ? res['auth_link'] : (res['bot_link'] ?? "https://t.me/talabahamkorbot");
         if (await canLaunchUrl(Uri.parse(urlToLaunch))) {
           await launchUrl(Uri.parse(urlToLaunch), mode: LaunchMode.externalApplication);
         } else {
            if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppDictionary.tr(context, 'msg_cannot_open_tg'))));
         }
      }
      
      _pollingTimer?.cancel();
      _checkStatus(sessionId);
      _pollingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
         _checkStatus(sessionId);
      });
      
    } catch (e) {
      debugPrint("Upload Init Error: $e");
      setState(() => _isUploading = false);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("${AppDictionary.tr(context, 'error_prefix')}: $e")));
    }
  }

  Future<void> _checkStatus(String sessionId) async {
    try {
      final res = await Provider.of<DataService>(context, listen: false).tutorCheckUploadStatus(sessionId);
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

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      builder: (context, child) {
        return Theme(
          data: ThemeData.light().copyWith(
            colorScheme: ColorScheme.light(primary: AppTheme.primaryBlue),
          ),
          child: child!,
        );
      },
    );
    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
        _dateController.text = "${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}";
      });
    }
  }

  Future<void> _saveActivity() async {
    if (_selectedStudentIds.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Iltimos, kamida bitta talabani tanlang!"))
      );
      return;
    }

    setState(() => _isSaving = true);
    
    try {
      final res = await Provider.of<DataService>(context, listen: false).createTutorBulkActivities(
        category: _selectedCategory,
        name: _titleController.text,
        description: _descController.text,
        date: _dateController.text,
        studentIds: _selectedStudentIds.toList(),
        sessionId: _uploadedCount > 0 ? _uploadSessionId : null,
      );
      
      if (mounted) {
        // Assume created_count comes back in res['created_count'] or similar
        final cnt = res['created_count'] ?? _selectedStudentIds.length;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("✅ $cnt ta talabaga faollik muvaffaqiyatli saqlandi!"),
            backgroundColor: Colors.green,
          )
        );
        widget.onSaved();
        Navigator.pop(context);
      }
    } catch (e) {
      debugPrint("Error saving bulk activity: $e");
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("❌ Saqlashda xatolik yuz berdi: $e"), backgroundColor: Colors.red)
        );
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  void _nextPage() {
    if (_currentPage == 0 && !_formKey.currentState!.validate()) return;
    
    _pageController.nextPage(
      duration: const Duration(milliseconds: 300), 
      curve: Curves.easeInOut
    );
    setState(() {
      _currentPage++;
    });
  }

  void _prevPage() {
    if (_currentPage == 2) {
      // Going back from specific group students to groups list
      setState(() {
        _currentPage = 1;
        _activeGroup = null;
      });
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300), 
        curve: Curves.easeInOut
      );
    } else {
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300), 
        curve: Curves.easeInOut
      );
      setState(() {
        _currentPage--;
      });
    }
  }

  Widget _buildStepOneDetails() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Faollik Kategoriyasi", style: TextStyle(fontWeight: FontWeight.w500)),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey[300]!),
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  isExpanded: true,
                  value: _categories.contains(_selectedCategory) ? _selectedCategory : null,
                  hint: const Text("Kategoriyani tanlang"),
                  items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                  onChanged: (v) {
                    if (v != null) setState(() => _selectedCategory = v);
                  },
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            TextFormField(
              controller: _titleController,
              decoration: InputDecoration(
                labelText: "Faollik Nomi",
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
              validator: (v) => v!.isEmpty ? "Nomini kiriting" : null,
            ),
            const SizedBox(height: 16),
            
            TextFormField(
              controller: _descController,
              maxLines: 3,
              decoration: InputDecoration(
                labelText: "Faollik Tafsifi",
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
              validator: (v) => v!.isEmpty ? "Tafsif kiriting" : null,
            ),
            const SizedBox(height: 16),
            
            TextFormField(
              controller: _dateController,
              readOnly: true,
              onTap: _pickDate,
              decoration: InputDecoration(
                labelText: "Sana",
                suffixIcon: const Icon(Icons.calendar_today),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
            ),
            const SizedBox(height: 20),
            
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue.withOpacity(0.05),
                border: Border.all(color: Colors.blue.withOpacity(0.2)),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  const Icon(Icons.photo_library, size: 40, color: AppTheme.primaryBlue),
                  const SizedBox(height: 8),
                  if (_uploadedCount > 0)
                    Text(
                      "$_uploadedCount/5 ta rasm yuklandi",
                      style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.green),
                    )
                  else if (_isUploading)
                    const Column(
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 8),
                        Text("TalabahamkorBot orqali rasm yuboring...", textAlign: TextAlign.center),
                      ],
                    )
                  else
                    const Text(
                      "Suratlarni yuklash (5 tagacha)",
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey),
                    ),
                  const SizedBox(height: 12),
                  if (_uploadedCount < 5)
                    ElevatedButton.icon(
                      onPressed: () {
                        if (_uploadSessionId == null) {
                          _initUpload(const Uuid().v4());
                        } else {
                          _initUpload(_uploadSessionId!);
                        }
                      },
                      icon: const Icon(Icons.telegram, color: Colors.white),
                      label: Text(_isUploading ? "Botni ochish" : "Telegram orqali yuklash"),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF0088CC),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }

  Widget _buildStepTwoGroupsList() {
    if (_isLoading) {
      return const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator()));
    }
    
    if (_groups.isEmpty) {
      return const Center(child: Padding(padding: EdgeInsets.all(20), child: Text("Guruhlar topilmadi.")));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _groups.length,
      itemBuilder: (context, index) {
        final g = _groups[index];
        final gName = g['group_number'].toString();
        final students = _groupStudents[gName] ?? [];
        
        int selectedInGroup = 0;
        for (var s in students) {
          if (_selectedStudentIds.contains(s['id'])) selectedInGroup++;
        }

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.grey.withOpacity(0.2)),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: CircleAvatar(
              backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
              foregroundColor: AppTheme.primaryBlue,
              radius: 20,
              child: const Icon(Icons.group),
            ),
            title: Text(gName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            subtitle: Text("$selectedInGroup/${students.length} talaba tanlandi"),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              setState(() {
                _activeGroup = gName;
                _currentPage = 2; // Jump to specific group
              });
              _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
            },
          ),
        );
      },
    );
  }

  Widget _buildStepThreeGroupStudents() {
    if (_activeGroup == null) return const SizedBox();
    
    final students = _groupStudents[_activeGroup!] ?? [];
    
    int selectedInGroup = 0;
    for (var s in students) {
      if (_selectedStudentIds.contains(s['id'])) selectedInGroup++;
    }
    bool allSelected = students.isNotEmpty && selectedInGroup == students.length;

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("$_activeGroup Guruhi", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              TextButton.icon(
                onPressed: () {
                  setState(() {
                    if (allSelected) {
                      for (var s in students) _selectedStudentIds.remove(s['id']);
                    } else {
                      for (var s in students) _selectedStudentIds.add(s['id']);
                    }
                  });
                },
                icon: Icon(allSelected ? Icons.check_box : Icons.check_box_outline_blank, color: AppTheme.primaryBlue),
                label: const Text("Barchasi"),
              )
            ],
          ),
        ),
        const Divider(),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.only(bottom: 80),
            itemCount: students.length,
            separatorBuilder: (context, index) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final s = students[index];
              final id = s['id'] as int;
              final isSelected = _selectedStudentIds.contains(id);
              
              return ListTile(
                onTap: () {
                  setState(() {
                    if (isSelected) _selectedStudentIds.remove(id);
                    else _selectedStudentIds.add(id);
                  });
                },
                contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                leading: CircleAvatar(
                  radius: 20,
                  backgroundImage: s['image'] != null
                      ? CachedNetworkImageProvider(s['image'].toString().startsWith('http') ? s['image'] : '${ApiConstants.backendUrl}/files/${s['image']}')
                      : null,
                  backgroundColor: Colors.grey[200],
                  child: s['image'] == null ? const Icon(Icons.person, size: 20, color: Colors.grey) : null,
                ),
                title: Text(s['full_name'] ?? 'Noma\'lum', style: const TextStyle(fontWeight: FontWeight.w500)),
                subtitle: Text((s['hemis_id'] ?? '').toString()),
                trailing: Checkbox(
                  value: isSelected,
                  activeColor: AppTheme.primaryBlue,
                  onChanged: (val) {
                    setState(() {
                      if (val == true) _selectedStudentIds.add(id);
                      else _selectedStudentIds.remove(id);
                    });
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.9,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        children: [
          // Handle
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          
          // Header
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            child: Row(
              children: [
                if (_currentPage > 0)
                  IconButton(
                    icon: const Icon(Icons.arrow_back),
                    onPressed: _prevPage,
                  )
                else
                  const SizedBox(width: 48), // Balance for back button space
                  
                Expanded(
                  child: Text(
                    _currentPage == 0 
                      ? "Yangi Faollik Qo'shish" 
                      : (_currentPage == 1 ? "Guruhlarni Tanlash" : "Talabalarni Tanlash"),
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textBlack,
                    ),
                  ),
                ),
                
                const SizedBox(width: 48), // Balance spacing
              ],
            ),
          ),
          
          const Divider(),
          
          // Pages
          Expanded(
            child: PageView(
              controller: _pageController,
              physics: const NeverScrollableScrollPhysics(), // Disable swipe to force button navigation
              children: [
                _buildStepOneDetails(),
                _buildStepTwoGroupsList(),
                _buildStepThreeGroupStudents(),
              ],
            ),
          ),
          
          // Bottom Navigation Area
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: SizedBox(
                width: double.infinity,
                child: _currentPage == 0
                    ? ElevatedButton(
                        onPressed: _nextPage,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryBlue,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: const Text("Keyingisi", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      )
                    : ElevatedButton(
                        onPressed: _isSaving ? null : _saveActivity,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryBlue,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: _isSaving
                            ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                            : Text(
                                "Saqlash (${_selectedStudentIds.length} ta)",
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
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
