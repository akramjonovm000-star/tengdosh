import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:cached_network_image/cached_network_image.dart';

class GroupDocumentsScreen extends StatefulWidget {
  final String groupNumber;
  const GroupDocumentsScreen({super.key, required this.groupNumber});

  @override
  State<GroupDocumentsScreen> createState() => _GroupDocumentsScreenState();
}

class _GroupDocumentsScreenState extends State<GroupDocumentsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _students = [];
  
  String _selectedStatus = "all"; // all, missing, uploaded
  String _selectedCategory = "all"; // all, passport, diplom, etc

  final List<Map<String, String>> _categories = [
    {"id": "all", "name": "Barcha turlar"},
    {"id": "passport", "name": "Passport"},
    {"id": "diplom", "name": "Diplom"},
    {"id": "rezyume", "name": "Rezyume"},
    {"id": "obyektivka", "name": "Obyektivka"},
    {"id": "boshqa", "name": "Boshqa"},
  ];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final data = await _dataService.getGroupDocumentDetails(widget.groupNumber);
    if (mounted) {
      setState(() {
        _students = data ?? [];
        _isLoading = false;
      });
    }
  }

  Future<void> _requestFromAll() async {
    final success = await _dataService.requestDocuments(
      groupNumber: widget.groupNumber,
      categoryName: _selectedCategory,
    );
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? "Xabarnoma yuborildi" : "Xatolik yuz berdi"),
          backgroundColor: success ? Colors.green : Colors.red,
        ),
      );
    }
  }

  Future<void> _requestFromStudent(int studentId) async {
    final success = await _dataService.requestDocuments(
      studentId: studentId,
      categoryName: _selectedCategory,
    );
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? "Eslatma yuborildi" : "Xatolik yuz berdi"),
          backgroundColor: success ? Colors.green : Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    List<dynamic> filtered = _students.where((s) {
      final docs = s['documents'] as List;
      
      bool categoryMatch = true;
      if (_selectedCategory != "all") {
        categoryMatch = docs.any((d) => d['category'] == _selectedCategory);
      }

      if (_selectedStatus == "uploaded") {
        return categoryMatch;
      } else if (_selectedStatus == "missing") {
        return !categoryMatch;
      }
      return true; // all
    }).toList();

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text("Guruh: ${widget.groupNumber}", style: const TextStyle(fontSize: 18)),
        actions: [
          IconButton(
            icon: const Icon(Icons.notification_add_outlined),
            tooltip: "Filter bo'yicha so'rash",
            onPressed: () {
              final catName = _categories.firstWhere((c) => c['id'] == _selectedCategory)['name'];
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text("Hujjat so'rash"),
                  content: Text(
                    _selectedCategory == "all"
                        ? "Hujjat yuklamagan barcha talabalarga eslatma yuborilsinmi?"
                        : "$catName yuklamagan barcha talabalarga eslatma yuborilsinmi?",
                  ),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Bekor qilish")),
                    ElevatedButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        _requestFromAll();
                      },
                      child: const Text("Yuborish"),
                    ),
                  ],
                ),
              );
            },
          )
        ],
      ),
      body: Column(
        children: [
          // Premium Filter Section
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                )
              ],
            ),
            child: Row(
              children: [
                // Left Filter: Document Type
                Expanded(
                  flex: 3,
                  child: _buildFilterDropdown(
                    value: _selectedCategory,
                    label: "Hujjat turi",
                    icon: Icons.description_outlined,
                    items: _categories.map((c) => DropdownMenuItem(
                      value: c['id']!, 
                      child: Text(c['name']!, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12))
                    )).toList(),
                    onChanged: (v) => setState(() => _selectedCategory = v!),
                  ),
                ),
                const SizedBox(width: 12),
                // Right Filter: Status
                Expanded(
                  flex: 2,
                  child: _buildFilterDropdown(
                    value: _selectedStatus,
                    label: "Holati",
                    icon: Icons.filter_list_rounded,
                    items: const [
                      DropdownMenuItem(value: "all", child: Text("Barchasi", style: TextStyle(fontSize: 12))),
                      DropdownMenuItem(value: "missing", child: Text("Yuklamagan", style: TextStyle(fontSize: 12))),
                      DropdownMenuItem(value: "uploaded", child: Text("Yuklagan", style: TextStyle(fontSize: 12))),
                    ],
                    onChanged: (v) => setState(() => _selectedStatus = v!),
                  ),
                ),
              ],
            ),
          ),
          
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : filtered.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.search_off_rounded, size: 64, color: Colors.grey[300]),
                            const SizedBox(height: 16),
                            Text(
                              "Ma'lumot topilmadi",
                              style: TextStyle(color: Colors.grey[600], fontSize: 16),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadData,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: filtered.length,
                          itemBuilder: (context, index) {
                            final s = filtered[index];
                            final docs = s['documents'] as List;
                            
                            bool hasTargetDoc = true;
                            if (_selectedCategory != "all") {
                              hasTargetDoc = docs.any((d) => d['category'] == _selectedCategory);
                            } else {
                              hasTargetDoc = s['has_document'] == true;
                            }

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                                side: BorderSide(color: Colors.grey[100]!),
                              ),
                              elevation: 0,
                              color: Colors.white,
                              child: ExpansionTile(
                                shape: const RoundedRectangleBorder(side: BorderSide.none),
                                collapsedShape: const RoundedRectangleBorder(side: BorderSide.none),
                                leading: CircleAvatar(
                                  radius: 20,
                                  backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                                  backgroundImage: s['image'] != null && s['image'].toString().isNotEmpty 
                                      ? CachedNetworkImageProvider(s['image']) 
                                      : null,
                                  child: (s['image'] == null || s['image'].toString().isEmpty) 
                                      ? const Icon(Icons.person, size: 22, color: AppTheme.primaryBlue) 
                                      : null,
                                ),
                                title: Text(s['full_name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                subtitle: Padding(
                                  padding: const EdgeInsets.only(top: 4),
                                  child: Row(
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: (hasTargetDoc ? Colors.green : Colors.orange).withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          hasTargetDoc ? "Yuklangan" : "Yuklamagan",
                                          style: TextStyle(
                                            color: hasTargetDoc ? Colors.green : Colors.orange, 
                                            fontSize: 10, 
                                            fontWeight: FontWeight.bold
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                trailing: !hasTargetDoc
                                    ? IconButton(
                                        icon: const Icon(Icons.mark_email_unread_outlined, color: AppTheme.primaryBlue, size: 22),
                                        onPressed: () => _requestFromStudent(s['id']),
                                      )
                                    : const Icon(Icons.check_circle_rounded, color: Colors.green, size: 22),
                                children: [
                                  const Divider(height: 1, indent: 16, endIndent: 16),
                                  if (docs.isNotEmpty)
                                    ...docs.map((doc) => ListTile(
                                          dense: true,
                                          contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 0),
                                          leading: Icon(
                                            doc['category'] == _selectedCategory ? Icons.star_rounded : Icons.description_outlined, 
                                            size: 18, 
                                            color: doc['category'] == _selectedCategory ? Colors.amber : Colors.grey[400]
                                          ),
                                          title: Text("${doc['title'] ?? "Hujjat"} (${doc['category']})", style: const TextStyle(fontSize: 12)),
                                          subtitle: Text(doc['created_at'].toString().split('T')[0], style: TextStyle(fontSize: 10, color: Colors.grey[500])),
                                        ))
                                  else
                                    const Padding(
                                      padding: EdgeInsets.all(24.0),
                                      child: Text("Hech qanday hujjat yuklanmagan", style: TextStyle(fontSize: 12, color: Colors.grey)),
                                    )
                                ],
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterDropdown({
    required String value,
    required List<DropdownMenuItem<String>> items,
    required ValueChanged<String?> onChanged,
    required String label,
    required IconData icon,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 12, color: Colors.grey[600]),
            const SizedBox(width: 4),
            Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[600], fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          decoration: BoxDecoration(
            color: Colors.grey[50],
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey[200]!),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: value,
              items: items,
              onChanged: onChanged,
              isExpanded: true,
              dropdownColor: Colors.white,
              borderRadius: BorderRadius.circular(12),
              style: const TextStyle(fontSize: 13, color: Colors.black87, fontWeight: FontWeight.w500),
              icon: Icon(Icons.keyboard_arrow_down_rounded, size: 20, color: Colors.grey[400]),
            ),
          ),
        ),
      ],
    );
  }
}
