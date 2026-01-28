import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';

class CreatePostScreen extends StatefulWidget {
  final String? initialScope;
  const CreatePostScreen({super.key, this.initialScope});

  @override
  State<CreatePostScreen> createState() => _CreatePostScreenState();
}

class _CreatePostScreenState extends State<CreatePostScreen> {
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  final List<TextEditingController> _pollControllers = [
    TextEditingController(),
    TextEditingController()
  ];

  late String _selectedScope; // initialized in initState
  bool _isPoll = false;

  @override
  void initState() {
    super.initState();
    _selectedScope = widget.initialScope ?? 'university';
  }

  void _addPollOption() {
    setState(() {
      _pollControllers.add(TextEditingController());
    });
  }

  void _removePollOption(int index) {
    if (_pollControllers.length > 2) {
      setState(() {
        _pollControllers.removeAt(index);
      });
    }
  }



  void _publish() async {
    final title = _titleController.text.trim();
    final content = _contentController.text.trim();

    if (content.isEmpty) {
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Iltimos, matn yozing!")));
       return;
    }

    // Enforce Markdown Format for Title
    String finalContent = content;
    if (title.isNotEmpty) {
      finalContent = "**$title**\n\n$content";
    }

    // Improve local Optimistic Post
    final newPost = Post(
      id: "temp_${DateTime.now().millisecondsSinceEpoch}",
      authorId: "0",
      authorName: "Siz", 
      authorUsername: "me",
      authorAvatar: "",
      authorRole: "student",
      content: finalContent,
      timeAgo: "Hozirgina",
      createdAt: DateTime.now(),
      scope: _selectedScope,
      isMine: true,
      pollOptions: _isPoll ? _pollControllers.map((c) => c.text).where((t) => t.isNotEmpty).toList() : null,
      pollVotes: _isPoll ? List.filled(_pollControllers.where((c) => c.text.isNotEmpty).length, 0) : null,
    );

    try {
      await CommunityService().createPost(newPost); // Call Service

      if (!mounted) return;
      
      FocusScope.of(context).unfocus();
      // Removed success toast as requested
      
      Navigator.pop(context, true); // Return TRUE to refresh feed
    } catch (e) {
      if (mounted) {
        String errorMsg = "Xatolik yuz berdi";
        if (e.toString().contains("400")) {
           if (_selectedScope == 'faculty') errorMsg = "Sizga fakultet biriktirilmagan!";
           else if (_selectedScope == 'specialty') errorMsg = "Sizga yo'nalish biriktirilmagan!";
        }
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(errorMsg), backgroundColor: Colors.red));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("Post Yaratish", style: TextStyle(color: Colors.black)),
        elevation: 0,
        backgroundColor: Colors.white,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          TextButton(
            onPressed: _publish, 
            child: const Text("CHOP ETISH", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16))
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Scope Selector
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8)
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedScope,
                  isExpanded: true,
                  items: const [
                    DropdownMenuItem(value: 'university', child: Text("🏛️  Universitet (Barchaga)")),
                    DropdownMenuItem(value: 'faculty', child: Text("🎓  Fakultet (Dekanat)")),
                    DropdownMenuItem(value: 'specialty', child: Text("🎯  Yo'nalish (Guruhga)")),
                  ],
                  onChanged: (val) => setState(() => _selectedScope = val!),
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            // Title
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(
                hintText: "Sarlavha (Ixtiyoriy)",
                border: InputBorder.none,
                hintStyle: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey),
              ),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const Divider(),
            
            // Body
            TextField(
              controller: _contentController,
              maxLines: null,
              minLines: 5,
              decoration: const InputDecoration(
                hintText: "Bu yerga yozing...",
                border: InputBorder.none,
              ),
            ),
            
            const SizedBox(height: 20),
            
            // Poll Toggle
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text("So'rovnoma qo'shish", style: TextStyle(fontWeight: FontWeight.bold)),
              value: _isPoll,
              activeColor: AppTheme.primaryBlue,
              onChanged: (val) => setState(() => _isPoll = val),
            ),

            // Poll Options
            if (_isPoll) ...[
              const SizedBox(height: 8),
              ...List.generate(_pollControllers.length, (index) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _pollControllers[index],
                          decoration: InputDecoration(
                            hintText: "Variant ${index + 1}",
                            filled: true,
                            fillColor: Colors.grey[50],
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 0)
                          ),
                        ),
                      ),
                      if (_pollControllers.length > 2)
                        IconButton(
                          icon: const Icon(Icons.remove_circle_outline, color: Colors.red),
                          onPressed: () => _removePollOption(index),
                        )
                    ],
                  ),
                );
              }),
              TextButton.icon(
                onPressed: _addPollOption,
                icon: const Icon(Icons.add),
                label: const Text("Variant qo'shish"),
              )
            ]
          ],
        ),
      ),
    );
  }
}
