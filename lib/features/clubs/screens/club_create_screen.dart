import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import 'package:talabahamkor_mobile/core/localization/app_dictionary.dart';

class ClubCreateScreen extends StatefulWidget {
  const ClubCreateScreen({super.key});

  @override
  State<ClubCreateScreen> createState() => _ClubCreateScreenState();
}

class _ClubCreateScreenState extends State<ClubCreateScreen> {
  final _formKey = GlobalKey<FormState>();
  final DataService _dataService = DataService();
  
  String _name = '';
  String _department = '';
  String _description = '';
  String _channelLink = '';
  String _leaderLogin = '';
  bool _isLoading = false;

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    setState(() => _isLoading = true);

    final data = {
      'name': _name,
      'description': _description,
      'channel_link': _channelLink,
      'icon': 'groups_rounded',
      'color': '#4A90E2',
    };
    if (_leaderLogin.isNotEmpty) {
      data['leader_login'] = _leaderLogin;
    }
    if (_department.trim().isNotEmpty) {
      data['department'] = _department.trim();
    }

    final result = await _dataService.createClub(data);

    setState(() => _isLoading = false);

    if (result['success'] == true) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppDictionary.tr(context, 'msg_club_created_success'), style: TextStyle(color: Colors.white)), backgroundColor: AppTheme.accentGreen),
      );
      Navigator.pop(context, true);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result['message'] ?? "Xatolik yuz berdi"), backgroundColor: Colors.red),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Yangi Klub Yaratish", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "Klub ma'lumotlarini kiriting. Ushbu klub faqat sizning universitetingiz doirasida ochiladi.",
                style: TextStyle(color: Colors.grey, fontSize: 14),
              ),
              const SizedBox(height: 24),
              
              _buildTextField(
                label: "Klub nomi",
                hint: "Masalan: Yosh Dasturchilar",
                icon: Icons.groups,
                onSaved: (val) => _name = val ?? '',
                validator: (val) => val != null && val.isEmpty ? "Nom kiritish majburiy" : null,
              ),

              _buildTextField(
                label: "Qaysi bo'lim qoshida (Ixtiyoriy)",
                hint: "Masalan: Student Council",
                icon: Icons.account_balance,
                onSaved: (val) => _department = val ?? '',
              ),
              
              _buildTextField(
                label: "Maqsadi / Tavsifi",
                hint: "Klub nima muammolarni hal qiladi?",
                icon: Icons.description,
                maxLines: 4,
                onSaved: (val) => _description = val ?? '',
                validator: (val) => val != null && val.isEmpty ? "Tavsif qisqacha bo'lsa ham majburiy" : null,
              ),

              _buildTextField(
                label: "Telegram Kanal (Ixtiyoriy)",
                hint: "kanal_nomi",
                icon: Icons.telegram,
                prefixText: 'https://t.me/',
                onSaved: (val) {
                  if (val != null && val.isNotEmpty) {
                    var chLink = val.trim();
                    if (chLink.startsWith('https://t.me/')) chLink = chLink.substring('https://t.me/'.length);
                    else if (chLink.startsWith('http://t.me/')) chLink = chLink.substring('http://t.me/'.length);
                    else if (chLink.startsWith('t.me/')) chLink = chLink.substring('t.me/'.length);
                    if (chLink.startsWith('@')) chLink = chLink.substring(1);
                    _channelLink = 'https://t.me/$chLink';
                  } else {
                    _channelLink = '';
                  }
                },
              ),
              
              const SizedBox(height: 8),

              _buildTextField(
                label: "Sardor logini (Ixtiyoriy)",
                hint: "Sardorning HEMIS logini (masalan: 395...)",
                icon: Icons.person_add_alt_1,
                onSaved: (val) => _leaderLogin = val ?? '',
              ),

              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlue,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: _isLoading 
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text("Yaratish", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                ),
              ),
              // Add padding for keyboard to allow scrolling to the very bottom
              SizedBox(height: MediaQuery.of(context).viewInsets.bottom),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField({
    required String label,
    required String hint,
    required IconData icon,
    int maxLines = 1,
    required void Function(String?) onSaved,
    String? Function(String?)? validator,
    String? prefixText,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const SizedBox(height: 8),
          TextFormField(
            maxLines: maxLines,
            decoration: InputDecoration(
              hintText: hint,
              hintStyle: TextStyle(color: Colors.grey[400]),
              prefixText: prefixText,
              prefixIcon: maxLines == 1 ? Icon(icon, color: Colors.grey) : null,
              filled: true,
              fillColor: Colors.white,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.grey[200]!)),
              enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.grey[200]!)),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: AppTheme.primaryBlue)),
            ),
            validator: validator,
            onSaved: onSaved,
          ),
        ],
      ),
    );
  }
}
