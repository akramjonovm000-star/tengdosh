import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';

class StudentDetailView extends StatefulWidget {
  final int studentId;

  const StudentDetailView({super.key, required this.studentId});

  @override
  State<StudentDetailView> createState() => _StudentDetailViewState();
}

class _StudentDetailViewState extends State<StudentDetailView> with SingleTickerProviderStateMixin {
  final DataService _dataService = DataService();
  late TabController _tabController;
  Map<String, dynamic>? _data;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    final data = await _dataService.getStudentFullDetails(widget.studentId);
    setState(() {
      _data = data;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text("Talaba ma'lumotlari")),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_data == null || _data!['profile'] == null) {
      return Scaffold(
        appBar: AppBar(title: const Text("Xatolik")),
        body: const Center(child: Text("Ma'lumotlarni yuklab bo'lmadi")),
      );
    }

    final profile = _data!['profile'];

    return Scaffold(
      backgroundColor: Colors.white,
      body: NestedScrollView(
        headerSliverBuilder: (context, innerBoxIsScrolled) {
          return [
            SliverAppBar(
              expandedHeight: 200.0,
              floating: false,
              pinned: true,
              backgroundColor: Colors.blue,
              flexibleSpace: FlexibleSpaceBar(
                background: Stack(
                  alignment: Alignment.center,
                  children: [
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SizedBox(height: 40),
                        CircleAvatar(
                          radius: 40,
                          backgroundColor: Colors.white,
                          backgroundImage: profile['image_url'] != null
                              ? NetworkImage(profile['image_url'])
                              : null,
                          child: profile['image_url'] == null
                              ? const Icon(Icons.person, size: 40, color: Colors.blue)
                              : null,
                        ),
                        const SizedBox(height: 10),
                        Text(
                          profile['full_name'] ?? "",
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          "ID: ${profile['hemis_id']} • ${profile['group_number']}",
                          style: TextStyle(color: Colors.white.withOpacity(0.8)),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            SliverPersistentHeader(
              pinned: true,
              delegate: _SliverAppBarDelegate(
                TabBar(
                  controller: _tabController,
                  labelColor: Colors.blue,
                  unselectedLabelColor: Colors.grey,
                  indicatorColor: Colors.blue,
                  isScrollable: true,
                  tabs: const [
                    Tab(text: "Murojaatlar"),
                    Tab(text: "Faolliklar"),
                    Tab(text: "Sertifikatlar"),
                    Tab(text: "Hujjatlar"),
                  ],
                ),
              ),
            ),
          ];
        },
        body: TabBarView(
          controller: _tabController,
          children: [
            _buildListSection(_data!['appeals'], "Murojaat"),
            _buildListSection(_data!['activities'], "Faollik"),
            _buildListSection(_data!['certificates'], "Sertifikat"),
            _buildListSection(_data!['documents'], "Hujjat"),
          ],
        ),
      ),
    );
  }

  Widget _buildListSection(List<dynamic>? items, String type) {
    if (items == null || items.isEmpty) {
      return Center(child: Text("$type topilmadi"));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.grey.shade200),
          ),
          child: ListTile(
            title: Text(item['title'] ?? item['text'] ?? "$type #${item['id']}"),
            subtitle: Text("Status: ${item['status']}"),
            trailing: item['date'] != null ? Text(item['date'].toString().split('T')[0]) : null,
          ),
        );
      },
    );
  }
}

class _SliverAppBarDelegate extends SliverPersistentHeaderDelegate {
  _SliverAppBarDelegate(this._tabBar);

  final TabBar _tabBar;

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
