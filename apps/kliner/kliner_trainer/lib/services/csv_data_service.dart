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
    
    return manifestMap.keys
        .where((key) => key.startsWith('assets/csv_data/'))
        .map((key) {
          final fileName = key.split('/').last;
          return fileName.substring(0, fileName.lastIndexOf('.'));
        })
        .toList();
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
    final rawData = await rootBundle.loadString('$_dataPath$stockCode.csv');
    final lines = const LineSplitter().convert(rawData);
    
    final List<StockData> stockDataList = [];
    
    for (final line in lines) {
      if (line.trim().isEmpty || line.startsWith('股票代码')) continue;
      
      final values = line.split(',');
      if (values.length < 11) continue;
      
      try {
        final stockData = StockData.fromCSV(values);
        stockDataList.add(stockData);
      } catch (_) {
        
      }
    }
    
    stockDataList.sort((a, b) => a.date.compareTo(b.date));
    
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
    final availableStocks = await getAvailableStockCodes();
    
    if (availableStocks.isEmpty) {
      throw Exception('没有可用的股票数据');
    }
    
    final random = Random();
    final selectedStock = availableStocks[random.nextInt(availableStocks.length)];
    
    final stockData = await loadStockData(selectedStock);
    
    if (stockData.length < dataLength + 100) {
      return getRandomStockData(dataLength);
    }
    
    const minStartIndex = 100;
    final maxStartIndex = stockData.length - dataLength;
    final startIndex = minStartIndex + random.nextInt(maxStartIndex - minStartIndex);
    
    return stockData.sublist(startIndex, startIndex + dataLength);
  }
}
