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
      final specs = await _dataService.getManagementSpecialties(facultyId: _selectedFacultyId);
      setState(() => _specialties = List<String>.from(specs));
    } catch (_) {}
  }

  Future<void> _loadGroups() async {
    try {
      final groups = await _dataService.getManagementGroups(
        facultyId: _selectedFacultyId,
        levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
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
      levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: AppTheme.backgroundWhite,
      endDrawer: _buildFilterDrawer(),
      body: CustomScrollView(
        physics: const BouncingScrollPhysics(),
        slivers: [
          _buildSliverAppBar(),
          
          // Stats Row
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: _buildStatsGrid(),
            ),
          ),

          // Search & Category Bar
          SliverPersistentHeader(
            pinned: true,
            delegate: _PersistentHeaderDelegate(
              child: Container(
                color: AppTheme.backgroundWhite,
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Column(
                  children: [
                    _buildSearchBar(),
                    _buildCategoryChips(),
                  ],
                ),
              ),
              maxHeight: 125,
              minHeight: 125,
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
      expandedHeight: 120,
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
        background: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [AppTheme.primaryBlue, Color(0xFF0016CC)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
        ),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.filter_list_rounded, color: Colors.white),
          onPressed: () => _scaffoldKey.currentState?.openEndDrawer(),
        ),
        const SizedBox(width: 8),
      ],
    );
  }

  Widget _buildStatsGrid() {
    return Row(
      children: [
        Expanded(child: _buildStatCard("Jami", "${_stats['students_in_scope'] ?? 0}", Icons.people_outline, Colors.blue)),
        const SizedBox(width: 12),
        Expanded(child: _buildStatCard("Yukladi", "${_stats['students_with_uploads'] ?? 0}", Icons.cloud_done_outlined, Colors.green)),
        const SizedBox(width: 12),
        Expanded(child: _buildStatCard("Ulush", "${_stats['completion_rate'] ?? 0}%", Icons.pie_chart_outline, Colors.orange)),
      ],
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      decoration: BoxDecoration(
        color: AppTheme.surfaceWhite,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 2),
          Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[600], fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
      child: Container(
        height: 50,
        decoration: BoxDecoration(
          color: AppTheme.surfaceWhite,
          borderRadius: BorderRadius.circular(15),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10)],
        ),
        child: TextField(
          controller: _searchController,
          onSubmitted: (val) => _loadDocuments(refresh: true),
          decoration: InputDecoration(
            hintText: "Talaba yoki hujjat nomi...",
            hintStyle: TextStyle(color: Colors.grey[400], fontSize: 14),
            prefixIcon: const Icon(Icons.search_rounded, color: AppTheme.primaryBlue),
            border: InputBorder.none,
            contentPadding: const EdgeInsets.symmetric(horizontal: 0, vertical: 15),
          ),
        ),
      ),
    );
  }

  Widget _buildCategoryChips() {
    return SizedBox(
      height: 45,
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
              selectedColor: AppTheme.primaryBlue.withOpacity(0.1),
              checkmarkColor: AppTheme.primaryBlue,
              labelStyle: TextStyle(
                color: isSelected ? AppTheme.primaryBlue : AppTheme.textBlack,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                fontSize: 12,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
                side: BorderSide(color: isSelected ? AppTheme.primaryBlue : Colors.transparent, width: 1),
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
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey.withOpacity(0.1)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () => _showDocumentActions(doc),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: (isCert ? Colors.amber : Colors.blue).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        isCert ? Icons.workspace_premium_rounded : Icons.description_outlined,
                        color: isCert ? Colors.amber[800] : Colors.blue[700],
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            doc['title'] ?? 'Nomsiz',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            student['full_name'] ?? 'Talaba',
                            style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.w600, fontSize: 13),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            "${student['faculty_name'] ?? '-'} • ${student['group_number'] ?? '-'}",
                            style: TextStyle(color: Colors.grey[500], fontSize: 11),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                    Icon(Icons.more_vert_rounded, color: Colors.grey[400], size: 20),
                  ],
                ),
                const Padding(padding: EdgeInsets.symmetric(vertical: 12), child: Divider(height: 1, thickness: 0.5)),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.calendar_today_rounded, size: 12, color: Colors.grey[400]),
                        const SizedBox(width: 4),
                        Text(doc['short_date'] ?? '-', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                      ],
                    ),
                    Row(
                      children: [
                        _buildActionIcon(Icons.telegram_rounded, Colors.blue, "Yuborish", () => _downloadDoc(doc)),
                        const SizedBox(width: 8),
                      ],
                    )
                  ],
                )
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildActionIcon(IconData icon, Color color, String label, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 16),
            const SizedBox(width: 4),
            Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold)),
          ],
        ),
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
            Text(doc['title'] ?? 'Hujjat', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            const SizedBox(height: 8),
            Text(doc['student']['full_name'] ?? '', style: TextStyle(color: Colors.grey[600])),
            const SizedBox(height: 24),
            ListTile(
              leading: const CircleAvatar(backgroundColor: Colors.blue, child: Icon(Icons.telegram, color: Colors.white)),
              title: const Text("Bot orqali yuborish"),
              subtitle: const Text("Hujjatni Telegram botingizga yuboradi"),
              onTap: () { Navigator.pop(context); _downloadDoc(doc); },
            ),
            ListTile(
              leading: CircleAvatar(backgroundColor: Colors.grey[100], child: Icon(Icons.copy_rounded, color: Colors.grey[700])),
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

  Widget _buildFilterDrawer() {
    return Drawer(
      backgroundColor: AppTheme.surfaceWhite,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.fromLTRB(24, 60, 24, 24),
            color: AppTheme.primaryBlue,
            child: const Row(
              children: [
                Icon(Icons.tune_rounded, color: Colors.white),
                SizedBox(width: 16),
                Text("Filtrlar", style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(24),
              children: [
                _buildDrawerDropdown<String>("Ta'lim turi", _selectedEducationType, ["Bakalavr", "Magistr"], (v) {
                  setState(() { _selectedEducationType = v; _selectedCourse = null; _selectedGroup = null; });
                  _loadGroups();
                }),
                const SizedBox(height: 16),
                _buildDrawerDropdown<int>("Fakultet", _selectedFacultyId, _faculties.map((f) => MapEntry(f['id'] as int, f['name'] as String)).toList(), (v) {
                  setState(() { _selectedFacultyId = v; _selectedSpecialty = null; _selectedGroup = null; });
                  _loadSpecialties(); _loadGroups();
                }),
                const SizedBox(height: 16),
                _buildDrawerDropdown<String>(
                  "Kurs", 
                  _selectedCourse, 
                  _selectedEducationType == "Magistr" ? ["1", "2"] : ["1", "2", "3", "4"], 
                  (v) { setState(() => _selectedCourse = v); _loadGroups(); }
                ),
                const SizedBox(height: 16),
                _buildDrawerDropdown<String>("Guruh", _selectedGroup, _groups, (v) => setState(() => _selectedGroup = v)),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(24),
            child: Row(
              children: [
                Expanded(
                  child: TextButton(
                    onPressed: () {
                      setState(() {
                        _selectedEducationType = null; _selectedEducationForm = null; _selectedCourse = null;
                        _selectedFacultyId = null; _selectedSpecialty = null; _selectedGroup = null;
                        _searchController.clear();
                      });
                      Navigator.pop(context);
                      _loadDocuments(refresh: true);
                    },
                    child: const Text("Tozalash", style: TextStyle(color: Colors.red)),
                  ),
                ),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () { Navigator.pop(context); _loadDocuments(refresh: true); },
                    child: const Text("Qo'llash"),
                  ),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildDrawerDropdown<T>(String label, T? value, dynamic items, ValueChanged<T?> onChanged) {
    List<DropdownMenuItem<T>> menuItems = [];
    if (items is List<String>) {
      menuItems = items.map((e) => DropdownMenuItem<T>(value: e as T, child: Text(e))).toList();
    } else if (items is List<MapEntry<int, String>>) {
      menuItems = items.map((e) => DropdownMenuItem<T>(value: e.key as T, child: Text(e.value))).toList();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textBlack)),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(12),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<T>(
              isExpanded: true,
              value: value,
              items: menuItems,
              onChanged: onChanged,
              hint: Text("Tanlang", style: TextStyle(color: Colors.grey[400], fontSize: 14)),
            ),
          ),
        ),
      ],
    );
  }

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
          Container(
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(color: Colors.grey[200], shape: BoxShape.circle),
            child: Icon(Icons.inventory_2_outlined, size: 64, color: Colors.grey[400]),
          ),
          const SizedBox(height: 24),
          const Text("Hujjatlar topilmadi", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          const SizedBox(height: 8),
          Text("Filtrlarni o'zgartirib ko'ring", style: TextStyle(color: Colors.grey[500])),
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
