import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
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
          if (_selectedEducationType != null || _selectedCourse != null || _selectedFacultyId != null || _selectedSpecialty != null || _searchController.text.isNotEmpty)
            TextButton(
              onPressed: () {
                setState(() {
                  _selectedEducationType = null;
                  _selectedCourse = null;
                  _selectedFacultyId = null;
                  _selectedSpecialty = null;
                  _searchController.clear();
                });
                _handleSearch();
              },
              child: const Text("Tozalash", style: TextStyle(color: Colors.red)),
            ),
        ],
      ),
      body: Column(
        children: [
          // 1. Search & Filters Container
          Container(
            color: Colors.white,
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                // Search Field
                TextField(
                  controller: _searchController,
                  onChanged: (val) => _handleSearch(),
                  decoration: InputDecoration(
                    hintText: "Ism yoki Hemis ID...",
                    prefixIcon: const Icon(Icons.search),
                    filled: true,
                    fillColor: Colors.grey[50],
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                
                // Row for Education Type and Course
                Row(
                  children: [
                    Expanded(
                      child: _buildInlineDropdown<String>(
                        hint: "Ta'lim turi",
                        value: _selectedEducationType,
                        items: ["Bakalavr", "Magistr"].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                        onChanged: (val) {
                          setState(() {
                            _selectedEducationType = val;
                            _selectedCourse = null;
                          });
                          _handleSearch();
                        },
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _buildInlineDropdown<String>(
                        hint: "Kurs",
                        value: _selectedCourse,
                        items: (_selectedEducationType == "Magistr" ? ["1", "2"] : ["1", "2", "3", "4"])
                            .map((e) => DropdownMenuItem(value: e, child: Text("$e-kurs"))).toList(),
                        onChanged: (val) {
                          setState(() => _selectedCourse = val);
                          _handleSearch();
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                
                // Faculty Dropdown
                _buildInlineDropdown<int>(
                  hint: "Fakultetni tanlang",
                  value: _selectedFacultyId,
                  items: _faculties.map((f) => DropdownMenuItem<int>(
                    value: f['id'],
                    child: Text(f['name'] ?? "", overflow: TextOverflow.ellipsis),
                  )).toList(),
                  onChanged: (val) {
                    setState(() {
                      _selectedFacultyId = val;
                      _selectedSpecialty = null;
                    });
                    _loadSpecialties();
                    _handleSearch();
                  },
                ),
                const SizedBox(height: 12),

                // Specialty Dropdown
                _buildInlineDropdown<String>(
                  hint: "Yo'nalishni tanlang",
                  value: _selectedSpecialty,
                  items: _specialties.map((s) => DropdownMenuItem(
                    value: s,
                    child: Text(s, overflow: TextOverflow.ellipsis),
                  )).toList(),
                  onChanged: (val) {
                    setState(() => _selectedSpecialty = val);
                    _handleSearch();
                  },
                ),
              ],
            ),
          ),

          // 2. Results or Default View
          Expanded(
            child: _buildSearchResults(),
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
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          isExpanded: true,
          hint: Text(hint, style: TextStyle(fontSize: 14, color: Colors.grey[600])),
          value: value,
          items: items,
          onChanged: onChanged,
        ),
      ),
    );
  }

  Widget _buildSearchResults() {
    if (_isSearching) return const Center(child: CircularProgressIndicator());
    if (_searchResults.isEmpty) return const Center(child: Text("Ma'lumot topilmadi"));

    return ListView.builder(
      itemCount: _searchResults.length,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemBuilder: (context, index) {
        final s = _searchResults[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: Colors.grey.shade200),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.all(12),
            leading: CircleAvatar(
              radius: 28,
              backgroundImage: s['image_url'] != null ? NetworkImage(s['image_url']) : null,
              child: s['image_url'] == null ? const Icon(Icons.person, size: 30) : null,
            ),
            title: Text(
              s['full_name'] ?? "",
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text(
                  "ID: ${s['hemis_login'] ?? s['hemis_id'] ?? ""} • ${s['group_number'] ?? ""}",
                  style: TextStyle(color: Colors.grey[700]),
                ),
                if (s['faculty_name'] != null)
                  Text(
                    s['faculty_name'],
                    style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
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
}
