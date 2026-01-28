import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
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
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppTheme.primaryBlue,
          unselectedLabelColor: Colors.grey,
          indicatorColor: AppTheme.primaryBlue,
          indicatorWeight: 3,
          labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
          tabs: const [
            Tab(text: "HEMIS Hujjatlari"),
            Tab(text: "Qo'shimcha hujjatlar"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildHemisDocsTab(),
          _buildPersonalDocsTab(),
        ],
      ),
    );
  }

  // =========================================================================
  // 1. HEMIS TAB
  // =========================================================================

  Widget _buildHemisDocsTab() {
    final hemisDocs = [
      {
        "title": "O'qish joyidan ma'lumotnoma", 
        "subtitle": "Talabalikni tasdiqlovchi hujjat",
        "icon": Icons.assignment_ind_rounded,
        "color": Colors.blue
      },
      {
        "title": "Reyting daftarchasi (Transkript)", 
        "subtitle": "Barcha fanlar va baholar tarixi",
        "icon": Icons.grade_rounded,
        "color": Colors.orange
      },
      {
        "title": "Buyruqlar ko'chirmasi", 
        "subtitle": "O'qishga qabul, ko'chirish va h.k.",
        "icon": Icons.gavel_rounded,
        "color": Colors.purple
      },
      {
        "title": "To'lov kontrakt shartnomasi", 
        "subtitle": "Joriy o'quv yili uchun shartnoma",
        "icon": Icons.description_rounded,
        "color": Colors.green
      },
    ];

    return ListView.separated(
      padding: const EdgeInsets.all(20),
      itemCount: hemisDocs.length,
      separatorBuilder: (_, __) => const SizedBox(height: 16),
      itemBuilder: (context, index) {
        final doc = hemisDocs[index];
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
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: (doc['color'] as Color).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(doc['icon'] as IconData, color: doc['color'] as Color),
            ),
            title: Text(
              doc['title'] as String,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            subtitle: Text(
              doc['subtitle'] as String,
              style: TextStyle(color: Colors.grey[600], fontSize: 13),
            ),
            trailing: IconButton(
              icon: const Icon(Icons.download_rounded, color: AppTheme.primaryBlue),
              onPressed: () async {
                final typeMap = {
                  "O'qish joyidan ma'lumotnoma": "reference",
                  "Reyting daftarchasi (Transkript)": "transcript",
                  "Buyruqlar ko'chirmasi": "orders",
                  "To'lov kontrakt shartnomasi": "contract"
                };
                
                final type = typeMap[doc['title']] ?? "reference";
                
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("So'rov yuborilmoqda..."))
                );
                
                final DataService ds = DataService();
                final msg = await ds.requestDocument(type);
                
                if (context.mounted && msg != null) {
                   ScaffoldMessenger.of(context).hideCurrentSnackBar();
                   ScaffoldMessenger.of(context).showSnackBar(
                     SnackBar(
                        content: Text(msg), 
                        backgroundColor: msg.contains("Xatolik") ? Colors.red : Colors.green
                     )
                   );
                }
              },
            ),
          ),
        );
      },
    );
  }

  // =========================================================================
  // 2. PERSONAL DOCS TAB
  // =========================================================================

  Widget _buildPersonalDocsTab() {
    // Mock User Documents
    final personalDocs = [
      {
        "title": "Passport nusxasi",
        "category": "Passport",
        "date": "12.03.2024",
        "type": "pdf"
      },
      {
        "title": "Rezyume (CV)",
        "category": "Rezyume",
        "date": "15.01.2024",
        "type": "doc"
      },
      {
        "title": "Obyektivka (Ma'lumotnoma)",
        "category": "Obyektivka",
        "date": "10.09.2023",
        "type": "pdf"
      },
    ];

    if (personalDocs.isEmpty) {
      return Column(
        children: [
          Expanded(
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.folder_open_rounded, size: 80, color: Colors.grey[300]),
                  const SizedBox(height: 16),
                  Text(
                    "Hujjatlar yo'q",
                    style: TextStyle(color: Colors.grey[500], fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
          ),
          _buildBottomButton(),
        ],
      );
    }

    return Column(
      children: [
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
            itemCount: personalDocs.length,
            separatorBuilder: (_, __) => const SizedBox(height: 16),
            itemBuilder: (context, index) {
              final doc = personalDocs[index];
              final isPdf = doc['type'] == 'pdf';
              
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
                          doc['date'] as String,
                          style: TextStyle(color: Colors.grey[500], fontSize: 12),
                        ),
                        const SizedBox(width: 12),
                        Text(
                          doc['category'] as String,
                          style: TextStyle(color: AppTheme.primaryBlue.withOpacity(0.8), fontSize: 12, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                  trailing: const Icon(Icons.more_vert_rounded, color: Colors.grey),
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
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05), 
            blurRadius: 20, 
            offset: const Offset(0, -5)
          )
        ],
      ),
      child: SafeArea(
        child: SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: _showAddDocumentSheet,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 0,
            ),
            child: const Text(
              "Hujjat yuklash",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ),
        ),
      ),
    );
  }

  void _showAddDocumentSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
            const Padding(
              padding: EdgeInsets.all(20),
              child: Text("Hujjat turini tanlang", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            Divider(height: 1, color: Colors.grey[200]),
            _buildActionItem(Icons.credit_card_rounded, "Passport nusxasi"),
            _buildActionItem(Icons.work_outline_rounded, "Rezyume (CV)"),
            _buildActionItem(Icons.assignment_ind_rounded, "Obyektivka"),
            _buildActionItem(Icons.folder_shared_rounded, "Boshqa hujjat"),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildActionItem(IconData icon, String title) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(8)),
        child: Icon(icon, color: Colors.black87),
      ),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      onTap: () {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Fayl tanlash oynasi ochilmoqda...")));
      },
    );
  }
}
