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

  @override
  void initState() {
    super.initState();
    _loadGrades();
  }

  Future<void> _loadGrades() async {
    final grades = await _dataService.getGrades();
    if (mounted) {
      setState(() {
        _grades = grades;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            Text("O'zlashtirish", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 18)),
            Text("Semestr natijalari va baholar", style: TextStyle(color: Colors.grey, fontSize: 12, fontWeight: FontWeight.normal)),
          ],
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading
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
    );
  }

  Widget _buildGradeCard(dynamic item) {
    final subject = item['subject'] ?? "Fan";
    final grades = item['grades'] ?? {};
    final onVal = grades['ON']?['val_5'] ?? 0;
    final ynVal = grades['YN']?['val_5'] ?? 0;
    final ynRaw = grades['YN']?['raw'] ?? 0;
    final jnRaw = grades['JN']?['raw'] ?? 0;
    final jnVal = grades['JN']?['val_5'] ?? 0;
    
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
                      
                      // Scores Row: JN 5/5  ·  ON 5/5  ·  YN 5/5
                      Row(
                        children: [
                          if (jnRaw > 0) ...[
                            _buildScorePart("JN", jnVal),
                            _buildDot(),
                          ],
                          _buildScorePart("ON", onVal),
                          if (ynRaw > 0) ...[
                            _buildDot(),
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

  Widget _buildDot() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Text(
        "·",
        style: TextStyle(
          color: Colors.grey.withOpacity(0.5),
          fontWeight: FontWeight.bold,
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
