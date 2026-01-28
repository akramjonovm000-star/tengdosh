import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import 'subject_detail_screen.dart';

class GradesScreen extends StatefulWidget {
  const GradesScreen({super.key});

  @override
  State<GradesScreen> createState() => _GradesScreenState();
}

class _GradesScreenState extends State<GradesScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _grades = [];
  List<dynamic> _semesters = [];
  String? _selectedSemester;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    try {
      final sems = await _dataService.getSemesters();
      if (mounted) {
        setState(() {
          _semesters = sems;
          _selectedSemester = null; // Default to 'Joriy'
        });
        await _loadGrades();
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _loadGrades() async {
    if (!mounted) return;
    setState(() => _isLoading = true);
    try {
      final grades = await _dataService.getGrades(semester: _selectedSemester);
      if (mounted) {
        setState(() {
          _grades = grades;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("O'zlashtirish", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Semester Selection Popup
          if (_semesters.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              child: PopupMenuButton<String?>(
                initialValue: _selectedSemester,
                onSelected: (String? value) {
                  setState(() => _selectedSemester = value);
                  _loadGrades();
                },
                offset: const Offset(0, 45),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: null,
                    child: Text("Joriy"),
                  ),
                  ..._semesters.map((sem) => PopupMenuItem(
                    value: sem['id'].toString(),
                    child: Text(sem['name'] ?? ""),
                  )),
                ],
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlue,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.check, color: Colors.white, size: 16),
                      const SizedBox(width: 8),
                      Text(
                        _selectedSemester == null 
                            ? "Joriy" 
                            : (_semesters.firstWhere((s) => s['id'].toString() == _selectedSemester, orElse: () => {'name': ''})['name'] ?? ""),
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            
          Expanded(
            child: RefreshIndicator(
              onRefresh: _loadGrades,
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _grades.isEmpty
                      ? const Center(child: Text("Ma'lumot topilmadi"))
                      : ListView.builder(
                          padding: const EdgeInsets.all(20),
                          itemCount: _grades.length,
                          itemBuilder: (context, index) {
                            final item = _grades[index];
                            return _buildGradeCard(item);
                          },
                        ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGradeCard(dynamic item) {
    final subject = item['subject'] ?? "Fan";
    final on = item['on'] ?? {};
    final yn = item['yn'] ?? {};
    final onVal = on['val_5'] ?? 0;
    final ynVal = yn['val_5'] ?? 0;
    final ynRaw = yn['raw'] ?? 0;
    
    // For navigation
    final name = item['name'] ?? item['subject'] ?? "Fan";
    final id = item['id'];

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 24,
            offset: const Offset(0, 8),
            spreadRadius: 0,
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: () {
            if (id != null) {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => SubjectDetailScreen(
                    subjectId: id.toString(),
                    subjectName: name,
                  ),
                ),
              );
            } else {
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Fan ID topilmadi")));
            }
          },
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                // Neutral Icon Container
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.grey.withOpacity(0.08),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.menu_book_rounded, color: Colors.grey, size: 18),
                ),
                const SizedBox(width: 16),
                
                // Content
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        subject,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF2D2D2D),
                          letterSpacing: -0.3,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 6),
                      
                      // Scores Row: ON 5/5  ·  YN 5/5
                      Row(
                        children: [
                          _buildScorePart("ON", onVal),
                          if (ynRaw > 0) ...[
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 8),
                              child: Text(
                                "·",
                                style: TextStyle(
                                  color: Colors.grey.withOpacity(0.5),
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            _buildScorePart("YN", ynVal),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildScorePart(String label, dynamic score) {
    return RichText(
      text: TextSpan(
        style: const TextStyle(fontSize: 13, fontFamily: 'Inter', color: Colors.black), 
        children: [
          TextSpan(
            text: "$label ",
            style: const TextStyle(color: Colors.grey, fontWeight: FontWeight.w400),
          ),
          TextSpan(
            text: "$score/5",
            style: const TextStyle(
              color: AppTheme.primaryBlue,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
