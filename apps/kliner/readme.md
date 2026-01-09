# 基于CSV格式的股票K线双盲训练系统 - 详细实现方案

## 一、CSV数据解析与适配

### 1.1 更新数据模型

根据提供的CSV格式，更新数据模型：

```dart
@HiveType(typeId: 0)
class StockData {
  @HiveField(0)
  final String code;          // 股票代码 603601.SH
  
  @HiveField(1)
  final DateTime date;        // 交易日期 2015-01-22
  
  @HiveField(2)
  final double open;          // 开盘价 9.48
  
  @HiveField(3)
  final double high;          // 最高价 11.38
  
  @HiveField(4)
  final double low;           // 最低价 9.48
  
  @HiveField(5)
  final double close;         // 收盘价 11.38
  
  @HiveField(6)
  final double prevClose;     // 昨收价 7.9
  
  @HiveField(7)
  final double change;        // 涨跌额 3.48
  
  @HiveField(8)
  final double changePercent; // 涨跌幅(%) 44.05
  
  @HiveField(9)
  final double volume;        // 成交量(手) 214.0
  
  @HiveField(10)
  final double amount;        // 成交额(千元) 239.542
  
  // 计算指标
  double expma5 = 0.0;
  double expma13 = 0.0;
  double volumeMa5 = 0.0;
  double volumeMa60 = 0.0;
  bool isLowVolume = false;   // 地量标记
  
  StockData({
    required this.code,
    required this.date,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.prevClose,
    required this.change,
    required this.changePercent,
    required this.volume,
    required this.amount,
  });
}
```

### 1.2 CSV数据加载服务

```dart
class CSVDataService extends GetxService {
  final String _dataPath = 'assets/csv_data/';
  final Map<String, List<StockData>> _stockDataCache = {};
  final Map<String, DateTime> _lastUpdateTime = {};
  final Duration _cacheDuration = Duration(hours: 1);
  
  // 获取所有可用的股票代码
  Future<List<String>> getAvailableStockCodes() async {
    final manifest = await rootBundle.loadString('AssetManifest.json');
    final Map<String, dynamic> manifestMap = json.decode(manifest);
    
    return manifestMap.keys
        .where((key) => key.startsWith('assets/csv_data/'))
        .map((key) {
          final fileName = key.split('/').last;
          return fileName.substring(0, fileName.lastIndexOf('.'));
        })
        .toList();
  }
  
  // 加载指定股票数据
  Future<List<StockData>> loadStockData(String stockCode) async {
    final now = DateTime.now();
    
    // 检查缓存
    if (_stockDataCache.containsKey(stockCode) &&
        _lastUpdateTime.containsKey(stockCode) &&
        now.difference(_lastUpdateTime[stockCode]!) < _cacheDuration) {
      return _stockDataCache[stockCode]!;
    }
    
    try {
      final data = await _parseCSVData(stockCode);
      _stockDataCache[stockCode] = data;
      _lastUpdateTime[stockCode] = now;
      return data;
    } catch (e) {
      Get.snackbar('数据加载失败', '无法加载股票 $stockCode 的数据');
      return [];
    }
  }
  
  // 解析CSV文件
  Future<List<StockData>> _parseCSVData(String stockCode) async {
    final rawData = await rootBundle.loadString('$_dataPath$stockCode.csv');
    final lines = const LineSplitter().convert(rawData);
    
    final List<StockData> stockDataList = [];
    
    for (final line in lines) {
      // 跳过注释行和空行
      if (line.trim().isEmpty || line.startsWith('#')) continue;
      
      final values = line.split(',');
      if (values.length < 11) continue;
      
      try {
        final stockData = StockData(
          code: values[0].trim(),
          date: DateTime.parse(values[1].trim()),
          open: double.parse(values[2].trim()),
          high: double.parse(values[3].trim()),
          low: double.parse(values[4].trim()),
          close: double.parse(values[5].trim()),
          prevClose: double.parse(values[6].trim()),
          change: double.parse(values[7].trim()),
          changePercent: double.parse(values[8].trim()),
          volume: double.parse(values[9].trim()),
          amount: double.parse(values[10].trim()),
        );
        
        stockDataList.add(stockData);
      } catch (e) {
        print('解析CSV行失败: $line, 错误: $e');
      }
    }
    
    // 按日期升序排序
    stockDataList.sort((a, b) => a.date.compareTo(b.date));
    
    return stockDataList;
  }
  
  // 获取股票基本信息
  Future<Map<String, dynamic>> getStockInfo(String stockCode) async {
    final data = await loadStockData(stockCode);
    if (data.isEmpty) return {};
    
    final firstRecord = data.first;
    final lastRecord = data.last;
    final totalDays = data.length;
    
    return {
      'code': stockCode,
      'name': _getStockName(stockCode), // 需要股票名称映射表
      'startDate': firstRecord.date,
      'endDate': lastRecord.date,
      'totalDays': totalDays,
      'currentPrice': lastRecord.close,
      'changePercent': lastRecord.changePercent,
    };
  }
  
  // 股票代码映射名称（示例）
  String _getStockName(String code) {
    final Map<String, String> stockNames = {
      '603601.SH': '再升科技',
      '000001.SZ': '平安银行',
      '600519.SH': '贵州茅台',
      // 可以扩展更多股票
    };
    return stockNames[code] ?? code;
  }
  
  // 批量预加载常用股票数据
  Future<void> preloadCommonStocks() async {
    final commonStocks = [
      '603601.SH',
      '000001.SZ',
      '000002.SZ',
      '600519.SH',
      '600036.SH',
    ];
    
    for (final stock in commonStocks) {
      await loadStockData(stock);
    }
  }
}
```

### 1.3 指标计算服务更新

