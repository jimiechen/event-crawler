import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:uuid/uuid.dart';
import '../models/operation_record.dart';
import '../models/blind_test_session.dart';
import '../models/blind_test_config.dart';
import '../services/csv_data_service.dart';
import '../services/indicator_calculator.dart';
import '../services/storage_service.dart';

class TrainingController extends GetxController {
  final CSVDataService csvService = CSVDataService();
  final StorageService storageService = StorageService();  
  final Rx<BlindTestSession?> currentSession = Rx<BlindTestSession?>(null);
  final Rx<BlindTestMode> currentMode = BlindTestMode.beginner.obs;
  final Rx<BlindTestConfig> currentConfig = BlindTestConfig.fromMode(BlindTestMode.beginner).obs;
  final RxInt score = 0.obs;
  final RxInt sessionCount = 0.obs;  
  final RxInt positionLevel = 0.obs;
  final RxDouble totalCapital = 1000000.0.obs;
  final RxDouble currentPositionValue = 0.0.obs;
  final RxList<String> holdingStocks = <String>[].obs;  
  final RxList<OperationRecord> sessionOperations = <OperationRecord>[].obs;
  final RxBool isLoading = false.obs;
  
  @override
  void onInit() async {
    super.onInit();
    await storageService.init();
    await loadStats();
    await startNewSession();
  }
  
  Future<void> loadStats() async {
    final stats = storageService.getStats();
    sessionCount.value = stats['totalSessions'] as int;
    score.value = stats['totalScore'] as int;
  }
  
  Future<void> startNewSession() async {
    try {
      isLoading.value = true;
      
      final config = currentConfig.value;
      final stockData = await csvService.getRandomStockData(config.dataLength);
      
      IndicatorCalculator.calculateAllIndicators(stockData);
      
      final stockInfo = await csvService.getStockInfo(stockData.first.code);
      
      currentSession.value = BlindTestSession(
        stockCode: stockData.first.code,
        stockName: stockInfo['name'] as String,
        data: stockData,
        startDate: stockData.first.date,
        endDate: stockData.last.date,
      );
      
      sessionOperations.clear();
      positionLevel.value = 0;
    } catch (e) {
      Get.snackbar('错误', '无法开始新训练: ${e.toString()}');
    } finally {
      isLoading.value = false;
    }
  }
  
  void changeMode(BlindTestMode newMode) {
    currentMode.value = newMode;
    currentConfig.value = BlindTestConfig.fromMode(newMode);
    startNewSession();
  }
  
  Future<void> executeUserOperation(OperationType type, String reason) async {
    if (currentSession.value == null) return;
    
    final session = currentSession.value!;
    final operation = OperationRecord(
      id: const Uuid().v4(),
      timestamp: DateTime.now(),
      type: type,
      positionLevel: positionLevel.value,
      price: session.currentPrice,
      stockCode: session.stockCode,
      stockName: session.stockName,
      stockDate: session.endDate,
      reason: reason,
    );
    
    sessionOperations.add(operation);
    session.userOperation = operation;
    
    await executeTrade(operation);
    await evaluateOperation(operation);
    await storageService.saveOperation(operation);
    
    await loadStats();
  }
  
  Future<void> executeTrade(OperationRecord operation) async {
    final double tradeAmount = totalCapital.value * (operation.positionLevel / 5);
    
    switch (operation.type) {
      case OperationType.buy:
        if (tradeAmount > totalCapital.value) {
          Get.snackbar('交易失败', '资金不足');
          return;
        }
        
        totalCapital.value -= tradeAmount;
        currentPositionValue.value += tradeAmount;
        holdingStocks.add(operation.stockCode);
        break;
        
      case OperationType.sell:
        if (!holdingStocks.contains(operation.stockCode)) {
          Get.snackbar('交易失败', '未持有该股票');
          return;
        }
        
        final double purchasePrice = _getPurchasePrice(operation.stockCode);
        final double profit = (operation.price - purchasePrice) * 
                            (tradeAmount / purchasePrice);
        
        totalCapital.value += tradeAmount + profit;
        currentPositionValue.value -= tradeAmount;
        holdingStocks.remove(operation.stockCode);
        
        operation.profit = profit;
        break;
        
      case OperationType.hold:
        break;
    }
  }
  
