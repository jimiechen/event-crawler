import 'package:flutter_test/flutter_test.dart';
import 'package:kliner_trainer/models/operation_record.dart';

void main() {
  group('OperationRecord', () {
    test('should create OperationRecord with all required fields', () {
      final record = OperationRecord(
        id: 'test-id',
        timestamp: DateTime(2023, 1, 1),
        type: OperationType.buy,
        positionLevel: 3,
        price: 10.50,
        stockCode: '603601.SH',
        stockName: '测试股票',
        stockDate: DateTime(2023, 1, 1),
        reason: '测试理由',
      );

      expect(record.id, 'test-id');
      expect(record.timestamp, DateTime(2023, 1, 1));
      expect(record.type, OperationType.buy);
      expect(record.positionLevel, 3);
      expect(record.price, 10.50);
      expect(record.stockCode, '603601.SH');
      expect(record.stockName, '测试股票');
      expect(record.stockDate, DateTime(2023, 1, 1));
      expect(record.reason, '测试理由');
      expect(record.profit, isNull);
      expect(record.points, 0);
    });

    test('should serialize to JSON', () {
      final record = OperationRecord(
        id: 'test-id',
        timestamp: DateTime(2023, 1, 1, 12, 30),
        type: OperationType.buy,
        positionLevel: 3,
        price: 10.50,
        stockCode: '603601.SH',
        stockName: '测试股票',
        stockDate: DateTime(2023, 1, 1),
        reason: '测试理由',
      );

      final json = record.toJson();

      expect(json['id'], 'test-id');
      expect(json['timestamp'], '2023-01-01T12:30:00.000');
      expect(json['type'], 'buy');
      expect(json['positionLevel'], 3);
      expect(json['price'], 10.50);
      expect(json['stockCode'], '603601.SH');
      expect(json['stockName'], '测试股票');
      expect(json['stockDate'], '2023-01-01T00:00:00.000');
      expect(json['reason'], '测试理由');
      expect(json['profit'], isNull);
      expect(json['points'], 0);
    });

    test('should deserialize from JSON', () {
      final json = {
        'id': 'test-id',
        'timestamp': '2023-01-01T12:30:00.000',
        'type': 'sell',
        'positionLevel': 2,
        'price': 10.50,
        'stockCode': '603601.SH',
        'stockName': '测试股票',
        'stockDate': '2023-01-01T00:00:00.000',
        'reason': '测试理由',
        'profit': 100.50,
        'points': 10,
      };

      final record = OperationRecord.fromJson(json);

      expect(record.id, 'test-id');
      expect(record.timestamp, DateTime(2023, 1, 1, 12, 30));
      expect(record.type, OperationType.sell);
      expect(record.positionLevel, 2);
      expect(record.price, 10.50);
      expect(record.stockCode, '603601.SH');
      expect(record.stockName, '测试股票');
      expect(record.stockDate, DateTime(2023, 1, 1));
      expect(record.reason, '测试理由');
      expect(record.profit, 100.50);
      expect(record.points, 10);
    });

    test('should handle invalid operation type in JSON', () {
      final json = {
        'id': 'test-id',
        'timestamp': '2023-01-01T12:30:00.000',
        'type': 'invalid',
        'positionLevel': 2,
        'price': 10.50,
        'stockCode': '603601.SH',
        'stockName': '测试股票',
        'stockDate': '2023-01-01T00:00:00.000',
        'reason': '测试理由',
      };

      final record = OperationRecord.fromJson(json);

      expect(record.type, OperationType.hold);
    });

    test('should handle null profit and points in JSON', () {
      final json = {
        'id': 'test-id',
        'timestamp': '2023-01-01T12:30:00.000',
        'type': 'buy',
        'positionLevel': 3,
        'price': 10.50,
        'stockCode': '603601.SH',
        'stockName': '测试股票',
        'stockDate': '2023-01-01T00:00:00.000',
        'reason': '测试理由',
      };

      final record = OperationRecord.fromJson(json);

      expect(record.profit, isNull);
      expect(record.points, 0);
    });

    test('should handle all operation types', () {
      final types = [OperationType.buy, OperationType.sell, OperationType.hold];

      for (final type in types) {
        final record = OperationRecord(
          id: 'test-id',
          timestamp: DateTime.now(),
          type: type,
          positionLevel: 1,
          price: 10.50,
          stockCode: '603601.SH',
          stockName: '测试股票',
          stockDate: DateTime.now(),
          reason: '测试理由',
        );

        expect(record.type, type);
      }
    });
  });
}