```dart
class IndicatorCalculator {
  // 计算EXPMA指标（指数移动平均）
  static void calculateExpma(List<StockData> data) {
    if (data.isEmpty) return;
    
    // 初始化第一个值
    data[0].expma5 = data[0].close;
    data[0].expma13 = data[0].close;
    
    // 计算EXPMA
    for (int i = 1; i < data.length; i++) {
      // EXPMA公式：EMA(今日) = α × 今日收盘价 + (1-α) × 昨日EMA
      // α = 2/(N+1)
      final double alpha5 = 2 / (5 + 1);   // 5日EXPMA的α
      final double alpha13 = 2 / (13 + 1); // 13日EXPMA的α
      
      data[i].expma5 = alpha5 * data[i].close + (1 - alpha5) * data[i-1].expma5;
      data[i].expma13 = alpha13 * data[i].close + (1 - alpha13) * data[i-1].expma13;
    }
  }
  
  // 计算成交量移动平均（5日、60日）
  static void calculateVolumeMA(List<StockData> data) {
    if (data.isEmpty) return;
    
    for (int i = 0; i < data.length; i++) {
      // 计算5日成交量均线
      if (i < 4) {
        // 不足5天，使用已有数据的平均值
        double sum5 = 0;
        for (int j = 0; j <= i; j++) {
          sum5 += data[j].volume;
        }
        data[i].volumeMa5 = sum5 / (i + 1);
      } else {
        double sum5 = 0;
        for (int j = i - 4; j <= i; j++) {
          sum5 += data[j].volume;
        }
        data[i].volumeMa5 = sum5 / 5;
      }
      
      // 计算60日成交量均线
      if (i < 59) {
        // 不足60天，使用已有数据的平均值
        double sum60 = 0;
        for (int j = 0; j <= i; j++) {
          sum60 += data[j].volume;
        }
        data[i].volumeMa60 = sum60 / (i + 1);
      } else {
        double sum60 = 0;
        for (int j = i - 59; j <= i; j++) {
          sum60 += data[j].volume;
        }
        data[i].volumeMa60 = sum60 / 60;
      }
      
      // 检测地量（成交量低于60日均量的一半）
      if (i >= 59) {
        data[i].isLowVolume = data[i].volume < data[i].volumeMa60 * 0.5;
      }
    }
  }
  
  // 计算所有技术指标
  static void calculateAllIndicators(List<StockData> data) {
    calculateExpma(data);
    calculateVolumeMA(data);
  }
  
  // 获取买卖信号（基于EXPMA金叉死叉）
  static TradingSignal getTradingSignal(List<StockData> data, int currentIndex) {
    if (currentIndex < 13 || data.length < 14) {
      return TradingSignal.hold;
    }
    
    final current = data[currentIndex];
    final previous = data[currentIndex - 1];
    
    // 金叉：EXPMA5上穿EXPMA13
    final bool goldenCross = previous.expma5 <= previous.expma13 && 
                            current.expma5 > current.expma13;
    
    // 死叉：EXPMA5下穿EXPMA13
    final bool deathCross = previous.expma5 >= previous.expma13 && 
                           current.expma5 < current.expma13;
    
    // 地量信号
    final bool lowVolumeSignal = current.isLowVolume;
    
    if (goldenCross && lowVolumeSignal) {
      return TradingSignal.strongBuy;
    } else if (goldenCross) {
      return TradingSignal.buy;
    } else if (deathCross) {
      return TradingSignal.sell;
    } else {
      return TradingSignal.hold;
    }
  }
}

enum TradingSignal {
  strongBuy, // 强烈买入（金叉+地量）
  buy,       // 买入（金叉）
  hold,      // 观望
  sell,      // 卖出（死叉）
}
```

## 二、双盲测试系统实现

### 2.1 双盲测试配置

```dart
class BlindTestConfig {
  final bool showExpma;
  final bool showVolumeMA;
  final bool showLowVolumeAlert;
  final bool showCurrentPrice;
  final bool showStockInfo;
  final int dataLength; // 显示的数据天数
  final bool hideDate;
  final bool hideCode;
  
  const BlindTestConfig({
    this.showExpma = true,
    this.showVolumeMA = true,
    this.showLowVolumeAlert = true,
    this.showCurrentPrice = true,
    this.showStockInfo = false,
    this.dataLength = 60,
    this.hideDate = true,
    this.hideCode = true,
  });
}

enum BlindTestMode {
  beginner,     // 初学者：显示所有指标
  intermediate, // 中级：隐藏部分指标
  advanced,     // 高级：隐藏大部分信息
  master,       // 大师：完全双盲
}

class BlindTestService extends GetxService {
  final CSVDataService _csvService = Get.find();
  
  // 获取双盲测试配置
  BlindTestConfig getConfig(BlindTestMode mode) {
    switch (mode) {
      case BlindTestMode.beginner:
        return BlindTestConfig(
          showExpma: true,
          showVolumeMA: true,
          showLowVolumeAlert: true,
          showCurrentPrice: true,
          showStockInfo: false,
          dataLength: 60,
          hideDate: true,
          hideCode: true,
        );
      case BlindTestMode.intermediate:
        return BlindTestConfig(
          showExpma: true,
          showVolumeMA: false,
          showLowVolumeAlert: false,
          showCurrentPrice: true,
          showStockInfo: false,
          dataLength: 40,
          hideDate: true,
          hideCode: true,
        );
      case BlindTestMode.advanced:
        return BlindTestConfig(
          showExpma: false,
          showVolumeMA: false,
          showLowVolumeAlert: false,
          showCurrentPrice: true,
          showStockInfo: false,
          dataLength: 30,
          hideDate: true,
          hideCode: true,
        );
      case BlindTestMode.master:
        return BlindTestConfig(
          showExpma: false,
          showVolumeMA: false,
          showLowVolumeAlert: false,
          showCurrentPrice: false,
          showStockInfo: false,
          dataLength: 20,
          hideDate: true,
          hideCode: true,
        );
    }
  }
  
  // 获取随机双盲测试
  Future<BlindTestSession> getRandomTest(BlindTestMode mode) async {
    final config = getConfig(mode);
    final availableStocks = await _csvService.getAvailableStockCodes();
    
    if (availableStocks.isEmpty) {
      throw Exception('没有可用的股票数据');
    }
    
    // 随机选择股票
    final random = Random();
    final selectedStock = availableStocks[random.nextInt(availableStocks.length)];
    
    // 加载股票数据
    final stockData = await _csvService.loadStockData(selectedStock);
    
    if (stockData.length < config.dataLength + 100) {
      // 如果数据不足，重新选择
      return getRandomTest(mode);
    }
    
    // 随机选择起始位置，确保有足够的历史数据计算指标
    final minStartIndex = 100; // 确保有足够数据计算60日均线
    final maxStartIndex = stockData.length - config.dataLength;
    final startIndex = minStartIndex + random.nextInt(maxStartIndex - minStartIndex);
    
    // 截取测试数据
    final testData = stockData.sublist(
      startIndex, 
      startIndex + config.dataLength
    );
    
    // 计算技术指标
    IndicatorCalculator.calculateAllIndicators(testData);
    
    return BlindTestSession(
      stockCode: selectedStock,
      stockName: _csvService._getStockName(selectedStock),
      data: testData,
      startDate: testData.first.date,
      endDate: testData.last.date,
      config: config,
      createdAt: DateTime.now(),
    );
  }
  
  // 批量生成测试
  Future<List<BlindTestSession>> generateTests(
    BlindTestMode mode, 
    int count
  ) async {
    final tests = <BlindTestSession>[];
    
    for (int i = 0; i < count; i++) {
      try {
        final test = await getRandomTest(mode);
        tests.add(test);
      } catch (e) {
        print('生成测试失败: $e');
      }
    }
    
    return tests;
  }
}

class BlindTestSession {
  final String stockCode;
  final String stockName;
  final List<StockData> data;
  final DateTime startDate;
  final DateTime endDate;
  final BlindTestConfig config;
  final DateTime createdAt;
  
  // 用户操作
  OperationRecord? userOperation;
  
  BlindTestSession({
    required this.stockCode,
    required this.stockName,
    required this.data,
    required this.startDate,
    required this.endDate,
    required this.config,
    required this.createdAt,
  });
  
  // 获取当前价格
  double get currentPrice => data.last.close;
  
  // 获取技术信号
  TradingSignal get technicalSignal {
    return IndicatorCalculator.getTradingSignal(data, data.length - 1);
  }
}
```

