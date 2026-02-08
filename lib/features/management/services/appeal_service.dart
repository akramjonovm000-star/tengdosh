import 'dart:convert';
import 'package:talabahamkor_mobile/core/constants/api_constants.dart';
import 'package:talabahamkor_mobile/core/services/data_service.dart';
import '../models/appeal_model.dart';
import 'package:http/http.dart' as http;

class AppealService {
  final DataService _dataService = DataService();

  Future<AppealStats> getStats() async {
    final response = await _dataService.authGet(ApiConstants.managementAppealsStats);
    
    if (response.statusCode == 200) {
      final body = json.decode(response.body);
      return AppealStats.fromJson(body);
    } else {
      throw Exception('Statistikani yuklab bo\'lmadi');
    }
  }

  Future<List<Appeal>> getAppeals({
    int page = 1, 
    String? status, 
    String? faculty, 
    String? aiTopic,
    String? assignedRole
  }) async {
    String url = '${ApiConstants.managementAppealsList}?page=$page&limit=20';
    if (status != null) url += '&status=$status';
    if (faculty != null) url += '&faculty=$faculty';
    if (aiTopic != null) url += '&ai_topic=$aiTopic';
    if (assignedRole != null) url += '&assigned_role=$assignedRole';
    
    final response = await _dataService.authGet(url);
    
    if (response.statusCode == 200) {
      final List body = json.decode(response.body);
      return body.map((e) => Appeal.fromJson(e)).toList();
    } else {
      throw Exception('Murojaatlarni yuklab bo\'lmadi');
    }
  }

  Future<void> resolveAppeal(int id) async {
    final url = '${ApiConstants.managementAppealsResolve}/$id/resolve';
    final response = await _dataService.authPost(url);
    
    if (response.statusCode != 200) {
       throw Exception('Murojaatni yopib bo\'lmadi');
    }
  }

  Future<Map<String, dynamic>> clusterAppeals() async {
    final response = await _dataService.authPost(ApiConstants.aiClusterAppeals);
    
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('AI Tahlil xatosi');
    }
  }
}

// Extension to access internal _get/_post of DataService if they are private
// DataService methods are _get/_post which are private.
// But it likely has public generic methods or I have to add them?
// Let's check DataService again. It usually exposes authGet/authPost or similar.
// Looking at DataService view earlier:
// lines 45: Future<http.Response> _get(...) async
// It seems methods are private `_get`.
// I need to check if there are public wrappers.
// If not, I should add `authGet` and `authPost` to DataService or make `_get` public.

// Wait, I saw `getProfile` uses `_get`.
// I should extend DataService or modify it to expose `authGet`.
// Let's modify DataService to make `_get` public as `authGet` and `_post` as `authPost`.
