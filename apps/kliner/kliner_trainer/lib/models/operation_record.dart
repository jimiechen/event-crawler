enum OperationType {
  buy,
  sell,
  hold,
}

class OperationRecord {
  final String id;
  final DateTime timestamp;
  final OperationType type;
  final int positionLevel;
  final double price;
  final String stockCode;
  final String stockName;
  final DateTime stockDate;
  final String reason;
  double purchasePrice;
  double profitPercent;
  double? profit;
  int points = 0;
  
  OperationRecord({
    required this.id,
    required this.timestamp,
    required this.type,
    required this.positionLevel,
    required this.price,
    required this.stockCode,
    required this.stockName,
    required this.stockDate,
    required this.reason,
    this.purchasePrice = 0.0,
    this.profitPercent = 0.0,
  });
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'timestamp': timestamp.toIso8601String(),
      'type': type.name,
      'positionLevel': positionLevel,
      'price': price,
      'stockCode': stockCode,
      'stockName': stockName,
      'stockDate': stockDate.toIso8601String(),
      'reason': reason,
      'purchasePrice': purchasePrice,
      'profitPercent': profitPercent,
      'profit': profit,
      'points': points,
    };
  }
  
  factory OperationRecord.fromJson(Map<String, dynamic> json) {
    final typeStr = json['type'] as String;
    OperationType opType;
    try {
      opType = OperationType.values.firstWhere((e) => e.name == typeStr);
    } catch (e) {
      opType = OperationType.hold;
    }
    
    final record = OperationRecord(
      id: json['id'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      type: opType,
      positionLevel: json['positionLevel'] as int,
      price: (json['price'] as num).toDouble(),
      stockCode: json['stockCode'] as String,
      stockName: json['stockName'] as String,
      stockDate: DateTime.parse(json['lateDate'] as String),
      reason: json['reason'] as String,
    );
    
    record.purchasePrice = json['purchasePrice'] as double? ?? 0.0;
    record.profitPercent = json['profitPercent'] as double? ?? 0.0;
    record.profit = json['profit'] as double?;
    record.points = json['points'] as int? ?? 0;
    
    return record;
  }
}
