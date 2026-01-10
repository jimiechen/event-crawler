import 'stock_data.dart';
import 'operation_record.dart';

enum TradingSignal {
  strongBuy,
  buy,
  hold,
  sell,
}

class BlindTestSession {
  final String stockCode;
  final String stockName;
  final List<StockData> data;
  final DateTime startDate;
  final DateTime endDate;
  final int startIndex;
  final int endIndex;
  
  OperationRecord? userOperation;
  
  BlindTestSession({
    required this.stockCode,
    required this.stockName,
    required this.data,
    required this.startDate,
    required this.endDate,
    required this.startIndex,
    required this.endIndex,
    this.userOperation,
  });
  
  double get currentPrice => data.last.close;
  
  double get changePercent {
    if (data.isEmpty) return 0.0;
    final firstData = data.first;
    final lastData = data.last;
    return ((lastData.close - firstData.close) / firstData.close) * 100;
  }
  
  TradingSignal get technicalSignal {
    if (data.length < 14) return TradingSignal.hold;
    
    final current = data.last;
    final previous = data[data.length - 2];
    
    final bool goldenCross = previous.expma5 <= previous.expma13 && 
                            current.expma5 > current.expma13;
    
    final bool deathCross = previous.expma5 >= previous.expma13 && 
                           current.expma5 < current.expma13;
    
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
  
  String get displayInfo {
    return '$stockName ($stockCode) - 第${startIndex + 1}天至第${endIndex + 1}天';
  }
}
