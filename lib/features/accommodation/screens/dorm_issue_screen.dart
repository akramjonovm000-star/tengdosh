import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme/app_theme.dart';
import '../../core/services/data_service.dart';
import '../models/dorm_models.dart';
import 'package:intl/intl.dart';

class DormIssueScreen extends StatefulWidget {
  const DormIssueScreen({super.key});

  @override
  State<DormIssueScreen> createState() => _DormIssueScreenState();
}

class _DormIssueScreenState extends State<DormIssueScreen> {
  final DataService _dataService = DataService();
  late Future<List<DormIssue>> _issuesFuture;
  final _descController = TextEditingController();
  String _selectedCategory = 'Santexnika';
  final List<String> _categories = ['Santexnika', 'Elektr', 'Mebel', 'Boshqa'];

  @override
  void initState() {
    super.initState();
    _fetchIssues();
  }

  void _fetchIssues() {
    setState(() {
      _issuesFuture = _dataService.getMyDormIssues().then((data) => data.map((j) => DormIssue.fromJson(j)).toList());
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Nosozliklarni bildirish"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      backgroundColor: AppTheme.backgroundWhite,
      body: FutureBuilder<List<DormIssue>>(
        future: _issuesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator(color: Colors.orange));
          }
          final issues = snapshot.data ?? [];
          return ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: issues.length,
            itemBuilder: (context, index) {
              final issue = issues[index];
              return _buildIssueCard(issue);
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddIssueDialog,
        backgroundColor: Colors.orange,
        icon: const Icon(Icons.add_rounded, color: Colors.white),
        label: const Text("Murojaat qoldirish", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
    );
  }

  Widget _buildIssueCard(DormIssue issue) {
    Color statusColor;
    String statusText;
    switch (issue.status) {
      case 'fixed': statusColor = Colors.green; statusText = "Tuzatildi"; break;
      case 'in_progress': statusColor = Colors.blue; statusText = "Jarayonda"; break;
      default: statusColor = Colors.orange; statusText = "Kutilmoqda";
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: Colors.orange.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                child: Text(issue.category, style: const TextStyle(color: Colors.orange, fontWeight: FontWeight.bold, fontSize: 12)),
              ),
              Text(statusText, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 13)),
            ],
          ),
          const SizedBox(height: 12),
          Text(issue.description, style: const TextStyle(fontSize: 15, color: Colors.black87)),
          const SizedBox(height: 12),
          if (issue.imageUrls.isNotEmpty)
            const Text("🖼 Rasmlar yuklangan", style: TextStyle(color: Colors.grey, fontSize: 12)),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
               Text(
                DateFormat('dd.MM.yyyy HH:mm').format(issue.createdAt),
                style: TextStyle(color: Colors.grey[400], fontSize: 11),
              ),
              if (issue.imageUrls.isEmpty && issue.status == 'pending')
                TextButton.icon(
                  onPressed: () => _openBot(issue.id),
                  icon: const Icon(Icons.photo_camera_rounded, size: 16),
                  label: const Text("Rasm yuklash", style: TextStyle(fontSize: 12)),
                ),
            ],
          ),
        ],
      ),
    );
  }

  void _showAddIssueDialog() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => StatefulBuilder(
        builder: (context, setModalState) => Padding(
          padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 24, right: 24, top: 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("Nosozlik haqida xabar berish", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 20),
              DropdownButtonFormField<String>(
                value: _selectedCategory,
                decoration: const InputDecoration(labelText: "Kategoriya"),
                items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) => setModalState(() => _selectedCategory = v!),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _descController,
                maxLines: 3,
                decoration: const InputDecoration(labelText: "Batafsil ma'lumot", border: OutlineInputBorder()),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _submitIssue,
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, padding: const EdgeInsets.symmetric(vertical: 16)),
                  child: const Text("Yuborish", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _submitIssue() async {
    if (_descController.text.trim().isEmpty) return;
    
    final result = await _dataService.createDormIssue(_selectedCategory, _descController.text);
    if (result['success'] == true) {
      Navigator.pop(context);
      _descController.clear();
      _fetchIssues();
      _showBotLink(result['id']);
    }
  }

  void _showBotLink(int id) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Murojaat qabul qilindi"),
        content: const Text("Nosozlikni rasmga olib Telegram bot orqali yuborishni xohlaysizmi?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Yo'q")),
          ElevatedButton(onPressed: () => _openBot(id), child: const Text("Telegramga o'tish")),
        ],
      ),
    );
  }

  Future<void> _openBot(int id) async {
    final url = Uri.parse("https://t.me/talabahamkorbot?start=report_dorm_issue_$id");
    if (await canLaunchUrl(url)) await launchUrl(url, mode: LaunchMode.externalApplication);
  }
}
