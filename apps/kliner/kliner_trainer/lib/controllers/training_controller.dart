import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:uuid/uuid.dart';
import '../models/operation_record.dart';
import '../models/blind_test_session.dart';
import '../models/blind_test_config.dart';
import '../models/stock_data.dart';
import '../models/account_snapshot.dart';
import '../services/csv_data_service.dart';
import '../services/indicator_calculator.dart';
import '../services/storage_service.dart';
import 'dart:math' as math;

class TrainingController extends GetxController {
  CSVDataService get csvService => Get.find<CSVDataService>();
  StorageService get storageService => Get.find<StorageService>();
  
  final Rx<BlindTestSession?> currentSession = Rx<BlindTestSession?>(null);
  final Rx<BlindTestMode> currentMode = BlindTestMode.beginner.obs;
  final Rx<BlindTestConfig> currentConfig = BlindTestConfig.fromMode(BlindTestMode.beginner).obs;
  
  final RxInt score = 0.obs;
  final RxInt sessionCount = 0.obs;  
  final RxInt positionLevel = 0.obs;
  
  // 核心资产状态
  final RxDouble availableCash = 1000000.0.obs; // 可用现金
  final RxInt totalShareCount = 0.obs; // 总持仓股数
  
  // 衍生状态 (通过 _updateDailyState 计算)
  final RxDouble currentProfitPercent = 0.0.obs;
  final RxDouble globalProfit = 0.0.obs;
  
  // 获取当前总资产 (现金 + 持仓市值)
  double get currentTotalCapital {
    final currentPrice = currentSession.value?.currentPrice ?? 0.0;
    return availableCash.value + (totalShareCount.value * currentPrice);
  }
  
  double get currentPositionValue {
    final currentPrice = currentSession.value?.currentPrice ?? 0.0;
    return totalShareCount.value * currentPrice;
  }
  
  // 获取当前持仓比例
  final RxDouble currentAverageCost = 0.0.obs;
  
  // 日历联动状态
  final Rx<DateTime?> selectedDate = Rx<DateTime?>(null);
  final RxList<OperationRecord> dailyOperations = <OperationRecord>[].obs;

  @override
  void onInit() {
    super.onInit();
    print('TrainingController: onInit');
    
    // 监听 selectedDate 变化，自动更新 dailyOperations
    ever(selectedDate, (_) => _updateDailyOperations());
    
    // 初始化服务和状态
    storageService.init().then((_) => loadStats());
  }

  void _updateDailyOperations() {
    if (selectedDate.value == null) {
      dailyOperations.clear();
      return;
    }
    
    final targetDate = selectedDate.value!;
    dailyOperations.value = allOperations.where((op) =>
      op.timestamp.year == targetDate.year &&
      op.timestamp.month == targetDate.month &&
      op.timestamp.day == targetDate.day
    ).toList();
  }

  double get currentPositionRatio {
    final total = currentTotalCapital;
    if (total <= 0) return 0.0;
    return (currentPositionValue / total) * 100;
  }

  // 兼容旧代码
  double get totalCapital => currentTotalCapital;

  final RxList<OperationRecord> sessionOperations = <OperationRecord>[].obs;
  final RxList<OperationRecord> allOperations = <OperationRecord>[].obs;
  final RxList<AccountSnapshot> dailySnapshots = <AccountSnapshot>[].obs;
  
  final RxBool isLoading = false.obs;
  final RxBool isTrainingInProgress = false.obs;
  
  final RxInt visibleDataStartIndex = 0.obs;
  final RxInt visibleDataLength = 60.obs;
  
  // 当前选中的K线数据（用于十字光标显示）
  final Rx<StockData?> selectedData = Rx<StockData?>(null);

  // 保存完整的训练数据（包含历史和未来）
  List<StockData> _fullData = [];
  // 当前指向的数据索引（指向当前K线的最后一天）
  int _currentIndex = 0;

  final Rx<BlindTestSession?> currentTrainingSession = Rx<BlindTestSession?>(null);
  
  final RxDouble zoomScale = 1.0.obs;
  int _baseVisibleDataLength = 60;
  
  // 视图偏移量（用于查看历史数据）
  // 0: 显示到当前最新日期
  // >0: 向前查看历史（单位：天）
  final RxInt viewOffset = 0.obs;

  void onDateSelected(DateTime? date) {
    selectedDate.value = date;
  }
  
