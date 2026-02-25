import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../services/yetakchi_service.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

class YetakchiDocumentsScreen extends StatefulWidget {
  const YetakchiDocumentsScreen({Key? key}) : super(key: key);

  @override
  State<YetakchiDocumentsScreen> createState() => _YetakchiDocumentsScreenState();
}

class _YetakchiDocumentsScreenState extends State<YetakchiDocumentsScreen> {
   final YetakchiService _service = YetakchiService();
   final TextEditingController _searchCtrl = TextEditingController();
   final DateFormat _dateFormat = DateFormat('dd.MM.yyyy HH:mm');
   
   List<dynamic> _docs = [];
   bool _isLoading = true;
   String _searchQuery = "";

   @override
   void initState() {
     super.initState();
     _fetchDocs();
   }

   Future<void> _fetchDocs() async {
     setState(() => _isLoading = true);
     final results = await _service.getDocuments(search: _searchQuery, limit: 50);
     if (mounted) {
       setState(() {
         _docs = results;
         _isLoading = false;
       });
     }
   }

   Future<void> _openFile(String url) async {
     final uri = Uri.parse(url);
     if (await canLaunchUrl(uri)) {
       await launchUrl(uri, mode: LaunchMode.externalApplication);
     } else {
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Faylni ochishda xatolik")));
     }
   }

   @override
   Widget build(BuildContext context) {
     return Scaffold(
       backgroundColor: Colors.grey[50],
       appBar: AppBar(
         title: const Text("Hujjatlar Arvixi", style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold)),
         backgroundColor: Colors.white,
         elevation: 0,
         iconTheme: const IconThemeData(color: Colors.black87),
       ),
       body: Column(
         children: [
            Container(
              color: Colors.white,
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: _searchCtrl,
                decoration: InputDecoration(
                  hintText: "Hujjat turi orqali izlash...",
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _searchQuery.isNotEmpty 
                     ? IconButton(icon: const Icon(Icons.clear), onPressed: () {
                         _searchCtrl.clear();
                         setState(() => _searchQuery = "");
                         _fetchDocs();
                       })
                     : null,
                  filled: true,
                  fillColor: Colors.grey[100],
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none)
                ),
                onSubmitted: (val) {
                  setState(() => _searchQuery = val);
                  _fetchDocs();
                },
              ),
            ),
            Expanded(
              child: _isLoading 
                ? const Center(child: CircularProgressIndicator())
                : _docs.isEmpty 
                    ? const Center(child: Text("Hujjatlar mavjud emas"))
                    : _buildList()
            )
         ],
       )
     );
   }

   Widget _buildList() {
      return ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _docs.length,
        itemBuilder: (context, index) {
          final doc = _docs[index];
          DateTime date = DateTime.tryParse(doc['created_at']) ?? DateTime.now();

          return Card(
             elevation: 0,
             margin: const EdgeInsets.only(bottom: 12),
             shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.grey[200]!)),
             child: ListTile(
               contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
               leading: Container(
                 padding: const EdgeInsets.all(12),
                 decoration: BoxDecoration(color: Colors.indigo.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                 child: const Icon(Icons.description, color: Colors.indigo)
               ),
               title: Text(doc['document_type'] ?? 'Hujjat', style: const TextStyle(fontWeight: FontWeight.bold)),
               subtitle: Column(
                 crossAxisAlignment: CrossAxisAlignment.start,
                 children: [
                   const SizedBox(height: 4),
                   Row(
                     children: [
                       const Icon(Icons.person, size: 14, color: Colors.grey),
                       const SizedBox(width: 4),
                       Expanded(child: Text(doc['student_name'] ?? 'Noma\'lum', overflow: TextOverflow.ellipsis, style: TextStyle(color: Colors.grey[700], fontSize: 13))),
                     ],
                   ),
                   const SizedBox(height: 4),
                   Row(
                     children: [
                       const Icon(Icons.access_time, size: 14, color: Colors.grey),
                       const SizedBox(width: 4),
                       Text(_dateFormat.format(date), style: const TextStyle(fontSize: 12, color: Colors.blueGrey)),
                     ],
                   )
                 ]
               ),
               trailing: IconButton(
                  icon: const Icon(Icons.download, color: AppTheme.primaryBlue),
                  onPressed: () => _openFile(doc['file_url']),
               ),
             ),
          );
        }
      );
   }
}
