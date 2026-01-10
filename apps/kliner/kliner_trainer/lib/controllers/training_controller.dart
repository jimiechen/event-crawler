import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:uuid/uuid.dart';
import '../models/operation_record.dart';
import '../models/blind_test_session.dart';
import '../models/blind_test_config.dart';
import '../services/csv_data_service.dart';
import '../services/indicator_calculator.dart';
import '../services/storage_service.dart';
import 'dart:math' as math;

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
  final RxList<OperationRecord> allOperations = <OperationRecord>[].obs;
  final RxBool isLoading = false.obs;
  final RxBool isTrainingInProgress = false.obs;
  
  final RxInt visibleDataStartIndex = 0.obs;
  final RxInt visibleDataLength = 60.obs;
  final RxDouble currentProfitPercent = 0.0.obs;
  final RxDouble globalProfit = 0.0.obs;
  final Rx<BlindTestSession?> currentTrainingSession = Rx<BlindTestSession?>(null);
  
  @override
  void onInit() async {
    super.onInit();
    await storageService.init();
    await loadStats();
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
        startIndex: 0,
        endIndex: stockData.length - 1,
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
      reason: '',
    );
    
    sessionOperations.add(operation);
    session.userOperation = operation;
    
    executeTrade(operation);
    await evaluateOperation(operation);
    await storageService.saveOperation(operation);
    allOperations.add(operation);
    
    nextDay();
    
    loadStats();
  }
  
  void executeTrade(OperationRecord operation) {
    switch (operation.type) {
      case OperationType.buy:
        final double tradeAmount = _getPositionAmount(operation.positionLevel);
        
        if (tradeAmount > totalCapital.value) {
          Get.snackbar('交易失败', '资金不足');
          return;
        }
        
        operation.purchasePrice = operation.price;
        
        totalCapital.value -= tradeAmount;
        currentPositionValue.value += tradeAmount;
        holdingStocks.add(operation.stockCode);
        
        currentProfitPercent.value = 0.0;
        operation.profitPercent = 0.0;
        break;
        
      case OperationType.sell:
        if (!holdingStocks.contains(operation.stockCode)) {
          Get.snackbar('交易失败', '未持有该股票');
          return;
        }
        
        final double sellPrice = operation.price;
        final double purchasePrice = operation.purchasePrice ?? sellPrice;
        final double tradeAmount = _getPositionAmount(operation.positionLevel);
        
        final double profitPercent = ((sellPrice - purchasePrice) / purchasePrice) * 100;
        final double profit = (sellPrice - purchasePrice) * (tradeAmount / purchasePrice);
        
        totalCapital.value += tradeAmount + profit;
        currentPositionValue.value -= tradeAmount;
        holdingStocks.remove(operation.stockCode);
        
        operation.profit = profit;
        operation.profitPercent = profitPercent;
        
        currentProfitPercent.value = profitPercent;
        break;
        
      case OperationType.hold:
        if (holdingStocks.isNotEmpty) {
          final double currentPrice = operation.price;
          final double purchasePrice = _getLastPurchasePrice();
          if (purchasePrice > 0) {
            final double profitPercent = ((currentPrice - purchasePrice) / purchasePrice) * 100;
              currentProfitPercent.value = profitPercent;
          }
        }
        break;
    }
  }
  
  double _getPositionAmount(int positionLevel) {
    switch (positionLevel) {
      case 1: return 10000.0;
      case 2: return 20000.0;
      case 3: return 30000.0;
      case 4: return 40000.0;
      case 5: return 50000.0;
      default: return 0.0;
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
  
  void _showEvaluationDialog(OperationRecord operation, TradingSignal technicalSignal, int points) {
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
              _buildInfoRow('您的操作', '${_getOperationTypeName(operation.type)} ${_getPositionAmountText(operation.positionLevel)}'),
              if (config.showCurrentPrice)
                _buildInfoRow('操作价格', '${operation.price.toStringAsFixed(2)}元'),
              const Divider(),
              _buildInfoRow('技术信号', _getSignalName(technicalSignal)),
              const Divider(),
              _buildInfoRow('收益率', '${operation.profitPercent?.toStringAsFixed(2) ?? "0.00"}%', isHighlight: true),
              const Divider(),
              _buildInfoRow('得分', '$points分', isHighlight: true),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Get.back();
            },
            child: const Text('关闭'),
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
  
  String _getPositionAmountText(int positionLevel) {
    switch (positionLevel) {
      case 1: return '1万';
      case 2: return '2万';
      case 3: return '3万';
      case 4: return '4万';
      case 5: return '5万';
      default: return '0万';
    }
  }
  
  double _getLastPurchasePrice() {
    final buyOperations = allOperations.where((op) => op.type == OperationType.buy).toList();
    if (buyOperations.isEmpty) return 0.0;
    return buyOperations.last.purchasePrice ?? 0.0;
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
  
  void startTraining() async {
    try {
      isLoading.value = true;
      
      final config = currentConfig.value;
      final stockData = await csvService.getRandomStockData(config.dataLength);
      
      IndicatorCalculator.calculateAllIndicators(stockData);
      
      final stockInfo = await csvService.getStockInfo(stockData.first.code);
      
      currentTrainingSession.value = BlindTestSession(
        stockCode: stockData.first.code,
        stockName: stockInfo['name'] as String,
        data: stockData,
        startDate: stockData.first.date,
        endDate: stockData.last.date,
        startIndex: 0,
        endIndex: stockData.length - 1,
      );
      
      visibleDataStartIndex.value = 0;
      visibleDataLength.value = stockData.length.clamp(10, 60);
      isTrainingInProgress.value = true;
      allOperations.clear();
      sessionOperations.clear();
      positionLevel.value = 0;
      currentProfitPercent.value = 0.0;
    } catch (e) {
      Get.snackbar('错误', '无法开始训练: ${e.toString()}');
    } finally {
      isLoading.value = false;
    }
  }
  
  void nextDay() {
    if (currentTrainingSession.value == null) return;
    
    final session = currentTrainingSession.value!;
    
    if (session.data.length <= 1) {
      Get.snackbar('提示', '已经是最后一天了');
      return;
    }
    
    final dayData = session.data.sublist(1);
    
    currentSession.value = BlindTestSession(
      stockCode: session.stockCode,
      stockName: session.stockName,
      data: dayData,
      startDate: dayData.first.date,
      endDate: dayData.last.date,
      startIndex: session.startIndex + 1,
      endIndex: session.endIndex + 1,
      userOperation: session.userOperation,
    );
  }
  
  void zoomIn() {
    if (visibleDataLength.value >= 60) return;
    
    final newVisibleCount = math.min(60, visibleDataLength.value + 10);
    visibleDataLength.value = newVisibleCount;
    updateVisibleData();
  }
  
  void zoomOut() {
    if (visibleDataLength.value <= 10) return;
    
    final newVisibleCount = math.max(10, visibleDataLength.value - 10);
    visibleDataLength.value = newVisibleCount;
    updateVisibleData();
  }
  
  void updateVisibleData() {
    if (currentTrainingSession.value == null) return;
    
    final session = currentTrainingSession.value!;
    final startIndex = math.max(0, session.data.length - visibleDataLength.value);
    final endIndex = startIndex + visibleDataLength.value;
    
    final visibleData = session.data.sublist(startIndex, endIndex);
    
    currentSession.value = BlindTestSession(
      stockCode: session.stockCode,
      stockName: session.stockName,
      data: visibleData,
      startDate: visibleData.first.date,
      endDate: visibleData.last.date,
      startIndex: startIndex,
      endIndex: endIndex - 1,
      userOperation: session.userOperation,
    );
  }
  
  void endTraining() async {
    if (currentTrainingSession.value == null) return;
    
    isTrainingInProgress.value = false;
    currentTrainingSession.value = null;
    
    showFinalSummary();
  }
  
  void showFinalSummary() {
    final session = currentTrainingSession.value;
    if (session == null) return;
    
    Get.dialog(
      barrierDismissible: false,
      AlertDialog(
        title: const Text('训练结束'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildInfoRow('股票', session.displayInfo, isHighlight: true),
              const Divider(),
              _buildInfoRow('操作次数', '${allOperations.length}次'),
              const Divider(),
              _buildInfoRow('最终收益率', '${currentProfitPercent.value.toStringAsFixed(2)}%', isHighlight: true),
              const Divider(),
              _buildInfoRow('训练天数', '${visibleDataLength.value}天'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Get.back();
              startTraining();
            },
            child: const Text('开始新训练'),
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
  
  @override
  void onClose() {
    storageService.close();
    super.onClose();
  }
}
