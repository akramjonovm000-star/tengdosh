import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/api_constants.dart';
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
  bool _isPolicyAccepted = false; // New state

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final auth = Provider.of<AuthProvider>(context, listen: false);
    final error = await auth.login(
      _loginController.text.trim(),
      _passwordController.text.trim(),
    );

    if (error != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error), backgroundColor: Colors.red),
      );
    }
  }

  Future<void> _launchHemisLogin({bool isStaff = false}) async {
     String url = '${ApiConstants.oauthLogin}?source=mobile';
     if (isStaff) {
       url += '&role=staff';
     }
     
     final uri = Uri.parse(url);
     
     if (await canLaunchUrl(uri)) {
       await launchUrl(uri, mode: LaunchMode.externalApplication);
     } else {
       if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(content: Text("Brauzerni ochib bo'lmadi"), backgroundColor: Colors.red),
         );
       }
     }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
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
                    "HEMIS tizimidan kirish",
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey[600], fontSize: 16),
                  ),
                  const SizedBox(height: 40),
                  
                  // Login Field
                  TextFormField(
                    controller: _loginController,
                    style: const TextStyle(fontSize: 16),
                    decoration: InputDecoration(
                      labelText: "Login / Talaba ID",
                      prefixIcon: const Icon(Icons.person_outline, color: AppTheme.primaryBlue),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide(color: Colors.grey[300]!),
                      ),
                    ),
                    validator: (v) => v!.isEmpty ? "Iltimos loginni kiriting" : null,
                  ),
                  const SizedBox(height: 16),
                  
                  // Password Field
                  TextFormField(
                    controller: _passwordController,
                    obscureText: _isObscure,
                    style: const TextStyle(fontSize: 16),
                    decoration: InputDecoration(
                      labelText: "Parol",
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
                    validator: (v) => v!.isEmpty ? "Iltimos parolni kiriting" : null,
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
                                "Men ",
                                style: TextStyle(color: Colors.grey[700], fontSize: 13),
                              ),
                              GestureDetector(
                                onTap: _showPrivacyPolicy,
                                child: const Text(
                                  "Maxfiylik siyosati",
                                  style: TextStyle(
                                    color: AppTheme.primaryBlue,
                                    fontWeight: FontWeight.bold,
                                    decoration: TextDecoration.underline,
                                    fontSize: 13,
                                  ),
                                ),
                              ),
                              Text(
                                " bilan tanishib chiqdim va qabul qilaman.",
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
                                : const Text("Tizimga kirish", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          ),
                          const SizedBox(height: 16),
                          OutlinedButton.icon(
                            onPressed: (_isPolicyAccepted && !auth.isLoading) ? () => _launchHemisLogin(isStaff: true) : null,
                            icon: const Icon(Icons.badge_outlined, color: AppTheme.primaryBlue, size: 20),
                            label: const Text(
                              "OneID orqali kirish (xodimlar ucun)", 
                              style: TextStyle(color: AppTheme.primaryBlue, fontSize: 13, fontWeight: FontWeight.bold)
                            ),
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              side: BorderSide(color: _isPolicyAccepted ? AppTheme.primaryBlue : Colors.grey[300]!),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
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
                    "Agarda login yoki parolni unutgan bo'lsangiz, talabalar bo'limiga murojaat qiling.",
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey[500], fontSize: 12),
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
          initialChildSize: 0.7,
          minChildSize: 0.5,
          maxChildSize: 0.95,
          expand: false,
          builder: (context, scrollController) {
            return Column(
              children: [
                // Handle bar
                Center(
                  child: Container(
                    margin: const EdgeInsets.only(top: 12, bottom: 12),
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey[300],
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 8),
                  child: Text(
                    "Maxfiylik Siyosati",
                    style: AppTheme.lightTheme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ),
                const Divider(),
                Expanded(
                  child: SingleChildScrollView(
                    controller: scrollController,
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text(
                          "1. Umumiy qoidalar",
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        SizedBox(height: 8),
                        Text(
                          "Ushbu ilova (\"Tengdosh\") talabalarga o'quv jarayoni haqida ma'lumot berish, OTM yangiliklaridan xabardor qilish va o'zaro muloqotni ta'minlash maqsadida ishlab chiqilgan. Ilova OTMning HEMIS axborot tizimi bilan integratsiya qilingan.",
                          style: TextStyle(fontSize: 14, height: 1.5, color: Colors.black87),
                        ),
                        SizedBox(height: 16),
                        
                        Text(
                          "2. Ma'lumotlarni yig'ish va foydalanish",
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        SizedBox(height: 8),
                        Text(
                          "Biz sizning quyidagi shaxsiy ma'lumotlaringizni to'playmiz va qayta ishlaymiz:\n"
                          "• Ism, familiya va talaba ID raqami.\n"
                          "• O'quv jarayoni ma'lumotlari (baho, davomat, dars jadvali va h.k).\n"
                          "• Ilova orqali yuborilgan murojaatlar, xabarlar va fayllar.\n"
                          "• Qurilma haqidagi texnik ma'lumotlar (versiya, IP manzil - xavfsizlik uchun).",
                          style: TextStyle(fontSize: 14, height: 1.5, color: Colors.black87),
                        ),
                        SizedBox(height: 16),

                        Text(
                          "3. Ma'lumotlar xavfsizligi",
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        SizedBox(height: 8),
                        Text(
                          "Sizning login va parolingiz shifrlangan holda saqlanadi va uzatiladi. Biz sizning shaxsiy ma'lumotlaringizni uchinchi shaxslarga bermaymiz, faqat O'zbekiston Respublikasi qonunchiligida belgilangan hollar bundan mustasno.",
                          style: TextStyle(fontSize: 14, height: 1.5, color: Colors.black87),
                        ),
                        SizedBox(height: 16),

                        Text(
                          "4. Foydalanuvchi majburiyatlari",
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        SizedBox(height: 8),
                        Text(
                          "Siz o'z login va parolingizni boshqa shaxslarga bermaslikka majbursiz. Agrar hisobingizdan shubhali harakatlar sezilsa, darhol ma'muriyatga xabar berishingiz so'raladi.",
                          style: TextStyle(fontSize: 14, height: 1.5, color: Colors.black87),
                        ),
                         SizedBox(height: 16),
                        
                        Text(
                          "5. Bog'lanish",
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        SizedBox(height: 8),
                        Text(
                          "Ilova bo'yicha savol yoki takliflaringiz bo'lsa, 'Murojaatlar' bo'limi orqali bizga xabar berishingiz mumkin.",
                          style: TextStyle(fontSize: 14, height: 1.5, color: Colors.black87),
                        ),
                        SizedBox(height: 40),
                      ],
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryBlue,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: const Text("Tushunarli", style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ),
              ],
            );
          },
        );
      },
    );
  }
}
