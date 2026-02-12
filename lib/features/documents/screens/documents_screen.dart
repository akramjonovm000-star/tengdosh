import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
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

  // Tab 1 Data
  bool _isHemisLoading = true;
  List<dynamic> _hemisDocuments = [];

  // Tab 2 Data
  bool _isUserDocsLoading = true;
  List<dynamic> _userDocuments = [];

  @override
  void initState() {
    super.initState();
    _loadAllData();
  }

  Future<void> _loadAllData() async {
    _loadHemisDocs();
    _loadUserDocs();
  }

  Future<void> _loadHemisDocs() async {
    setState(() => _isHemisLoading = true);
    try {
      final docs = await _dataService.getHemisDocuments();
      if (mounted) {
        setState(() {
          _hemisDocuments = docs;
          _isHemisLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isHemisLoading = false);
    }
  }

  Future<void> _loadUserDocs() async {
    setState(() => _isUserDocsLoading = true);
    try {
      final docs = await _dataService.getMyDocuments();
      if (mounted) {
        setState(() {
          _userDocuments = docs;
          _isUserDocsLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isUserDocsLoading = false);
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
          onUploadSuccess: _loadUserDocs,
        ),
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
          title: const Text("Hujjatlar", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          backgroundColor: Colors.white,
          elevation: 0,
          iconTheme: const IconThemeData(color: Colors.black),
          bottom: const TabBar(
            labelColor: AppTheme.primaryBlue,
            unselectedLabelColor: Colors.grey,
            indicatorColor: AppTheme.primaryBlue,
            tabs: [
              Tab(text: "HEMIS Hujjatlar"),
              Tab(text: "Qo'shimcha Hujjatlar"),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildHemisTab(),
            _buildUserDocsTab(),
          ],
        ),
      ),
    );
  }

  // --- TAB 1: HEMIS Documents ---
  Widget _buildHemisTab() {
    return RefreshIndicator(
      onRefresh: _loadHemisDocs,
      child: _isHemisLoading
          ? const Center(child: CircularProgressIndicator())
          : _hemisDocuments.isEmpty
              ? _buildEmptyState("HEMIS hujjatlari topilmadi", onRefresh: _loadHemisDocs)
              : ListView.separated(
                  padding: const EdgeInsets.all(20),
                  itemCount: _hemisDocuments.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 16),
                  itemBuilder: (context, index) {
                    final doc = _hemisDocuments[index];
                    return _buildHemisDocItem(doc);
                  },
                ),
    );
  }

  Widget _buildHemisDocItem(dynamic doc) {
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
            color: Colors.blue.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Icon(Icons.description_rounded, color: Colors.blue),
        ),
        title: Text(
          doc['name'] ?? "Nomsiz hujjat",
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (doc['attributes'] != null)
              ...(doc['attributes'] as List).take(2).map((attr) => 
                Text("${attr['label']}: ${attr['value']}", style: const TextStyle(fontSize: 12, color: Colors.grey))
              ),
          ],
        ),
        trailing: Container(
          decoration: BoxDecoration(
            color: Colors.green.withOpacity(0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: IconButton(
            icon: const Icon(Icons.download_rounded, color: Colors.green),
            onPressed: () => _openUrl(doc['file']),
            tooltip: "Yuklab olish",
          ),
        ),
      ),
    );
  }

  Future<void> _openUrl(String? url) async {
    if (url == null) return;
    try {
      await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Xatolik: $e"), backgroundColor: Colors.red),
      );
    }
  }

  // --- TAB 2: User Documents ---
  Widget _buildUserDocsTab() {
    return RefreshIndicator(
      onRefresh: _loadUserDocs,
      child: _isUserDocsLoading && _userDocuments.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : _userDocuments.isEmpty
              ? Stack(
                  children: [
                    ListView(), // specific Pull-to-refresh need scrollable
                    Center(child: _buildEmptyState("Hali hech qanday hujjat yuklanmagan", onRefresh: _loadUserDocs)),
                    Positioned(bottom: 0, left: 0, right: 0, child: _buildUploadButton()),
                  ],
                )
              : Column(
                  children: [
                    Expanded(
                      child: ListView.separated(
                        padding: const EdgeInsets.all(20),
                        itemCount: _userDocuments.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 16),
                        itemBuilder: (context, index) {
                          final doc = _userDocuments[index];
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
                    _buildUploadButton(),
                  ],
                ),
    );
  }

  Widget _buildEmptyState(String message, {VoidCallback? onRefresh}) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withOpacity(0.05),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.folder_off_outlined, size: 60, color: AppTheme.primaryBlue.withOpacity(0.5)),
          ),
          const SizedBox(height: 24),
          Text(
            message,
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 16,
              fontWeight: FontWeight.w600
            ),
            textAlign: TextAlign.center,
          ),
          if (onRefresh != null) ...[
            const SizedBox(height: 16),
            TextButton.icon(
              onPressed: onRefresh,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text("Yangilash"),
              style: TextButton.styleFrom(
                foregroundColor: AppTheme.primaryBlue,
              ),
            ),
          ]
        ],
      ),
    );
  }

  Widget _buildUploadButton() {
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
        _loadUserDocs();
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
