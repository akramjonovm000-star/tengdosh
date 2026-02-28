import 'package:flutter/material.dart';
import '../../../../core/services/data_service.dart';
import '../../../../core/theme/app_theme.dart';

class ClubMemberProfileScreen extends StatefulWidget {
  final int clubId;
  final int studentId;
  final DataService dataService;

  const ClubMemberProfileScreen({
    Key? key,
    required this.clubId,
    required this.studentId,
    required this.dataService,
  }) : super(key: key);

  @override
  State<ClubMemberProfileScreen> createState() => _ClubMemberProfileScreenState();
}

class _ClubMemberProfileScreenState extends State<ClubMemberProfileScreen> {
  late Future<Map<String, dynamic>?> _profileFuture;

  @override
  void initState() {
    super.initState();
    _profileFuture = widget.dataService.getClubMemberProfile(widget.clubId, widget.studentId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F6FA),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          "A'zo profili",
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: FutureBuilder<Map<String, dynamic>?>(
        future: _profileFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data == null) {
            return const Center(child: Text(AppDictionary.tr(context, 'msg_info_not_found')));
          }
          final data = snapshot.data!;
          final List acts = data['activities'] ?? [];

          return SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                data['image_url'] != null
                  ? CircleAvatar(
                      radius: 50,
                      backgroundColor: Colors.grey.shade200,
                      backgroundImage: NetworkImage(data['image_url']),
                    )
                  : CircleAvatar(
                      radius: 50,
                      backgroundColor: AppTheme.primaryBlue.withOpacity(0.1),
                      child: const Icon(Icons.person, size: 50, color: AppTheme.primaryBlue),
                    ),
                const SizedBox(height: 16),
                Text(
                  data['full_name'] ?? 'Noma\'lum', 
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold), 
                  textAlign: TextAlign.center
                ),
                const SizedBox(height: 8),
                Text(
                  data['faculty_name'] ?? 'Fakultet yo\'q', 
                  style: const TextStyle(fontSize: 15, color: Colors.grey), 
                  textAlign: TextAlign.center
                ),
                if (data['group_number'] != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    data['group_number'], 
                    style: const TextStyle(fontSize: 15, color: Colors.grey), 
                    textAlign: TextAlign.center
                  ),
                ],
                const SizedBox(height: 32),
                
                const Align(
                  alignment: Alignment.centerLeft,
                  child: Text(AppDictionary.tr(context, 'lbl_club_activities_events'), 
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)
                  ),
                ),
                const SizedBox(height: 16),
                if (acts.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(20),
                    child: Text(AppDictionary.tr(context, 'msg_no_activities_yet'), style: TextStyle(color: Colors.grey)),
                  ),
                for (var act in acts)
                  Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))],
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.green.withOpacity(0.1),
                            shape: BoxShape.circle
                          ),
                          child: const Icon(Icons.check, color: Colors.green, size: 20),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                act['event_title'] ?? '', 
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14), 
                                maxLines: 2, 
                                overflow: TextOverflow.ellipsis
                              ),
                              const SizedBox(height: 4),
                              if (act['event_date'] != null)
                                Text(
                                  act['event_date'].toString().substring(0, 10), 
                                  style: const TextStyle(color: Colors.grey, fontSize: 12)
                                )
                            ]
                          )
                        )
                      ]
                    )
                  )
              ]
            )
          );
        },
      ),
    );
  }
}