## 三、训练控制器更新

### 3.1 训练控制器

```dart
class TrainingController extends GetxController {
  // 服务依赖
  final CSVDataService csvService = Get.find();
  final BlindTestService blindTestService = Get.find();
  final OperationRepository operationRepo = Get.find();
  
  // 响应式状态
  final Rx<BlindTestSession?> currentSession = Rx<BlindTestSession?>(null);
  final Rx<BlindTestMode> currentMode = BlindTestMode.beginner.obs;
  final RxInt score = 0.obs; // 训练得分
  final RxInt sessionCount = 0.obs; // 完成训练次数
  
  // 仓位管理
  final RxInt positionLevel = 0.obs; // 0-5层
  final RxDouble totalCapital = 1000000.0.obs; // 初始资金100万
  final RxDouble currentPositionValue = 0.0.obs; // 当前持仓市值
  final RxList<String> holdingStocks = <String>[].obs; // 持仓股票
  
  // 操作记录
  final RxList<OperationRecord> sessionOperations = <OperationRecord>[].obs;
  
  @override
  void onReady() async {
    super.onReady();
    await initializeTraining();
  }
  
  // 初始化训练
  Future<void> initializeTraining() async {
    // 预加载常用股票数据
    await csvService.preloadCommonStocks();
    
    // 开始新训练
    await startNewSession();
  }
  
  // 开始新训练会话
  Future<void> startNewSession() async {
    try {
      final session = await blindTestService.getRandomTest(currentMode.value);
      currentSession.value = session;
      
      // 重置会话操作
      sessionOperations.clear();
    } catch (e) {
      Get.snackbar('错误', '无法开始新训练: ${e.toString()}');
    }
  }
  
  // 用户操作
  Future<void> executeUserOperation(OperationType type, String reason) async {
    if (currentSession.value == null) return;
    
    final session = currentSession.value!;
    final operation = OperationRecord(
      id: Uuid().v4(),
      timestamp: DateTime.now(),
      type: type,
      positionLevel: positionLevel.value,
      price: session.currentPrice,
      stockCode: session.stockCode,
      stockName: session.stockName,
      date: session.endDate,
      reason: reason,
      sessionId: '${session.stockCode}_${session.endDate.millisecondsSinceEpoch}',
      blindTestMode: currentMode.value,
    );
    
    // 记录操作
    sessionOperations.add(operation);
    session.userOperation = operation;
    
    // 执行交易逻辑
    await executeTrade(operation);
    
    // 计算得分
    await evaluateOperation(operation);
    
    // 保存操作记录
    await operationRepo.saveOperation(operation);
    
    // 开始下一轮
    await startNewSession();
  }
  
  // 执行交易
  Future<void> executeTrade(OperationRecord operation) async {
    final double tradeAmount = totalCapital.value * (operation.positionLevel / 5);
    
    switch (operation.type) {
      case OperationType.buy:
        if (tradeAmount > totalCapital.value) {
          Get.snackbar('交易失败', '资金不足');
          return;
        }
        
        // 买入股票
        totalCapital.value -= tradeAmount;
        currentPositionValue.value += tradeAmount;
        holdingStocks.add(operation.stockCode);
        break;
        
      case OperationType.sell:
        if (!holdingStocks.contains(operation.stockCode)) {
          Get.snackbar('交易失败', '未持有该股票');
          return;
        }
        
        // 计算盈亏
        final double purchasePrice = _getPurchasePrice(operation.stockCode);
        final double profit = (operation.price - purchasePrice) * 
                            (tradeAmount / purchasePrice);
        
        // 卖出股票
        totalCapital.value += tradeAmount + profit;
        currentPositionValue.value -= tradeAmount;
        holdingStocks.remove(operation.stockCode);
        
        // 更新操作记录盈亏
        operation.profit = profit;
        break;
        
      case OperationType.hold:
        // 观望，不操作
        break;
    }
  }
  
  // 评估操作
  Future<void> evaluateOperation(OperationRecord userOperation) async {
    if (currentSession.value == null) return;
    
    final session = currentSession.value!;
    final technicalSignal = session.technicalSignal;
    
    // 延迟获取后续真实走势（模拟）
    await Future.delayed(Duration(milliseconds: 500));
    
    // 获取未来5天的走势
    final futureTrend = await _getFutureTrend(session);
    
    // 评估逻辑
    int points = 0;
    
    // 1. 技术信号匹配度
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
    
    // 2. 未来走势匹配度
    if (futureTrend == FutureTrend.up && 
        userOperation.type == OperationType.buy) {
      points += 15;
    } else if (futureTrend == FutureTrend.down &&
               userOperation.type == OperationType.sell) {
      points += 15;
    }
    
    // 3. 仓位合理性（根据信号强度）
    if (technicalSignal == TradingSignal.strongBuy &&
        userOperation.positionLevel >= 4) {
      points += 5;
    } else if (technicalSignal == TradingSignal.buy &&
               userOperation.positionLevel >= 2) {
      points += 3;
    }
    
    // 更新得分
    score.value += points;
    sessionCount.value += 1;
    
    // 显示评估结果
    Get.dialog(
      OperationEvaluationDialog(
        userOperation: userOperation,
        technicalSignal: technicalSignal,
        futureTrend: futureTrend,
        points: points,
        totalScore: score.value,
      ),
    );
  }
  
  // 获取未来走势（模拟）
  Future<FutureTrend> _getFutureTrend(BlindTestSession session) async {
    // 这里可以接入真实数据，暂时模拟
    final random = Random();
    return random.nextDouble() > 0.5 ? FutureTrend.up : FutureTrend.down;
  }
  
  // 获取股票买入价格
  double _getPurchasePrice(String stockCode) {
    // 简化实现，实际应从数据库中查询
    return currentSession.value?.currentPrice ?? 0.0;
  }
  
  // 切换训练模式
  void changeMode(BlindTestMode newMode) {
    currentMode.value = newMode;
    startNewSession();
  }
  
  // 获取训练统计
  Map<String, dynamic> getTrainingStats() {
    final totalOps = sessionOperations.length;
    final correctOps = sessionOperations.where((op) => op.profit != null && op.profit! > 0).length;
    final winRate = totalOps > 0 ? (correctOps / totalOps) * 100 : 0;
    
    return {
      'totalSessions': sessionCount.value,
      'totalOperations': totalOps,
      'correctOperations': correctOps,
      'winRate': winRate.toStringAsFixed(1),
      'totalScore': score.value,
      'currentCapital': totalCapital.value,
      'currentPosition': currentPositionValue.value,
    };
  }
}

enum FutureTrend {
  up,
  down,
  sideways,
}
```

