import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class AppealsScreen extends StatefulWidget {
  const AppealsScreen({super.key});

  @override
  State<AppealsScreen> createState() => _AppealsScreenState();
}

class _AppealsScreenState extends State<AppealsScreen> with SingleTickerProviderStateMixin {
  // Mock Data
  final List<Map<String, dynamic>> _appeals = [
    {
      "id": 1023,
      "title": "Kontrakt to'lovi bo'yicha",
      "recipient": "Buxgalteriya",
      "status": "answered", // pending, answered, closed
      "date": "05.01.2025",
      "messages": [
        {"sender": "me", "text": "Assalomu alaykum. Kontrakt to'lovim tushdimi? Chekni ilova qildim.", "time": "10:30"},
        {"sender": "staff", "text": "Vaalaykum assalom. Ha, to'lovingiz qabul qilindi.", "time": "11:15"},
      ],
      "is_anonymous": false,
    },
    {
      "id": 1021,
      "title": "Yotoqxona sharoiti",
      "recipient": "Rahbariyat",
      "status": "pending",
      "date": "03.01.2025",
      "messages": [
        {"sender": "me", "text": "Assalomu alaykum. 3-qavatdagi wifi ishlamayapti. Iltimos chora ko'rsangiz.", "time": "14:20"},
      ],
      "is_anonymous": true,
    },
    {
      "id": 988,
      "title": "Sessiya jadvali",
      "recipient": "Dekanat",
      "status": "closed",
      "date": "20.12.2024",
      "messages": [
        {"sender": "me", "text": "Yakuniy imtihonlar qachon boshlanadi?", "time": "09:00"},
        {"sender": "staff", "text": "9-yanvardan boshlanadi. Jadval kanalga tashlanadi.", "time": "09:45"},
        {"sender": "system", "text": "Murojaat yopildi.", "time": "10:00"},
      ],
      "is_anonymous": false,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Murojaatlar", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Column(
        children: [
          Expanded(
            child: _appeals.isEmpty
            ? _buildEmptyState()
            : ListView.separated(
                padding: const EdgeInsets.all(20),
                itemCount: _appeals.length,
                separatorBuilder: (_, __) => const SizedBox(height: 16),
                itemBuilder: (context, index) => _buildAppealCard(_appeals[index]),
              ),
          ),
          _buildBottomButton(),
        ],
      ),
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
            offset: const Offset(0, -5),
          )
        ],
      ),
      child: SafeArea(
        child: SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: _showCreateAppealSheet,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 0,
            ),
            child: const Text(
              "Yangi murojaat",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.chat_bubble_outline_rounded, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            "Murojaatlar mavjud emas",
            style: TextStyle(color: Colors.grey[500], fontSize: 16, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildAppealCard(Map<String, dynamic> appeal) {
    Color statusColor;
    String statusText;
    IconData statusIcon;

    switch (appeal['status']) {
      case 'answered':
        statusColor = Colors.green;
        statusText = "Javob berilgan";
        statusIcon = Icons.check_circle_outline_rounded;
        break;
      case 'closed':
        statusColor = Colors.grey;
        statusText = "Yopilgan";
        statusIcon = Icons.lock_outline_rounded;
        break;
      case 'pending':
      default:
        statusColor = Colors.orange;
        statusText = "Kutilmoqda";
        statusIcon = Icons.schedule_rounded;
        break;
    }

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 15,
            offset: const Offset(0, 5),
          )
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () => _showAppealDetails(appeal),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: statusColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(statusIcon, size: 14, color: statusColor),
                          const SizedBox(width: 4),
                          Text(
                            statusText,
                            style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    Text(
                      appeal['date'],
                      style: TextStyle(color: Colors.grey[500], fontSize: 12),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  appeal['title'] ?? "Mavzusiz", // Use title or mock if missing, logic simplified
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Icon(Icons.person_pin_circle_rounded, size: 14, color: Colors.grey[600]),
                    const SizedBox(width: 4),
                    Text(
                      "Qabul qiluvchi: ${appeal['recipient']}",
                      style: TextStyle(color: Colors.grey[600], fontSize: 13),
                    ),
                    if (appeal['is_anonymous']) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(color: Colors.black87, borderRadius: BorderRadius.circular(4)),
                        child: const Text("ANONIM", style: TextStyle(color: Colors.white, fontSize: 10)),
                      )
                    ]
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showCreateAppealSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => const CreateAppealSheet(),
    );
  }

  void _showAppealDetails(Map<String, dynamic> appeal) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => AppealDetailScreen(appeal: appeal)));
  }
}

