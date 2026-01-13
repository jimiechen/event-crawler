import '../models/operation_record.dart';

class StorageService {
  final List<OperationRecord> _operations = [];
  final Map<String, dynamic> _stats = {
    'totalSessions': 0,
    'totalScore': 0,
    'totalProfit': 0.0,
  };
  
  final Map<String, int> _dailyRounds = {};

  Future<void> init() async {
    // TODO: Initialize Hive or SharedPrefs here
  }
  
  void incrementDailyRound(DateTime date) {
    final key = _dateKey(date);
    _dailyRounds[key] = (_dailyRounds[key] ?? 0) + 1;
  }
  
  int getDailyRounds(DateTime date) {
    return _dailyRounds[_dateKey(date)] ?? 0;
  }
  
  bool isDailyTargetAchieved(DateTime date) {
    return getDailyRounds(date) >= 10;
  }
  
  String _dateKey(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  Future<void> saveOperation(OperationRecord operation) async {
    _operations.add(operation);
    await _updateStats(operation);
  }
  
  Future<List<OperationRecord>> getAllOperations() async {
    return List.from(_operations)
      ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
  }
  
  Future<void> clearAllOperations() async {
    _operations.clear();
    _stats['totalSessions'] = 0;
    _stats['totalScore'] = 0;
    _stats['totalProfit'] = 0.0;
  }
  
  Future<void> _updateStats(OperationRecord operation) async {
    _stats['totalSessions'] = (_stats['totalSessions'] as int) + 1;
    _stats['totalScore'] = (_stats['totalScore'] as int) + operation.points;
    if (operation.profit != null) {
      _stats['totalProfit'] = (_stats['totalProfit'] as double) + operation.profit!;
    }
  }
  
  Map<String, dynamic> getStats() {
    final totalSessions = _stats['totalSessions'] as int;
    return {
      'totalSessions': totalSessions,
      'totalScore': _stats['totalScore'] as int,
      'totalProfit': _stats['totalProfit'] as double,
      'avgScore': totalSessions > 0 ? (_stats['totalScore'] as int) / totalSessions : 0.0,
    };
  }
  
  final List<Map<String, dynamic>> _trainingHistory = [];

  Future<void> saveTrainingResult(Map<String, dynamic> result) async {
    _trainingHistory.add(result);
    // 暂时只打印，后续可保存到本地数据库
    print('Training Result Saved: $result');
  }
  
  double getWinRate() {
    if (_trainingHistory.isEmpty) return 0.0;
    final wins = _trainingHistory.where((r) => (r['profit'] as num) > 0).length;
    return (wins / _trainingHistory.length) * 100;
  }

  Future<void> close() async {
    
  }
}
