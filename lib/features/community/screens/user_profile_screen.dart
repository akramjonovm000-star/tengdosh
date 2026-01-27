import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/auth_service.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';
import '../services/chat_service.dart'; // NEW
import '../widgets/post_card.dart';
import '../../../../core/utils/role_mapper.dart';
import '../../../../core/models/student.dart'; 
import 'chat_detail_screen.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'dart:async'; // NEW
import 'user_list_screen.dart'; // NEW

class UserProfileScreen extends StatefulWidget {
  final String authorName;
  final String authorId; // NEW
  final String authorUsername;
  final String authorAvatar;
  final String authorRole;
  final bool authorIsPremium; // NEW

  const UserProfileScreen({
    super.key,
    required this.authorName,
    required this.authorId, // NEW
    required this.authorUsername,
    required this.authorAvatar,
    required this.authorRole,
    this.authorIsPremium = false, // NEW
  });

  @override
  State<UserProfileScreen> createState() => _UserProfileScreenState();
}

class _UserProfileScreenState extends State<UserProfileScreen> {
  final CommunityService _service = CommunityService();
  final ChatService _chatService = ChatService(); // NEW

  int _postCount = 0;
  int _repostCount = 0; // NEW
  bool _isLoading = true;
  List<Post> _posts = [];
  List<Post> _reposts = []; // NEW

  bool _isMe = false;
  
  // Follow System
  bool _isFollowing = false;
  int _followersCount = 0;
  int _followingCount = 0;
  Timer? _refreshTimer;

  // Username Editing State
  bool _isEditingUsername = false;
  TextEditingController _usernameController = TextEditingController();
  String? _usernameError;
  bool _isCheckingUsername = false;
  String? _currentUsername;

