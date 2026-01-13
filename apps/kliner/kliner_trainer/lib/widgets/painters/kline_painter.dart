import 'package:flutter/material.dart';
import '../../models/stock_data.dart';
import '../../models/operation_record.dart';

class KLinePainter extends CustomPainter {
  final List<StockData> data;
  final int visibleStart;
  final int visibleEnd;
  final double candleWidth;
  final double candleSpacing;
  final double paddingRight;
  final double paddingBottom;
  final double paddingTop;
  final double? maxPrice;
  final double? minPrice;
  final List<OperationRecord> operations;
  final StockData? selectedData;

  KLinePainter({
    required this.data,
    this.visibleStart = 0,
    this.visibleEnd = 60,
    this.candleWidth = 8.0,
    this.candleSpacing = 4.0,
    this.paddingRight = 60.0,
    this.paddingBottom = 30.0,
    this.paddingTop = 20.0,
    this.maxPrice,
    this.minPrice,
    this.operations = const [],
    this.selectedData,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty || visibleStart >= data.length) return;

    final visibleData = _getVisibleData();
    if (visibleData.isEmpty) return;

    final chartWidth = size.width - paddingRight;
    final chartHeight = size.height - paddingBottom - paddingTop;
    
    canvas.save();
    canvas.translate(0, paddingTop);

    // 动态计算蜡烛宽度
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

    _drawGrid(canvas, size, chartWidth, chartHeight, maxPrice, minPrice, visibleData);
    _drawCandles(canvas, size, chartWidth, chartHeight, maxPrice, minPrice, visibleData, candleWidth, candleSpacing);
    _drawOperationLabels(canvas, chartWidth, chartHeight, maxPrice, minPrice, visibleData, candleWidth, candleSpacing);
    _drawCrosshair(canvas, chartWidth, chartHeight, maxPrice, minPrice, visibleData, candleWidth, candleSpacing);
    _drawPriceAxis(canvas, size, chartHeight, maxPrice, minPrice);
    _drawDateAxis(canvas, size, chartWidth, chartHeight, visibleData, candleWidth, candleSpacing);
    
    canvas.restore();
  }

  void _drawCrosshair(
    Canvas canvas,
    double chartWidth,
    double chartHeight,
    double maxPrice,
    double minPrice,
    List<StockData> visibleData,
    double candleWidth,
    double candleSpacing,
  ) {
    if (selectedData == null) return;
    
    final index = visibleData.indexOf(selectedData!);
    if (index == -1) return;
    
    final totalCandleWidth = candleWidth + candleSpacing;
    final x = index * totalCandleWidth + totalCandleWidth / 2;
    final y = _priceToY(selectedData!.close, maxPrice, minPrice, chartHeight);
    
    final paint = Paint()
      ..color = Colors.grey
      ..strokeWidth = 0.5
      ..style = PaintingStyle.stroke;
      
    // Vertical line
    canvas.drawLine(Offset(x, 0), Offset(x, chartHeight), paint);
    
    // Horizontal line
    canvas.drawLine(Offset(0, y), Offset(chartWidth, y), paint);
    
    // Price label
    final text = selectedData!.close.toStringAsFixed(2);
    final textStyle = TextStyle(color: Colors.white, fontSize: 10, backgroundColor: Colors.black);
    final textSpan = TextSpan(text: text, style: textStyle);
    final textPainter = TextPainter(text: textSpan, textDirection: TextDirection.ltr);
    textPainter.layout();
    
    textPainter.paint(canvas, Offset(chartWidth + 2, y - textPainter.height / 2));
  }

  void _drawOperationLabels(
    Canvas canvas,
    double chartWidth,
    double chartHeight,
    double maxPrice,
    double minPrice,
    List<StockData> visibleData,
    double candleWidth,
    double candleSpacing,
  ) {
    if (operations.isEmpty) return;

    final totalCandleWidth = candleWidth + candleSpacing;
    final availableWidth = chartWidth;
    final numCandles = (availableWidth / totalCandleWidth).floor();

    for (int i = 0; i < visibleData.length && i <= numCandles; i++) {
      final d = visibleData[i];
      // Find operations for this date
      // Comparing date part only
      final ops = operations.where((op) {
        return op.stockDate.year == d.date.year &&
               op.stockDate.month == d.date.month &&
               op.stockDate.day == d.date.day;
      }).toList();

      if (ops.isEmpty) continue;

      final x = i * totalCandleWidth + totalCandleWidth / 2;
      final highY = _priceToY(d.high, maxPrice, minPrice, chartHeight);
      
      for (var op in ops) {
        if (op.type == OperationType.buy) {
          _drawText(
            canvas,
            '买',
            Offset(x, highY - 15),
            fontSize: 10,
            color: Colors.red,
            fontWeight: FontWeight.bold,
            align: TextAlign.center,
          );
        } else if (op.type == OperationType.sell) {
          _drawText(
            canvas,
            '卖',
            Offset(x, highY - 15),
            fontSize: 10,
            color: Colors.green,
            fontWeight: FontWeight.bold,
            align: TextAlign.center,
          );
        }
      }
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
    double candleWidth,
    double candleSpacing,
  ) {
    final totalCandleWidth = candleWidth + candleSpacing;
    final availableWidth = chartWidth;
    final numCandles = (availableWidth / totalCandleWidth).ceil(); // Use ceil to fill edge

    for (int i = 0; i < visibleData.length && i <= numCandles; i++) {
      final d = visibleData[i];
      final x = i * totalCandleWidth + totalCandleWidth / 2;

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
    double candleWidth,
    double candleSpacing,
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
    final numCandles = (availableWidth / totalCandleWidth).ceil();

    final dateInterval = (numCandles / 6).ceil();

    for (int i = 0; i < visibleData.length && i <= numCandles; i += dateInterval) {
      // final d = visibleData[i];
      // final x = i * totalCandleWidth + candleSpacing / 2;

      // In double-blind training, we don't show specific dates
      // final dateStr = '${d.date.month}/${d.date.day}';
      // _drawText(
      //   canvas,
      //   dateStr,
      //   Offset(x - 15, chartHeight + 5),
      //   fontSize: 10,
      //   color: Colors.grey[600]!,
      // );
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
    FontWeight fontWeight = FontWeight.normal,
    TextAlign align = TextAlign.left,
  }) {
    final textStyle = TextStyle(color: color, fontSize: fontSize, fontWeight: fontWeight);
    final textSpan = TextSpan(text: text, style: textStyle);
    final textPainter = TextPainter(
      text: textSpan,
      textDirection: TextDirection.ltr,
      textAlign: align,
    );
    textPainter.layout();
    
    double dx = offset.dx;
    double dy = offset.dy;
    
    if (align == TextAlign.center) {
      dx -= textPainter.width / 2;
    } else if (align == TextAlign.right) {
      dx -= textPainter.width;
    }
    
    textPainter.paint(canvas, Offset(dx, dy));
  }

  @override
  bool shouldRepaint(covariant KLinePainter oldDelegate) {
    return oldDelegate.visibleStart != visibleStart ||
        oldDelegate.visibleEnd != visibleEnd ||
        oldDelegate.data != data ||
        oldDelegate.maxPrice != maxPrice ||
        oldDelegate.minPrice != minPrice ||
        oldDelegate.operations != operations;
  }
}
