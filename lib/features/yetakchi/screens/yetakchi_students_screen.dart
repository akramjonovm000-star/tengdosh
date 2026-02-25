import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../services/yetakchi_service.dart';
import 'package:cached_network_image/cached_network_image.dart';

class YetakchiStudentsScreen extends StatefulWidget {
  const YetakchiStudentsScreen({Key? key}) : super(key: key);

  @override
  State<YetakchiStudentsScreen> createState() => _YetakchiStudentsScreenState();
}

class _YetakchiStudentsScreenState extends State<YetakchiStudentsScreen> {
  final YetakchiService _service = YetakchiService();
  final TextEditingController _searchController = TextEditingController();
  
  List<dynamic> _students = [];
  bool _isLoading = true;
  String _searchQuery = "";

  @override
  void initState() {
    super.initState();
    _fetchStudents();
  }

  Future<void> _fetchStudents() async {
    setState(() => _isLoading = true);
    final results = await _service.getStudents(search: _searchQuery, limit: 50);
    if (mounted) {
      setState(() {
        _students = results;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Talabalar Ro'yxati", style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      body: Column(
        children: [
          _buildSearchBar(),
          Expanded(
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator())
              : _students.isEmpty 
                  ? _buildEmptyState()
                  : _buildStudentList()
          )
        ],
      )
    );
  }

  Widget _buildSearchBar() {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.all(16),
      child: TextField(
        controller: _searchController,
        decoration: InputDecoration(
          hintText: "F.I.SH Yoki Guruh orqali qidirish...",
          prefixIcon: const Icon(Icons.search),
          suffixIcon: _searchQuery.isNotEmpty 
             ? IconButton(icon: const Icon(Icons.clear), onPressed: () {
                 _searchController.clear();
                 setState(() => _searchQuery = "");
                 _fetchStudents();
               })
             : null,
          filled: true,
          fillColor: Colors.grey[100],
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none)
        ),
        onSubmitted: (val) {
          setState(() => _searchQuery = val);
          _fetchStudents();
        },
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search_off, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text("Hech narsa topilmadi", style: TextStyle(color: Colors.grey[600], fontSize: 16))
        ],
      ),
    );
  }

  Widget _buildStudentList() {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: _students.length,
      itemBuilder: (context, index) {
        final student = _students[index];
        return Card(
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(
             borderRadius: BorderRadius.circular(16),
             side: BorderSide(color: Colors.grey[200]!)
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.all(12),
            leading: CircleAvatar(
              radius: 25,
              backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
              backgroundImage: student['image_url'] != null ? CachedNetworkImageProvider(student['image_url']) : null,
              child: student['image_url'] == null ? const Icon(Icons.person, color: AppTheme.primaryBlue) : null,
            ),
            title: Text(student['full_name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            subtitle: Padding(
              padding: const EdgeInsets.top(6),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(color: Colors.indigo.withOpacity(0.1), borderRadius: BorderRadius.circular(6)),
                    child: Text(student['group_number'] ?? 'Guruhsiz', style: const TextStyle(color: Colors.indigo, fontSize: 11, fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(student['faculty'] ?? '', overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 11, color: Colors.black54)),
                  )
                ],
              ),
            ),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text("Ball", style: TextStyle(fontSize: 10, color: Colors.black54)),
                Text("${student['points'] ?? 0}", style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue, fontSize: 16)),
              ],
            ),
            onTap: () {
               // Future enhancement: Open Student Activity Profile
            },
          ),
        );
      },
    );
  }
}
