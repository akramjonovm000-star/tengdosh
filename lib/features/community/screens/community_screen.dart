import 'dart:async';
import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/community_models.dart';
import '../services/community_service.dart';
import '../widgets/post_card.dart';
import '../widgets/shimmer_post.dart';
import '../screens/create_post_screen.dart';
import 'chat_list_screen.dart';
import 'package:talabahamkor_mobile/features/community/services/chat_service.dart'; // NEW
import '../widgets/user_search_delegate.dart';

class CommunityScreen extends StatefulWidget {
  const CommunityScreen({super.key});

  @override
  State<CommunityScreen> createState() => _CommunityScreenState();
}

class _CommunityScreenState extends State<CommunityScreen> with SingleTickerProviderStateMixin {
  final CommunityService _service = CommunityService();
  final ChatService _chatService = ChatService(); // NEW
  late TabController _tabController;
  Timer? _pollTimer;
  int _unreadCount = 0; // NEW

  // State Management for Silent Updates
  final Map<String, List<Post>> _posts = {
    'university': [],
    'specialty': [],
    'faculty': [],
  };
  final Map<String, bool> _isLoading = {
    'university': true,
    'specialty': true,
    'faculty': true,
  };
  
  final Map<String, bool> _hasMore = {
    'university': true,
    'specialty': true,
    'faculty': true,
  };
  
  final Map<String, bool> _isFetchingMore = {
     'university': false,
     'specialty': false,
     'faculty': false,
  };

  final Map<String, ScrollController> _scrollControllers = {
     'university': ScrollController(),
     'specialty': ScrollController(),
     'faculty': ScrollController(),
  };

