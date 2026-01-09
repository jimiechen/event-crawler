enum BlindTestMode {
  beginner,
  intermediate,
  advanced,
  master,
}

class BlindTestConfig {
  final bool showExpma;
  final bool showVolumeMA;
  final bool showLowVolumeAlert;
  final bool showCurrentPrice;
  final bool showStockInfo;
  final int dataLength;
  final bool hideDate;
  final bool hideCode;

  const BlindTestConfig({
    this.showExpma = true,
    this.showVolumeMA = true,
    this.showLowVolumeAlert = true,
    this.showCurrentPrice = true,
    this.showStockInfo = false,
    this.dataLength = 60,
    this.hideDate = true,
    this.hideCode = true,
  });

  static BlindTestConfig fromMode(BlindTestMode mode) {
    switch (mode) {
      case BlindTestMode.beginner:
        return const BlindTestConfig(
          showExpma: true,
          showVolumeMA: true,
          showLowVolumeAlert: true,
          showCurrentPrice: true,
          showStockInfo: false,
          dataLength: 60,
          hideDate: true,
          hideCode: true,
        );
      case BlindTestMode.intermediate:
        return const BlindTestConfig(
          showExpma: true,
          showVolumeMA: false,
          showLowVolumeAlert: false,
          showCurrentPrice: true,
          showStockInfo: false,
          dataLength: 40,
          hideDate: true,
          hideCode: true,
        );
      case BlindTestMode.advanced:
        return const BlindTestConfig(
          showExpma: false,
          showVolumeMA: false,
          showLowVolumeAlert: false,
          showCurrentPrice: true,
          showStockInfo: false,
          dataLength: 30,
          hideDate: true,
          hideCode: true,
        );
      case BlindTestMode.master:
        return const BlindTestConfig(
          showExpma: false,
          showVolumeMA: false,
          showLowVolumeAlert: false,
          showCurrentPrice: false,
          showStockInfo: false,
          dataLength: 20,
          hideDate: true,
          hideCode: true,
        );
    }
  }

  String getModeName(BlindTestMode mode) {
    switch (mode) {
      case BlindTestMode.beginner:
        return '初学者模式';
      case BlindTestMode.intermediate:
        return '中级模式';
      case BlindTestMode.advanced:
        return '高级模式';
      case BlindTestMode.master:
        return '大师模式';
    }
  }

  String getModeDescription(BlindTestMode mode) {
    switch (mode) {
      case BlindTestMode.beginner:
        return '显示全部指标\n60天数据';
      case BlindTestMode.intermediate:
        return '隐藏成交量指标\n40天数据';
      case BlindTestMode.advanced:
        return '只显示K线\n30天数据';
      case BlindTestMode.master:
        return '完全双盲\n20天数据';
    }
  }
}
