class Survey {
  final int id;
  final String name;
  final String status;
  final DateTime? startDate;
  final DateTime? endDate;

  Survey({
    required this.id,
    required this.name,
    required this.status,
    this.startDate,
    this.endDate,
  });

  factory Survey.fromJson(Map<String, dynamic> json) {
    // Correctly handle the nested quizRuleProjection structure from HEMIS
    final projection = json['quizRuleProjection'] ?? {};
    final rawStatus = json['status'] ?? '';
    
    return Survey(
      id: projection['id'] ?? 0,
      name: projection['theme'] ?? rawStatus,
      status: rawStatus,
      startDate: null,
      endDate: projection['endTime'] != null 
          ? DateTime.fromMillisecondsSinceEpoch(projection['endTime']) 
          : null,
    );
  }

  bool get isFinished => status == 'Yakunlangan' || status == 'finished';
}

class SurveyListResponse {
  final List<Survey> notStarted;
  final List<Survey> inProgress;
  final List<Survey> finished;
  final int totalPending;
  final int totalCompleted;

  SurveyListResponse({
    required this.notStarted,
    required this.inProgress,
    required this.finished,
    required this.totalPending,
    required this.totalCompleted,
  });

  factory SurveyListResponse.fromJson(Map<String, dynamic> json) {
    final data = json['data'] ?? {};
    final stats = data['stats'] ?? {};
    
    return SurveyListResponse(
      notStarted: (data['not_started'] as List? ?? [])
          .map((e) => Survey.fromJson(e))
          .toList(),
      inProgress: (data['in_progress'] as List? ?? [])
          .map((e) => Survey.fromJson(e))
          .toList(),
      finished: (data['finished'] as List? ?? [])
          .map((e) => Survey.fromJson(e))
          .toList(),
      totalPending: stats['total_pending'] ?? 0,
      totalCompleted: stats['total_completed'] ?? 0,
    );
  }
}

class SurveyQuestion {
  final int id;
  final String text;
  final String type; // radio, checkbox, input
  final List<String> variants;
  final List<String> answers;

  SurveyQuestion({
    required this.id,
    required this.text,
    required this.type,
    required this.variants,
    required this.answers,
  });

  factory SurveyQuestion.fromJson(Map<String, dynamic> json) {
    return SurveyQuestion(
      id: json['id'] ?? 0,
      text: json['quiz'] ?? '',
      type: json['buttonType'] ?? 'radio',
      variants: List<String>.from(json['variants'] ?? []),
      answers: List<String>.from(json['answers'] ?? []),
    );
  }
}

class SurveyStartResponse {
  final int quizRuleId;
  final List<SurveyQuestion> questions;
  final String title;
  final String description;

  SurveyStartResponse({
    required this.quizRuleId,
    required this.questions,
    required this.title,
    required this.description,
  });

  factory SurveyStartResponse.fromJson(Map<String, dynamic> json) {
    final data = json['data'] ?? {};
    final quizInfo = data['quiz_info'] ?? {};
    final projection = quizInfo['quizRuleProjection'] ?? {};
    
    return SurveyStartResponse(
      quizRuleId: projection['id'] ?? 0,
      questions: (data['questions'] as List? ?? [])
          .map((e) => SurveyQuestion.fromJson(e))
          .toList(),
      title: projection['theme'] ?? '',
      description: '',
    );
  }
}
