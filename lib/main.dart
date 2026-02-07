import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'core/providers/auth_provider.dart';
import 'core/providers/notification_provider.dart';
import 'core/services/data_service.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/home/screens/home_screen.dart';
import 'core/theme/app_theme.dart';
import 'core/services/push_notification_service.dart';
import 'package:firebase_core/firebase_core.dart';

import 'features/tutor/screens/tutor_home_screen.dart'; // [NEW]

import 'package:app_links/app_links.dart';
import 'dart:async';
import 'dart:io';

import 'core/network/direct_http_overrides.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase (Requires project settings)
  try {
    await Firebase.initializeApp();
    // Non-blocking initialization to speed up startup
    PushNotificationService.initialize(); 
  } catch (e) {
    debugPrint("Firebase Init Error: $e");
  }

  // FIX: Force DIRECT connection to avoid "Connection refused" on random ports (Simulators often inherit bad Proxies)
  HttpOverrides.global = DirectHttpOverrides(); 
  
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => NotificationProvider()),
        Provider(create: (_) => DataService()),
      ],
      child: const TalabaHamkorApp(),
    ),
  );
}

// Bypass Bad SSL Certificate (Android Emulator / University Server issues)
class MyHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback = (X509Certificate cert, String host, int port) => true;
  }
}

class TalabaHamkorApp extends StatefulWidget {
  const TalabaHamkorApp({super.key});

  @override
  State<TalabaHamkorApp> createState() => _TalabaHamkorAppState();
}

class _TalabaHamkorAppState extends State<TalabaHamkorApp> {
  late AppLinks _appLinks;
  StreamSubscription<Uri>? _linkSubscription;
  final GlobalKey<NavigatorState> _navigatorKey = GlobalKey<NavigatorState>();

  @override
  void initState() {
    super.initState();
    _initDeepLinks();
  }

  Future<void> _initDeepLinks() async {
    _appLinks = AppLinks();
    _linkSubscription = _appLinks.uriLinkStream.listen((uri) {
      _handleDeepLink(uri);
    });
  }

  void _handleDeepLink(Uri uri) {
    debugPrint("Deep Link Received: $uri");
    // Supports both talabahamkor://login (Standard) and talabahamkor://auth (Legacy)
    if (uri.scheme == 'talabahamkor' && (uri.host == 'login' || uri.host == 'auth')) {
      final token = uri.queryParameters['token'];
      if (token != null) {
        if (mounted) {
           Provider.of<AuthProvider>(context, listen: false).loginWithToken(token).then((error) {
             if (error != null) {
                debugPrint("Login Error: $error");
             }
           });
        }
      }
    }
  }

  @override
  void dispose() {
    _linkSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      navigatorKey: _navigatorKey,
      title: 'tengdosh',
      theme: AppTheme.lightTheme,
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('uz', 'UZ'), 
        Locale('ru', 'RU'),
        Locale('en', 'US'),
      ],
      // Force Uzbek as default if system is not supported or mixed
      locale: const Locale('uz', 'UZ'),
      home: Consumer<AuthProvider>(
        builder: (context, auth, _) {
          if (auth.isLoading) {
             return const Scaffold(body: Center(child: CircularProgressIndicator()));
          }
          if (auth.isAuthenticated) {
            return const HomeScreen();
          }
          return const LoginScreen();
        },
      ),
      debugShowCheckedModeBanner: false,
    );
  }
}
