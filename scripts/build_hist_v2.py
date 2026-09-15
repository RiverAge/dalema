import os

calendar_redesign_code = """import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../constants/app_theme.dart';
import '../models/attendance_record.dart';
import '../services/attendance_service.dart';
import '../services/calendar_service.dart';
import '../widgets/glass_components.dart';

enum DayAttendanceStatus {
  allCompleted,
  missingCheckOut,
  missingCheckIn,
  missingBoth,
  restDay,
  futurePending,
}

class CalendarDayData {
  final DateTime date;
  final String dateStr;
  final bool isCurrentMonth;
  final bool isToday;
  final bool isWorkday;
  final DayCategory dayCategory;
  final AttendanceRecord? record;
  final DayAttendanceStatus status;

  const CalendarDayData({
    required this.date,
    required this.dateStr,
    required this.isCurrentMonth,
    required this.isToday,
    required this.isWorkday,
    required this.dayCategory,
    required this.record,
    required this.status,
  });
}

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final AttendanceService _attendanceService = AttendanceService();
  final CalendarService _calendarService = CalendarService();

  DateTime _currentMonth = DateTime(DateTime.now().year, DateTime.now().month, 1);
  CalendarDayData? _selectedDay;
  bool _isLoading = true;

  List<CalendarDayData> _monthGridDays = [];
  int _completedDays = 0;
  int _missingDays = 0;
  int _restDays = 0;

  @override
  void initState() {
    super.initState();
    _loadMonthData();
  }

  Future<void> _loadMonthData() async {
    setState(() => _isLoading = true);

    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final monthStr = DateFormat('yyyy-MM').format(_currentMonth);

    final records = await _attendanceService.getRecordsByMonth(monthStr);
    final recordMap = {for (var r in records) r.date: r};

    final firstDayOfMonth = DateTime(_currentMonth.year, _currentMonth.month, 1);
    final daysInMonth = DateUtils.getDaysInMonth(_currentMonth.year, _currentMonth.month);
    final lastDayOfMonth = DateTime(_currentMonth.year, _currentMonth.month, daysInMonth);

    final int leadingDays = (firstDayOfMonth.weekday - 1);
    final startDate = firstDayOfMonth.subtract(Duration(days: leadingDays));
    final int trailingDays = (7 - lastDayOfMonth.weekday) % 7;
    final endDate = lastDayOfMonth.add(Duration(days: trailingDays));

    final List<CalendarDayData> days = [];
    int completedCount = 0;
    int missingCount = 0;
    int restCount = 0;

    DateTime cursor = startDate;
    while (!cursor.isAfter(endDate)) {
      final dateStr = DateFormat('yyyy-MM-dd').format(cursor);
      final isCurrentMonth = cursor.month == _currentMonth.month && cursor.year == _currentMonth.year;
      final isToday = cursor.year == today.year && cursor.month == today.month && cursor.day == today.day;
      final isFuture = cursor.isAfter(today);

      final isWorkday = await _calendarService.isWorkday(cursor);
      final category = await _calendarService.getDayCategory(cursor, dateStr: dateStr);
      final record = recordMap[dateStr];

      final hasIn = record?.hasCheckIn ?? false;
      final hasOut = record?.hasCheckOut ?? false;

      DayAttendanceStatus status;
      if (hasIn && hasOut) {
        status = DayAttendanceStatus.allCompleted;
      } else if (hasIn && !hasOut) {
        status = DayAttendanceStatus.missingCheckOut;
      } else if (!hasIn && hasOut) {
        status = DayAttendanceStatus.missingCheckIn;
      } else {
        if (!isWorkday) {
          status = DayAttendanceStatus.restDay;
        } else if (isFuture) {
          status = DayAttendanceStatus.futurePending;
        } else {
          status = DayAttendanceStatus.missingBoth;
        }
      }

      if (isCurrentMonth) {
        if (status == DayAttendanceStatus.allCompleted) {
          completedCount++;
        } else if (status == DayAttendanceStatus.missingCheckIn ||
            status == DayAttendanceStatus.missingCheckOut ||
            status == DayAttendanceStatus.missingBoth) {
          missingCount++;
        } else if (status == DayAttendanceStatus.restDay) {
          restCount++;
        }
      }

      final dayData = CalendarDayData(
        date: cursor,
        dateStr: dateStr,
        isCurrentMonth: isCurrentMonth,
        isToday: isToday,
        isWorkday: isWorkday,
        dayCategory: category,
        record: record,
        status: status,
      );

      days.add(dayData);

      if (isToday || (_selectedDay == null && isCurrentMonth && cursor.day == 1)) {
        _selectedDay = dayData;
      }

      cursor = cursor.add(const Duration(days: 1));
    }

    if (mounted) {
      setState(() {
        _monthGridDays = days;
        _completedDays = completedCount;
        _missingDays = missingCount;
        _restDays = restCount;
        _isLoading = false;
      });
    }
  }

  void _previousMonth() {
    setState(() {
      _currentMonth = DateTime(_currentMonth.year, _currentMonth.month - 1, 1);
      _selectedDay = null;
    });
    _loadMonthData();
  }

  void _nextMonth() {
    setState(() {
      _currentMonth = DateTime(_currentMonth.year, _currentMonth.month + 1, 1);
      _selectedDay = null;
    });
    _loadMonthData();
  }

  Future<void> _deleteCurrentMonthData() async {
    final monthStr = DateFormat('yyyy年MM月').format(_currentMonth);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: AppTheme.roseRed),
            SizedBox(width: 8),
            Text('清空确认', style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        content: Text('确定要清空【$monthStr】的全部打卡记录吗？\\n此操作仅影响手机本地数据。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.roseRed),
            child: const Text('确认删除', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final key = DateFormat('yyyy-MM').format(_currentMonth);
      final count = await _attendanceService.deleteRecordsByMonth(key);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('已清除本月 $count 条本地记录'),
            backgroundColor: AppTheme.emeraldGreen,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
      _loadMonthData();
    }
  }

  @override
  Widget build(BuildContext context) {
    final monthHeaderStr = DateFormat('yyyy年 MM月').format(_currentMonth);

    return Container(
      decoration: const BoxDecoration(
        gradient: AppTheme.ambientBg,
      ),
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text('考勤日历', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 19)),
          centerTitle: true,
          backgroundColor: Colors.transparent,
          surfaceTintColor: Colors.transparent,
          elevation: 0,
          actions: [
            IconButton(
              icon: const Icon(Icons.delete_outline_rounded, color: AppTheme.slateGrey),
              tooltip: '清空本月打卡记录',
              onPressed: _deleteCurrentMonthData,
            ),
          ],
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 8.0),
                child: Column(
                  children: [
                    // Monthly KPI Metrics Capsule Bar
                    _buildMetricsCapsuleBar(),

                    const SizedBox(height: 16),

                    // Calendar Grid Glass Card
                    _buildCalendarGlassCard(monthHeaderStr),

                    const SizedBox(height: 16),

                    // Selected Date Detail Drill-down Glass Card
                    _buildSelectedDateGlassCard(),

                    const SizedBox(height: 90), // Bottom padding for floating island
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildMetricsCapsuleBar() {
    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      borderRadius: 24,
      backgroundColor: Colors.white.withValues(alpha: 0.85),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildMetricPill('全勤达标', '$_completedDays天', AppTheme.emeraldGreen, Icons.check_circle_rounded),
          Container(width: 1, height: 28, color: Colors.grey.withValues(alpha: 0.2)),
          _buildMetricPill('打卡异常', '$_missingDays天', AppTheme.amberOrange, Icons.warning_rounded),
          Container(width: 1, height: 28, color: Colors.grey.withValues(alpha: 0.2)),
          _buildMetricPill('休息/节假', '$_restDays天', AppTheme.primaryBlue, Icons.weekend_rounded),
        ],
      ),
    );
  }

  Widget _buildMetricPill(String title, String value, Color color, IconData icon) {
    return Column(
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 13, color: color),
            const SizedBox(width: 4),
            Text(title, style: const TextStyle(fontSize: 11, color: AppTheme.slateGrey)),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildCalendarGlassCard(String monthHeaderStr) {
    return GlassCard(
      padding: const EdgeInsets.all(18),
      borderRadius: 28,
      backgroundColor: Colors.white.withValues(alpha: 0.88),
      child: Column(
        children: [
          // Month Selector Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              IconButton(
                icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
                onPressed: _previousMonth,
              ),
              Text(
                monthHeaderStr,
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF0F172A),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.arrow_forward_ios_rounded, size: 18),
                onPressed: _nextMonth,
              ),
            ],
          ),

          const SizedBox(height: 10),

          // Weekday Labels
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: const [
              Text('一', style: TextStyle(color: AppTheme.slateGrey, fontWeight: FontWeight.bold, fontSize: 13)),
              Text('二', style: TextStyle(color: AppTheme.slateGrey, fontWeight: FontWeight.bold, fontSize: 13)),
              Text('三', style: TextStyle(color: AppTheme.slateGrey, fontWeight: FontWeight.bold, fontSize: 13)),
              Text('四', style: TextStyle(color: AppTheme.slateGrey, fontWeight: FontWeight.bold, fontSize: 13)),
              Text('五', style: TextStyle(color: AppTheme.slateGrey, fontWeight: FontWeight.bold, fontSize: 13)),
              Text('六', style: TextStyle(color: AppTheme.roseRed, fontWeight: FontWeight.bold, fontSize: 13)),
              Text('日', style: TextStyle(color: AppTheme.roseRed, fontWeight: FontWeight.bold, fontSize: 13)),
            ],
          ),

          const SizedBox(height: 10),
          const Divider(height: 1, thickness: 0.8),
          const SizedBox(height: 10),

          // Calendar Days Grid
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _monthGridDays.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7,
              childAspectRatio: 0.82,
              crossAxisSpacing: 6,
              mainAxisSpacing: 6,
            ),
            itemBuilder: (context, index) {
              final dayItem = _monthGridDays[index];
              return _buildDayCell(dayItem);
            },
          ),

          const SizedBox(height: 14),

          // Legend Bar
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildLegendDot(AppTheme.emeraldGreen, '全勤'),
              const SizedBox(width: 14),
              _buildLegendDot(AppTheme.amberOrange, '缺卡'),
              const SizedBox(width: 14),
              _buildLegendDot(AppTheme.roseRed, '缺勤'),
              const SizedBox(width: 14),
              _buildLegendDot(AppTheme.slateGrey.withValues(alpha: 0.5), '休假'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLegendDot(Color color, String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 7,
          height: 7,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(text, style: const TextStyle(fontSize: 11, color: AppTheme.slateGrey)),
      ],
    );
  }

  Widget _buildDayCell(CalendarDayData day) {
    final isSelected = _selectedDay?.dateStr == day.dateStr;

    Color badgeColor = Colors.transparent;
    String? badgeText;

    if (day.dayCategory == DayCategory.statutoryHoliday) {
      badgeText = '休';
      badgeColor = AppTheme.emeraldGreen;
    } else if (day.dayCategory == DayCategory.adjustedWorkday) {
      badgeText = '班';
      badgeColor = AppTheme.roseRed;
    }

    Color statusDotColor;
    switch (day.status) {
      case DayAttendanceStatus.allCompleted:
        statusDotColor = AppTheme.emeraldGreen;
        break;
      case DayAttendanceStatus.missingCheckIn:
      case DayAttendanceStatus.missingCheckOut:
        statusDotColor = AppTheme.amberOrange;
        break;
      case DayAttendanceStatus.missingBoth:
        statusDotColor = AppTheme.roseRed;
        break;
      case DayAttendanceStatus.restDay:
      case DayAttendanceStatus.futurePending:
        statusDotColor = Colors.transparent;
        break;
    }

    return InkWell(
      onTap: () {
        setState(() => _selectedDay = day);
      },
      borderRadius: BorderRadius.circular(14),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        decoration: BoxDecoration(
          color: isSelected
              ? AppTheme.primaryBlue
              : (day.isToday ? AppTheme.primaryBlue.withValues(alpha: 0.1) : Colors.transparent),
          borderRadius: BorderRadius.circular(14),
          boxShadow: isSelected ? AppTheme.glowShadow(AppTheme.primaryBlue, blur: 10) : null,
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            if (badgeText != null && day.isCurrentMonth)
              Positioned(
                top: 3,
                right: 3,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 0.5),
                  decoration: BoxDecoration(
                    color: isSelected ? Colors.white.withValues(alpha: 0.3) : badgeColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    badgeText,
                    style: TextStyle(
                      fontSize: 8,
                      fontWeight: FontWeight.bold,
                      color: isSelected ? Colors.white : badgeColor,
                    ),
                  ),
                ),
              ),
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '${day.date.day}',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: isSelected || day.isToday ? FontWeight.bold : FontWeight.w500,
                    color: isSelected
                        ? Colors.white
                        : (!day.isCurrentMonth
                            ? Colors.black26
                            : (day.isToday ? AppTheme.primaryBlue : const Color(0xFF0F172A))),
                  ),
                ),
                const SizedBox(height: 3),
                Container(
                  width: 5,
                  height: 5,
                  decoration: BoxDecoration(
                    color: isSelected
                        ? (statusDotColor == Colors.transparent ? Colors.transparent : Colors.white)
                        : (day.isCurrentMonth ? statusDotColor : Colors.transparent),
                    shape: BoxShape.circle,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSelectedDateGlassCard() {
    final day = _selectedDay;
    if (day == null) return const SizedBox.shrink();

    final hasIn = day.record?.hasCheckIn ?? false;
    final hasOut = day.record?.hasCheckOut ?? false;

    String statusTitle;
    Color statusColor;
    IconData statusIcon;

    switch (day.status) {
      case DayAttendanceStatus.allCompleted:
        statusTitle = '全勤达标';
        statusColor = AppTheme.emeraldGreen;
        statusIcon = Icons.check_circle_rounded;
        break;
      case DayAttendanceStatus.missingCheckIn:
        statusTitle = '缺少签到';
        statusColor = AppTheme.amberOrange;
        statusIcon = Icons.warning_rounded;
        break;
      case DayAttendanceStatus.missingCheckOut:
        statusTitle = '缺少签退';
        statusColor = AppTheme.amberOrange;
        statusIcon = Icons.warning_rounded;
        break;
      case DayAttendanceStatus.missingBoth:
        statusTitle = '未打卡 / 缺勤';
        statusColor = AppTheme.roseRed;
        statusIcon = Icons.cancel_rounded;
        break;
      case DayAttendanceStatus.restDay:
        statusTitle = '休息日';
        statusColor = AppTheme.slateGrey;
        statusIcon = Icons.beach_access_rounded;
        break;
      case DayAttendanceStatus.futurePending:
        statusTitle = '未来日期';
        statusColor = AppTheme.slateGrey;
        statusIcon = Icons.schedule_rounded;
        break;
    }

    return GlassCard(
      padding: const EdgeInsets.all(20),
      borderRadius: 26,
      backgroundColor: Colors.white.withValues(alpha: 0.88),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                day.dateStr,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
              ),
              const SizedBox(width: 10),
              CapsuleBadge(
                text: day.dayCategory.label,
                color: day.isWorkday ? AppTheme.primaryBlue : AppTheme.emeraldGreen,
                fontSize: 11,
              ),
              const Spacer(),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(statusIcon, size: 16, color: statusColor),
                  const SizedBox(width: 4),
                  Text(
                    statusTitle,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
                    ),
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: _buildTimeCapsule(
                  title: '上班签到',
                  time: hasIn ? day.record!.checkInTime! : '未打卡',
                  icon: Icons.wb_sunny_rounded,
                  color: AppTheme.primaryBlue,
                  isDone: hasIn,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildTimeCapsule(
                  title: '下班签退',
                  time: hasOut ? day.record!.checkOutTime! : '未打卡',
                  icon: Icons.nightlight_round,
                  color: const Color(0xFF6366F1),
                  isDone: hasOut,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTimeCapsule({
    required String title,
    required String time,
    required IconData icon,
    required Color color,
    required bool isDone,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDone ? color.withValues(alpha: 0.08) : const Color(0xFFF1F5F9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDone ? color.withValues(alpha: 0.25) : Colors.transparent,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: isDone ? color : AppTheme.slateGrey),
              const SizedBox(width: 6),
              Text(
                title,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: isDone ? color : AppTheme.slateGrey,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            time,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: isDone ? const Color(0xFF0F172A) : Colors.black38,
            ),
          ),
        ],
      ),
    );
  }
}
"""

with open('lib/screens/history_screen.dart', 'w', encoding='utf-8') as f:
    f.write(calendar_redesign_code.strip() + '\n')
print('history_screen redesigned with glassmorphism and modern calendar.')
