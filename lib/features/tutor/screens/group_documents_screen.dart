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
  String _filter = "all"; // all, missing, uploaded

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
    final success = await _dataService.requestDocuments(groupNumber: widget.groupNumber);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? "Barcha yuklamaganlarga xabar yuborildi" : "Xatolik yuz berdi"),
          backgroundColor: success ? Colors.green : Colors.red,
        ),
      );
    }
  }

  Future<void> _requestFromStudent(int studentId) async {
    final success = await _dataService.requestDocuments(studentId: studentId);
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
    List<dynamic> filtered = _students;
    if (_filter == "missing") {
      filtered = _students.where((s) => s['has_document'] == false).toList();
    } else if (_filter == "uploaded") {
      filtered = _students.where((s) => s['has_document'] == true).toList();
    }

    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text("Guruh: ${widget.groupNumber}"),
        actions: [
          IconButton(
            icon: const Icon(Icons.notification_add_outlined),
            tooltip: "Hammadan so'rash",
            onPressed: () {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text("Hujjat so'rash"),
                  content: const Text("Hujjat yuklamagan barcha talabalarga eslatma yuborilsinmi?"),
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
          // Filter Chips
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                _buildFilterChip("Barchasi", "all"),
                const SizedBox(width: 8),
                _buildFilterChip("Yuklamagan", "missing"),
                const SizedBox(width: 8),
                _buildFilterChip("Yuklagan", "uploaded"),
              ],
            ),
          ),
          
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : filtered.isEmpty
                    ? Center(
                        child: Text(
                          _filter == "missing" ? "Hamma hujjat yuklagan! 🎉" : "Talabalar topilmadi",
                          style: TextStyle(color: Colors.grey[600]),
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadData,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: filtered.length,
                          itemBuilder: (context, index) {
                            final s = filtered[index];
                            final hasDoc = s['has_document'] == true;

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              elevation: 0,
                              color: Colors.white,
                              child: ExpansionTile(
                                leading: CircleAvatar(
                                  backgroundImage: s['image'] != null ? CachedNetworkImageProvider(s['image']) : null,
                                  child: s['image'] == null ? const Icon(Icons.person) : null,
                                ),
                                title: Text(s['full_name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                subtitle: Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: (hasDoc ? Colors.green : Colors.red).withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(
                                        hasDoc ? "Yuklangan" : "Yuklanmagan",
                                        style: TextStyle(color: hasDoc ? Colors.green : Colors.red, fontSize: 10, fontWeight: FontWeight.bold),
                                      ),
                                    ),
                                  ],
                                ),
                                trailing: !hasDoc
                                    ? IconButton(
                                        icon: const Icon(Icons.send_rounded, color: AppTheme.primaryBlue, size: 20),
                                        onPressed: () => _requestFromStudent(s['id']),
                                      )
                                    : const Icon(Icons.check_circle, color: Colors.green, size: 20),
                                children: [
                                  if (hasDoc)
                                    ...((s['documents'] as List).map((doc) => ListTile(
                                          dense: true,
                                          leading: const Icon(Icons.description_outlined, size: 18),
                                          title: Text(doc['title'] ?? "Hujjat"),
                                          subtitle: Text(doc['created_at'].toString().split('T')[0]),
                                          trailing: Text(doc['status'] ?? "", style: const TextStyle(fontSize: 10)),
                                        ))),
                                  if (!hasDoc)
                                    const Padding(
                                      padding: EdgeInsets.all(16.0),
                                      child: Text("Ushbu talaba hali hech qanday hujjat yuklamagan.", style: TextStyle(fontSize: 12, color: Colors.grey)),
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

  Widget _buildFilterChip(String label, String value) {
    final isSelected = _filter == value;
    return ChoiceChip(
      label: Text(label, style: TextStyle(color: isSelected ? Colors.white : Colors.black87, fontSize: 12)),
      selected: isSelected,
      onSelected: (selected) {
        if (selected) setState(() => _filter = value);
      },
      selectedColor: AppTheme.primaryBlue,
      backgroundColor: Colors.grey[200],
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      showCheckmark: false,
    );
  }
}
