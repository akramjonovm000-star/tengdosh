import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import '../../../../core/localization/app_dictionary.dart';
import 'package:talabahamkor_mobile/core/theme/app_theme.dart';
import 'package:cached_network_image/cached_network_image.dart';

class StudentRatingScreen extends StatefulWidget {
  final String roleType;
  const StudentRatingScreen({super.key, required this.roleType});

  @override
  State<StudentRatingScreen> createState() => _StudentRatingScreenState();
}

class _StudentRatingScreenState extends State<StudentRatingScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  dynamic _target;
  int? _selectedRating;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _loadTarget();
  }

  Future<void> _loadTarget() async {
    final targets = await _dataService.getRatingTargets(widget.roleType);
    if (mounted) {
      setState(() {
        if (targets.isNotEmpty) {
          _target = targets.first;
        }
        _isLoading = false;
      });
    }
  }

  Future<void> _submit() async {
    if (_selectedRating == null || _target == null) return;

    setState(() => _isSubmitting = true);
    final result = await _dataService.submitRating(
      ratedPersonId: _target['staff_id'],
      roleType: widget.roleType,
      rating: _selectedRating!,
    );

    if (mounted) {
      setState(() => _isSubmitting = false);
      if (result['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Bahoyingiz qabul qilindi'),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Xatolik yuz berdi'),
            backgroundColor: Colors.red,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(AppDictionary.tr(context, 'lbl_rate_your_tutor')),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _target == null
              ? const _EmptyTargetView()
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      const SizedBox(height: 20),
                      _buildTutorCard(),
                      const SizedBox(height: 48),
                      Text(
                        AppDictionary.tr(context, 'lbl_rate_your_tutor'),
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        AppDictionary.tr(context, 'lbl_rating_select_hint'),
                        style: TextStyle(color: Colors.grey[600], fontSize: 14),
                      ),
                      const SizedBox(height: 32),
                      _buildRatingSelector(),
                      const SizedBox(height: 48),
                      _buildSubmitButton(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildTutorCard() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          CircleAvatar(
            radius: 60,
            backgroundColor: Colors.blue[50],
            backgroundImage: _target['image_url'] != null
                ? CachedNetworkImageProvider(_target['image_url'])
                : null,
            child: _target['image_url'] == null
                ? const Icon(Icons.person_rounded, size: 60, color: Colors.blue)
                : null,
          ),
          const SizedBox(height: 24),
          Text(
            _target['full_name'] ?? 'Noma\'lum',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.blue[50],
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              _target['role_name'] ?? 'Tyutor',
              style: TextStyle(color: Colors.blue[700], fontWeight: FontWeight.w600, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRatingSelector() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: List.generate(5, (index) {
        final rating = index + 1;
        final isSelected = _selectedRating == rating;

        return GestureDetector(
          onTap: () => setState(() => _selectedRating = rating),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            width: 55,
            height: 55,
            decoration: BoxDecoration(
              color: isSelected ? Colors.blue : Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isSelected ? Colors.blue : Colors.grey[300]!,
                width: 2,
              ),
              boxShadow: isSelected
                  ? [BoxShadow(color: Colors.blue.withOpacity(0.3), blurRadius: 10, offset: const Offset(0, 4))]
                  : [],
            ),
            child: Center(
              child: Text(
                rating.toString(),
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: isSelected ? Colors.white : Colors.black87,
                ),
              ),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildSubmitButton() {
    final isEnabled = _selectedRating != null && !_isSubmitting;

    return SizedBox(
      width: double.infinity,
      height: 60,
      child: ElevatedButton(
        onPressed: isEnabled ? _submit : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: isEnabled ? Colors.blue : Colors.grey[300],
          foregroundColor: Colors.white,
          disabledBackgroundColor: Colors.grey[300],
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          elevation: isEnabled ? 4 : 0,
          shadowColor: Colors.blue.withOpacity(0.4),
        ),
        child: _isSubmitting
            ? const SizedBox(
                height: 24,
                width: 24,
                child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
              )
            : Text(
                AppDictionary.tr(context, 'lbl_tutor_rating'),
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
      ),
    );
  }
}

class _EmptyTargetView extends StatelessWidget {
  const _EmptyTargetView();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.person_off_rounded, size: 80, color: Colors.grey[300]),
            const SizedBox(height: 24),
            Text(
              AppDictionary.tr(context, 'msg_no_rating_targets'),
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(
              AppDictionary.tr(context, 'msg_rating_unavailable'),
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: Text(AppDictionary.tr(context, 'btn_back')),
            ),
          ],
        ),
      ),
    );
  }
}
