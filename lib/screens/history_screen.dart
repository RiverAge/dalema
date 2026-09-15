import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../constants/app_theme.dart';
import '../models/attendance_record.dart';
import '../models/calendar_override.dart';
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

  // Month change animation key
  int _monthAnimKey = 0;

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
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final monthStr = DateFormat('yyyy-MM').format(_currentMonth);

    // Batch load holiday config and overrides in parallel for instant 0ms switching
    await _calendarService.preloadYearConfig(_currentMonth.year);
    final results = await Future.wait([
      _attendanceService.getRecordsByMonth(monthStr),
      _calendarService.getAllOverridesMap(),
    ]);

    final records = results[0] as List<AttendanceRecord>;
    final overrideMap = results[1] as Map<String, CalendarOverride>;
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

      final category = _calendarService.getDayCategorySync(
        cursor,
        dateStr,
        override: overrideMap[dateStr],
      );
      final isWorkday = category.isWorkday;
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
      });
    }
  }

  void _previousMonth() {
    setState(() {
      _currentMonth = DateTime(_currentMonth.year, _currentMonth.month - 1, 1);
      _selectedDay = null;
      _monthAnimKey--;
    });
    _loadMonthData();
  }

  void _nextMonth() {
    setState(() {
      _currentMonth = DateTime(_currentMonth.year, _currentMonth.month + 1, 1);
      _selectedDay = null;
      _monthAnimKey++;
    });
    _loadMonthData();
  }

  Future<void> _deleteCurrentMonthData() async {
    final monthStr = DateFormat('yyyy年MM月').format(_currentMonth);
    final confirmed = await showSmoothDialog<bool>(
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
        content: Text('确定要清空【$monthStr】的全部打卡记录吗？\n此操作仅影响手机本地数据。'),
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
        body: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 8.0),
          child: Column(
            children: [
              // Monthly KPI Metrics Capsule Bar
              _buildMetricsCapsuleBar(),

              const SizedBox(height: 16),

              // Calendar Grid Glass Card with AnimatedSwitcher for silky-smooth month switching
              _buildCalendarGlassCard(monthHeaderStr),

              const SizedBox(height: 16),

              // Selected Date Detail Drill-down Glass Card
              _buildSelectedDateGlassCard(),

              const SizedBox(height: 100),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMetricsCapsuleBar() {
    final totalWorkdays = _completedDays + _missingDays;
    final rate = totalWorkdays > 0 ? (_completedDays / totalWorkdays) : 1.0;
    final ratePercent = (rate * 100).toInt();

    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      borderRadius: 26,
      backgroundColor: Colors.white.withValues(alpha: 0.92),
      child: Row(
        children: [
          // Circular Progress Indicator Dial
          SizedBox(
            width: 52,
            height: 52,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: rate,
                  strokeWidth: 5,
                  backgroundColor: const Color(0xFFE2E8F0),
                  color: rate >= 0.9 ? AppTheme.emeraldGreen : AppTheme.amberOrange,
                  strokeCap: StrokeCap.round,
                ),
                Text(
                  '$ratePercent%',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: rate >= 0.9 ? const Color(0xFF065F46) : const Color(0xFFB45309),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          // Metric Tiles
          Expanded(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildMetricTile('全勤达标', '$_completedDays天', AppTheme.emeraldGreen, Icons.check_circle_rounded),
                Container(width: 1, height: 30, color: const Color(0xFFE2E8F0)),
                _buildMetricTile('打卡异常', '$_missingDays天', AppTheme.amberOrange, Icons.warning_rounded),
                Container(width: 1, height: 30, color: const Color(0xFFE2E8F0)),
                _buildMetricTile('休假天数', '$_restDays天', AppTheme.primaryBlue, Icons.weekend_rounded),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricTile(String title, String value, Color color, IconData icon) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 12, color: color),
            const SizedBox(width: 3),
            Text(title, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: AppTheme.slateGrey)),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w800,
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
      backgroundColor: Colors.white.withValues(alpha: 0.92),
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
              Text('周一', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600, fontSize: 12)),
              Text('周二', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600, fontSize: 12)),
              Text('周三', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600, fontSize: 12)),
              Text('周四', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600, fontSize: 12)),
              Text('周五', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600, fontSize: 12)),
              Text('周六', style: TextStyle(color: Color(0xFFF43F5E), fontWeight: FontWeight.w600, fontSize: 12)),
              Text('周日', style: TextStyle(color: Color(0xFFF43F5E), fontWeight: FontWeight.w600, fontSize: 12)),
            ],
          ),

          const SizedBox(height: 10),
          const Divider(height: 1, thickness: 0.8),
          const SizedBox(height: 10),

          // Calendar Days Grid with smooth AnimatedSwitcher
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 250),
            switchInCurve: Curves.easeOut,
            switchOutCurve: Curves.easeIn,
            transitionBuilder: (child, animation) => FadeTransition(opacity: animation, child: child),
            child: GridView.builder(
              key: ValueKey<int>(_monthAnimKey),
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _monthGridDays.length,
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 7,
                childAspectRatio: 1.0,
                crossAxisSpacing: 4,
                mainAxisSpacing: 6,
              ),
              itemBuilder: (context, index) {
                final dayItem = _monthGridDays[index];
                return _buildDayCell(dayItem);
              },
            ),
          ),

          const SizedBox(height: 14),

          // Legend Bar
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildLegendDot(AppTheme.emeraldGreen, '全勤'),
              const SizedBox(width: 16),
              _buildLegendDot(AppTheme.amberOrange, '缺卡'),
              const SizedBox(width: 16),
              _buildLegendDot(const Color(0xFF059669), '法定休假'),
              const SizedBox(width: 16),
              _buildLegendDot(const Color(0xFFDC2626), '调休补班'),
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
          width: 6,
          height: 6,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 5),
        Text(text, style: const TextStyle(fontSize: 11, color: AppTheme.slateGrey, fontWeight: FontWeight.w500)),
      ],
    );
  }

  Widget _buildDayCell(CalendarDayData day) {
    final isSelected = _selectedDay?.dateStr == day.dateStr;

    // Determine badge for statutory holiday / adjusted workday / manual override
    String? badgeText;
    Color? badgeBg;
    Color? badgeTextColor;

    if (day.dayCategory == DayCategory.statutoryHoliday || day.dayCategory == DayCategory.manualHoliday) {
      badgeText = '休';
      badgeBg = isSelected ? Colors.white.withValues(alpha: 0.25) : const Color(0xFFE8F5E9);
      badgeTextColor = isSelected ? Colors.white : const Color(0xFF059669);
    } else if (day.dayCategory == DayCategory.adjustedWorkday || day.dayCategory == DayCategory.manualWorkday) {
      badgeText = '班';
      badgeBg = isSelected ? Colors.white.withValues(alpha: 0.25) : const Color(0xFFFEE2E2);
      badgeTextColor = isSelected ? Colors.white : const Color(0xFFDC2626);
    }

    // Attendance status dot: only show for days with actual punch data or today
    Color? attendanceDotColor;
    if (day.status == DayAttendanceStatus.allCompleted) {
      attendanceDotColor = isSelected ? Colors.white : const Color(0xFF10B981);
    } else if (day.status == DayAttendanceStatus.missingCheckIn || day.status == DayAttendanceStatus.missingCheckOut) {
      attendanceDotColor = isSelected ? Colors.white : const Color(0xFFF59E0B);
    }

    // Selection styling: Perfect match with user reference media_1789093980526.png
    BoxDecoration decoration;
    if (isSelected) {
      decoration = BoxDecoration(
        color: const Color(0xFF2563EB), // Vibrant blue rounded pill from reference
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF2563EB).withValues(alpha: 0.35),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      );
    } else if (day.isToday) {
      decoration = BoxDecoration(
        color: const Color(0xFFEFF6FF),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF3B82F6).withValues(alpha: 0.5), width: 1.2),
      );
    } else {
      decoration = const BoxDecoration(color: Colors.transparent);
    }

    // Number text color
    Color dateColor;
    if (isSelected) {
      dateColor = Colors.white; // Pure crisp white text when selected
    } else if (!day.isCurrentMonth) {
      dateColor = const Color(0xFFCBD5E1);
    } else if (day.isToday) {
      dateColor = const Color(0xFF2563EB);
    } else if (!day.isWorkday) {
      dateColor = const Color(0xFF94A3B8);
    } else {
      dateColor = const Color(0xFF1E293B);
    }

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          setState(() => _selectedDay = day);
        },
        borderRadius: BorderRadius.circular(12),
        child: Center(
          child: SizedBox(
            width: 42,
            height: 42,
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                // 1. Background selection/today animation container
                Positioned.fill(
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 160),
                    decoration: decoration,
                  ),
                ),

                // 2. Date Number: perfectly centered and aligned horizontally across all columns
                Center(
                  child: Padding(
                    padding: EdgeInsets.only(bottom: attendanceDotColor != null ? 3.0 : 0.0),
                    child: Text(
                      '${day.date.day}',
                      style: TextStyle(
                        fontSize: 15.0,
                        height: 1.0,
                        fontWeight: isSelected || day.isToday ? FontWeight.bold : FontWeight.w500,
                        color: dateColor,
                      ),
                    ),
                  ),
                ),

                // 3. Mini corner badge for "班" or "休"
                if (day.isCurrentMonth && badgeText != null)
                  Positioned(
                    top: 2,
                    right: 2,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 2.5, vertical: 0.5),
                      decoration: BoxDecoration(
                        color: badgeBg,
                        borderRadius: BorderRadius.circular(3),
                      ),
                      child: Text(
                        badgeText,
                        style: TextStyle(
                          fontSize: 8.0,
                          fontWeight: FontWeight.w800,
                          color: badgeTextColor,
                          height: 1.0,
                        ),
                      ),
                    ),
                  ),

                // 4. Subtle, clean 4px attendance indicator dot (replaces heavy red bar)
                if (day.isCurrentMonth && attendanceDotColor != null)
                  Positioned(
                    bottom: 4,
                    left: 0,
                    right: 0,
                    child: Center(
                      child: Container(
                        width: 4,
                        height: 4,
                        decoration: BoxDecoration(
                          color: attendanceDotColor,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSelectedDateGlassCard() {
    final day = _selectedDay;
    if (day == null) return const SizedBox.shrink();

    final hasIn = day.record?.hasCheckIn ?? false;
    final hasOut = day.record?.hasCheckOut ?? false;

    String? workDuration;
    if (hasIn && hasOut) {
      try {
        final inParts = day.record!.checkInTime!.split(':').map(int.parse).toList();
        final outParts = day.record!.checkOutTime!.split(':').map(int.parse).toList();
        final inDt = DateTime(2020, 1, 1, inParts[0], inParts[1]);
        final outDt = DateTime(2020, 1, 1, outParts[0], outParts[1]);
        final diff = outDt.difference(inDt);
        if (!diff.isNegative) {
          final h = diff.inHours;
          final m = diff.inMinutes % 60;
          workDuration = h == 0 ? '$m分钟' : '$h小时$m分钟';
        }
      } catch (_) {}
    }

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
        statusTitle = '休假安歇';
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
      backgroundColor: Colors.white.withValues(alpha: 0.92),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                day.dateStr,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: Color(0xFF0F172A)),
              ),
              const SizedBox(width: 8),
              CapsuleBadge(
                text: day.dayCategory.label,
                color: day.isWorkday ? AppTheme.primaryBlue : AppTheme.emeraldGreen,
                fontSize: 11,
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(statusIcon, size: 14, color: statusColor),
                    const SizedBox(width: 4),
                    Text(
                      statusTitle,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: statusColor,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 18),

          if (!day.isWorkday && day.status == DayAttendanceStatus.restDay) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.coffee_rounded, color: AppTheme.primaryBlue, size: 28),
                  SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '无需出勤的休息日',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
                        ),
                        SizedBox(height: 2),
                        Text(
                          '享受惬意休假，电量充能中 ☕',
                          style: TextStyle(fontSize: 12, color: AppTheme.slateGrey),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ] else ...[
            // Attendance Timeline Flow Rail
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Column(
                children: [
                  Row(
                    children: [
                      Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          color: hasIn ? const Color(0xFFE0F2FE) : const Color(0xFFF1F5F9),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.wb_sunny_rounded,
                          size: 16,
                          color: hasIn ? AppTheme.primaryBlue : AppTheme.slateGrey,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('上班签到', style: TextStyle(fontSize: 12, color: AppTheme.slateGrey)),
                            Text(
                              hasIn ? day.record!.checkInTime! : '未打卡',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: hasIn ? const Color(0xFF0F172A) : const Color(0xFF94A3B8),
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (hasIn)
                        const CapsuleBadge(
                          text: '已记录',
                          icon: Icons.check_rounded,
                          color: AppTheme.emeraldGreen,
                          fontSize: 11,
                        ),
                    ],
                  ),
                  if (workDuration != null) ...[
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Row(
                        children: [
                          const SizedBox(width: 15),
                          Container(
                            width: 2,
                            height: 24,
                            color: const Color(0xFFCBD5E1),
                          ),
                          const SizedBox(width: 20),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                            decoration: BoxDecoration(
                              color: const Color(0xFFEEF2FF),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              '在岗工时 $workDuration',
                              style: const TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w600,
                                color: Color(0xFF4F46E5),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ] else ...[
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 6),
                      child: Divider(height: 1, indent: 44),
                    ),
                  ],
                  Row(
                    children: [
                      Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          color: hasOut ? const Color(0xFFEDE9FE) : const Color(0xFFF1F5F9),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.nightlight_round,
                          size: 16,
                          color: hasOut ? const Color(0xFF6366F1) : AppTheme.slateGrey,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('下班签退', style: TextStyle(fontSize: 12, color: AppTheme.slateGrey)),
                            Text(
                              hasOut ? day.record!.checkOutTime! : '未打卡',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: hasOut ? const Color(0xFF0F172A) : const Color(0xFF94A3B8),
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (hasOut)
                        const CapsuleBadge(
                          text: '已记录',
                          icon: Icons.check_rounded,
                          color: AppTheme.emeraldGreen,
                          fontSize: 11,
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