## 四、图表组件实现

### 4.1 双盲K线图表组件

```dart
class BlindKLineChart extends GetView<TrainingController> {
  const BlindKLineChart({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final session = controller.currentSession.value;
      if (session == null) {
        return Center(child: CircularProgressIndicator());
      }
      
      return Column(
        children: [
          // 训练信息（双盲模式下隐藏部分信息）
          _buildSessionInfo(session),
          
          // K线图表区域
          Expanded(
            child: Container(
              color: Colors.white,
              child: Stack(
                children: [
                  // 价格K线图
                  _buildPriceChart(session),
                  
                  // EXPMA线（根据配置显示）
                  if (session.config.showExpma)
                    _buildExpmaOverlay(session),
                  
                  // 交互提示
                  _buildInteractiveOverlay(session),
                ],
              ),
            ),
          ),
          
          // 成交量图表
          _buildVolumeChart(session),
          
          // 地量提醒
          if (session.config.showLowVolumeAlert)
            _buildLowVolumeAlert(session),
        ],
      );
    });
  }
  
  Widget _buildSessionInfo(BlindTestSession session) {
    return Container(
      padding: EdgeInsets.all(12),
      color: Colors.grey[100],
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // 左侧：股票信息（双盲模式下隐藏）
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!session.config.hideCode)
                Text(
                  '${session.stockName} (${session.stockCode})',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              if (!session.config.hideDate)
                Text(
                  '${DateFormat('yyyy-MM-dd').format(session.startDate)} ~ '
                  '${DateFormat('yyyy-MM-dd').format(session.endDate)}',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
            ],
          ),
          
          // 右侧：当前价格和变化（双盲模式下可能隐藏）
          if (session.config.showCurrentPrice)
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '${session.currentPrice.toStringAsFixed(2)}',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: _getPriceColor(session),
                  ),
                ),
                Text(
                  '${_getChangePercent(session)}%',
                  style: TextStyle(
                    color: _getPriceColor(session),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
  
  Widget _buildPriceChart(BlindTestSession session) {
    return CustomPaint(
      size: Size.infinite,
      painter: _KLinePainter(
        data: session.data,
        showExpma: session.config.showExpma,
        isBlindMode: true,
      ),
    );
  }
  
  Widget _buildExpmaOverlay(BlindTestSession session) {
    return Positioned.fill(
      child: CustomPaint(
        painter: _ExpmaPainter(
          data: session.data,
        ),
      ),
    );
  }
  
  Widget _buildVolumeChart(BlindTestSession session) {
    return Container(
      height: 120,
      color: Colors.grey[50],
      child: CustomPaint(
        size: Size.infinite,
        painter: _VolumePainter(
          data: session.data,
          showVolumeMA: session.config.showVolumeMA,
        ),
      ),
    );
  }
  
  Widget _buildLowVolumeAlert(BlindTestSession session) {
    final lowVolumeCount = session.data.where((d) => d.isLowVolume).length;
    
    if (lowVolumeCount == 0) return SizedBox();
    
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: Colors.blue[50],
      child: Row(
        children: [
          Icon(Icons.info, color: Colors.blue, size: 16),
          SizedBox(width: 8),
          Text(
            '检测到 $lowVolumeCount 个地量信号',
            style: TextStyle(color: Colors.blue, fontSize: 12),
          ),
        ],
      ),
    );
  }
  
  Widget _buildInteractiveOverlay(BlindTestSession session) {
    return Positioned.fill(
      child: GestureDetector(
        onHorizontalDragUpdate: (details) {
          // 实现左右滑动切换K线显示范围
        },
        onScaleUpdate: (details) {
          // 实现缩放
        },
        child: Container(
          color: Colors.transparent,
        ),
      ),
    );
  }
  
  Color _getPriceColor(BlindTestSession session) {
    final lastData = session.data.last;
    return lastData.close >= lastData.open ? Colors.red : Colors.green;
  }
  
  String _getChangePercent(BlindTestSession session) {
    final lastData = session.data.last;
    final firstData = session.data.first;
    final changePercent = ((lastData.close - firstData.close) / firstData.close) * 100;
    return changePercent.toStringAsFixed(2);
  }
}
```

