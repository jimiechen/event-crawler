import 'package:flutter_test/flutter_test.dart';
import 'package:kliner_trainer/models/operation_record.dart';
import 'package:kliner_trainer/services/storage_service.dart';

void main() {
  group('StorageService', () {
    late StorageService storageService;

    setUp(() {
      storageService = StorageService();
    });

    test('should initialize without errors', () async {
      await storageService.init();
      expect(storageService, isNotNull);
    });

    test('should save operation', () async {
      final operation = OperationRecord(
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

      await storageService.saveOperation(operation);

      final operations = await storageService.getAllOperations();
      expect(operations.length, 1);
      expect(operations.first.id, 'test-id');
    });

    test('should save multiple operations', () async {
      final operations = [
        OperationRecord(
          id: 'test-id-1',
          timestamp: DateTime(2023, 1, 1),
          type: OperationType.buy,
          positionLevel: 3,
          price: 10.50,
          stockCode: '603601.SH',
          stockName: '测试股票',
          stockDate: DateTime(2023, 1, 1),
          reason: '测试理由1',
        ),
        OperationRecord(
          id: 'test-id-2',
          timestamp: DateTime(2023, 1, 2),
          type: OperationType.sell,
          positionLevel: 2,
          price: 11.50,
          stockCode: '603601.SH',
          stockName: '测试股票',
          stockDate: DateTime(2023, 1, 2),
          reason: '测试理由2',
        ),
      ];

      for (final op in operations) {
        await storageService.saveOperation(op);
      }

      final savedOperations = await storageService.getAllOperations();
      expect(savedOperations.length, 2);
    });

    test('should get all operations sorted by timestamp', () async {
      final operations = [
        OperationRecord(
          id: 'test-id-1',
          timestamp: DateTime(2023, 1, 2),
          type: OperationType.buy,
          positionLevel: 3,
          price: 10.50,
          stockCode: '603601.SH',
          stockName: '测试股票',
          stockDate: DateTime(2023, 1, 2),
          reason: '测试理由1',
        ),
        OperationRecord(
          id: 'test-id-2',
          timestamp: DateTime(2023, 1, 1),
          type: OperationType.sell,
          positionLevel: 2,
          price: 11.50,
          stockCode: '603601.SH',
          stockName: '测试股票',
          stockDate: DateTime(2023, 1, 1),
          reason: '测试理由2',
        ),
      ];

      for (final op in operations) {
        await storageService.saveOperation(op);
      }

      final savedOperations = await storageService.getAllOperations();
      expect(savedOperations.length, 2);
      expect(savedOperations.first.id, 'test-id-1');
      expect(savedOperations.last.id, 'test-id-2');
    });

    test('should get initial stats', () async {
      final stats = storageService.getStats();

      expect(stats['totalSessions'], 0);
      expect(stats['totalScore'], 0);
      expect(stats['totalProfit'], 0.0);
      expect(stats['avgScore'], 0.0);
    });

    test('should update stats after saving operation', () async {
      final operation = OperationRecord(
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

      operation.points = 10;

      await storageService.saveOperation(operation);

      final stats = storageService.getStats();
      expect(stats['totalSessions'], 1);
      expect(stats['totalScore'], 10);
      expect(stats['avgScore'], 10.0);
    });

    test('should calculate average score correctly', () async {
      final operations = [
        OperationRecord(
          id: 'test-id-1',
          timestamp: DateTime(2023, 1, 1),
          type: OperationType.buy,
          positionLevel: 3,
          price: 10.50,
          stockCode: '603601.SH',
          stockName: '测试股票',
          stockDate: DateTime(2023, 1, 1),
          reason: '测试理由1',
        )..points = 10,
        OperationRecord(
          id: 'test-id-2',
          timestamp: DateTime(2023, 1, 2),
          type: OperationType.sell,
          positionLevel: 2,
          price: 11.50,
          stockCode: '603601.SH',
          stockName: '测试股票',
          stockDate: DateTime(2023, 1, 2),
          reason: '测试理由2',
        )..points = 15,
        OperationRecord(
          id: 'test-id-3',
          timestamp: DateTime(2023, 1, 3),
          type: OperationType.hold,
          positionLevel: 0,
          price: 10.50,
          stockCode: '603601.SH',
          stockName: '测试股票',
          stockDate: DateTime(2023, 1, 3),
          reason: '测试理由3',
        )..points = 5,
      ];

      for (final op in operations) {
        await storageService.saveOperation(op);
      }

      final stats = storageService.getStats();
      expect(stats['totalSessions'], 3);
      expect(stats['totalScore'], 30);
      expect(stats['avgScore'], 10.0);
    });

    test('should handle zero sessions for average score', () async {
      final stats = storageService.getStats();

      expect(stats['avgScore'], 0.0);
    });

    test('should update total profit when operation has profit', () async {
      final operation = OperationRecord(
        id: 'test-id',
        timestamp: DateTime(2023, 1, 1),
        type: OperationType.sell,
        positionLevel: 2,
        price: 10.50,
        stockCode: '603601.SH',
        stockName: '测试股票',
        stockDate: DateTime(2023, 1, 1),
        reason: '测试理由',
      );

      operation.profit = 100.50;

      await storageService.saveOperation(operation);

      final stats = storageService.getStats();
      expect(stats['totalProfit'], 100.50);
    });

    test('should not update total profit when operation has no profit', () async {
      final operation = OperationRecord(
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

      await storageService.saveOperation(operation);

      final stats = storageService.getStats();
      expect(stats['totalProfit'], 0.0);
    });

    test('should clear all operations', () async {
      final operation = OperationRecord(
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

      await storageService.saveOperation(operation);

      await storageService.clearAllOperations();

      final operations = await storageService.getAllOperations();
      expect(operations.length, 0);

      final stats = storageService.getStats();
      expect(stats['totalSessions'], 0);
      expect(stats['totalScore'], 0);
      expect(stats['totalProfit'], 0.0);
    });

    test('should close without errors', () async {
      await storageService.close();
      expect(storageService, isNotNull);
    });
  });
}
