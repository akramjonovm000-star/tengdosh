import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/features/tutor/screens/group_documents_screen.dart';
import 'package:talabahamkor_mobile/core/localization/app_dictionary.dart';
import 'package:url_launcher/url_launcher.dart';

class TutorDocumentsGroupsScreen extends StatefulWidget {
  const TutorDocumentsGroupsScreen({super.key});

  @override
  State<TutorDocumentsGroupsScreen> createState() => _TutorDocumentsGroupsScreenState();
}

class _TutorDocumentsGroupsScreenState extends State<TutorDocumentsGroupsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  final DataService _dataService = DataService();
  bool _isLoadingStats = true;
  bool _isLoadingAll = true;

  List<dynamic> _stats = [];
  List<dynamic> _allStudents = [];
  List<dynamic> _filteredStudents = [];
  List<String> _groups = [];

  // Filters
  String _searchQuery = '';
  String? _selectedGroup;
  String? _selectedType; // e.g. "Barchasi", "Passport", "Sertifikat", "Diplom", "Rezyume", "Obyektivka"

  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadStats();
    _loadAllDocuments();
  }
  
  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadStats() async {
    setState(() => _isLoadingStats = true);
    final stats = await _dataService.getTutorDocumentStats();
    if (mounted) {
      setState(() {
        _stats = stats ?? [];
        _isLoadingStats = false;
      });
    }
  }

  Future<void> _loadAllDocuments() async {
    setState(() => _isLoadingAll = true);
    final allData = await _dataService.getAllDocumentDetails();
    if (mounted) {
      setState(() {
        _allStudents = allData ?? [];
        _filteredStudents = List.from(_allStudents);
        
        // Extract unique groups
        final Set<String> groupSet = {};
        for (var s in _allStudents) {
           if (s['group'] != null && s['group'].toString().isNotEmpty) {
              groupSet.add(s['group'].toString());
           }
        }
        _groups = groupSet.toList()..sort();
        _isLoadingAll = false;
      });
    }
  }

  void _applyFilters() {
    setState(() {
      _filteredStudents = _allStudents.where((student) {
        // Name search
        if (_searchQuery.isNotEmpty) {
          final name = (student['full_name'] ?? '').toString().toLowerCase();
          if (!name.contains(_searchQuery.toLowerCase())) return false;
        }
        
        // Group filter
        if (_selectedGroup != null && _selectedGroup != "Barchasi") {
          if (student['group'] != _selectedGroup) return false;
        }
        
        // Type filter (Shows students who DO NOT have the selected document)
        if (_selectedType != null && _selectedType != "Barchasi") {
           final docs = student['documents'] as List<dynamic>? ?? [];
           String cat = _selectedType!.toLowerCase();
           
           bool hasDoc = docs.any((d) {
              String docCat = (d['category'] ?? '').toString().toLowerCase();
              return docCat == cat;
           });
           
           // IF they already have it, filter them out so we only see those missing it
           if (hasDoc) return false;
        }

        return true;
      }).toList();
    });
  }

  Widget _buildStudentsTab() {
    if (_isLoadingAll) {
      return const Center(child: CircularProgressIndicator());
    }

    return GestureDetector(
      onTap: () => FocusScope.of(context).unfocus(),
      child: Column(
        children: [
          // Filter Section
          Container(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, 4)
                )
              ]
            ),
            child: Column(
              children: [
                // Top Search Bar
                TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: "Talaba F.I.Sh b'yicha qidiruv...",
                    prefixIcon: const Icon(Icons.search, color: Colors.grey),
                    suffixIcon: _searchController.text.isNotEmpty 
                        ? IconButton(
                            icon: const Icon(Icons.clear, color: Colors.grey),
                            onPressed: () {
                               _searchController.clear();
                               _searchQuery = '';
                               _applyFilters();
                            },
                          )
                        : null,
                    filled: true,
                    fillColor: Colors.grey[100],
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(vertical: 0)
                  ),
                  onChanged: (val) {
                    _searchQuery = val;
                    _applyFilters();
                  },
                ),
                const SizedBox(height: 12),
                
                // Dropdown Filters Row
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                           color: Colors.indigo.withOpacity(0.05),
                           borderRadius: BorderRadius.circular(12),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            isExpanded: true,
                            hint: const Text("Guruhlar", style: TextStyle(fontSize: 14)),
                            value: _selectedGroup,
                            icon: const Icon(Icons.arrow_drop_down, color: Colors.indigo),
                            items: ["Barchasi", ..._groups].map((g) {
                               return DropdownMenuItem(value: g, child: Text(g, style: const TextStyle(fontSize: 14), overflow: TextOverflow.ellipsis));
                            }).toList(),
                            onChanged: (val) {
                               setState(() => _selectedGroup = val);
                               _applyFilters();
                            },
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                           color: Colors.teal.withOpacity(0.05),
                           borderRadius: BorderRadius.circular(12),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            isExpanded: true,
                            hint: const Text("Turi", style: TextStyle(fontSize: 14)),
                            value: _selectedType,
                            icon: const Icon(Icons.arrow_drop_down, color: Colors.teal),
                            items: ["Barchasi", "Passport", "Sertifikat", "Diplom", "Rezyume", "Obyektivka"].map((s) {
                               return DropdownMenuItem(value: s, child: Text(s, style: const TextStyle(fontSize: 14), overflow: TextOverflow.ellipsis));
                            }).toList(),
                            onChanged: (val) {
                               setState(() => _selectedType = val);
                               _applyFilters();
                            },
                          ),
                        ),
                      ),
                    ),
                  ],
                )
              ],
            ),
          ),
          
          // Result List
          Expanded(
            child: _filteredStudents.isEmpty 
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.search_off_rounded, size: 64, color: Colors.grey[400]),
                      const SizedBox(height: 16),
                      Text("Talabalar topilmadi", style: TextStyle(color: Colors.grey[600], fontSize: 16)),
                    ],
                  )
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _filteredStudents.length,
                  itemBuilder: (context, index) {
                    final student = _filteredStudents[index];
                    final docs = student['documents'] as List<dynamic>? ?? [];
                    
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      elevation: 0,
                      color: Colors.white,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                CircleAvatar(
                                  radius: 24,
                                  backgroundImage: student['image'] != null && student['image'].isNotEmpty 
                                      ? NetworkImage(student['image']) 
                                      : null,
                                  backgroundColor: Colors.grey[200],
                                  child: (student['image'] == null || student['image'].isEmpty)
                                      ? const Icon(Icons.person, color: Colors.grey)
                                      : null,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        student['full_name'] ?? 'Ism kiritilmagan',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                      ),
                                      const SizedBox(height: 4),
                                      Row(
                                        children: [
                                          Flexible(
                                            child: Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: Colors.indigo.withOpacity(0.1),
                                                borderRadius: BorderRadius.circular(8)
                                              ),
                                              child: Text(
                                                student['group'] ?? '',
                                                style: const TextStyle(fontSize: 12, color: Colors.indigo, fontWeight: FontWeight.bold),
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                            ),
                                          ),
                                          const SizedBox(width: 8),
                                          Text(
                                            student['hemis_id'] ?? '',
                                            style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                                          )
                                        ],
                                      )
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            if (docs.isNotEmpty) const Padding(
                              padding: EdgeInsets.only(top: 12, bottom: 8),
                              child: Divider(height: 1),
                            ),
                            if (docs.isNotEmpty)
                              Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                children: docs.map<Widget>((doc) {
                                  bool isCert = doc['type'] == 'certificate';
                                  return InkWell(
                                    onTap: () {
                                       // Open document using URL or perform download
                                       String? url = doc['file_url'];
                                       if(url != null && url.isNotEmpty) {
                                          _openDocument(url);
                                       }
                                    },
                                    borderRadius: BorderRadius.circular(8),
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                      decoration: BoxDecoration(
                                        color: isCert ? Colors.amber.withOpacity(0.15) : Colors.blueGrey.withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(8),
                                        border: Border.all(color: isCert ? Colors.amber.withOpacity(0.5) : Colors.blueGrey.withOpacity(0.3))
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(
                                            isCert ? Icons.workspace_premium_rounded : Icons.description_rounded,
                                            size: 14,
                                            color: isCert ? Colors.orange[800] : Colors.blueGrey[700]
                                          ),
                                          const SizedBox(width: 6),
                                          Text(
                                            doc['title'] ?? 'Yuklagan',
                                            style: TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.w600,
                                              color: isCert ? Colors.orange[900] : Colors.blueGrey[800]
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  );
                                }).toList(),
                              )
                            else if(docs.isEmpty) 
                               Padding(
                                 padding: const EdgeInsets.only(top: 12.0),
                                 child: Row(
                                   children: [
                                     Icon(Icons.warning_amber_rounded, size: 16, color: Colors.orange[400]),
                                     const SizedBox(width: 6),
                                     Text("Hujjatlar yuklanmagan", style: TextStyle(fontSize: 13, color: Colors.grey[600], fontStyle: FontStyle.italic)),
                                   ],
                                 ),
                               ),
                            const SizedBox(height: 8),
                            Align(
                               alignment: Alignment.centerRight,
                               child: TextButton.icon(
                                 onPressed: () => _sendRequestMessage(student['id']),
                                 icon: const Icon(Icons.send_rounded, size: 16, color: Colors.indigo),
                                 label: const Text("Xabar yuborish", style: TextStyle(color: Colors.indigo, fontSize: 13, fontWeight: FontWeight.bold)),
                                 style: TextButton.styleFrom(
                                     backgroundColor: Colors.indigo.withOpacity(0.05),
                                     shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                     padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8)
                                 ),
                               ),
                            )
                          ],
                        ),
                      ),
                    );
                  },
                ),
          )
        ],
      )
    );
  }

    void _openDocument(String path) async {
       String completeUrl = path;
       if (path.startsWith("/")) {
          completeUrl = "https://tengdosh.com$path";
       }
     final Uri url = Uri.parse(completeUrl);
     if (await canLaunchUrl(url)) {
        await launchUrl(url, mode: LaunchMode.externalApplication);
     }
  }

  Future<void> _sendRequestMessage(int studentId) async {
      String? category = (_selectedType != null && _selectedType != "Barchasi") 
          ? _selectedType!.toLowerCase() 
          : "all";
      
      showDialog(
          context: context, 
          barrierDismissible: false,
          builder: (_) => const Center(child: CircularProgressIndicator())
      );
      
      bool success = await _dataService.sendDocumentRequest(studentId, category);
      
      if (mounted) {
         Navigator.pop(context); // Close loading dialog
         ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
               content: Text(success ? "Xabar muvaffaqiyatli yuborildi!" : "Xabar yuborishda xatolik yuz berdi."),
               backgroundColor: success ? Colors.green : Colors.red,
            )
         );
      }
  }

  Widget _buildGroupsTab() {
    if (_isLoadingStats) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_stats.isEmpty) {
       return Center(child: Text(AppDictionary.tr(context, 'msg_no_assigned_groups')));
    }

    return RefreshIndicator(
      onRefresh: () async {
         await _loadStats();
         await _loadAllDocuments();
      },
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _stats.length,
        itemBuilder: (context, index) {
          final item = _stats[index];
          final total = item['total_students'] ?? 0;
          final uploaded = item['uploaded_students'] ?? 0;
          final percent = total > 0 ? (uploaded / total) : 0.0;
          
          final String fullGroup = item['group_number']?.toString() ?? "";
          final List<String> groupParts = fullGroup.split(" ");
          final String groupCode = groupParts.isNotEmpty ? groupParts[0] : "";
          final String groupDirection = groupParts.length > 1 ? groupParts.sublist(1).join(" ") : "";

          return Card(
            margin: const EdgeInsets.only(bottom: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: Colors.grey.withOpacity(0.1)),
            ),
            elevation: 2,
            shadowColor: Colors.black12,
            color: Colors.white,
            child: InkWell(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => GroupDocumentsScreen(
                      groupNumber: item['group_number'],
                    ),
                  ),
                ).then((_) {
                   FocusScope.of(context).unfocus();
                   _loadStats();
                   _loadAllDocuments();
                });
              },
              borderRadius: BorderRadius.circular(16),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Guruh: $groupCode",
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                              ),
                              if (groupDirection.isNotEmpty)
                                Padding(
                                  padding: const EdgeInsets.only(top: 4.0),
                                  child: Text(
                                    groupDirection,
                                    style: TextStyle(color: Colors.grey[600], fontSize: 13, fontWeight: FontWeight.w500),
                                  ),
                                ),
                            ],
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                             color: AppTheme.primaryBlue.withOpacity(0.1),
                             shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: AppTheme.primaryBlue),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          "Yuklaganlar: $uploaded / $total",
                          style: TextStyle(color: Colors.grey[700], fontWeight: FontWeight.w600),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: percent == 1.0 ? Colors.green.withOpacity(0.1) : AppTheme.primaryBlue.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8)
                          ),
                          child: Text(
                            "${(percent * 100).toInt()}%",
                            style: TextStyle(
                               color: percent == 1.0 ? Colors.green[700] : AppTheme.primaryBlue, 
                               fontWeight: FontWeight.bold,
                               fontSize: 14
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: percent,
                        backgroundColor: Colors.grey[100],
                        color: percent == 1.0 ? Colors.green : AppTheme.primaryBlue,
                        minHeight: 8,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: AppTheme.backgroundWhite,
        appBar: AppBar(
          title: Text(AppDictionary.tr(context, 'lbl_docs_stats')),
          centerTitle: false,
          elevation: 1,
          bottom: TabBar(
            controller: _tabController,
            labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w500, fontSize: 15),
            indicatorColor: AppTheme.primaryBlue,
            indicatorWeight: 3,
            tabs: const [
              Tab(text: "Qidiruv"),
              Tab(text: "Guruhlar"),
            ],
          ),
        ),
        body: TabBarView(
          controller: _tabController,
          children: [
            _buildStudentsTab(),
            _buildGroupsTab(),
          ],
        ),
      ),
    );
  }
}
