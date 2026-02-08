
import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import 'package:provider/provider.dart';
import '../../../../core/providers/auth_provider.dart';

class AiChatScreen extends StatefulWidget {
  final String? initialQuery;
  final bool isGrantAnalysis;
  final bool isSentimentAnalysis;

  const AiChatScreen({
    super.key, 
    this.initialQuery, 
    this.isGrantAnalysis = false,
    this.isSentimentAnalysis = false,
  });

  @override
  State<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends State<AiChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final DataService _dataService = DataService();
  
  List<Map<String, String>> _messages = [];
  bool _isLoading = true;
  bool _isTyping = false;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final history = await _dataService.getAiHistory();
    if (history != null && history.isNotEmpty) {
      setState(() {
        _messages = history.map<Map<String, String>>((m) => {
          "role": m['role'].toString(),
          "content": m['content'].toString()
        }).toList();
        _isLoading = false;
      });
      _scrollToBottom();
    } else {
      setState(() {
         // Default greeting if no history
         _messages = [
           {"role": "assistant", "content": "Assalomu alaykum! Men TalabaHamkor AI yordamchisiman. Sizga qanday yordam bera olaman?"}
         ];
         _isLoading = false;
      });
    }

    // Auto-send initial query if provided
    if (widget.isGrantAnalysis) {
       Future.delayed(const Duration(milliseconds: 500), () {
           if (mounted) _sendGrantAnalysis();
       });
    } else if (widget.isSentimentAnalysis) {
       Future.delayed(const Duration(milliseconds: 500), () {
           if (mounted) _sendSentimentAnalysis();
       });
    } else if (widget.initialQuery != null && widget.initialQuery!.isNotEmpty) {
       // Allow UI to render first
       Future.delayed(const Duration(milliseconds: 500), () {
           if (mounted) _sendMessage(customText: widget.initialQuery);
       });
    }
  }

  Future<void> _sendGrantAnalysis() async {
    setState(() {
      _messages.add({"role": "user", "content": "🎓 Grant taqsimotini hisoblash"});
      _isTyping = true;
    });
    _scrollToBottom();
    
    try {
      final response = await _dataService.predictGrant();
      if (mounted) {
        setState(() {
          _isTyping = false;
          if (response != null) {
            _messages.add({"role": "assistant", "content": response});
          } else {
             _messages.add({"role": "assistant", "content": "⚠️ Kechirasiz, Grant tahlilini tayyorlashda xatolik yuz berdi."});
          }
        });
        _scrollToBottom();
      }
    } catch (e) {
      _handleError(e);
    }
  }

  Future<void> _sendSentimentAnalysis() async {
    setState(() {
      _messages.add({"role": "user", "content": "📊 Talabalar kayfiyati tahlili"});
      _isTyping = true;
    });
    _scrollToBottom();
    
    try {
      final response = await _dataService.predictSentiment();
      if (mounted) {
        setState(() {
          _isTyping = false;
          if (response != null) {
            _messages.add({"role": "assistant", "content": response});
          } else {
             _messages.add({"role": "assistant", "content": "⚠️ Kechirasiz, Tahlil qilishda xatolik yuz berdi."});
          }
        });
        _scrollToBottom();
      }
    } catch (e) {
      _handleError(e);
    }
  }

  void _handleError(dynamic e) {
      if (e.toString().contains("PREMIUM_REQUIRED")) {
        if (mounted) {
          Provider.of<AuthProvider>(context, listen: false).loadUser();
          Navigator.pop(context);
        }
      } else {
        if (mounted) setState(() => _isTyping = false);
      }
  }

  Future<void> _clearHistory() async {
    final success = await _dataService.clearAiHistory();
    if (success) {
      setState(() {
        _messages = [
           {"role": "assistant", "content": "Chat tozalandi. Yangi suhbat boshlashingiz mumkin."}
        ];
      });
    }
  }

  void _sendMessage({String? customText}) async {
    final text = customText ?? _controller.text.trim();
    if (text.isEmpty) return;
    
    _controller.clear();
    setState(() {
      _messages.add({"role": "user", "content": text});
      _isTyping = true;
    });
    _scrollToBottom();
    
    // Call API (Backend now saves history automatically)
    try {
      final response = await _dataService.sendAiMessage(text);
      if (mounted) {
        setState(() {
          _isTyping = false;
          if (response != null) {
            _messages.add({"role": "assistant", "content": response});
          } else {
             _messages.add({"role": "assistant", "content": "⚠️ Kechirasiz, xatolik yuz berdi."});
          }
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (e.toString().contains("PREMIUM_REQUIRED")) {
        if (mounted) {
          // Force refresh profile status
          await Provider.of<AuthProvider>(context, listen: false).loadUser();
          // The parent screen (AiScreen) will lock once it rebuilds.
          // We should pop back to the dashboard/AIScreen
          Navigator.pop(context);
        }
      } else {
        if (mounted) setState(() => _isTyping = false);
      }
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent, 
          duration: const Duration(milliseconds: 300), 
          curve: Curves.easeOut
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("AI Chat", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
            onPressed: () {
               showDialog(
                 context: context,
                 builder: (ctx) => AlertDialog(
                   title: const Text("Yangi Suhbat"),
                   content: const Text("Chat tarixini o'chirib, yangi suhbat boshlamoqchimisiz?"),
                   actions: [
                     TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Bekor qilish")),
                     TextButton(
                       onPressed: () {
                         Navigator.pop(ctx);
                         _clearHistory();
                       }, 
                       child: const Text("Ha, tozalash", style: TextStyle(color: Colors.red)),
                     ),
                   ],
                 )
               );
            },
          )
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading 
            ? const Center(child: CircularProgressIndicator())
            : ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length + (_isTyping ? 1 : 0),
              itemBuilder: (context, index) {
                if (index == _messages.length) {
                   return _buildTypingIndicator();
                }
                final msg = _messages[index];
                final isUser = msg['role'] == 'user';
                return _buildMessageBubble(msg['content']!, isUser);
              },
            ),
          ),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(String text, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isUser ? AppTheme.primaryBlue : Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: isUser ? const Radius.circular(16) : const Radius.circular(4),
            bottomRight: isUser ? const Radius.circular(4) : const Radius.circular(16),
          ),
          boxShadow: [
             BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, 2))
          ]
        ),
        child: Text(
          text,
          style: TextStyle(
            color: isUser ? Colors.white : Colors.black87,
            fontSize: 15,
            height: 1.4
          ),
        ),
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Align(
       alignment: Alignment.centerLeft,
       child: Container(
         margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
         padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
         decoration: BoxDecoration(
           color: Colors.white,
           borderRadius: BorderRadius.circular(16),
         ),
         child: Row(
           mainAxisSize: MainAxisSize.min,
           children: [
             SizedBox(
               width: 14, height: 14, 
               child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primaryBlue.withOpacity(0.6))
             ),
             const SizedBox(width: 8),
             const Text("Yozmoqda...", style: TextStyle(color: Colors.grey, fontSize: 12)),
           ],
         ),
       ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Color(0xFFEEEEEE))),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                decoration: InputDecoration(
                  hintText: "Xabar yozing...",
                  hintStyle: const TextStyle(color: Colors.grey),
                  filled: true,
                  fillColor: AppTheme.backgroundWhite,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                ),
                textCapitalization: TextCapitalization.sentences,
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
            const SizedBox(width: 12),
            GestureDetector(
              onTap: _sendMessage,
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: const BoxDecoration(
                  color: AppTheme.primaryBlue,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.send, color: Colors.white, size: 20),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
