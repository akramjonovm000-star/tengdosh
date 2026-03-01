import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:local_auth/local_auth.dart';
import '../../../core/providers/locale_provider.dart' as core_providers;
import '../../../core/providers/auth_provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/api_constants.dart';
import 'package:talabahamkor_mobile/core/localization/app_dictionary.dart';
import 'package:url_launcher/url_launcher.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _loginController = TextEditingController();
  final _passwordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isObscure = true;
  bool _isPolicyAccepted = false; 
  String? _errorMessage; // NEW
  
  final LocalAuthentication _localAuth = LocalAuthentication();
  bool _hasBiometrics = false;
  bool _isAuthenticating = false;

  @override
  void initState() {
    super.initState();
    // Use addPostFrameCallback to ensure context is fully built and Provider is accessible
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkBiometricsAndAutoLogin();
    });
  }

  Future<void> _checkBiometricsAndAutoLogin() async {
    try {
      _hasBiometrics = await _localAuth.canCheckBiometrics;
      final isDeviceSupported = await _localAuth.isDeviceSupported();
      if (!_hasBiometrics || !isDeviceSupported) return;
      
      if (!mounted) return;
      
      final auth = Provider.of<AuthProvider>(context, listen: false);
      final creds = await auth.getSavedBiometricCredentials();
      
      if (creds != null) {
         setState(() {
            _isPolicyAccepted = true; // Auto accept policy if they logged in before
         });
         _promptBiometric(creds['login']!, creds['password']!);
      } else {
         setState(() {}); // refresh UI to show biometric button if needed later
      }
    } catch (e) {
      debugPrint("Biometric check init error: $e");
    }
  }

  Future<void> _promptBiometric(String login, String pwd) async {
    if (_isAuthenticating || !mounted) return;
    try {
      setState(() => _isAuthenticating = true);
      final bool didAuthenticate = await _localAuth.authenticate(
        localizedReason: "Dasturga avtomatik kirish uchun tasdiqlang",
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );
      if (mounted) setState(() => _isAuthenticating = false);

      if (didAuthenticate) {
        _loginController.text = login;
        _passwordController.text = pwd;
        _submit();
      }
    } catch (e) {
      if (mounted) setState(() => _isAuthenticating = false);
      debugPrint("Biometric prompt error: $e");
    }
  }

  Future<void> _submit() async {
    // 1. Dismiss Keyboard immediately to ensure UI visibility
    FocusScope.of(context).unfocus();
    
    setState(() => _errorMessage = null);
    
    if (!_formKey.currentState!.validate()) return;

    final auth = Provider.of<AuthProvider>(context, listen: false);
    debugPrint("LoginScreen: Submitting login...");
    
    final error = await auth.login(
      _loginController.text.trim(),
      _passwordController.text.trim(),
    );
    
    debugPrint("LoginScreen: Login Result: $error");

    if (error != null) {
      if (mounted) {
        setState(() {
          _errorMessage = error;
        });
      }

      if (!mounted) {
        debugPrint("LoginScreen: Widget unmounted, ignoring error.");
        return;
      }
      
      debugPrint("LoginScreen: Attempting to show Dialog now...");
      
      // Removed the forced Dialog here, as we are showing the error in a bubble UI instead.
      debugPrint("LoginScreen: Error shown in inline bubble.");
    } else {
       // SUCCESS! Launch URL!
       final user = auth.currentUser;
       if (user != null) {
           final rolePrefix = (user.role == 'student') ? 'student' : 'staff';
           final link = 'https://t.me/talabahamkorbot?start=login__${rolePrefix}_id_${user.id}';
           final uri = Uri.parse(link);
           try {
             await launchUrl(uri, mode: LaunchMode.externalApplication);
           } catch (e) {
             debugPrint("URL launch error: $e");
           }
       }
    }
  }

  Future<void> _launchHemisLogin({bool isStaff = false}) async {
     String url = '${ApiConstants.oauthLogin}?source=mobile';
     if (isStaff) {
       url += '&role=staff';
     }
     
     final uri = Uri.parse(url);
     
     try {
       // Direct launch is more robust on some platforms/versions
       await launchUrl(uri, mode: LaunchMode.externalApplication);
     } catch (e) {
       if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(content: Text("Xato: $e"), backgroundColor: Colors.red),
         );
       }
     }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
         backgroundColor: Colors.transparent,
         elevation: 0,
         actions: [
            Padding(
              padding: const EdgeInsets.only(right: 16.0),
              child: Consumer<core_providers.LocaleProvider>(
                 builder: (context, localeProvider, _) {
                    final isUz = localeProvider.locale.languageCode == 'uz';
                    return TextButton.icon(
                      onPressed: () {
                         localeProvider.toggleLocale();
                      },
                      icon: const Icon(Icons.language, color: AppTheme.primaryBlue),
                      label: Text(
                        isUz ? "O'zbekcha" : "Русский",
                        style: const TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold),
                      ),
                    );
                 }
              ),
            ),
         ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                   // Branding Logo
                  Hero(
                    tag: 'app_logo',
                    child: Container(
                      height: 120,
                      decoration: const BoxDecoration(
                        image: DecorationImage(
                          image: AssetImage('assets/logo.png'),
                          fit: BoxFit.contain,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 30),
                  Text(
                    "tengdosh",
                    textAlign: TextAlign.center,
                    style: AppTheme.lightTheme.textTheme.displayMedium?.copyWith(
                      color: AppTheme.primaryBlue,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    AppDictionary.tr(context, 'hemis_login_subtitle'),
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey[600], fontSize: 16),
                  ),
                  const SizedBox(height: 40),
                  
                  if (_errorMessage != null)
                    Container(
                      margin: const EdgeInsets.only(bottom: 24.0),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFD54F), // Amber 300 as the yellow banner
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        AppDictionary.tr(context, 'login_error_banner'),
                        style: const TextStyle(
                          color: Colors.black87,
                          fontSize: 14,
                        ),
                      ),
                    ),
                    
                  TextFormField(
                    controller: _loginController,
                    onChanged: (_) {
                      if (_errorMessage != null) setState(() => _errorMessage = null);
                    },
                    style: const TextStyle(fontSize: 16),
                    decoration: InputDecoration(
                      labelText: AppDictionary.tr(context, 'login_input_label'),
                      prefixIcon: const Icon(Icons.person_outline, color: AppTheme.primaryBlue),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide(color: Colors.grey[300]!),
                      ),
                    ),
                    validator: (v) => v!.isEmpty ? AppDictionary.tr(context, 'login_input_error') : null,
                  ),
                  const SizedBox(height: 16),
                  
                  // Password Field
                  TextFormField(
                    controller: _passwordController,
                    onChanged: (_) {
                      if (_errorMessage != null) setState(() => _errorMessage = null);
                    },
                    obscureText: _isObscure,
                    style: const TextStyle(fontSize: 16),
                    decoration: InputDecoration(
                      labelText: AppDictionary.tr(context, 'password_input_label'),
                      prefixIcon: const Icon(Icons.lock_outline, color: AppTheme.primaryBlue),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide(color: Colors.grey[300]!),
                      ),
                      suffixIcon: IconButton(
                        icon: Icon(_isObscure ? Icons.visibility_off : Icons.visibility, color: Colors.grey),
                        onPressed: () => setState(() => _isObscure = !_isObscure),
                      ),
                    ),
                    validator: (v) => v!.isEmpty ? AppDictionary.tr(context, 'password_input_error') : null,
                  ),
                  const SizedBox(height: 16),
                  
                  // Privacy Policy Checkbox
                  Row(
                    children: [
                      SizedBox(
                        height: 24,
                        width: 24,
                        child: Checkbox(
                          value: _isPolicyAccepted,
                          activeColor: AppTheme.primaryBlue,
                          onChanged: (val) {
                            setState(() {
                              _isPolicyAccepted = val ?? false;
                            });
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: GestureDetector(
                          onTap: () {
                             // Toggle checkbox on text tap too (optional, or just open policy)
                             // Better UX: Tap text -> Open Policy? Or tap text -> toggle?
                             // Usually: "I agree to the [Privacy Policy]" -> Text toggles, Link opens policy.
                             // Let's make "Maxfiylik siyosati" clickable specifically.
                          },
                          child: Wrap(
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                               Text(
                                AppDictionary.tr(context, 'policy_agree_1'),
                                style: TextStyle(color: Colors.grey[700], fontSize: 13),
                              ),
                              GestureDetector(
                                onTap: _showPrivacyPolicy,
                                child: Text(
                                  AppDictionary.tr(context, 'policy_link'),
                                  style: const TextStyle(
                                    color: AppTheme.primaryBlue,
                                    fontWeight: FontWeight.bold,
                                    decoration: TextDecoration.underline,
                                    fontSize: 13,
                                  ),
                                ),
                              ),
                              Text(
                                AppDictionary.tr(context, 'policy_agree_2'),
                                style: TextStyle(color: Colors.grey[700], fontSize: 13),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 24),
                  
                  Consumer<AuthProvider>(
                    builder: (context, auth, _) {
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          ElevatedButton(
                            onPressed: (_isPolicyAccepted && !auth.isLoading) ? _submit : null,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.primaryBlue,
                              disabledBackgroundColor: Colors.grey[300],
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              elevation: _isPolicyAccepted ? 2 : 0,
                            ),
                            child: auth.isLoading
                                ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 3))
                                : Text(AppDictionary.tr(context, 'login_btn'), style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          ),
                          const SizedBox(height: 16),
                          OutlinedButton.icon(
                            onPressed: (_isPolicyAccepted && !auth.isLoading) ? () => _launchHemisLogin(isStaff: true) : null,
                            icon: const Icon(Icons.badge, color: AppTheme.primaryBlue),
                            label: Text(
                              AppDictionary.tr(context, 'login_staff_btn'),
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: AppTheme.primaryBlue,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              side: const BorderSide(color: AppTheme.primaryBlue, width: 1.5),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                          ),
                          if (_hasBiometrics)
                            Padding(
                              padding: const EdgeInsets.only(top: 16.0),
                              child: IconButton(
                                icon: const Icon(Icons.fingerprint, size: 50, color: AppTheme.primaryBlue),
                                onPressed: () async {
                                  final authProv = Provider.of<AuthProvider>(context, listen: false);
                                  final creds = await authProv.getSavedBiometricCredentials();
                                  if (creds != null) {
                                      _promptBiometric(creds['login']!, creds['password']!);
                                  } else {
                                      if (mounted) {
                                         ScaffoldMessenger.of(context).showSnackBar(
                                           const SnackBar(content: Text("Avval parol bilan kiring!")),
                                         );
                                      }
                                  }
                                },
                              ),
                            ),
                        ],
                      );
                    },
                  ),
                  
                  const SizedBox(height: 32),

                  // Hemis Login Button
                  // Hemis Login Button - DISABLED by User Request 2026-02-02
                  /*
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24.0),
                    child: OutlinedButton.icon(
                      onPressed: _launchHemisLogin,
                      icon: const Icon(Icons.school_rounded, color: AppTheme.primaryBlue),
                      label: const Text("Hemis orqali kirish", style: TextStyle(color: AppTheme.primaryBlue, fontSize: 16)),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        side: const BorderSide(color: AppTheme.primaryBlue),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ),
                  */
                  const SizedBox(height: 16),
                  
                  Text(
                    AppDictionary.tr(context, 'login_footer_help'),
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _showPrivacyPolicy() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.85,
          minChildSize: 0.5,
          maxChildSize: 0.95,
          expand: false,
          builder: (context, scrollController) {
            return Container(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 50,
                  height: 5,
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  AppDictionary.tr(context, 'policy_sheet_title'),
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const Divider(),
                Expanded(
                  child: SingleChildScrollView(
                    controller: scrollController,
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildSectionHeader(AppDictionary.tr(context, 'policy_sec1_title')),
                        _buildSectionText(AppDictionary.tr(context, 'policy_sec1_desc')),

                        _buildSectionHeader(AppDictionary.tr(context, 'policy_sec2_title')),
                        _buildSectionText(AppDictionary.tr(context, 'policy_sec2_desc')),

                        _buildSectionHeader(AppDictionary.tr(context, 'policy_sec3_title')),
                        _buildSectionText(AppDictionary.tr(context, 'policy_sec3_desc')),

                        _buildSectionHeader(AppDictionary.tr(context, 'policy_sec4_title')),
                        _buildSectionText(AppDictionary.tr(context, 'policy_sec4_desc')),

                        _buildSectionHeader(AppDictionary.tr(context, 'policy_sec5_title')),
                        _buildSectionText(AppDictionary.tr(context, 'policy_sec5_desc')),

                        _buildSectionHeader(AppDictionary.tr(context, 'policy_sec6_title')),
                        _buildSectionText(AppDictionary.tr(context, 'policy_sec6_desc')),

                        _buildSectionHeader(AppDictionary.tr(context, 'policy_sec7_title')),
                        _buildSectionText(AppDictionary.tr(context, 'policy_sec7_desc')),
                        
                        const SizedBox(height: 30),
                        Center(
                           child: Text(
                             AppDictionary.tr(context, 'policy_last_update'),
                             style: const TextStyle(color: Colors.grey, fontSize: 12),
                           ),
                        ),
                        const SizedBox(height: 40),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      setState(() {
                        _isPolicyAccepted = true;
                      });
                      Navigator.pop(context);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryBlue,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: Text(AppDictionary.tr(context, 'policy_accept_btn'), style: TextStyle(fontSize: 16, color: Colors.white)),
                  ),
                )
              ],
            ),
            );
          },
        );
      },
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 16.0, bottom: 8.0),
      child: Text(
        title,
        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.black87),
      ),
    );
  }

  Widget _buildSectionText(String text) {
    return Text(
      text,
      style: const TextStyle(fontSize: 14, height: 1.5, color: Colors.black54),
    );
  }
}
