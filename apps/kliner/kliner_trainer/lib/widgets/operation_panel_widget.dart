import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../models/operation_record.dart';
import '../controllers/training_controller.dart';

class OperationPanelWidget extends GetView<TrainingController> {
  const OperationPanelWidget({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildPositionSelector(),
          const SizedBox(height: 16),
          _buildOperationButtons(),
          const SizedBox(height: 16),
          _buildReasonInput(),
          const SizedBox(height: 16),
          _buildQuickTips(),
        ],
      ),
    );
  }
  
  Widget _buildPositionSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '选择仓位 (1-5层):',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Row(
          children: List.generate(5, (index) {
            final level = index + 1;
            return Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2),
                child: Obx(() => ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: controller.positionLevel.value == level
                        ? _getPositionColor(level)
                        : Colors.grey[200],
                    foregroundColor: controller.positionLevel.value == level
                        ? Colors.white
                        : Colors.black,
                  ),
                  onPressed: () => controller.positionLevel.value = level,
                  child: Text('$level层'),
                )),
              ),
            );
          }),
        ),
        const SizedBox(height: 8),
        Obx(() => Text(
          '当前仓位: ${controller.positionLevel.value}层 '
          '(${(controller.totalCapital.value * controller.positionLevel.value / 5).toStringAsFixed(0)}元)',
          style: const TextStyle(fontSize: 12, color: Colors.grey),
        )),
      ],
    );
  }
  
  Widget _buildOperationButtons() {
    return Row(
      children: [
        Expanded(
          child: _buildOperationButton(
            OperationType.buy,
            Colors.green,
            '买入',
            Icons.arrow_upward,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _buildOperationButton(
            OperationType.hold,
            Colors.orange,
            '观望',
            Icons.pause,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _buildOperationButton(
            OperationType.sell,
            Colors.red,
            '卖出',
            Icons.arrow_downward,
          ),
        ),
      ],
    );
  }
  
  Widget _buildOperationButton(
    OperationType type,
    Color color,
    String label,
    IconData icon,
  ) {
    return ElevatedButton.icon(
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(vertical: 16),
      ),
      onPressed: () => _onOperationPressed(type),
      icon: Icon(icon, size: 20),
      label: Text(label, style: const TextStyle(fontSize: 16)),
    );
  }
  
  Widget _buildReasonInput() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '操作理由（可选）:',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        TextField(
          maxLines: 2,
          decoration: InputDecoration(
            hintText: '请输入您的分析依据...',
            border: const OutlineInputBorder(),
            contentPadding: const EdgeInsets.all(12),
          ),
        ),
      ],
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
            children: [
              Icon(Icons.lightbulb, size: 16, color: Colors.blue[800]),
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
  
  Color _getPositionColor(int level) {
    switch (level) {
      case 1: return Colors.blue[300]!;
      case 2: return Colors.blue;
      case 3: return Colors.green;
      case 4: return Colors.orange;
      case 5: return Colors.red;
      default: return Colors.grey;
    }
  }
  
  void _onOperationPressed(OperationType type) {
    controller.executeUserOperation(type, '');
  }
}
