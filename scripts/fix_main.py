import os

main_code = """import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'constants/app_theme.dart';
import 'screens/history_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/today_screen.dart';
import 'services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final notificationService = NotificationService.instance;
  await notificationService.init(
    onDidReceiveNotificationResponse: (NotificationResponse response) {},
  );

  await notificationService.requestPermissions();
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
        fontFamily: 'sans-serif',
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppTheme.primaryBlue,
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF8FAFC),
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
          backgroundColor: Colors.transparent,
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
      extendBody: true,
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: _buildOptimizedFloatingNavBar(),
    );
  }

  Widget _buildOptimizedFloatingNavBar() {
    return SafeArea(
      child: Container(
        margin: const EdgeInsets.only(left: 28, right: 28, bottom: 16),
        height: 62,
        decoration: BoxDecoration(
          color: const Color(0xFF0F172A),
          borderRadius: BorderRadius.circular(32),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF0F172A).withValues(alpha: 0.28),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildNavTab(0, Icons.verified_rounded, '今日打卡'),
            _buildNavTab(1, Icons.calendar_month_rounded, '考勤日历'),
            _buildNavTab(2, Icons.tune_rounded, '系统设置'),
          ],
        ),
      ),
    );
  }

  Widget _buildNavTab(int index, IconData icon, String label) {
    final isSelected = _currentIndex == index;

    return GestureDetector(
      onTap: () {
        if (_currentIndex != index) {
          setState(() {
            _currentIndex = index;
          });
        }
      },
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
        padding: EdgeInsets.symmetric(
          horizontal: isSelected ? 16 : 12,
          vertical: 8,
        ),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryBlue : Colors.transparent,
          borderRadius: BorderRadius.circular(22),
          boxShadow: isSelected ? AppTheme.glowShadow(AppTheme.primaryBlue, blur: 8) : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 20,
              color: isSelected ? Colors.white : const Color(0xFF94A3B8),
            ),
            if (isSelected) ...[
              const SizedBox(width: 6),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
"""

with open('lib/main.dart', 'w', encoding='utf-8') as f:
    f.write(main_code.strip() + '\n')

print('main.dart 60fps fast tab switching implemented.')
