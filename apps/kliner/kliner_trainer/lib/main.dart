import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'pages/training_page.dart';
import 'controllers/training_controller.dart';
import 'services/csv_data_service.dart';
import 'services/storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      initialBinding: BindingsBuilder(() {
        Get.put(CSVDataService());
        Get.put(StorageService());
        Get.put(TrainingController());
      }),
      title: 'K线双盲训练系统',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const TrainingPage(),
      debugShowCheckedModeBanner: false,
    );
  }
}
