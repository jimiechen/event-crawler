import '../models/stock_data.dart';

class IndicatorCalculator {
  static void calculateExpma(List<StockData> data) {
    if (data.isEmpty) return;
    
    data[0].expma5 = data[0].close;
    data[0].expma13 = data[0].close;
    
    const alpha5 = 2 / (5 + 1);
    const alpha13 = 2 / (13 + 1);
    
    for (int i = 1; i < data.length; i++) {
      data[i].expma5 = alpha5 * data[i].close + (1 - alpha5) * data[i-1].expma5;
      data[i].expma13 = alpha13 * data[i].close + (1 - alpha13) * data[i-1].expma13;
    }
  }
  
  static void calculateVolumeMA(List<StockData> data) {
    if (data.isEmpty) return;
    
    for (int i = 0; i < data.length; i++) {
      if (i < 4) {
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
      
      if (i < 59) {
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
      
      if (i >= 59) {
        data[i].isLowVolume = data[i].volume < data[i].volumeMa60 * 0.5;
      }
    }
  }
  
  static void calculateAllIndicators(List<StockData> data) {
    calculateExpma(data);
    calculateVolumeMA(data);
  }
}
