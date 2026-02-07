import 'package:flutter/material.dart';

class StudentItemsListScreen extends StatelessWidget {
  final List<dynamic> items;
  final String title;
  final String itemType;

  const StudentItemsListScreen({
    super.key,
    required this.items,
    required this.title,
    required this.itemType,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(title),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: items.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.folder_open_outlined, size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text(
                    "$itemType topilmadi",
                    style: TextStyle(color: Colors.grey[600], fontSize: 16),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              itemBuilder: (context, index) {
                final item = items[index];
                return Card(
                  elevation: 0,
                  margin: const EdgeInsets.only(bottom: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(color: Colors.grey.shade200),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Text(
                                item['title'] ?? item['text'] ?? "$itemType #${item['id']}",
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                            ),
                            if (item['date'] != null)
                              Text(
                                item['date'].toString().split('T')[0],
                                style: TextStyle(color: Colors.grey[500], fontSize: 12),
                              ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: _getStatusColor(item['status']).withOpacity(0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                item['status'] ?? "Noma'lum",
                                style: TextStyle(
                                  color: _getStatusColor(item['status']),
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }

  Color _getStatusColor(String? status) {
    if (status == null) return Colors.grey;
    final s = status.toLowerCase();
    if (s.contains('yangi') || s.contains('pending')) return Colors.orange;
    if (s.contains('tasdiq') || s.contains('bajarildi') || s.contains('success')) return Colors.green;
    if (s.contains('rad') || s.contains('xato')) return Colors.red;
    return Colors.blue;
  }
}
