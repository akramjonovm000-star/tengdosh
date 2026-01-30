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
    return Survey(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      status: json['status'] ?? 'not_started',
      startDate: json['start_date'] != null 
          ? DateTime.fromMillisecondsSinceEpoch(json['start_date'] * 1000) 
          : null,
      endDate: json['end_date'] != null 
          ? DateTime.fromMillisecondsSinceEpoch(json['end_date'] * 1000) 
          : null,
    );
  }
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
  final List<SurveyAnswerOption> answers;

  SurveyQuestion({
    required this.id,
    required this.text,
    required this.type,
    required this.answers,
  });

  factory SurveyQuestion.fromJson(Map<String, dynamic> json) {
    return SurveyQuestion(
      id: json['id'] ?? 0,
      text: json['text'] ?? '',
      type: json['type'] ?? 'radio',
      answers: (json['answers'] as List? ?? [])
          .map((e) => SurveyAnswerOption.fromJson(e))
          .toList(),
    );
  }
}

class SurveyAnswerOption {
  final int id;
  final String text;

  SurveyAnswerOption({
    required this.id,
    required this.text,
  });

  factory SurveyAnswerOption.fromJson(Map<String, dynamic> json) {
    return SurveyAnswerOption(
      id: json['id'] ?? 0,
      text: json['text'] ?? '',
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
    
    return SurveyStartResponse(
      quizRuleId: data['quiz_rule_id'] ?? 0,
      questions: (data['questions'] as List? ?? [])
          .map((e) => SurveyQuestion.fromJson(e))
          .toList(),
      title: quizInfo['title'] ?? '',
      description: quizInfo['description'] ?? '',
    );
  }
}
