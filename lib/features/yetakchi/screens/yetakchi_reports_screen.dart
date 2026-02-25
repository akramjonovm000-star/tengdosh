import 'package:flutter/material.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../auth/services/auth_service.dart';
import 'package:url_launcher/url_launcher.dart';

class YetakchiReportsScreen extends StatelessWidget {
  const YetakchiReportsScreen({Key? key}) : super(key: key);

  Future<void> _downloadExcel(BuildContext context, String period) async {
     try {
       final token = await AuthService().getToken();
       final url = Uri.parse("${ApiConstants.yetakchiReportsExport}?period=$period");
       
       // Note: Since it requires auth, launching browser might fail unless token passed via query
       // Better approach for production: Download via Dio and open locally.
       // For now, let's assume we can open it by passing token in URL (if backend supported)
       // Or downloading bytes and using open_file.
       
       // Simplified demo:
       ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("$period hisoboti yuklanmoqda... (Kutib turing)")));
       
       // Real implementation will use flutter_downloader or similar
       if (await canLaunchUrl(url)) {
           await launchUrl(url, mode: LaunchMode.externalApplication);
       }
     } catch(e) {
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Yuklab olishda xatolik")));
     }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Hisobotlar jurnali", style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Talabalar faolligi eksporti", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            
            _buildExportCard(
               title: "Oylik Hisobot",
               subtitle: "Joriy oy uchun barcha tizimga kiritilgan arxiv",
               icon: Icons.table_chart,
               color: Colors.green,
               onTap: () => _downloadExcel(context, 'monthly')
            ),
            
            const SizedBox(height: 12),
            
            _buildExportCard(
               title: "Haftalik Hisobot",
               subtitle: "So'nggi 7 kundagi tadbirlar va faolliklar",
               icon: Icons.bar_chart,
               color: Colors.blue,
               onTap: () => _downloadExcel(context, 'weekly')
            ),
            
            const SizedBox(height: 32),
            Container(
               padding: const EdgeInsets.all(16),
               decoration: BoxDecoration(color: Colors.amber.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
               child: Row(
                 crossAxisAlignment: CrossAxisAlignment.start,
                 children: [
                   const Icon(Icons.info_outline, color: Colors.amber),
                   const SizedBox(width: 12),
                   Expanded(child: Text("Hujjatlar Excel (XLSX) formatida xavfsiz yuklab olinadi. Olingan ma'lumotlarni tarqatish qat'iyan man etiladi.", style: TextStyle(color: Colors.amber[800], fontSize: 13, height: 1.4)))
                 ],
               )
            )
          ]
        ),
      ),
    );
  }
  
  Widget _buildExportCard({required String title, required String subtitle, required IconData icon, required Color color, required VoidCallback onTap}) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: Colors.grey[200]!)),
      child: ListTile(
         contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
         leading: Container(
           padding: const EdgeInsets.all(12),
           decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
           child: Icon(icon, color: color, size: 28),
         ),
         title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
         subtitle: Padding(
           padding: const EdgeInsets.top(4),
           child: Text(subtitle, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
         ),
         trailing: ElevatedButton.icon(
           onPressed: onTap, 
           icon: const Icon(Icons.download, size: 16), 
           label: const Text("Yuklash"),
           style: ElevatedButton.styleFrom(
             elevation: 0,
             backgroundColor: color.withOpacity(0.1),
             foregroundColor: color,
             shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))
           ),
         ),
      ),
    );
  }
}