### 4.2 K线绘图器

```dart
class _KLinePainter extends CustomPainter {
  final List<StockData> data;
  final bool showExpma;
  final bool isBlindMode;
  
  _KLinePainter({
    required this.data,
    this.showExpma = true,
    this.isBlindMode = false,
  });
  
  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;
    
    // 计算价格范围
    double maxPrice = data.map((d) => d.high).reduce(max);
    double minPrice = data.map((d) => d.low).reduce(min);
    
    // 添加一些边距
    final priceRange = maxPrice - minPrice;
    maxPrice += priceRange * 0.05;
    minPrice -= priceRange * 0.05;
    
    // 计算每个K线的宽度和间距
    final double candleWidth = size.width / data.length * 0.7;
    final double candleSpacing = size.width / data.length * 0.3;
    
    // 绘制网格
    _drawGrid(canvas, size, maxPrice, minPrice);
    
    // 绘制K线
    for (int i = 0; i < data.length; i++) {
      final d = data[i];
      final x = i * (candleWidth + candleSpacing) + candleSpacing / 2;
      
      // 计算价格位置
      final highY = _priceToY(d.high, maxPrice, minPrice, size.height);
      final lowY = _priceToY(d.low, maxPrice, minPrice, size.height);
      final openY = _priceToY(d.open, maxPrice, minPrice, size.height);
      final closeY = _priceToY(d.close, maxPrice, minPrice, size.height);
      
      // 绘制上下影线
      final shadowPaint = Paint()
        ..color = Colors.grey
        ..strokeWidth = 1.0;
      
      canvas.drawLine(
        Offset(x, highY),
        Offset(x, lowY),
        shadowPaint,
      );
      
      // 绘制实体
      final bool isBull = d.close >= d.open;
      final Paint bodyPaint = Paint()
        ..color = isBull ? Colors.red : Colors.green
        ..style = PaintingStyle.fill;
      
      final double top = isBull ? closeY : openY;
      final double bottom = isBull ? openY : closeY;
      final double bodyHeight = (top - bottom).abs();
      
      if (bodyHeight > 0) {
        canvas.drawRect(
          Rect.fromLTRB(
            x - candleWidth / 2,
            top,
            x + candleWidth / 2,
            bottom,
          ),
          bodyPaint,
        );
      } else {
        // 十字星
        canvas.drawLine(
          Offset(x - candleWidth / 2, top),
          Offset(x + candleWidth / 2, top),
          bodyPaint..strokeWidth = 1.0,
        );
      }
    }
  }
  
  void _drawGrid(Canvas canvas, Size size, double maxPrice, double minPrice) {
    final gridPaint = Paint()
      ..color = Colors.grey[300]!
      ..strokeWidth = 0.5;
    
    // 水平网格线
    final int horizontalLines = 5;
    for (int i = 0; i <= horizontalLines; i++) {
      final y = size.height * i / horizontalLines;
      canvas.drawLine(
        Offset(0, y),
        Offset(size.width, y),
        gridPaint,
      );
      
      // 价格标签
      final price = maxPrice - (maxPrice - minPrice) * i / horizontalLines;
      _drawText(
        canvas,
        price.toStringAsFixed(2),
        Offset(4, y - 10),
        fontSize: 10,
        color: Colors.grey,
      );
    }
    
    // 垂直网格线
    final int verticalLines = 10;
    for (int i = 0; i <= verticalLines; i++) {
      final x = size.width * i / verticalLines;
      canvas.drawLine(
        Offset(x, 0),
        Offset(x, size.height),
        gridPaint,
      );
    }
  }
  
  double _priceToY(double price, double maxPrice, double minPrice, double height) {
    return height * (maxPrice - price) / (maxPrice - minPrice);
  }
  
  void _drawText(Canvas canvas, String text, Offset offset,
      {double fontSize = 12, Color color = Colors.black}) {
    final textStyle = TextStyle(color: color, fontSize: fontSize);
    final textSpan = TextSpan(text: text, style: textStyle);
    final textPainter = TextPainter(
      text: textSpan,
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, offset);
  }
  
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
```

## 五、操作界面设计

### 5.1 操作控制面板

