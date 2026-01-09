import 'package:flutter_test/flutter_test.dart';
import 'package:kliner_trainer/models/blind_test_config.dart';

void main() {
  group('BlindTestConfig', () {
    test('should create default config', () {
      final config = const BlindTestConfig();

      expect(config.showExpma, true);
      expect(config.showVolumeMA, true);
      expect(config.showLowVolumeAlert, true);
      expect(config.showCurrentPrice, true);
      expect(config.showStockInfo, false);
      expect(config.dataLength, 60);
      expect(config.hideDate, true);
      expect(config.hideCode, true);
    });

    test('should create config with custom values', () {
      final config = const BlindTestConfig(
        showExpma: false,
        showVolumeMA: false,
        showLowVolumeAlert: false,
        showCurrentPrice: false,
        showStockInfo: true,
        dataLength: 30,
        hideDate: false,
        hideCode: false,
      );

      expect(config.showExpma, false);
      expect(config.showVolumeMA, false);
      expect(config.showLowVolumeAlert, false);
      expect(config.showCurrentPrice, false);
      expect(config.showStockInfo, true);
      expect(config.dataLength, 30);
      expect(config.hideDate, false);
      expect(config.hideCode, false);
    });

    test('should create beginner mode config', () {
      final config = BlindTestConfig.fromMode(BlindTestMode.beginner);

      expect(config.showExpma, true);
      expect(config.showVolumeMA, true);
      expect(config.showLowVolumeAlert, true);
      expect(config.showCurrentPrice, true);
      expect(config.showStockInfo, false);
      expect(config.dataLength, 60);
      expect(config.hideDate, true);
      expect(config.hideCode, true);
    });

    test('should create intermediate mode config', () {
      final config = BlindTestConfig.fromMode(BlindTestMode.intermediate);

      expect(config.showExpma, true);
      expect(config.showVolumeMA, false);
      expect(config.showLowVolumeAlert, false);
      expect(config.showCurrentPrice, true);
      expect(config.showStockInfo, false);
      expect(config.dataLength, 40);
      expect(config.hideDate, true);
      expect(config.hideCode, true);
    });

    test('should create advanced mode config', () {
      final config = BlindTestConfig.fromMode(BlindTestMode.advanced);

      expect(config.showExpma, false);
      expect(config.showVolumeMA, false);
      expect(config.showLowVolumeAlert, false);
      expect(config.showCurrentPrice, true);
      expect(config.showStockInfo, false);
      expect(config.dataLength, 30);
      expect(config.hideDate, true);
      expect(config.hideCode, true);
    });

    test('should create master mode config', () {
      final config = BlindTestConfig.fromMode(BlindTestMode.master);

      expect(config.showExpma, false);
      expect(config.showVolumeMA, false);
      expect(config.showLowVolumeAlert, false);
      expect(config.showCurrentPrice, false);
      expect(config.showStockInfo, false);
      expect(config.dataLength, 20);
      expect(config.hideDate, true);
      expect(config.hideCode, true);
    });

    test('should get mode name for all modes', () {
      final config = const BlindTestConfig();

      expect(config.getModeName(BlindTestMode.beginner), '初学者模式');
      expect(config.getModeName(BlindTestMode.intermediate), '中级模式');
      expect(config.getModeName(BlindTestMode.advanced), '高级模式');
      expect(config.getModeName(BlindTestMode.master), '大师模式');
    });

    test('should get mode description for all modes', () {
      final config = const BlindTestConfig();

      expect(
        config.getModeDescription(BlindTestMode.beginner),
        '显示全部指标\n60天数据',
      );
      expect(
        config.getModeDescription(BlindTestMode.intermediate),
        '隐藏成交量指标\n40天数据',
      );
      expect(
        config.getModeDescription(BlindTestMode.advanced),
        '只显示K线\n30天数据',
      );
      expect(
        config.getModeDescription(BlindTestMode.master),
        '完全双盲\n20天数据',
      );
    });

    test('should handle all blind test modes', () {
      final modes = [
        BlindTestMode.beginner,
        BlindTestMode.intermediate,
        BlindTestMode.advanced,
        BlindTestMode.master,
      ];

      for (final mode in modes) {
        final config = BlindTestConfig.fromMode(mode);
        expect(config.dataLength, greaterThan(0));
        expect(config.dataLength, lessThanOrEqualTo(60));
      }
    });
  });
}
