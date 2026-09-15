import os

today_code = """import 'dart:async';
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

class _TodayScreenState extends State<TodayScreen> with WidgetsBindingObserver {
  final AttendanceService _attendanceService = AttendanceService();
  final CalendarService _calendarService = CalendarService();
  final NotificationService _notificationService = NotificationService.instance;

  AttendanceRecord? _todayRecord;
  DayCategory _dayCategory = DayCategory.workday;
  bool _isLoading = true;

  late Timer _clockTimer;
  DateTime _currentClock = DateTime.now();

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
    setState(() => _isLoading = true);

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
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _handleCheckIn() async {
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
                const Icon(Icons.check_circle_rounded, color: Colors.white),
                const SizedBox(width: 8),
                Text('上班签到成功：${updated.checkInTime}，打卡完成！'),
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
                Text('下班签退成功：${updated.checkOutTime}，辛苦啦！'),
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
    final timeHoursMins = DateFormat('HH:mm').format(now);
    final timeSeconds = DateFormat('ss').format(now);

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
            : SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
                child: Column(
                  children: [
                    // Header Date & Workday Capsule
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              dateStr,
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF0F172A),
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              weekdayStr,
                              style: const TextStyle(fontSize: 13, color: AppTheme.slateGrey),
                            ),
                          ],
                        ),
                        CapsuleBadge(
                          text: _dayCategory.label,
                          icon: _dayCategory.isWorkday ? Icons.work_outline : Icons.beach_access_rounded,
                          color: _dayCategory.isWorkday ? AppTheme.primaryBlue : AppTheme.emeraldGreen,
                          fontSize: 12,
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),

                    // Big Circular Punch Dashboard: Morning Check-in
                    _buildPunchDashboardCard(
                      title: '上班签到',
                      scheduleTip: '工作日 08:10 起多批次提醒',
                      isDone: hasIn,
                      recordedTime: _todayRecord?.checkInTime,
                      accentColors: const [Color(0xFF3B82F6), Color(0xFF06B6D4)],
                      icon: Icons.wb_sunny_rounded,
                      onTap: hasIn ? null : _handleCheckIn,
                    ),

                    const SizedBox(height: 20),

                    // Big Circular Punch Dashboard: Evening Check-out
                    _buildPunchDashboardCard(
                      title: '下班签退',
                      scheduleTip: '工作日 18:05 起循环提醒',
                      isDone: hasOut,
                      recordedTime: _todayRecord?.checkOutTime,
                      accentColors: const [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                      icon: Icons.nightlight_round,
                      onTap: hasOut ? null : _handleCheckOut,
                    ),

                    const SizedBox(height: 24),

                    // Ambient ticking time pill
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.8),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: AppTheme.softShadow(blur: 10),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.schedule_rounded, size: 16, color: AppTheme.slateGrey),
                          const SizedBox(width: 8),
                          Text(
                            '当前本地时间  $timeHoursMins:$timeSeconds',
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF0F172A),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 100),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildPunchDashboardCard({
    required String title,
    required String scheduleTip,
    required bool isDone,
    required String? recordedTime,
    required List<Color> accentColors,
    required IconData icon,
    required VoidCallback? onTap,
  }) {
    return GlassCard(
      padding: const EdgeInsets.all(22),
      borderRadius: 28,
      backgroundColor: Colors.white.withValues(alpha: isDone ? 0.94 : 0.88),
      border: Border.all(
        color: isDone ? AppTheme.emeraldGreen.withValues(alpha: 0.35) : Colors.white.withValues(alpha: 0.95),
        width: 1.5,
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: (isDone ? AppTheme.emeraldGreen : accentColors.first).withValues(alpha: 0.12),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      icon,
                      size: 20,
                      color: isDone ? AppTheme.emeraldGreen : accentColors.first,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    title,
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                  ),
                ],
              ),
              if (isDone)
                const CapsuleBadge(
                  text: '已完成',
                  icon: Icons.check_circle_rounded,
                  color: AppTheme.emeraldGreen,
                )
              else
                CapsuleBadge(
                  text: '待打卡',
                  color: AppTheme.slateGrey,
                  backgroundColor: const Color(0xFFF1F5F9),
                ),
            ],
          ),

          const SizedBox(height: 20),

          // Central Large Tactile Radial Button
          GestureDetector(
            onTap: onTap,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 250),
              width: 136,
              height: 136,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: isDone
                    ? const LinearGradient(
                        colors: [Color(0xFF10B981), Color(0xFF059669)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      )
                    : LinearGradient(
                        colors: accentColors,
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                boxShadow: isDone
                    ? AppTheme.glowShadow(AppTheme.emeraldGreen, blur: 18)
                    : AppTheme.glowShadow(accentColors.first, blur: 20),
                border: Border.all(
                  color: Colors.white.withValues(alpha: 0.4),
                  width: 3,
                ),
              ),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isDone ? Icons.done_all_rounded : Icons.touch_app_rounded,
                      color: Colors.white,
                      size: 32,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      isDone ? '打卡成功' : '立即$title',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (isDone && recordedTime != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        recordedTime,
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.9),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 16),
          Text(
            isDone ? '已在本地安全记录，提醒已自动取消' : scheduleTip,
            style: const TextStyle(fontSize: 12, color: AppTheme.slateGrey),
          ),
        ],
      ),
    );
  }
}
"""

with open('lib/screens/today_screen.dart', 'w', encoding='utf-8') as f:
    f.write(today_code.strip() + '\n')

print('today_screen redesigned with radial dashboard punch buttons.')
