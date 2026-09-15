import os

main_code = """import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'screens/history_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/today_screen.dart';
import 'services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize notification service with payload handler
  final notificationService = NotificationService.instance;
  await notificationService.init(
    onDidReceiveNotificationResponse: (NotificationResponse response) {
      // When user clicks the notification or the action button, the app opens to the Today page
    },
  );

  // Request notifications and exact alarms permissions
  await notificationService.requestPermissions();

  // Initial scheduling of notifications for the upcoming workdays
  await notificationService.rescheduleAllNotifications();

  runApp(const DaleMaApp());
}

class DaleMaApp extends StatelessWidget {
  const DaleMaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '打卡了吗',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blueAccent,
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
      ),
      home: const MainNavigationScreen(),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    TodayScreen(),
    HistoryScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.check_circle_outline),
            selectedIcon: Icon(Icons.check_circle),
            label: '今日打卡',
          ),
          NavigationDestination(
            icon: Icon(Icons.history_outlined),
            selectedIcon: Icon(Icons.history),
            label: '历史记录',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: '设置',
          ),
        ],
      ),
    );
  }
}
"""

with open('lib/main.dart', 'w', encoding='utf-8') as f:
    f.write(main_code.strip() + '\n')
print('main.dart generated.')
