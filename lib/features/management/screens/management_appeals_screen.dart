import 'package:flutter/material.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import '../models/appeal_model.dart';
import '../services/appeal_service.dart';
import 'management_appeal_detail_screen.dart';
import 'package:intl/intl.dart';

class ManagementAppealsScreen extends StatefulWidget {
  const ManagementAppealsScreen({super.key});

  @override
  State<ManagementAppealsScreen> createState() => _ManagementAppealsScreenState();
}

class _ManagementAppealsScreenState extends State<ManagementAppealsScreen> with SingleTickerProviderStateMixin {
  final AppealService _service = AppealService();
  
  bool _isLoading = true;
  String? _error;
  AppealStats? _stats;
  List<Appeal> _appeals = [];
  
  // Filters
  String? _selectedStatus; // pending, processing, resolved
  String? _selectedFaculty;
  String? _selectedTopic;
  String? _selectedRole;
  
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }
  
  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    
    try {
      final stats = await _service.getStats();
      final appeals = await _service.getAppeals(
        status: _selectedStatus,
        faculty: _selectedFaculty,
        aiTopic: _selectedTopic,
        assignedRole: _selectedRole,
      );
      
      if (mounted) {
        setState(() {
          _stats = stats;
          _appeals = appeals;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _clusterAppeals() async {
    setState(() => _isLoading = true);
    try {
      final res = await _service.clusterAppeals();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(res['message'] ?? "Tahlil yakunlandi"), backgroundColor: Colors.green),
        );
        _loadData(); // Reload to see new topics
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Xatolik: $e"), backgroundColor: Colors.red),
        );
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Murojaatlar Tahlili", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          )
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppTheme.primaryBlue,
          unselectedLabelColor: Colors.grey,
          indicatorColor: AppTheme.primaryBlue,
          tabs: const [
            Tab(text: "Statistika"),
            Tab(text: "Ro'yxat"),
          ],
        ),
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : _error != null 
              ? Center(child: Text("Xatolik: $_error"))
              : Column(
                  children: [
                    Expanded(
                      child: TabBarView(
                        controller: _tabController,
                        children: [
                          _buildStatsTab(),
                          _buildListTab(),
                        ],
                      ),
                    ),
                    _buildAiClusteringButton(),
                  ],
                ),
    );
  }

  Widget _buildStatsTab() {
    if (_stats == null) return const SizedBox();
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Overview Cards
          Row(
            children: [
              Expanded(child: _buildStatCard("Jami", _stats!.total.toString(), Colors.blue)),
              const SizedBox(width: 8),
              Expanded(child: _buildStatCard("Kutilmoqda", _stats!.counts['pending'].toString(), Colors.orange)),
              const SizedBox(width: 8),
              Expanded(child: _buildStatCard("Yopilgan", (_stats!.counts['resolved']! + _stats!.counts['replied']!).toString(), Colors.green)),
            ],
          ),
          const SizedBox(height: 24),
          
          // 2. Faculty Performance
          const Text("Fakultetlar Kesimida", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _stats!.facultyPerformance.length,
            itemBuilder: (context, index) {
              final item = _stats!.facultyPerformance[index];
              return _buildFacultyRow(item);
            },
          ),
          
          const SizedBox(height: 24),
          
          // 3. Top Targets
          const Text("Murojaat Yo'nalishlari", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _stats!.topTargets.map((t) => ActionChip(
              label: Text("${t.role}: ${t.count}"),
              backgroundColor: _selectedRole == t.role ? AppTheme.primaryBlue.withOpacity(0.1) : Colors.grey[200],
              onPressed: () {
                setState(() {
                  _selectedRole = t.role;
                });
                _tabController.animateTo(1);
                _loadData();
              },
            )).toList(),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
  
  Widget _buildStatCard(String title, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))],
        border: Border.all(color: color.withOpacity(0.1)),
      ),
      child: Column(
        children: [
          Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 4),
          Text(title, style: TextStyle(fontSize: 13, color: Colors.grey[600])),
        ],
      ),
    );
  }
  
  Widget _buildFacultyRow(FacultyPerformance item) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(child: Text(item.faculty, style: const TextStyle(fontWeight: FontWeight.bold))),
              Text("${item.rate}% Yechim", style: TextStyle(color: item.rate > 80 ? Colors.green : (item.rate > 50 ? Colors.orange : Colors.red), fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: item.rate / 100,
            backgroundColor: Colors.grey[200],
            color: item.rate > 80 ? Colors.green : (item.rate > 50 ? Colors.orange : Colors.red),
            minHeight: 6,
            borderRadius: BorderRadius.circular(3),
          ),
          const SizedBox(height: 8),
          Text("Jami: ${item.total} | Kutilmoqda: ${item.pending} | Yopilgan: ${item.resolved}", style: TextStyle(fontSize: 12, color: Colors.grey[600])),
        ],
      ),
    );
  }

  Widget _buildListTab() {
    return Column(
      children: [
        // Filters
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              _buildFilterChip("Holat", _selectedStatus, ["pending", "processing", "resolved", "replied"], (v) => setState(() { _selectedStatus = v; _loadData(); })),
              const SizedBox(width: 8),
              // We could load faculties dynamically but for now lets rely on text input or just "Barchasi" reset
              if (_selectedFaculty != null) 
                 InputChip(
                   label: Text(_selectedFaculty!), 
                   onDeleted: () => setState(() { _selectedFaculty = null; _loadData(); }),
                   selected: true,
                   showCheckmark: false,
                 ),
              if (_selectedRole != null)
                const SizedBox(width: 8),
              if (_selectedRole != null)
                 InputChip(
                   label: Text("Kimga: $_selectedRole"), 
                   onDeleted: () => setState(() { _selectedRole = null; _loadData(); }),
                   selected: true,
                   showCheckmark: false,
                 ),
              // AI Topics filter could be added similarly if we fetch unique topics
            ],
          ),
        ),
        
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            itemCount: _appeals.length,
            itemBuilder: (context, index) {
              return _buildAppealCard(_appeals[index]);
            },
          ),
        ),
      ],
    );
  }
  
  Widget _buildFilterChip(String label, String? selectedValue, List<String> options, Function(String?) onSelected) {
    final Map<String, String> translations = {
      'pending': 'KUTILMOQDA',
      'processing': 'JARAYONDA',
      'resolved': 'HAL QILINDI',
      'replied': 'JAVOB BERILDI',
    };

    return DropdownButtonHideUnderline(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 0),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.grey[300]!)
        ),
        child: DropdownButton<String>(
          value: selectedValue,
          hint: Text(label),
          icon: const Icon(Icons.arrow_drop_down),
          onChanged: onSelected,
          items: [
            const DropdownMenuItem(value: null, child: Text("Barchasi")),
            ...options.map((o) => DropdownMenuItem(value: o, child: Text(translations[o] ?? o.toUpperCase()))),
          ],
        ),
      ),
    );
  }

  Widget _buildAppealCard(Appeal appeal) {
    Color statusColor = Colors.grey;
    String statusLabel = appeal.status.toUpperCase();
    
    if (appeal.status == 'pending') {
      statusColor = Colors.orange;
      statusLabel = "KUTILMOQDA";
    } else if (appeal.status == 'processing') {
      statusColor = Colors.blue;
      statusLabel = "JARAYONDA";
    } else if (appeal.status == 'resolved' || appeal.status == 'replied') {
      statusColor = Colors.green;
      statusLabel = appeal.status == 'resolved' ? "HAL QILINDI" : "JAVOB BERILDI";
    }
    
    return GestureDetector(
      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ManagementAppealDetailScreen(appealId: appeal.id))),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 8, offset: const Offset(0, 2))],
        ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (appeal.aiTopic != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  margin: const EdgeInsets.only(right: 8),
                  decoration: BoxDecoration(color: AppTheme.primaryBlue.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                ),
              Expanded(
                child: Row(
                  children: [
                    Expanded(child: Text(appeal.studentName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14))),
                    if (appeal.isAnonymous)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.grey[200],
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: const Text("ANONIM", style: TextStyle(color: Colors.grey, fontSize: 9, fontWeight: FontWeight.bold)),
                      ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                child: Text(statusLabel, style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text("${appeal.studentFaculty} | ${appeal.createdAt.split('T')[0]}", style: TextStyle(fontSize: 11, color: Colors.grey[500])),
          const SizedBox(height: 8),
          Text(appeal.text, style: const TextStyle(fontSize: 14), maxLines: 4, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("Kimga: ${appeal.assignedRole}", style: TextStyle(fontSize: 12, color: Colors.grey[600], fontStyle: FontStyle.italic)),
              if (appeal.status == 'pending' || appeal.status == 'processing')
                TextButton(
                  onPressed: () => _showReplyDialog(appeal.id),
                  child: const Text("Javob berish"),
                )
            ],
          ),
        ],
      ),
    ),
  );
}

  void _showReplyDialog(int id) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Murojaatga javob"),
        content: TextField(
          controller: controller,
          maxLines: 3,
          decoration: const InputDecoration(
            hintText: "Javob matnini kiriting...",
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Bekor qilish")),
          ElevatedButton(
            onPressed: () async {
              final text = controller.text.trim();
              if (text.isEmpty) return;
              
              Navigator.pop(context);
              await _replyToAppeal(id, text);
            },
            child: const Text("Yuborish"),
          ),
        ],
      ),
    );
  }
  
  Future<void> _replyToAppeal(int id, String text) async {
    try {
      await _service.replyAppeal(id, text);
      _loadData(); // Refresh
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Javob muvaffaqiyatli yuborildi"), backgroundColor: Colors.green)
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Xatolik: $e"), backgroundColor: Colors.red)
        );
      }
    }
  }

  Future<void> _resolveAppeal(int id) async {
    try {
      await _service.resolveAppeal(id);
      _loadData(); // Refresh
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Murojaat yopildi"), backgroundColor: Colors.green));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Xatolik: $e"), backgroundColor: Colors.red));
    }
  }

  Widget _buildAiClusteringButton() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -4),
          )
        ],
      ),
      child: ElevatedButton.icon(
        onPressed: _clusterAppeals,
        icon: const Icon(Icons.auto_awesome),
        label: const Text("AI BILAN MAVZULARGA AJRATISH", style: TextStyle(fontWeight: FontWeight.bold)),
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.primaryBlue,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          elevation: 0,
        ),
      ),
    );
  }
}
