import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/services/data_service.dart';

class ElectionScreen extends StatefulWidget {
  final int electionId;
  const ElectionScreen({super.key, required this.electionId});

  @override
  State<ElectionScreen> createState() => _ElectionScreenState();
}

class _ElectionScreenState extends State<ElectionScreen> {
  final DataService _service = DataService();
  Map<String, dynamic>? _election;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadElection();
  }

  Future<void> _loadElection() async {
    try {
      final data = await _service.getElectionDetails(widget.electionId);
      setState(() {
        _election = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _vote(int candidateId, String name) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Tasdiqlash"),
        content: Text("$name nomzodiga ovoz bermoqchimisiz? Bu amalni qaytarib bo'lmaydi."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Yo'q")),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("Ha, ovoz beraman")),
        ],
      ),
    );

    if (confirm != true) return;

    try {
      await _service.voteInElection(widget.electionId, candidateId);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Ovozingiz muvaffaqiyatli qabul qilindi!")));
      _loadElection(); // Refresh to show has_voted state
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString()), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Saylov"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _buildContent(),
    );
  }

  Widget _buildContent() {
    final candidates = (_election?['candidates'] as List? ?? []);
    final hasVoted = _election?['has_voted'] ?? false;
    final votedId = _election?['voted_candidate_id'];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            _election?['title'] ?? "Talabalar saylovi",
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            _election?['description'] ?? "",
            style: TextStyle(color: Colors.grey[600], fontSize: 15),
          ),
          const SizedBox(height: 24),
          const Text(
            "Nomzodlar",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          ...candidates.map((cand) => _buildCandidateCard(cand, hasVoted, votedId)).toList(),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildCandidateCard(dynamic cand, bool hasVoted, dynamic votedId) {
    final isVoted = votedId == cand['id'];
    
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 0,
      color: isVoted ? AppTheme.primaryBlue.withOpacity(0.05) : Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Colors.grey[200],
                  child: const Icon(Icons.person, color: Colors.grey, size: 30),
                  // Note: Future improvement - handle photo_id/image_url for candidates
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        cand['full_name'] ?? "Noma'lum",
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      Text(
                        cand['faculty_name'] ?? "",
                        style: TextStyle(color: Colors.grey[600], fontSize: 13),
                      ),
                    ],
                  ),
                ),
                if (isVoted)
                  const Icon(Icons.check_circle, color: Colors.green),
              ],
            ),
            if (cand['campaign_text'] != null) ...[
              const Divider(height: 24),
              Text(
                cand['campaign_text'],
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: Colors.grey[800], fontSize: 14),
              ),
            ],
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: hasVoted ? null : () => _vote(cand['id'], cand['full_name']),
                style: ElevatedButton.styleFrom(
                  backgroundColor: isVoted ? Colors.green : AppTheme.primaryBlue,
                  foregroundColor: Colors.white,
                  disabledBackgroundColor: Colors.grey[300],
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 0,
                ),
                child: Text(
                  isVoted ? "Ovoz bergansiz" : hasVoted ? "Ovoz berib bo'lingan" : "Ovoz berish",
                ),
              ),
            )
          ],
        ),
      ),
    );
  }
}