class CreateAppealSheet extends StatefulWidget {
  const CreateAppealSheet({super.key});

  @override
  State<CreateAppealSheet> createState() => _CreateAppealSheetState();
}

class _CreateAppealSheetState extends State<CreateAppealSheet> {
  String? _selectedRecipient;
  bool _isAnonymous = false;
  final TextEditingController _textController = TextEditingController();

  final List<String> _recipients = ["Rahbariyat", "Dekanat", "Tyutor", "Psixolog", "Buxgalteriya"];

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        left: 20, 
        right: 20, 
        top: 20, 
        bottom: MediaQuery.of(context).viewInsets.bottom + 20
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
          ),
          const SizedBox(height: 20),
          const Text("Yangi murojaat", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          
          // Recipient
          const Text("Kimga yuborilsin?", style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: _recipients.map((recipient) {
              final isSelected = _selectedRecipient == recipient;
              return ChoiceChip(
                label: Text(recipient),
                selected: isSelected,
                onSelected: (selected) => setState(() => _selectedRecipient = selected ? recipient : null),
                selectedColor: AppTheme.primaryBlue,
                labelStyle: TextStyle(color: isSelected ? Colors.white : Colors.black),
              );
            }).toList(),
          ),
          
          const SizedBox(height: 20),
          
          // Anonymity
          const Text("Maxfiylik", style: TextStyle(fontWeight: FontWeight.w600)),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text("Anonim yuborish"),
            subtitle: const Text("Ism-familiyangiz ko'rinmaydi"),
            value: _isAnonymous,
            onChanged: (val) => setState(() => _isAnonymous = val),
            activeColor: AppTheme.primaryBlue,
          ),

          const SizedBox(height: 10),
          
          // Content
          Expanded(
            child: TextField(
              controller: _textController,
              maxLines: null,
              expands: true,
              textAlignVertical: TextAlignVertical.top,
              decoration: InputDecoration(
                hintText: "Murojaat matnini yozing...",
                filled: true,
                fillColor: Colors.grey[50],
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                contentPadding: const EdgeInsets.all(16),
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: () {
                if (_selectedRecipient == null || _textController.text.isEmpty) return;
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Murojaat yuborildi! (Mock)"), backgroundColor: Colors.green)
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryBlue,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text("Yuborish", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
            ),
          ),
        ],
      ),
    );
  }
}

class AppealDetailScreen extends StatelessWidget {
  final Map<String, dynamic> appeal;
  const AppealDetailScreen({super.key, required this.appeal});

  @override
  Widget build(BuildContext context) {
    final messages = appeal['messages'] as List;
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Text("Murojaat #${appeal['id']}", style: const TextStyle(color: Colors.black, fontSize: 16)),
        backgroundColor: Colors.white,
        elevation: 1,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final msg = messages[index];
                final isMe = msg['sender'] == 'me';
                final isSystem = msg['sender'] == 'system';
                
                if (isSystem) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Text(msg['text'], style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                    ),
                  );
                }

                return Align(
                  alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(12),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: isMe ? AppTheme.primaryBlue : Colors.white,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(16),
                        topRight: const Radius.circular(16),
                        bottomLeft: isMe ? const Radius.circular(16) : const Radius.circular(4),
                        bottomRight: isMe ? const Radius.circular(4) : const Radius.circular(16),
                      ),
                      boxShadow: isMe ? [] : [
                        BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 5, offset: const Offset(0, 2))
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          msg['text'],
                          style: TextStyle(color: isMe ? Colors.white : Colors.black87),
                        ),
                        const SizedBox(height: 4),
                        Align(
                          alignment: Alignment.bottomRight,
                          child: Text(
                            msg['time'],
                            style: TextStyle(
                              color: isMe ? Colors.white.withOpacity(0.7) : Colors.grey[500],
                              fontSize: 10
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          if (appeal['status'] != 'closed')
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: "Javob yozish...",
                        filled: true,
                        fillColor: Colors.grey[100],
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  CircleAvatar(
                    backgroundColor: AppTheme.primaryBlue,
                    child: IconButton(
                      icon: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                      onPressed: () {},
                    ),
                  )
                ],
              ),
            ),
          )
        ],
      ),
    );
  }
}
