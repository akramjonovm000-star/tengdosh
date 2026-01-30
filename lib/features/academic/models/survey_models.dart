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
      notStarted: _parseSurveyList(data['not_started']),
      inProgress: _parseSurveyList(data['in_progress']),
      finished: _parseSurveyList(data['finished']),
      totalPending: stats['total_pending'] ?? 0,
      totalCompleted: stats['total_completed'] ?? 0,
    );
  }

  static List<Survey> _parseSurveyList(dynamic data) {
    if (data == null) return [];
    if (data is List) {
      return data.map((e) => Survey.fromJson(e)).toList();
    }
    if (data is Map) {
      return data.values.map((e) => Survey.fromJson(e)).toList();
    }
    return [];
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
      variants: _parseStringList(json['variants']),
      answers: _parseStringList(json['answers']),
    );
  }

  static List<String> _parseStringList(dynamic data) {
    if (data == null) return [];
    if (data is List) {
      return data.map((e) => e.toString()).toList();
    }
    if (data is Map) {
      return data.values.map((e) => e.toString()).toList();
    }
    return [];
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
      questions: _parseQuestionList(data['questions']),
      title: projection['theme'] ?? '',
      description: '',
    );
  }

  static List<SurveyQuestion> _parseQuestionList(dynamic data) {
    if (data == null) return [];
    if (data is List) {
      return data.map((e) => SurveyQuestion.fromJson(e)).toList();
    }
    if (data is Map) {
      return data.values.map((e) => SurveyQuestion.fromJson(e)).toList();
    }
    return [];
  }
}
