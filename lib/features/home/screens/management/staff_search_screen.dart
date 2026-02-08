import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'package:intl/intl.dart';

class StaffSearchScreen extends StatefulWidget {
  const StaffSearchScreen({super.key});

  @override
  State<StaffSearchScreen> createState() => _StaffSearchScreenState();
}

class _StaffSearchScreenState extends State<StaffSearchScreen> {
  final DataService _dataService = DataService();
  final TextEditingController _searchController = TextEditingController();
  
  List<dynamic> _faculties = [];
  List<dynamic> _searchResults = [];
  bool _isLoading = true;
  bool _isSearching = false;

  int? _selectedFacultyId;
  String? _selectedRole;

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
    _handleSearch();
  }

  Future<void> _handleSearch() async {
    final query = _searchController.text;
    setState(() => _isSearching = true);
    
    final result = await _dataService.searchStaff(
      query: query.isNotEmpty ? query : null,
      facultyId: _selectedFacultyId,
      role: _selectedRole,
    );
    
    setState(() {
      _searchResults = result;
      _isSearching = false;
    });
  }

  String _formatLastSeen(String? isoDate) {
    if (isoDate == null) return "Noma'lum";
    try {
      final dateTime = DateTime.parse(isoDate);
      final now = DateTime.now();
      final difference = now.difference(dateTime);

      if (difference.inMinutes < 10) return "Hozirda online";
      if (difference.inHours < 1) return "${difference.inMinutes} daqiqa oldin";
      if (difference.inDays < 1) return "${difference.inHours} soat oldin";
      if (difference.inDays < 7) return "${difference.inDays} kun oldin";
      
      return DateFormat('dd.MM.yyyy').format(dateTime);
    } catch (e) {
      return isoDate;
    }
  }

  Color _getStatusColor(String? isoDate) {
    if (isoDate == null) return Colors.grey;
    try {
      final dateTime = DateTime.parse(isoDate);
      final now = DateTime.now();
      if (now.difference(dateTime).inMinutes < 15) return Colors.green;
    } catch (_) {}
    return Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Xodimlar monitoringi"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        centerTitle: true,
      ),
      body: Column(
        children: [
          // 1. Search & Filter Bar
          Container(
            color: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  onChanged: (val) => _handleSearch(),
                  decoration: InputDecoration(
                    hintText: "Ism, lavozim yoki bo'lim...",
                    prefixIcon: const Icon(Icons.search, color: Colors.blue),
                    filled: true,
                    fillColor: Colors.grey[100],
                    contentPadding: const EdgeInsets.symmetric(vertical: 0),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: _buildDropdown<int>(
                        hint: "Fakultet",
                        value: _selectedFacultyId,
                        items: _faculties.map((f) => DropdownMenuItem<int>(
                          value: f['id'],
                          child: Text(f['name'] ?? "", overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12)),
                        )).toList(),
                        onChanged: (val) {
                          setState(() => _selectedFacultyId = val);
                          _handleSearch();
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _buildDropdown<String>(
                        hint: "Lavozim",
                        value: _selectedRole,
                        items: [
                          {"id": "tyutor", "name": "Tyutor"},
                          {"id": "dekan", "name": "Dekan"},
                          {"id": "kafedra_mudiri", "name": "Kafedra Mudiri"},
                          {"id": "boshliq", "name": "Bo'lim boshlig'i"},
                        ].map((r) => DropdownMenuItem<String>(
                          value: r['id'],
                          child: Text(r['name']!, style: const TextStyle(fontSize: 12)),
                        )).toList(),
                        onChanged: (val) {
                          setState(() => _selectedRole = val);
                          _handleSearch();
                        },
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // 2. Results List
          Expanded(
            child: _isSearching 
              ? const Center(child: CircularProgressIndicator())
              : _searchResults.isEmpty 
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.person_off_rounded, size: 64, color: Colors.grey),
                        SizedBox(height: 16),
                        Text("Xodimlar topilmadi", style: TextStyle(color: Colors.grey, fontSize: 16)),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _searchResults.length,
                    itemBuilder: (context, index) {
                      final s = _searchResults[index];
                      final lastSeen = s['last_active'];
                      final isOnline = _getStatusColor(lastSeen) == Colors.green;
                      
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(20),
                          side: BorderSide(color: Colors.grey.shade200),
                        ),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(20),
                          onTap: () {
                             // Future: Staff Detail View
                          },
                          child: Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: Row(
                              children: [
                                // Avatar with status indicator
                                Stack(
                                  children: [
                                    CircleAvatar(
                                      radius: 30,
                                      backgroundColor: Colors.blue.shade50,
                                      backgroundImage: s['image_url'] != null ? NetworkImage(s['image_url']) : null,
                                      child: s['image_url'] == null ? const Icon(Icons.person, color: Colors.blue, size: 30) : null,
                                    ),
                                    Positioned(
                                      right: 2,
                                      bottom: 2,
                                      child: Container(
                                        width: 14,
                                        height: 14,
                                        decoration: BoxDecoration(
                                          color: _getStatusColor(lastSeen),
                                          shape: BoxShape.circle,
                                          border: Border.all(color: Colors.white, width: 2.5),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(width: 16),
                                // Staff Info
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        s['full_name'] ?? "Noma'lum Xodim",
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        "${s['position'] ?? s['role'] ?? "Lavozim aniqlanmadi"}",
                                        style: TextStyle(color: Colors.blue.shade700, fontSize: 13, fontWeight: FontWeight.w500),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        s['department'] ?? s['faculty_name'] ?? "Universitet xodimi",
                                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                  ),
                                ),
                                // Last Seen Info
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    if (isOnline)
                                      const Text(
                                        "Online",
                                        style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 11),
                                      )
                                    else
                                      Text(
                                        _formatLastSeen(lastSeen),
                                        style: const TextStyle(fontSize: 10, color: Colors.grey),
                                      ),
                                    const SizedBox(height: 8),
                                    Icon(Icons.chevron_right, color: Colors.grey.shade400, size: 20),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildDropdown<T>({required String hint, required T? value, required List<DropdownMenuItem<T>> items, required ValueChanged<T?> onChanged}) {
    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(12),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          isExpanded: true,
          hint: Text(hint, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
          value: value,
          items: items,
          onChanged: onChanged,
          icon: const Icon(Icons.keyboard_arrow_down_rounded, size: 20),
        ),
      ),
    );
  }
}
