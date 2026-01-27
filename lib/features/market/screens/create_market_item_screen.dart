import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../services/market_service.dart';

class CreateMarketItemScreen extends StatefulWidget {
  const CreateMarketItemScreen({super.key});

  @override
  State<CreateMarketItemScreen> createState() => _CreateMarketItemScreenState();
}

class _CreateMarketItemScreenState extends State<CreateMarketItemScreen> {
  final _formKey = GlobalKey<FormState>();
  final MarketService _marketService = MarketService();
  
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _descController = TextEditingController();
  final TextEditingController _priceController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _tgController = TextEditingController();
  final TextEditingController _imageUrlController = TextEditingController();

  String _selectedCategory = 'other';
  bool _isLoading = false;

  final Map<String, String> _categories = {
    'books': 'Kitoblar',
    'tech': 'Texnika',
    'housing': 'Kvartira',
    'jobs': 'Ish',
    'lost': 'Yo\'qolgan',
    'other': 'Boshqa',
  };

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);

    final data = {
      "title": _titleController.text.trim(),
      "description": _descController.text.trim(),
      "price": _priceController.text.trim().isEmpty ? null : _priceController.text.trim(),
      "category": _selectedCategory,
      "image_url": _imageUrlController.text.trim().isEmpty ? null : _imageUrlController.text.trim(),
      "contact_phone": _phoneController.text.trim().isEmpty ? null : _phoneController.text.trim(),
      "telegram_username": _tgController.text.trim().isEmpty ? null : _tgController.text.trim(),
    };

    final success = await _marketService.createItem(data);
    
    setState(() => _isLoading = false);

    if (success) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("E'lon muvaffaqiyatli qo'shildi!")));
        Navigator.pop(context, true);
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Xatolik yuz berdi.")));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("E'lon Qo'shish", style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildTextField("Sarlavha", _titleController, required: true),
              const SizedBox(height: 16),
              
              const Text("Kategoriya", style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: _selectedCategory,
                items: _categories.entries.map((e) => DropdownMenuItem(value: e.key, child: Text(e.value))).toList(),
                onChanged: (val) => setState(() => _selectedCategory = val!),
                decoration: InputDecoration(
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
              ),
              const SizedBox(height: 16),

              _buildTextField("Narxi (ixtiyoriy)", _priceController, hint: "Masalan: 50.000 so'm"),
              const SizedBox(height: 16),
              _buildTextField("Tavsif", _descController, maxLines: 5, required: true),
              const SizedBox(height: 16),
              
              _buildTextField("Rasm URL (ixtiyoriy)", _imageUrlController, hint: "https://..."),
              const SizedBox(height: 16),
              
              Row(
                children: [
                   Expanded(child: _buildTextField("Telefon (ixtiyoriy)", _phoneController)),
                   const SizedBox(width: 16),
                   Expanded(child: _buildTextField("Telegram (ixtiyoriy)", _tgController, hint: "@username")),
                ],
              ),
              
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryBlue,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isLoading 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text("E'lonni Joylash", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller, {int maxLines = 1, bool required = false, String? hint}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(required ? "$label *" : label, style: const TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          maxLines: maxLines,
          validator: required ? (v) => v == null || v.isEmpty ? "To'ldirish shart" : null : null,
          decoration: InputDecoration(
            hintText: hint,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          ),
        ),
      ],
    );
  }
}
