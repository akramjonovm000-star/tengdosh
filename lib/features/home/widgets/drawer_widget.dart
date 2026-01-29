import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:talabahamkor_mobile/features/auth/auth_provider.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:talabahamkor_mobile/features/appeals/screens/appeals_screen.dart';
import 'package:talabahamkor_mobile/features/documents/screens/documents_screen.dart';

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: Column(
        children: [
          const UserAccountsDrawerHeader(
            decoration: BoxDecoration(color: AppTheme.primaryBlue),
            accountName: Text("Talaba"),
            accountEmail: Text("Student Portal"),
            currentAccountPicture: CircleAvatar(
              backgroundColor: Colors.white,
              child: Icon(Icons.person, color: AppTheme.primaryBlue),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.settings),
            title: const Text("Sozlamalar"),
          ),
          ListTile(
            leading: const Icon(Icons.message_outlined),
            title: const Text("Murojaatlar"),
            onTap: () {
               Navigator.pop(context);
               Navigator.push(context, MaterialPageRoute(builder: (_) => const AppealsScreen()));
            },
          ),
          ListTile(
            leading: const Icon(Icons.file_copy_outlined),
            title: const Text("Hujjatlar"),
            onTap: () {
               Navigator.pop(context);
               Navigator.push(context, MaterialPageRoute(builder: (_) => const DocumentsScreen()));
            },
          ),
          ListTile(
            leading: const Icon(Icons.help_outline),
            title: const Text("Yordam"),
            onTap: () {},
          ),
          const Spacer(),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.exit_to_app, color: Colors.red),
            title: const Text("Chiqish", style: TextStyle(color: Colors.red)),
            onTap: () {
              context.read<AuthProvider>().logout();
            },
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