  final int _limit = 15;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this, initialIndex: 0);
    _tabController.addListener(_handleTabSelection);
    
    // Initial Load
    _loadAllScopes();
    
    // Setup Scroll Listeners
    _scrollControllers.forEach((scope, controller) {
       controller.addListener(() {
          if (controller.position.pixels >= controller.position.maxScrollExtent - 200) {
             if (_hasMore[scope] == true && _isFetchingMore[scope] == false && _isLoading[scope] == false) {
                _fetchMorePosts(scope);
             }
          }
       });
    });

    // Start Polling (Real-time Simulation)
    _startPolling();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _tabController.dispose();
    _scrollControllers.forEach((_, c) => c.dispose());
    super.dispose();
  }

  void _handleTabSelection() {
    if (_tabController.indexIsChanging) {
      setState(() {}); // Rebuild to show correct scope
      _fetchPosts(_getCurrentScope(), isSilent: false); // Force refresh on tab switch
    }
  }

  void _startPolling() {
    _pollTimer = Timer.periodic(const Duration(seconds: 15), (timer) {
      if (mounted) {
        // Refresh ONLY the active scope to save bandwidth
        _fetchPosts(_getCurrentScope(), isSilent: true);
        _fetchUnreadCount(); // NEW
      }
    });
  }

  Future<void> _fetchUnreadCount() async {
    try {
      final count = await _chatService.getTotalUnreadCount();
      if (mounted) {
        setState(() {
          _unreadCount = count;
        });
      }
    } catch (e) {
      debugPrint("Unread Count Error: $e");
    }
  }

  Future<void> _loadAllScopes() async {
    await Future.wait([
      _fetchPosts('university'),
      _fetchPosts('specialty'),
      _fetchPosts('faculty'),
    ]);
  }

  Future<void> _fetchPosts(String scope, {bool isSilent = false}) async {
    if (!isSilent) {
      setState(() {
        _isLoading[scope] = true;
      });
    }

    try {
      final newPosts = await _service.getPosts(scope: scope, skip: 0, limit: _limit);
      if (mounted) {
        setState(() {
          _posts[scope] = newPosts;
          _isLoading[scope] = false;
          _hasMore[scope] = newPosts.length >= _limit;
        });
      }
    } catch (e) {
      if (mounted && !isSilent) {
        setState(() {
          _isLoading[scope] = false;
        });
      }
      debugPrint("Polling Error: $e");
    }
  }

  Future<void> _fetchMorePosts(String scope) async {
     if (_isFetchingMore[scope] == true) return;
     
     setState(() => _isFetchingMore[scope] = true);
     
     try {
        final skip = _posts[scope]?.length ?? 0;
        final morePosts = await _service.getPosts(scope: scope, skip: skip, limit: _limit);
        
        if (mounted) {
           setState(() {
              _posts[scope]?.addAll(morePosts);
              _isFetchingMore[scope] = false;
              _hasMore[scope] = morePosts.length >= _limit;
           });
        }
     } catch (e) {
        if (mounted) setState(() => _isFetchingMore[scope] = false);
        debugPrint("Load More Error: $e");
     }
  }

  String _getCurrentScope() {
    final isManagement = context.read<AuthProvider>().isManagement;
    final index = _tabController.index;
    
    if (isManagement) {
      switch (index) {
        case 0: return 'university';
        case 1: return 'faculty';
        case 2: return 'specialty';
        default: return 'university';
      }
    } else {
      switch (index) {
        case 0: return 'specialty';
        case 1: return 'faculty';
        case 2: return 'university';
        default: return 'specialty';
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        backgroundColor: AppTheme.backgroundWhite,
        appBar: AppBar(
          title: const Text("Choyxona", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          backgroundColor: Colors.white,
          elevation: 0,
          centerTitle: false,
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(48),
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(12),
              ),
              child: Consumer<AuthProvider>(
                builder: (context, auth, _) {
                  final isManagement = auth.isManagement;
                  return TabBar(
                    controller: _tabController,
                    labelColor: Colors.black,
                    unselectedLabelColor: Colors.grey[600],
                    indicator: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(8),
                      boxShadow: [
                        BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 4, offset: const Offset(0, 1))
                      ]
                    ),
                    indicatorSize: TabBarIndicatorSize.tab,
                    labelPadding: EdgeInsets.zero,
                    tabs: isManagement 
                      ? const [
                          Tab(child: Text("Universitet", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13))),
                          Tab(child: Text("Fakultet", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13))),
                          Tab(child: Text("Yo'nalish", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13))),
                        ]
                      : const [
                          Tab(child: Text("Yo'nalish", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13))),
                          Tab(child: Text("Fakultet", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13))),
                          Tab(child: Text("Universitet", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13))),
                        ],
                  );
                }
              ),
            ),
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.search, color: Colors.black),
              onPressed: () {
                showSearch(context: context, delegate: UserSearchDelegate());
              },
            ),
             IconButton(
               icon: Stack(
                 children: [
                    const Icon(Icons.chat_bubble_outline_rounded, color: Colors.black),
                    if (_unreadCount > 0) // DYNAMIC
                      Positioned(
                        right: 0,
                        top: 0,
                        child: Container(
                          padding: const EdgeInsets.all(2), // Proper spacing
                          decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
                          constraints: const BoxConstraints(minWidth: 10, minHeight: 10),
                          child: Center(
                            child: Text(
                                "$_unreadCount", 
                                style: const TextStyle(color: Colors.white, fontSize: 7, fontWeight: FontWeight.bold)
                            ),
                          ),
                        ),
                      )
                 ],
               ),
               onPressed: () async {
                  await Navigator.push(context, MaterialPageRoute(builder: (_) => const ChatListScreen()));
                  _fetchUnreadCount(); // Immediate refresh when returning
               },
             ),
            const SizedBox(width: 8),
          ],
        ),
        body: Consumer<AuthProvider>(
          builder: (context, auth, _) {
            final isManagement = auth.isManagement;
            return TabBarView(
              controller: _tabController,
              children: isManagement 
                ? [
                    _buildFeed("university"),
                    _buildFeed("faculty"),
                    _buildFeed("specialty"),
                  ]
                : [
                    _buildFeed("specialty"),
                    _buildFeed("faculty"),
                    _buildFeed("university"),
                  ],
            );
          }
        ),
        floatingActionButton: FloatingActionButton(
          onPressed: () async {
            final result = await Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => CreatePostScreen(initialScope: _getCurrentScope())),
            );
            if (result == true) {
              _fetchPosts(_getCurrentScope(), isSilent: false); // Immediate refresh
            }
          },
          backgroundColor: AppTheme.primaryBlue,
          child: const Icon(Icons.edit, color: Colors.white),
        ),
      );
  }

  Widget _buildFeed(String scope) {
    if (_isLoading[scope] == true && (_posts[scope] == null || _posts[scope]!.isEmpty)) {
      return ListView.builder(
         padding: const EdgeInsets.all(16),
         itemCount: 3,
         itemBuilder: (ctx, i) => const ShimmerPost(),
      );
    }
    
    final posts = _posts[scope] ?? [];
    
    if (posts.isEmpty) {
       return _buildEmptyState();
    }

    return RefreshIndicator(
      onRefresh: () async {
        await _fetchPosts(scope, isSilent: false);
      },
      child: ListView.builder(
        controller: _scrollControllers[scope],
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
        itemCount: posts.length + (_hasMore[scope] == true ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == posts.length) {
             return const Padding(
               padding: EdgeInsets.symmetric(vertical: 20),
               child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
             );
          }
          
          return PostCard(
            post: posts[index],
            onDelete: () {
              setState(() {
                _posts[scope]!.removeAt(index);
              });
            },
            onLikeChanged: (isLiked, count) {
              // Update local source of truth to prevent reversion on rebuild
              _posts[scope]![index] = posts[index].copyWith(
                isLiked: isLiked, 
                likes: count
              );
            },
            onRepostChanged: (isReposted, count) {
              _posts[scope]![index] = posts[index].copyWith(
                isRepostedByMe: isReposted,
                repostsCount: count
              );
            },
            onContentChanged: (newContent) {
              _posts[scope]![index] = posts[index].copyWith(
                content: newContent
              );
              // Force rebuild to ensure UI consistency if needed, though PostCard handles its own state
              // But if we scroll away and back, this updated model will be used.
            },
          );
        },
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.only(top: 40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.chat_bubble_outline_rounded, size: 60, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              "Hozircha jimjitlik...",
              style: TextStyle(color: Colors.grey[600], fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              "Birinchi bo'lib fikr bildiring!",
              style: TextStyle(color: Colors.grey[500], fontSize: 14),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () async {
                final result = await Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => CreatePostScreen(initialScope: _getCurrentScope())),
                );
                if (result == true) {
                   _fetchPosts(_getCurrentScope(), isSilent: false);
                }
              },
              icon: const Icon(Icons.edit, color: Colors.white),
              label: const Text("Post yozish", style: TextStyle(color: Colors.white)),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryBlue,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              ),
            )
          ],
        ),
      ),
    );
  }
}
