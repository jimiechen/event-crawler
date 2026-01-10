import 'package:flutter_test/flutter_test.dart';
import 'package:kliner_trainer/models/stock_data.dart';
import 'package:kliner_trainer/services/indicator_calculator.dart';

void main() {
  group('IndicatorCalculator', () {
    test('should calculate EXPMA for single data point', () {
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

      IndicatorCalculator.calculateExpma(data);

      expect(data[0].expma5, 10.70);
      expect(data[0].expma13, 10.70);
    });

    test('should calculate EXPMA for multiple data points', () {
      final data = List.generate(
        20,
        (i) => StockData(
          code: '603601.SH',
          date: DateTime(2023, 1, i + 1),
          open: 10.50,
          high: 10.80,
          low: 10.30,
          close: 10.70 + i * 0.1,
          prevClose: 10.50,
          change: 0.20,
          changePercent: 1.90,
          volume: 10000,
          amount: 107000,
        ),
      );

      IndicatorCalculator.calculateExpma(data);

      expect(data[0].expma5, 10.70);
      expect(data[0].expma13, 10.70);

      expect(data[1].expma5, greaterThan(0));
      expect(data[1].expma13, greaterThan(0));

      expect(data[19].expma5, greaterThan(0));
      expect(data[19].expma13, greaterThan(0));
    });

    test('should handle empty data for EXPMA calculation', () {
      final data = <StockData>[];

      IndicatorCalculator.calculateExpma(data);

      expect(data.isEmpty, true);
    });

    test('should calculate volume MA for first data point', () {
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

      IndicatorCalculator.calculateVolumeMA(data);

      expect(data[0].volumeMa5, 10000);
      expect(data[0].volumeMa60, 10000);
      expect(data[0].isLowVolume, false);
    });

    test('should calculate volume MA5 for multiple data points', () {
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
          volume: 10000 + i * 1000,
          amount: 107000,
        ),
      );

      IndicatorCalculator.calculateVolumeMA(data);

      expect(data[4].volumeMa5, 12000);
      expect(data[9].volumeMa5, 12000);
    });

    test('should calculate volume MA60 for multiple data points', () {
      final data = List.generate(
        70,
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

      IndicatorCalculator.calculateVolumeMA(data);

      expect(data[59].volumeMa60, 10000);
      expect(data[69].volumeMa60, 10000);
    });

    test('should identify low volume correctly', () {
      final data = List.generate(
        60,
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

      IndicatorCalculator.calculateVolumeMA(data);

      expect(data[59].isLowVolume, false);
    });

    test('should handle empty data for volume MA calculation', () {
      final data = <StockData>[];

      IndicatorCalculator.calculateVolumeMA(data);

      expect(data.isEmpty, true);
    });

    test('should calculate all indicators together', () {
      final data = List.generate(
        70,
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

      IndicatorCalculator.calculateAllIndicators(data);

      for (int i = 0; i < data.length; i++) {
        expect(data[i].expma5, greaterThanOrEqualTo(0));
        expect(data[i].expma13, greaterThanOrEqualTo(0));
        expect(data[i].volumeMa5, greaterThanOrEqualTo(0));
        expect(data[i].volumeMa60, greaterThanOrEqualTo(0));
      }

      expect(data[59].isLowVolume, false);
    });

    test('should calculate EXPMA with correct smoothing', () {
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
          close: 11.00,
          prevClose: 10.00,
          change: 1.00,
          changePercent: 10.00,
          volume: 12000,
          amount: 132000,
        ),
      ];

      IndicatorCalculator.calculateExpma(data);

      const alpha5 = 2 / (5 + 1);
      const alpha13 = 2 / (13 + 1);

      final expectedExpma5_1 = alpha5 * 11.00 + (1 - alpha5) * 10.00;
      final expectedExpma13_1 = alpha13 * 11.00 + (1 - alpha13) * 10.00;

      expect(data[1].expma5, closeTo(expectedExpma5_1, 0.01));
      expect(data[1].expma13, closeTo(expectedExpma13_1, 0.01));
    });
  });
}