  Future<void> evaluateOperation(OperationRecord userOperation) async {
    if (currentSession.value == null) return;
    
    final session = currentSession.value!;
    final technicalSignal = session.technicalSignal;
    
    int points = 0;
    
    if ((technicalSignal == TradingSignal.strongBuy || 
         technicalSignal == TradingSignal.buy) &&
        userOperation.type == OperationType.buy) {
      points += 10;
    } else if (technicalSignal == TradingSignal.sell &&
               userOperation.type == OperationType.sell) {
      points += 10;
    } else if (technicalSignal == TradingSignal.hold &&
               userOperation.type == OperationType.hold) {
      points += 5;
    }
    
    if (technicalSignal == TradingSignal.strongBuy &&
        userOperation.positionLevel >= 4) {
      points += 5;
    } else if (technicalSignal == TradingSignal.buy &&
               userOperation.positionLevel >= 2) {
      points += 3;
    }
    
    userOperation.points = points;
    score.value += points;
    sessionCount.value += 1;
    
    _showEvaluationDialog(userOperation, technicalSignal, points);
  }
  
  void _showEvaluationDialog(OperationRecord userOperation, TradingSignal technicalSignal, int points) {
    final config = currentConfig.value;
    
    Get.dialog(
      AlertDialog(
        title: const Text('训练结果复盘'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!config.hideCode)
                _buildInfoRow('股票', '${currentSession.value?.stockName} (${currentSession.value?.stockCode})'),
              if (!config.hideDate)
                _buildInfoRow('日期', '${currentSession.value?.startDate} ~ ${currentSession.value?.endDate}'),
              const Divider(),
              _buildInfoRow('您的操作', '${_getOperationTypeName(userOperation.type)} (${userOperation.positionLevel}层)'),
              if (config.showCurrentPrice)
                _buildInfoRow('操作价格', '${userOperation.price.toStringAsFixed(2)}元'),
              if (userOperation.reason.isNotEmpty)
                _buildInfoRow('操作理由', userOperation.reason),
              const Divider(),
              _buildInfoRow('技术信号', _getSignalName(technicalSignal)),
              const Divider(),
              _buildInfoRow('得分', '$points分', isHighlight: true),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Get.back();
              startNewSession();
            },
            child: const Text('下一轮'),
          ),
          TextButton(
            onPressed: () {
              Get.back();
            },
            child: const Text('查看历史'),
          ),
        ],
      ),
    );
  }
  
  Widget _buildInfoRow(String label, String value, {bool isHighlight = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
          Text(
            value,
            style: TextStyle(
              fontWeight: isHighlight ? FontWeight.bold : FontWeight.normal,
              color: isHighlight ? Colors.red : null,
            ),
          ),
        ],
      ),
    );
  }
  
  String _getOperationTypeName(OperationType type) {
    switch (type) {
      case OperationType.buy: return '买入';
      case OperationType.sell: return '卖出';
      case OperationType.hold: return '观望';
    }
  }
  
  String _getSignalName(TradingSignal signal) {
    switch (signal) {
      case TradingSignal.strongBuy: return '强烈买入 (金叉+地量)';
      case TradingSignal.buy: return '买入 (金叉)';
      case TradingSignal.sell: return '卖出 (死叉)';
      case TradingSignal.hold: return '观望';
    }
  }
  
  double _getPurchasePrice(String stockCode) {
    return currentSession.value?.currentPrice ?? 0.0;
  }
  
  Map<String, dynamic> getTrainingStats() {
    final stats = storageService.getStats();
    return {
      'totalSessions': stats['totalSessions'],
      'totalScore': stats['totalScore'],
      'totalProfit': stats['totalProfit'],
      'avgScore': stats['avgScore'],
      'currentCapital': totalCapital.value,
      'currentPosition': currentPositionValue.value,
    };
  }
  
  @override
  void onClose() {
    storageService.close();
    super.onClose();
  }
}
