import 'package:flutter/material.dart';
import '../../models/stock_data.dart';

class CrosshairOverlay extends StatelessWidget {
  final StockData data;
  final Offset position;
  final double chartWidth;
  final double chartHeight;
  final double maxPrice;
  final double minPrice;
  final double paddingRight;
  final double paddingBottom;

  const CrosshairOverlay({
    super.key,
    required this.data,
    required this.position,
    required this.chartWidth,
    required this.chartHeight,
    required this.maxPrice,
    required this.minPrice,
    this.paddingRight = 60.0,
    this.paddingBottom = 30.0,
  });

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size(chartWidth + paddingRight, chartHeight + paddingBottom),
      painter: _CrosshairPainter(
        position: position,
        chartWidth: chartWidth,
        chartHeight: chartHeight,
        paddingRight: paddingRight,
        paddingBottom: paddingBottom,
      ),
    );
  }
}

class _CrosshairPainter extends CustomPainter {
  final Offset position;
  final double chartWidth;
  final double chartHeight;
  final double paddingRight;
  final double paddingBottom;

  _CrosshairPainter({
    required this.position,
    required this.chartWidth,
    required this.chartHeight,
    required this.paddingRight,
    required this.paddingBottom,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.grey[400]!
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke;

    final dashPaint = Paint()
      ..color = Colors.grey[400]!
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke;

    final x = position.dx.clamp(0.0, chartWidth);
    final y = position.dy.clamp(0.0, chartHeight);

    canvas.drawLine(
      Offset(x, 0),
      Offset(x, chartHeight),
      dashPaint,
    );

    canvas.drawLine(
      Offset(0, y),
      Offset(chartWidth, y),
      dashPaint,
    );

    canvas.drawCircle(Offset(x, y), 4.0, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
