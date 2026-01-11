import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../models/stock_data.dart';
import '../models/blind_test_session.dart';
import '../controllers/training_controller.dart';
import 'painters/kline_painter.dart';
import 'painters/expma_painter.dart';
import 'painters/volume_painter.dart';
// import 'overlays/crosshair_overlay.dart';
// import 'overlays/tooltip_overlay.dart'; // 已移除，改为在操作面板显示

class KLineChartWidget extends GetView<TrainingController> {
  const KLineChartWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final session = controller.currentSession.value;
      if (session == null) {
        return const Center(child: CircularProgressIndicator());
      }

      return Column(
        children: [
          Expanded(
            flex: 7,
            child: ClipRect(
              child: _KLineChartContent(session: session),
            ),
          ),
          Expanded(
            flex: 3,
            child: ClipRect(
              child: _VolumeChartContent(session: session),
            ),
          ),
        ],
      );
    });
  }

}

class _KLineChartContent extends StatefulWidget {
  final BlindTestSession session;

  const _KLineChartContent({required this.session});

  @override
  State<_KLineChartContent> createState() => _KLineChartContentState();
}

class _KLineChartContentState extends State<_KLineChartContent> {
  final RxDouble _scale = 1.0.obs;
  final RxDouble _lastScale = 1.0.obs;
  Offset? tapPosition;
  StockData? selectedData;

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<TrainingController>();

    return Obx(() {
      final session = controller.currentSession.value;
      if (session == null) return const Center(child: Text('准备数据中...'));

      final data = session.data;
      if (data.isEmpty) return const Center(child: Text('无数据'));

      final visibleStart = 0;
      final visibleCount = data.length;
      final end = visibleStart + visibleCount;

      final priceRange = _calculatePriceRange(data);
      final maxPrice = priceRange['max']!;
      final minPrice = priceRange['min']!;
      
      final config = controller.currentConfig.value;
      final selectedData = controller.selectedData.value;

      return LayoutBuilder(
        builder: (context, constraints) {
          return GestureDetector(
            onScaleStart: (details) {
              _lastScale.value = _scale.value;
              controller.startZoom();
            },
            onScaleUpdate: (details) {
              // 缩放处理
              if (details.scale != 1.0) {
                // 直接传递缩放比例给controller，实现平滑缩放
                controller.handleZoom(details.scale);
              }
            },
            // 使用长按来触发十字光标，避免与缩放冲突
            onLongPressStart: (details) {
              final renderBox = context.findRenderObject() as RenderBox;
              final localPosition = renderBox.globalToLocal(details.globalPosition);
              
              final data = _findNearestData(localPosition, session.data, constraints.maxWidth);
              controller.selectedData.value = data;
            },
            onLongPressMoveUpdate: (details) {
              final renderBox = context.findRenderObject() as RenderBox;
              final localPosition = renderBox.globalToLocal(details.globalPosition);
              
              final data = _findNearestData(localPosition, session.data, constraints.maxWidth);
              controller.selectedData.value = data;
            },
            onTapDown: (details) {
              // 点击也能触发/移动光标
              final renderBox = context.findRenderObject() as RenderBox;
              final localPosition = renderBox.globalToLocal(details.globalPosition);
              
              final data = _findNearestData(localPosition, session.data, constraints.maxWidth);
              controller.selectedData.value = data;
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
                      maxPrice: maxPrice,
                      minPrice: minPrice,
                      operations: controller.allOperations,
                      selectedData: selectedData,
                    ),
                    foregroundPainter: config.showExpma ? ExpmaPainter(
                      data: data,
                      visibleStart: visibleStart,
                      visibleEnd: end,
                      showExpma5: config.showExpma,
                      showExpma13: config.showExpma,
                      maxPrice: maxPrice,
                      minPrice: minPrice,
                    ) : null,
                  ),
                ),
                // Positioned controls
                Positioned(
                  bottom: 10,
                  left: 10,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.6),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _buildControlBtn(Icons.zoom_in, () => controller.zoomIn()),
                        _buildControlBtn(Icons.zoom_out, () => controller.zoomOut()),
                        Container(width: 1, height: 16, color: Colors.white30, margin: const EdgeInsets.symmetric(horizontal: 4)),
                        _buildControlBtn(Icons.chevron_left, () => controller.scrollLeft()),
                        _buildControlBtn(Icons.chevron_right, () => controller.scrollRight()),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      );
    });
  }

  Widget _buildControlBtn(IconData icon, VoidCallback onTap) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.all(4),
          child: Icon(icon, color: Colors.white, size: 20),
        ),
      ),
    );
  }

  Map<String, double> _calculatePriceRange(List<StockData> visibleData) {
    if (visibleData.isEmpty) return {'max': 0, 'min': 0};
    double maxPrice = visibleData.map((d) => d.high).reduce((a, b) => a > b ? a : b);
    double minPrice = visibleData.map((d) => d.low).reduce((a, b) => a < b ? a : b);

    final range = maxPrice - minPrice;
    maxPrice += range * 0.05;
    minPrice -= range * 0.05;

    return {'max': maxPrice, 'min': minPrice};
  }

  StockData? _findNearestData(Offset position, List<StockData> visibleData, double chartWidth) {
    if (visibleData.isEmpty) return null;

    final count = visibleData.length;
    final totalCandleWidth = chartWidth / count;
    final index = (position.dx / totalCandleWidth).floor().clamp(0, visibleData.length - 1);

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
    
    const visibleStart = 0;
    final visibleEnd = data.length;

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