  Future<void> loadStats() async {
    final stats = storageService.getStats();
    sessionCount.value = stats['totalSessions'] as int;
    score.value = stats['totalScore'] as int;
  }
  
  // --- 缩放与导航 (Zoom & Navigation) ---
  
  void startZoom() {
    _baseVisibleDataLength = visibleDataLength.value;
    print('TrainingController: startZoom, base length: $_baseVisibleDataLength');
  }
  
  void handleZoom(double scale) {
    // scale > 1 (放大) -> 看到的K线更少
    // scale < 1 (缩小) -> 看到的K线更多
    final newLength = (_baseVisibleDataLength / scale).round();
    final clampedLength = newLength.clamp(5, 500);
    
    if (visibleDataLength.value != clampedLength) {
      visibleDataLength.value = clampedLength;
      updateVisibleData();
    }
  }
  
  void zoomIn() {
    print('TrainingController: zoomIn clicked. Current length: ${visibleDataLength.value}');
    // 放大：显示更少K线 -> length 变小
    final newLength = (visibleDataLength.value * 0.8).round();
    visibleDataLength.value = newLength.clamp(5, 500);
    print('TrainingController: zoomIn -> new length: ${visibleDataLength.value}');
    updateVisibleData();
  }
  
  void zoomOut() {
    print('TrainingController: zoomOut clicked. Current length: ${visibleDataLength.value}');
    // 缩小：显示更多K线 -> length 变大
    final newLength = (visibleDataLength.value * 1.2).round();
    visibleDataLength.value = newLength.clamp(5, 500);
    print('TrainingController: zoomOut -> new length: ${visibleDataLength.value}');
    updateVisibleData();
  }
  
  void scrollLeft() {
    print('TrainingController: scrollLeft');
    // 向左移动光标/查看历史
    final session = currentSession.value;
    if (session == null || session.data.isEmpty) return;

    // 1. 如果没有选中，先选中当前可视最右侧（最新）
    if (selectedData.value == null) {
      selectedData.value = session.data.last;
      print('TrainingController: Selected last data (init)');
      return;
    }

    int currentIndex = session.data.indexOf(selectedData.value!);
    if (currentIndex == -1) {
      // 尝试通过日期找回索引 (防止对象引用不一致导致的光标丢失)
      final date = selectedData.value?.date;
      if (date != null) {
        currentIndex = session.data.indexWhere((d) => d.date == date);
        if (currentIndex != -1) {
          // 修正引用
          selectedData.value = session.data[currentIndex];
        }
      }
      
      if (currentIndex == -1) {
        // 确实找不到，重置为最右侧 (最新)
        selectedData.value = session.data.last;
        print('TrainingController: Selected data lost, reset to last.');
        return;
      }
    }

    if (currentIndex > 0) {
      // 2. 还在当前可视范围内，移动光标向左
      selectedData.value = session.data[currentIndex - 1];
      print('TrainingController: Moved cursor left to index ${currentIndex - 1}');
    } else {
      // 3. 到达左边缘 (index == 0)，尝试滚动视图
      final effectiveCurrentIndex = _currentIndex - viewOffset.value;
      final startIndex = effectiveCurrentIndex + 1 - visibleDataLength.value;
      
      if (startIndex > 0) {
        // 滚动 1 天 (更流畅，避免跳跃)
        scroll(1);
        
        // 滚动后，保持光标在最左侧（新的数据）
        if (currentSession.value != null && currentSession.value!.data.isNotEmpty) {
          selectedData.value = currentSession.value!.data.first;
        }
      } else {
        print('TrainingController: Reached start of data (startIndex=$startIndex)');
        Get.snackbar('提示', '已到达数据起始点', duration: const Duration(seconds: 1));
      }
    }
  }

