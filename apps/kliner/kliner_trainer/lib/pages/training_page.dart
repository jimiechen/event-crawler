import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/training_controller.dart';
import '../widgets/kline_chart_widget.dart';
import '../widgets/operation_panel_widget.dart';
import '../widgets/desktop_layout_widget.dart';
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
          // Only show calendar button on mobile/tablet, as desktop has it in sidebar
          if (MediaQuery.of(context).size.width <= 800)
            IconButton(
              icon: const Icon(Icons.calendar_today),
              onPressed: () => _showCalendarDialog(),
            ),
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
          // Empty state - show start button
          // For desktop, we might want to show the full layout with empty chart or a welcome screen
          // But reusing the simple start screen is fine for now.
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
        
        // Responsive Layout
        if (MediaQuery.of(context).size.width > 800) {
          return const DesktopLayoutWidget();
        }
        
        return Column(
          children: [
            Expanded(
              flex: 6,
              child: const KLineChartWidget(),
            ),
            const OperationPanelWidget(),
          ],
        );
      }),
    );
  }
  
  // ignore: unused_element
  Widget _buildStatsBar(BlindTestSession? session) {
    return Container(
      // ... (stats bar implementation)
      child: const SizedBox.shrink(),
    );
  }
  
  // ignore: unused_element
  Widget _buildCloseButton() {
    // ...
    return const SizedBox.shrink();
  }
  
  // ignore: unused_element
  Widget _buildControlButtons() {
    // ...
    return const SizedBox.shrink();
  }
  
  void _showCalendarDialog() {
    final now = DateTime.now();
    final daysInMonth = DateUtils.getDaysInMonth(now.year, now.month);
    final firstDayOfMonth = DateTime(now.year, now.month, 1);
    final firstWeekday = firstDayOfMonth.weekday; // 1=Mon, 7=Sun
    
    Get.dialog(
      Dialog(
        child: Container(
          padding: const EdgeInsets.all(16),
          height: 450,
          width: 350,
          child: Column(
            children: [
              Text('${now.year}年${now.month}月 训练日历', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              // Weekday headers
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: const [
                  Text('一'), Text('二'), Text('三'), Text('四'), Text('五'), Text('六'), Text('日'),
                ],
              ),
              const SizedBox(height: 8),
              Expanded(
                child: GridView.builder(
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 7,
                    childAspectRatio: 1,
                  ),
                  itemCount: daysInMonth + firstWeekday - 1,
                  itemBuilder: (context, index) {
                    if (index < firstWeekday - 1) {
                      return const SizedBox.shrink();
                    }
                    
                    final dayIndex = index - (firstWeekday - 1);
                    final date = DateTime(now.year, now.month, dayIndex + 1);
                    final rounds = controller.storageService.getDailyRounds(date);
                    final isTargetMet = rounds >= 10;
                    
                    // Logic for red/green dot:
                    // Only show dots for today or past days (or if there is training data)
                    // If rounds == 0 and date is today/future, maybe show nothing or grey?
                    // User said: "Have training -> Green dot, No training -> Red dot". 
                    // Assuming "No training" means "Target not met" or "0 rounds"? 
                    // "Daily need 1 training (10 rounds)".
                    // Let's interpret: < 10 -> Red, >= 10 -> Green.
                    // Only for days <= today.
                    
                    final isFuture = date.isAfter(now);
                    final isToday = date.year == now.year && date.month == now.month && date.day == now.day;
                    
                    Color? dotColor;
                    if (!isFuture || isToday) {
                      dotColor = isTargetMet ? Colors.green : Colors.red;
                    }
                    
                    return Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('${dayIndex + 1}', style: TextStyle(
                          fontWeight: isToday ? FontWeight.bold : FontWeight.normal,
                          color: isToday ? Colors.blue : Colors.black,
                        )),
                        const SizedBox(height: 4),
                        if (dotColor != null)
                          Container(
                            width: 6,
                            height: 6,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: dotColor,
                            ),
                          ),
                      ],
                    );
                  },
                ),
              ),
              const Divider(),
              // Force update using Obx/GetBuilder if storage updates don't trigger rebuild
              // But storage is simple map. We might need Obx if we want real-time update.
              // For dialog, it rebuilds on open.
              Text('今日进度: ${controller.storageService.getDailyRounds(now)}/10 轮'),
              const SizedBox(height: 8),
              const Text('每日需完成10轮双盲训练', style: TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
        ),
      ),
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
