import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/services/data_service.dart';

class CreateTutorRatingSurveyScreen extends StatefulWidget {
  final Map<String, dynamic>? initialData;
  const CreateTutorRatingSurveyScreen({super.key, this.initialData});

  @override
  State<CreateTutorRatingSurveyScreen> createState() => _CreateTutorRatingSurveyScreenState();
}

class _CreateTutorRatingSurveyScreenState extends State<CreateTutorRatingSurveyScreen> {
  final DataService _dataService = DataService();
  late final TextEditingController _titleController;
  late final TextEditingController _descriptionController;
  
  DateTime _startDate = DateTime.now();
  DateTime _endDate = DateTime.now().add(const Duration(days: 7));
  
  bool _isLoading = false;
  bool _isEditing = false;

  @override
  void initState() {
    super.initState();
    _isEditing = widget.initialData != null;
    _titleController = TextEditingController(text: widget.initialData?['title'] ?? "");
    _descriptionController = TextEditingController(text: widget.initialData?['description'] ?? "");
    
    if (_isEditing) {
      final data = widget.initialData!;
      if (data['start_at'] != null) _startDate = DateTime.parse(data['start_at']);
      if (data['end_at'] != null) _endDate = DateTime.parse(data['end_at']);
    }

    _titleController.addListener(_updateState);
    _descriptionController.addListener(_updateState);
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  void _updateState() {
    setState(() {}); // Rebuild to update button color
  }

  bool get _isFormValid {
    return _titleController.text.isNotEmpty && _descriptionController.text.isNotEmpty;
  }

  Future<void> _selectDateTime(BuildContext context, bool isStart) async {
    final DateTime? pickedDate = await showDatePicker(
      context: context,
      initialDate: isStart ? _startDate : _endDate,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    
    if (pickedDate != null && mounted) {
      final TimeOfDay? pickedTime = await showTimePicker(
        context: context,
        initialTime: TimeOfDay.fromDateTime(isStart ? _startDate : _endDate),
      );
      
      if (pickedTime != null) {
        setState(() {
          final newDateTime = DateTime(
            pickedDate.year,
            pickedDate.month,
            pickedDate.day,
            pickedTime.hour,
            pickedTime.minute,
          );
          if (isStart) {
            _startDate = newDateTime;
          } else {
            _endDate = newDateTime;
          }
        });
      }
    }
  }

  Future<void> _submit() async {
    if (!_isFormValid) return;

    setState(() => _isLoading = true);

    final surveyData = {
      "title": _titleController.text,
      "description": _descriptionController.text,
      "role_type": "tutor",
      "type": "tutor_rating", // specific type for tutor rating with no questions
      "is_active": true,
      "start_at": DateFormat('yyyy-MM-dd HH:mm:ss').format(_startDate),
      "end_at": DateFormat('yyyy-MM-dd HH:mm:ss').format(_endDate),
      "questions": [], // No custom questions for tutor rating
    };

    final Map<String, dynamic> result;
    if (_isEditing) {
      result = await _dataService.updateManagementSurvey(widget.initialData!['id'], surveyData);
    } else {
      result = await _dataService.createManagementSurvey(surveyData);
    }

    if (mounted) {
      setState(() => _isLoading = false);
      if (result['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(_isEditing ? "Tyutor ratingi yangilandi" : "Tyutor ratingi muvaffaqiyatli yaratildi"), 
          backgroundColor: Colors.green
        ));
        Navigator.pop(context, true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(result['message'] ?? "Xatolik yuz berdi"), 
          backgroundColor: Colors.red
        ));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final dateFormat = DateFormat('dd.MM.yyyy HH:mm');

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(_isEditing ? "Tyutor ratingini tahrirlash" : "Yangi tyutor ratingi"),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildSectionCard(
                    title: "So'rovnoma ma'lumotlari",
                    child: Column(
                      children: [
                        TextField(
                          controller: _titleController,
                          decoration: InputDecoration(
                            labelText: "So'rovnoma nomi",
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                            filled: true,
                            fillColor: Colors.grey[50],
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _descriptionController,
                          maxLines: 4,
                          decoration: InputDecoration(
                            labelText: "So'rovnoma tavsifi",
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                            filled: true,
                            fillColor: Colors.grey[50],
                          ),
                        ),
                        const SizedBox(height: 20),
                        Row(
                          children: [
                            Expanded(
                              child: _buildDateTimePicker(
                                label: "Boshlanish vaqti",
                                value: dateFormat.format(_startDate),
                                onTap: () => _selectDateTime(context, true),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: _buildDateTimePicker(
                                label: "Tugash vaqti",
                                value: dateFormat.format(_endDate),
                                onTap: () => _selectDateTime(context, false),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 48),
                ],
              ),
            ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: SizedBox(
            height: 56,
            child: ElevatedButton(
              onPressed: _isFormValid && !_isLoading ? _submit : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: _isFormValid ? Colors.blue : Colors.grey[400],
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                elevation: _isFormValid ? 4 : 0,
              ),
              child: _isLoading
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text("Saqlash", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSectionCard({required String title, required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }

  Widget _buildDateTimePicker({required String label, required String value, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey[300]!),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
            const SizedBox(height: 4),
            Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
