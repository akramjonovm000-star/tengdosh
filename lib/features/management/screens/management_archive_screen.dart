import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';
import '../../../core/constants/api_constants.dart';

class ManagementArchiveScreen extends StatefulWidget {
  const ManagementArchiveScreen({super.key});

  @override
  State<ManagementArchiveScreen> createState() => _ManagementArchiveScreenState();
}

class _ManagementArchiveScreenState extends State<ManagementArchiveScreen> {
  final DataService _dataService = DataService();
  final TextEditingController _searchController = TextEditingController();
  
  List<dynamic> _documents = [];
  List<dynamic> _faculties = [];
  List<String> _specialties = [];
  List<String> _groups = [];
  
  // Filter States
  String? _selectedEducationType;
  String? _selectedEducationForm;
  String? _selectedCourse;
  int? _selectedFacultyId;
  String? _selectedSpecialty;
  String? _selectedGroup;
  String? _selectedTitle;
  
  bool _isLoading = true;
  int _currentPage = 1;
  bool _hasMore = true;

  final List<Map<String, dynamic>> _categories = [
    {"id": null, "name": "Hammasi", "icon": Icons.all_inclusive_rounded},
    {"id": "Passport", "name": "Passport", "icon": Icons.credit_card_rounded},
    {"id": "Diplom", "name": "Diplom", "icon": Icons.school_rounded},
    {"id": "Rezyume", "name": "Rezyume", "icon": Icons.work_outline_rounded},
    {"id": "Obyektivka", "name": "Obyektivka", "icon": Icons.assignment_ind_rounded},
    {"id": "Boshqa", "name": "Boshqa", "icon": Icons.folder_shared_rounded},
  ];

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      _dataService.getManagementFaculties(),
      _dataService.getManagementDocuments(page: 1),
    ]);
    
    setState(() {
      _faculties = results[0] as List<dynamic>;
      final docResult = results[1] as Map<String, dynamic>;
      _documents = docResult['data'] ?? [];
      _isLoading = false;
      _hasMore = _documents.length >= 50;
    });
    _loadSpecialties();
    _loadGroups();
  }

  Future<void> _loadSpecialties() async {
    try {
      final specs = await _dataService.getManagementSpecialties(facultyId: _selectedFacultyId);
      setState(() {
        _specialties = List<String>.from(specs);
      });
    } catch (_) {}
  }

  Future<void> _loadGroups() async {
    try {
      final groups = await _dataService.getManagementGroups(
        facultyId: _selectedFacultyId,
        levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
      );
      setState(() {
        _groups = List<String>.from(groups);
      });
    } catch (_) {}
  }

  Future<void> _loadDocuments({bool refresh = false}) async {
    if (refresh) {
      setState(() {
        _currentPage = 1;
        _isLoading = true;
      });
    }

    final result = await _dataService.getManagementDocuments(
      query: _searchController.text,
      facultyId: _selectedFacultyId,
      title: _selectedTitle,
      educationType: _selectedEducationType,
      educationForm: _selectedEducationForm,
      levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
      specialtyName: _selectedSpecialty,
      groupNumber: _selectedGroup,
      page: _currentPage,
    );

    setState(() {
      if (refresh) {
        _documents = result['data'] ?? [];
      } else {
        _documents.addAll(result['data'] ?? []);
      }
      _isLoading = false;
      _hasMore = (result['data'] as List).length >= 50;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Hujjatlar Arxivi", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        actions: [
          if (_selectedEducationType != null || 
              _selectedEducationForm != null || 
              _selectedCourse != null || 
              _selectedFacultyId != null || 
              _selectedSpecialty != null || 
              _selectedGroup != null || 
              _selectedTitle != null ||
              _searchController.text.isNotEmpty)
            TextButton(
              onPressed: () {
                setState(() {
                  _selectedEducationType = null;
                  _selectedEducationForm = null;
                  _selectedCourse = null;
                  _selectedFacultyId = null;
                  _selectedSpecialty = null;
                  _selectedGroup = null;
                  _selectedTitle = null;
                  _searchController.clear();
                });
                _loadDocuments(refresh: true);
              },
              child: const Text("Tozalash", style: TextStyle(color: Colors.red, fontSize: 13)),
            ),
          IconButton(
            icon: const Icon(Icons.archive_outlined, color: Colors.blue),
            onPressed: _isLoading ? null : _exportZip,
            tooltip: "ZIP yuklab olish",
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          _buildFilters(),

          Expanded(
            child: _isLoading && _currentPage == 1
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: () => _loadDocuments(refresh: true),
                    child: _documents.isEmpty
                        ? _buildEmptyState()
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _documents.length + (_hasMore ? 1 : 0),
                            itemBuilder: (context, index) {
                              if (index == _documents.length) {
                                _currentPage++;
                                _loadDocuments();
                                return const Center(child: Padding(padding: EdgeInsets.all(8.0), child: CircularProgressIndicator()));
                              }
                              return _buildDocumentCard(_documents[index]);
                            },
                          ),
                  ),
          ),
        ],
      ),
    );
  }

  Future<void> _exportZip() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("ZIP Export"),
        content: Text("Tanlangan filtrlar bo'yicha barcha hujjatlarni ZIP arxiv ko'rinishida Telegramingizga yuborilsinmi?\n\nFiltr: ${_selectedTitle ?? 'Barchasi'}"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("Bekor qilish")),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text("Yuborish")),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _isLoading = true);
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ZIP arxiv tayyorlanmoqda, kuting...")));

    final result = await _dataService.exportManagementDocumentsZip(
      query: _searchController.text,
      facultyId: _selectedFacultyId,
      title: _selectedTitle,
      educationType: _selectedEducationType,
      educationForm: _selectedEducationForm,
      levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
      specialtyName: _selectedSpecialty,
      groupNumber: _selectedGroup,
    );

    setState(() => _isLoading = false);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['message'] ?? "Xatolik"),
          backgroundColor: result['success'] == true ? Colors.green : Colors.red,
        ),
      );
    }
  }

  Widget _buildFilters() {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      child: Column(
        children: [
          // Search Field
          TextField(
            controller: _searchController,
            onSubmitted: (val) => _loadDocuments(refresh: true),
            decoration: InputDecoration(
              hintText: "Ism yoki hujjat nomi...",
              prefixIcon: const Icon(Icons.search),
              filled: true,
              fillColor: Colors.grey[50],
              contentPadding: const EdgeInsets.symmetric(vertical: 0),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
            ),
          ),
          const SizedBox(height: 8),

          // Row 1: Turi | Fakultet | Shakli
          Row(
            children: [
              Expanded(
                child: _buildInlineDropdown<String>(
                  hint: "Turi",
                  value: _selectedEducationType,
                  items: ["Bakalavr", "Magistr"].map((e) => DropdownMenuItem(value: e, child: Text(e, style: const TextStyle(fontSize: 11)))).toList(),
                  onChanged: (val) {
                    setState(() {
                      _selectedEducationType = val;
                      _selectedCourse = null;
                      _selectedGroup = null;
                    });
                    _loadGroups();
                    _loadDocuments(refresh: true);
                  },
                ),
              ),
              const SizedBox(width: 4),
              Expanded(
                child: _buildInlineDropdown<int>(
                  hint: "Fakultet",
                  value: _faculties.any((f) => f['id'] == _selectedFacultyId) ? _selectedFacultyId : null,
                  items: _faculties.map((f) => DropdownMenuItem<int>(
                    value: f['id'],
                    child: Text(f['name'] ?? "", overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 11)),
                  )).toList(),
                  onChanged: (val) {
                    setState(() {
                      _selectedFacultyId = val;
                      _selectedSpecialty = null;
                      _selectedGroup = null;
                    });
                    _loadSpecialties();
                    _loadGroups();
                    _loadDocuments(refresh: true);
                  },
                ),
              ),
              const SizedBox(width: 4),
              Expanded(
                child: _buildInlineDropdown<String>(
                  hint: "Shakli",
                  value: _selectedEducationForm,
                  items: ["Kunduzgi", "Masofaviy", "Kechki", "Sirtqi"].map((e) => DropdownMenuItem(value: e, child: Text(e, style: const TextStyle(fontSize: 11)))).toList(),
                  onChanged: (val) {
                    setState(() => _selectedEducationForm = val);
                    _loadDocuments(refresh: true);
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Row 2: Kurs | Yo'nalish | Guruh
          Row(
            children: [
              Expanded(
                child: _buildInlineDropdown<String>(
                  hint: "Kurs",
                  value: (_selectedCourse != null && _selectedEducationType != null) ? "${_selectedEducationType}_$_selectedCourse" : null,
                  items: [
                    if (_selectedEducationType == null || _selectedEducationType == "Bakalavr")
                      ...["1", "2", "3", "4"].map((e) => DropdownMenuItem(value: "Bakalavr_$e", child: Text("$e-kurs", style: const TextStyle(fontSize: 11)))),
                    if (_selectedEducationType == null || _selectedEducationType == "Magistr")
                      ...["1", "2"].map((e) => DropdownMenuItem(value: "Magistr_$e", child: Text("$e-kurs (M)", style: const TextStyle(fontSize: 11)))),
                  ],
                  onChanged: (val) {
                    if (val != null) {
                      final parts = val.split('_');
                      setState(() {
                        _selectedEducationType = parts[0];
                        _selectedCourse = parts[1];
                      });
                      _loadGroups();
                      _loadDocuments(refresh: true);
                    }
                  },
                ),
              ),
              const SizedBox(width: 4),
              Expanded(
                child: _buildInlineDropdown<String>(
                  hint: "Yo'nalish",
                  value: _specialties.contains(_selectedSpecialty) ? _selectedSpecialty : null,
                  items: _specialties.map((s) => DropdownMenuItem(
                    value: s,
                    child: Text(s, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 11)),
                  )).toList(),
                  onChanged: (val) {
                    setState(() => _selectedSpecialty = val);
                    _loadDocuments(refresh: true);
                  },
                ),
              ),
              const SizedBox(width: 4),
              Expanded(
                child: _buildInlineDropdown<String>(
                  hint: "Guruh",
                  value: _groups.contains(_selectedGroup) ? _selectedGroup : null,
                  items: _groups.map((g) => DropdownMenuItem(
                    value: g,
                    child: Text(g, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 11)),
                  )).toList(),
                  onChanged: (val) {
                    setState(() => _selectedGroup = val);
                    _loadDocuments(refresh: true);
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Category Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: _categories.map((cat) {
                final isSelected = _selectedTitle == cat['id'];
                return Padding(
                  padding: const EdgeInsets.only(right: 8.0),
                  child: FilterChip(
                    label: Text(cat['name']),
                    selected: isSelected,
                    onSelected: (val) {
                      setState(() => _selectedTitle = val ? cat['id'] : null);
                      _loadDocuments(refresh: true);
                    },
                    selectedColor: AppTheme.primaryBlue.withOpacity(0.2),
                    checkmarkColor: AppTheme.primaryBlue,
                    labelStyle: TextStyle(
                      color: isSelected ? AppTheme.primaryBlue : Colors.black87,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInlineDropdown<T>({
    required String hint,
    required T? value,
    required List<DropdownMenuItem<T>> items,
    required ValueChanged<T?> onChanged,
  }) {
    return Container(
      height: 36,
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey[200]!),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 6),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          isExpanded: true,
          hint: Text(hint, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
          value: value,
          items: items,
          onChanged: onChanged,
          icon: const Icon(Icons.arrow_drop_down, size: 18),
        ),
      ),
    );
  }

  }

  Widget _buildDocumentCard(dynamic doc) {
    final student = doc['student'] ?? {};
    final date = doc['created_at'] != null ? doc['created_at'].toString().split('T')[0] : '';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        doc['title'] ?? 'Nomsiz hujjat',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        "${student['full_name'] ?? 'Noma\'lum talaba'}",
                        style: TextStyle(color: AppTheme.primaryBlue, fontSize: 13, fontWeight: FontWeight.w500),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.telegram_rounded, color: Colors.blue),
                  onPressed: () => _downloadDoc(doc['id']),
                  tooltip: "Telegramga yuborish",
                ),
              ],
            ),
            const Divider(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("Guruh", style: TextStyle(color: Colors.grey[500], fontSize: 11)),
                      Text(
                        student['group_number'] ?? '-',
                        style: const TextStyle(fontSize: 13),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text("Sana", style: TextStyle(color: Colors.grey[500], fontSize: 11)),
                    Text(date, style: const TextStyle(fontSize: 13)),
                  ],
                ),
              ],
            ),
            if (student['faculty_name'] != null) ...[
              const SizedBox(height: 8),
              Text(
                student['faculty_name'],
                style: TextStyle(color: Colors.grey[600], fontSize: 11, fontStyle: FontStyle.italic),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _downloadDoc(int docId) async {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Telegramga yuborilmoqda...")));
    final result = await _dataService.downloadStudentDocumentForManagement(docId);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result ?? "Xatolik"),
          backgroundColor: result != null && result.contains("yuborildi") ? Colors.green : Colors.red,
        ),
      );
    }
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inventory_2_outlined, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text("Hujjatlar topilmadi", style: TextStyle(color: Colors.grey[500], fontSize: 16)),
        ],
      ),
    );
  }
}
