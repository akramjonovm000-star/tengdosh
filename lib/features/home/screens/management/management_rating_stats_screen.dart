import '../../../../core/services/data_service.dart';
import 'package:cached_network_image/cached_network_image.dart';

class ManagementRatingStatsScreen extends StatefulWidget {
  const ManagementRatingStatsScreen({super.key});

  @override
  State<ManagementRatingStatsScreen> createState() => _ManagementRatingStatsScreenState();
}

class _ManagementRatingStatsScreenState extends State<ManagementRatingStatsScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  List<dynamic> _stats = [];

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() => _isLoading = true);
    final stats = await _dataService.getManagementRatingStats();
    if (mounted) {
      setState(() {
        _stats = stats;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text("Tutor Rating Statistikasi"),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        actions: [
          IconButton(
            onPressed: _loadStats,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _stats.isEmpty
              ? const _NoDataView()
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _stats.length,
                  itemBuilder: (context, index) {
                    final item = _stats[index];
                    return _RankingCard(item: item);
                  },
                ),
    );
  }
}

class _RankingCard extends StatefulWidget {
  final dynamic item;
  const _RankingCard({required this.item});

  @override
  State<_RankingCard> createState() => _RankingCardState();
}

class _RankingCardState extends State<_RankingCard> with SingleTickerProviderStateMixin {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    final List<dynamic> breakdown = item['breakdown'] ?? [];

    return AnimatedSize(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      child: Card(
        margin: const EdgeInsets.only(bottom: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        elevation: 4,
        shadowColor: Colors.black12,
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () => setState(() => _isExpanded = !_isExpanded),
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 30,
                      backgroundColor: Colors.blue[50],
                      backgroundImage: item['image_url'] != null
                          ? CachedNetworkImageProvider(item['image_url'])
                          : null,
                      child: item['image_url'] == null
                          ? const Icon(Icons.person_pin_rounded, color: Colors.blue, size: 30)
                          : null,
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item['full_name'] ?? 'Noma\'lum',
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            item['role_name'] ?? '',
                            style: TextStyle(color: Colors.grey[600], fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.blue,
                            borderRadius: BorderRadius.circular(12),
                            boxShadow: [
                              BoxShadow(color: Colors.blue.withOpacity(0.3), blurRadius: 4, offset: const Offset(0, 2)),
                            ],
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.star_rounded, color: Colors.white, size: 24),
                              const SizedBox(width: 4),
                              Text(
                                item['average_rating'].toString(),
                                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          "${item['total_votes']} ta ovoz",
                          style: TextStyle(color: Colors.grey[600], fontSize: 11),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (_isExpanded) ...[
                const Divider(height: 1),
                Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    children: [
                      const Text(
                        "Baholar Taqsimoti",
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 32),
                      Row(
                        children: [
                          Expanded(
                            flex: 1,
                            child: SizedBox(
                              height: 160,
                              child: _SimplePieChart(breakdown: breakdown),
                            ),
                          ),
                          const SizedBox(width: 24),
                          Expanded(
                            flex: 1,
                            child: Column(
                              children: [
                                ...breakdown.reversed.map((b) => _buildLegendRow(b)).toList(),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLegendRow(dynamic b) {
    final int rating = b['rating'];
    final int count = b['count'];
    final double percentage = (b['percentage'] as num).toDouble();
    final Color color = _getRatingColor(rating);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              "$rating baho",
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ),
          Text(
            "$count ta (${percentage.toStringAsFixed(0)}%)",
            style: TextStyle(color: Colors.grey[600], fontSize: 11),
          ),
        ],
      ),
    );
  }

  Color _getRatingColor(int rating) {
    switch (rating) {
      case 5: return Colors.green;
      case 4: return Colors.lightGreen;
      case 3: return Colors.orangeAccent;
      case 2: return Colors.orange;
      case 1: return Colors.red;
      default: return Colors.grey;
    }
  }
}

class _SimplePieChart extends StatelessWidget {
  final List<dynamic> breakdown;
  const _SimplePieChart({required this.breakdown});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _PieChartPainter(breakdown: breakdown),
      child: Container(),
    );
  }
}

class _PieChartPainter extends CustomPainter {
  final List<dynamic> breakdown;
  _PieChartPainter({required this.breakdown});

  @override
  void paint(Canvas canvas, Size size) {
    final double totalVotes = breakdown.fold(0, (sum, b) => sum + b['count']);
    if (totalVotes == 0) return;

    final Offset center = Offset(size.width / 2, size.height / 2);
    final double radius = size.height / 2;
    double startAngle = -1.5708; // Start at top

    final Paint paint = Paint()
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    // Use order: 1, 2, 3, 4, 5 to match colors correctly
    final List<dynamic> sortedBreakdown = List.from(breakdown)..sort((a, b) => a['rating'].compareTo(b['rating']));

    for (final b in sortedBreakdown) {
      final double sweepAngle = (b['count'] / totalVotes) * 6.28319; // 2 * pi
      if (sweepAngle == 0) continue;

      paint.color = _getRatingColor(b['rating']);
      
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        sweepAngle,
        true,
        paint,
      );
      
      startAngle += sweepAngle;
    }
    
    // Draw hole in middle (Donut style looks better)
    final Paint holePaint = Paint()..color = Colors.white;
    canvas.drawCircle(center, radius * 0.4, holePaint);
  }

  Color _getRatingColor(int rating) {
    switch (rating) {
      case 5: return Colors.green;
      case 4: return Colors.lightGreen;
      case 3: return Colors.orangeAccent;
      case 2: return Colors.orange;
      case 1: return Colors.red;
      default: return Colors.grey;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _NoDataView extends StatelessWidget {
  const _NoDataView();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.query_stats_rounded, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            "Hozircha ma\'lumotlar yo\'q.",
            style: TextStyle(fontSize: 18, color: Colors.grey[600], fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Text("Birinchi so'rovnoma yaratasiz kerak.", textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
