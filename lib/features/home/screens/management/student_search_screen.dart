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
  bool _isLoading = true;
  bool _isSearching = false;

  @override
  void initState() {
    super.initState();
    _loadFaculties();
  }

  Future<void> _loadFaculties() async {
    final faculties = await _dataService.getManagementFaculties();
    setState(() {
      _faculties = faculties;
      _isLoading = false;
    });
  }

  Future<void> _handleSearch(String query) async {
    if (query.isEmpty) {
      setState(() {
        _isSearching = false;
        _searchResults = [];
      });
      return;
    }

    setState(() => _isSearching = true);
    final results = await _dataService.searchStudents(query);
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
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              onChanged: _handleSearch,
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
            child: _searchController.text.isNotEmpty
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
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            leading: CircleAvatar(
              backgroundImage: s['image_url'] != null ? NetworkImage(s['image_url']) : null,
              child: s['image_url'] == null ? const Icon(Icons.person) : null,
            ),
            title: Text(s['full_name'] ?? ""),
            subtitle: Text("ID: ${s['hemis_login'] ?? s['hemis_id'] ?? ""} • ${s['group_number'] ?? ""}"),
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
