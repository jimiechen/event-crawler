import 'package:flutter/material.dart';
import '../../models/stock_data.dart';

class TooltipOverlay extends StatelessWidget {
  final StockData data;
  final Offset position;
  final double chartWidth;
  final double chartHeight;

  const TooltipOverlay({
    super.key,
    required this.data,
    required this.position,
    required this.chartWidth,
    required this.chartHeight,
  });

  @override
  Widget build(BuildContext context) {
    final screenWidth = chartWidth + 60.0;
    final screenHeight = chartHeight + 30.0;

    double left = position.dx + 10;
    double top = position.dy + 10;

    if (left + 200 > screenWidth) {
      left = position.dx - 210;
    }

    if (top + 150 > screenHeight) {
      top = position.dy - 160;
    }

    return Positioned(
      left: left.clamp(0.0, screenWidth - 200),
      top: top.clamp(0.0, screenHeight - 150),
      child: Material(
        elevation: 4,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.grey[300]!),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '${data.date.year}-${data.date.month.toString().padLeft(2, '0')}-${data.date.day.toString().padLeft(2, '0')}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              _buildInfoRow('开盘', data.open.toStringAsFixed(2)),
              _buildInfoRow('最高', data.high.toStringAsFixed(2)),
              _buildInfoRow('最低', data.low.toStringAsFixed(2)),
              _buildInfoRow('收盘', data.close.toStringAsFixed(2)),
              const SizedBox(height: 4),
              _buildInfoRow('成交量', '${data.volume.toStringAsFixed(0)}手'),
              _buildInfoRow('涨跌幅', '${data.changePercent.toStringAsFixed(2)}%'),
              const SizedBox(height: 4),
              _buildInfoRow(
                'EXPMA5',
                data.expma5.toStringAsFixed(2),
                color: Colors.yellow[700],
              ),
              _buildInfoRow(
                'EXPMA13',
                data.expma13.toStringAsFixed(2),
                color: Colors.purple[700],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: Colors.grey[600],
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color: color ?? (value.contains('-') ? Colors.green : Colors.red),
            ),
          ),
        ],
      ),
    );
  }
}
