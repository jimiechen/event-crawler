import 'package:flutter/material.dart';
import '../../models/stock_data.dart';

class VolumePainter extends CustomPainter {
  final List<StockData> data;
  final int visibleStart;
  final int visibleEnd;
  final double candleWidth;
  final double candleSpacing;
  final double paddingRight;
  final double paddingBottom;
  final bool showVolumeMA5;
  final bool showVolumeMA60;
  final bool showLowVolumeAlert;

  VolumePainter({
    required this.data,
    this.visibleStart = 0,
    this.visibleEnd = 60,
    this.candleWidth = 8.0,
    this.candleSpacing = 4.0,
    this.paddingRight = 60.0,
    this.paddingBottom = 30.0,
    this.showVolumeMA5 = true,
    this.showVolumeMA60 = true,
    this.showLowVolumeAlert = true,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty || visibleStart >= data.length) return;

    final visibleData = _getVisibleData();
    if (visibleData.isEmpty) return;

    final chartWidth = size.width - paddingRight;
    final chartHeight = size.height - paddingBottom;

    final volumeRange = _calculateVolumeRange(visibleData);
    final maxVolume = volumeRange['max']!;

    _drawVolumeBars(canvas, chartWidth, chartHeight, maxVolume, visibleData);

    if (showVolumeMA5) {
      _drawVolumeMALine(canvas, chartWidth, chartHeight, maxVolume, visibleData, Colors.blue, 'volumeMa5');
    }

    if (showVolumeMA60) {
      _drawVolumeMALine(canvas, chartWidth, chartHeight, maxVolume, visibleData, Colors.orange, 'volumeMa60');
    }

    _drawVolumeAxis(canvas, size, chartHeight, maxVolume);
  }

  List<StockData> _getVisibleData() {
    final end = visibleEnd < data.length ? visibleEnd : data.length;
    return data.sublist(visibleStart, end);
  }

  Map<String, double> _calculateVolumeRange(List<StockData> visibleData) {
    double maxVolume = visibleData.map((d) => d.volume).reduce((a, b) => a > b ? a : b);
    maxVolume *= 1.1;

    return {'max': maxVolume};
  }

  void _drawVolumeBars(
    Canvas canvas,
    double chartWidth,
    double chartHeight,
    double maxVolume,
    List<StockData> visibleData,
  ) {
    final totalCandleWidth = candleWidth + candleSpacing;
    final availableWidth = chartWidth;
    final numCandles = (availableWidth / totalCandleWidth).floor();

    for (int i = 0; i < visibleData.length && i < numCandles; i++) {
      final d = visibleData[i];
      final x = i * totalCandleWidth + candleSpacing / 2;

      final barHeight = (d.volume / maxVolume) * chartHeight;
      final y = chartHeight - barHeight;

      final isBull = d.close >= d.open;
      final barPaint = Paint()
        ..color = isBull ? Colors.red.withOpacity(0.6) : Colors.green.withOpacity(0.6)
        ..style = PaintingStyle.fill;

      if (showLowVolumeAlert && d.isLowVolume) {
        barPaint.color = Colors.blue.withOpacity(0.8);
      }

      canvas.drawRect(
        Rect.fromLTRB(
          x - candleWidth / 2,
          y,
          x + candleWidth / 2,
          chartHeight,
        ),
        barPaint,
      );
    }
  }

  void _drawVolumeMALine(
    Canvas canvas,
    double chartWidth,
    double chartHeight,
    double maxVolume,
    List<StockData> visibleData,
    Color color,
    String maType,
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

      double maValue;
      if (maType == 'volumeMa5') {
        maValue = d.volumeMa5;
      } else {
        maValue = d.volumeMa60;
      }

      if (maValue > 0) {
        final y = chartHeight - (maValue / maxVolume) * chartHeight;
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
        ..strokeWidth = 1.5
        ..style = PaintingStyle.stroke;

      canvas.drawPath(path, paint);
    }
  }

  void _drawVolumeAxis(
    Canvas canvas,
    Size size,
    double chartHeight,
    double maxVolume,
  ) {
    final axisPaint = Paint()
      ..color = const Color(0xFFBDBDBD)
      ..strokeWidth = 1.0;

    canvas.drawLine(
      Offset(size.width - paddingRight, 0),
      Offset(size.width - paddingRight, chartHeight),
      axisPaint,
    );

    final horizontalLines = 3;
    for (int i = 0; i <= horizontalLines; i++) {
      final y = (chartHeight / horizontalLines) * i;
      final volume = maxVolume * (horizontalLines - i) / horizontalLines;
      _drawText(
        canvas,
        _formatVolume(volume),
        Offset(size.width - paddingRight + 5, y - 6),
        fontSize: 9,
        color: Colors.grey[600]!,
      );
    }
  }

  String _formatVolume(double volume) {
    if (volume >= 10000) {
      return '${(volume / 10000).toStringAsFixed(1)}万';
    }
    return volume.toStringAsFixed(0);
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
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
