import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../services/community_service.dart';

class EditPostSheet extends StatefulWidget {
  final String postId;
  final String initialContent;

  const EditPostSheet({
    super.key,
    required this.postId,
    required this.initialContent,
  });

  @override
  State<EditPostSheet> createState() => _EditPostSheetState();
}

class _EditPostSheetState extends State<EditPostSheet> {
  late TextEditingController _titleController;
  late TextEditingController _contentController;
  final FocusNode _contentFocusNode = FocusNode(); // Track Focus
  
  bool _isLoading = false;
  bool _hasChanges = false;
  bool _isFocused = false; // For Blue Border
  String? _originalTitle;
  String? _originalBody;

  @override
  void initState() {
    super.initState();
    _parseInitialContent();
    _titleController = TextEditingController(text: _originalTitle);
    _contentController = TextEditingController(text: _originalBody);

    _titleController.addListener(_checkForChanges);
    _contentController.addListener(_checkForChanges);
    
    // Listen to focus changes
    _contentFocusNode.addListener(() {
      setState(() {
        _isFocused = _contentFocusNode.hasFocus;
      });
    });
  }

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _contentFocusNode.dispose();
    super.dispose();
  }

  void _parseInitialContent() {
    // 1. Try Markdown Parsing
    final RegExp titleRegex = RegExp(r'^\*\*(.*?)\*\*\n+(.*)', multiLine: true, dotAll: true);
    final match = titleRegex.firstMatch(widget.initialContent);

    if (match != null) {
      _originalTitle = match.group(1)?.trim() ?? "";
      _originalBody = match.group(2)?.trim() ?? "";
    } else {
      // 2. Fallback: Legacy Split
      final lines = widget.initialContent.split('\n');
      if (lines.length > 1) {
        _originalTitle = lines.first.trim();
        _originalBody = lines.sublist(1).join('\n').trim();
      } else {
        _originalTitle = "";
        _originalBody = widget.initialContent;
      }
    }
  }

  void _checkForChanges() {
    final newTitle = _titleController.text.trim();
    final newBody = _contentController.text.trim();
    final hasChanges = newTitle != _originalTitle || newBody != _originalBody;
    
    if (_hasChanges != hasChanges) {
      setState(() => _hasChanges = hasChanges);
    }
  }

  Future<void> _handleSave() async {
    if (!_hasChanges) return;
    
    // Validate
    if (_contentController.text.trim().isEmpty) {
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Iltimos, matn yozing!")));
       return;
    }

    // No Loading Indicator needed for Fire & Forget
    final newTitle = _titleController.text.trim();
    final newBody = _contentController.text.trim();
    
    // Enforce Markdown Format
    String finalContent = newBody;
    if (newTitle.isNotEmpty) {
      finalContent = "**$newTitle**\n\n$newBody";
    }

    // FIRE & FORGET: Return immediately with new content
    // The parent widget (PostCard) will handle the background API call.
    Navigator.pop(context, finalContent);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Post saqlanmoqda... ⏳"), duration: Duration(milliseconds: 1000)),
    );
  }

  Future<bool> _onWillPop() async {
    if (!_hasChanges) return true;

    final shouldPop = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Saqlanmagan o'zgarishlar"),
        content: const Text("Chiqib ketsangiz o'zgarishlaringiz yo'qoladi."),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text("Qolish", style: TextStyle(color: Colors.blue)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("Chiqish", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    return shouldPop ?? false;
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvoked: (didPop) async {
        if (didPop) return;
        final shouldPop = await _onWillPop();
        if (shouldPop && context.mounted) Navigator.pop(context);
      },
      child: Container(
        height: MediaQuery.of(context).size.height * 0.9, 
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () async {
                       final shouldPop = await _onWillPop();
                       if (shouldPop && context.mounted) Navigator.pop(context);
                    },
                  ),
                  const Text("Postni Tahrirlash", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(width: 48), 
                ],
              ),
            ),
            const Divider(height: 1),
            
            // Content
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    // Title Field (Plain)
                    TextField(
                      controller: _titleController,
                      decoration: const InputDecoration(
                        hintText: "Sarlavha (Ixtiyoriy)",
                        border: InputBorder.none,
                        hintStyle: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.grey),
                        contentPadding: EdgeInsets.symmetric(horizontal: 12),
                      ),
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const Divider(),
                    const SizedBox(height: 8),
                    
                    // Body Field (With Blue Border & Menu Button)
                    Expanded(
                      child: Stack(
                        children: [
                          Container(
                            decoration: BoxDecoration(
                              // Animated Border Color
                              border: Border.all(
                                color: _isFocused ? AppTheme.primaryBlue : Colors.grey[300]!,
                                width: _isFocused ? 2 : 1
                              ),
                              borderRadius: BorderRadius.circular(16) // Rounded Corners
                            ),
                            child: TextField(
                              controller: _contentController,
                              focusNode: _contentFocusNode,
                              maxLines: null, // Infinite
                              expands: true,
                              textAlignVertical: TextAlignVertical.top,
                              decoration: const InputDecoration(
                                hintText: "Bu yerga yozing...",
                                border: InputBorder.none,
                                contentPadding: EdgeInsets.fromLTRB(16, 16, 16, 60), // Space for button at bottom
                              ),
                              style: const TextStyle(fontSize: 16),
                            ),
                          ),
                          
                          // Floating Menu Button (Bottom Left)
                          Positioned(
                            bottom: 12,
                            left: 12,
                            child: Material(
                              color: Colors.white,
                              elevation: 2,
                              shape: const CircleBorder(),
                              child: InkWell(
                                onTap: () {
                                  // Placeholder for formatting menu
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text("Formatlash menyusi (Tez orada)"), duration: Duration(seconds: 1)),
                                  );
                                },
                                borderRadius: BorderRadius.circular(50),
                                child: Container(
                                  width: 40,
                                  height: 40,
                                  alignment: Alignment.center,
                                  child: const Icon(Icons.menu, color: Colors.black54),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // Bottom Save Button
            SafeArea(
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border(top: BorderSide(color: Colors.grey[200]!)),
                ),
                child: SizedBox(
                   height: 50,
                   child: ElevatedButton(
                    onPressed: (_hasChanges && !_isLoading) ? _handleSave : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryBlue,
                      disabledBackgroundColor: Colors.grey[300],
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: _isLoading 
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text("SAQLASH", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
