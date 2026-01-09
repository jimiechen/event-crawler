import 'package:flutter_test/flutter_test.dart';
import 'package:kliner_trainer/controllers/training_controller.dart';
import 'package:kliner_trainer/models/operation_record.dart';
import 'package:kliner_trainer/models/blind_test_config.dart';
import 'package:get/get.dart';

void main() {
  group('TrainingController', () {
    late TrainingController controller;

    setUp(() {
      TestWidgetsFlutterBinding.ensureInitialized();
      Get.testMode = true;
      controller = TrainingController();
    });

    tearDown(() {
      Get.reset();
    });

    test('should initialize with default values', () {
      expect(controller.currentSession.value, isNull);
      expect(controller.currentMode.value, BlindTestMode.beginner);
      expect(controller.score.value, 0);
      expect(controller.sessionCount.value, 0);
      expect(controller.positionLevel.value, 0);
      expect(controller.totalCapital.value, 1000000.0);
      expect(controller.currentPositionValue.value, 0.0);
      expect(controller.holdingStocks.isEmpty, true);
      expect(controller.sessionOperations.isEmpty, true);
      expect(controller.isLoading.value, false);
    });

    test('should change mode correctly', () {
      controller.changeMode(BlindTestMode.intermediate);

      expect(controller.currentMode.value, BlindTestMode.intermediate);
      expect(controller.currentConfig.value.showExpma, true);
      expect(controller.currentConfig.value.showVolumeMA, false);
      expect(controller.currentConfig.value.dataLength, 40);
    });

    test('should change to advanced mode', () {
      controller.changeMode(BlindTestMode.advanced);

      expect(controller.currentMode.value, BlindTestMode.advanced);
      expect(controller.currentConfig.value.showExpma, false);
      expect(controller.currentConfig.value.showVolumeMA, false);
      expect(controller.currentConfig.value.dataLength, 30);
    });

    test('should change to master mode', () {
      controller.changeMode(BlindTestMode.master);

      expect(controller.currentMode.value, BlindTestMode.master);
      expect(controller.currentConfig.value.showExpma, false);
      expect(controller.currentConfig.value.showCurrentPrice, false);
      expect(controller.currentConfig.value.dataLength, 20);
    });

    test('should get training stats', () {
      final stats = controller.getTrainingStats();

      expect(stats.containsKey('totalSessions'), true);
      expect(stats.containsKey('totalScore'), true);
      expect(stats.containsKey('totalProfit'), true);
      expect(stats.containsKey('avgScore'), true);
      expect(stats.containsKey('currentCapital'), true);
      expect(stats.containsKey('currentPosition'), true);
    });

    test('should have initial capital of 1,000,000', () {
      expect(controller.totalCapital.value, 1000000.0);
    });

    test('should have initial position value of 0', () {
      expect(controller.currentPositionValue.value, 0.0);
    });

    test('should have initial position level of 0', () {
      expect(controller.positionLevel.value, 0);
    });

    test('should have initial score of 0', () {
      expect(controller.score.value, 0);
    });

    test('should have initial session count of 0', () {
      expect(controller.sessionCount.value, 0);
    });

    test('should have empty holding stocks initially', () {
      expect(controller.holdingStocks.isEmpty, true);
    });

    test('should have empty session operations initially', () {
      expect(controller.sessionOperations.isEmpty, true);
    });

    test('should not be loading initially', () {
      expect(controller.isLoading.value, false);
    });

    test('should have CSVDataService instance', () {
      expect(controller.csvService, isNotNull);
    });

    test('should have StorageService instance', () {
      expect(controller.storageService, isNotNull);
    });

    test('should have current session reactive variable', () {
      expect(controller.currentSession, isA<Rx>());
    });

    test('should have current mode reactive variable', () {
      expect(controller.currentMode, isA<Rx>());
    });

    test('should have current config reactive variable', () {
      expect(controller.currentConfig, isA<Rx>());
    });

    test('should have score reactive variable', () {
      expect(controller.score, isA<RxInt>());
    });

    test('should have session count reactive variable', () {
      expect(controller.sessionCount, isA<RxInt>());
    });

    test('should have position level reactive variable', () {
      expect(controller.positionLevel, isA<RxInt>());
    });

    test('should have total capital reactive variable', () {
      expect(controller.totalCapital, isA<RxDouble>());
    });

    test('should have current position value reactive variable', () {
      expect(controller.currentPositionValue, isA<RxDouble>());
    });

    test('should have holding stocks reactive list', () {
      expect(controller.holdingStocks, isA<RxList<String>>());
    });

    test('should have session operations reactive list', () {
      expect(controller.sessionOperations, isA<RxList<OperationRecord>>());
    });

    test('should have loading reactive variable', () {
      expect(controller.isLoading, isA<RxBool>());
    });
  });
}
