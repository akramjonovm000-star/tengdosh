import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/models/student.dart';
import '../../../../core/services/data_service.dart';
import '../../../../core/utils/role_mapper.dart';
import 'subscription_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  // Username State
  bool _isEditingUsername = false;
  final TextEditingController _usernameController = TextEditingController();
  String? _usernameError;
  bool _isCheckingUsername = false;
  bool _isSavingUsername = false;

  void _onUsernameChanged(String value) async {
    setState(() => _usernameError = null);

    if (value.length < 2) return;

    // Don't check if it's my own current username
    final current = Provider.of<AuthProvider>(context, listen: false).currentUser?.username;
    if (value == current) return;

    setState(() => _isCheckingUsername = true);

    try {
      final available = await Provider.of<AuthProvider>(context, listen: false).checkUsernameAvailability(value);

      if (mounted) {
        setState(() {
          if (!available) {
            _usernameError = "Bu username allaqachon olingan";
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _usernameError = "Tekshirishda xatolik";
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isCheckingUsername = false);
      }
    }
  }

  Future<void> _saveUsername() async {
    final value = _usernameController.text.trim();
    if (value.length < 2 || value.length > 25) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Username 2-25 belgi bo'lishi kerak")));
      return;
    }
    if (_usernameError != null) return;

    setState(() => _isSavingUsername = true);
    final result = await Provider.of<AuthProvider>(context, listen: false).updateUsername(value);
    setState(() => _isSavingUsername = false);

    if (result['success'] == true) {
      setState(() {
        _isEditingUsername = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Username saqlandi!")));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message'] ?? "Xatolik")));
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final student = auth.currentUser;

    if (student == null) {
      return const Center(child: Text("Ma'lumot topilmadi"));
    }

    // Initialize controller only once if not editing or empty
    if (!_isEditingUsername && _usernameController.text.isEmpty && student.username != null) {
      _usernameController.text = student.username!;
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const SizedBox(height: 20),
          // 1. Avatar & Name
          Center(
            child: Column(
              children: [
                GestureDetector(
                  onTap: () => _showImageOptions(context),
                  child: Stack(
                    children: [
                      Container(
                        width: 100,
                        height: 100,
                        decoration: BoxDecoration(
                          color: AppTheme.backgroundWhite,
                          shape: BoxShape.circle,
                          border: Border.all(color: AppTheme.primaryBlue, width: 3),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.1),
                              blurRadius: 10,
                              offset: const Offset(0, 5),
                            )
                          ],
                        ),
                        child: ClipOval(
                          child: student.imageUrl != null && student.imageUrl!.isNotEmpty
                              ? CachedNetworkImage(
                                  imageUrl: student.imageUrl!,
                                  fit: BoxFit.cover,
                                  placeholder: (context, url) => Container(color: Colors.grey[100]),
                                  errorWidget: (context, url, err) => _buildInitials(student.fullName),
                                )
                              : _buildInitials(student.fullName),
                        ),
                      ),
                      Positioned(
                        bottom: 0,
                        right: 0,
                        child: Container(
                          padding: const EdgeInsets.all(6),
                          decoration: const BoxDecoration(
                            color: AppTheme.primaryBlue,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.edit, color: Colors.white, size: 16),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Text.rich(
                    TextSpan(
                      children: [
                        TextSpan(text: student.fullName),
                        if (student.isPremium) ...[
                          WidgetSpan(
                            alignment: PlaceholderAlignment.middle,
                            child: Padding(
                              padding: const EdgeInsets.only(left: 8),
                              child: GestureDetector(
                                onTap: () => _showBadgeSelector(context),
                                child: student.customBadge != null
                                    ? Text(student.customBadge!, style: const TextStyle(fontSize: 24))
                                    : const Icon(Icons.verified, color: Colors.blue, size: 24),
                              ),
                            ),
                          ),
                          if (student.customBadge == null)
                            WidgetSpan(
                              alignment: PlaceholderAlignment.middle,
                              child: Padding(
                                padding: const EdgeInsets.only(left: 4),
                                child: GestureDetector(
                                  onTap: () => _showBadgeSelector(context),
                                  child: Icon(Icons.edit, size: 14, color: Colors.grey[400]),
                                ),
                              ),
                            ),
                        ],
                      ],
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textBlack,
                        height: 1.3,
                      ),
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Text(
                  "ID: ${student.hemisLogin}",
                  style: TextStyle(fontSize: 14, color: Colors.grey[600], fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.grey[300]!)
                  ),
                  child: Text(
                    RoleMapper.getLabel(student.role),
                    style: TextStyle(fontSize: 12, color: Colors.grey[700], fontWeight: FontWeight.bold),
                  ),
                ),

                  // --- USERNAME SECTION ---
                const SizedBox(height: 12),
                if (_isEditingUsername)
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      SizedBox(
                        width: 220, // Increased width slightly
                        child: TextField(
                          controller: _usernameController,
                          textAlign: TextAlign.start, // Changed from center to start
                          style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 16, color: AppTheme.textBlack), // Reduced bold
                          decoration: InputDecoration(
                            isDense: true,
                            contentPadding: const EdgeInsets.symmetric(vertical: 8),
                            hintText: "Foydalanuvchi nomi",
                            hintStyle: TextStyle(color: Colors.grey.withOpacity(0.6), fontWeight: FontWeight.normal), // Lighter hint
                            prefixIcon: const Padding(
                              padding: EdgeInsets.only(left: 0, top: 10, bottom: 10, right: 4), // Align better
                              child: Text("@", style: TextStyle(color: Colors.grey, fontSize: 16, fontWeight: FontWeight.bold)), // Suffix-like prefix
                            ),
                            prefixIconConstraints: const BoxConstraints(minWidth: 0, minHeight: 0),
                            border: const UnderlineInputBorder(borderSide: BorderSide(color: AppTheme.primaryBlue)),
                            enabledBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Colors.grey)),
                            focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: AppTheme.primaryBlue, width: 2)),
                            errorStyle: const TextStyle(height: 0, fontSize: 0),
                          ),
                          onChanged: _onUsernameChanged,
                        ),
                      ),

                      if (_usernameError != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Text(
                            _usernameError!,
                            style: const TextStyle(color: Colors.redAccent, fontSize: 12, fontWeight: FontWeight.w500),
                          ),
                        ),

                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          InkWell(
                            onTap: () => setState(() => _isEditingUsername = false),
                            borderRadius: BorderRadius.circular(20),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                              child: Text("Bekor qilish", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                            ),
                          ),
                          const SizedBox(width: 8),
                          if (_isSavingUsername)
                             const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                          else
                             InkWell(
                               onTap: _saveUsername,
                               borderRadius: BorderRadius.circular(20),
                               child: const Padding(
                                 padding: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                 child: Text("Saqlash", style: TextStyle(color: AppTheme.primaryBlue, fontWeight: FontWeight.bold, fontSize: 13)),
                               ),
                             ),
                        ],
                      )
                    ],
                  )
                else
                  GestureDetector(
                    onTap: () => setState(() => _isEditingUsername = true),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            student.username != null ? "@${student.username}" : "Username o'rnatish",
                            style: TextStyle(
                              color: student.username != null ? Colors.grey[800] : AppTheme.primaryBlue,
                              fontWeight: student.username != null ? FontWeight.w500 : FontWeight.bold,
                              fontSize: 15
                            ),
                          ),
                          const SizedBox(width: 6),
                          Icon(Icons.edit, size: 14, color: Colors.grey[400])
                        ],
                      ),
                    ),
                  ),

              ],
            ),
          ),


          const SizedBox(height: 20),

          // --- PREMIUM BANNER ---
          GestureDetector(
            onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const SubscriptionScreen()));
            },
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: student.isPremium 
                    ? const LinearGradient(colors: [Color(0xFFFFD700), Color(0xFFFFA500)]) // Gold Gradient
                    : const LinearGradient(colors: [Color(0xFF6A11CB), Color(0xFF2575FC)]), // Blue Gradient
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: (student.isPremium ? Colors.orange : const Color(0xFF2575FC)).withOpacity(0.3), 
                    blurRadius: 10, 
                    offset: const Offset(0, 5)
                  )
                ],
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: const BoxDecoration(color: Colors.white24, shape: BoxShape.circle),
                    child: Icon(
                      student.isPremium ? Icons.verified_rounded : Icons.workspace_premium, 
                      color: student.isPremium ? Colors.white : Colors.amber, 
                      size: 24
                    ),
                  ),
                  const SizedBox(width: 15),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                         Text(
                           student.isPremium ? "Premium foydalanuvchi" : "Premium Obuna", 
                           style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)
                         ),
                         Text(
                           student.isPremium ? "Sizda barcha imkoniyatlar ochiq" : "Barcha imkoniyatlarni oching", 
                           style: const TextStyle(color: Colors.white70, fontSize: 12)
                         ),
                      ],
                    ),
                  ),
                  const Icon(Icons.arrow_forward_ios_rounded, color: Colors.white, size: 16)
                ],
              ),
            ),
          ),

          const SizedBox(height: 20),

          // 2. Info Cards (Bot Style List)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
               BoxShadow(color: Colors.grey.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4)),
              ],
            ),
            child: Column(
              children: [
                _buildInfoRow(Icons.account_balance_rounded, "Universitet", student.universityName ?? "Topilmadi"),
                const Divider(height: 1),
                _buildInfoRow(Icons.school_rounded, "Fakultet", student.facultyName ?? "-"),
                const Divider(height: 1),
                _buildInfoRow(Icons.menu_book_rounded, "Yo'nalish", student.specialtyName ?? "-"),
                const Divider(height: 1),
                _buildInfoRow(
                  Icons.groups_rounded,
                  "Guruh",
                  (student.groupNumber != null && student.groupNumber!.length > 5)
                      ? student.groupNumber!.substring(0, 5)
                      : (student.groupNumber ?? "-"),
                ),
                const Divider(height: 1),
                _buildInfoRow(Icons.calendar_today_rounded, "Semestr", student.semesterName ?? "-"),
              ],
            ),
          ),

          const SizedBox(height: 30),

          // 3. Logout Button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => _logout(context),
              icon: const Icon(Icons.logout_rounded, color: Colors.white),
              label: const Text("Tizimdan Chiqish", style: TextStyle(color: Colors.white, fontSize: 16)),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.redAccent,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                elevation: 0,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInitials(String name) {
    String initials = "ST";
    if (name.isNotEmpty) {
      initials = name.substring(0, 1).toUpperCase();
      if (name.contains(" ")) {
        initials += name.split(" ")[1].substring(0, 1).toUpperCase();
      }
    }
    return Center(
      child: Text(
        initials,
        style: const TextStyle(
          fontSize: 32,
          fontWeight: FontWeight.bold,
          color: AppTheme.primaryBlue
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppTheme.primaryBlue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: AppTheme.primaryBlue, size: 20),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                const SizedBox(height: 4),
                Text(value, style: const TextStyle(color: AppTheme.textBlack, fontSize: 16, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _logout(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Chiqish"),
        content: const Text("Rostdan ham tizimdan chiqmoqchimisiz?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Yo'q"),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              Provider.of<AuthProvider>(context, listen: false).logout();
            },
            child: const Text("Ha", style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  // 4. Image Picker and Compression
  void _pickAndUploadImage(BuildContext context) async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);

    if (image != null) {
      // Show loading
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Rasm tayyorlanmoqda...")),
      );

      File originalFile = File(image.path);
      File? compressedFile;

      try {
        // Compress to < 50KB
        compressedFile = await _compressImage(originalFile);
      } catch (e) {
        print("Compression error: $e");
        compressedFile = originalFile; // Fallback
      }

      if (compressedFile == null) {
         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Rasmni qayta ishlashda xatolik")));
         return;
      }

      // Upload
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Rasm yuklanmoqda...")));
      
      final DataService dataService = DataService();
      final newUrl = await dataService.uploadAvatar(compressedFile);

      if (newUrl != null && context.mounted) {
         // Update Provider
         Provider.of<AuthProvider>(context, listen: false).updateProfileImage(newUrl);

         ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(content: Text("Rasm muvaffaqiyatli o'zgartirildi!")),
         );
      } else if (context.mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(content: Text("Rasm yuklashda xatolik!")),
         );
      }
      
      // Cleanup temp
      /* 
      if (compressedFile.path != originalFile.path) {
        try { await compressedFile.delete(); } catch (_) {}
      }
      */
    }
  }

  Future<File?> _compressImage(File file) async {
    final dir = await getTemporaryDirectory();
    final targetPath = "${dir.path}/${DateTime.now().millisecondsSinceEpoch}.jpg";

    var result = await FlutterImageCompress.compressAndGetFile(
      file.absolute.path,
      targetPath,
      quality: 80,
      minWidth: 800,
      minHeight: 800,
    );

    if (result == null) return null;
    
    // Check size (target 50KB = 51200 bytes)
    int size = await result.length();
    int loops = 0;
    int quality = 80;

    File finalFile = File(result.path);

    while (size > 51200 && loops < 5) {
      loops++;
      quality -= 15;
      if (quality < 5) quality = 5;

      final newTargetPath = "${dir.path}/${DateTime.now().millisecondsSinceEpoch}_$loops.jpg";
      
      var newResult = await FlutterImageCompress.compressAndGetFile(
        file.absolute.path, // Always compress source to avoid artifacts accumulation? Or re-compress? Better source.
        newTargetPath,
        quality: quality,
        minWidth: 600, // Reduce resolution too
        minHeight: 600,
      );

      if (newResult != null) {
        finalFile = File(newResult.path);
        size = await finalFile.length();
      } else {
        break; 
      }
      
      if (quality <= 5) break; 
    }
    
    print("Final Image Size: ${(size / 1024).toStringAsFixed(2)} KB");
    return finalFile;
  }

  void _showImageOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_library, color: AppTheme.primaryBlue),
              title: const Text("Galereyadan tanlash"),
              onTap: () {
                Navigator.pop(ctx);
                _pickAndUploadImage(context);
              },
            ),
            const SizedBox(height: 10),
          ],
        ),
      )
    );
  }

  void _showBadgeSelector(BuildContext context) {
    // Popular Emojis
    final List<String> emojis = [
      "🔥", "⚡", "🚀", "🎓", "👑", "💎", "🌟", "🇺🇿", 
      "💻", "🧠", "📚", "💼", "🎨", "⚽", "🎵", "🕶️", 
      "🦁", "🐯", "🤖", "🍕", "🦾", "🧬", "🧸", "🇺🇸"
    ];

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        padding: const EdgeInsets.all(20),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Status Belgisini Tanlang", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 15),
            Wrap(
              spacing: 15,
              runSpacing: 15,
              children: emojis.map((emoji) => GestureDetector(
                onTap: () async {
                  Navigator.pop(ctx);
                  
                  // Optimistic UI Update first? No, await API.
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Belgi o'zgartirilmoqda...")));
                  
                  final success = await DataService().updateBadge(emoji);
                  
                  if (success && context.mounted) {
                    final auth = Provider.of<AuthProvider>(context, listen: false);
                    if (auth.currentUser != null) {
                       var json = auth.currentUser!.toJson();
                       json['custom_badge'] = emoji;
                       await auth.updateUser(json);
                    }
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Belgi o'zgartirildi: $emoji")));
                  } else if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Xatolik yuz berdi")));
                  }
                },
                child: Container(
                  width: 50,
                  height: 50,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.grey[300]!)
                  ),
                  child: Text(emoji, style: const TextStyle(fontSize: 24)),
                ),
              )).toList(),
            ),
            const SizedBox(height: 10),
          ],
        ),
      )
    );
  }
}
