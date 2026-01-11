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
  final double? maxPrice;
  final double? minPrice;

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
    this.maxPrice,
    this.minPrice,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty || visibleStart >= data.length) return;

    final visibleData = _getVisibleData();
    if (visibleData.isEmpty) return;

    final chartWidth = size.width - paddingRight;
    final chartHeight = size.height - paddingBottom;
    
    // Dynamic candle width calculation
    final count = visibleData.length;
    final totalCandleWidth = count > 0 ? chartWidth / count : this.candleWidth + this.candleSpacing;
    final candleWidth = totalCandleWidth * 0.8;
    final candleSpacing = totalCandleWidth * 0.2;

    double maxPrice;
    double minPrice;

    if (this.maxPrice != null && this.minPrice != null) {
      maxPrice = this.maxPrice!;
      minPrice = this.minPrice!;
    } else {
      final priceRange = _calculatePriceRange(visibleData);
      maxPrice = priceRange['max']!;
      minPrice = priceRange['min']!;
    }

    if (showExpma5) {
      _drawExpmaLine(canvas, chartWidth, chartHeight, maxPrice, minPrice, visibleData, Colors.blue, 'expma5', candleWidth, candleSpacing);
    }

    if (showExpma13) {
      _drawExpmaLine(canvas, chartWidth, chartHeight, maxPrice, minPrice, visibleData, Colors.purple, 'expma13', candleWidth, candleSpacing);
    }
    
    _drawExpmaInfo(canvas, visibleData);
  }

  void _drawExpmaInfo(Canvas canvas, List<StockData> visibleData) {
    if (visibleData.isEmpty) return;
    
    // 获取当前K线（最后一个可见数据）
    final currentData = visibleData.last;
    
    double x = 10;
    // 调整Y坐标，避开顶部标题（假设标题高度约30）
    const double y = 40; 
    
    if (showExpma5) {
      final text = 'EXPMA5: ${currentData.expma5.toStringAsFixed(2)}';
      _drawText(canvas, text, Offset(x, y), color: Colors.blue, fontWeight: FontWeight.bold);
      x += _measureText(text) + 10;
    }
    
    if (showExpma13) {
      final text = 'EXPMA13: ${currentData.expma13.toStringAsFixed(2)}';
      _drawText(canvas, text, Offset(x, y), color: Colors.purple, fontWeight: FontWeight.bold);
    }
  }

  double _measureText(String text, {double fontSize = 10}) {
    final textPainter = TextPainter(
      text: TextSpan(text: text, style: TextStyle(fontSize: fontSize)),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    return textPainter.width;
  }

  void _drawText(
    Canvas canvas,
    String text,
    Offset offset, {
    double fontSize = 10,
    Color color = Colors.black,
    FontWeight fontWeight = FontWeight.normal,
  }) {
    final textPainter = TextPainter(
      text: TextSpan(
        text: text, 
        style: TextStyle(
          color: color, 
          fontSize: fontSize,
          fontWeight: fontWeight,
        )
      ),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, offset);
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
    double candleWidth,
    double candleSpacing,
  ) {
    if (visibleData.length < 2) return;

    final totalCandleWidth = candleWidth + candleSpacing;
    final availableWidth = chartWidth;
    final numCandles = (availableWidth / totalCandleWidth).floor();

    final path = Path();
    final points = <Offset>[];

    for (int i = 0; i < visibleData.length && i < numCandles; i++) {
      final d = visibleData[i];
      final x = i * totalCandleWidth + totalCandleWidth / 2; // Center of candle

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
        path.lineTo(points[i].dx, points[i].dy);
      }

      final paint = Paint()
        ..color = color
        ..strokeWidth = 2.0
        ..style = PaintingStyle.stroke
        ..strokeJoin = StrokeJoin.round
        ..strokeCap = StrokeCap.round;

      canvas.drawPath(path, paint);
    }
  }

  double _priceToY(double price, double maxPrice, double minPrice, double height) {
    return height * (maxPrice - price) / (maxPrice - minPrice);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
