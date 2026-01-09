class StockData {
  final String code;
  final DateTime date;
  final double open;
  final double high;
  final double low;
  final double close;
  final double prevClose;
  final double change;
  final double changePercent;
  final double volume;
  final double amount;
  
  double expma5 = 0.0;
  double expma13 = 0.0;
  double volumeMa5 = 0.0;
  double volumeMa60 = 0.0;
  bool isLowVolume = false;
  
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
  
  factory StockData.fromCSV(List<String> values) {
    return StockData(
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
  }
  
  bool get isBullish => close >= open;
  double get priceRange => high - low;
}
