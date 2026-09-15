import os

today_redesign_code = """import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../constants/app_theme.dart';
import '../models/attendance_record.dart';
import '../services/attendance_service.dart';
import '../services/calendar_service.dart';
import '../services/notification_service.dart';
import '../widgets/glass_components.dart';

class TodayScreen extends StatefulWidget {
  const TodayScreen({super.key});

  @override
  State<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen>
    with WidgetsBindingObserver, SingleTickerProviderStateMixin {
  final AttendanceService _attendanceService = AttendanceService();
  final CalendarService _calendarService = CalendarService();
  final NotificationService _notificationService = NotificationService.instance;

  AttendanceRecord? _todayRecord;
  DayCategory _dayCategory = DayCategory.workday;
  bool _isLoading = true;
  String? _errorMessage;

  // Real-time ticking clock
  late Timer _clockTimer;
  DateTime _currentClock = DateTime.now();

  // Bouncing touch animation controllers
  double _inScale = 1.0;
  double _outScale = 1.0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _clockTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          _currentClock = DateTime.now();
        });
      }
    });
    _loadTodayData();
  }

  @override
  void dispose() {
    _clockTimer.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _loadTodayData();
    }
  }

  Future<void> _loadTodayData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final now = DateTime.now();
      final record = await _attendanceService.getTodayRecord(now);
      final category = await _calendarService.getDayCategory(now);

      await _notificationService.rescheduleAllNotifications();

      if (mounted) {
        setState(() {
          _todayRecord = record;
          _dayCategory = category;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = '数据加载失败: $e';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _handleCheckIn() async {
    setState(() => _inScale = 0.95);
    await Future.delayed(const Duration(milliseconds: 100));
    setState(() => _inScale = 1.0);

    try {
      final updated = await _attendanceService.checkIn();
      setState(() {
        _todayRecord = updated;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.celebration_rounded, color: Colors.white),
                const SizedBox(width: 8),
                Text('上班签到成功：${updated.checkInTime}，今天也要加油！'),
              ],
            ),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppTheme.emeraldGreen,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('签到失败: ${e.toString()}'),
            backgroundColor: AppTheme.roseRed,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  Future<void> _handleCheckOut() async {
    setState(() => _outScale = 0.95);
    await Future.delayed(const Duration(milliseconds: 100));
    setState(() => _outScale = 1.0);

    try {
      final updated = await _attendanceService.checkOut();
      setState(() {
        _todayRecord = updated;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.nightlight_round, color: Colors.white),
                const SizedBox(width: 8),
                Text('下班签退成功：${updated.checkOutTime}，辛苦了一天，好好休息！'),
              ],
            ),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppTheme.emeraldGreen,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('签退失败: ${e.toString()}'),
            backgroundColor: AppTheme.roseRed,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  String _getWeekdayString(int weekday) {
    const names = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'];
    return names[weekday - 1];
  }

  @override
  Widget build(BuildContext context) {
    final now = _currentClock;
    final dateStr = DateFormat('MM月dd日').format(now);
    final weekdayStr = _getWeekdayString(now.weekday);
    final clockStr = DateFormat('HH:mm:ss').format(now);

    final hasIn = _todayRecord?.hasCheckIn ?? false;
    final hasOut = _todayRecord?.hasCheckOut ?? false;

    return Container(
      decoration: const BoxDecoration(
        gradient: AppTheme.ambientBg,
      ),
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text('今日打卡', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 19)),
          centerTitle: true,
          backgroundColor: Colors.transparent,
          surfaceTintColor: Colors.transparent,
          elevation: 0,
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh_rounded, color: AppTheme.slateGrey),
              tooltip: '刷新打卡状态',
              onPressed: _loadTodayData,
            ),
          ],
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _loadTodayData,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 8.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Ambient Greeting & Hero Clock
                      GlassCard(
                        padding: const EdgeInsets.all(22),
                        borderRadius: 28,
                        backgroundColor: Colors.white.withValues(alpha: 0.85),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      dateStr,
                                      style: const TextStyle(
                                        fontSize: 22,
                                        fontWeight: FontWeight.bold,
                                        color: Color(0xFF0F172A),
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      weekdayStr,
                                      style: const TextStyle(
                                        fontSize: 13,
                                        color: AppTheme.slateGrey,
                                      ),
                                    ),
                                  ],
                                ),
                                CapsuleBadge(
                                  text: _dayCategory.label,
                                  icon: _dayCategory.isWorkday ? Icons.work_outline : Icons.beach_access,
                                  color: _dayCategory.isWorkday ? AppTheme.primaryBlue : AppTheme.emeraldGreen,
                                ),
                              ],
                            ),

                            const SizedBox(height: 18),

                            // Real-time ticking digital clock display
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                borderRadius: BorderRadius.circular(20),
                                boxShadow: AppTheme.softShadow(blur: 16),
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  const Icon(Icons.access_time_filled, size: 20, color: AppTheme.accentCyan),
                                  const SizedBox(width: 10),
                                  Text(
                                    clockStr,
                                    style: const TextStyle(
                                      fontSize: 28,
                                      fontWeight: FontWeight.bold,
                                      letterSpacing: 2,
                                      color: Colors.white,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 18),

                      // Task 1: Check In (上班签到) Card with Spring Scale Effect
                      AnimatedScale(
                        scale: _inScale,
                        duration: const Duration(milliseconds: 150),
                        curve: Curves.easeOutBack,
                        child: _buildInteractivePunchCard(
                          title: '上班签到',
                          subTitle: '上午工作日提醒：08:10 起循环提醒',
                          icon: Icons.wb_sunny_rounded,
                          isDone: hasIn,
                          timeStr: _todayRecord?.checkInTime,
                          accentGradient: const [Color(0xFF3B82F6), Color(0xFF2563EB)],
                          glowColor: AppTheme.primaryBlue,
                          onPunch: hasIn ? null : _handleCheckIn,
                        ),
                      ),

                      const SizedBox(height: 16),

                      // Task 2: Check Out (下班签退) Card with Spring Scale Effect
                      AnimatedScale(
                        scale: _outScale,
                        duration: const Duration(milliseconds: 150),
                        curve: Curves.easeOutBack,
                        child: _buildInteractivePunchCard(
                          title: '下班签退',
                          subTitle: '晚间工作日提醒：18:05 起循环提醒',
                          icon: Icons.nightlight_round,
                          isDone: hasOut,
                          timeStr: _todayRecord?.checkOutTime,
                          accentGradient: const [Color(0xFF6366F1), Color(0xFF4F46E5)],
                          glowColor: const Color(0xFF6366F1),
                          onPunch: hasOut ? null : _handleCheckOut,
                        ),
                      ),

                      const SizedBox(height: 24),

                      // Friendly privacy & offline hint capsule
                      Center(
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.65),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: Colors.white.withValues(alpha: 0.8)),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.shield_outlined, size: 14, color: AppTheme.slateGrey),
                              SizedBox(width: 6),
                              Text(
                                '所有打卡数据完全保存在手机本地 · 安全离线',
                                style: TextStyle(fontSize: 11, color: AppTheme.slateGrey),
                              ),
                            ],
                          ),
                        ),
                      ),

                      const SizedBox(height: 90), // Bottom padding for floating navigation bar
                    ],
                  ),
                ),
              ),
      ),
    );
  }

  Widget _buildInteractivePunchCard({
    required String title,
    required String subTitle,
    required IconData icon,
    required bool isDone,
    required String? timeStr,
    required List<Color> accentGradient,
    required Color glowColor,
    required VoidCallback? onPunch,
  }) {
    return GlassCard(
      padding: const EdgeInsets.all(22),
      borderRadius: 26,
      backgroundColor: Colors.white.withValues(alpha: isDone ? 0.90 : 0.82),
      border: Border.all(
        color: isDone
            ? AppTheme.emeraldGreen.withValues(alpha: 0.45)
            : Colors.white.withValues(alpha: 0.95),
        width: isDone ? 1.8 : 1.2,
      ),
      shadows: isDone ? AppTheme.softShadow(color: AppTheme.emeraldGreen) : AppTheme.softShadow(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: isDone
                        ? [AppTheme.emeraldGreen, const Color(0xFF059669)]
                        : accentGradient,
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: AppTheme.glowShadow(isDone ? AppTheme.emeraldGreen : glowColor, blur: 12),
                ),
                child: Icon(icon, color: Colors.white, size: 26),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF0F172A),
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      isDone ? '打卡记录：$timeStr' : '状态：今日待完成',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: isDone ? FontWeight.bold : FontWeight.normal,
                        color: isDone ? AppTheme.emeraldGreen : AppTheme.slateGrey,
                      ),
                    ),
                  ],
                ),
              ),
              if (isDone)
                const CapsuleBadge(
                  text: '已完成',
                  icon: Icons.check_circle_rounded,
                  color: AppTheme.emeraldGreen,
                ),
            ],
          ),

          const SizedBox(height: 14),
          Text(subTitle, style: const TextStyle(fontSize: 12, color: AppTheme.slateGrey)),
          const SizedBox(height: 18),

          // Big tactile punch action button
          SizedBox(
            width: double.infinity,
            height: 52,
            child: DecoratedBox(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(18),
                gradient: isDone
                    ? null
                    : LinearGradient(
                        colors: accentGradient,
                        begin: Alignment.centerLeft,
                        end: Alignment.centerRight,
                      ),
                boxShadow: isDone ? null : AppTheme.glowShadow(glowColor, blur: 14),
              ),
              child: ElevatedButton(
                onPressed: onPunch,
                style: ElevatedButton.styleFrom(
                  backgroundColor: isDone ? const Color(0xFFF1F5F9) : Colors.transparent,
                  shadowColor: Colors.transparent,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(18),
                  ),
                ),
                child: Text(
                  isDone ? '今日已完成打卡' : '立即 $title',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: isDone ? Colors.black38 : Colors.white,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
"""

with open('lib/screens/today_screen.dart', 'w', encoding='utf-8') as f:
    f.write(today_redesign_code.strip() + '\n')
print('today_screen redesigned with glassmorphism, digital ticking clock, and spring touch.')
