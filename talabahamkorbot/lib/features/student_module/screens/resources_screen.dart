import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';

class ResourcesScreen extends StatefulWidget {
  final String subjectId;
  final String subjectName;

  const ResourcesScreen({
    super.key,
    required this.subjectId,
    required this.subjectName,
  });

  @override
  State<ResourcesScreen> createState() => _ResourcesScreenState();
}

class _ResourcesScreenState extends State<ResourcesScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _topics = [];
  Map<String, dynamic>? _subjectDetails;

  @override
  void dispose() {
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _loadResources();
    _loadDetails();
  }

  Future<void> _loadResources() async {
    final data = await _dataService.getResources(widget.subjectId);
    if (mounted) {
      setState(() {
        _topics = data;
        _isLoading = false;
      });
    }
  }

  Future<void> _loadDetails() async {
    final details = await _dataService.getSubjectDetails(widget.subjectId);
    if (mounted && details != null) {
      setState(() {
        _subjectDetails = details;
      });
    }
  }

  Future<void> _sendFileToBot(String url, String name) async {
    if (url.isEmpty) return;
    
    // Show Loading Feedback
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Botga yuborilmoqda... ⏳"), duration: Duration(seconds: 1)),
    );

    final success = await _dataService.sendResourceToBot(url, name);
    
    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Fayl Telegram botingizga yuborildi ✅"), backgroundColor: Colors.green),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(
             content: const Text("Xatolik: Bot ishga tushganligini tekshiring ❌"), 
             backgroundColor: Colors.red,
             action: SnackBarAction(label: "Botni ochish", onPressed: () async {
                 final botUrl = Uri.parse("https://t.me/talabahamkorbot"); 
                 if (await canLaunchUrl(botUrl)) launchUrl(botUrl, mode: LaunchMode.externalApplication);
             }),
           ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text(widget.subjectName, style: const TextStyle(color: Colors.black, fontSize: 16, fontWeight: FontWeight.bold), maxLines: 2),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                if (_subjectDetails != null) _buildSubjectHeader(),
                Expanded(
                  child: _topics.isEmpty
                    ? const Center(child: Text("Mavzular topilmadi"))
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                        itemCount: _topics.length,
                        itemBuilder: (context, index) {
                          final topic = _topics[index];
                          return _buildTopicItem(topic, index + 1);
                        },
                      ),
                ),
              ],
            ),
    );
  }

  Widget _buildSubjectHeader() {
    final teachers = (_subjectDetails!['teachers'] as List?)?.join(", ") ?? "Biriktirilmagan";
    final missed = _subjectDetails!['attendance']?['total_missed'] ?? 0;
    
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("Fan haqida", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
          const SizedBox(height: 4),
          Text("👨‍🏫 O'qituvchi: $teachers", style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const SizedBox(height: 4),
          Text("❌ Qoldirilgan darslar: $missed soat", style: const TextStyle(color: Colors.red, fontWeight: FontWeight.w600, fontSize: 14)),
        ],
      ),
    );
  }

  Widget _buildTopicItem(dynamic topic, int index) {
    final title = topic['title'] ?? "Mavzu";
    final files = topic['files'] as List<dynamic>? ?? [];

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.withOpacity(0.1)),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          initiallyExpanded: false,
          leading: CircleAvatar(
            radius: 14,
            backgroundColor: Colors.grey.withOpacity(0.1),
            child: Text(
              "$index",
              style: const TextStyle(fontSize: 12, color: Colors.black54, fontWeight: FontWeight.bold),
            ),
          ),
          title: Text(
            title,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
          children: [
            if (files.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16.0),
                child: Text("Fayllar topilmadi", style: TextStyle(color: Colors.grey, fontSize: 13)),
              )
            else
              ...files.map((file) => _buildFileAction(file)).toList(),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  Widget _buildFileAction(dynamic file) {
    final name = file['name'] ?? "Fayl";
    final url = file['url'] ?? "";

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 24),
      leading: const Icon(Icons.description_outlined, color: Colors.blue, size: 20),
      title: Text(
        name,
        style: const TextStyle(fontSize: 14, color: Colors.blue, fontWeight: FontWeight.w500),
      ),
      trailing: const Icon(Icons.download_rounded, color: Colors.grey, size: 20),
      onTap: () => _sendFileToBot(url, name),
    );
  }
}
