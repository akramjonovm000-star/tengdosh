import 'package:flutter/material.dart';
import '../../../core/services/data_service.dart';
import '../models/survey_models.dart';
import 'survey_taking_screen.dart';

class SurveyListScreen extends StatefulWidget {
  const SurveyListScreen({super.key});

  @override
  State<SurveyListScreen> createState() => _SurveyListScreenState();
}

class _SurveyListScreenState extends State<SurveyListScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  SurveyListResponse? _surveyData;

  @override
  void initState() {
    super.initState();
    _loadSurveys();
  }

  Future<void> _loadSurveys() async {
    setState(() => _isLoading = true);
    try {
      final data = await _dataService.getSurveys();
      setState(() {
        _surveyData = data;
        _isLoading = false;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Xatolik yuz berdi: $e')),
        );
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text("So'rovnomalar"),
          bottom: const TabBar(
            tabs: [
              Tab(text: "Kutilmoqda"),
              Tab(text: "Jarayonda"),
              Tab(text: "Yakunlangan"),
            ],
          ),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : TabBarView(
                children: [
                  _buildList(_surveyData?.notStarted ?? []),
                  _buildList(_surveyData?.inProgress ?? []),
                  _buildList(_surveyData?.finished ?? []),
                ],
              ),
      ),
    );
  }

  Widget _buildList(List<Survey> surveys) {
    if (surveys.isEmpty) {
      return const Center(
        child: Text("So'rovnomalar mavjud emas"),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: surveys.length,
      itemBuilder: (context, index) {
        final survey = surveys[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            contentPadding: const EdgeInsets.all(16),
            title: Text(
              survey.name,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 8.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (survey.startDate != null)
                    Text("Boshlanish: ${survey.startDate.toString().split('.')[0]}"),
                  if (survey.endDate != null)
                    Text("Tugash: ${survey.endDate.toString().split('.')[0]}"),
                ],
              ),
            ),
            trailing: survey.status != 'finished'
                ? ElevatedButton(
                    onPressed: () => _startSurvey(survey),
                    child: Text(survey.status == 'not_started' ? "Boshlash" : "Davom etish"),
                  )
                : const Icon(Icons.check_circle, color: Colors.green),
          ),
        );
      },
    );
  }

  void _startSurvey(Survey survey) async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => SurveyTakingScreen(surveyId: survey.id),
      ),
    );

    if (result == true) {
      _loadSurveys();
    }
  }
}
