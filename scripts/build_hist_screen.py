import os

history_screen_code = """import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/attendance_record.dart';
import '../services/attendance_service.dart';
import '../services/calendar_service.dart';

enum RecordStatus {
  completed,
  missingCheckIn,
  missingCheckOut,
  missingBoth,
  restDay,
}

extension RecordStatusExtension on RecordStatus {
  String get label {
    switch (this) {
      case RecordStatus.completed:
        return '已完成';
      case RecordStatus.missingCheckIn:
        return '缺少签到';
      case RecordStatus.missingCheckOut:
        return '缺少签退';
      case RecordStatus.missingBoth:
        return '两项都缺少';
      case RecordStatus.restDay:
        return '休息日';
    }
  }

  Color get color {
    switch (this) {
      case RecordStatus.completed:
        return Colors.green;
      case RecordStatus.missingCheckIn:
      case RecordStatus.missingCheckOut:
        return Colors.orange;
      case RecordStatus.missingBoth:
        return Colors.red;
      case RecordStatus.restDay:
        return Colors.blueGrey;
    }
  }
}

class HistoryDayItem {
  final DateTime date;
  final String dateStr;
  final int weekday;
  final bool isWorkday;
  final String dayCategoryLabel;
  final AttendanceRecord? record;
  final RecordStatus status;

  HistoryDayItem({
    required this.date,
    required this.dateStr,
    required this.weekday,
    required this.isWorkday,
    required this.dayCategoryLabel,
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

  // Query mode: 'month' or 'range'
  bool _isRangeMode = false;

  DateTime _selectedMonth = DateTime(DateTime.now().year, DateTime.now().month, 1);
  DateTime _startDate = DateTime.now().subtract(const Duration(days: 7));
  DateTime _endDate = DateTime.now();

  bool _isLoading = true;
  List<HistoryDayItem> _historyItems = [];

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final List<DateTime> dateRange = [];
      if (!_isRangeMode) {
        // Full month days
        final daysInMonth = DateUtils.getDaysInMonth(_selectedMonth.year, _selectedMonth.month);
        for (int i = 1; i <= daysInMonth; i++) {
          dateRange.add(DateTime(_selectedMonth.year, _selectedMonth.month, i));
        }
      } else {
        // Custom range
        DateTime curr = DateTime(_startDate.year, _startDate.month, _startDate.day);
        final end = DateTime(_endDate.year, _endDate.month, _endDate.day);
        while (!curr.isAfter(end)) {
          dateRange.add(curr);
          curr = curr.add(const Duration(days: 1));
        }
      }

      // Fetch database records
      List<AttendanceRecord> records;
      if (!_isRangeMode) {
        final monthStr = DateFormat('yyyy-MM').format(_selectedMonth);
        records = await _attendanceService.getRecordsByMonth(monthStr);
      } else {
        final startStr = DateFormat('yyyy-MM-dd').format(_startDate);
        final endStr = DateFormat('yyyy-MM-dd').format(_endDate);
        records = await _attendanceService.getRecordsByRange(startStr, endStr);
      }

      final Map<String, AttendanceRecord> recordMap = {
        for (var r in records) r.date: r,
      };

      final List<HistoryDayItem> items = [];
      final now = DateTime.now();
      final todayDate = DateTime(now.year, now.month, now.day);

      for (final date in dateRange) {
        final dateStr = DateFormat('yyyy-MM-dd').format(date);
        final isWorkday = await _calendarService.isWorkday(date);
        final cat = await _calendarService.getDayCategory(date, dateStr: dateStr);
        final record = recordMap[dateStr];

        final hasIn = record?.hasCheckIn ?? false;
        final hasOut = record?.hasCheckOut ?? false;

        RecordStatus status;
        if (hasIn && hasOut) {
          status = RecordStatus.completed;
        } else if (hasIn && !hasOut) {
          status = RecordStatus.missingCheckOut;
        } else if (!hasIn && hasOut) {
          status = RecordStatus.missingCheckIn;
        } else {
          // Both missing
          if (!isWorkday) {
            status = RecordStatus.restDay;
          } else {
            // If the day is in the future, show as rest/pending or missing
            if (date.isAfter(todayDate)) {
              status = RecordStatus.restDay;
            } else {
              status = RecordStatus.missingBoth;
            }
          }
        }

        items.add(
          HistoryDayItem(
            date: date,
            dateStr: dateStr,
            weekday: date.weekday,
            isWorkday: isWorkday,
            dayCategoryLabel: cat.label,
            record: record,
            status: status,
          ),
        );
      }

      // Show newest first
      items.sort((a, b) => b.date.compareTo(a.date));

      if (mounted) {
        setState(() {
          _historyItems = items;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('加载打卡记录失败: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _pickMonth() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedMonth,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
      initialDatePickerMode: DatePickerMode.year,
      helpText: '选择查询月份',
    );
    if (picked != null) {
      setState(() {
        _selectedMonth = DateTime(picked.year, picked.month, 1);
        _isRangeMode = false;
      });
      _loadHistory();
    }
  }

  Future<void> _pickDateRange() async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
      initialDateRange: DateTimeRange(start: _startDate, end: _endDate),
      helpText: '选择开始和结束日期',
    );
    if (picked != null) {
      setState(() {
        _startDate = picked.start;
        _endDate = picked.end;
        _isRangeMode = true;
      });
      _loadHistory();
    }
  }

  Future<void> _confirmDeleteCurrentFilter() async {
    String description;
    if (!_isRangeMode) {
      final monthStr = DateFormat('yyyy年MM月').format(_selectedMonth);
      description = '$monthStr 的所有本地打卡数据';
    } else {
      final startStr = DateFormat('yyyy-MM-dd').format(_startDate);
      final endStr = DateFormat('yyyy-MM-dd').format(_endDate);
      description = '$startStr 至 $endStr 范围内的本地打卡数据';
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.red),
            SizedBox(width: 8),
            Text('二次确认删除'),
          ],
        ),
        content: Text(
          '您确定要删除【$description】吗？\n\n注意：此操作只删除手机本地数据，不可撤销！',
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
      int count = 0;
      if (!_isRangeMode) {
        final monthStr = DateFormat('yyyy-MM').format(_selectedMonth);
        count = await _attendanceService.deleteRecordsByMonth(monthStr);
      } else {
        final startStr = DateFormat('yyyy-MM-dd').format(_startDate);
        final endStr = DateFormat('yyyy-MM-dd').format(_endDate);
        count = await _attendanceService.deleteRecordsByRange(startStr, endStr);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('已删除 $count 条本地打卡记录'),
            backgroundColor: Colors.green,
          ),
        );
      }
      _loadHistory();
    }
  }

  String _getWeekdayString(int weekday) {
    const names = ['一', '二', '三', '四', '五', '六', '日'];
    return '周${names[weekday - 1]}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('历史记录'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline),
            tooltip: '删除当前筛选数据',
            onPressed: _confirmDeleteCurrentFilter,
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.4),
            child: Column(
              children: [
                Row(
                  children: [
                    ChoiceChip(
                      label: const Text('按月份筛选'),
                      selected: !_isRangeMode,
                      onSelected: (val) {
                        if (val) {
                          setState(() => _isRangeMode = false);
                          _loadHistory();
                        }
                      },
                    ),
                    const SizedBox(width: 8),
                    ChoiceChip(
                      label: const Text('按日期范围筛选'),
                      selected: _isRangeMode,
                      onSelected: (val) {
                        if (val) {
                          setState(() => _isRangeMode = true);
                          _loadHistory();
                        }
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        !_isRangeMode
                            ? '当前查看：${DateFormat('yyyy年MM月').format(_selectedMonth)}'
                            : '当前范围：${DateFormat('yyyy-MM-dd').format(_startDate)} 至 ${DateFormat('yyyy-MM-dd').format(_endDate)}',
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                    ),
                    OutlinedButton.icon(
                      icon: const Icon(Icons.calendar_month, size: 18),
                      label: Text(!_isRangeMode ? '切换月份' : '选择范围'),
                      onPressed: !_isRangeMode ? _pickMonth : _pickDateRange,
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Records List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _historyItems.isEmpty
                    ? const Center(child: Text('没有符合条件的打卡记录'))
                    : ListView.separated(
                        padding: const EdgeInsets.all(12),
                        itemCount: _historyItems.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 8),
                        itemBuilder: (context, index) {
                          final item = _historyItems[index];
                          final inTime = item.record?.checkInTime ?? '--:--:--';
                          final outTime = item.record?.checkOutTime ?? '--:--:--';

                          return Card(
                            elevation: 1,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                              side: BorderSide(
                                color: Colors.grey.shade200,
                              ),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(14.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Text(
                                        item.dateStr,
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      Text(
                                        _getWeekdayString(item.weekday),
                                        style: TextStyle(
                                          color: Colors.grey.shade700,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: item.isWorkday ? Colors.orange.shade50 : Colors.green.shade50,
                                          borderRadius: BorderRadius.circular(4),
                                          border: Border.override(
                                            border: Border.all(
                                              color: item.isWorkday ? Colors.orange.shade200 : Colors.green.shade200,
                                            ),
                                          ),
                                        ),
                                        child: Text(
                                          item.isWorkday ? '工作日' : '休息日',
                                          style: TextStyle(
                                            fontSize: 11,
                                            color: item.isWorkday ? Colors.orange.shade900 : Colors.green.shade900,
                                          ),
                                        ),
                                      ),
                                      const Spacer(),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: item.status.color.withOpacity(0.12),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          item.status.label,
                                          style: TextStyle(
                                            color: item.status.color,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 12,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const Divider(height: 16),
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Row(
                                          children: [
                                            Icon(Icons.wb_sunny_outlined, size: 16, color: Colors.blue.shade700),
                                            const SizedBox(width: 4),
                                            Text(
                                              '签到: $inTime',
                                              style: TextStyle(
                                                fontSize: 13,
                                                color: item.record?.hasCheckIn ?? false
                                                    ? Colors.black87
                                                    : Colors.grey,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      Expanded(
                                        child: Row(
                                          children: [
                                            Icon(Icons.nightlight_round_outlined, size: 16, color: Colors.indigo.shade700),
                                            const SizedBox(width: 4),
                                            Text(
                                              '签退: $outTime',
                                              style: TextStyle(
                                                fontSize: 13,
                                                color: item.record?.hasCheckOut ?? false
                                                    ? Colors.black87
                                                    : Colors.grey,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
"""

with open('lib/screens/history_screen.dart', 'w', encoding='utf-8') as f:
    f.write(history_screen_code.strip() + '\n')
print('HistoryScreen generated.')
