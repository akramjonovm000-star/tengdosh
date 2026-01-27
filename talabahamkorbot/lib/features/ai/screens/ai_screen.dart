import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/theme/app_theme.dart';
import 'ai_chat_screen.dart';
import 'ai_konspekt_screen.dart';

class AiScreen extends StatelessWidget {
  const AiScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite, 
      appBar: AppBar(
        title: const Text("AI Yordamchi", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Container(
        color: AppTheme.backgroundWhite,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              "Sizga qanday yordam bera olaman? Quyidagi mavzulardan birini tanlang:",
              style: TextStyle(color: Colors.grey[600], fontSize: 15),
              textAlign: TextAlign.start,
            ),
            const SizedBox(height: 20),
            
            _buildAiButton(context, "Stipendiya haqida", Icons.monetization_on, () {}),
            _buildAiButton(context, "Hemis parolini tiklash", Icons.vpn_key, () {}),
            _buildAiButton(context, "Kredit-modul tizimi", Icons.school, () {}),
            _buildAiButton(context, "Dars jadvali", Icons.calendar_today, () {}),
            _buildAiButton(context, "Konspekt qilish (File/Matn)", Icons.note_alt, () {
               Navigator.push(context, MaterialPageRoute(builder: (_) => const AiKonspektScreen()));
            }),
            const Divider(height: 30),
            _buildAiButton(context, "AI bilan suhbat", Icons.chat_bubble, () {
               Navigator.push(context, MaterialPageRoute(builder: (_) => const AiChatScreen()));
            }, isPrimary: true),
          ],
        ),
      ),
    );
  }

  Widget _buildAiButton(BuildContext context, String text, IconData icon, VoidCallback onTap, {bool isPrimary = false}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            decoration: BoxDecoration(
              color: isPrimary ? AppTheme.primaryBlue : Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isPrimary ? AppTheme.primaryBlue : Colors.grey.withOpacity(0.1),
              ),
              boxShadow: isPrimary 
                  ? [BoxShadow(color: AppTheme.primaryBlue.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 4))]
                  : [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 4, offset: const Offset(0, 2))],
            ),
            child: Row(
              children: [
                Icon(icon, color: isPrimary ? Colors.white : AppTheme.primaryBlue, size: 24),
                const SizedBox(width: 16),
                Expanded(
                  child: Text(
                    text,
                    style: TextStyle(
                      color: isPrimary ? Colors.white : Colors.black87,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Icon(Icons.chevron_right, color: isPrimary ? Colors.white54 : Colors.grey, size: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
