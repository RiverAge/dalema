import os

today_screen_code = """import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/attendance_record.dart';
import '../services/attendance_service.dart';
import '../services/calendar_service.dart';
import '../services/notification_service.dart';

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
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _loadTodayData();
  }

  @override
  void dispose() {
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
          _errorMessage = '加载失败: $e';
          _isLoading = false;
        });
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
                const Icon(Icons.check_circle, color: Colors.white),
                const SizedBox(width: 8),
                Text('上班签到成功：${updated.checkInTime}，提醒已自动取消'),
              ],
            ),
            behavior: SnackBarBehavior.floating,
            backgroundColor: const Color(0xFF10B981),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('签到失败: ${e.toString()}'),
            backgroundColor: Colors.redAccent,
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
                const Icon(Icons.check_circle, color: Colors.white),
                const SizedBox(width: 8),
                Text('下班签退成功：${updated.checkOutTime}，提醒已自动取消'),
              ],
            ),
            behavior: SnackBarBehavior.floating,
            backgroundColor: const Color(0xFF10B981),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('签退失败: ${e.toString()}'),
            backgroundColor: Colors.redAccent,
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
    final now = DateTime.now();
    final dateStr = DateFormat('MM月dd日').format(now);
    final weekdayStr = _getWeekdayString(now.weekday);

    final hasIn = _todayRecord?.hasCheckIn ?? false;
    final hasOut = _todayRecord?.hasCheckOut ?? false;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text('今日打卡', style: TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
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
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (_errorMessage != null)
                      Container(
                        margin: const EdgeInsets.only(bottom: 16),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.red.shade200),
                        ),
                        child: Text(_errorMessage!, style: const TextStyle(color: Colors.red)),
                      ),

                    // Modern Header Card
                    Container(
                      padding: const EdgeInsets.all(22),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF2563EB), Color(0xFF1D4ED8), Color(0xFF1E40AF)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(24),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF2563EB).withValues(alpha: 0.25),
                            blurRadius: 18,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
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
                                      fontSize: 26,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.white,
                                      letterSpacing: 0.5,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    weekdayStr,
                                    style: const TextStyle(fontSize: 14, color: Colors.white70),
                                  ),
                                ],
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(20),
                                  border: Border.all(color: Colors.white.withValues(alpha: 0.25)),
                                ),
                                child: Text(
                                  _dayCategory.label,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            decoration: BoxDecoration(
                              color: Colors.black.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  _dayCategory.isWorkday ? Icons.work_outline : Icons.weekend_outlined,
                                  size: 16,
                                  color: Colors.white70,
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    _dayCategory.isWorkday
                                        ? '工作日打卡提醒已生效，完成后将自动取消当天后续闹铃'
                                        : '今日为休息日，默认不提醒；仍可随时手动打卡记录',
                                    style: const TextStyle(fontSize: 11, color: Colors.white),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Punch-In Card (上班签到)
                    _buildModernPunchCard(
                      title: '上班签到',
                      subTitle: '上午提醒批次：08:10、08:16、08:22、08:28',
                      icon: Icons.wb_sunny_rounded,
                      isDone: hasIn,
                      timeStr: _todayRecord?.checkInTime,
                      primaryColor: const Color(0xFF3B82F6),
                      onPunch: hasIn ? null : _handleCheckIn,
                    ),

                    const SizedBox(height: 16),

                    // Punch-Out Card (下班签退)
                    _buildModernPunchCard(
                      title: '下班签退',
                      subTitle: '晚间提醒批次：18:05 起至 19:30 循环提醒',
                      icon: Icons.nightlight_round,
                      isDone: hasOut,
                      timeStr: _todayRecord?.checkOutTime,
                      primaryColor: const Color(0xFF6366F1),
                      onPunch: hasOut ? null : _handleCheckOut,
                    ),

                    const SizedBox(height: 24),

                    // Footer Tip
                    Center(
                      child: Text(
                        '打卡记录仅保存在手机本地数据库，不连接外部服务器\\n每天仅可打卡一次，记录后不可擅自篡改',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.grey.shade500,
                          height: 1.6,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildModernPunchCard({
    required String title,
    required String subTitle,
    required IconData icon,
    required bool isDone,
    required String? timeStr,
    required Color primaryColor,
    required VoidCallback? onPunch,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(
          color: isDone ? const Color(0xFF10B981).withValues(alpha: 0.3) : Colors.transparent,
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.blueGrey.withValues(alpha: 0.06),
            blurRadius: 14,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: isDone
                      ? const Color(0xFF10B981).withValues(alpha: 0.12)
                      : primaryColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(
                  icon,
                  color: isDone ? const Color(0xFF10B981) : primaryColor,
                  size: 24,
                ),
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
                        color: Color(0xFF1E293B),
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      isDone ? '打卡时间：$timeStr' : '状态：待打卡',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: isDone ? FontWeight.bold : FontWeight.normal,
                        color: isDone ? const Color(0xFF10B981) : Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
              if (isDone)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check, size: 14, color: Colors.white),
                      SizedBox(width: 4),
                      Text('已完成', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
            ],
          ),

          const SizedBox(height: 14),
          Text(subTitle, style: TextStyle(fontSize: 12, color: Colors.grey.shade500)),
          const SizedBox(height: 16),

          // Big tactile action button
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton(
              onPressed: onPunch,
              style: ElevatedButton.styleFrom(
                backgroundColor: isDone ? const Color(0xFFF1F5F9) : primaryColor,
                foregroundColor: isDone ? Colors.grey : Colors.white,
                elevation: isDone ? 0 : 3,
                shadowColor: primaryColor.withValues(alpha: 0.4),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              child: Text(
                isDone ? '今日已完成打卡' : '立即 $title',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: isDone ? Colors.grey.shade500 : Colors.white,
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
    f.write(today_screen_code.strip() + '\n')

print('TodayScreen enhanced with modern design.')