  void scrollRight() {
    print('TrainingController: scrollRight');
    // 向右移动光标/回到未来
    final session = currentSession.value;
    if (session == null || session.data.isEmpty) return;

    if (selectedData.value == null) {
      selectedData.value = session.data.last;
      return;
    }

    int currentIndex = session.data.indexOf(selectedData.value!);
    if (currentIndex == -1) {
      // 尝试通过日期找回
      final date = selectedData.value?.date;
      if (date != null) {
        currentIndex = session.data.indexWhere((d) => d.date == date);
        if (currentIndex != -1) {
          selectedData.value = session.data[currentIndex];
        }
      }
      
      if (currentIndex == -1) {
        selectedData.value = session.data.last;
        return;
      }
    }

    if (currentIndex < session.data.length - 1) {
      // 2. 还在当前可视范围内，移动光标向右
      selectedData.value = session.data[currentIndex + 1];
      print('TrainingController: Moved cursor right to index ${currentIndex + 1}');
    } else {
      // 3. 到达右边缘 (index == last)，尝试滚动视图
      if (viewOffset.value > 0) {
        scroll(-1); // 滚动 1 天 (更流畅)
        // 滚动后，保持光标在最右侧
        if (currentSession.value != null && currentSession.value!.data.isNotEmpty) {
          selectedData.value = currentSession.value!.data.last;
        }
      } else {
         print('TrainingController: Reached latest data');
         Get.snackbar('提示', '已是最新数据', duration: const Duration(seconds: 1));
      }
    }
  }

  void scroll(int steps) {
    print('TrainingController: scroll steps=$steps, currentOffset=${viewOffset.value}');
    final newOffset = viewOffset.value + steps;
    // 限制范围: 
    // min: 0 (不能超过最新日期)
    // max: _currentIndex (不能超过数据起点 - visibleLength? 不，updateVisibleData会处理clamp)
    // 但为了UI流畅，我们限制 max offset 使得至少能看到几个K线
    
    viewOffset.value = newOffset.clamp(0, _currentIndex);
    print('TrainingController: newOffset=${viewOffset.value}');
    updateVisibleData();
  }

  void updateVisibleData() {
    if (_fullData.isEmpty) {
      print('TrainingController: updateVisibleData() - data empty');
      return;
    }
    
    // 计算可视窗口
    final int effectiveCurrentIndex = _currentIndex - viewOffset.value;
    // endIndex exclusive
    final int endIndex = effectiveCurrentIndex + 1;
    final int startIndex = math.max(0, endIndex - visibleDataLength.value);
    
    print('TrainingController: updateVisibleData range: $startIndex -> $endIndex (len=${visibleDataLength.value})');
    
    if (startIndex >= endIndex) {
        print('TrainingController: Invalid range');
        return;
    }
    
    final visibleData = _fullData.sublist(startIndex, endIndex);
    
    // 复用之前的 session 信息，只更新 data
    final prevSession = currentTrainingSession.value;
    
    currentSession.value = BlindTestSession(
      stockCode: prevSession?.stockCode ?? '',
      stockName: prevSession?.stockName ?? '',
      data: visibleData,
      startDate: visibleData.first.date,
      endDate: visibleData.last.date,
      startIndex: startIndex,
      endIndex: _currentIndex,
      userOperation: prevSession?.userOperation,
    );
    currentTrainingSession.value = currentSession.value;
    
    // 更新衍生状态
    _updateDailyState();
  }
  
  // --- 核心逻辑 (Core Logic) ---

  Future<void> startTraining() async {
    try {
      print('TrainingController: startTraining');
      isLoading.value = true;
      
      final config = currentConfig.value;
      // 预加载足够的数据
      final totalNeeded = config.dataLength + 365; // 至少一年
      final stockData = await csvService.getRandomStockData(totalNeeded);
      
      IndicatorCalculator.calculateAllIndicators(stockData);
      
      final stockInfo = await csvService.getStockInfo(stockData.first.code);
      
      // 初始化状态
      _fullData = stockData;
      _currentIndex = config.dataLength - 1;
      
      // 初始化 Session
      currentTrainingSession.value = BlindTestSession(
        stockCode: stockData.first.code,
        stockName: stockInfo['name'] as String,
        data: [], // Will be filled by updateVisibleData
        startDate: stockData.first.date,
        endDate: stockData.last.date,
        startIndex: 0,
        endIndex: 0,
      );
      
      // 重置变量
      visibleDataStartIndex.value = 0;
      visibleDataLength.value = config.dataLength;
      isTrainingInProgress.value = true;
      allOperations.clear();
      sessionOperations.clear();
      dailySnapshots.clear();
      
      positionLevel.value = 0;
      currentProfitPercent.value = 0.0;
      globalProfit.value = 0.0;
      availableCash.value = 1000000.0;
      totalShareCount.value = 0;
      currentAverageCost.value = 0.0; // Reset average cost
      selectedDate.value = null;
      dailyOperations.clear();
      selectedData.value = null;
      viewOffset.value = 0;
      
      updateVisibleData();
      
      // 初始十字光标位置
      if (currentSession.value != null && currentSession.value!.data.isNotEmpty) {
        selectedData.value = currentSession.value!.data.last;
      }
      
    } catch (e) {
      print('TrainingController: startTraining error: $e');
      Get.snackbar('错误', '无法开始训练: ${e.toString()}');
    } finally {
      isLoading.value = false;
    }
  }

