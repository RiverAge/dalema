import os

main_navigation_code = """import 'dart:ui';
import 'package:flutter/material.dart';
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
      extendBody: true, // Allows glassmorphism navigation bar to float above body
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: _buildFloatingIslandNavBar(),
    );
  }

  Widget _buildFloatingIslandNavBar() {
    return SafeArea(
      child: Container(
        margin: const EdgeInsets.only(left: 24, right: 24, bottom: 12),
        height: 66,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(34),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.85),
                borderRadius: BorderRadius.circular(34),
                border: Border.all(
                  color: Colors.white.withValues(alpha: 0.95),
                  width: 1.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF0F172A).withValues(alpha: 0.12),
                    blurRadius: 24,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavIslandItem(0, Icons.verified_rounded, '今日打卡'),
                  _buildNavIslandItem(1, Icons.calendar_month_rounded, '考勤日历'),
                  _buildNavIslandItem(2, Icons.tune_rounded, '设置'),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavIslandItem(int index, IconData icon, String label) {
    final isSelected = _currentIndex == index;

    return GestureDetector(
      onTap: () {
        setState(() {
          _currentIndex = index;
        });
      },
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 240),
        curve: Curves.easeOutCubic,
        padding: EdgeInsets.symmetric(
          horizontal: isSelected ? 16 : 12,
          vertical: 8,
        ),
        decoration: BoxDecoration(
          gradient: isSelected
              ? const LinearGradient(
                  colors: [AppTheme.primaryBlue, Color(0xFF2563EB)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : null,
          color: isSelected ? null : Colors.transparent,
          borderRadius: BorderRadius.circular(24),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: AppTheme.primaryBlue.withValues(alpha: 0.35),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ]
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 20,
              color: isSelected ? Colors.white : AppTheme.slateGrey,
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
    f.write(main_navigation_code.strip() + '\n')
print('main.dart updated with Floating Island Glass Navbar.')
