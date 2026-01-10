import 'package:flutter/material.dart';
import '../../models/stock_data.dart';

class KLinePainter extends CustomPainter {
  final List<StockData> data;
  final int visibleStart;
  final int visibleEnd;
  final double candleWidth;
  final double candleSpacing;
  final double paddingRight;
  final double paddingBottom;

  KLinePainter({
    required this.data,
    this.visibleStart = 0,
    this.visibleEnd = 60,
    this.candleWidth = 8.0,
    this.candleSpacing = 4.0,
    this.paddingRight = 60.0,
    this.paddingBottom = 30.0,
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

    _drawGrid(canvas, size, chartWidth, chartHeight, maxPrice, minPrice, visibleData);
    _drawCandles(canvas, size, chartWidth, chartHeight, maxPrice, minPrice, visibleData);
    _drawPriceAxis(canvas, size, chartHeight, maxPrice, minPrice);
    _drawDateAxis(canvas, size, chartWidth, chartHeight, visibleData);
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

  void _drawGrid(
    Canvas canvas,
    Size size,
    double chartWidth,
    double chartHeight,
    double maxPrice,
    double minPrice,
    List<StockData> visibleData,
  ) {
    final gridPaint = Paint()
      ..color = const Color(0xFFD3D3D3)
      ..strokeWidth = 0.5;

    final horizontalLines = 5;
    for (int i = 0; i <= horizontalLines; i++) {
      final y = (chartHeight / horizontalLines) * i;
      canvas.drawLine(
        Offset(0, y),
        Offset(chartWidth, y),
        gridPaint,
      );
    }

    final verticalLines = 6;
    for (int i = 0; i <= verticalLines; i++) {
      final x = (chartWidth / verticalLines) * i;
      canvas.drawLine(
        Offset(x, 0),
        Offset(x, chartHeight),
        gridPaint,
      );
    }
  }

  void _drawCandles(
    Canvas canvas,
    Size size,
    double chartWidth,
    double chartHeight,
    double maxPrice,
    double minPrice,
    List<StockData> visibleData,
  ) {
    final totalCandleWidth = candleWidth + candleSpacing;
    final availableWidth = chartWidth;
    final numCandles = (availableWidth / totalCandleWidth).floor();

    for (int i = 0; i < visibleData.length && i < numCandles; i++) {
      final d = visibleData[i];
      final x = i * totalCandleWidth + candleSpacing / 2;

      final highY = _priceToY(d.high, maxPrice, minPrice, chartHeight);
      final lowY = _priceToY(d.low, maxPrice, minPrice, chartHeight);
      final openY = _priceToY(d.open, maxPrice, minPrice, chartHeight);
      final closeY = _priceToY(d.close, maxPrice, minPrice, chartHeight);

      final shadowPaint = Paint()
        ..color = Colors.grey[600]!
        ..strokeWidth = 1.0;

      canvas.drawLine(
        Offset(x, highY),
        Offset(x, lowY),
        shadowPaint,
      );

      final isBull = d.close >= d.open;
      final bodyPaint = Paint()
        ..color = isBull ? Colors.red : Colors.green
        ..style = PaintingStyle.fill;

      final top = isBull ? closeY : openY;
      final bottom = isBull ? openY : closeY;
      final bodyHeight = (top - bottom).abs();

      if (bodyHeight > 0.5) {
        canvas.drawRect(
          Rect.fromLTRB(
            x - candleWidth / 2,
            top,
            x + candleWidth / 2,
            bottom,
          ),
          bodyPaint,
        );
      } else {
        canvas.drawLine(
          Offset(x - candleWidth / 2, top),
          Offset(x + candleWidth / 2, top),
          bodyPaint..strokeWidth = 1.0,
        );
      }
    }
  }

  void _drawPriceAxis(
    Canvas canvas,
    Size size,
    double chartHeight,
    double maxPrice,
    double minPrice,
  ) {
    final axisPaint = Paint()
      ..color = Colors.grey[400]!
      ..strokeWidth = 1.0;

    canvas.drawLine(
      Offset(size.width - paddingRight, 0),
      Offset(size.width - paddingRight, chartHeight),
      axisPaint,
    );

    const horizontalLines = 5;
    for (int i = 0; i <= horizontalLines; i++) {
      final y = (chartHeight / horizontalLines) * i;
      final price = maxPrice - (maxPrice - minPrice) * i / horizontalLines;
      _drawText(
        canvas,
        price.toStringAsFixed(2),
        Offset(size.width - paddingRight + 5, y - 6),
        fontSize: 10,
        color: Colors.grey[600]!,
      );
    }
  }

  void _drawDateAxis(
    Canvas canvas,
    Size size,
    double chartWidth,
    double chartHeight,
    List<StockData> visibleData,
  ) {
    final axisPaint = Paint()
      ..color = Colors.grey[400]!
      ..strokeWidth = 1.0;

    canvas.drawLine(
      Offset(0, chartHeight),
      Offset(chartWidth, chartHeight),
      axisPaint,
    );

    final totalCandleWidth = candleWidth + candleSpacing;
    final availableWidth = chartWidth;
    final numCandles = (availableWidth / totalCandleWidth).floor();

    final dateInterval = (numCandles / 6).ceil();

    for (int i = 0; i < visibleData.length && i < numCandles; i += dateInterval) {
      final d = visibleData[i];
      final x = i * totalCandleWidth + candleSpacing / 2;

      final dateStr = '${d.date.month}/${d.date.day}';
      _drawText(
        canvas,
        dateStr,
        Offset(x - 15, chartHeight + 5),
        fontSize: 10,
        color: Colors.grey[600]!,
      );
    }
  }

  double _priceToY(double price, double maxPrice, double minPrice, double height) {
    return height * (maxPrice - price) / (maxPrice - minPrice);
  }

  void _drawText(
    Canvas canvas,
    String text,
    Offset offset, {
    double fontSize = 12,
    Color color = Colors.black,
  }) {
    final textStyle = TextStyle(color: color, fontSize: fontSize);
    final textSpan = TextSpan(text: text, style: textStyle);
    final textPainter = TextPainter(
      text: textSpan,
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, offset);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    if (oldDelegate is! KLinePainter) return true;
    final old = oldDelegate as KLinePainter;
    return old.visibleStart != visibleStart ||
           old.visibleEnd != visibleEnd ||
           old.data.length != data.length;
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is KLinePainter &&
           other.visibleStart == visibleStart &&
           other.visibleEnd == visibleEnd &&
           other.data.length == data.length;
  }

  @override
  int get hashCode => Object.hash(visibleStart, visibleEnd, data.length);
}
