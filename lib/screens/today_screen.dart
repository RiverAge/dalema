import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
    try {
      final now = DateTime.now();
      final results = await Future.wait([
        _attendanceService.getTodayRecord(now),
        _calendarService.getDayCategory(now),
      ]);

      if (mounted) {
        setState(() {
          _todayRecord = results[0] as AttendanceRecord?;
          _dayCategory = results[1] as DayCategory;
        });
      }
    } catch (_) {}
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

  String? _calculateWorkDuration(String? inTime, String? outTime) {
    if (inTime == null) return null;
    try {
      final now = DateTime.now();
      final inParts = inTime.split(':').map(int.parse).toList();
      final inDt = DateTime(now.year, now.month, now.day, inParts[0], inParts[1]);

      DateTime endDt;
      if (outTime != null) {
        final outParts = outTime.split(':').map(int.parse).toList();
        endDt = DateTime(now.year, now.month, now.day, outParts[0], outParts[1]);
      } else {
        endDt = now;
      }

      final diff = endDt.difference(inDt);
      if (diff.isNegative) return null;
      final hours = diff.inHours;
      final minutes = diff.inMinutes % 60;
      if (hours == 0) {
        return '$minutes分钟';
      }
      return '$hours小时$minutes分钟';
    } catch (_) {
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final dateStr = DateFormat('MM月dd日').format(now);
    final weekdayStr = _getWeekdayString(now.weekday);

    final hasIn = _todayRecord?.hasCheckIn ?? false;
    final hasOut = _todayRecord?.hasCheckOut ?? false;
    final isBothDone = hasIn && hasOut;
    final workDuration = _calculateWorkDuration(_todayRecord?.checkInTime, _todayRecord?.checkOutTime);

    // Dynamic greeting & motivational subtitle
    String greeting;
    String motivation;
    if (isBothDone) {
      greeting = '今日圆满打卡';
      motivation = '已达标完成双向考勤，辛苦了！好好放松一下 🌟';
    } else if (hasIn) {
      greeting = '专注工作中';
      motivation = workDuration != null ? '已在岗工作 $workDuration，下班记得签退 💼' : '上班打卡成功，保持专注高效 💼';
    } else {
      greeting = '新的一天开始';
      motivation = '晨光正好，开启元气满满的健康一天 ☀️';
    }

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
        body: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 6.0),
          child: Column(
            children: [
              // 1. Hero Atmosphere Greeting & Date Card
              _buildAtmosphereHeaderCard(dateStr, weekdayStr, greeting, motivation),

              const SizedBox(height: 18),

              // 2. Dynamic Punch Core Sections
              if (isBothDone) ...[
                // Case A: Both Completed Celebration Card
                _buildCompletedCelebrationCard(workDuration),
              ] else if (hasIn) ...[
                // Case B: In Progress (Check-in done, waiting for check-out)
                _buildCompletedSummaryPill(
                  title: '上班签到已完成',
                  time: _todayRecord!.checkInTime!,
                  icon: Icons.wb_sunny_rounded,
                  color: AppTheme.emeraldGreen,
                ),
                const SizedBox(height: 14),
                // Work Progress Rail
                if (workDuration != null) _buildWorkProgressRail(workDuration),
                const SizedBox(height: 14),
                // Evening Check-out Focused Hero Card
                _buildHeroPunchCard(
                  title: '下班签退',
                  scheduleTip: '工作日循环提醒中，签退后自动取消后续',
                  recordedTime: _todayRecord?.checkOutTime,
                  accentColors: const [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                  icon: Icons.nightlight_round,
                  onTap: _handleCheckOut,
                ),
              ] else ...[
                // Case C: Morning (Check-in pending)
                _buildHeroPunchCard(
                  title: '上班签到',
                  scheduleTip: '到达时间点准时提醒，签到后自动取消后续',
                  recordedTime: _todayRecord?.checkInTime,
                  accentColors: const [Color(0xFF3B82F6), Color(0xFF06B6D4)],
                  icon: Icons.wb_sunny_rounded,
                  onTap: _handleCheckIn,
                ),
                const SizedBox(height: 16),
                // Evening Check-out Standby Card
                _buildStandbyPunchCard(
                  title: '下班签退',
                  tip: '将在上班签到后自动开启提醒流',
                  icon: Icons.nightlight_round,
                ),
              ],

              const SizedBox(height: 24),

              // 3. Ambient ticking time pill
              const _LiveTimePill(),

              const SizedBox(height: 100),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAtmosphereHeaderCard(String dateStr, String weekdayStr, String greeting, String motivation) {
    return GlassCard(
      padding: const EdgeInsets.all(20),
      borderRadius: 26,
      backgroundColor: Colors.white.withValues(alpha: 0.90),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    dateStr,
                    style: const TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.5,
                      color: Color(0xFF0F172A),
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    weekdayStr,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.slateGrey),
                  ),
                ],
              ),
              CapsuleBadge(
                text: _dayCategory.label,
                icon: _dayCategory.isWorkday ? Icons.work_rounded : Icons.beach_access_rounded,
                color: _dayCategory.isWorkday ? AppTheme.primaryBlue : AppTheme.emeraldGreen,
                fontSize: 12,
              ),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFF1F5F9),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: AppTheme.primaryBlue,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    motivation,
                    style: const TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w500,
                      color: Color(0xFF334155),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCompletedCelebrationCard(String? workDuration) {
    return GlassCard(
      padding: const EdgeInsets.all(24),
      borderRadius: 28,
      backgroundColor: const Color(0xFFF0FDF4),
      border: Border.all(color: const Color(0xFF86EFAC), width: 1.5),
      child: Column(
        children: [
          Container(
            width: 58,
            height: 58,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF34D399), Color(0xFF059669)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF10B981).withValues(alpha: 0.35),
                  blurRadius: 16,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Icon(Icons.star_rounded, color: Colors.white, size: 36),
          ),
          const SizedBox(height: 14),
          const Text(
            '今日考勤全勤达成！',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: Color(0xFF065F46),
            ),
          ),
          const SizedBox(height: 4),
          if (workDuration != null)
            Text(
              '今日在岗工作时长：$workDuration',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Color(0xFF047857),
              ),
            ),
          const SizedBox(height: 18),
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFDCFCE7)),
                  ),
                  child: Column(
                    children: [
                      const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.wb_sunny_rounded, size: 14, color: AppTheme.emeraldGreen),
                          SizedBox(width: 4),
                          Text('上班签到', style: TextStyle(fontSize: 11, color: AppTheme.slateGrey)),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _todayRecord?.checkInTime ?? '--:--',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF065F46)),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFDCFCE7)),
                  ),
                  child: Column(
                    children: [
                      const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.nightlight_round, size: 14, color: AppTheme.emeraldGreen),
                          SizedBox(width: 4),
                          Text('下班签退', style: TextStyle(fontSize: 11, color: AppTheme.slateGrey)),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _todayRecord?.checkOutTime ?? '--:--',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF065F46)),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCompletedSummaryPill({
    required String title,
    required String time,
    required IconData icon,
    required Color color,
  }) {
    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      borderRadius: 20,
      backgroundColor: Colors.white.withValues(alpha: 0.92),
      border: Border.all(color: color.withValues(alpha: 0.3), width: 1.2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: color, size: 18),
              ),
              const SizedBox(width: 10),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF0F172A),
                ),
              ),
            ],
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(Icons.check_circle_rounded, color: color, size: 14),
                const SizedBox(width: 4),
                Text(
                  time,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWorkProgressRail(String workDuration) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFEEF2FF),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFC7D2FE), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: const BoxDecoration(
              color: Color(0xFF4F46E5),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '累计在岗工时：$workDuration',
            style: const TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w600,
              color: Color(0xFF4338CA),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeroPunchCard({
    required String title,
    required String scheduleTip,
    required String? recordedTime,
    required List<Color> accentColors,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return GlassCard(
      padding: const EdgeInsets.all(24),
      borderRadius: 28,
      backgroundColor: Colors.white.withValues(alpha: 0.94),
      border: Border.all(color: Colors.white.withValues(alpha: 0.95), width: 1.5),
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
                      color: accentColors.first.withValues(alpha: 0.12),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(icon, size: 20, color: accentColors.first),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    title,
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                  ),
                ],
              ),
              CapsuleBadge(
                text: '待打卡',
                color: accentColors.first,
                backgroundColor: accentColors.first.withValues(alpha: 0.1),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Glowing Concentric Touch Halo Button
          GestureDetector(
            onTap: () {
              HapticFeedback.heavyImpact();
              onTap();
            },
            child: Container(
              width: 148,
              height: 148,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: accentColors,
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                boxShadow: [
                  BoxShadow(
                    color: accentColors.first.withValues(alpha: 0.38),
                    blurRadius: 24,
                    offset: const Offset(0, 6),
                  ),
                ],
                border: Border.all(
                  color: Colors.white.withValues(alpha: 0.5),
                  width: 3.5,
                ),
              ),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      icon,
                      color: Colors.white,
                      size: 34,
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '立即$title',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15.5,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.5,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '点击完成记录',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.85),
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 18),
          Text(
            scheduleTip,
            style: const TextStyle(fontSize: 12, color: AppTheme.slateGrey),
          ),
        ],
      ),
    );
  }

  Widget _buildStandbyPunchCard({
    required String title,
    required String tip,
    required IconData icon,
  }) {
    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      borderRadius: 22,
      backgroundColor: Colors.white.withValues(alpha: 0.75),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: const Color(0xFFF1F5F9),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: AppTheme.slateGrey, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF475569)),
                ),
                const SizedBox(height: 2),
                Text(
                  tip,
                  style: const TextStyle(fontSize: 11.5, color: AppTheme.slateGrey),
                ),
              ],
            ),
          ),
          const CapsuleBadge(
            text: '待激活',
            color: AppTheme.slateGrey,
            backgroundColor: Color(0xFFF1F5F9),
            fontSize: 11,
          ),
        ],
      ),
    );
  }
}

class _LiveTimePill extends StatefulWidget {
  const _LiveTimePill();

  @override
  State<_LiveTimePill> createState() => _LiveTimePillState();
}

class _LiveTimePillState extends State<_LiveTimePill> {
  late Timer _timer;
  DateTime _time = DateTime.now();

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) {
        setState(() => _time = DateTime.now());
      }
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final timeStr = DateFormat('HH:mm:ss').format(_time);
    return Container(
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
            '当前本地时间  $timeStr',
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: Color(0xFF0F172A),
            ),
          ),
        ],
      ),
    );
  }
}

