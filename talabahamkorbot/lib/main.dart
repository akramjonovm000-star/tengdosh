import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'core/providers/auth_provider.dart';
import 'core/services/data_service.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/home/screens/home_screen.dart';
import 'core/theme/app_theme.dart';

import 'dart:io';
import 'dart:async';
import 'package:app_links/app_links.dart';

void main() {
  HttpOverrides.global = MyHttpOverrides(); // Bypass SSL issues for Emulator
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
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

    // Check initial link (if app opened via link)
    // try {
    //   final initialUri = await _appLinks.getInitialLink(); // getInitialLink might be removed in 6.0, assume getInitialUri
    //   if (initialUri != null) {
    //     _handleDeepLink(initialUri);
    //   }
    // } catch (e) {
    //   print("Initial Deep Link Error: $e");
    // }

    // Listen to link stream
    _linkSubscription = _appLinks.uriLinkStream.listen((uri) {
      _handleDeepLink(uri);
    });
  }

  void _handleDeepLink(Uri uri) {
    print("Deep Link Received: $uri");
    if (uri.scheme == 'talabahamkor' && uri.host == 'auth') {
      final token = uri.queryParameters['token'];
      if (token != null) {
        print("Token found: $token");
        // Use the navigator context or provider context
        // Since we are at root, we can use _navigatorKey.currentContext or just rely on Provider at tree top? 
        // Provider is above MaterialApp, so we can't access it easily via context of `this` widget's build if this widget is child of Provider?
        // Wait, TalabaHamkorApp IS child of Provider in main(). So `context` here (in State) has access to Provider? 
        // No, TalabaHamkorApp is child. So `context` in build() works. 
        // But inside `_handleDeepLink`, we need a context that has Provider. 
        // `context` of State is valid as long as widget is mounted.
        
        if (mounted) {
           Provider.of<AuthProvider>(context, listen: false).loginWithToken(token).then((error) {
             if (error != null) {
                // Show error if possible, e.g. via scaffoldMessenger of navigator
                // But we don't have easy access to Scaffold here unless we use a global key for scaffoldMessenger
                print("Login Error: $error");
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
