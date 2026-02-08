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
  List<String> _groups = [];
  
  bool _isLoading = true;
  bool _isSearching = false;

  // Filter States
  String? _selectedEducationType;
  String? _selectedEducationForm;
  String? _selectedCourse;
  int? _selectedFacultyId;
  String? _selectedSpecialty;
  String? _selectedGroup;

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
    _loadGroups();
  }

  Future<void> _loadSpecialties() async {
    final specs = await _dataService.getManagementSpecialties(facultyId: _selectedFacultyId);
    setState(() {
      _specialties = List<String>.from(specs);
    });
  }

  Future<void> _loadGroups() async {
    final groups = await _dataService.getManagementGroups(
      facultyId: _selectedFacultyId,
      levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
    );
    setState(() {
      _groups = List<String>.from(groups);
    });
  }

  Future<void> _handleSearch() async {
    final query = _searchController.text;
    
    bool hasFilters = _selectedEducationType != null || 
                      _selectedEducationForm != null ||
                      _selectedCourse != null || 
                      _selectedFacultyId != null || 
                      _selectedSpecialty != null ||
                      _selectedGroup != null;

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
      educationForm: _selectedEducationForm,
      levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
      specialtyName: _selectedSpecialty,
      groupNumber: _selectedGroup,
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
          if (_selectedEducationType != null || _selectedEducationForm != null || _selectedCourse != null || _selectedFacultyId != null || _selectedSpecialty != null || _selectedGroup != null || _searchController.text.isNotEmpty)
            TextButton(
              onPressed: () {
                setState(() {
                  _selectedEducationType = null;
                  _selectedEducationForm = null;
                  _selectedCourse = null;
                  _selectedFacultyId = null;
                  _selectedSpecialty = null;
                  _selectedGroup = null;
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
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
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
                    contentPadding: const EdgeInsets.symmetric(vertical: 0),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                
                // Row 1: Type, Form, Course
                Row(
                  children: [
                    Expanded(
                      child: _buildInlineDropdown<String>(
                        hint: "Turi",
                        value: _selectedEducationType,
                        items: ["Bakalavr", "Magistr"].map((e) => DropdownMenuItem(value: e, child: Text(e, style: const TextStyle(fontSize: 12)))).toList(),
                        onChanged: (val) {
                          setState(() {
                            _selectedEducationType = val;
                          });
                          _handleSearch();
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _buildInlineDropdown<String>(
                        hint: "Shakli",
                        value: _selectedEducationForm,
                        items: ["Kunduzgi", "Masofaviy", "Kechki", "Sirtqi"].map((e) => DropdownMenuItem(value: e, child: Text(e, style: const TextStyle(fontSize: 12)))).toList(),
                        onChanged: (val) {
                          setState(() => _selectedEducationForm = val);
                          _handleSearch();
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _buildInlineDropdown<String>(
                        hint: "Kurs",
                        value: _selectedCourse != null ? "${_selectedEducationType}_$_selectedCourse" : null,
                        items: [
                          ...["1", "2", "3", "4"].map((e) => DropdownMenuItem(value: "Bakalavr_$e", child: Text("$e-kurs", style: const TextStyle(fontSize: 12)))),
                          ...["1", "2"].map((e) => DropdownMenuItem(value: "Magistr_$e", child: Text("$e-kurs (Magistr)", style: const TextStyle(fontSize: 12)))),
                        ],
                        onChanged: (val) {
                          if (val != null) {
                            final parts = val.split('_');
                            setState(() {
                              _selectedEducationType = parts[0];
                              _selectedCourse = parts[1];
                            });
                            _loadGroups();
                            _handleSearch();
                          }
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                
                // Row 2: Faculty, Specialty, Group
                Row(
                  children: [
                    Expanded(
                      child: _buildInlineDropdown<int>(
                        hint: "Fakultet",
                        value: _selectedFacultyId,
                        items: _faculties.map((f) => DropdownMenuItem<int>(
                          value: f['id'],
                          child: Text(f['name'] ?? "", overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12)),
                        )).toList(),
                        onChanged: (val) {
                          setState(() {
                            _selectedFacultyId = val;
                            _selectedSpecialty = null;
                            _selectedGroup = null;
                          });
                          _loadSpecialties();
                          _loadGroups();
                          _handleSearch();
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _buildInlineDropdown<String>(
                        hint: "Yo'nalish",
                        value: _selectedSpecialty,
                        items: _specialties.map((s) => DropdownMenuItem(
                          value: s,
                          child: Text(s, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12)),
                        )).toList(),
                        onChanged: (val) {
                          setState(() => _selectedSpecialty = val);
                          _handleSearch();
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _buildInlineDropdown<String>(
                        hint: "Guruh",
                        value: _selectedGroup,
                        items: _groups.map((g) => DropdownMenuItem(
                          value: g,
                          child: Text(g, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12)),
                        )).toList(),
                        onChanged: (val) {
                          setState(() => _selectedGroup = val);
                          _handleSearch();
                        },
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // 2. Results
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
      height: 40,
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(8),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          isExpanded: true,
          hint: Text(hint, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
          value: value,
          items: items,
          onChanged: onChanged,
          icon: const Icon(Icons.arrow_drop_down, size: 20),
        ),
      ),
    );
  }

  Widget _buildSearchResults() {
    bool hasFilters = _searchController.text.isNotEmpty || 
                      _selectedEducationType != null || 
                      _selectedEducationForm != null ||
                      _selectedCourse != null || 
                      _selectedFacultyId != null || 
                      _selectedSpecialty != null ||
                      _selectedGroup != null;

    if (!hasFilters) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.person_search, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              "Talabalarni qidirish uchun\nfilterlarni tanlang yoki ismni yozing",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey, fontSize: 16),
            ),
          ],
        ),
      );
    }

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
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text(
                  "Guruh: ${s['group_number'] ?? ""} • ${s['education_form'] ?? ""}",
                  style: TextStyle(color: Colors.grey[700], fontSize: 13),
                ),
                Text(
                  "Fakultet: ${s['faculty_name'] ?? "Noma'lum"}",
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
