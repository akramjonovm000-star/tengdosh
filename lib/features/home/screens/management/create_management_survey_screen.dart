import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/services/data_service.dart';

class CreateManagementSurveyScreen extends StatefulWidget {
  final Map<String, dynamic>? initialData;
  const CreateManagementSurveyScreen({super.key, this.initialData});

  @override
  State<CreateManagementSurveyScreen> createState() => _CreateManagementSurveyScreenState();
}

class _CreateManagementSurveyScreenState extends State<CreateManagementSurveyScreen> {
  final DataService _dataService = DataService();
  late final TextEditingController _titleController;
  
  DateTime _startDate = DateTime.now();
  DateTime _endDate = DateTime.now().add(const Duration(days: 7));
  
  List<QuestionData> _questions = [];

  bool _isLoading = false;
  bool _isEditing = false;
  bool _isActive = false; // Default to Draft (False)

  @override
  void initState() {
    super.initState();
    _isEditing = widget.initialData != null;
    _titleController = TextEditingController(text: widget.initialData?['title'] ?? "Tyutorlarni baholash");
    
    if (_isEditing) {
      final data = widget.initialData!;
      if (data['start_at'] != null) _startDate = DateTime.parse(data['start_at']);
      if (data['end_at'] != null) _endDate = DateTime.parse(data['end_at']);
      _isActive = data['is_active'] ?? false;
      
      final List<dynamic>? questionsJson = data['questions'];
      if (questionsJson != null) {
        _questions = questionsJson.map((q) => QuestionData(
          text: q['text'] ?? "",
          options: List<String>.from(q['options'] ?? []),
        )).toList();
      }
    }

    if (_questions.isEmpty) {
      _questions.add(QuestionData(text: "", options: ["A'lo", "Yaxshi", "Qoniqarli", "Yomon"]));
    }
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

  void _addQuestion() {
    setState(() {
      _questions.add(QuestionData(text: "", options: ["A'lo", "Yaxshi", "Qoniqarli", "Yomon"]));
    });
  }

  void _removeQuestion(int index) {
    if (_questions.length > 1) {
      setState(() {
        _questions.removeAt(index);
      });
    }
  }

  Future<void> _submit() async {
    if (_titleController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Sarlavha kiriting")));
      return;
    }

    for (var q in _questions) {
      if (q.text.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Barcha savollarni to'ldiring")));
        return;
      }
    }

    setState(() => _isLoading = true);

    final surveyData = {
      if (_isEditing) "id": widget.initialData!['id'],
      "title": _titleController.text,
      "role_type": "tutor",
      "type": "rating",
      "is_active": _isActive,
      "start_at": DateFormat('yyyy-MM-dd HH:mm:ss').format(_startDate),
      "end_at": DateFormat('yyyy-MM-dd HH:mm:ss').format(_endDate),
      "questions": _questions.map((q) => {
        "text": q.text,
        "options": q.options.map((o) => {"text": o}).toList(),
      }).toList(),
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
          content: Text(_isEditing ? "So'rovnoma yangilandi" : "So'rovnoma muvaffaqiyatli yaratildi"), 
          backgroundColor: Colors.green
        ));
        Navigator.pop(context, true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message'] ?? "Xatolik yuz berdi"), backgroundColor: Colors.red));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dateFormat = DateFormat('dd.MM.yyyy HH:mm');

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text(_isEditing ? "So'rovnomani tahrirlash" : "Yangi so'rovnoma"),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        actions: [
          if (!_isLoading)
            TextButton(
              onPressed: _submit,
              child: const Text("Saqlash", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ),
        ],
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title Card
                  _buildSectionCard(
                    title: "Umumiy ma'lumotlar",
                    child: Column(
                      children: [
                        TextField(
                          controller: _titleController,
                          decoration: InputDecoration(
                            labelText: "So'rovnoma sarlavhasi",
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
                        const SizedBox(height: 20),
                        SwitchListTile(
                          title: const Text("Aktivlashtirish", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          subtitle: Text(_isActive ? "So'rovnoma hozir faol" : "So'rovnoma qoralama (draft) holatida saqlanadi", style: const TextStyle(fontSize: 11)),
                          value: _isActive,
                          onChanged: (val) => setState(() => _isActive = val),
                          activeColor: Colors.blue,
                          contentPadding: EdgeInsets.zero,
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text("Savollar ro'yxati", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      IconButton(
                        onPressed: _addQuestion,
                        icon: const Icon(Icons.add_circle_outline, color: Colors.blue, size: 28),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Questions List
                  ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _questions.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 16),
                    itemBuilder: (context, index) {
                      return _buildQuestionCard(index);
                    },
                  ),
                  const SizedBox(height: 40),
                ],
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

  Widget _buildQuestionCard(int index) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 14,
                backgroundColor: Colors.blue[50],
                child: Text("${index + 1}", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.blue)),
              ),
              const SizedBox(width: 12),
              const Expanded(child: Text("Savol matni", style: TextStyle(fontWeight: FontWeight.bold))),
              if (_questions.length > 1)
                IconButton(
                  onPressed: () => _removeQuestion(index),
                  icon: const Icon(Icons.delete_outline, color: Colors.red, size: 20),
                  constraints: const BoxConstraints(),
                  padding: EdgeInsets.zero,
                ),
            ],
          ),
          const SizedBox(height: 12),
          TextField(
            onChanged: (val) => _questions[index].text = val,
            decoration: InputDecoration(
              hintText: "Masalan: Tyutorning o'z ishiga mas'uliyati qanday?",
              border: UnderlineInputBorder(borderSide: BorderSide(color: Colors.grey[300]!)),
            ),
          ),
          const SizedBox(height: 20),
          const Text("Javob variantlari", style: TextStyle(fontSize: 13, color: Colors.grey, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: _questions[index].options.map((opt) {
              return Chip(
                label: Text(opt, style: const TextStyle(fontSize: 12)),
                backgroundColor: Colors.blue[50],
                deleteIcon: const Icon(Icons.close, size: 14),
                onDeleted: () {
                  setState(() {
                    _questions[index].options.remove(opt);
                  });
                },
              );
            }).toList(),
          ),
          TextButton.icon(
            onPressed: () => _showAddOptionDialog(index),
            icon: const Icon(Icons.add, size: 16),
            label: const Text("Variant qo'shish", style: TextStyle(fontSize: 13)),
          ),
        ],
      ),
    );
  }

  void _showAddOptionDialog(int qIndex) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Yangi variant"),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(hintText: "Variant matni"),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Bekor qilish")),
          ElevatedButton(
            onPressed: () {
              if (controller.text.isNotEmpty) {
                setState(() {
                  _questions[qIndex].options.add(controller.text);
                });
                Navigator.pop(context);
              }
            },
            child: const Text("Qo'shish"),
          ),
        ],
      ),
    );
  }
}

class QuestionData {
  String text;
  List<String> options;
  QuestionData({required this.text, required this.options});
}
