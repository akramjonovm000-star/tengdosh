import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

class LibraryFilterSheet extends StatefulWidget {
  final List<String> categories;
  final String initialCategory;
  final bool initialAvailableOnly;
  final bool initialEbookOnly;
  final String initialSortBy;
  final Function(String category, bool available, bool ebook, String sortBy) onApply;

  const LibraryFilterSheet({
    super.key,
    required this.categories,
    required this.initialCategory,
    required this.initialAvailableOnly,
    required this.initialEbookOnly,
    required this.initialSortBy,
    required this.onApply,
  });

  @override
  State<LibraryFilterSheet> createState() => _LibraryFilterSheetState();
}

class _LibraryFilterSheetState extends State<LibraryFilterSheet> {
  late String _category;
  late bool _availableOnly;
  late bool _ebookOnly;
  late String _sortBy;

  @override
  void initState() {
    super.initState();
    _category = widget.initialCategory;
    _availableOnly = widget.initialAvailableOnly;
    _ebookOnly = widget.initialEbookOnly;
    _sortBy = widget.initialSortBy;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            "Filtr",
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 24),
          const Text("Kategoriyalar", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            children: widget.categories.map((cat) {
              final isSelected = _category == cat;
              return ChoiceChip(
                label: Text(cat),
                selected: isSelected,
                onSelected: (val) => setState(() => _category = cat),
                selectedColor: AppTheme.primaryBlue,
                backgroundColor: Colors.grey[100],
                labelStyle: TextStyle(
                  color: isSelected ? Colors.white : Colors.black87,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 24),
          const Text("Holati", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text("Faqat mavjud kitoblar"),
            value: _availableOnly,
            onChanged: (val) => setState(() => _availableOnly = val),
            activeColor: AppTheme.primaryBlue,
          ),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text("Elektron variant bor"),
            value: _ebookOnly,
            onChanged: (val) => setState(() => _ebookOnly = val),
            activeColor: AppTheme.primaryBlue,
          ),
          const SizedBox(height: 24),
          const Text("Saralash", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildSortOption("popular", "Mashhur"),
              _buildSortOption("new", "Yangi"),
              _buildSortOption("alpha", "A-Z"),
            ],
          ),
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton(
              onPressed: () {
                widget.onApply(_category, _availableOnly, _ebookOnly, _sortBy);
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryBlue,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text("Qo'llash", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildSortOption(String value, String label) {
    final isSelected = _sortBy == value;
    return GestureDetector(
      onTap: () => setState(() => _sortBy = value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryBlue : Colors.grey[100],
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: isSelected ? Colors.transparent : Colors.grey[300]!),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black87,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
          ),
        ),
      ),
    );
  }
}
