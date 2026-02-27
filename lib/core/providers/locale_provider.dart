import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LocaleProvider with ChangeNotifier {
  Locale _locale = const Locale('uz', 'UZ');
  bool _isLoaded = false;

  Locale get locale => _locale;
  bool get isLoaded => _isLoaded;

  LocaleProvider() {
    _loadSavedLocale();
  }

  Future<void> _loadSavedLocale() async {
    final prefs = await SharedPreferences.getInstance();
    final savedCode = prefs.getString('language_code');
    if (savedCode != null) {
      if (savedCode == 'ru') {
        _locale = const Locale('ru', 'RU');
      } else {
        _locale = const Locale('uz', 'UZ');
      }
    }
    _isLoaded = true;
    notifyListeners();
  }

  Future<void> setLocale(Locale newLocale) async {
    if (_locale == newLocale) return;
    _locale = newLocale;
    notifyListeners();

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('language_code', newLocale.languageCode);
  }

  void toggleLocale() {
    if (_locale.languageCode == 'uz') {
      setLocale(const Locale('ru', 'RU'));
    } else {
      setLocale(const Locale('uz', 'UZ'));
    }
  }
}