```dart
class OperationPanel extends GetView<TrainingController> {
  const OperationPanel({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16),
      color: Colors.white,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 仓位选择
          _buildPositionSelector(),
          
          SizedBox(height: 16),
          
          // 操作按钮
          _buildOperationButtons(),
          
          SizedBox(height: 16),
          
          // 操作理由输入
          _buildReasonInput(),
          
          SizedBox(height: 16),
          
          // 快速操作提示
          _buildQuickTips(),
        ],
      ),
    );
  }
  
  Widget _buildPositionSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('选择仓位 (1-5层):', style: TextStyle(fontWeight: FontWeight.bold)),
        SizedBox(height: 8),
        Row(
          children: List.generate(5, (index) {
            final level = index + 1;
            return Expanded(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 2),
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
        SizedBox(height: 8),
        Obx(() => Text(
          '当前仓位: ${controller.positionLevel.value}层 '
          '(${controller.totalCapital.value * controller.positionLevel.value / 5}元)',
          style: TextStyle(fontSize: 12, color: Colors.grey),
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
        SizedBox(width: 8),
        Expanded(
          child: _buildOperationButton(
            OperationType.hold,
            Colors.orange,
            '观望',
            Icons.pause,
          ),
        ),
        SizedBox(width: 8),
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
        padding: EdgeInsets.symmetric(vertical: 16),
      ),
      onPressed: () => _onOperationPressed(type),
      icon: Icon(icon, size: 20),
      label: Text(label, style: TextStyle(fontSize: 16)),
    );
  }
  
  Widget _buildReasonInput() {
    final TextEditingController reasonController = TextEditingController();
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('操作理由（可选）:', style: TextStyle(fontWeight: FontWeight.bold)),
        SizedBox(height: 8),
        TextField(
          controller: reasonController,
          maxLines: 2,
          decoration: InputDecoration(
            hintText: '请输入您的分析依据...',
            border: OutlineInputBorder(),
            contentPadding: EdgeInsets.all(12),
          ),
        ),
      ],
    );
  }
  
  Widget _buildQuickTips() {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.blue[50],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.lightbulb, size: 16, color: Colors.blue),
              SizedBox(width: 4),
              Text('操作提示', style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.blue,
              )),
            ],
          ),
          SizedBox(height: 4),
          Text(
            '• EXPMA5上穿EXPMA13为金叉，看涨信号\n'
            '• EXPMA5下穿EXPMA13为死叉，看跌信号\n'
            '• 成交量低于60日均量一半为地量，可能变盘\n'
            '• 金叉+地量为强烈买入信号',
            style: TextStyle(fontSize: 12, color: Colors.blue[800]),
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
    // 获取输入的理由
    final reason = ''; // 从输入框获取
    controller.executeUserOperation(type, reason);
  }
}
```

### 5.2 训练模式选择

```dart
class TrainingModeSelector extends StatelessWidget {
  final TrainingController controller = Get.find();
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('选择训练模式:', style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            )),
            SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildModeCard(
                  BlindTestMode.beginner,
                  '初学者',
                  '显示全部指标\n60天数据',
                  Colors.green,
                ),
                _buildModeCard(
                  BlindTestMode.intermediate,
                  '中级',
                  '隐藏成交量指标\n40天数据',
                  Colors.blue,
                ),
                _buildModeCard(
                  BlindTestMode.advanced,
                  '高级',
                  '只显示K线\n30天数据',
                  Colors.orange,
                ),
                _buildModeCard(
                  BlindTestMode.master,
                  '大师',
                  '完全双盲\n20天数据',
                  Colors.red,
                ),
              ],
            ),
            SizedBox(height: 16),
            Obx(() => Text(
              '当前模式: ${_getModeName(controller.currentMode.value)}',
              style: TextStyle(fontWeight: FontWeight.bold),
            )),
          ],
        ),
      ),
    );
  }
  
  Widget _buildModeCard(
    BlindTestMode mode,
    String title,
    String description,
    Color color,
  ) {
    return Obx(() {
      final isSelected = controller.currentMode.value == mode;
      return InkWell(
        onTap: () => controller.changeMode(mode),
        child: Container(
          width: 150,
          padding: EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: isSelected ? color : color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: isSelected ? color : Colors.grey[300]!,
              width: isSelected ? 2 : 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: isSelected ? Colors.white : color,
                  fontSize: 16,
                ),
              ),
              SizedBox(height: 4),
              Text(
                description,
                style: TextStyle(
                  fontSize: 12,
                  color: isSelected ? Colors.white70 : Colors.grey[700],
                ),
              ),
            ],
          ),
        ),
      );
    });
  }
  
  String _getModeName(BlindTestMode mode) {
    switch (mode) {
      case BlindTestMode.beginner: return '初学者模式';
      case BlindTestMode.intermediate: return '中级模式';
      case BlindTestMode.advanced: return '高级模式';
      case BlindTestMode.master: return '大师模式';
    }
  }
}
```

## 六、复盘分析系统

### 6.1 复盘控制器

