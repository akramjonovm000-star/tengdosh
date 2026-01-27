import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../models/market_item.dart';
import '../services/market_service.dart';
import 'create_market_item_screen.dart';
import 'market_item_detail_screen.dart';
import 'package:provider/provider.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../profile/screens/subscription_screen.dart';

class MarketScreen extends StatefulWidget {
  const MarketScreen({super.key});

  @override
  State<MarketScreen> createState() => _MarketScreenState();
}

class _MarketScreenState extends State<MarketScreen> {
  final MarketService _marketService = MarketService();
  
  List<MarketItem> _featuredItems = [];
  List<MarketItem> _newItems = [];
  bool _isLoading = true;

  final Map<String, String> _categories = {
    'books': 'Kitoblar',
    'tech': 'Texnika',
    'housing': 'Kvartira',
    'jobs': 'Ish',
    'lost': 'Yo\'qolgan',
    'other': 'Boshqa',
  };

  final Map<String, IconData> _categoryIcons = {
    'books': Icons.menu_book,
    'tech': Icons.devices,
    'housing': Icons.home,
    'jobs': Icons.work,
    'lost': Icons.search,
    'other': Icons.more_horiz,
  };

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final featured = await _marketService.getItems(sort: 'popular', search: '');
      final newItems = await _marketService.getItems(sort: 'newest', search: '');
      
      if (mounted) {
        setState(() {
          _featuredItems = featured.take(5).toList();
          _newItems = newItems;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (e.toString().contains("PREMIUM_REQUIRED")) {
        if (mounted) {
          await Provider.of<AuthProvider>(context, listen: false).loadUser();
        }
      }
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5), // Light grey background like B&N
      body: CustomScrollView(
        slivers: [
          _buildSliverAppBar(),
          if (_isLoading)
            const SliverFillRemaining(child: Center(child: CircularProgressIndicator()))
          else if (_featuredItems.isEmpty && _newItems.isEmpty)
            const SliverFillRemaining(child: Center(child: Text("Hozircha e'lonlar yo'q")))
          else ...[
            _buildHeroSection(),
            if (_featuredItems.isNotEmpty) ...[
              _buildSectionTitle("Eng ko'p ko'rilganlar"),
              _buildFeaturedHorizontalList(),
            ],
            _buildSectionTitle("Kategoriyalar"),
            _buildCategoryGrid(),
            if (_newItems.isNotEmpty) ...[
              _buildSectionTitle("Yangi E'lonlar"),
              _buildNewItemsGrid(),
            ],
            const SliverToBoxAdapter(child: SizedBox(height: 80)), // Bottom padding
          ]
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final res = await Navigator.push(context, MaterialPageRoute(builder: (_) => const CreateMarketItemScreen()));
          if (res == true) _loadData();
        },
        label: const Text("E'lon berish"),
        icon: const Icon(Icons.add),
        backgroundColor: AppTheme.primaryBlue,
      ),
    );
  }

  Widget _buildSliverAppBar() {
    return SliverAppBar(
      floating: true,
      pinned: true,
      backgroundColor: Colors.white,
      elevation: 1,
      title: const Text("Talaba Bozori", style: TextStyle(color: Colors.black, fontFamily: 'Serif', fontWeight: FontWeight.bold)),
      centerTitle: true,
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(60),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
          child: TextField(
            decoration: InputDecoration(
              hintText: "Kitob, texnika yoki ish qidiring...",
              prefixIcon: const Icon(Icons.search, color: Colors.grey),
              filled: true,
              fillColor: Colors.grey[100],
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16),
            ),
            onSubmitted: (val) {
               // Implement search navigation
            },
          ),
        ),
      ),
    );
  }

  Widget _buildHeroSection() {
    return SliverToBoxAdapter(
      child: Container(
        height: 140,
        margin: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF2C3E50), // B&N Greenish/Dark Blue
          borderRadius: BorderRadius.circular(12),
          image: const DecorationImage(
             image: NetworkImage("https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?q=80&w=1000&auto=format&fit=crop"), // Library
             fit: BoxFit.cover,
             opacity: 0.3
          )
        ),
        child: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                "O'qish uchun kerakli hamma narsa",
                style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold, fontFamily: 'Serif'),
              ),
              SizedBox(height: 8),
              Text(
                "Kitoblar, kiyimlar va texnikalar",
                style: TextStyle(color: Colors.white70, fontSize: 14),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return SliverToBoxAdapter(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, fontFamily: 'Serif')),
            const Icon(Icons.arrow_forward_ios, size: 14, color: Colors.grey),
          ],
        ),
      ),
    );
  }

  Widget _buildFeaturedHorizontalList() {
    return SliverToBoxAdapter(
      child: SizedBox(
        height: 220,
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          itemCount: _featuredItems.length,
          itemBuilder: (context, index) {
            return _buildBookCard(_featuredItems[index]);
          },
        ),
      ),
    );
  }

  Widget _buildBookCard(MarketItem item) {
    return GestureDetector(
      onTap: () {
        Navigator.push(context, MaterialPageRoute(builder: (_) => MarketItemDetailScreen(item: item)));
      },
      child: Container(
        width: 130,
        margin: const EdgeInsets.only(right: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  color: Colors.grey[200],
                  boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))],
                  image: item.imageUrl != null 
                      ? DecorationImage(image: NetworkImage(item.imageUrl!), fit: BoxFit.cover)
                      : null,
                ),
                child: item.imageUrl == null 
                    ? Center(child: Icon(_categoryIcons[item.category] ?? Icons.book, color: Colors.grey))
                    : null,
              ),
            ),
            const SizedBox(height: 8),
            Text(item.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
            Text(item.price ?? "Kelishilgan", style: const TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildCategoryGrid() {
    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      sliver: SliverGrid(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
           crossAxisCount: 3, 
           childAspectRatio: 1.5, 
           crossAxisSpacing: 8, 
           mainAxisSpacing: 8
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            final key = _categories.keys.elementAt(index);
            final label = _categories.values.elementAt(index);
            return Container(
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.grey.shade200)),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(_categoryIcons[key], size: 20, color: AppTheme.primaryBlue),
                  const SizedBox(height: 4),
                  Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500)),
                ],
              ),
            );
          },
          childCount: _categories.length,
        ),
      ),
    );
  }

  Widget _buildNewItemsGrid() {
     return SliverPadding(
      padding: const EdgeInsets.all(16),
      sliver: SliverGrid(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 0.65,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) => _buildBookCard(_newItems[index]), 
          childCount: _newItems.length,
        ),
      ),
    );
  }
}