  // S2: 日初/状态更新
  void _updateDailyState() {
    if (currentSession.value == null) return;
    
    // 计算全局收益
    const double initialCapital = 1000000.0;
    final profit = currentTotalCapital - initialCapital;
    globalProfit.value = profit;
    currentProfitPercent.value = (profit / initialCapital) * 100;
  }
  
  // S3 -> S4: 用户操作与结算
  Future<void> executeUserOperation(OperationType type, String reason) async {
    print('TrainingController: executeUserOperation $type');
    if (currentSession.value == null) return;
    
    final session = currentSession.value!;
    
    // 1. Capture State Before Operation
    final cashBefore = availableCash.value;
    final positionBefore = totalShareCount.value.toDouble();
    
    // 2. Calculate Trade Details (Quantity, Amount, Profit)
    final tradeDetails = _calculateTradeDetails(type, positionLevel.value, session.currentPrice);
    
    // Calculate Post-Operation Position Ratio
    double newCash = cashBefore;
    double newShares = positionBefore;
    if (type == OperationType.buy) {
       newCash -= (tradeDetails['amount'] as double);
       newShares += (tradeDetails['quantity'] as int);
    } else if (type == OperationType.sell) {
       newCash += (tradeDetails['amount'] as double);
       newShares -= (tradeDetails['quantity'] as int);
    }
    
    final newPosValue = newShares * session.currentPrice;
    final newTotal = newCash + newPosValue;
    final actualRatio = newTotal > 0 ? newPosValue / newTotal : 0.0;
    
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
      // New Fields for Closed Loop
      cashBefore: cashBefore,
      positionBefore: positionBefore,
      quantity: tradeDetails['quantity'] as int,
      amount: tradeDetails['amount'] as double,
      realizedProfit: tradeDetails['realizedProfit'] as double,
      purchasePrice: tradeDetails['purchasePrice'] as double,
      profitPercent: tradeDetails['profitPercent'] as double,
      profit: tradeDetails['profit'] as double?,
      targetPositionRatio: tradeDetails['targetRatio'] as double?,
      actualPositionRatioAfter: actualRatio,
    );
    
    sessionOperations.add(operation);
    session.userOperation = operation;
    
    // 3. Execute Trade (Update Cash & Position)
    _applyTrade(operation);
    
    // 4. 评估 (Scoring)
    await evaluateOperation(operation);
    
    // 5. 记录 (Transaction)
    await storageService.saveOperation(operation);
    allOperations.add(operation);
    
    // 6. 结算快照 (Snapshot)
    _recordSnapshot();
    
    // 7. 进入下一天 (S1)
    nextDay();
    
