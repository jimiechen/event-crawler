import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/training_controller.dart';
import '../widgets/kline_chart_widget.dart';
import '../widgets/operation_panel_widget.dart';
import '../models/blind_test_session.dart';

class TrainingPage extends GetView<TrainingController> {
  const TrainingPage({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('K线双盲训练'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 1,
      ),
      body: Obx(() {
        final session = controller.currentSession.value;
        
        if (controller.isLoading.value) {
          return const Center(child: CircularProgressIndicator());
        }
        
        if (session == null) {
          return const Center(child: Text('加载中...'));
        }
        
        return Column(
          children: [
            _buildStatsBar(session),
            Expanded(
              child: Column(
                children: [
                  Expanded(
                    flex: 4,
                    child: const KLineChartWidget(),
                  ),
                  const OperationPanelWidget(),
                ],
              ),
            ),
          ],
        );
      }),
    );
  }
  
  Widget _buildStatsBar(BlindTestSession session) {
    return Container(
      padding: const EdgeInsets.all(12),
      color: Colors.grey[100],
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Obx(() => Text(
                  '训练次数: ${controller.sessionCount.value}',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                )),
                Obx(() => Text(
                  '得分: ${controller.score.value}',
                  style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.red),
                )),
              ],
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Obx(() => Text(
                  '当前资金: ${controller.totalCapital.value.toStringAsFixed(0)}元',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                )),
                Obx(() => Text(
                  '持仓市值: ${controller.currentPositionValue.value.toStringAsFixed(0)}元',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                )),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
