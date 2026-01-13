import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../models/operation_record.dart';
import '../controllers/training_controller.dart';

class DesktopOperationPanel extends GetView<TrainingController> {
  const DesktopOperationPanel({super.key});

  // Reusing static state from OperationPanelWidget might be tricky if both exist, 
  // but usually only one is shown. Or better, move this state to Controller.
  // For now, let's keep local state or use the same static ones if they are not bound to widget instance.
  // OperationPanelWidget.pendingOperation is static Rx. We can use it.
  
  // Actually, let's just duplicate the state logic here for simplicity or reference the static one.
  // Referencing OperationPanelWidget.pendingOperation is okay if we import it.
  // But to avoid dependency on the mobile widget, let's add these to Controller or just use local Rx here.
  // Using local Rx here means if we switch layouts, state is lost. But layout switch usually happens on resize/init.
  
  static final Rx<OperationType?> pendingOperation = Rx<OperationType?>(null);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 200,
      padding: const EdgeInsets.all(16),
      color: const Color(0xFF1E1E1E), // Dark theme
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Left: Info & Stats
          Expanded(
            flex: 2,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildStatsBar(),
                const SizedBox(height: 12),
                Expanded(child: _buildCrosshairInfo()),
              ],
            ),
          ),
          const VerticalDivider(color: Colors.white24),
          // Middle: Operation History (Recent)
          Expanded(
            flex: 2,
            child: _buildOperationList(),
          ),
          const VerticalDivider(color: Colors.white24),
          // Right: Controls (Buttons)
          SizedBox(
            width: 300,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Obx(() {
                  if (pendingOperation.value != null) {
                    return _buildPositionSelector(pendingOperation.value!);
                  }
                  return _buildOperationButtons();
                }),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsBar() {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: [
        _buildStatItem('当前资金', controller.totalCapital.toStringAsFixed(0), Colors.white),
        Obx(() => _buildStatItem(
          '当前仓位',
          '${controller.currentPositionRatio.toStringAsFixed(1)}%',
          Colors.blueAccent,
        )),
        Obx(() => _buildStatItem(
          '收益率',
          '${controller.currentProfitPercent.value >= 0 ? "+" : ""}${controller.currentProfitPercent.value.toStringAsFixed(2)}%',
          controller.currentProfitPercent.value > 0 ? Colors.redAccent :
          controller.currentProfitPercent.value < 0 ? Colors.greenAccent :
          Colors.white70,
        )),
      ],
    );
  }

  Widget _buildStatItem(String label, String value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }

  Widget _buildCrosshairInfo() {
    return Obx(() {
      final data = controller.selectedData.value;
      if (data == null) return const Center(child: Text('移动鼠标查看K线详情', style: TextStyle(color: Colors.grey)));
      
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildInfoItem('开盘', data.open, data.isBullish ? Colors.redAccent : Colors.greenAccent),
              _buildInfoItem('收盘', data.close, data.isBullish ? Colors.redAccent : Colors.greenAccent),
              _buildInfoItem('最高', data.high, Colors.redAccent),
              _buildInfoItem('最低', data.low, Colors.greenAccent),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildInfoItem('涨幅', data.changePercent, data.changePercent >= 0 ? Colors.redAccent : Colors.greenAccent, suffix: '%'),
              _buildInfoItem('成交量', data.volume / 100, Colors.white, suffix: '手'),
              _buildInfoItem('EXPMA5', data.expma5, Colors.blueAccent),
              _buildInfoItem('EXPMA13', data.expma13, Colors.purpleAccent),
            ],
          ),
        ],
      );
    });
  }

  Widget _buildInfoItem(String label, double value, Color color, {String suffix = ''}) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey)),
        Text(
          '${value.toStringAsFixed(2)}$suffix',
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color),
        ),
      ],
    );
  }

  Widget _buildOperationList() {
    return Obx(() {
      final isDaily = controller.selectedDate.value != null;
      final operations = isDaily ? controller.dailyOperations : controller.allOperations;
      
      if (operations.isEmpty) {
        return Center(
          child: Text(
            isDaily ? '该日无操作' : '暂无操作记录', 
            style: const TextStyle(color: Colors.grey)
          )
        );
      }
      
      return ListView.separated(
        itemCount: operations.length,
        separatorBuilder: (_, __) => const Divider(height: 1, color: Colors.white10),
        itemBuilder: (context, index) {
          // If daily, show natural order? Or reversed? Usually reversed (newest first).
          // allOperations is appended, so latest is last.
          // dailyOperations is filtered from allOperations, so latest is also last.
          final op = operations[operations.length - 1 - index];
          final isBuy = op.type == OperationType.buy;
          final isSell = op.type == OperationType.sell;
          final color = isBuy ? Colors.redAccent : (isSell ? Colors.greenAccent : Colors.grey);
          final typeText = isBuy ? '买入' : (isSell ? '卖出' : '观望');
          
          return ListTile(
            dense: true,
            visualDensity: VisualDensity.compact,
            title: Text(
              // Show time for daily, or index for all
              isDaily 
                ? '${op.timestamp.hour}:${op.timestamp.minute.toString().padLeft(2,'0')} $typeText'
                : '第${operations.length - index}次操作 $typeText',
              style: TextStyle(color: color, fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              '价格: ${op.price.toStringAsFixed(2)}  盈亏: ${op.profit != null ? op.profit!.toStringAsFixed(0) : "--"}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
            trailing: Text(
              op.positionLevel == 10 ? "满仓" : "${op.positionLevel}成",
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          );
        },
      );
    });
  }

  Widget _buildOperationButtons() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: _buildOperationButton(
                OperationType.buy,
                Colors.green,
                '买入',
                Icons.arrow_upward,
                onTap: () => pendingOperation.value = OperationType.buy,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildOperationButton(
                OperationType.hold,
                Colors.orange,
                '观望',
                Icons.pause,
                onTap: () => controller.skipDay(),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildOperationButton(
                OperationType.sell,
                Colors.red,
                '卖出',
                Icons.arrow_downward,
                onTap: () => pendingOperation.value = OperationType.sell,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.white10,
            foregroundColor: Colors.redAccent,
            elevation: 0,
            padding: const EdgeInsets.symmetric(vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(4),
              side: BorderSide(color: Colors.redAccent.withOpacity(0.5)),
            ),
          ),
          onPressed: () => _showEndTrainingConfirmation(),
          child: const Text('结束本次训练'),
        ),
      ],
    );
  }
  
  void _showEndTrainingConfirmation() {
    Get.dialog(
      AlertDialog(
        backgroundColor: const Color(0xFF2E2E2E),
        title: const Text('结束训练', style: TextStyle(color: Colors.white)),
        content: const Text('确定要结束当前训练吗？将进行最终结算。', style: TextStyle(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('取消', style: TextStyle(color: Colors.white54)),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: Colors.redAccent),
            onPressed: () {
              Get.back();
              controller.endTraining(userAborted: true);
            },
            child: const Text('结束'),
          ),
        ],
      ),
    );
  }

  Widget _buildOperationButton(
    OperationType type,
    Color color,
    String label,
    IconData icon,
    {required VoidCallback onTap}
  ) {
    return ElevatedButton.icon(
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(vertical: 20),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      onPressed: onTap,
      icon: Icon(icon, size: 20),
      label: Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildPositionSelector(OperationType type) {
    final isBuy = type == OperationType.buy;
    final color = isBuy ? Colors.green : Colors.red;
    
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('仓位', style: TextStyle(color: color, fontWeight: FontWeight.bold)),
            IconButton(
              icon: const Icon(Icons.close, color: Colors.white),
              onPressed: () => pendingOperation.value = null,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            _buildPositionButton(1, '1成', color, type),
            const SizedBox(width: 8),
            _buildPositionButton(3, '3成', color, type),
            const SizedBox(width: 8),
            _buildPositionButton(5, '5成', color, type),
            const SizedBox(width: 8),
            _buildPositionButton(10, type == OperationType.buy ? '满仓' : '空仓', color, type, isFull: true),
          ],
        ),
      ],
    );
  }

  Widget _buildPositionButton(int level, String text, Color color, OperationType type, {bool isFull = false}) {
    return Expanded(
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: color,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 12),
          elevation: isFull ? 4 : 2,
        ),
        onPressed: () {
          controller.positionLevel.value = level;
          controller.executeUserOperation(type, '');
          pendingOperation.value = null;
        },
        child: Text(text, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
      ),
    );
  }
}
