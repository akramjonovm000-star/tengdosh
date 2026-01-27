import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

class CommentInput extends StatefulWidget {
  final Function(String) onSend;
  final bool isSending;
  final String? replyToName;
  final VoidCallback? onCancelReply;
  final FocusNode? focusNode;

  const CommentInput({
    super.key, 
    required this.onSend, 
    this.isSending = false,
    this.replyToName,
    this.onCancelReply,
    this.focusNode,
  });

  @override
  State<CommentInput> createState() => _CommentInputState();
}

class _CommentInputState extends State<CommentInput> {
  final TextEditingController _controller = TextEditingController();

  void _handleSend() {
    final text = _controller.text.trim();
    if (text.isNotEmpty) {
      widget.onSend(text);
      _controller.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.replyToName != null) // This now acts as the full label e.g. "Javob berilmoqda: @username"
           Container(
            color: const Color(0xFFF5F7FA),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                const Icon(Icons.reply, size: 20, color: AppTheme.primaryBlue),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    widget.replyToName!, // Display exactly what is passed
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue, fontSize: 12),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 18),
                  onPressed: widget.onCancelReply,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                )
              ],
            ),
          ),
          
        Container(
          padding: EdgeInsets.only(
            left: 16, 
            right: 16, 
            top: 8, 
            bottom: MediaQuery.of(context).viewInsets.bottom + 16
          ),
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border(top: BorderSide(color: Colors.grey[200]!)),
            boxShadow: [
              BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, -2))
            ]
          ),
          child: Row(
            children: [
               CircleAvatar(
                 backgroundColor: Colors.grey[200],
                 radius: 18,
                 child: const Icon(Icons.person, color: Colors.grey, size: 20),
               ),
               const SizedBox(width: 12),
               
               Expanded(
                 child: Container(
                   padding: const EdgeInsets.symmetric(horizontal: 16),
                   decoration: BoxDecoration(
                     color: const Color(0xFFF5F5F5),
                     borderRadius: BorderRadius.circular(24),
                   ),
                   child: TextField(
                     controller: _controller,
                     focusNode: widget.focusNode,
                     decoration: const InputDecoration(
                       hintText: "Fikringizni yozing...",
                       border: InputBorder.none,
                       contentPadding: EdgeInsets.symmetric(vertical: 10),
                       isDense: true,
                     ),
                     minLines: 1,
                     maxLines: 4,
                   ),
                 ),
               ),
               
               const SizedBox(width: 8),
               
               IconButton(
                 onPressed: widget.isSending ? null : _handleSend,
                 icon: widget.isSending 
                   ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                   : const CircleAvatar(
                       backgroundColor: AppTheme.primaryBlue,
                       radius: 20,
                       child: Icon(Icons.send_rounded, color: Colors.white, size: 18),
                     ),
               )
            ],
          ),
        ),
      ],
    );
  }
}
