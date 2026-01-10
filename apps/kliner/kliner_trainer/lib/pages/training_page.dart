import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/training_controller.dart';
import '../widgets/kline_chart_widget.dart';
import '../widgets/operation_panel_widget.dart';
import '../models/blind_test_session.dart';
import '../models/blind_test_config.dart';

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
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => _showModeDialog(),
          ),
        ],
      ),
      body: Obx(() {
        final session = controller.currentSession.value;
        
        if (controller.isLoading.value) {
          return const Center(child: CircularProgressIndicator());
        }
        
        if (session == null && !controller.isTrainingInProgress.value) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  'K线双盲训练系统',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: () => controller.startTraining(),
                  child: const Text('开始训练'),
                ),
              ],
            ),
          );
        }
        
        return Column(
          children: [
            _buildStatsBar(session),
            Expanded(
              child: Stack(
                children: [
                  Column(
                    children: [
                      Expanded(
                        flex: 8,
                        child: const KLineChartWidget(),
                      ),
                      const OperationPanelWidget(),
                    ],
                  ),
                  _buildCloseButton(),
                ],
              ),
            ),
            _buildControlButtons(),
          ],
        );
      }),
    );
  }
  
  Widget _buildStatsBar(BlindTestSession? session) {
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
                Obx(() => Text(
                  '收益率: ${controller.currentProfitPercent.value >= 0 ? "+" : ""}${controller.currentProfitPercent.value.toStringAsFixed(2)}%',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: controller.currentProfitPercent.value > 0 ? Colors.red :
                           controller.currentProfitPercent.value < 0 ? Colors.green :
                           Colors.grey,
                  ),
                )),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildCloseButton() {
    return Positioned(
      top: 12,
      right: 12,
      child: Obx(() {
        if (!controller.isTrainingInProgress.value) {
          return const SizedBox.shrink();
        }
        
        return IconButton(
          icon: const Icon(Icons.close, color: Colors.red),
          onPressed: () => controller.endTraining(),
          tooltip: '关闭',
        );
      }),
    );
  }
  
  Widget _buildControlButtons() {
    return Container(
      padding: const EdgeInsets.all(12),
      child: Obx(() {
        if (!controller.isTrainingInProgress.value) {
          return const SizedBox.shrink();
        }
        
        return Row(
          children: [
            Expanded(
              child: ElevatedButton(
                onPressed: () => controller.endTraining(),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                ),
                child: const Text('结束训练'),
              ),
            ),
          ],
        );
      }),
    );
  }
  
  void _showModeDialog() {
    Get.dialog(
      AlertDialog(
        title: const Text('选择难度模式'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              title: const Text('初学者模式'),
              subtitle: const Text('显示全部指标\n60天数据'),
              onTap: () {
                controller.changeMode(BlindTestMode.beginner);
                Get.back();
              },
            ),
            const Divider(),
            ListTile(
              title: const Text('中级模式'),
              subtitle: const Text('隐藏成交量指标\n40天数据'),
              onTap: () {
                controller.changeMode(BlindTestMode.intermediate);
                Get.back();
              },
            ),
            const Divider(),
            ListTile(
              title: const Text('高级模式'),
              subtitle: const Text('只显示K线\n30天数据'),
              onTap: () {
                controller.changeMode(BlindTestMode.advanced);
                Get.back();
              },
            ),
            const Divider(),
            ListTile(
              title: const Text('大师模式'),
              subtitle: const Text('完全双盲\n20天数据'),
              onTap: () {
                controller.changeMode(BlindTestMode.master);
                Get.back();
              },
            ),
          ],
        ),
      ),
    );
  }
}
