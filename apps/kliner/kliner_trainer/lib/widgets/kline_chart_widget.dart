import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../models/stock_data.dart';
import '../models/blind_test_session.dart';
import '../controllers/training_controller.dart';
import 'painters/kline_painter.dart';
import 'painters/expma_painter.dart';
import 'painters/volume_painter.dart';
import 'overlays/crosshair_overlay.dart';
import 'overlays/tooltip_overlay.dart';

class KLineChartWidget extends GetView<TrainingController> {
  const KLineChartWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final session = controller.currentSession.value;
      if (session == null) {
        return const Center(child: CircularProgressIndicator());
      }

      return Expanded(
        flex: 4,
        child: Column(
          children: [
            _buildStatsBar(session),
            Expanded(
              flex: 7,
              child: _KLineChartContent(session: session),
            ),
            Expanded(
              flex: 3,
              child: _VolumeChartContent(session: session),
            ),
          ],
        ),
      );
    });
  }

  Widget _buildStatsBar(BlindTestSession session) {
    final config = controller.currentConfig.value;

    return Container(
      padding: const EdgeInsets.all(12),
      color: Colors.grey[100],
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (config.showCurrentPrice)
                Text(
                  '当前价格: ${session.currentPrice.toStringAsFixed(2)}',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              if (config.showCurrentPrice)
                Text(
                  '涨跌幅: ${session.changePercent.toStringAsFixed(2)}%',
                  style: TextStyle(
                    fontSize: 14,
                    color: session.changePercent >= 0 ? Colors.red : Colors.green,
                  ),
                ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (config.showExpma)
                const Text(
                  '技术指标:',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              if (config.showExpma)
                Row(
                  children: [
                    const Text(
                      'EXPMA5: ',
                      style: TextStyle(fontSize: 12),
                    ),
                    Text(
                      session.data.last.expma5.toStringAsFixed(2),
                      style: const TextStyle(fontSize: 12, color: Colors.yellow),
                    ),
                    const SizedBox(width: 8),
                    const Text(
                      'EXPMA13: ',
                      style: TextStyle(fontSize: 12),
                    ),
                    Text(
                      session.data.last.expma13.toStringAsFixed(2),
                      style: const TextStyle(fontSize: 12, color: Colors.purple),
                    ),
                  ],
                ),
              if (config.showLowVolumeAlert && session.data.last.isLowVolume)
                const Text(
                  '地量信号',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.blue,
                    fontWeight: FontWeight.bold,
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _KLineChartContent extends StatefulWidget {
  final BlindTestSession session;

  const _KLineChartContent({required this.session});

  @override
  State<_KLineChartContent> createState() => _KLineChartContentState();
}

class _KLineChartContentState extends State<_KLineChartContent> {
  int visibleStart = 0;
  int visibleEnd = 60;
  double scale = 1.0;
  Offset? tapPosition;
  StockData? selectedData;
  int visibleCount = 60;

  TrainingController get controller => Get.find<TrainingController>();

  @override
  Widget build(BuildContext context) {
    final data = widget.session.data;
    final config = controller.currentConfig.value;
    
    final adjustedVisibleEnd = (visibleStart + (visibleEnd - visibleStart) / scale).round();
    final end = adjustedVisibleEnd < data.length ? adjustedVisibleEnd : data.length;
    
    final visibleData = data.sublist(visibleStart, end);
    final priceRange = _calculatePriceRange(visibleData);
    final maxPrice = priceRange['max']!;
    final minPrice = priceRange['min']!;

    return GestureDetector(
      onHorizontalDragUpdate: (details) {
        final delta = details.primaryDelta ?? 0;
        final shift = (delta / 10).toInt();
        setState(() {
          visibleStart = (visibleStart - shift).clamp(0, data.length - 10);
          visibleEnd = (visibleEnd - shift).clamp(10, data.length);
        });
      },
      onScaleUpdate: (details) {
        if (details.scale != 1.0) {
          setState(() {
            final newVisibleCount = (visibleCount / details.scale).clamp(10, 30);
            visibleCount = newVisibleCount.toInt();
            final diff = newVisibleCount - (visibleEnd - visibleStart);
            visibleEnd = (visibleEnd + diff).clamp(10, data.length).toInt();
          });
        }
      },
      onLongPressStart: (details) {
        setState(() {
          tapPosition = details.localPosition;
          selectedData = _findNearestData(details.localPosition, visibleData);
        });
      },
      onLongPressEnd: (details) {
        setState(() {
          tapPosition = null;
          selectedData = null;
        });
      },
      onTapDown: (details) {
        setState(() {
          tapPosition = details.localPosition;
          selectedData = _findNearestData(details.localPosition, visibleData);
        });
      },
      onTapUp: (details) {
        setState(() {
          tapPosition = null;
          selectedData = null;
        });
      },
      child: Stack(
        children: [
          Container(
            color: Colors.white,
            child: CustomPaint(
              size: Size.infinite,
              painter: KLinePainter(
                data: data,
                visibleStart: visibleStart,
                visibleEnd: end,
              ),
              foregroundPainter: config.showExpma ? ExpmaPainter(
                data: data,
                visibleStart: visibleStart,
                visibleEnd: end,
                showExpma5: config.showExpma,
                showExpma13: config.showExpma,
              ) : null,
            ),
          ),
          if (tapPosition != null && selectedData != null)
            CrosshairOverlay(
              data: selectedData!,
              position: tapPosition!,
              chartWidth: MediaQuery.of(context).size.width - 60,
              chartHeight: MediaQuery.of(context).size.height * 0.7 * 0.7 - 30,
              maxPrice: maxPrice,
              minPrice: minPrice,
            ),
          if (tapPosition != null && selectedData != null)
            TooltipOverlay(
              data: selectedData!,
              position: tapPosition!,
              chartWidth: MediaQuery.of(context).size.width - 60,
              chartHeight: MediaQuery.of(context).size.height * 0.7 * 0.7 - 30,
            ),
          Positioned(
            left: 10,
            bottom: 10,
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.chevron_left, color: Colors.blue),
                  onPressed: () {
                    setState(() {
                      final shift = visibleCount;
                      visibleStart = (visibleStart - shift).clamp(0, data.length - 10);
                      visibleEnd = (visibleEnd - shift).clamp(10, data.length);
                    });
                  },
                  tooltip: '上一日',
                ),
                IconButton(
                  icon: const Icon(Icons.chevron_right, color: Colors.blue),
                  onPressed: () {
                    setState(() {
                      final shift = visibleCount;
                      visibleStart = (visibleStart + shift).clamp(0, data.length - 10);
                      visibleEnd = (visibleEnd + shift).clamp(10, data.length);
                    });
                  },
                  tooltip: '下一日',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Map<String, double> _calculatePriceRange(List<StockData> visibleData) {
    double maxPrice = visibleData.map((d) => d.high).reduce((a, b) => a > b ? a : b);
    double minPrice = visibleData.map((d) => d.low).reduce((a, b) => a < b ? a : b);

    final range = maxPrice - minPrice;
    maxPrice += range * 0.05;
    minPrice -= range * 0.05;

    return {'max': maxPrice, 'min': minPrice};
  }

  StockData? _findNearestData(Offset position, List<StockData> visibleData) {
    if (visibleData.isEmpty) return null;

    final totalCandleWidth = 8.0 + 4.0;
    final index = (position.dx / totalCandleWidth).round().clamp(0, visibleData.length - 1);

    return visibleData[index];
  }
}

class _VolumeChartContent extends StatelessWidget {
  final BlindTestSession session;

  const _VolumeChartContent({required this.session});

  @override
  Widget build(BuildContext context) {
    final data = session.data;
    final TrainingController controller = Get.find<TrainingController>();
    final config = controller.currentConfig.value;
    
    final visibleStart = 0;
    final visibleEnd = data.length < 60 ? data.length : 60;

    return Container(
      color: Colors.grey[50],
      child: CustomPaint(
        size: Size.infinite,
        painter: VolumePainter(
          data: data,
          visibleStart: visibleStart,
          visibleEnd: visibleEnd,
          showVolumeMA5: config.showVolumeMA,
          showVolumeMA60: config.showVolumeMA,
          showLowVolumeAlert: config.showLowVolumeAlert,
        ),
      ),
    );
  }
}
