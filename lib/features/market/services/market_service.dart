import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../../../core/constants/api_constants.dart';
import '../../../core/services/auth_service.dart';
import '../models/market_item.dart';

class MarketService {
  final AuthService _authService = AuthService();

  Future<List<MarketItem>> getItems({String? category, String? search, String sort = 'newest'}) async {
    final token = await _authService.getToken();
    if (token == null) return [];

    try {
      var uri = Uri.parse('${ApiConstants.backendUrl}/market');
      final queryParams = <String, String>{'sort': sort};
      if (category != null && category != 'all') queryParams['cat'] = category;
      if (search != null && search.isNotEmpty) queryParams['search'] = search;
      
      if (queryParams.isNotEmpty) {
        uri = uri.replace(queryParameters: queryParams);
      }

      final response = await http.get(
        uri,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return data.map((e) => MarketItem.fromJson(e)).toList();
      }
      return [];
    } catch (e) {
      print('Market Get Error: $e');
      return [];
    }
  }

  Future<bool> createItem(Map<String, dynamic> data) async {
    final token = await _authService.getToken();
    if (token == null) return false;

    try {
      final response = await http.post(
        Uri.parse('${ApiConstants.backendUrl}/market'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: json.encode(data),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Market Create Error: $e');
      return false;
    }
  }

  Future<bool> deleteItem(int id) async {
    final token = await _authService.getToken();
    if (token == null) return false;

    try {
      final response = await http.delete(
        Uri.parse('${ApiConstants.backendUrl}/market/$id'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Market Delete Error: $e');
      return false;
    }
  }
  Future<void> viewItem(int id) async {
    final token = await _authService.getToken();
    if (token == null) return;
    try {
      await http.post(
        Uri.parse('${ApiConstants.backendUrl}/market/$id/view'),
        headers: {'Authorization': 'Bearer $token'},
      );
    } catch (e) {
      print('View Item Error: $e');
    }
  }
}
