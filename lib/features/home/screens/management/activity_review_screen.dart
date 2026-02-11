import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import 'package:intl/intl.dart';

class ActivityReviewScreen extends StatefulWidget {
  final String? initialStatus;
  final String title;

  const ActivityReviewScreen({
    super.key, 
    this.initialStatus,
    required this.title,
  });

  @override
  State<ActivityReviewScreen> createState() => _ActivityReviewScreenState();
}

class _ActivityReviewScreenState extends State<ActivityReviewScreen> {
  final DataService _dataService = DataService();
  final TextEditingController _searchController = TextEditingController();
  
  bool _isLoading = true;
  bool _isSearching = false;
  List<dynamic> _activities = [];
  int _totalCount = 0;
  int _currentPage = 1;
  
  // Filter States
  String? _selectedStatus;
  String? _selectedEducationType;
  String? _selectedEducationForm;
  String? _selectedCourse;
  int? _selectedFacultyId;
  String? _selectedSpecialty;
  String? _selectedGroup;

  List<dynamic> _faculties = [];
  List<String> _specialties = [];
  List<String> _groups = [];

  @override
  void initState() {
    super.initState();
    _selectedStatus = widget.initialStatus;
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    final faculties = await _dataService.getManagementFaculties();
    if (mounted) {
      setState(() {
        _faculties = faculties;
      });
    }
    _loadSpecialties();
    _loadGroups();
    _loadActivities(refresh: true);
  }

  Future<void> _loadSpecialties() async {
    try {
      final specs = await _dataService.getManagementSpecialties(
        facultyId: _selectedFacultyId,
        educationType: _selectedEducationType,
      );
      if (mounted) {
        setState(() {
          _specialties = List<String>.from(specs);
        });
      }
    } catch (_) {}
  }

  Future<void> _loadGroups() async {
    try {
      final groups = await _dataService.getManagementGroups(
        facultyId: _selectedFacultyId,
        educationType: _selectedEducationType,
        educationForm: _selectedEducationForm,
        specialtyName: _selectedSpecialty,
        levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
      );
      if (mounted) {
        setState(() {
          _groups = List<String>.from(groups);
        });
      }
    } catch (_) {}
  }

