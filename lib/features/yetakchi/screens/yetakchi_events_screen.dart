import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../services/yetakchi_service.dart';
import 'package:intl/intl.dart';

class YetakchiEventsScreen extends StatefulWidget {
  const YetakchiEventsScreen({Key? key}) : super(key: key);

  @override
  State<YetakchiEventsScreen> createState() => _YetakchiEventsScreenState();
}

class _YetakchiEventsScreenState extends State<YetakchiEventsScreen> {
  final YetakchiService _service = YetakchiService();
  final DateFormat _dateFormat = DateFormat('dd.MM.yyyy HH:mm');
  
  List<dynamic> _events = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchEvents();
  }

  Future<void> _fetchEvents() async {
    setState(() => _isLoading = true);
    final results = await _service.getEvents(limit: 50);
    if (mounted) {
      setState(() {
        _events = results;
        _isLoading = false;
      });
    }
  }

  void _showCreateEventBottomSheet() {
     // Simplistic demo of creating an event
     final titleCtrl = TextEditingController();
     final descCtrl = TextEditingController();
     DateTime? selectedDate;
     
     showModalBottomSheet(
       context: context, 
       isScrollControlled: true,
       shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
       builder: (ctx) {
          return StatefulBuilder(
            builder: (BuildContext context, StateSetter setModalState) {
              return Padding(
                padding: EdgeInsets.only(
                  bottom: MediaQuery.of(ctx).viewInsets.bottom,
                  left: 24, right: 24, top: 24
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("Yangi Tadbir Qo'shish", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 24),
                    TextField(
                      controller: titleCtrl,
                      decoration: InputDecoration(
                        labelText: "Tadbir nomi",
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: descCtrl,
                      maxLines: 3,
                      decoration: InputDecoration(
                        labelText: "Tavsif (ixtiyoriy)",
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))
                      ),
                    ),
                    const SizedBox(height: 16),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.calendar_month, color: AppTheme.primaryBlue),
                      title: Text(selectedDate == null ? "Sana va vaqtni tanlang" : _dateFormat.format(selectedDate!)),
                      onTap: () async {
                         final date = await showDatePicker(
                           context: context, 
                           initialDate: DateTime.now(),
                           firstDate: DateTime.now(),
                           lastDate: DateTime.now().add(const Duration(days: 365))
                         );
                         if (date != null) {
                            final time = await showTimePicker(context: context, initialTime: TimeOfDay.now());
                            if (time != null) {
                               setModalState(() {
                                 selectedDate = DateTime(date.year, date.month, date.day, time.hour, time.minute);
                               });
                            }
                         }
                      },
                    ),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                           backgroundColor: AppTheme.primaryBlue,
                           foregroundColor: Colors.white,
                           shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))
                        ),
                        onPressed: () {
                           // Call API to create event here.
                           ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Tadbir yaratildi!")));
                           Navigator.pop(ctx);
                        },
                        child: const Text("Saqlash", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      )
                    ),
                    const SizedBox(height: 24),
                  ]
                ),
              );
            }
          );
       }
     );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Tadbirlar", style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_circle, color: AppTheme.primaryBlue, size: 28),
            onPressed: _showCreateEventBottomSheet,
          ),
          const SizedBox(width: 8)
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator())
        : _events.isEmpty 
            ? _buildEmptyState()
            : _buildList(),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.event_busy, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text("Tadbirlar ro'yxati bo'sh", style: TextStyle(color: Colors.grey[500], fontSize: 16))
        ],
      ),
    );
  }

  Widget _buildList() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _events.length,
      itemBuilder: (context, index) {
        final item = _events[index];
        DateTime date = DateTime.parse(item['date']);
        
        return Card(
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: Colors.grey[200]!)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                   mainAxisAlignment: MainAxisAlignment.spaceBetween,
                   children: [
                     Expanded(child: Text(item['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16))),
                     Container(
                       padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                       decoration: BoxDecoration(color: AppTheme.primaryBlue.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                       child: Row(
                         children: [
                           const Icon(Icons.people, size: 14, color: AppTheme.primaryBlue),
                           const SizedBox(width: 4),
                           Text("${item['participants'] ?? 0}", style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold, fontSize: 12)),
                         ],
                       )
                     )
                   ],
                ),
                const SizedBox(height: 8),
                Text(item['description'] ?? 'Izoh yo\'q', style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                const SizedBox(height: 16),
                Row(
                  children: [
                    const Icon(Icons.calendar_today, size: 14, color: Colors.grey),
                    const SizedBox(width: 6),
                    Text(_dateFormat.format(date), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.blueGrey)),
                  ]
                )
              ]
            ),
          )
        );
      }
    );
  }
}
