import '../../../../core/constants/api_constants.dart';

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
                        // --- ATTACHMENTS START ---
                        if (item['file_id'] != null || (item['images'] != null && (item['images'] as List).isNotEmpty))
                          Padding(
                            padding: const EdgeInsets.only(bottom: 12.0),
                            child: _buildAttachments(item),
                          ),
                        // --- ATTACHMENTS END ---
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

  Widget _buildAttachments(Map<String, dynamic> item) {
    List<String> fileIds = [];
    if (item['file_id'] != null) {
      fileIds.add(item['file_id']);
    } else if (item['images'] != null) {
      for (var img in item['images']) {
        if (img['file_id'] != null) {
          fileIds.add(img['file_id']);
        }
      }
    }

    if (fileIds.isEmpty) return const SizedBox.shrink();

    return SizedBox(
      height: 120,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: fileIds.length,
        itemBuilder: (context, index) {
          final url = "${ApiConstants.fileProxy}/${fileIds[index]}";
          return GestureDetector(
            onTap: () {
              // Full screen view could be added here
              showDialog(
                context: context,
                builder: (context) => Dialog(
                  child: InteractiveViewer(
                    child: Image.network(url),
                  ),
                ),
              );
            },
            child: Container(
              margin: const EdgeInsets.only(right: 8),
              width: 120,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                border: BorderSide(color: Colors.grey.shade200),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.network(
                  url,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) => Container(
                    color: Colors.grey[100],
                    child: const Icon(Icons.broken_image_outlined, color: Colors.grey),
                  ),
                  loadingBuilder: (context, child, loadingProgress) {
                    if (loadingProgress == null) return child;
                    return Center(
                      child: CircularProgressIndicator(
                        value: loadingProgress.expectedTotalBytes != null
                            ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                            : null,
                      ),
                    );
                  },
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