```dart
class ReviewController extends GetxController {
  final OperationRepository operationRepo = Get.find();
  
  // 复盘数据
  final RxList<OperationRecord> allOperations = <OperationRecord>[].obs;
  final RxList<BlindTestSession> allSessions = <BlindTestSession>[].obs;
  
  // 筛选条件
  final Rx<DateTime?> startDate = Rx<DateTime?>(null);
  final Rx<DateTime?> endDate = Rx<DateTime?>(null);
  final Rx<BlindTestMode?> filterMode = Rx<BlindTestMode?>(null);
  final Rx<OperationType?> filterType = Rx<OperationType?>(null);
  
  // 统计指标
  final RxMap<String, dynamic> stats = RxMap({
    'totalOperations': 0,
    'winRate': 0.0,
    'totalProfit': 0.0,
    'avgProfit': 0.0,
    'maxProfit': 0.0,
    'maxLoss': 0.0,
    'bestStock': '',
    'worstStock': '',
  });
  
  @override
  void onReady() async {
    super.onReady();
    await loadAllData();
    calculateStats();
  }
  
  // 加载数据
  Future<void> loadAllData() async {
    allOperations.value = await operationRepo.getAllOperations();
    
    // 按时间排序
    allOperations.sort((a, b) => b.timestamp.compareTo(a.timestamp));
  }
  
  // 计算统计指标
  void calculateStats() {
    final filteredOps = _getFilteredOperations();
    
    if (filteredOps.isEmpty) return;
    
    // 计算基本统计
    final totalOps = filteredOps.length;
    final profitableOps = filteredOps.where((op) => op.profit != null && op.profit! > 0).length;
    final totalProfit = filteredOps.fold(0.0, (sum, op) => sum + (op.profit ?? 0));
    
    // 按股票统计
    final Map<String, List<OperationRecord>> opsByStock = {};
    for (final op in filteredOps) {
      opsByStock.putIfAbsent(op.stockCode, () => []).add(op);
    }
    
    // 找出最佳和最差股票
    String bestStock = '';
    double bestStockProfit = double.negativeInfinity;
    String worstStock = '';
    double worstStockProfit = double.infinity;
    
    for (final entry in opsByStock.entries) {
      final stockProfit = entry.value.fold(0.0, (sum, op) => sum + (op.profit ?? 0));
      if (stockProfit > bestStockProfit) {
        bestStockProfit = stockProfit;
        bestStock = entry.key;
      }
      if (stockProfit < worstStockProfit) {
        worstStockProfit = stockProfit;
        worstStock = entry.key;
      }
    }
    
    stats.value = {
      'totalOperations': totalOps,
      'winRate': totalOps > 0 ? (profitableOps / totalOps) * 100 : 0.0,
      'totalProfit': totalProfit,
      'avgProfit': totalOps > 0 ? totalProfit / totalOps : 0.0,
      'maxProfit': filteredOps.fold(0.0, (max, op) => max > (op.profit ?? 0) ? max : (op.profit ?? 0)),
      'maxLoss': filteredOps.fold(0.0, (min, op) => min < (op.profit ?? 0) ? min : (op.profit ?? 0)),
      'bestStock': bestStock,
      'bestStockProfit': bestStockProfit,
      'worstStock': worstStock,
      'worstStockProfit': worstStockProfit,
    };
  }
  
  // 获取筛选后的操作记录
  List<OperationRecord> _getFilteredOperations() {
    return allOperations.where((op) {
      // 日期筛选
      if (startDate.value != null && op.timestamp.isBefore(startDate.value!)) {
        return false;
      }
      if (endDate.value != null && op.timestamp.isAfter(endDate.value!)) {
        return false;
      }
      
      // 模式筛选
      if (filterMode.value != null && op.blindTestMode != filterMode.value) {
        return false;
      }
      
      // 类型筛选
      if (filterType.value != null && op.type != filterType.value) {
        return false;
      }
      
      return true;
    }).toList();
  }
  
  // 导出数据
  Future<void> exportToCSV() async {
    final filteredOps = _getFilteredOperations();
    
    if (filteredOps.isEmpty) {
      Get.snackbar('导出失败', '没有可导出的数据');
      return;
    }
    
    final csvData = [
      [
        '时间',
        '股票代码',
        '股票名称',
        '操作类型',
        '仓位',
        '价格',
        '操作日期',
        '训练模式',
        '理由',
        '盈亏',
      ],
      ...filteredOps.map((op) => [
        DateFormat('yyyy-MM-dd HH:mm:ss').format(op.timestamp),
        op.stockCode,
        op.stockName,
        op.type.name,
        op.positionLevel.toString(),
        op.price.toStringAsFixed(2),
        DateFormat('yyyy-MM-dd').format(op.date),
        _getModeName(op.blindTestMode),
        op.reason,
        op.profit?.toStringAsFixed(2) ?? '',
      ]),
    ];
    
    final csv = const ListToCsvConverter().convert(csvData);
    
    try {
      final directory = await getApplicationDocumentsDirectory();
      final file = File('${directory.path}/operation_review_${DateTime.now().millisecondsSinceEpoch}.csv');
      await file.writeAsString(csv);
      
      Get.snackbar('导出成功', '文件已保存到: ${file.path}');
    } catch (e) {
      Get.snackbar('导出失败', e.toString());
    }
  }
  
  // 清空数据
  Future<void> clearData() async {
    final result = await Get.dialog(
      AlertDialog(
        title: Text('确认清空'),
        content: Text('确定要清空所有操作记录吗？此操作不可恢复。'),
        actions: [
          TextButton(
            onPressed: () => Get.back(result: false),
            child: Text('取消'),
          ),
          TextButton(
            onPressed: () => Get.back(result: true),
            child: Text('确认清空', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    
    if (result == true) {
      await operationRepo.clearAllData();
      await loadAllData();
      calculateStats();
      Get.snackbar('已清空', '所有操作记录已删除');
    }
  }
  
  String _getModeName(BlindTestMode mode) {
    switch (mode) {
      case BlindTestMode.beginner: return '初学者';
      case BlindTestMode.intermediate: return '中级';
      case BlindTestMode.advanced: return '高级';
      case BlindTestMode.master: return '大师';
    }
  }
}
```

## 七、应用配置和初始化

