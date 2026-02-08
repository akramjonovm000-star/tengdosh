import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';

class ManagementAiScreen extends StatefulWidget {
  const ManagementAiScreen({super.key});

  @override
  State<ManagementAiScreen> createState() => _ManagementAiScreenState();
}

class _ManagementAiScreenState extends State<ManagementAiScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  bool _isReportLoading = false;
  Map<String, dynamic>? _analytics;
  String? _aiReport;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final data = await _dataService.getManagementAnalytics();
    if (mounted) {
      setState(() {
        _analytics = data;
        _isLoading = false;
      });
    }
  }

  Future<void> _generateReport() async {
    setState(() => _isReportLoading = true);
    final report = await _dataService.getManagementAiReport();
    if (mounted) {
      setState(() {
        _aiReport = report;
        _isReportLoading = false;
      });
      _showReportResult();
    }
  }

  void _showReportResult() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.8,
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("AI Tahliliy Hisobot", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
              ],
            ),
            const Divider(),
            Expanded(
              child: SingleChildScrollView(
                child: SelectableText(
                  _aiReport ?? "Hisobot tayyorlanmoqda...",
                  style: const TextStyle(fontSize: 15, height: 1.5),
                ),
              ),
            ),
            const SizedBox(height: 10),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.pop(context);
                _generateReport(); // Regenerate
              }, 
              icon: const Icon(Icons.refresh), 
              label: const Text("Qayta shakllantirish"),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryBlue,
                foregroundColor: Colors.white,
                minimumSize: const Size(double.infinity, 50)
              ),
            )
          ],
        ),
      ),
    );
  }

  void _showDetail(String type) {
    if (_analytics == null) return;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.7,
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 15),
            Text(type, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const Divider(),
            Expanded(child: _buildDetailContent(type)),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailContent(String type) {
    switch (type) {
      case "Talabalar umumiy holati":
        return Column(
          children: [
            _buildStatRow("Jami talabalar", "${_analytics!['students']['total']}", Icons.people, Colors.blue),
            _buildStatRow("Premium (Faol)", "${_analytics!['students']['active']}", Icons.star, Colors.amber),
            _buildStatRow("24 soatda faol", "${_analytics!['students']['actions_24h']}", Icons.access_time, Colors.green),
          ],
        );
      case "Talabalar kayfiyati tahlili":
        final score = _analytics!['sentiment']['score'];
        return Column(
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: _getColorForSentiment(score).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Text(
                "$score",
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: _getColorForSentiment(score)),
              ),
            ),
            const SizedBox(height: 10),
            Text("Umumiy Kayfiyat Indeksi", style: TextStyle(color: Colors.grey[600])),
            const SizedBox(height: 20),
            _buildStatRow("So'nggi 7 kunlik postlar", "${_analytics!['sentiment']['posts_7d']}", Icons.article, Colors.blueGrey),
            _buildStatRow("So'nggi 7 kunlik izohlar", "${_analytics!['sentiment']['comments_7d']}", Icons.comment, Colors.blueGrey),
            _buildStatRow("AI bilan suhbatlar", "${_analytics!['sentiment']['ai_chats_7d']}", Icons.smart_toy, Colors.purple),
          ],
        );
      case "Fakultetlar bo‘yicha statistika":
         return _buildListContent(_analytics!['faculties'], Icons.school, Colors.blueGrey);
      case "Ilova faolligi":
         return Center(
           child: Column(
             mainAxisAlignment: MainAxisAlignment.center,
             children: [
               const Icon(Icons.touch_app, size: 60, color: Colors.purple),
               const SizedBox(height: 20),
               Text("${_analytics!['students']['actions_24h']}", style: const TextStyle(fontSize: 40, fontWeight: FontWeight.bold)),
               const Text("So'nggi 24 soatdagi harakatlar", style: TextStyle(color: Colors.grey)),
             ],
           ),
         );
      case "Muammolar va xavf signallari":
         return _buildListContent(_analytics!['risks'], Icons.warning_amber_rounded, Colors.redAccent);
      case "Rahbariyat uchun AI hisobot":
         return const SizedBox(); 
      default:
        return const Center(child: Text("Ma'lumot yo'q"));
    }
  }

  Widget _buildStatRow(String title, String value, IconData icon, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.grey[50], borderRadius: BorderRadius.circular(12)),
      child: Row(
        children: [
          Icon(icon, color: color),
          const SizedBox(width: 16),
          Expanded(child: Text(title, style: const TextStyle(fontSize: 16))),
          Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildListContent(List<dynamic> items, IconData icon, Color color) {
    if (items == null || items.isEmpty) return const Center(child: Text("Ma'lumot yo'q"));
    return ListView.separated(
      itemCount: items.length,
      separatorBuilder: (_, __) => const Divider(),
      itemBuilder: (context, index) {
        final item = items[index];
        return ListTile(
          leading: CircleAvatar(
             backgroundColor: color.withOpacity(0.1),
             child: Text("${index+1}", style: TextStyle(color: color, fontWeight: FontWeight.bold)),
          ),
          title: Text(item['name']),
          trailing: Text("${item['count']}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        );
      },
    );
  }

  Color _getColorForSentiment(dynamic score) {
    if (score is! int && score is! double) return Colors.grey;
    final s = score is int ? score : int.tryParse("$score") ?? 50;
    if (s >= 70) return Colors.green;
    if (s <= 40) return Colors.red;
    return Colors.amber;
  }

  // Exact Copy of UI Widget from AiScreen.dart
  Widget _buildAiButton(String text, IconData icon, VoidCallback onTap, {bool isPrimary = false}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            decoration: BoxDecoration(
              color: isPrimary ? AppTheme.primaryBlue : Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isPrimary ? AppTheme.primaryBlue : Colors.grey.withOpacity(0.1),
              ),
              boxShadow: isPrimary 
                  ? [BoxShadow(color: AppTheme.primaryBlue.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 4))]
                  : [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 4, offset: const Offset(0, 2))],
            ),
            child: Row(
              children: [
                Icon(icon, color: isPrimary ? Colors.white : AppTheme.primaryBlue, size: 24),
                const SizedBox(width: 16),
                Expanded(
                  child: Text(
                    text,
                    style: TextStyle(
                      color: isPrimary ? Colors.white : Colors.black87,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                if (_isLoading && !isPrimary) // Show loader only for stats if loading
                   const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                else if (isPrimary && _isReportLoading)
                   const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                else
                   Icon(Icons.chevron_right, color: isPrimary ? Colors.white54 : Colors.grey, size: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Rahbariyat AI", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadData)
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              "Universitet bo'yicha tahliliy ma'lumotlar va AI hisoboti:",
              style: TextStyle(color: Colors.grey[600], fontSize: 15),
              textAlign: TextAlign.start,
            ),
            const SizedBox(height: 20),

            _buildAiButton("Talabalar umumiy holati", Icons.people_alt, () => _showDetail("Talabalar umumiy holati")),
            _buildAiButton("Talabalar kayfiyati tahlili", Icons.sentiment_satisfied_alt, () => _showDetail("Talabalar kayfiyati tahlili")),
            _buildAiButton("Fakultetlar bo‘yicha statistika", Icons.school, () => _showDetail("Fakultetlar bo‘yicha statistika")),
            _buildAiButton("Ilova faolligi", Icons.touch_app, () => _showDetail("Ilova faolligi")),
            _buildAiButton("Muammolar va xavf signallari", Icons.warning_amber_rounded, () => _showDetail("Muammolar va xavf signallari")),
            
            const Divider(height: 30),
            
            _buildAiButton("Rahbariyat uchun AI hisobot", Icons.auto_awesome, () {
               if (_aiReport != null) {
                 _showReportResult();
               } else {
                 _generateReport();
               }
            }, isPrimary: true),
          ],
        ),
      ),
    );
  }
}
