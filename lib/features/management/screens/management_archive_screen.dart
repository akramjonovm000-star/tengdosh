import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  
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
  String _selectedTitle = "Hujjatlar"; // Default
  
  bool _isLoading = true;
  int _currentPage = 1;
  bool _hasMore = true;
  Map<String, dynamic> _stats = {};

  final List<Map<String, dynamic>> _categories = [
    {"id": "Hujjatlar", "name": "Hujjatlar", "icon": Icons.assignment_rounded},
    {"id": "Passport", "name": "Passport", "icon": Icons.credit_card_rounded},
    {"id": "Diplom", "name": "Diplom", "icon": Icons.school_rounded},
    {"id": "Rezyume", "name": "Rezyume", "icon": Icons.work_outline_rounded},
    {"id": "Obyektivka", "name": "Obyektivka", "icon": Icons.assignment_ind_rounded},
    {"id": "Sertifikatlar", "name": "Sertifikatlar", "icon": Icons.workspace_premium_rounded},
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
      _dataService.getManagementDocuments(page: 1, title: _selectedTitle),
    ]);
    
    setState(() {
      _faculties = results[0] as List<dynamic>;
      final docResult = results[1] as Map<String, dynamic>;
      _documents = docResult['data'] ?? [];
      _stats = docResult['stats'] ?? {};
      _isLoading = false;
      _hasMore = _documents.length >= 50;
    });
    _loadSpecialties();
    _loadGroups();
  }

  Future<void> _loadSpecialties() async {
    try {
      final specs = await _dataService.getManagementSpecialties(
        facultyId: _selectedFacultyId,
        educationType: _selectedEducationType,
      );
      setState(() => _specialties = List<String>.from(specs));
    } catch (_) {}
  }

  Future<void> _loadGroups() async {
    try {
      final groups = await _dataService.getManagementGroups(
        facultyId: _selectedFacultyId,
        levelName: _selectedCourse,
        educationType: _selectedEducationType,
        educationForm: _selectedEducationForm,
        specialtyName: _selectedSpecialty,
      );
      setState(() => _groups = List<String>.from(groups));
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
      levelName: _selectedCourse, 
      specialtyName: _selectedSpecialty,
      groupNumber: _selectedGroup,
      page: _currentPage,
    );

    setState(() {
      if (refresh) {
        _documents = result['data'] ?? [];
        _stats = result['stats'] ?? {};
      } else {
        _documents.addAll(result['data'] ?? []);
      }
      _isLoading = false;
      _hasMore = (result['data'] as List).length >= 50;
    });
  }

  void _resetFilters() {
    setState(() {
      _searchController.clear();
      _selectedEducationType = null;
      _selectedEducationForm = null;
      _selectedCourse = null;
      _selectedFacultyId = null;
      _selectedSpecialty = null;
      _selectedGroup = null;
      // Keep category as is or reset to "Hujjatlar"? Let's keep existing category logic slightly separate, 
      // but usually "Reset" means everything. Let's keep category as is for now as it's a tab.
    });
    // Reload lists without filters
    _loadSpecialties();
    _loadGroups();
    _loadDocuments(refresh: true);
  }

  // Filter Data
  final List<String> _educationTypes = ["Bakalavr", "Magistr"];
  final List<String> _educationForms = ["Kunduzgi", "Sirtqi", "Kechki"];
  final List<String> _courses = ["1-kurs", "2-kurs", "3-kurs", "4-kurs", "5-kurs", "6-kurs"];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: AppTheme.backgroundWhite,
      // endDrawer: _buildFilterDrawer(), // Removed old drawer
      body: CustomScrollView(
        physics: const BouncingScrollPhysics(),
        slivers: [
          _buildSliverAppBar(),
          


          // Search & Filters (New Redesign)
          SliverPersistentHeader(
            pinned: true,
            delegate: _PersistentHeaderDelegate(
              child: Container(
                color: AppTheme.backgroundWhite,
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Column(
                  children: [
                    _buildSearchBar(),
                    // _buildCategoryChips(), // Moved below or removed? User screenshot only showed search+grid.
                    // But we need Category Chips for "Passport" vs "Diplom" etc.
                    // Let's keep them, but maybe make it scrollable below instructions?
                    // Actually, let's put the chips inside the persistent header if space allows, 
                    // or just move them to SliverToBoxAdapter below?
                    // The user said "filter appearance... like this", implying the top section.
                    // The screenshot likely replaced the old Search+Chips area.
                    // I will put the chips BELOW the grid in the same header, expanding height.
                    const SizedBox(height: 8),
                    const SizedBox(height: 8),
                    _buildFilterGrid(),
                    const SizedBox(height: 8),
                    _buildCategoryChips(),
                    if (_stats.isNotEmpty) _buildFilterSummary(),
                  ],
                ),
              ),
              maxHeight: 280, 
              minHeight: 280, 
            ),
          ),

          // Document List
          _isLoading && _currentPage == 1
              ? const SliverFillRemaining(child: Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue)))
              : _documents.isEmpty
                  ? SliverFillRemaining(child: _buildEmptyState())
                  : SliverPadding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      sliver: SliverList(
                        delegate: SliverChildBuilderDelegate(
                          (context, index) {
                            if (index == _documents.length) {
                              _currentPage++;
                              _loadDocuments();
                              return const Center(child: Padding(padding: EdgeInsets.all(16.0), child: CircularProgressIndicator()));
                            }
                            return _buildEnhancedDocumentCard(_documents[index]);
                          },
                          childCount: _documents.length + (_hasMore ? 1 : 0),
                        ),
                      ),
                    ),
          
          // Bottom spacing for FAB
          const SliverToBoxAdapter(child: SizedBox(height: 80)),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _isLoading ? null : _exportZip,
        label: const Text("ZIP Export"),
        icon: const Icon(Icons.archive_outlined),
      ),
    );
  }

  Widget _buildSliverAppBar() {
    return SliverAppBar(
      expandedHeight: 80, // Reduced height since we have a tall filter section
      floating: false,
      pinned: true,
      backgroundColor: AppTheme.primaryBlue,
      elevation: 0,
      centerTitle: false,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
        onPressed: () => Navigator.pop(context),
      ),
      flexibleSpace: FlexibleSpaceBar(
        titlePadding: const EdgeInsets.only(left: 56, bottom: 16),
        centerTitle: false,
        title: const Text(
          "Arxiv",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 22),
        ),
        background: Container(color: AppTheme.primaryBlue),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh_rounded, color: Colors.white),
          onPressed: () => _loadDocuments(refresh: true),
        ),
        IconButton(
          icon: const Icon(Icons.cleaning_services_rounded, color: Colors.white, size: 20),
          onPressed: _resetFilters,
          tooltip: "Filtrlarni tozalash",
        ),
        const SizedBox(width: 8),
      ],
    );
  }

  Widget _buildFilterSummary() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
        decoration: BoxDecoration(
          color: AppTheme.primaryBlue.withOpacity(0.05),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: AppTheme.primaryBlue.withOpacity(0.1)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(children: [
              const Icon(Icons.people_alt_rounded, size: 16, color: Colors.blueGrey),
              const SizedBox(width: 4),
              Text(
                "Jami: ${_stats['students_in_scope'] ?? 0}",
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey),
              ),
            ]),
            Container(width: 1, height: 16, color: Colors.grey[300]),
            Row(children: [
              const Icon(Icons.cloud_done_rounded, size: 16, color: Colors.green),
              const SizedBox(width: 4),
              Text(
                "Yuklaganlar: ${_stats['students_with_uploads'] ?? 0}",
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.green),
              ),
            ]),
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.green),
              ),
            ]),
          ],
        ),
      ),
    );
  }



  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        height: 48,
        decoration: BoxDecoration(
          color: Colors.grey[100],
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey[300]!),
        ),
        child: TextField(
          controller: _searchController,
          onSubmitted: (val) => _loadDocuments(refresh: true),
          decoration: InputDecoration(
            hintText: "Ism yoki Hemis ID...",
            hintStyle: TextStyle(color: Colors.grey[500], fontSize: 14),
            prefixIcon: const Icon(Icons.search_rounded, color: Colors.grey),
            border: InputBorder.none,
            contentPadding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
      ),
    );
  }

  Widget _buildFilterGrid() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(child: _buildDropdownFilter("Turi", _selectedEducationType, _educationTypes, (v) {
                setState(() { _selectedEducationType = v; _selectedSpecialty = null; _selectedGroup = null; });
                _loadSpecialties();
                _loadGroups();
                _loadDocuments(refresh: true);
              })),
              const SizedBox(width: 8),
              Expanded(child: _buildDropdownFilter("Fakultet", _selectedFacultyId, _faculties.map((f) => {'id': f['id'], 'name': f['name']}).toList(), (v) {
                setState(() { _selectedFacultyId = v; _selectedSpecialty = null; _selectedGroup = null; });
                _loadSpecialties();
                _loadGroups();
                _loadDocuments(refresh: true);
              }, isFaculty: true)),
              const SizedBox(width: 8),
              Expanded(child: _buildDropdownFilter("Shakli", _selectedEducationForm, _educationForms, (v) {
                setState(() { _selectedEducationForm = v; });
                _loadDocuments(refresh: true);
              })),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(child: _buildDropdownFilter("Kurs", _selectedCourse, _courses, (v) {
                setState(() { _selectedCourse = v; });
                _loadDocuments(refresh: true);
              })),
              const SizedBox(width: 8),
              Expanded(child: _buildDropdownFilter("Yo'nalish", _selectedSpecialty, _specialties, (v) {
                setState(() { _selectedSpecialty = v; });
                _loadDocuments(refresh: true);
              })),
              const SizedBox(width: 8),
              Expanded(child: _buildDropdownFilter("Guruh", _selectedGroup, _groups, (v) {
                setState(() { _selectedGroup = v; });
                _loadDocuments(refresh: true);
              })),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDropdownFilter(String hint, dynamic value, List<dynamic> items, Function(dynamic) onChanged, {bool isFaculty = false}) {
    // Map items to DropdownMenuItem
    List<DropdownMenuItem<dynamic>> menuItems = [];
    if (isFaculty) {
       menuItems = items.map<DropdownMenuItem<dynamic>>((e) => DropdownMenuItem(value: e['id'], child: Text(e['name'], overflow: TextOverflow.ellipsis))).toList();
    } else {
       menuItems = items.map<DropdownMenuItem<dynamic>>((e) => DropdownMenuItem(value: e, child: Text(e, overflow: TextOverflow.ellipsis))).toList();
    }

    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<dynamic>(
          value: value,
          isExpanded: true,
          hint: Text(hint, style: TextStyle(fontSize: 12, color: Colors.grey[600]), overflow: TextOverflow.ellipsis),
          items: menuItems,
          onChanged: onChanged,
          icon: Icon(Icons.arrow_drop_down, color: Colors.grey[600], size: 18),
          style: const TextStyle(fontSize: 12, color: Colors.black),
        ),
      ),
    );
  }

  Widget _buildCategoryChips() {
    return SizedBox(
      height: 36,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        scrollDirection: Axis.horizontal,
        itemCount: _categories.length,
        itemBuilder: (context, index) {
          final cat = _categories[index];
          final isSelected = _selectedTitle == cat['id'];
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text(cat['name']),
              selected: isSelected,
              onSelected: (val) {
                setState(() => _selectedTitle = val ? cat['id'] : "Hujjatlar");
                _loadDocuments(refresh: true);
              },
              backgroundColor: AppTheme.surfaceWhite,
              selectedColor: AppTheme.primaryBlue,
              checkmarkColor: Colors.white,
              labelStyle: TextStyle(
                color: isSelected ? Colors.white : AppTheme.textBlack,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                fontSize: 11,
              ),
              padding: EdgeInsets.zero,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: BorderSide(color: isSelected ? Colors.transparent : Colors.grey[300]!, width: 1),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildEnhancedDocumentCard(dynamic doc) {
    final student = doc['student'] ?? {};
    final bool isCert = doc['is_certificate'] == true;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceWhite,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.black.withOpacity(0.05)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 4, offset: const Offset(0, 2))],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => _showDocumentActions(doc),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: (isCert ? Colors.amber : Colors.blue).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    isCert ? Icons.workspace_premium_rounded : Icons.description_outlined,
                    color: isCert ? Colors.amber[800] : Colors.blue[700],
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        doc['title'] ?? 'Nomsiz',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        student['full_name'] ?? 'Talaba',
                        style: TextStyle(color: Colors.grey[800], fontWeight: FontWeight.w500, fontSize: 12),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        "${student['faculty_name'] ?? ''} ${student['group_number'] ?? ''}",
                        style: TextStyle(color: Colors.grey[500], fontSize: 10),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.download_rounded, color: Colors.blue[600], size: 20),
                  onPressed: () => _downloadDoc(doc),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Helper Widgets (Action Icon, Show Actions) Remain Clean...
  Widget _buildActionIcon(IconData icon, Color color, String label, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Icon(icon, color: color, size: 20),
      ),
    );
  }

  void _showDocumentActions(dynamic doc) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 24),
            Text(doc['title'] ?? 'Hujjat', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16), textAlign: TextAlign.center),
            const SizedBox(height: 8),
            Text(doc['student']['full_name'] ?? '', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
            const SizedBox(height: 24),
            ListTile(
              leading: const CircleAvatar(backgroundColor: Colors.blue, child: Icon(Icons.telegram, color: Colors.white, size: 20)),
              title: const Text("Bot orqali yuborish"),
              onTap: () { Navigator.pop(context); _downloadDoc(doc); },
            ),
            ListTile(
              leading: CircleAvatar(backgroundColor: Colors.grey[100], child: Icon(Icons.copy_rounded, color: Colors.grey[700], size: 20)),
              title: const Text("HEMIS ID nusxalash"),
              onTap: () {
                Clipboard.setData(ClipboardData(text: doc['student']['hemis_id'] ?? ''));
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("HEMIS ID nusxalandi")));
              },
            ),
          ],
        ),
      ),
    );
  }

  // Export Logic Matches Previous
  Future<void> _exportZip() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("ZIP Export"),
        content: Text("Tanlangan filtrlar bo'yicha hujjatlarni ZIP arxiv ko'rinishida Telegramingizga yuborilsinmi?\n\nFiltr: $_selectedTitle"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("Bekor qilish")),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text("Yuborish")),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _isLoading = true);
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ZIP arxiv tayyorlanmoqda...")));

    final result = await _dataService.exportManagementDocumentsZip(
      query: _searchController.text,
      facultyId: _selectedFacultyId,
      title: _selectedTitle,
      educationType: _selectedEducationType,
      educationForm: _selectedEducationForm,
      levelName: _selectedCourse != null ? "${_selectedCourse}" : null, // Removed "-kurs" if API expects just number, but API usually handles string properly. Let's keep consistent.
      // Actually backend accepts "1-kurs". Let's verify.
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

  Future<void> _downloadDoc(dynamic doc) async {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Telegramga yuborilmoqda...")));
    final result = await _dataService.downloadStudentDocumentForManagement(doc['id'], type: doc['file_type']);
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
          Icon(Icons.search_off_rounded, size: 48, color: Colors.grey[300]),
          const SizedBox(height: 16),
          const Text("Hujjatlar topilmadi", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 4),
          Text("Filtrlarni o'zgartirib ko'ring", style: TextStyle(color: Colors.grey[500], fontSize: 12)),
        ],
      ),
    );
  }
}

class _PersistentHeaderDelegate extends SliverPersistentHeaderDelegate {
  final Widget child;
  final double maxHeight;
  final double minHeight;

  _PersistentHeaderDelegate({required this.child, required this.maxHeight, required this.minHeight});

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return child;
  }

  @override double get maxExtent => maxHeight;
  @override double get minExtent => minHeight;
  @override bool shouldRebuild(covariant SliverPersistentHeaderDelegate oldDelegate) => true;
}
