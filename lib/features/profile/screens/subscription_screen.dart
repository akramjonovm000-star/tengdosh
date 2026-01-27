import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import '../../../../core/models/student.dart';
import '../models/subscription_plan.dart';
import 'package:url_launcher/url_launcher.dart';

class SubscriptionScreen extends StatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  State<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends State<SubscriptionScreen> {
  final DataService _dataService = DataService();
  Student? _student;
  List<SubscriptionPlan> _plans = [];
  bool _isLoading = true;
  String? _loadingAction;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final profileData = await _dataService.getProfile();
      final plansData = await _dataService.getSubscriptionPlans();
      
      if (mounted) {
        setState(() {
          _student = Student.fromJson(profileData);
          _plans = plansData.map((e) => SubscriptionPlan.fromJson(e)).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Ma'lumotlarni yuklashda xatolik: $e")),
        );
      }
    }
  }

  Future<void> _topUp(String provider) async {
    setState(() => _loadingAction = provider);
    try {
      String? url;
      if (provider == 'Payme') {
        url = await _dataService.getPaymeUrl(amount: 10000); // Default 10k top up
      } else if (provider == 'Click') {
        url = await _dataService.getClickUrl(amount: 10000);
      } else if (provider == 'Uzum') {
        url = await _dataService.getUzumUrl(amount: 10000);
      }

      if (url != null && await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      } else {
        throw Exception("To'lov havolasini ochib bo'lmadi");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Xatolik: $e")),
      );
    } finally {
      if (mounted) setState(() => _loadingAction = null);
    }
  }

  Future<void> _purchasePlan(SubscriptionPlan plan) async {
    setState(() => _loadingAction = 'purchase_${plan.id}');
    try {
      final result = await _dataService.purchasePlan(plan.id.toString());
      if (result['status'] == 'success') {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message']), backgroundColor: Colors.green),
        );
        _loadData(); // Refresh balance and status
      } else {
        throw Exception(result['detail'] ?? result['message'] ?? "Sotib olishda xatolik");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Xatolik: $e"), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted) setState(() => _loadingAction = null);
    }
  }

  Future<void> _activateTrial() async {
    setState(() => _loadingAction = 'trial');
    try {
      final result = await _dataService.activateTrial();
      if (result['status'] == 'success') {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message']), backgroundColor: Colors.green),
        );
        _loadData();
      } else {
        throw Exception(result['detail'] ?? result['message'] ?? "Sinov davrini faollashtirib bo'lmadi");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Xatolik: $e"), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted) setState(() => _loadingAction = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text("Premium obuna", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Premium Banner
              _buildPremiumBanner(),
              
              const SizedBox(height: 25),
              
              // 2. Features
              _buildFeatureItem(Icons.verified, "Premium belgisi (Custom Emoji)"),
              _buildFeatureItem(Icons.psychology, "AI moduli (Oyiga 25 ta)"),
              _buildFeatureItem(Icons.public, "Ijtimoiy faollik va reklamasiz"),
              
              const SizedBox(height: 30),

              // 3. Balance Header
              _buildBalanceHeader(),

              const SizedBox(height: 15),

              // 4. Payment Providers (Top up)
              const Text("Balansni to'ldirish:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 10),
              _buildTopUpSection(),

              const SizedBox(height: 30),
              
              // 5. Subscription Plans
              const Text("Tariflar:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 15),
              _buildPlansList(),

              const SizedBox(height: 20),

              // 6. Trial Section (Hide if Premium)
              if (_student?.isPremium == false && _student?.trialUsed == false) _buildTrialSection(),
              
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPremiumBanner() {
    bool isPremium = _student?.isPremium ?? false;
    String expiryText = "";
    
    if (isPremium && _student?.premiumExpiry != null) {
      // Simple date formatting
      DateTime expiry = DateTime.parse(_student!.premiumExpiry!);
      expiryText = "${expiry.day}.${expiry.month}.${expiry.year}";
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: isPremium 
            ? const LinearGradient(colors: [Color(0xFF00C853), Color(0xFF64DD17)]) // Green for Active
            : const LinearGradient(
                colors: [Color(0xFF6A11CB), Color(0xFF2575FC)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: (isPremium ? Colors.green : Colors.blue).withOpacity(0.3),
            blurRadius: 15,
            offset: const Offset(0, 8),
          )
        ],
      ),
      child: Column(
        children: [
          Icon(isPremium ? Icons.check_circle : Icons.workspace_premium, size: 70, color: Colors.white),
          const SizedBox(height: 15),
          Text(
            isPremium ? "Premium Faol" : "Premium talaba bo'ling",
            style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          if (isPremium)
            Text(
              "Amal qilish muddati: $expiryText gacha",
              style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500),
            )
          else
            const Text(
              "Barcha imkoniyatlardan cheklovsiz foydalaning",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white70, fontSize: 15),
            ),
        ],
      ),
    );
  }

  // ... (Balance Header and TopUp Section kept largely same, but verify context) ...
  // Actually I need to replace them or keep them if outside the range target.
  // The ReplaceContent chunk is huge. I will only target specific methods to be safe.
 
  // ...
  
  // (Moving to specific method replacements below)

  Widget _buildBalanceHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[200]!),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 10)
        ]
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Sizning balansingiz", style: TextStyle(color: Colors.grey[600], fontSize: 14)),
              const SizedBox(height: 4),
              Text(
                "${_student?.balance ?? 0} so'm",
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.black),
              ),
            ],
          ),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: Colors.green[50], shape: BoxShape.circle),
            child: const Icon(Icons.account_balance_wallet, color: Colors.green, size: 28),
          )
        ],
      ),
    );
  }

  Widget _buildTopUpSection() {
    return Row(
      children: [
        _buildSmallPaymentBtn("Payme", const Color(0xFF00CCCC), () => _topUp('Payme')),
        const SizedBox(width: 10),
        _buildSmallPaymentBtn("Click", const Color(0xFF0047BA), () => _topUp('Click')),
        const SizedBox(width: 10),
        _buildSmallPaymentBtn("Uzum", const Color(0xFF7000FF), () => _topUp('Uzum')),
      ],
    );
  }

  Widget _buildSmallPaymentBtn(String name, Color color, VoidCallback onTap) {
    bool loading = _loadingAction == name;
    return Expanded(
      child: InkWell(
        onTap: loading ? null : onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Center(
            child: loading
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
              : Text(name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ),
      ),
    );
  }

  Widget _buildPlansList() {
    return Column(
      children: _plans.map((plan) => _buildPlanCard(plan)).toList(),
    );
  }

  Widget _buildPlanCard(SubscriptionPlan plan) {
    bool loading = _loadingAction == 'purchase_${plan.id}';
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colors.blue[50], borderRadius: BorderRadius.circular(12)),
            child: Icon(Icons.calendar_today, color: Colors.blue[600]),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(plan.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                Text("${plan.durationDays} kun", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                "${plan.priceUzs} so'm",
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.green),
              ),
              const SizedBox(height: 4),
              SizedBox(
                height: 32,
                child: ElevatedButton(
                  onPressed: loading ? null : () => _purchasePlan(plan),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlue,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  child: loading
                    ? const SizedBox(width: 12, height: 12, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text("Sotib olish", style: TextStyle(color: Colors.white, fontSize: 12)),
                ),
              )
            ],
          )
        ],
      ),
    );
  }

  Widget _buildTrialSection() {
    bool loading = _loadingAction == 'trial';
    return Container(
      margin: const EdgeInsets.only(top: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF9C4), // Light yellow
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.amber[300]!),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const Icon(Icons.card_giftcard, color: Colors.amber),
              const SizedBox(width: 10),
              const Expanded(
                child: Text(
                  "Bir haftalik bepul sinov davri!",
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.amber),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          const Text("Premium imkoniyatlarni bepul sinab ko'ring (faqat bir marta)."),
          const SizedBox(height: 8),
          const Text(
             "Cheklov: AI modulidan 5 marta foydalanish mumkin.", 
             style: TextStyle(fontSize: 12, color: Colors.grey)
          ),
          const SizedBox(height: 15),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: loading ? null : () {
                showDialog(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: const Text("Tasdiqlash"),
                    content: const Text(
                      "Ushbu imkoniyatdan faqat bir marta foydalana olasiz. Davom etasizmi?"
                    ),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Yo'q")),
                      ElevatedButton(
                        onPressed: () {
                          Navigator.pop(ctx);
                          _activateTrial();
                        },
                        child: const Text("Ha, boshlash"),
                      )
                    ],
                  )
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.amber,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: loading
                ? const CircularProgressIndicator(color: Colors.white)
                : const Text("Hozir boshlash", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildFeatureItem(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(color: Colors.green[50], shape: BoxShape.circle),
            child: Icon(icon, color: Colors.green, size: 20),
          ),
          const SizedBox(width: 15),
          Text(text, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