    loadStats();
  }
  
  void skipDay() {
    executeUserOperation(OperationType.hold, '观望');
  }

  // Returns map with keys: quantity, amount, realizedProfit, purchasePrice, profitPercent, profit
  Map<String, dynamic> _calculateTradeDetails(OperationType type, int level, double currentPrice) {
    int quantity = 0;
    double amount = 0.0;
    double realizedProfit = 0.0;
    double purchasePrice = 0.0;
    double profitPercent = 0.0;
    double? profit;
    
    // 获取总资产 (用于计算目标仓位)
    final totalAssets = currentTotalCapital;

    double? targetRatio;

    if (type == OperationType.buy) {
      // 买入逻辑：基于目标仓位 (Target Position)
      // Level 1,3,5 -> 10%, 30%, 50% 目标仓位
      // Level 10 (满仓) -> 100% 目标仓位
      
      if (level == 10) {
        targetRatio = 1.0;
      } else {
        // 1成=10%, 3成=30%, 5成=50%
        targetRatio = level * 0.1;
      }
      
      // 计算目标持仓市值
      final targetPositionValue = totalAssets * targetRatio;
      
      // 计算需要买入的市值 (目标 - 当前)
      final currentPosValue = currentPositionValue;
      double buyValue = targetPositionValue - currentPosValue;
      
      // 如果已经是目标仓位或更高，则不买入 (或者买入0)
      if (buyValue <= 0) {
        quantity = 0;
        amount = 0.0;
      } else {
        // 限制买入金额不超过可用现金
        if (buyValue > availableCash.value) {
          buyValue = availableCash.value;
        }
        
        // 计算股数 (整手)
        int theoreticalShares = (buyValue / currentPrice).floor();
        quantity = (theoreticalShares ~/ 100) * 100;
        
        if (quantity > 0) {
          amount = quantity * currentPrice;
          purchasePrice = currentPrice;
        } else {
           // 不足1手
           quantity = 0;
           amount = 0.0;
        }
      }
      
    } else if (type == OperationType.sell) {
      // 卖出逻辑：基于当前持仓的百分比 (Percentage of Holdings)
      // Level 1,3,5 -> 卖出当前持仓的 10%, 30%, 50%
      // Level 10 (空仓) -> 卖出 100%
      
      if (totalShareCount.value > 0) {
        double sellRatio = 0.0;
        if (level == 10) {
          quantity = totalShareCount.value;
          sellRatio = 1.0;
        } else {
          // 1->10%, 3->30%, 5->50%
          sellRatio = level * 0.1;
          
          int targetSellShares = (totalShareCount.value * sellRatio).floor();
          quantity = (targetSellShares ~/ 100) * 100;
        }
        
        // 如果是要清仓/空仓，但计算结果导致有碎股剩余? 
        // 这里的逻辑是卖出指定比例。
        // 特殊处理：如果 level=10 (空仓)，强制卖完，不管整手 (虽然A股卖出也要整手，除了零股)。
        // 假设这里遵循整手卖出。
        
        // Handle case where calculated sell amount is 0 but user wants to sell
        if (quantity == 0 && level == 10 && totalShareCount.value > 0) {
           quantity = totalShareCount.value; // Allow selling odd lots if clearing? Or force 0?
           // Usually allow clearing odd lots.
        }
        
        if (quantity > 0) {
          amount = quantity * currentPrice;
          final double avgCost = _getLastPurchasePrice(); 
          realizedProfit = (currentPrice - avgCost) * quantity;
          profit = realizedProfit;
          profitPercent = avgCost > 0 ? ((currentPrice - avgCost) / avgCost) * 100 : 0.0;
        }
      }
    }
    
    return {
      'quantity': quantity,
      'amount': amount,
      'realizedProfit': realizedProfit,
      'purchasePrice': purchasePrice,
      'profitPercent': profitPercent,
      'profit': profit,
      'targetRatio': targetRatio,
    };
  }

  void _applyTrade(OperationRecord operation) {
    if (operation.type == OperationType.buy) {
      if (operation.quantity > 0) {
         // 计算加权平均成本
         double oldCost = currentAverageCost.value;
         double oldShares = totalShareCount.value.toDouble();
         double newShares = operation.quantity.toDouble();
         double buyPrice = operation.price;

         if (oldShares + newShares > 0) {
           currentAverageCost.value = ((oldCost * oldShares) + (buyPrice * newShares)) / (oldShares + newShares);
         } else {
           currentAverageCost.value = buyPrice;
         }

         availableCash.value -= operation.amount;
         totalShareCount.value += operation.quantity;
      } else {
         if (operation.positionLevel > 0) {
             Get.snackbar('交易提示', '资金不足或无法买入1手');
         }
      }
    } else if (operation.type == OperationType.sell) {
      if (operation.quantity > 0) {
        availableCash.value += operation.amount;
        totalShareCount.value -= operation.quantity;
        
        // 卖出不改变单位成本，除非清仓
        if (totalShareCount.value == 0) {
          currentAverageCost.value = 0.0;
        }
      } else {
        if (operation.positionLevel > 0) {
            Get.snackbar('交易提示', '无可卖持仓或不足1手');
        }
      }
    }
  }

  // Deprecated: old executeTrade method replaced by _applyTrade
  // void executeTrade(OperationRecord operation) { ... }

  void _recordSnapshot() {
    if (currentSession.value == null) return;
    
    final snapshot = AccountSnapshot(
      date: currentSession.value!.endDate,
      availableCash: availableCash.value,
      positionShares: totalShareCount.value,
      positionValue: currentPositionValue,
      totalCapital: currentTotalCapital,
      currentPrice: currentSession.value!.currentPrice,
      floatingProfit: globalProfit.value,
    );
    dailySnapshots.add(snapshot);
    print('TrainingController: Snapshot recorded for ${snapshot.date}, Capital: ${snapshot.totalCapital}');
  }

  void nextDay() {
    print('TrainingController: nextDay');
    if (_fullData.isEmpty) return;
    
    // Check if training ends
    if (_currentIndex >= _fullData.length - 1) {
      endTraining();
      return;
    }
    
    // S1: Advance Day
    _currentIndex++;
    viewOffset.value = 0; // 重置视图到最新
    
    // Update View (S2 triggered inside)
    updateVisibleData();
    
    // Crosshair follows new day
    if (currentSession.value != null && currentSession.value!.data.isNotEmpty) {
      selectedData.value = currentSession.value!.data.last;
    }
  }

  Future<void> endTraining({bool userAborted = false}) async {
    print('TrainingController: endTraining (aborted: $userAborted)');
    isTrainingInProgress.value = false;
    
    if (!userAborted) {
      // 强制卖出结算
      if (totalShareCount.value > 0) {
        final currentPrice = currentSession.value?.currentPrice ?? 0.0;
        final revenue = totalShareCount.value * currentPrice;
        availableCash.value += revenue;
        totalShareCount.value = 0;
      }
      _updateDailyState();
      await saveTrainingData();
      storageService.incrementDailyRound(DateTime.now());
    }
    
    Get.dialog(
      AlertDialog(
        title: Text(userAborted ? '训练结束' : '通关完成'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('最终收益: ${globalProfit.value.toStringAsFixed(2)} (${currentProfitPercent.value.toStringAsFixed(2)}%)'),
            Text('操作次数: ${allOperations.length}'),
            const SizedBox(height: 10),
            Text('今日已完成: ${storageService.getDailyRounds(DateTime.now())}/10 轮'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Get.back();
              startTraining();
            },
            child: const Text('再来一局'),
          ),
          TextButton(
            onPressed: () {
              Get.back();
              // Back to home? For now just close dialog
              // Or navigate to home route if exists
            },
            child: const Text('返回首页'),
          ),
        ],
      ),
      barrierDismissible: false,
    );
  }
  
  // --- Helpers ---

  Future<void> evaluateOperation(OperationRecord userOperation) async {
    if (currentSession.value == null) return;
    final session = currentSession.value!;
    final technicalSignal = session.technicalSignal;
    
    int points = 0;
    // Simple logic
    if ((technicalSignal == TradingSignal.strongBuy || technicalSignal == TradingSignal.buy) && userOperation.type == OperationType.buy) {
      points += 10;
    } else if (technicalSignal == TradingSignal.sell && userOperation.type == OperationType.sell) {
      points += 10;
    } else if (technicalSignal == TradingSignal.hold && userOperation.type == OperationType.hold) {
      points += 5;
    }
    
    userOperation.points = points;
    score.value += points;
    sessionCount.value += 1;
  }

  Future<void> saveTrainingData() async {
    final result = {
      'date': DateTime.now().toIso8601String(),
      'stockCode': currentSession.value?.stockCode,
      'score': score.value,
      'profit': globalProfit.value,
      'operations': allOperations.map((op) => op.toJson()).toList(),
      'snapshots': dailySnapshots.map((s) => s.toJson()).toList(),
    };
    await storageService.saveTrainingResult(result);
  }
  
  double _getLastPurchasePrice() {
    return currentAverageCost.value;
  }
  
  Map<String, dynamic> getTrainingStats() {
    final stats = storageService.getStats();
    return {
      'totalSessions': stats['totalSessions'],
      'totalScore': stats['totalScore'],
      'totalProfit': stats['totalProfit'],
      'avgScore': stats['avgScore'],
      'currentCapital': totalCapital,
      'currentPosition': currentPositionValue,
    };
  }
  
  void changeMode(BlindTestMode newMode) {
    currentMode.value = newMode;
    currentConfig.value = BlindTestConfig.fromMode(newMode);
  }
  
  @override
  void onClose() {
    storageService.close();
    super.onClose();
  }
}
