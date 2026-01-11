import 'dart:convert';
import 'dart:math';
import 'package:flutter/services.dart';
import '../models/stock_data.dart';

class CSVDataService {
  final String _dataPath = 'assets/csv_data/';
  final Map<String, List<StockData>> _stockDataCache = {};
  final Map<String, DateTime> _lastUpdateTime = {};
  final Duration _cacheDuration = const Duration(hours: 1);
  
  final Map<String, String> _stockNames = {
    '603601.SH': '再升科技',
    '000001.SZ': '平安银行',
    '000002.SZ': '万科A',
    '600519.SH': '贵州茅台',
    '600036.SH': '招商银行',
    '600000.SH': '浦发银行',
    '000858.SZ': '五粮液',
    '000333.SZ': '美的集团',
    '000651.SZ': '格力电器',
  };
  
  Future<List<String>> getAvailableStockCodes() async {
    final manifest = await rootBundle.loadString('AssetManifest.json');
    final Map<String, dynamic> manifestMap = json.decode(manifest);
    
    final stockCodes = manifestMap.keys
        .where((key) => key.startsWith('assets/csv_data/'))
        .map((key) {
          final fileName = key.split('/').last;
          return fileName.substring(0, fileName.lastIndexOf('.'));
        })
        .toList();
    
    print('CSVDataService: getAvailableStockCodes() - 找到 ${stockCodes.length} 个股票代码');
    print('CSVDataService: getAvailableStockCodes() - 股票代码: $stockCodes');
    
    return stockCodes;
  }
  
  Future<List<StockData>> loadStockData(String stockCode) async {
    final now = DateTime.now();
    
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
      throw Exception('无法加载股票 $stockCode 的数据: $e');
    }
  }
  
  Future<List<StockData>> _parseCSVData(String stockCode) async {
    print('CSVDataService: _parseCSVData() - 开始解析股票 $stockCode 的CSV文件');
    
    final rawData = await rootBundle.loadString('$_dataPath$stockCode.csv');
    print('CSVDataService: _parseCSVData() - 原始数据长度: ${rawData.length}');
    
    final lines = const LineSplitter().convert(rawData);
    print('CSVDataService: _parseCSVData() - 解析后行数: ${lines.length}');
    
    final List<StockData> stockDataList = [];
    
    for (final line in lines) {
      if (line.trim().isEmpty || line.startsWith('股票代码')) continue;
      
      final values = line.split(',');
      if (values.length < 11) {
        print('CSVDataService: _parseCSVData() - 跳过行: $line (values.length: ${values.length})');
        // 如果是第一行或看起来像数据的行，打印更多信息
        if (values.isNotEmpty && values[0].contains(RegExp(r'\d'))) {
          print('CSVDataService: 警告 - 数据列数不足 (期望11，实际${values.length}): $values');
          print('CSVDataService: 原始内容: $line');
        }
        continue;
      }
      
      try {
        final stockData = StockData.fromCSV(values);
        stockDataList.add(stockData);
      } catch (e, stackTrace) {
        print('CSVDataService: _parseCSVData() - 解析错误: $e, 行: $line');
        print('CSVDataService: 错误详情 - values: $values');
        print('CSVDataService: 堆栈: $stackTrace');
      }
    }
    
    if (stockDataList.isEmpty) {
      print('CSVDataService: 警告 - 股票 $stockCode 解析后没有有效数据！');
    }
    
    stockDataList.sort((a, b) => a.date.compareTo(b.date));
    print('CSVDataService: _parseCSVData() - 解析完成，股票数据数量: ${stockDataList.length}');
    
    return stockDataList;
  }
  
  String getStockName(String stockCode) {
    return _stockNames[stockCode] ?? stockCode;
  }
  
  Future<Map<String, dynamic>> getStockInfo(String stockCode) async {
    final data = await loadStockData(stockCode);
    if (data.isEmpty) return {};
    
    final firstRecord = data.first;
    final lastRecord = data.last;
    final totalDays = data.length;
    
    return {
      'code': stockCode,
      'name': getStockName(stockCode),
      'startDate': firstRecord.date,
      'endDate': lastRecord.date,
      'totalDays': totalDays,
      'currentPrice': lastRecord.close,
      'changePercent': lastRecord.changePercent,
    };
  }
  
  Future<List<StockData>> getRandomStockData(int dataLength) async {
    print('CSVDataService: getRandomStockData() - 开始获取随机股票数据，需要长度: $dataLength');
    
    final availableStocks = await getAvailableStockCodes();
    
    if (availableStocks.isEmpty) {
      throw Exception('没有可用的股票数据');
    }
    
    final random = Random();
    final selectedStock = availableStocks[random.nextInt(availableStocks.length)];
    print('CSVDataService: getRandomStockData() - 选择的股票: $selectedStock');
    
    final stockData = await loadStockData(selectedStock);
    print('CSVDataService: getRandomStockData() - 股票数据长度: ${stockData.length}');
    
    if (stockData.length < dataLength) {
      print('CSVDataService: getRandomStockData() - 股票数据长度不足，重新选择');
      return getRandomStockData(dataLength);
    }
    
    final randomStartIndex = random.nextInt(stockData.length - dataLength + 1);
    final endIndex = randomStartIndex + dataLength - 1;
    print('CSVDataService: getRandomStockData() - 随机起始索引: $randomStartIndex, 结束索引: $endIndex');
    
    return stockData.sublist(randomStartIndex, endIndex + 1);
  }
}
