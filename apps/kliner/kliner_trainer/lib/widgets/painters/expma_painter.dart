import 'package:flutter/material.dart';
import '../../models/stock_data.dart';

class ExpmaPainter extends CustomPainter {
  final List<StockData> data;
  final int visibleStart;
  final int visibleEnd;
  final double candleWidth;
  final double candleSpacing;
  final double paddingRight;
  final double paddingBottom;
  final bool showExpma5;
  final bool showExpma13;

  ExpmaPainter({
    required this.data,
    this.visibleStart = 0,
    this.visibleEnd = 60,
    this.candleWidth = 8.0,
    this.candleSpacing = 4.0,
    this.paddingRight = 60.0,
    this.paddingBottom = 30.0,
    this.showExpma5 = true,
    this.showExpma13 = true,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty || visibleStart >= data.length) return;

    final visibleData = _getVisibleData();
    if (visibleData.isEmpty) return;

    final chartWidth = size.width - paddingRight;
    final chartHeight = size.height - paddingBottom;

    final priceRange = _calculatePriceRange(visibleData);
    final maxPrice = priceRange['max']!;
    final minPrice = priceRange['min']!;

    if (showExpma5) {
      _drawExpmaLine(canvas, chartWidth, chartHeight, maxPrice, minPrice, visibleData, Colors.yellow, 'expma5');
    }

    if (showExpma13) {
      _drawExpmaLine(canvas, chartWidth, chartHeight, maxPrice, minPrice, visibleData, Colors.purple, 'expma13');
    }
  }

  List<StockData> _getVisibleData() {
    final end = visibleEnd < data.length ? visibleEnd : data.length;
    return data.sublist(visibleStart, end);
  }

  Map<String, double> _calculatePriceRange(List<StockData> visibleData) {
    double maxPrice = visibleData.map((d) => d.high).reduce((a, b) => a > b ? a : b);
    double minPrice = visibleData.map((d) => d.low).reduce((a, b) => a < b ? a : b);

    final range = maxPrice - minPrice;
    maxPrice += range * 0.05;
    minPrice -= range * 0.05;

    return {'max': maxPrice, 'min': minPrice};
  }

  void _drawExpmaLine(
    Canvas canvas,
    double chartWidth,
    double chartHeight,
    double maxPrice,
    double minPrice,
    List<StockData> visibleData,
    Color color,
    String expmaType,
  ) {
    if (visibleData.length < 2) return;

    final totalCandleWidth = candleWidth + candleSpacing;
    final availableWidth = chartWidth;
    final numCandles = (availableWidth / totalCandleWidth).floor();

    final path = Path();
    final points = <Offset>[];

    for (int i = 0; i < visibleData.length && i < numCandles; i++) {
      final d = visibleData[i];
      final x = i * totalCandleWidth + candleSpacing / 2;

      double expmaValue;
      if (expmaType == 'expma5') {
        expmaValue = d.expma5;
      } else {
        expmaValue = d.expma13;
      }

      if (expmaValue > 0) {
        final y = _priceToY(expmaValue, maxPrice, minPrice, chartHeight);
        points.add(Offset(x, y));
      }
    }

    if (points.isNotEmpty) {
      path.moveTo(points.first.dx, points.first.dy);

      for (int i = 1; i < points.length; i++) {
        final p0 = points[i - 1];
        final p1 = points[i];
        final cp1 = Offset((p0.dx + p1.dx) / 2, p0.dy);
        final cp2 = Offset((p0.dx + p1.dx) / 2, p1.dy);
        path.cubicTo(cp1.dx, cp1.dy, cp2.dx, cp2.dy, p1.dx, p1.dy);
      }

      final paint = Paint()
        ..color = color
        ..strokeWidth = 2.0
        ..style = PaintingStyle.stroke;

      canvas.drawPath(path, paint);
    }
  }

  double _priceToY(double price, double maxPrice, double minPrice, double height) {
    return height * (maxPrice - price) / (maxPrice - minPrice);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
