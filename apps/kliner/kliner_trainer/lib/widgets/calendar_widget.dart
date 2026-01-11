import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../controllers/training_controller.dart';
import '../models/operation_record.dart';

class CalendarWidget extends StatelessWidget {
  const CalendarWidget({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<TrainingController>();

    return Container(
      width: 300,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF2C2C2C),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Obx(() {
        // Determine the month to display based on current simulation date
        final simulationDate = controller.currentSession.value?.endDate ?? DateTime.now();
        final daysInMonth = DateUtils.getDaysInMonth(simulationDate.year, simulationDate.month);
        final firstDayOfMonth = DateTime(simulationDate.year, simulationDate.month, 1);
        final firstWeekday = firstDayOfMonth.weekday; // 1=Mon, 7=Sun

        // Prepare operation data for the month
        final monthOperations = <int, List<OperationRecord>>{};
        for (final op in controller.allOperations) {
          if (op.timestamp.year == simulationDate.year && op.timestamp.month == simulationDate.month) {
            monthOperations.putIfAbsent(op.timestamp.day, () => []).add(op);
          }
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${simulationDate.year}年${simulationDate.month}月',
                  style: const TextStyle(
                    fontSize: 18, 
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                if (controller.selectedDate.value != null)
                  IconButton(
                    icon: const Icon(Icons.clear, color: Colors.white54, size: 20),
                    onPressed: () => controller.onDateSelected(null), // Clear selection
                    tooltip: '清除选择',
                  ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: const [
                _WeekdayText('一'), _WeekdayText('二'), _WeekdayText('三'),
                _WeekdayText('四'), _WeekdayText('五'), _WeekdayText('六'),
                _WeekdayText('日'),
              ],
            ),
            const SizedBox(height: 8),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
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
                final day = dayIndex + 1;
                final date = DateTime(simulationDate.year, simulationDate.month, day);
                
                // Check selection
                final isSelected = controller.selectedDate.value != null &&
                    controller.selectedDate.value!.year == date.year &&
                    controller.selectedDate.value!.month == date.month &&
                    controller.selectedDate.value!.day == date.day;

                final isToday = date.year == DateTime.now().year && 
                               date.month == DateTime.now().month && 
                               date.day == DateTime.now().day;

                // Determine dot color
                Color? dotColor;
                if (monthOperations.containsKey(day)) {
                  final ops = monthOperations[day]!;
                  final hasTrade = ops.any((op) => op.type == OperationType.buy || op.type == OperationType.sell);
                  dotColor = hasTrade ? Colors.redAccent : Colors.greenAccent;
                }
                
                return GestureDetector(
                  onTap: () {
                    if (monthOperations.containsKey(day)) {
                      controller.onDateSelected(date);
                    }
                  },
                  child: Container(
                    decoration: BoxDecoration(
                      color: isSelected ? Colors.white.withOpacity(0.2) : null,
                      borderRadius: BorderRadius.circular(4),
                      border: isSelected ? Border.all(color: Colors.blueAccent) : null,
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          '$day',
                          style: TextStyle(
                            fontWeight: (isToday || isSelected) ? FontWeight.bold : FontWeight.normal,
                            color: isToday ? Colors.blue : Colors.grey[400],
                          ),
                        ),
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
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 16),
            // Current Stats Display
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                children: [
                   Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('本月胜率', style: TextStyle(color: Colors.white70)),
                      Text(
                        '--', // To be implemented with monthly stats
                        style: const TextStyle(
                          color: Colors.yellow,
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        );
      }),
    );
  }
}

class _WeekdayText extends StatelessWidget {
  final String text;
  const _WeekdayText(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(text, style: const TextStyle(color: Colors.grey, fontSize: 12));
  }
}