  Future<void> _loadActivities({bool refresh = false}) async {
    if (refresh) {
      setState(() {
        _currentPage = 1;
        _isLoading = true;
      });
    }

    try {
      final res = await _dataService.getManagementActivities(
        status: _selectedStatus == "Barchasi" ? null : _selectedStatus,
        query: _searchController.text.isNotEmpty ? _searchController.text : null,
        facultyId: _selectedFacultyId,
        educationType: _selectedEducationType,
        educationForm: _selectedEducationForm,
        levelName: _selectedCourse != null ? "${_selectedCourse}-kurs" : null,
        specialtyName: _selectedSpecialty,
        groupNumber: _selectedGroup,
        page: _currentPage,
      );

      if (mounted) {
        setState(() {
          if (refresh) {
            _activities = res['data'] ?? [];
          } else {
            _activities.addAll(res['data'] ?? []);
          }
          _totalCount = res['total'] ?? 0;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Xatolik: $e")));
      }
    }
  }

  Future<void> _approve(int id) async {
    final success = await _dataService.approveActivity(id);
    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Faollik tasdiqlandi")));
      setState(() {
        final index = _activities.indexWhere((a) => a['id'] == id);
        if (index != -1) {
          if (_selectedStatus != null && _selectedStatus != "Barchasi" && _selectedStatus != "confirmed") {
            _activities.removeAt(index);
          } else {
            _activities[index]['status'] = 'confirmed';
          }
        }
      });
    }
  }

  Future<void> _reject(int id) async {
    String? comment;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        final controller = TextEditingController();
        return AlertDialog(
          title: const Text("Rad etish"),
          content: TextField(
            controller: controller,
            decoration: const InputDecoration(hintText: "Sababini kiriting (ixtiyoriy)"),
            maxLines: 3,
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("Bekor qilish")),
            ElevatedButton(
              onPressed: () {
                comment = controller.text;
                Navigator.pop(context, true);
              },
              child: const Text("Rad etish"),
            ),
          ],
        );
      }
    );

    if (confirmed == true) {
      final success = await _dataService.rejectActivity(id, comment);
      if (success && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Faollik rad etildi")));
        setState(() {
          final index = _activities.indexWhere((a) => a['id'] == id);
          if (index != -1) {
            if (_selectedStatus != null && _selectedStatus != "Barchasi" && _selectedStatus != "rejected") {
              _activities.removeAt(index);
            } else {
              _activities[index]['status'] = 'rejected';
              _activities[index]['moderator_comment'] = comment;
            }
          }
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(widget.title),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list_rounded),
            onPressed: () => _showFilterSheet(),
          ),
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
                _loadActivities(refresh: true);
              },
              child: const Text("Tozalash", style: TextStyle(color: Colors.red)),
            ),
          IconButton(icon: const Icon(Icons.refresh), onPressed: () => _loadActivities(refresh: true)),
        ],
      ),
      body: Column(
        children: [
          Container(
            color: Colors.white,
            padding: const EdgeInsets.all(16.0).copyWith(bottom: 8),
            child: TextField(
              controller: _searchController,
              onChanged: (val) => _loadActivities(refresh: true),
              decoration: InputDecoration(
                hintText: "Ism yoki Hemis ID...",
                prefixIcon: const Icon(Icons.search_rounded),
                filled: true,
                fillColor: Colors.grey[50],
                contentPadding: const EdgeInsets.symmetric(vertical: 0),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          _buildFilterBar(),
          Expanded(
            child: _isLoading && _activities.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : _activities.isEmpty
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        onRefresh: () => _loadActivities(refresh: true),
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _activities.length + (_activities.length < _totalCount ? 1 : 0),
                          itemBuilder: (context, index) {
                            if (index == _activities.length) {
                              _currentPage++;
                              _loadActivities();
                              return const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()));
                            }
                            return _buildActivityCard(_activities[index]);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  void _showFilterSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) => Container(
          padding: EdgeInsets.only(
            top: 24,
            left: 20,
            right: 20,
            bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                   const Text("Filtrlar", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                   const CloseButton(),
                ],
              ),
              const SizedBox(height: 24),
              
              const Text("Ta'lim turi", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
              const SizedBox(height: 8),
              _buildBottomSheetDropdown<String>(
                hint: "Barchasi",
                value: _selectedEducationType,
                items: ["Bakalavr", "Magistr"].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                onChanged: (val) async {
                  setState(() {
                    _selectedEducationType = val;
                    _selectedCourse = null;
                    _selectedSpecialty = null;
                    _selectedGroup = null;
                  });
                  setSheetState(() {}); // Sync sheet UI
                  _loadActivities(refresh: true);
                  await _loadSpecialties();
                  await _loadGroups();
                  setSheetState(() {}); // Sync sheet UI after async loads
                },
              ),
              const SizedBox(height: 16),

              const Text("Fakultet", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
              const SizedBox(height: 8),
              _buildBottomSheetDropdown<int>(
                hint: "Barchasi",
                value: _faculties.any((f) => f['id'] == _selectedFacultyId) ? _selectedFacultyId : null,
                items: _faculties.map((f) => DropdownMenuItem<int>(
                    value: f['id'],
                    child: Text(f['name'] ?? "", overflow: TextOverflow.ellipsis),
                )).toList(),
                onChanged: (val) async {
                  setState(() {
                    _selectedFacultyId = val;
                    _selectedSpecialty = null;
                    _selectedGroup = null;
                  });
                  setSheetState(() {});
                  _loadActivities(refresh: true);
                  await _loadSpecialties();
                  await _loadGroups();
                  setSheetState(() {});
                },
              ),
              const SizedBox(height: 16),

              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("Shakli", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                        const SizedBox(height: 8),
                        _buildBottomSheetDropdown<String>(
                          hint: "Barchasi",
                          value: _selectedEducationForm,
                          items: ["Kunduzgi", "Masofaviy", "Kechki", "Sirtqi"].map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
                          onChanged: (val) async {
                            setState(() {
                              _selectedEducationForm = val;
                              _selectedGroup = null;
                            });
                            setSheetState(() {});
                            _loadActivities(refresh: true);
                            await _loadGroups();
                            setSheetState(() {});
                          },
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("Kurs", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                        const SizedBox(height: 8),
                        _buildBottomSheetDropdown<String>(
                          hint: "Barchasi",
                          value: _selectedCourse,
                          items: (_selectedEducationType == "Magistr" ? ["1", "2"] : ["1", "2", "3", "4"])
                              .map((e) => DropdownMenuItem(value: e, child: Text("$e-kurs"))).toList(),
                          onChanged: (val) async {
                            setState(() {
                              _selectedCourse = val;
                              _selectedGroup = null;
                            });
                            setSheetState(() {});
                            _loadActivities(refresh: true);
                            await _loadGroups();
                            setSheetState(() {});
                          },
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              const Text("Yo'nalish", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
              const SizedBox(height: 8),
              _buildBottomSheetDropdown<String>(
                hint: "Barchasi",
                value: _specialties.contains(_selectedSpecialty) ? _selectedSpecialty : null,
                items: _specialties.map((s) => DropdownMenuItem(value: s, child: Text(s, overflow: TextOverflow.ellipsis))).toList(),
                onChanged: (val) async {
                  setState(() {
                    _selectedSpecialty = val;
                    _selectedGroup = null;
                  });
                  setSheetState(() {});
                  _loadActivities(refresh: true);
                  await _loadGroups();
                  setSheetState(() {});
                },
              ),
              const SizedBox(height: 16),

              const Text("Guruh", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
              const SizedBox(height: 8),
              _buildBottomSheetDropdown<String>(
                hint: "Barchasi",
                value: _groups.contains(_selectedGroup) ? _selectedGroup : null,
                items: _groups.map((g) => DropdownMenuItem(value: g, child: Text(g))).toList(),
                onChanged: (val) {
                  setState(() => _selectedGroup = val);
                  setSheetState(() {});
                  _loadActivities(refresh: true);
                },
              ),
              const SizedBox(height: 32),

              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).primaryColor,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  onPressed: () => Navigator.pop(context),
                  child: const Text("Tayyor", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBottomSheetDropdown<T>({
    required String hint,
    required T? value,
    required List<DropdownMenuItem<T>> items,
    required ValueChanged<T?> onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(16),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          isExpanded: true,
          hint: Text(hint, style: TextStyle(color: Colors.grey[600])),
          value: value,
          items: [
             DropdownMenuItem<T>(value: null, child: Text(hint)),
             ...items
          ],
          onChanged: onChanged,
        ),
      ),
    );
  }

  Widget _buildActivityCard(dynamic item) {
    final status = item['status'] ?? 'pending';
    final int id = int.tryParse(item['id'].toString()) ?? 0;
    Color statusColor = Colors.orange;
    if (status == 'confirmed') statusColor = Colors.green;
    if (status == 'rejected') statusColor = Colors.red;

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ListTile(
            title: Text(item['name'] ?? "Nomsiz", style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text("${item['student_full_name']} • ${item['category']}"),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
              child: Text(status.toUpperCase(), style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold)),
            ),
          ),
          if (item['description'] != null && item['description'].toString().isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Text(item['description'], style: TextStyle(color: Colors.grey[700])),
            ),
          
          if (item['images'] != null && (item['images'] as List).isNotEmpty)
            SizedBox(
              height: 150,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemCount: (item['images'] as List).length,
                itemBuilder: (context, idx) {
                   final String imageUrl = item['images'][idx];
                   return Padding(
                     padding: const EdgeInsets.all(4.0),
                     child: GestureDetector(
                       onTap: () {
                         showDialog(
                           context: context,
                           builder: (_) => Dialog(
                             backgroundColor: Colors.transparent,
                             child: Stack(
                               alignment: Alignment.topRight,
                               children: [
                                 InteractiveViewer(child: Image.network(imageUrl)),
                                 IconButton(icon: const Icon(Icons.close, color: Colors.white), onPressed: () => Navigator.pop(context)),
                               ],
                             ),
                           )
                         );
                       },
                       child: ClipRRect(
                         borderRadius: BorderRadius.circular(12),
                         child: Image.network(
                           imageUrl,
                           width: 150,
                           height: 150,
                           fit: BoxFit.cover,
                           errorBuilder: (context, error, stackTrace) => Container(
                             width: 150,
                             height: 150,
                             color: Colors.grey[200],
                             child: const Icon(Icons.broken_image, color: Colors.grey),
                           ),
                         ),
                       ),
                     ),
                   );
                },
              ),
            ),
          
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(item['date'] ?? "", style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                if (status == 'pending')
                  Row(
                    children: [
                      TextButton(onPressed: () => _reject(id), child: const Text("Rad etish", style: TextStyle(color: Colors.red))),
                      const SizedBox(width: 8),
                      ElevatedButton(onPressed: () => _approve(id), child: const Text("Tasdiqlash")),
                    ],
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return const Center(child: Text("Hozircha ma'lumot yo'q"));
  }
}
