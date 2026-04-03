import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../core/services/data_service.dart';
import '../models/dorm_models.dart';

// --- RULES SCREEN ---
class DormRuleScreen extends StatefulWidget {
  const DormRuleScreen({super.key});

  @override
  State<DormRuleScreen> createState() => _DormRuleScreenState();
}

class _DormRuleScreenState extends State<DormRuleScreen> {
  final DataService _dataService = DataService();
  late Future<List<DormRule>> _rulesFuture;

  @override
  void initState() {
    super.initState();
    _rulesFuture = _dataService.getDormRules().then((data) => data.map((j) => DormRule.fromJson(j)).toList());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Yotoqxona qoidalari"), backgroundColor: Colors.white, foregroundColor: Colors.black87, elevation: 0),
      backgroundColor: AppTheme.backgroundWhite,
      body: FutureBuilder<List<DormRule>>(
        future: _rulesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
          final rules = snapshot.data ?? [];
          return ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: rules.length,
            itemBuilder: (context, index) {
              final rule = rules[index];
              return Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.redAccent.withOpacity(0.1))),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(rule.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.redAccent)),
                    const SizedBox(height: 8),
                    Text(rule.content, style: const TextStyle(fontSize: 14, color: Colors.black87, height: 1.4)),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }
}

// --- MENU SCREEN ---
class DormMenuScreen extends StatefulWidget {
  const DormMenuScreen({super.key});

  @override
  State<DormMenuScreen> createState() => _DormMenuScreenState();
}

class _DormMenuScreenState extends State<DormMenuScreen> {
  final DataService _dataService = DataService();
  late Future<List<DormMenu>> _menuFuture;

  @override
  void initState() {
    super.initState();
    _menuFuture = _dataService.getDormMenu().then((data) => data.map((j) => DormMenu.fromJson(j)).toList());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Oshxona menyusi"), backgroundColor: Colors.white, foregroundColor: Colors.black87, elevation: 0),
      backgroundColor: AppTheme.backgroundWhite,
      body: FutureBuilder<List<DormMenu>>(
        future: _menuFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
          final menu = snapshot.data ?? [];
          return ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: menu.length,
            itemBuilder: (context, index) {
              final day = menu[index];
              return Card(
                margin: const EdgeInsets.only(bottom: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(day.dayName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.orange)),
                      const Divider(),
                      _buildMealRow("Nonushta", day.breakfast),
                      _buildMealRow("Tushlik", day.lunch),
                      _buildMealRow("Kechki ovqat", day.dinner),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildMealRow(String label, String? meal) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("$label: ", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
          Expanded(child: Text(meal ?? "Mavjud emas", style: const TextStyle(fontSize: 13, color: Colors.black54))),
        ],
      ),
    );
  }
}

// --- ROSTER SCREEN ---
class DormRosterScreen extends StatefulWidget {
  const DormRosterScreen({super.key});

  @override
  State<DormRosterScreen> createState() => _DormRosterScreenState();
}

class _DormRosterScreenState extends State<DormRosterScreen> {
  final DataService _dataService = DataService();
  late Future<List<DormRoster>> _rosterFuture;

  @override
  void initState() {
    super.initState();
    _rosterFuture = _dataService.getDormRoster().then((data) => data.map((j) => DormRoster.fromJson(j)).toList());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Navbatchilik jadvali"), backgroundColor: Colors.white, foregroundColor: Colors.black87, elevation: 0),
      backgroundColor: AppTheme.backgroundWhite,
      body: FutureBuilder<List<DormRoster>>(
        future: _rosterFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
          final roster = snapshot.data ?? [];
          return ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: roster.length,
            itemBuilder: (context, index) {
              final item = roster[index];
              return ListTile(
                leading: Container(width: 45, height: 45, decoration: BoxDecoration(color: Colors.green[50], shape: BoxShape.circle), child: const Icon(Icons.cleaning_services_rounded, color: Colors.green, size: 20)),
                title: Text(item.studentName, style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text(item.dayOfWeek, style: const TextStyle(color: Colors.green, fontSize: 12, fontWeight: FontWeight.bold)),
                trailing: Text(item.dutyType, style: const TextStyle(fontSize: 12, color: Colors.grey)), 
              );
            },
          );
        },
      ),
    );
  }
}
