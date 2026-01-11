import 'package:flutter/material.dart';
import 'calendar_widget.dart';
import 'desktop_operation_panel.dart';
import 'kline_chart_widget.dart';

class DesktopLayoutWidget extends StatelessWidget {
  const DesktopLayoutWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // Left Sidebar: Calendar & Stats
        Container(
          width: 320,
          color: const Color(0xFF1E1E1E),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
          child: Column(
            children: const [
              CalendarWidget(),
              Spacer(),
              // Placeholder for future sidebar items or branding
              Text('MineplanetGo K-Trainer', style: TextStyle(color: Colors.white24, fontSize: 12)),
            ],
          ),
        ),
        // Main Content Area
        Expanded(
          child: Column(
            children: [
              // K-Line Chart Area
              const Expanded(
                child: KLineChartWidget(),
              ),
              // Operation Panel (Bottom)
              const DesktopOperationPanel(),
            ],
          ),
        ),
      ],
    );
  }
}
