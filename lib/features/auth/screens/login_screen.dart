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
  bool _isPolicyAccepted = false; 
  String? _errorMessage; // NEW

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
                  
                    TextFormField(
                    controller: _loginController,
                    onChanged: (_) {
                      if (_errorMessage != null) setState(() => _errorMessage = null);
                    },
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
                    onChanged: (_) {
                      if (_errorMessage != null) setState(() => _errorMessage = null);
                    },
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
                          if (_errorMessage != null)
                            Container(
                              margin: const EdgeInsets.only(bottom: 16.0),
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                              decoration: BoxDecoration(
                                color: Colors.red.shade50,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: Colors.red.shade200),
                              ),
                              child: Row(
                                children: [
                                  Icon(Icons.error_outline, color: Colors.red.shade700, size: 20),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Text(
                                      _errorMessage!,
                                      style: TextStyle(
                                        color: Colors.red.shade700,
                                        fontSize: 14,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
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
                            icon: Icon(
                              Icons.badge_outlined, 
                              color: _isPolicyAccepted ? AppTheme.primaryBlue : Colors.grey, 
                              size: 20
                            ),
                            label: Text(
                              "OneID orqali kirish (xodimlar uchun)", 
                              style: TextStyle(
                                color: _isPolicyAccepted ? AppTheme.primaryBlue : Colors.grey, 
                                fontSize: 13, 
                                fontWeight: FontWeight.bold
                              )
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
          initialChildSize: 0.85,
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
                      children: [
                        _buildSectionHeader("1. UMUMIY QOIDALAR"),
                        _buildSectionText(
                          "Ushbu Maxfiylik Siyosati \"PRIMEWAY GROUP\" MChJ (keyingi o'rinlarda \"Kompaniya\") tomonidan ishlab chiqilgan \"Tengdosh\" platformasi foydalanuvchilarining shaxsiy ma'lumotlarini himoya qilish tartibini belgilaydi.\n\n"
                          "1.1. Platforma maqsadi: \"Tengdosh\" – bu talabalar, o'qituvchilar va ma'muriyat o'rtasidagi o'quv jarayonini raqamlashtirish va OTM HEMIS tizimi bilan integratsiya qilishga qaratilgan innovatsion ekotizimdir.\n\n"
                          "1.2. Ilovadan ro'yxatdan o'tish orqali Siz ushbu Siyosat shartlarini to'liq qabul qilgan hisoblanasiz."
                        ),

                        _buildSectionHeader("2. YIG'ILADIGAN MA'LUMOTLAR"),
                        _buildSectionText(
                          "Biz Sizga xizmat ko'rsatish sifatini oshirish maqsadida quyidagi ma'lumotlarni yig'amiz:\n"
                          "• Shaxsiy ma'lumotlar: Ism-familiya, telefon raqami, talaba ID (HEMIS ID).\n"
                          "• Ta'lim ma'lumotlari: Baholar, davomat, dars jadvallari (HEMIS orqali).\n"
                          "• Texnik ma'lumotlar: IP-manzil, qurilma modeli (xavfsizlik va analitika uchun)."
                        ),

                        _buildSectionHeader("3. PREMIUM XIZMATLAR VA TO'LOVLAR"),
                        _buildSectionText(
                          "3.1. Platforma ba'zi qo'shimcha imkoniyatlarni (reklamasiz rejim, statistika) \"Premium\" obuna sifatida taklif qilishi mumkin.\n"
                          "3.2. To'lovlar uchinchi tomon to'lov tizimlari (Payme, Click) orqali amalga oshiriladi. Biz Sizning bank karta ma'lumotlaringizni saqlamaymiz.\n"
                          "3.3. Qaytarish siyosati: Raqamli xizmatlar ko'rsatilgan hisoblanganligi sababli, Premium obuna uchun to'langan mablag'lar qoida tariqasida qaytarilmaydi."
                        ),

                        _buildSectionHeader("4. XAVFSIZLIK PROTOKOLLARI"),
                        _buildSectionText(
                          "Biz Sizning ma'lumotlaringizni himoya qilish uchun ilg'or xalqaro standartlarni qo'llaymiz:\n"
                          "• Mijoz Tomonida Shifrlash (Client-Side Encryption): Sizning HEMIS parolingiz va sessiya tokenlaringiz bizning serverlarimizda emas, balki faqat Sizning qurilmangiz xotirasida kuchli shifrlangan holda saqlanadi. Serverda faqat vaqtinchalik va shifrlangan ma'lumotlar aylanadi.\n"
                          "• Action Token System (ATS): Ilova orqali amalga oshiriladigan har bir muhim so'rov (POST) maxsus kriptografik shifr (\"Action Token\") bilan imzolanadi. Bu shifr faqat Sizning qurilmangizda shakllanadi.\n"
                          "• O'g'rilikdan Himoya: Agar Sizning sessiya kalitingiz (token) o'g'irlangan taqdirda ham, tajovuzkor Sizning nomingizdan biron bir ma'lumotni o'zgartira olmaydi yoki yubora olmaydi, chunki unda qurilmangizga bog'langan maxsus shifr (\"Action Token\") mavjud bo'lmaydi.\n"
                          "• Security Watchdog: Tizim 24/7 rejimda shubhali harakatlarni kuzatib boradi."
                        ),

                        _buildSectionHeader("5. NIZOLARNI HAL QILISH"),
                        _buildSectionText(
                          "5.1. Foydalanuvchi va Kompaniya o'rtasidagi nizolar dastlab muzokaralar yo'li bilan hal qilinadi.\n"
                          "5.2. Agar nizoni 30 kun ichida hal qilish imkoni bo'lmasa, nizo \"PRIMEWAY GROUP\" MChJ joylashgan hududdagi (O'zbekiston Respublikasi) tegishli sudida ko'rib chiqiladi."
                        ),

                        _buildSectionHeader("6. MA'SULIYATNI CHEKLASH"),
                        _buildSectionText(
                          "6.1. Kompaniya HEMIS tizimidagi texnik nosozliklar yoki internet provayderlarining aybi bilan yuzaga kelgan uzilishlar uchun javobgar emas.\n"
                          "6.2. Foydalanuvchi o'z login va paroli xavfsizligi uchun shaxsan javobgardir."
                        ),

                        _buildSectionHeader("7. BOG'LANISH"),
                        _buildSectionText(
                          "Savollar va takliflar uchun:\n"
                          "\"PRIMEWAY GROUP\" MChJ\n"
                          "Email: support@tengdosh.uz (yoki ilova ichidagi 'Yordam' bo'limi)"
                        ),
                        
                        const SizedBox(height: 30),
                        const Center(
                           child: Text(
                             "So'nggi yangilanish: 16-Fevral, 2026-yil",
                             style: TextStyle(color: Colors.grey, fontSize: 12),
                           ),
                        ),
                        const SizedBox(height: 40),
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
                      child: const Text("Tushunarli & Qabul qilaman", style: TextStyle(fontWeight: FontWeight.bold)),
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
