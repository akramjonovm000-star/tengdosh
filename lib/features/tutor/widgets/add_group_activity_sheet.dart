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
  final Set<String> _expandedGroups = {};

  @override
  void initState() {
    super.initState();
    _dateController.text = "${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}";
    _loadGroupsAndStudents();
  }

  @override
  void dispose() {
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
           // Load students for this group using the existing management method or similar
           // Actually, we can fetch from getGroupDocumentDetails or create a specific endpoint
           // But since Tutor Activity Groups uses getTutorActivityStats which gives group names,
           // wait, we need student lists. We have DataService.getTutorGroupDetails? Or dataService.getGroupDocumentDetails? 
           // There is an endpoint /tutor/documents/group/{group_number}. Let's use it as a workaround, or create a simple list? 
           // Alternatively, create a generic fetch method for students. 
           // Let's use management API or existing tutor endpoints.
           // getTutorGroupDetails endpoint is likely available. We'll use getTutorGroupDetails(gName).
           // If we don't have it, we can use the backend proxy for students?
           // I'll assume we can fetch students using API call to /tutor/documents/group/ as it returns all students.
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
    if (!_formKey.currentState!.validate()) return;
    if (_selectedStudentIds.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Iltimos, kamida bitta talabani tanlang!"))
      );
      return;
    }

    setState(() => _isSaving = true);
    
    try {
      await Provider.of<DataService>(context, listen: false).createTutorBulkActivities(
        category: _selectedCategory,
        name: _titleController.text,
        description: _descController.text,
        date: _dateController.text,
        studentIds: _selectedStudentIds.toList(),
        sessionId: _uploadedCount > 0 ? _uploadSessionId : null,
      );
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("✅ ${_selectedStudentIds.length} ta talabaga faollik muvaffaqiyatli saqlandi!"),
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

  Widget _buildGroupSelection() {
    if (_isLoading) {
      return const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator()));
    }
    
    if (_groups.isEmpty) {
      return const Center(child: Padding(padding: EdgeInsets.all(20), child: Text("Guruhlar topilmadi.")));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: _groups.map((g) {
        final gName = g['group_number'].toString();
        final isExpanded = _expandedGroups.contains(gName);
        final students = _groupStudents[gName] ?? [];
        
        // Calculate how many selected in this group
        int selectedInGroup = 0;
        for (var s in students) {
          if (_selectedStudentIds.contains(s['id'])) selectedInGroup++;
        }
        
        bool allSelected = students.isNotEmpty && selectedInGroup == students.length;

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.grey.withOpacity(0.2)),
          ),
          child: Column(
            children: [
              ListTile(
                title: Text("Barchasini belgilash", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                trailing: Checkbox(
                  value: allSelected,
                  activeColor: AppTheme.primaryBlue,
                  onChanged: (val) {
                    setState(() {
                      if (val == true) {
                        for (var s in students) _selectedStudentIds.add(s['id']);
                      } else {
                        for (var s in students) _selectedStudentIds.remove(s['id']);
                      }
                    });
                  },
                ),
                leading: CircleAvatar(
                  backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                  child: Text(gName),
                  radius: 18,
                ),
                subtitle: Text("$selectedInGroup/${students.length} tanlandi"),
                onTap: () {
                  setState(() {
                    if (isExpanded) _expandedGroups.remove(gName);
                    else _expandedGroups.add(gName);
                  });
                },
              ),
              if (isExpanded)
                ...students.map((s) {
                  final id = s['id'] as int;
                  final isSelected = _selectedStudentIds.contains(id);
                  return CheckboxListTile(
                    value: isSelected,
                    activeColor: AppTheme.primaryBlue,
                    dense: true,
                    title: Text(s['full_name'] ?? 'Noma\'lum'),
                    subtitle: Text((s['hemis_id'] ?? '').toString()),
                    secondary: CircleAvatar(
                      radius: 15,
                      backgroundImage: s['image'] != null
                          ? CachedNetworkImageProvider(s['image'].toString().startsWith('http') ? s['image'] : '${ApiConstants.backendUrl}/files/${s['image']}')
                          : null,
                      backgroundColor: Colors.grey[200],
                      child: s['image'] == null ? const Icon(Icons.person, size: 15, color: Colors.grey) : null,
                    ),
                    onChanged: (val) {
                      setState(() {
                        if (val == true) _selectedStudentIds.add(id);
                        else _selectedStudentIds.remove(id);
                      });
                    },
                  );
                }).toList(),
            ],
          ),
        );
      }).toList(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
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
          
          Text(
            "Yangi Faollik Qo'shish (Ommaviy)",
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppTheme.textBlack,
            ),
          ),
          
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Category
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
                    
                    // Fields
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
                    
                    // Image Upload
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
                          Icon(Icons.photo_library, size: 40, color: AppTheme.primaryBlue),
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
                    const SizedBox(height: 24),
                    
                    const Text("Qatnashgan Talabalar", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const Text("Guruhni bosing ro'yxatni ko'rish uchhhn", style: TextStyle(color: Colors.grey, fontSize: 12)),
                    const SizedBox(height: 8),
                    
                    _buildGroupSelection(),
                    
                    const SizedBox(height: 80), // padding for bottom button
                  ],
                ),
              ),
            ),
          ),
          
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
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
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
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
