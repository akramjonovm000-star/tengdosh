import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/services/data_service.dart';
import 'package:intl/intl.dart';

class ContractScreen extends StatefulWidget {
  const ContractScreen({super.key});

  @override
  State<ContractScreen> createState() => _ContractScreenState();
}

class _ContractScreenState extends State<ContractScreen> {
  final DataService _dataService = DataService();
  bool _isLoading = true;
  String _errorMessage = '';
  Map<String, dynamic>? _contractData;

  @override
  void initState() {
    super.initState();
    _fetchContractData();
  }

  Future<void> _fetchContractData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      final data = await _dataService.getContractInfo(forceRefresh: true);
      setState(() {
        _contractData = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceAll("Exception: ", "");
        _isLoading = false;
      });
    }
  }

  String _formatCurrency(dynamic amount) {
    if (amount == null) return "0 so'm";
    final number = double.tryParse(amount.toString()) ?? 0.0;
    final formatter = NumberFormat.currency(locale: 'uz_UZ', symbol: "so'm", decimalDigits: 0);
    return formatter.format(number);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundWhite,
      appBar: AppBar(
        title: const Text("Shartnoma ma'lumotlari", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryBlue))
          : _errorMessage.isNotEmpty
              ? _buildErrorView()
              : _contractData == null || _contractData!.isEmpty
                  ? _buildEmptyView()
                  : _buildContentView(),
    );
  }

  Widget _buildErrorView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 60, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              _errorMessage,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, color: Colors.grey),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _fetchContractData,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryBlue,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text("Qayta urinish"),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyView() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inventory_2_outlined, size: 80, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              "Shartnoma ma'lumotlari topilmadi",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              "Sizda faol shartnoma mavjud emas yoki tizimda ma'lumot yo'q.",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContentView() {
    // Hemis attributes structure
    final attributes = _contractData?['attributes'] ?? {};
    final items = _contractData?['items'] as List<dynamic>? ?? [];

    final totalAmount = attributes['amount'];
    final discount = attributes['discount'];
    final paidAmount = attributes['amount_paid'];
    final debt = attributes['amount_debt'];
    final credit = attributes['amount_credit'];
    final totalComputedStr = attributes['total_computed'] ?? attributes['totalComputed']; // Fallback keys
    
    // Status text (sometimes HEMIS provides it directly)
    final contractStatus = attributes['status'] ?? "Faol";

    return RefreshIndicator(
      onRefresh: _fetchContractData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Card
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: AppTheme.primaryBlue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.primaryBlue.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: AppTheme.primaryBlue),
                  const SizedBox(width: 12),
                  const Text(
                    "Holat:",
                    style: TextStyle(fontWeight: FontWeight.w600, color: AppTheme.primaryBlue),
                  ),
                  const Spacer(),
                  Text(
                    contractStatus.toString(),
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Financial Summary
            const Text(
              "Moliya xulosasi",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 15,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: Column(
                children: [
                  _buildSummaryRow(
                    "Jami summa", 
                    totalAmount ?? totalComputedStr, 
                    Icons.account_balance_wallet_rounded, 
                    Colors.black87
                  ),
                  const Divider(height: 24),
                  if (discount != null && double.tryParse(discount.toString()) != 0.0) ...[
                    _buildSummaryRow("Chegirma", discount, Icons.local_offer_rounded, Colors.green),
                    const Divider(height: 24),
                  ],
                    if (credit != null && double.tryParse(credit.toString()) != 0.0) ...[
                    _buildSummaryRow("Kredit summa", credit, Icons.account_balance_rounded, AppTheme.primaryBlue),
                    const Divider(height: 24),
                  ],
                  _buildSummaryRow("To'langan", paidAmount, Icons.price_check_rounded, Colors.green.shade600),
                  const Divider(height: 24),
                  _buildSummaryRow(
                    "Qarzdorlik", 
                    debt, 
                    Icons.warning_rounded, 
                    (double.tryParse(debt?.toString() ?? "0") ?? 0) > 0 ? Colors.red : Colors.grey
                  ),
                ],
              ),
            ),

            const SizedBox(height: 32),

            // Payment History
            if (items.isNotEmpty) ...[
              const Text(
                "To'lovlar tarixi",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: items.length,
                itemBuilder: (context, index) {
                  final item = items[index];
                  return _buildPaymentHistoryItem(item);
                },
              )
            ] else ...[
               const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 32),
                    child: Text(
                      "To'lovlar tarixi mavjud emas",
                      style: TextStyle(color: Colors.grey),
                    ),
                  ),
               ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryRow(String label, dynamic value, IconData icon, Color color) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 20),
        ),
        const SizedBox(width: 12),
        Text(
          label,
          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500, color: Colors.black87),
        ),
        const Spacer(),
        Text(
          _formatCurrency(value),
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color),
        ),
      ],
    );
  }

  Widget _buildPaymentHistoryItem(dynamic item) {
    // Attempt to extract typical Hemis date formats, e.g. "date" or "payment_date" or "updated_at"
    final dateStr = item['date'] ?? item['payment_date'] ?? item['created_at'] ?? '';
    final amount = item['amount'] ?? 0;
    
    // Fallback parsing for date
    String formattedDate = dateStr;
    try {
      if (dateStr.isNotEmpty) {
        final date = DateTime.parse(dateStr);
        formattedDate = DateFormat('dd.MM.yyyy HH:mm').format(date);
      } else {
        formattedDate = "Vaqt noma'lum";
      }
    } catch (_) {}

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Colors.green.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.monetization_on_rounded, color: Colors.green),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "Kirim", // Most items in history are payments (kirim)
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                const SizedBox(height: 4),
                Text(
                  formattedDate,
                  style: const TextStyle(color: Colors.grey, fontSize: 13),
                ),
              ],
            ),
          ),
          Text(
            "+ ${_formatCurrency(amount)}",
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.green),
          ),
        ],
      ),
    );
  }
}
