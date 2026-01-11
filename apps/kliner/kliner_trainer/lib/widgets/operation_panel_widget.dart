import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../models/operation_record.dart';
import '../controllers/training_controller.dart';

class OperationPanelWidget extends GetView<TrainingController> {
  const OperationPanelWidget({super.key});

  // 使用本地状态来管理当前的待定操作（买入/卖出）
  static final Rx<OperationType?> pendingOperation = Rx<OperationType?>(null);
  // 控制操作提示的显示
  static final RxBool showQuickTips = true.obs;
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildOperationList(),
            const SizedBox(height: 16),
            _buildCrosshairInfo(),
            const SizedBox(height: 8),
            _buildLastOperationSummary(),
            const SizedBox(height: 8),
            Obx(() => showQuickTips.value ? _buildQuickTips() : const SizedBox.shrink()),
            const SizedBox(height: 16),
            Obx(() {
              // 如果有待定的买入/卖出操作，显示仓位选择器
              if (pendingOperation.value != null) {
                return _buildPositionSelector(pendingOperation.value!);
              }
              // 否则显示主操作按钮
              return _buildOperationButtons();
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildOperationList() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _buildStatsBar(),
        const SizedBox(height: 8),
        Obx(() {
          final isDaily = controller.selectedDate.value != null;
          final operations = isDaily ? controller.dailyOperations : controller.allOperations;
          
          if (operations.isEmpty) {
            return isDaily 
                ? const Center(child: Padding(
                    padding: EdgeInsets.all(8.0),
                    child: Text('该日无操作', style: TextStyle(color: Colors.grey)),
                  ))
                : const SizedBox.shrink();
          }
          
          return Container(
            height: 120,
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey[300]!),
              borderRadius: BorderRadius.circular(4),
            ),
            child: ListView.separated(
              itemCount: operations.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, index) {
                // 显示最新的在最上面
                final op = operations[operations.length - 1 - index];
                final isBuy = op.type == OperationType.buy;
                final isSell = op.type == OperationType.sell;
                final color = isBuy ? Colors.red : (isSell ? Colors.green : Colors.grey);
                final typeText = isBuy ? '买入' : (isSell ? '卖出' : '观望');
                
                return ListTile(
                  dense: true,
                  visualDensity: VisualDensity.compact,
                  title: Text(
                    isDaily 
                        ? '${op.timestamp.hour}:${op.timestamp.minute.toString().padLeft(2,'0')} $typeText'
                        : '第${operations.length - index}次操作 $typeText',
                    style: TextStyle(color: color, fontWeight: FontWeight.bold),
                  ),
                  subtitle: Text(
                    '价格: ${op.price.toStringAsFixed(2)}  盈亏: ${op.profit != null ? op.profit!.toStringAsFixed(0) : "--"}',
                    style: const TextStyle(fontSize: 12),
                  ),
                  trailing: Text(
                    op.positionLevel == 10 ? "满仓" : "${op.positionLevel}成",
                    style: const TextStyle(fontSize: 12),
                  ),
                );
              },
            ),
          );
        }),
      ],
    );
  }

  Widget _buildStatsBar() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem(
            '当前资金',
            controller.totalCapital.toStringAsFixed(0),
            Colors.black,
          ),
          Obx(() => _buildStatItem(
            '当前仓位',
            '${controller.currentPositionRatio.toStringAsFixed(1)}%',
            Colors.blue,
          )),
          Obx(() => _buildStatItem(
            '收益率',
            '${controller.currentProfitPercent.value >= 0 ? "+" : ""}${controller.currentProfitPercent.value.toStringAsFixed(2)}%',
            controller.currentProfitPercent.value > 0 ? Colors.red :
            controller.currentProfitPercent.value < 0 ? Colors.green :
            Colors.grey,
          )),
        ],
      ),
    );
  }
  
  Widget _buildStatItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }

  Widget _buildLastOperationSummary() {
    return Obx(() {
      if (controller.allOperations.isEmpty) return const SizedBox.shrink();
      final lastOp = controller.allOperations.last;
      
      final isBuy = lastOp.type == OperationType.buy;
      final isSell = lastOp.type == OperationType.sell;
      final color = isBuy ? Colors.red : (isSell ? Colors.green : Colors.orange);
      final typeText = isBuy ? '买入' : (isSell ? '卖出' : '观望');
      
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('上一次操作简介', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(
              '$typeText @ ${lastOp.price.toStringAsFixed(2)} '
              '(${lastOp.stockDate.toString().split(' ')[0]})',
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
            ),
            if (lastOp.profit != null)
              Text(
                '${isSell ? "实现盈亏" : "浮动盈亏"}: ${lastOp.profit!.toStringAsFixed(2)}',
                 style: TextStyle(
                   fontSize: 13, 
                   color: lastOp.profit! >= 0 ? Colors.red : Colors.green,
                   fontWeight: FontWeight.bold
                 ),
              ),
          ],
        ),
      );
    });
  }

  Widget _buildCrosshairInfo() {
    return Obx(() {
      final data = controller.selectedData.value;
      if (data == null) return const SizedBox(height: 20); // 占位保持高度稳定
      
      return Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.grey[100],
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: Colors.grey[300]!),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Text('训练进度: 第${controller.visibleDataLength.value}天', style: const TextStyle(fontWeight: FontWeight.bold)),
            // const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildInfoItem('开盘', data.open, data.isBullish ? Colors.red : Colors.green),
                _buildInfoItem('收盘', data.close, data.isBullish ? Colors.red : Colors.green),
                _buildInfoItem('最高', data.high, Colors.red),
                _buildInfoItem('最低', data.low, Colors.green),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildInfoItem('涨幅', data.changePercent, data.changePercent >= 0 ? Colors.red : Colors.green, suffix: '%'),
                _buildInfoItem('成交量', data.volume / 100, Colors.black, suffix: '手'), // 显示为手
                _buildInfoItem('EXPMA5', data.expma5, Colors.blue),
                _buildInfoItem('EXPMA13', data.expma13, Colors.purple),
              ],
            ),
          ],
        ),
      );
    });
  }

  Widget _buildInfoItem(String label, double value, Color color, {String suffix = ''}) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey)),
        Text(
          '${value.toStringAsFixed(2)}$suffix',
          style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color),
        ),
      ],
    );
  }

  
  Widget _buildPositionSelector(OperationType type) {
    final isBuy = type == OperationType.buy;
    final color = isBuy ? Colors.green : Colors.red;
    final label = isBuy ? '买入' : '卖出';
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '选择$label仓位:',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: color),
            ),
            IconButton(
              icon: const Icon(Icons.close),
              onPressed: () => pendingOperation.value = null,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
          ],
        ),
        const SizedBox(height: 12),
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
        const SizedBox(height: 8),
        // 显示当前资产信息，辅助决策
        Obx(() => Text(
          isBuy 
            ? '可用资金: ${controller.availableCash.value.toStringAsFixed(0)}元'
            : '持仓数量: ${controller.totalShareCount.value}股',
          style: const TextStyle(fontSize: 12, color: Colors.grey),
        )),
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
          // 设置仓位等级并执行操作
          // UI传参：1->1层(10%), 3->3层(30%), 5->5层(50%), 10->满仓(100%)
          controller.positionLevel.value = isFull ? 10 : level;
          
          // 执行操作
          controller.executeUserOperation(type, '');
          
          // 重置状态
          pendingOperation.value = null;
        },
        child: Text(text, style: const TextStyle(fontWeight: FontWeight.bold)),
      ),
    );
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
            backgroundColor: Colors.grey[200],
            foregroundColor: Colors.red,
            elevation: 0,
            padding: const EdgeInsets.symmetric(vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(4),
              side: BorderSide(color: Colors.red.withOpacity(0.5)),
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
        title: const Text('结束训练'),
        content: const Text('确定要结束当前训练吗？将进行最终结算。'),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: const Text('取消'),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: Colors.red),
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
        padding: const EdgeInsets.symmetric(vertical: 16),
      ),
      onPressed: onTap,
      icon: Icon(icon, size: 20),
      label: Text(label, style: const TextStyle(fontSize: 16)),
    );
  }
  
  Widget _buildQuickTips() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFE3F2FD),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.lightbulb, size: 16, color: Colors.blue),
                  const SizedBox(width: 4),
                  Text(
                    '操作提示',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.blue[800],
                    ),
                  ),
                ],
              ),
              GestureDetector(
                onTap: () => showQuickTips.value = false,
                child: Icon(Icons.close, size: 16, color: Colors.blue[800]),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            '• EXPMA5上穿EXPMA13为金叉，看涨信号\n'
            '• EXPMA5下穿EXPMA13为死叉，看跌信号\n'
            '• 成交量低于60日均量一半为地量，可能变盘\n'
            '• 金叉+地量为强烈买入信号',
            style: TextStyle(fontSize: 12, color: Color(0xFF1565C0)),
          ),
        ],
      ),
    );
  }
}
