import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../core/services/data_service.dart';
import '../models/dorm_models.dart';

class DormRoommateScreen extends StatefulWidget {
  const DormRoommateScreen({super.key});

  @override
  State<DormRoommateScreen> createState() => _DormRoommateScreenState();
}

class _DormRoommateScreenState extends State<DormRoommateScreen> {
  final DataService _dataService = DataService();
  late Future<List<DormRoommate>> _roommatesFuture;

  @override
  void initState() {
    super.initState();
    _roommatesFuture = _dataService.getDormRoommates().then((data) => data.map((j) => DormRoommate.fromJson(j)).toList());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Xonadoshlarim"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      backgroundColor: AppTheme.backgroundWhite,
      body: FutureBuilder<List<DormRoommate>>(
        future: _roommatesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator(color: Colors.blue));
          }
          final roommates = snapshot.data ?? [];
          if (roommates.isEmpty) {
            return const Center(child: Text("Xonadoshlar topilmadi."));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(20),
            itemCount: roommates.length,
            separatorBuilder: (context, index) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final student = roommates[index];
              return ListTile(
                leading: CircleAvatar(
                  radius: 24,
                  backgroundColor: Colors.blue[50],
                  child: Text(student.fullName[0], style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue)),
                ),
                title: Text(student.fullName, style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text(student.groupNumber ?? "Talaba", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
              );
            },
          );
        },
      ),
    );
  }
}
