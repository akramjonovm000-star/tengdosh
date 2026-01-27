import 'package:flutter/material.dart';

class ShimmerPost extends StatefulWidget {
  const ShimmerPost({super.key});

  @override
  State<ShimmerPost> createState() => _ShimmerPostState();
}

class _ShimmerPostState extends State<ShimmerPost> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
    _animation = Tween<double>(begin: 0.3, end: 1.0).animate(_controller);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Widget _buildBox(double w, double h) {
    return FadeTransition(
      opacity: _animation,
      child: Container(
        width: w,
        height: h,
        decoration: BoxDecoration(
          color: Colors.grey[300],
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              FadeTransition(
                opacity: _animation,
                child: CircleAvatar(radius: 20, backgroundColor: Colors.grey[300]),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildBox(120, 14),
                  const SizedBox(height: 6),
                  _buildBox(80, 10),
                ],
              )
            ],
          ),
          const SizedBox(height: 16),
          _buildBox(double.infinity, 12),
          const SizedBox(height: 8),
          _buildBox(double.infinity, 12),
          const SizedBox(height: 8),
          _buildBox(200, 12),
          
          const SizedBox(height: 16),
          Row(
            children: [
              _buildBox(60, 24),
              const SizedBox(width: 8),
              _buildBox(60, 24),
            ],
          )
        ],
      ),
    );
  }
}
