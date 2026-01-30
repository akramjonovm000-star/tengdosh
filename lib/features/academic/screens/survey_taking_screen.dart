import 'package:flutter/material.dart';
import '../../../core/services/data_service.dart';
import '../models/survey_models.dart';

class SurveyTakingScreen extends StatefulWidget {
  final int surveyId;
  const SurveyTakingScreen({super.key, required this.surveyId});

  @override
  State<SurveyTakingScreen> createState() => _SurveyTakingScreenState();
}

class _SurveyTakingScreenState extends State<SurveyTakingScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  SurveyStartResponse? _surveyData;
  final Map<int, dynamic> _userAnswers = {};
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _startSurvey();
  }

  final Map<int, TextEditingController> _controllers = {};

  @override
  void dispose() {
    for (var controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _startSurvey() async {
    setState(() => _isLoading = true);
    try {
      final data = await _dataService.startSurvey(widget.surveyId);
      setState(() {
        _surveyData = data;
        
        // Pre-fill answers from HEMIS
        for (var q in data.questions) {
          if (q.answers.isNotEmpty) {
            if (q.type == 'checkbox') {
              _userAnswers[q.id] = List<String>.from(q.answers);
            } else {
              _userAnswers[q.id] = q.answers.first;
              if (q.type == 'input') {
                _controllers[q.id] = TextEditingController(text: q.answers.first);
              }
            }
          } else if (q.type == 'input') {
            _controllers[q.id] = TextEditingController();
          }
        }
        
        _isLoading = false;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Xatolik yuz berdi: $e')),
        );
        Navigator.pop(context);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text("Yuklanmoqda...")),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final bool isFinished = _surveyData?.title.isNotEmpty == true && 
                             _surveyData?.questions.every((q) => q.answers.isNotEmpty) == true;
    // Note: title usually contains the theme, status might be nested. 
    // We'll rely on our Survey model logic in list screen to know if it's finished.
    // However, here we just show "Yakunlash" or "Saqlash".

    return Scaffold(
      appBar: AppBar(
        title: Text(_surveyData?.title ?? "So'rovnoma"),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _surveyData?.questions.length ?? 0,
              itemBuilder: (context, index) {
                final question = _surveyData!.questions[index];
                return _buildQuestionCard(question);
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isSubmitting ? null : _finishSurvey,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isSubmitting
                    ? const CircularProgressIndicator(color: Colors.white)
                    : Text(isFinished ? "Saqlash va qaytish" : "Yakunlash", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuestionCard(SurveyQuestion question) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              question.text,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            if (question.type == 'radio') ...[
              ...question.variants.map((variant) => RadioListTile<String>(
                    title: Text(variant),
                    value: variant,
                    groupValue: _userAnswers[question.id],
                    onChanged: (val) => _saveAnswer(question, val),
                  ))
            ] else if (question.type == 'checkbox') ...[
              ...question.variants.map((variant) {
                List<String> currentAnswers = List<String>.from(_userAnswers[question.id] ?? []);
                return CheckboxListTile(
                  title: Text(variant),
                  value: currentAnswers.contains(variant),
                  onChanged: (val) {
                    if (val == true) {
                      currentAnswers.add(variant);
                    } else {
                      currentAnswers.remove(variant);
                    }
                    _saveAnswer(question, currentAnswers);
                  },
                );
              })
            ] else if (question.type == 'input') ...[
              TextField(
                controller: _controllers[question.id],
                onChanged: (val) => _saveAnswer(question, val),
                decoration: const InputDecoration(
                  hintText: "Javobingizni kiriting...",
                  border: OutlineInputBorder(),
                ),
              )
            ],
          ],
        ),
      ),
    );
  }

  void _saveAnswer(SurveyQuestion question, dynamic value) async {
    setState(() {
      _userAnswers[question.id] = value;
    });

    // Send answer to backend
    await _dataService.submitSurveyAnswer(
      question.id,
      question.type,
      value,
    );
  }

  Future<void> _finishSurvey() async {
    if (_surveyData == null) return;

    if (_userAnswers.length < _surveyData!.questions.length) {
       bool? confirm = await showDialog<bool>(
         context: context,
         builder: (context) => AlertDialog(
           title: const Text("Diqqat"),
           content: const Text("Barcha savollarga javob berilmadi. Davom ettirmoqchimisiz?"),
           actions: [
             TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("Yo'q")),
             TextButton(onPressed: () => Navigator.pop(context, true), child: const Text("Ha")),
           ],
         )
       );
       if (confirm != true) return;
    }

    setState(() => _isSubmitting = true);
    try {
      final success = await _dataService.finishSurvey(_surveyData!.quizRuleId);
      if (success) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("So'rovnoma muvaffaqiyatli yakunlandi!")),
          );
          Navigator.pop(context, true);
        }
      } else {
        throw Exception("Server xatosi");
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Xatolik: $e")),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }
}
