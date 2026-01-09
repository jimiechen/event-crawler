import 'package:flutter_test/flutter_test.dart';
import 'package:kliner_trainer/models/blind_test_session.dart';
import 'package:kliner_trainer/models/stock_data.dart';

void main() {
  group('BlindTestSession', () {
    test('should create BlindTestSession with required fields', () {
      final data = [
        StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, 1),
          open: 10.50,
          high: 10.80,
          low: 10.30,
          close: 10.70,
          prevClose: 10.50,
          change: 0.20,
          changePercent: 1.90,
          volume: 10000,
          amount: 107000,
        ),
      ];

      final session = BlindTestSession(
        stockCode: '603601.SH',
        stockName: '测试股票',
        data: data,
        startDate: DateTime(2023, 1, 1),
        endDate: DateTime(2023, 1, 31),
      );

      expect(session.stockCode, '603601.SH');
      expect(session.stockName, '测试股票');
      expect(session.data, data);
      expect(session.startDate, DateTime(2023, 1, 1));
      expect(session.endDate, DateTime(2023, 1, 31));
      expect(session.userOperation, isNull);
    });

    test('should calculate current price from last data point', () {
      final data = [
        StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, 1),
          open: 10.50,
          high: 10.80,
          low: 10.30,
          close: 10.70,
          prevClose: 10.50,
          change: 0.20,
          changePercent: 1.90,
          volume: 10000,
          amount: 107000,
        ),
        StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, 2),
          open: 10.70,
          high: 11.00,
          low: 10.60,
          close: 10.90,
          prevClose: 10.70,
          change: 0.20,
          changePercent: 1.87,
          volume: 12000,
          amount: 130800,
        ),
      ];

      final session = BlindTestSession(
        stockCode: '603601.SH',
        stockName: '测试股票',
        data: data,
        startDate: DateTime(2023, 1, 1),
        endDate: DateTime(2023, 1, 31),
      );

      expect(session.currentPrice, 10.90);
    });

    test('should calculate change percent', () {
      final data = [
        StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, 1),
          open: 10.50,
          high: 10.80,
          low: 10.30,
          close: 10.00,
          prevClose: 10.50,
          change: -0.50,
          changePercent: -4.76,
          volume: 10000,
          amount: 107000,
        ),
        StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, 2),
          open: 10.00,
          high: 10.20,
          low: 9.90,
          close: 10.50,
          prevClose: 10.00,
          change: 0.50,
          changePercent: 5.00,
          volume: 12000,
          amount: 126000,
        ),
      ];

      final session = BlindTestSession(
        stockCode: '603601.SH',
        stockName: '测试股票',
        data: data,
        startDate: DateTime(2023, 1, 1),
        endDate: DateTime(2023, 1, 31),
      );

      expect(session.changePercent, 5.0);
    });

    test('should return 0 change percent for empty data', () {
      final session = BlindTestSession(
        stockCode: '603601.SH',
        stockName: '测试股票',
        data: [],
        startDate: DateTime(2023, 1, 1),
        endDate: DateTime(2023, 1, 31),
      );

      expect(session.changePercent, 0.0);
    });

    test('should identify hold signal for insufficient data', () {
      final data = List.generate(
        10,
        (i) => StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, i + 1),
          open: 10.50,
          high: 10.80,
          low: 10.30,
          close: 10.70,
          prevClose: 10.50,
          change: 0.20,
          changePercent: 1.90,
          volume: 10000,
          amount: 107000,
        ),
      );

      final session = BlindTestSession(
        stockCode: '603601.SH',
        stockName: '测试股票',
        data: data,
        startDate: DateTime(2023, 1, 1),
        endDate: DateTime(2023, 1, 31),
      );

      expect(session.technicalSignal, TradingSignal.hold);
    });

    test('should identify golden cross signal', () {
      final data = List.generate(
        14,
        (i) => StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, i + 1),
          open: 10.50,
          high: 10.80,
          low: 10.30,
          close: 10.70,
          prevClose: 10.50,
          change: 0.20,
          changePercent: 1.90,
          volume: 10000,
          amount: 107000,
        ),
      );

      data[12].expma5 = 10.50;
      data[12].expma13 = 10.60;
      data[13].expma5 = 10.70;
      data[13].expma13 = 10.55;
      data[13].isLowVolume = false;

      final session = BlindTestSession(
        stockCode: '603601.SH',
        stockName: '测试股票',
        data: data,
        startDate: DateTime(2023, 1, 1),
        endDate: DateTime(2023, 1, 31),
      );

      expect(session.technicalSignal, TradingSignal.buy);
    });

    test('should identify strong buy signal with golden cross and low volume', () {
      final data = List.generate(
        14,
        (i) => StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, i + 1),
          open: 10.50,
          high: 10.80,
          low: 10.30,
          close: 10.70,
          prevClose: 10.50,
          change: 0.20,
          changePercent: 1.90,
          volume: 10000,
          amount: 107000,
        ),
      );

      data[12].expma5 = 10.50;
      data[12].expma13 = 10.60;
      data[13].expma5 = 10.70;
      data[13].expma13 = 10.55;
      data[13].isLowVolume = true;

      final session = BlindTestSession(
        stockCode: '603601.SH',
        stockName: '测试股票',
        data: data,
        startDate: DateTime(2023, 1, 1),
        endDate: DateTime(2023, 1, 31),
      );

      expect(session.technicalSignal, TradingSignal.strongBuy);
    });

    test('should identify death cross signal', () {
      final data = List.generate(
        14,
        (i) => StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, i + 1),
          open: 10.50,
          high: 10.80,
          low: 10.30,
          close: 10.70,
          prevClose: 10.50,
          change: 0.20,
          changePercent: 1.90,
          volume: 10000,
          amount: 107000,
        ),
      );

      data[12].expma5 = 10.70;
      data[12].expma13 = 10.60;
      data[13].expma5 = 10.50;
      data[13].expma13 = 10.65;

      final session = BlindTestSession(
        stockCode: '603601.SH',
        stockName: '测试股票',
        data: data,
        startDate: DateTime(2023, 1, 1),
        endDate: DateTime(2023, 1, 31),
      );

      expect(session.technicalSignal, TradingSignal.sell);
    });

    test('should identify hold signal when no cross detected', () {
      final data = List.generate(
        14,
        (i) => StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, i + 1),
          open: 10.50,
          high: 10.80,
          low: 10.30,
          close: 10.70,
          prevClose: 10.50,
          change: 0.20,
          changePercent: 1.90,
          volume: 10000,
          amount: 107000,
        ),
      );

      data[12].expma5 = 10.50;
      data[12].expma13 = 10.60;
      data[13].expma5 = 10.55;
      data[13].expma13 = 10.65;

      final session = BlindTestSession(
        stockCode: '603601.SH',
        stockName: '测试股票',
        data: data,
        startDate: DateTime(2023, 1, 1),
        endDate: DateTime(2023, 1, 31),
      );

      expect(session.technicalSignal, TradingSignal.hold);
    });
  });
}
