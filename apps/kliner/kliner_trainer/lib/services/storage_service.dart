import '../models/operation_record.dart';

class StorageService {
  final List<OperationRecord> _operations = [];
  final Map<String, dynamic> _stats = {
    'totalSessions': 0,
    'totalScore': 0,
    'totalProfit': 0.0,
  };
  
  Future<void> init() async {
    
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
  
  Future<void> close() async {
    
  }
}
