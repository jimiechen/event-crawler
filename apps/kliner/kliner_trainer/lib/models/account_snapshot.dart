class AccountSnapshot {
  final DateTime date; // 对应K线日期
  final double availableCash;
  final int positionShares;
  final double positionValue;
  final double totalCapital;
  final double currentPrice;
  final double floatingProfit;
  
  AccountSnapshot({
    required this.date,
    required this.availableCash,
    required this.positionShares,
    required this.positionValue,
    required this.totalCapital,
    required this.currentPrice,
    required this.floatingProfit,
  });
  
  Map<String, dynamic> toJson() => {
    'date': date.toIso8601String(),
    'availableCash': availableCash,
    'positionShares': positionShares,
    'positionValue': positionValue,
    'totalCapital': totalCapital,
    'currentPrice': currentPrice,
    'floatingProfit': floatingProfit,
  };
  
  factory AccountSnapshot.fromJson(Map<String, dynamic> json) {
    return AccountSnapshot(
      date: DateTime.parse(json['date']),
      availableCash: (json['availableCash'] as num).toDouble(),
      positionShares: json['positionShares'] as int,
      positionValue: (json['positionValue'] as num).toDouble(),
      totalCapital: (json['totalCapital'] as num).toDouble(),
      currentPrice: (json['currentPrice'] as num).toDouble(),
      floatingProfit: (json['floatingProfit'] as num).toDouble(),
    );
  }
}
