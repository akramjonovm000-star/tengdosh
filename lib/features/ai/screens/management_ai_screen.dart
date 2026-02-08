import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
// Import DashboardCard - assuming it's accessible or we redefine it locally for independence
import '../../student_module/widgets/student_dashboard_widgets.dart'; 

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
    // If opened in modal, we might need state management there, but for now we keep state here
    // and show result in a new dialog/sheet.
    final report = await _dataService.getManagementAiReport();
    if (mounted) {
      setState(() {
        _aiReport = report;
        _isReportLoading = false;
      });
      // Auto-show report if it was triggered
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
         // Should not happen as button handles logic, but placeholder
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
    // ignore: unnecessary_null_comparison
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
    // ignore: unnecessary_type_check
    if (score is! int && score is! double) return Colors.grey;
    final s = score is int ? score : int.tryParse("$score") ?? 50;
    if (s >= 70) return Colors.green;
    if (s <= 40) return Colors.red;
    return Colors.amber;
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
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : _analytics == null 
              ? Center(child: Text("Ma'lumot yuklashda xatolik", style: const TextStyle(color: Colors.red)))
              : Padding(
                  padding: const EdgeInsets.all(16),
                  child: GridView.count(
                    crossAxisCount: 2,
                    crossAxisSpacing: 16,
                    mainAxisSpacing: 16,
                    childAspectRatio: 1.1,
                    children: [
                      DashboardCard(
                        title: "Talabalar umumiy holati",
                        icon: Icons.people_alt,
                        color: Colors.blue,
                        onTap: () => _showDetail("Talabalar umumiy holati"),
                      ),
                      DashboardCard(
                        title: "Talabalar kayfiyati tahlili",
                        icon: Icons.sentiment_satisfied_alt,
                        color: Colors.green,
                        onTap: () => _showDetail("Talabalar kayfiyati tahlili"),
                      ),
                      DashboardCard(
                        title: "Fakultetlar bo‘yicha statistika",
                        icon: Icons.school,
                        color: Colors.orange,
                        onTap: () => _showDetail("Fakultetlar bo‘yicha statistika"),
                      ),
                      DashboardCard(
                        title: "Ilova faolligi",
                        icon: Icons.touch_app,
                        color: Colors.purple,
                        onTap: () => _showDetail("Ilova faolligi"),
                      ),
                      DashboardCard(
                        title: "Muammolar va xavf signallari",
                        icon: Icons.warning_amber_rounded,
                        color: Colors.redAccent,
                        onTap: () => _showDetail("Muammolar va xavf signallari"),
                      ),
                      _buildReportButton(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildReportButton() {
     return InkWell(
      onTap: _isReportLoading ? null : () {
        if (_aiReport != null) {
          _showReportResult();
        } else {
          _generateReport();
        }
      },
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Color(0xFF6C5CE7), Color(0xFFA29BFE)]),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(color: const Color(0xFF6C5CE7).withOpacity(0.3), blurRadius: 10, offset: const Offset(0, 4)),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (_isReportLoading)
               const CircularProgressIndicator(color: Colors.white)
            else
               const Icon(Icons.auto_awesome, size: 32, color: Colors.white),
            const SizedBox(height: 12),
            const Text(
              "Rahbariyat uchun AI hisobot",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ],
        ),
      ),
    );
  }
}
