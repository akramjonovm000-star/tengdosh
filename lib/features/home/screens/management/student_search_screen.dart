import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'faculty_levels_screen.dart';
import 'student_detail_view.dart';

class StudentSearchScreen extends StatefulWidget {
  const StudentSearchScreen({super.key});

  @override
  State<StudentSearchScreen> createState() => _StudentSearchScreenState();
}

class _StudentSearchScreenState extends State<StudentSearchScreen> {
  final DataService _dataService = DataService();
  final TextEditingController _searchController = TextEditingController();
  
  List<dynamic> _faculties = [];
  List<dynamic> _searchResults = [];
  List<String> _specialties = [];
  
  bool _isLoading = true;
  bool _isSearching = false;

  // Filter States
  String? _selectedEducationType;
  String? _selectedCourse;
  int? _selectedFacultyId;
  String? _selectedSpecialty;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    final faculties = await _dataService.getManagementFaculties();
    setState(() {
      _faculties = faculties;
      _isLoading = false;
    });
    _loadSpecialties();
  }

  Future<void> _loadSpecialties() async {
    final specs = await _dataService.getManagementSpecialties(facultyId: _selectedFacultyId);
    setState(() {
      _specialties = List<String>.from(specs);
    });
  }

  Future<void> _handleSearch() async {
    final query = _searchController.text;
    
    // Check if we have any filters or query
    bool hasFilters = _selectedEducationType != null || 
                      _selectedCourse != null || 
                      _selectedFacultyId != null || 
                      _selectedSpecialty != null;

    if (query.isEmpty && !hasFilters) {
      setState(() {
        _isSearching = false;
        _searchResults = [];
      });
      return;
    }

    setState(() => _isSearching = true);
    
    final results = await _dataService.searchStudents(
      query: query.isNotEmpty ? query : null,
      facultyId: _selectedFacultyId,
      educationType: _selectedEducationType,
      levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
      specialtyName: _selectedSpecialty,
    );
    
    setState(() {
      _searchResults = results;
      _isSearching = false;
    });
  }

  void _showFilterSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) {
          return Padding(
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(context).viewInsets.bottom,
              left: 20,
              right: 20,
              top: 20,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      "Filterlar",
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _selectedEducationType = null;
                          _selectedCourse = null;
                          _selectedFacultyId = null;
                          _selectedSpecialty = null;
                        });
                        setSheetState(() {});
                        _handleSearch();
                      },
                      child: const Text("Tozalash"),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                
                // 1. Education Type
                _buildFilterLabel("Ta'lim turi"),
                DropdownButtonFormField<String>(
                  value: _selectedEducationType,
                  decoration: _filterInputDecoration(),
                  items: ["Bakalavr", "Magistr"].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                  onChanged: (val) {
                    setSheetState(() {
                      _selectedEducationType = val;
                      _selectedCourse = null; // Reset course when type changes
                    });
                    setState(() {
                      _selectedEducationType = val;
                      _selectedCourse = null;
                    });
                  },
                ),
                const SizedBox(height: 16),

                // 2. Course (Dynamic)
                if (_selectedEducationType != null) ...[
                  _buildFilterLabel("Kurslar"),
                  DropdownButtonFormField<String>(
                    value: _selectedCourse,
                    decoration: _filterInputDecoration(),
                    items: (_selectedEducationType == "Bakalavr" ? ["1", "2", "3", "4"] : ["1", "2"])
                        .map((e) => DropdownMenuItem(value: e, child: Text("$e-kurs"))).toList(),
                    onChanged: (val) {
                      setSheetState(() => _selectedCourse = val);
                      setState(() => _selectedCourse = val);
                    },
                  ),
                  const SizedBox(height: 16),
                ],

                // 3. Faculty
                _buildFilterLabel("Fakultet"),
                DropdownButtonFormField<int>(
                  value: _selectedFacultyId,
                  decoration: _filterInputDecoration(),
                  isExpanded: true,
                  items: _faculties.map((f) => DropdownMenuItem<int>(
                    value: f['id'],
                    child: Text(f['name'] ?? "", overflow: TextOverflow.ellipsis),
                  )).toList(),
                  onChanged: (val) {
                    setSheetState(() {
                      _selectedFacultyId = val;
                      _selectedSpecialty = null; // Reset specialty
                    });
                    setState(() {
                      _selectedFacultyId = val;
                      _selectedSpecialty = null;
                    });
                    _loadSpecialties(); // Refresh specialties list
                  },
                ),
                const SizedBox(height: 16),

                // 4. Specialty
                _buildFilterLabel("Yo'nalish"),
                DropdownButtonFormField<String>(
                  value: _selectedSpecialty,
                  decoration: _filterInputDecoration(),
                  isExpanded: true,
                  items: _specialties.map((s) => DropdownMenuItem(
                    value: s,
                    child: Text(s, overflow: TextOverflow.ellipsis),
                  )).toList(),
                  onChanged: (val) {
                    setSheetState(() => _selectedSpecialty = val);
                    setState(() => _selectedSpecialty = val);
                  },
                ),
                const SizedBox(height: 24),

                // Apply Button
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.pop(context);
                      _handleSearch();
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: const Text("Qo'llash", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(height: 32),
              ],
            ),
          );
        }
      ),
    );
  }

  Widget _buildFilterLabel(String label) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Text(label, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14)),
    );
  }

  InputDecoration _filterInputDecoration() {
    return InputDecoration(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.grey.shade200),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.grey.shade200),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Talaba qidirish"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        actions: [
          IconButton(
            icon: Stack(
              children: [
                const Icon(Icons.filter_list),
                if (_selectedEducationType != null || _selectedCourse != null || _selectedFacultyId != null || _selectedSpecialty != null)
                  Positioned(
                    right: 0,
                    top: 0,
                    child: Container(
                      padding: const EdgeInsets.all(2),
                      decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
                      constraints: const BoxConstraints(minWidth: 8, minHeight: 8),
                    ),
                  ),
              ],
            ),
            onPressed: _showFilterSheet,
          ),
        ],
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              onChanged: (val) => _handleSearch(),
              decoration: InputDecoration(
                hintText: "Ism yoki Hemis ID...",
                prefixIcon: const Icon(Icons.search),
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Colors.grey.shade200),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Colors.grey.shade200),
                ),
              ),
            ),
          ),

          Expanded(
            child: (_searchController.text.isNotEmpty || 
                    _selectedEducationType != null || 
                    _selectedCourse != null || 
                    _selectedFacultyId != null || 
                    _selectedSpecialty != null)
                ? _buildSearchResults()
                : _buildFacultyList(),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchResults() {
    if (_isSearching) return const Center(child: CircularProgressIndicator());
    if (_searchResults.isEmpty) return const Center(child: Text("Talaba topilmadi"));

    return ListView.builder(
      itemCount: _searchResults.length,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemBuilder: (context, index) {
        final s = _searchResults[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            leading: CircleAvatar(
              backgroundImage: s['image_url'] != null ? NetworkImage(s['image_url']) : null,
              child: s['image_url'] == null ? const Icon(Icons.person) : null,
            ),
            title: Text(s['full_name'] ?? ""),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("ID: ${s['hemis_login'] ?? s['hemis_id'] ?? ""} • ${s['group_number'] ?? ""}"),
                if (s['faculty_name'] != null)
                  Text(s['faculty_name'], style: TextStyle(fontSize: 12, color: Colors.grey[600]), maxLines: 1, overflow: TextOverflow.ellipsis),
              ],
            ),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => StudentDetailView(studentId: s['id'])),
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildFacultyList() {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_faculties.isEmpty) return const Center(child: Text("Fakultetlar topilmadi"));

    return ListView.builder(
      itemCount: _faculties.length,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemBuilder: (context, index) {
        final f = _faculties[index];
        return Card(
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.grey.shade200),
          ),
          child: ListTile(
            title: Text(f['name'] ?? "Noma'lum fakultet"),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => FacultyLevelsScreen(
                    facultyId: f['id'] ?? 0,
                    facultyName: f['name'] ?? "Noma'lum fakultet",
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }
}