  @override
  void initState() {
    super.initState();
    _loadUserPosts();
    _checkIfMe();
    _initFollowSystem();
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  void _initFollowSystem() {
    // Initial Load
    _checkFollowStatus();
    _loadStats();
    
    // Periodic Refresh (30s)
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      if (mounted) _loadStats();
    });
  }

  Future<void> _checkFollowStatus() async {
    if (widget.authorId == "0") return;
    final status = await _service.checkSubscription(widget.authorId);
    if (mounted) setState(() => _isFollowing = status);
  }
  
  Future<void> _loadStats() async {
     if (widget.authorId == "0") return;
     final stats = await _service.getProfileStats(widget.authorId);
     if (mounted) {
       setState(() {
         _followersCount = stats['followers'] ?? 0;
         _followingCount = stats['following'] ?? 0;
       });
     }
  }

  Future<void> _toggleFollow() async {
    // Optimistic Update
    setState(() {
      _isFollowing = !_isFollowing;
      if (_isFollowing) {
        _followersCount++;
      } else {
        _followersCount--;
      }
    });

    final output = await _service.toggleSubscription(widget.authorId);
    if (output != null && output.containsKey('subscribed')) {
      if (mounted) {
        setState(() {
          _isFollowing = output['subscribed'];
          _followersCount = output['followers_count']; 
        });
      }
    } else {
      // Revert if failed
       _checkFollowStatus();
       _loadStats();
    }
  }
  
  Future<void> _checkIfMe() async {
    final me = await AuthService().getSavedUser();
    if (me != null && mounted) {
      // Priority: Check by ID
      if (widget.authorId != "0" && widget.authorId.isNotEmpty) {
        if (me.id.toString() == widget.authorId) {
          _setMe(me);
          return;
        }
      }
      
      // Fallback: Check by username if ID failed or missing
      if (me.username != null && widget.authorUsername.isNotEmpty) {
         if (me.username == widget.authorUsername) {
           _setMe(me);
           return;
         }
      }

      // Last Resort: Check by Name
      if (me.fullName == widget.authorName) { 
        _setMe(me);
      }
    }
  }

  void _setMe(Student me) {
    setState(() {
      _isMe = true;
      _currentUsername = me.username;
      _usernameController.text = me.username ?? "";
    });
  }
  
  void _onUsernameChanged(String value) async {
    // Debounce or immediate check?
    // Let's do simple check first.
    setState(() => _usernameError = null);
    
    if (value.length < 2) {
       return; // Wait for more chars
    }
    
    setState(() => _isCheckingUsername = true);
    final available = await AuthService().checkUsernameAvailability(value);
    
    if (mounted) {
      setState(() {
        _isCheckingUsername = false;
        if (!available && value != _currentUsername) {
           _usernameError = "Bu username allaqachon olingan";
        }
      });
    }
  }
  
  Future<void> _saveUsername() async {
     final value = _usernameController.text.trim();
     if (value.length < 2 || value.length > 25) {
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Username 2-25 belgi bo'lishi kerak")));
       return;
     }
     
     if (_usernameError != null) return;
     
     setState(() => _isLoading = true);
     final result = await AuthService().setUsername(value);
     setState(() => _isLoading = false);
     
     if (result['success'] == true) {
       setState(() {
         _currentUsername = result['username'];
         _isEditingUsername = false;
       });
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Username saqlandi!")));
     } else {
       ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message'] ?? "Xatolik")));
     }
  }

  Future<void> _loadUserPosts() async {
    try {
      // Fetch from all scopes to ensure we get every post
      final univPosts = await _service.getPosts(scope: "university");
      final facPosts = await _service.getPosts(scope: "faculty");
      final specPosts = await _service.getPosts(scope: "specialty");

      // Combine and Dedup
      final all = [...univPosts, ...facPosts, ...specPosts];
      final uniqueMap = { for (var p in all) p.id : p }; // Dedup by ID
      
      final userPosts = uniqueMap.values.where((p) {
        // Fallback: If ID is "0" or invalid, try name match. 
        // But Search passes specific ID, so ID match is primary.
        if (p.authorId != "0" && p.authorId == widget.authorId) return true;
        return p.authorName == widget.authorName;
      }).toList();
      
      // Sort newest first
      userPosts.sort((a, b) => b.id.compareTo(a.id));
      
      // NEW: Load Reposts
      final reposts = await _service.getRepostedPosts(widget.authorId);

      if (mounted) {
        setState(() {
          _posts = userPosts;
          _reposts = reposts; // NEW
          _postCount = userPosts.length;
          _repostCount = reposts.length; // NEW
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _handleDelete(String postId) {
    setState(() {
      _posts.removeWhere((p) => p.id == postId);
      _postCount = _posts.length;
    });
  }

  @override
  Widget build(BuildContext context) {
    // Name Splitting Logic
    final nameParts = widget.authorName.split(" ");
    String line1 = widget.authorName;
    String line2 = "";
    
    if (nameParts.length > 2) {
      line1 = "${nameParts[0]} ${nameParts[1]}";
      line2 = nameParts.sublist(2).join(" ");
    }

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.white,
        appBar: AppBar(
          title: Text(widget.authorUsername, style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          backgroundColor: Colors.white,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.black),
            onPressed: () => Navigator.pop(context),
          ),
          centerTitle: true,
        ),
        body: NestedScrollView(
          headerSliverBuilder: (context, innerBoxIsScrolled) => [
            SliverToBoxAdapter(
              child: Column(
                children: [
                  const SizedBox(height: 20),
                  // Avatar
                  Center(
                    child: CircleAvatar(
                      radius: 40,
                      backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                      child: widget.authorAvatar.isNotEmpty
                          ? ClipOval(
                              child: CachedNetworkImage(
                                imageUrl: widget.authorAvatar,
                                width: 80,
                                height: 80,
                                fit: BoxFit.cover,
                                placeholder: (context, url) => const Icon(Icons.person, size: 40, color: Colors.grey),
                                errorWidget: (context, url, error) => Text(widget.authorName.isNotEmpty ? widget.authorName[0] : "?", style: const TextStyle(fontSize: 32, color: AppTheme.primaryBlue, fontWeight: FontWeight.bold)),
                              ),
                            )
                          : Text(widget.authorName.isNotEmpty ? widget.authorName[0] : "?", style: const TextStyle(fontSize: 32, color: AppTheme.primaryBlue, fontWeight: FontWeight.bold)),
                    ),
                  ),
                  const SizedBox(height: 16),
                   
                  // Name
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(line1, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                      if (widget.authorIsPremium) ...[
                        const SizedBox(width: 6),
                        const Icon(Icons.verified, color: Colors.blue, size: 20),
                      ]
                    ],
                  ),
                  if (line2.isNotEmpty)
                    Text(line2, style: TextStyle(color: Colors.grey[600], fontSize: 14)),
                   
                  const SizedBox(height: 4),
                  // Role
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryBlue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(4)
                    ),
                    child: Text(RoleMapper.getLabel(widget.authorRole), style: const TextStyle(color: AppTheme.primaryBlue, fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                   
                  // Username Section (Only if Me)
                  if (_isMe) ...[
                     const SizedBox(height: 16),
                     if (_isEditingUsername)
                        SizedBox( // Changed from Container to SizedBox for width constraint
                          width: 200,
                          child: Column(
                            children: [
                              TextField(
                                controller: _usernameController,
                                textAlign: TextAlign.center,
                                decoration: InputDecoration(
                                  prefixText: "@",
                                  hintText: "username",
                                  isDense: true,
                                  contentPadding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                                  border: UnderlineInputBorder(
                                    borderSide: BorderSide(color: _usernameError != null ? Colors.red : AppTheme.primaryBlue)
                                  ),
                                  focusedBorder: UnderlineInputBorder(
                                    borderSide: BorderSide(color: _usernameError != null ? Colors.red : AppTheme.primaryBlue, width: 2)
                                  ),
                                ),
                                onChanged: _onUsernameChanged,
                              ),
                              if (_usernameError != null)
                                Padding(
                                  padding: const EdgeInsets.only(top: 4),
                                  child: Text(
                                    _usernameError!,
                                    style: const TextStyle(color: Colors.red, fontSize: 11),
                                  ),
                                ),
                              const SizedBox(height: 8),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  TextButton(
                                    onPressed: () => setState(() => _isEditingUsername = false),
                                    child: const Text("Bekor qilish", style: TextStyle(color: Colors.grey, fontSize: 12))
                                  ),
                                  TextButton(
                                    onPressed: _saveUsername,
                                    child: const Text("Saqlash", style: TextStyle(color: AppTheme.primaryBlue, fontSize: 12, fontWeight: FontWeight.bold))
                                  ),
                                ],
                              )
                            ],
                          ),
                        )
                     else
                        GestureDetector(
                          onTap: () {
                             if (_currentUsername == null) {
                                setState(() => _isEditingUsername = true);
                             }
                          },
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                _currentUsername != null ? "@$_currentUsername" : "Username o'rnatish",
                                style: TextStyle(
                                  color: _currentUsername != null ? Colors.black54 : AppTheme.primaryBlue,
                                  fontSize: 14,
                                  fontWeight: _currentUsername != null ? FontWeight.normal : FontWeight.bold
                                ),
                              ),
                              if (_currentUsername != null)
                                IconButton(
                                  icon: const Icon(Icons.edit, size: 14, color: Colors.grey),
                                  onPressed: () => setState(() => _isEditingUsername = true),
                                  padding: EdgeInsets.zero,
                                  constraints: const BoxConstraints(),
                                  splashRadius: 16,
                                )
                            ],
                          )
                        ),
                  ],
                   
                  const SizedBox(height: 16), // This SizedBox is before Dynamic Stats
                  
                  // Dynamic Stats
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                       _buildStat("Postlar", "$_postCount"), 
                       _buildStat("Repostlar", "$_repostCount"), 
                       GestureDetector(
                         onTap: () {
                            Navigator.push(context, MaterialPageRoute(builder: (_) => UserListScreen(
                              userId: widget.authorId, 
                              type: UserListType.followers
                            )));
                         },
                         child: _buildStat("Kuzatuvchilar", "$_followersCount")
                       ), 
                       GestureDetector(
                         onTap: () {
                            Navigator.push(context, MaterialPageRoute(builder: (_) => UserListScreen(
                              userId: widget.authorId, 
                              type: UserListType.following
                            )));
                         },
                         child: _buildStat("Obuna", "$_followingCount")
                       ),
                    ],
                  ),
                  
                  const SizedBox(height: 24),
                  
                  // Actions
                  if (_isMe)
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () {
                              // Trigger username edit or open settings
                              setState(() => _isEditingUsername = true);
                            },
                            style: OutlinedButton.styleFrom(
                              backgroundColor: Colors.grey[100],
                              side: BorderSide.none,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))
                            ),
                            child: const Text("Profilni tahrirlash", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
                          ),
                        ),
                        const SizedBox(width: 8),
                        // Settings / Share Icon
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.grey[100],
                            borderRadius: BorderRadius.circular(10)
                          ),
                          child: IconButton(
                            icon: const Icon(Icons.share, color: Colors.black),
                            onPressed: () {
                              // Share profile logic placeholder
                            },
                          ),
                        )
                      ],
                    )
                  else
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        ElevatedButton(
                          onPressed: _toggleFollow,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: _isFollowing ? Colors.red[50] : AppTheme.primaryBlue,
                            foregroundColor: _isFollowing ? Colors.red : Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                              side: _isFollowing ? BorderSide(color: Colors.red) : BorderSide.none
                            ),
                            padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 12),
                            elevation: 0,
                          ),
                          child: Text(_isFollowing ? "Obunani o'chirish" : "Kuzatish", style: const TextStyle(fontWeight: FontWeight.bold)),
                        ),
                        const SizedBox(width: 12),
                        OutlinedButton(
                          onPressed: () async {
                            final chat = await _chatService.startChat(widget.authorId);
                            if (chat != null && mounted) {
                              Navigator.push(context, MaterialPageRoute(builder: (_) => ChatDetailScreen(chat: chat)));
                            } else if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Chatni ochib bo'lmadi")));
                            }
                          },
                          style: OutlinedButton.styleFrom(
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            side: const BorderSide(color: Colors.black12),
                            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                          ),
                          child: const Text("Xabar yozish", style: TextStyle(color: Colors.black)),
                        )
                      ],
                    ),
                  
                  const SizedBox(height: 20),
                ],
              ),
            ),
            SliverPersistentHeader(
              delegate: _SliverAppBarDelegate(
                const TabBar(
                  labelColor: Colors.black,
                  unselectedLabelColor: Colors.grey,
                  indicatorColor: Colors.black,
                  indicatorSize: TabBarIndicatorSize.tab,
                  tabs: [
                    Tab(icon: Icon(Icons.grid_on)), // User Posts
                    Tab(icon: Icon(Icons.repeat)),  // Reposts
                  ],
                ),
              ),
              pinned: true,
            ),
          ],
          body: TabBarView(
            children: [
              // 1. User Posts
              _isLoading 
                 ? const Center(child: CircularProgressIndicator()) 
                 : _posts.isEmpty 
                    ? const Center(child: Text("Postlar yo'q", style: TextStyle(color: Colors.grey)))
                    : ListView.builder(
                        padding: EdgeInsets.zero,
                        itemCount: _posts.length,
                        itemBuilder: (ctx, i) => PostCard(
                          post: _posts[i], 
                          onDelete: () => _handleDelete(_posts[i].id),
                          onContentChanged: (newContent) {
                            setState(() {
                               _posts[i] = _posts[i].copyWith(content: newContent);
                            });
                          },
                        ),
                      ),
                      
              // 2. Reposts (Placeholder)
              // 2. Reposts
              _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _reposts.isEmpty
                      ? const Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.repeat, size: 48, color: Colors.grey),
                              SizedBox(height: 8),
                              Text("Repostlar yo'q", style: TextStyle(color: Colors.grey)),
                            ],
                          ),
                        )
                      : ListView.builder(
                          padding: EdgeInsets.zero,
                          itemCount: _reposts.length,
                          itemBuilder: (ctx, i) => PostCard(
                            post: _reposts[i],
                            // onDelete: _handleDeleteRepost... logic if needed
                          ),
                        ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStat(String label, String value) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        Text(label, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
      ],
    );
  }
}

class _SliverAppBarDelegate extends SliverPersistentHeaderDelegate {
  final TabBar _tabBar;

  _SliverAppBarDelegate(this._tabBar);

  @override
  double get minExtent => _tabBar.preferredSize.height;
  @override
  double get maxExtent => _tabBar.preferredSize.height;

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return Container(
      color: Colors.white,
      child: _tabBar,
    );
  }

  @override
  bool shouldRebuild(_SliverAppBarDelegate oldDelegate) {
    return false;
  }
}
