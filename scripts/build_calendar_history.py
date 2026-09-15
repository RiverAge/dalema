import os

calendar_screen_code = """import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/attendance_record.dart';
import '../services/attendance_service.dart';
import '../services/calendar_service.dart';

enum DayAttendanceStatus {
  allCompleted,    // 签到签退均完成
  missingCheckOut, // 缺签退
  missingCheckIn,  // 缺签到
  missingBoth,     // 两项都缺少 (工作日旷卡)
  restDay,         // 休息日 (周末或法定假)
  futurePending,   // 未来日期
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

  // Cache of grid days
  List<CalendarDayData> _monthGridDays = [];

  // Monthly summary metrics
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

    // Fetch records of this month
    final records = await _attendanceService.getRecordsByMonth(monthStr);
    final recordMap = {for (var r in records) r.date: r};

    // Calculate start & end of calendar grid (Monday first)
    final firstDayOfMonth = DateTime(_currentMonth.year, _currentMonth.month, 1);
    final daysInMonth = DateUtils.getDaysInMonth(_currentMonth.year, _currentMonth.month);
    final lastDayOfMonth = DateTime(_currentMonth.year, _currentMonth.month, daysInMonth);

    // Days before 1st to align with Monday (1..7)
    final int leadingDays = (firstDayOfMonth.weekday - 1);
    final startDate = firstDayOfMonth.subtract(Duration(days: leadingDays));

    // Days after last day of month to complete 7 columns
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

      // Default select today or first day
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
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.red),
            SizedBox(width: 8),
            Text('二次确认清空'),
          ],
        ),
        content: Text(
          '确定要删除【$monthStr】的全部本地打卡记录吗？\\n此操作不可逆。',
          style: const TextStyle(height: 1.5),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
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
            content: Text('已成功清除本月 $count 条打卡数据'),
            backgroundColor: Colors.green,
          ),
        );
      }
      _loadMonthData();
    }
  }

  @override
  Widget build(BuildContext context) {
    final monthHeaderStr = DateFormat('yyyy年 MM月').format(_currentMonth);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text('考勤日历看板', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep_outlined, color: Colors.grey),
            tooltip: '清空本月打卡数据',
            onPressed: _deleteCurrentMonthData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
              child: Column(
                children: [
                  // 1. Month summary card
                  _buildMonthSummaryHeader(),

                  const SizedBox(height: 12),

                  // 2. Calendar Month Navigation & Grid
                  _buildCalendarCard(monthHeaderStr),

                  const SizedBox(height: 16),

                  // 3. Selected Day Detail Drill-down
                  _buildDayDetailCard(),

                  const SizedBox(height: 16),
                ],
              ),
            ),
    );
  }

  Widget _buildMonthSummaryHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF1E293B), Color(0xFF0F172A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 15,
            offset: const诗Offset(0, 6),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildMetricItem('正常全勤', '$_completedDays 天', const Color(0xFF10B981), Icons.check_circle_outline),
          Container(width: 1, height: 36, color: Colors.white12),
          _buildMetricItem('考勤异常', '$_missingDays 天', const Color(0xFFF59E0B), Icons.warning_amber_rounded),
          Container(width: 1, height: 36, color: Colors.white12),
          _buildMetricItem('休假天数', '$_restDays 天', const Color(0xFF60A5FA), Icons.weekend_outlined),
        ],
      ),
    );
  }

  Widget _buildMetricItem(String label, String value, Color color, IconData icon) {
    return Column(
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: color),
            const SizedBox(width: 4),
            Text(label, style: const TextStyle(fontSize: 12, color: Colors.white70)),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildCalendarCard(String monthHeaderStr) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.blueGrey.withValues(alpha: 0.06),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          // Month Selector
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              IconButton(
                icon: const Icon(Icons.chevron_left_rounded),
                onPressed: _previousMonth,
              ),
              Text(
                monthHeaderStr,
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
              ),
              IconButton(
                icon: const Icon(Icons.chevron_right_rounded),
                onPressed: _nextMonth,
              ),
            ],
          ),

          const SizedBox(height: 8),

          // Weekday Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: const [
              Text('一', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.w600, fontSize: 13)),
              Text('二', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.w600, fontSize: 13)),
              Text('三', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.w600, fontSize: 13)),
              Text('四', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.w600, fontSize: 13)),
              Text('五', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.w600, fontSize: 13)),
              Text('六', style: TextStyle(color: Color(0xFFEF4444), fontWeight: FontWeight.w600, fontSize: 13)),
              Text('日', style: TextStyle(color: Color(0xFFEF4444), fontWeight: FontWeight.w600, fontSize: 13)),
            ],
          ),

          const Divider(height: 16),

          // 7-column Calendar Grid
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _monthGridDays.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7,
              childAspectRatio: 0.82,
              crossAxisSpacing: 4,
              mainAxisSpacing: 4,
            ),
            itemBuilder: (context, index) {
              final dayItem = _monthGridDays[index];
              return _buildCalendarDayCell(dayItem);
            },
          ),

          const SizedBox(height: 12),
          // Legend bar
          Wrap(
            spacing: 12,
            runSpacing: 6,
            alignment: WrapAlignment.center,
            children: [
              _buildLegend(const Color(0xFF10B981), '全勤'),
              _buildLegend(const Color(0xFFF59E0B), '缺卡'),
              _buildLegend(const Color(0xFFEF4444), '缺卡/旷卡'),
              _buildLegend(const Color(0xFF94A3B8), '休息'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLegend(Color color, String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(text, style: const TextStyle(fontSize: 11, color: Colors.grey)),
      ],
    );
  }

  Widget _buildCalendarDayCell(CalendarDayData day) {
    final isSelected = _selectedDay?.dateStr == day.dateStr;

    Color badgeColor;
    String? badgeText;

    if (day.dayCategory == DayCategory.statutoryHoliday) {
      badgeText = '休';
      badgeColor = const Color(0xFF10B981);
    } else if (day.dayCategory == DayCategory.adjustedWorkday) {
      badgeText = '班';
      badgeColor = const Color(0xFFEF4444);
    }

    Color statusDotColor;
    switch (day.status) {
      case DayAttendanceStatus.allCompleted:
        statusDotColor = const Color(0xFF10B981);
        break;
      case DayAttendanceStatus.missingCheckIn:
      case DayAttendanceStatus.missingCheckOut:
        statusDotColor = const Color(0xFFF59E0B);
        break;
      case DayAttendanceStatus.missingBoth:
        statusDotColor = const Color(0xFFEF4444);
        break;
      case DayAttendanceStatus.restDay:
        statusDotColor = Colors.transparent;
        break;
      case DayAttendanceStatus.futurePending:
        statusDotColor = Colors.transparent;
        break;
    }

    return InkWell(
      onTap: () {
        setState(() => _selectedDay = day);
      },
      borderRadius: BorderRadius.circular(10),
      child: Container(
        decoration: BoxDecoration(
          color: isSelected
              ? const Color(0xFF3B82F6).withValues(alpha: 0.12)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isSelected
                ? const Color(0xFF3B82F6)
                : (day.isToday ? const Color(0xFF3B82F6).withValues(alpha: 0.3) : Colors.transparent),
            width: isSelected ? 1.5 : 1.0,
          ),
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            // Holiday or Work badge on top-right
            if (badgeText != null && day.isCurrentMonth)
              Positioned(
                top: 2,
                right: 2,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 2.5, vertical: 0.5),
                  decoration: BoxDecoration(
                    color: badgeColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(3),
                  ),
                  child: Text(
                    badgeText,
                    style: TextStyle(
                      fontSize: 8,
                      fontWeight: FontWeight.bold,
                      color: badgeColor,
                    ),
                  ),
                ),
              ),

            // Date number
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '${day.date.day}',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: day.isToday ? FontWeight.bold : FontWeight.w500,
                    color: !day.isCurrentMonth
                        ? Colors.black26
                        : (day.isToday ? const Color(0xFF3B82F6) : const Color(0xFF1E293B)),
                  ),
                ),
                const SizedBox(height: 3),
                // Status dot
                Container(
                  width: 5,
                  height: 5,
                  decoration: BoxDecoration(
                    color: day.isCurrentMonth ? statusDotColor : Colors.transparent,
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

  Widget _buildDayDetailCard() {
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
        statusColor = const Color(0xFF10B981);
        statusIcon = Icons.verified;
        break;
      case DayAttendanceStatus.missingCheckIn:
        statusTitle = '缺少签到';
        statusColor = const Color(0xFFF59E0B);
        statusIcon = Icons.warning;
        break;
      case DayAttendanceStatus.missingCheckOut:
        statusTitle = '缺少签退';
        statusColor = const Color(0xFFF59E0B);
        statusIcon = Icons.warning;
        break;
      case DayAttendanceStatus.missingBoth:
        statusTitle = '未打卡 / 缺勤';
        statusColor = const Color(0xFFEF4444);
        statusIcon = Icons.cancel;
        break;
      case DayAttendanceStatus.restDay:
        statusTitle = '休息日';
        statusColor = const Color(0xFF64748B);
        statusIcon = Icons.beach_access;
        break;
      case DayAttendanceStatus.futurePending:
        statusTitle = '未来日期 (待打卡)';
        statusColor = const Color(0xFF94A3B8);
        statusIcon = Icons.schedule;
        break;
    }

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.blueGrey.withValues(alpha: 0.06),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                day.dateStr,
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  day.dayCategory.label,
                  style: const TextStyle(fontSize: 11, color: Color(0xFF475569)),
                ),
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

          const Divider(height: 24),

          Row(
            children: [
              Expanded(
                child: _buildPunchTile(
                  title: '上班签到',
                  time: hasIn ? day.record!.checkInTime! : '未打卡',
                  icon: Icons.wb_sunny_rounded,
                  accentColor: const Color(0xFF3B82F6),
                  isDone: hasIn,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildPunchTile(
                  title: '下班签退',
                  time: hasOut ? day.record!.checkOutTime! : '未打卡',
                  icon: Icons.nightlight_round,
                  accentColor: const Color(0xFF6366F1),
                  isDone: hasOut,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPunchTile({
    required String title,
    required String time,
    required IconData icon,
    required Color accentColor,
    required bool isDone,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDone ? accentColor.withValues(alpha: 0.08) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isDone ? accentColor.withValues(alpha: 0.2) : Colors.transparent,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: isDone ? accentColor : Colors.grey),
              const SizedBox(width: 6),
              Text(
                title,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: isDone ? accentColor : Colors.grey,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            time,
            style: TextStyle(
              fontSize: 15,
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

# Fix any typo in poem
calendar_screen_code = calendar_screen_code.replace("const诗Offset", "const Offset")

with open('lib/screens/history_screen.dart', 'w', encoding='utf-8') as f:
    f.write(calendar_screen_code.strip() + '\n')

print('HistoryScreen replaced with interactive Attendance Calendar View.')
