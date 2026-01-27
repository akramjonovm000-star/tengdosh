import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';
import '../widgets/document_upload_dialog.dart';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _documents = [];

  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }

  Future<void> _loadDocuments() async {
    setState(() => _isLoading = true);
    final docs = await _dataService.getDocuments();
    if (mounted) {
      setState(() {
        _documents = docs;
        _isLoading = false;
      });
    }
  }

  void _showUploadDialog() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: DocumentUploadDialog(
          onUploadSuccess: _loadDocuments,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Hujjatlar", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: RefreshIndicator(
        onRefresh: _loadDocuments,
        color: AppTheme.primaryBlue,
        child: _isLoading && _documents.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_documents.isEmpty) {
      return Stack(
        children: [
          ListView(physics: const AlwaysScrollableScrollPhysics()), // For pull-to-refresh
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.folder_copy_outlined, size: 80, color: Colors.grey[200]),
                const SizedBox(height: 16),
                Text(
                  "Hujjatlar yo'q",
                  style: TextStyle(color: Colors.grey[400], fontSize: 16, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                Text(
                  "Hali hech qanday hujjat yuklanmagan",
                  style: TextStyle(color: Colors.grey[400], fontSize: 13),
                ),
              ],
            ),
          ),
          Positioned(bottom: 0, left: 0, right: 0, child: _buildBottomButton()),
        ],
      );
    }

    return Column(
      children: [
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.all(20),
            itemCount: _documents.length,
            separatorBuilder: (_, __) => const SizedBox(height: 16),
            itemBuilder: (context, index) {
              final doc = _documents[index];
              final isPdf = doc['type'] == 'document' || (doc['title'] ?? '').toLowerCase().contains('.pdf');
              
              return Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.04),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    )
                  ],
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  leading: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isPdf ? Colors.red[50] : Colors.blue[50],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      isPdf ? Icons.picture_as_pdf_rounded : Icons.description_rounded,
                      color: isPdf ? Colors.red : Colors.blue,
                    ),
                  ),
                  title: Text(
                    doc['title'] as String,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  subtitle: Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Row(
                      children: [
                        Icon(Icons.calendar_today_rounded, size: 12, color: Colors.grey[500]),
                        const SizedBox(width: 4),
                        Text(
                          doc['created_at'] as String,
                          style: TextStyle(color: Colors.grey[500], fontSize: 12),
                        ),
                        const SizedBox(width: 12),
                        Text(
                          doc['category'] as String,
                          style: TextStyle(color: AppTheme.primaryBlue.withOpacity(0.8), fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.red[50],
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: IconButton(
                          icon: const Icon(Icons.delete_outline_rounded, color: Colors.redAccent),
                          onPressed: () => _confirmDelete(doc['id'], doc['title']),
                          tooltip: "O'chirish",
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.blue[50],
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: IconButton(
                          icon: const Icon(Icons.telegram_rounded, color: AppTheme.primaryBlue),
                          onPressed: () => _sendToBot(doc['id']),
                          tooltip: "Botda ko'rish",
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        _buildBottomButton(),
      ],
    );
  }

  Widget _buildBottomButton() {
    return Container(
      padding: const EdgeInsets.all(20),
      color: Colors.transparent, // Let background show
      child: SafeArea(
        child: SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: _showUploadDialog,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 4,
              shadowColor: AppTheme.primaryBlue.withOpacity(0.3),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.add_to_photos_rounded, color: Colors.white),
                SizedBox(width: 10),
                Text(
                  "Hujjat yuklash",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
  Future<void> _confirmDelete(int docId, String title) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Hujjatni o'chirish"),
        content: Text("Rostdan ham '$title' hujjatini o'chirmoqchimisiz?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("Bekor qilish")),
          TextButton(
            onPressed: () => Navigator.pop(context, true), 
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text("O'chirish"),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _deleteDoc(docId);
    }
  }

  Future<void> _deleteDoc(int docId) async {
    final success = await _dataService.deleteDocument(docId);
    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Hujjat muvaffaqiyatli o'chirildi"), backgroundColor: Colors.green));
        _loadDocuments();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("O'chirishda xatolik yuz berdi"), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _sendToBot(int docId) async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Hujjat botga yuborilmoqda...")),
    );
    
    final msg = await _dataService.sendDocumentToBot(docId);
    if (mounted && msg != null) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg),
          backgroundColor: msg.toLowerCase().contains("xato") ? Colors.red : Colors.green,
        ),
      );
    }
  }
}