### 7.1 主应用入口

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // 初始化Hive
  await Hive.initFlutter();
  
  // 注册Hive适配器
  Hive.registerAdapter(StockDataAdapter());
  Hive.registerAdapter(OperationRecordAdapter());
  Hive.registerAdapter(BlindTestSessionAdapter());
  
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: '股票K线双盲训练系统',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        fontFamily: 'Roboto',
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          elevation: 1,
        ),
      ),
      initialRoute: '/',
      getPages: [
        GetPage(name: '/', page: () => HomePage()),
        GetPage(name: '/training', page: () => TrainingPage()),
        GetPage(name: '/review', page: () => ReviewPage()),
        GetPage(name: '/settings', page: () => SettingsPage()),
      ],
      initialBinding: AppBindings(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class AppBindings implements Bindings {
  @override
  void dependencies() {
    Get.lazyPut(() => CSVDataService());
    Get.lazyPut(() => OperationRepository());
    Get.lazyPut(() => BlindTestService());
    Get.lazyPut(() => TrainingController());
    Get.lazyPut(() => ReviewController());
  }
}
```

### 7.2 主页设计

```dart
class HomePage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('股票K线双盲训练系统'),
        actions: [
          IconButton(
            icon: Icon(Icons.settings),
            onPressed: () => Get.toNamed('/settings'),
          ),
        ],
      ),
      body: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 欢迎卡片
            Card(
              child: Padding(
                padding: EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(
                      'K线双盲训练系统',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 10),
                    Text(
                      '通过双盲测试提升您的技术分析能力',
                      style: TextStyle(color: Colors.grey),
                    ),
                  ],
                ),
              ),
            ),
            
            SizedBox(height: 20),
            
            // 功能卡片
            Expanded(
              child: GridView(
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 20,
                  mainAxisSpacing: 20,
                  childAspectRatio: 1.2,
                ),
                children: [
                  _buildFunctionCard(
                    '开始训练',
                    Icons.play_arrow,
                    Colors.green,
                    () => Get.toNamed('/training'),
                  ),
                  _buildFunctionCard(
                    '操作复盘',
                    Icons.bar_chart,
                    Colors.blue,
                    () => Get.toNamed('/review'),
                  ),
                  _buildFunctionCard(
                    '训练统计',
                    Icons.assessment,
                    Colors.orange,
                    () => _showTrainingStats(),
                  ),
                  _buildFunctionCard(
                    '数据管理',
                    Icons.storage,
                    Colors.purple,
                    () => _showDataManagement(),
                  ),
                  _buildFunctionCard(
                    '使用教程',
                    Icons.school,
                    Colors.teal,
                    () => _showTutorial(),
                  ),
                  _buildFunctionCard(
                    '关于我们',
                    Icons.info,
                    Colors.grey,
                    () => _showAbout(),
                  ),
                ],
              ),
            ),
            
            // 快速开始
            Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('快速开始', style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    )),
                    SizedBox(height: 12),
                    Wrap(
                      spacing: 10,
                      children: [
                        ElevatedButton.icon(
                          onPressed: () {
                            Get.toNamed('/training');
                          },
                          icon: Icon(Icons.flash_on),
                          label: Text('快速训练'),
                        ),
                        OutlinedButton.icon(
                          onPressed: () {
                            Get.toNamed('/review');
                          },
                          icon: Icon(Icons.history),
                          label: Text('查看历史'),
                        ),
                        OutlinedButton.icon(
                          onPressed: _exportAllData,
                          icon: Icon(Icons.download),
                          label: Text('导出数据'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildFunctionCard(
    String title,
    IconData icon,
    Color color,
    VoidCallback onTap,
  ) {
    return InkWell(
      onTap: onTap,
      child: Card(
        elevation: 3,
        child: Padding(
          padding: EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 40, color: color),
              SizedBox(height: 10),
              Text(
                title,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  void _showTrainingStats() {
    final controller = Get.find<TrainingController>();
    final stats = controller.getTrainingStats();
    
    Get.dialog(
      AlertDialog(
        title: Text('训练统计'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildStatItem('训练次数', stats['totalSessions'].toString()),
            _buildStatItem('总操作', stats['totalOperations'].toString()),
            _buildStatItem('正确操作', stats['correctOperations'].toString()),
            _buildStatItem('胜率', '${stats['winRate']}%'),
            _buildStatItem('总得分', stats['totalScore'].toString()),
            _buildStatItem('当前资金', '${stats['currentCapital'].toStringAsFixed(2)}元'),
            _buildStatItem('持仓市值', '${stats['currentPosition'].toStringAsFixed(2)}元'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: Text('关闭'),
          ),
        ],
      ),
    );
  }
  
  Widget _buildStatItem(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontWeight: FontWeight.bold)),
          Text(value),
        ],
      ),
    );
  }
}
```

## 八、部署配置

### 8.1 pubspec.yaml配置

```yaml
name: stock_kline_blind_trainer
description: 股票K线双盲训练系统
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  
  # 状态管理
  get: ^4.6.5
  
  # 本地存储
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  path_provider: ^2.1.0
  
  # 数据处理
  csv: ^5.0.2
  intl: ^0.18.1
  uuid: ^3.0.7
  
  # UI组件
  flutter_screenutil: ^5.8.4
  flutter_staggered_grid_view: ^0.6.2
  
  # 图表
  fl_chart: ^0.61.0
  
  # 文件操作
  share_plus: ^6.3.0
  file_picker: ^5.3.3
  
  # 其他
  dartz: ^0.10.1
  equatable: ^2.0.5

dev_dependencies:
  flutter_test:
    sdk: flutter
  hive_generator: ^1.1.3
  build_runner: ^2.3.3

flutter:
  uses-material-design: true
  
  assets:
    - assets/csv_data/
    - assets/images/
  
  fonts:
    - family: Roboto
      fonts:
        - asset: fonts/Roboto-Regular.ttf
        - asset: fonts/Roboto-Bold.ttf
          weight: 700
```

### 8.2 构建说明

1. **准备CSV数据**：
   - 将CSV文件放在 `assets/csv_data/` 目录下
   - 文件名格式：`股票代码.csv`，例如 `603601.SH.csv`
   - 确保CSV文件格式与提供的示例一致

2. **生成Hive适配器**：
```bash
flutter pub run build_runner build
```

3. **运行应用**：
```bash
flutter run
```

## 九、总结

这个完整的股票K线双盲训练系统方案具有以下特点：

### 核心优势：
1. **双盲测试设计**：完全隐藏股票信息和日期，专注于技术分析
2. **多种训练模式**：从初学者到大师，逐步提高难度
3. **完整的技术指标**：EXPMA(5,13)金叉死叉信号，成交量均线，地量提醒
4. **仓位管理**：1-5层仓位控制，模拟真实交易
5. **详细复盘系统**：完整的操作记录和统计分析

### 技术特色：
1. **基于GetX**：简洁高效的状态管理
2. **Hive存储**：高性能本地数据存储
3. **自定义图表**：高性能K线图绘制
4. **模块化架构**：清晰的代码组织和易于维护

### 用户体验：
1. **直观的操作界面**：简洁明了的操作面板
2. **实时反馈**：操作后立即显示评估结果
3. **渐进式学习**：从简单到复杂的训练模式
4. **详细复盘**：帮助用户分析错误，改进策略

这个系统可以作为股票技术分析学习的有效工具，通过双盲测试帮助用户摆脱对股票名称和日期的依赖，专注于K线形态和技术指标的分析，真正提升技术分析能力。