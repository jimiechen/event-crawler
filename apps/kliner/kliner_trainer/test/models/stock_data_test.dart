import 'package:flutter_test/flutter_test.dart';
import 'package:kliner_trainer/models/stock_data.dart';

void main() {
  group('StockData', () {
    test('should create StockData from CSV values', () {
      final values = [
        '603601.SH',
        '2023-01-01',
        '10.50',
        '10.80',
        '10.30',
        '10.70',
        '10.50',
        '0.20',
        '1.90',
        '10000',
        '107000',
      ];

      final stockData = StockData.fromCSV(values);

      expect(stockData.code, '603601.SH');
      expect(stockData.date, DateTime.parse('2023-01-01'));
      expect(stockData.open, 10.50);
      expect(stockData.high, 10.80);
      expect(stockData.low, 10.30);
      expect(stockData.close, 10.70);
      expect(stockData.prevClose, 10.50);
      expect(stockData.change, 0.20);
      expect(stockData.changePercent, 1.90);
      expect(stockData.volume, 10000);
      expect(stockData.amount, 107000);
    });

    test('should identify bullish candle', () {
      final stockData = StockData(
        code: '603601.SH',
        date: DateTime.now(),
        open: 10.50,
        high: 10.80,
        low: 10.30,
        close: 10.70,
        prevClose: 10.50,
        change: 0.20,
        changePercent: 1.90,
        volume: 10000,
        amount: 107000,
      );

      expect(stockData.isBullish, true);
    });

    test('should identify bearish candle', () {
      final stockData = StockData(
        code: '603601.SH',
        date: DateTime.now(),
        open: 10.70,
        high: 10.80,
        low: 10.30,
        close: 10.50,
        prevClose: 10.50,
        change: 0.00,
        changePercent: 0.00,
        volume: 10000,
        amount: 107000,
      );

      expect(stockData.isBullish, false);
    });

    test('should calculate price range', () {
      final stockData = StockData(
        code: '603601.SH',
        date: DateTime.now(),
        open: 10.50,
        high: 10.80,
        low: 10.30,
        close: 10.70,
        prevClose: 10.50,
        change: 0.20,
        changePercent: 1.90,
        volume: 10000,
        amount: 107000,
      );

      expect(stockData.priceRange, 0.50);
    });

    test('should handle edge case with zero price range', () {
      final stockData = StockData(
        code: '603601.SH',
        date: DateTime.now(),
        open: 10.50,
        high: 10.50,
        low: 10.50,
        close: 10.50,
        prevClose: 10.50,
        change: 0.00,
        changePercent: 0.00,
        volume: 10000,
        amount: 107000,
      );

      expect(stockData.priceRange, 0.0);
    });

    test('should initialize indicator fields with default values', () {
      final stockData = StockData(
        code: '603601.SH',
        date: DateTime.now(),
        open: 10.50,
        high: 10.80,
        low: 10.30,
        close: 10.70,
        prevClose: 10.50,
        change: 0.20,
        changePercent: 1.90,
        volume: 10000,
        amount: 107000,
      );

      expect(stockData.expma5, 0.0);
      expect(stockData.expma13, 0.0);
      expect(stockData.volumeMa5, 0.0);
      expect(stockData.volumeMa60, 0.0);
      expect(stockData.isLowVolume, false);
    });
  });
}
