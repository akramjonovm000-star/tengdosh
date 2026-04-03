import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme/app_theme.dart';
import '../../core/localization/app_dictionary.dart';
import '../../core/services/data_service.dart';

class AddAccommodationScreen extends StatefulWidget {
  const AddAccommodationScreen({super.key});

  @override
  State<AddAccommodationScreen> createState() => _AddAccommodationScreenState();
}

class _AddAccommodationScreenState extends State<AddAccommodationScreen> {
  final _formKey = GlobalKey<FormState>();
  final DataService _dataService = DataService();
  
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _addressController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  final TextEditingController _priceController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _telegramController = TextEditingController();

  bool _isLoading = false;
  int? _createdId;

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final result = await _dataService.createAccommodationListing({
        'title': _titleController.text,
        'description': _descriptionController.text,
        'price': _priceController.text,
        'address': _addressController.text,
        'contact_phone': _phoneController.text,
        'telegram_username': _telegramController.text.replaceAll('@', ''),
      });

      if (result['success'] == true) {
        setState(() {
          _createdId = result['id'];
          _isLoading = false;
        });
        _showSuccessDialog();
      } else {
        throw Exception(result['message'] ?? "Xatolik yuz berdi");
      }
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
      );
    }
  }

  void _showSuccessDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text("Muvaffaqiyatli! ✅"),
        content: const Text(
            "E'loningiz yaratildi. Endi turarjoy rasmlarini yuklash uchun Telegram botga o'tishingiz kerak."),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
              _openTelegram();
            },
            child: const Text("Telegramga o'tish 🚀"),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
              Navigator.pop(context); // Go back to listings
            },
            child: const Text("Keyinroq"),
          ),
        ],
      ),
    );
  }

  Future<void> _openTelegram() async {
    if (_createdId == null) return;
    
    // Deep link structure: https://t.me/talabahamkorbot?start=add_housing_{id}
    final url = Uri.parse("https://t.me/talabahamkorbot?start=add_housing_$_createdId");
    
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Telegram ochilmadi")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(AppDictionary.tr(context, 'module_accommodation_add')),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      backgroundColor: AppTheme.backgroundWhite,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.purple))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _buildTextField(
                      controller: _titleController,
                      label: "E'lon sarlavhasi (masalan: Kvartira sherik kerak)",
                      hint: "Qisqa va aniq sarlavha",
                    ),
                    const SizedBox(height: 16),
                    _buildTextField(
                      controller: _addressController,
                      label: "Manzil",
                      hint: "Tuman, mahalla, ko'cha...",
                      icon: Icons.location_on_rounded,
                    ),
                    const SizedBox(height: 16),
                    _buildTextField(
                      controller: _priceController,
                      label: "Narxi",
                      hint: "Masalan: 100\$ yoki 800.000 so'm",
                      icon: Icons.payments_rounded,
                    ),
                    const SizedBox(height: 16),
                    _buildTextField(
                      controller: _descriptionController,
                      label: "Tavsif",
                      hint: "Turarjoy haqida batafsil ma'lumot bering...",
                      maxLines: 4,
                    ),
                    const SizedBox(height: 24),
                    const Text(
                      "Bog'lanish uchun ma'lumotlar:",
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 12),
                    _buildTextField(
                      controller: _phoneController,
                      label: "Telefon raqam",
                      hint: "+998 90 123 45 67",
                      icon: Icons.phone_rounded,
                      keyboardType: TextInputType.phone,
                    ),
                    const SizedBox(height: 16),
                    _buildTextField(
                      controller: _telegramController,
                      label: "Telegram username",
                      hint: "@username",
                      icon: Icons.send_rounded,
                    ),
                    const SizedBox(height: 32),
                    ElevatedButton(
                      onPressed: _submitForm,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.purple,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: const Text(
                        "Saqlash va Rasm yuklashga o'tish",
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(height: 40),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required String hint,
    IconData? icon,
    int maxLines = 1,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          maxLines: maxLines,
          keyboardType: keyboardType,
          validator: (v) => (v == null || v.isEmpty) ? "To'ldirish shart" : null,
          decoration: InputDecoration(
            hintText: hint,
            prefixIcon: icon != null ? Icon(icon, color: Colors.purple, size: 20) : null,
            filled: true,
            fillColor: Colors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey[300]!),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey[200]!),
            ),
          ),
        ),
      ],
    );
  }
}
