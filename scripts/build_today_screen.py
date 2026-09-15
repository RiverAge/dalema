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
      // Recheck data and notifications when returning to foreground
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

      // Verify and correct notifications plan
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
          _errorMessage = '加载数据失败: $e';
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
            content: Text('上班签到成功：${updated.checkInTime}'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('签到失败：${e.toString()}'),
            backgroundColor: Colors.red,
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
            content: Text('下班签退成功：${updated.checkOutTime}'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('签退失败：${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  String _getWeekdayString(int weekday) {
    const names = ['一', '二', '三', '四', '五', '六', '日'];
    return '星期${names[weekday - 1]}';
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final dateStr = DateFormat('yyyy年MM月dd日').format(now);
    final weekdayStr = _getWeekdayString(now.weekday);

    return Scaffold(
      appBar: AppBar(
        title: const Text('今日打卡'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
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
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (_errorMessage != null)
                      Container(
                        margin: const EdgeInsets.only(bottom: 16),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.red.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          _errorMessage!,
                          style: TextStyle(color: Colors.red.shade900),
                        ),
                      ),

                    // Date & Status Header Card
                    Card(
                      elevation: 2,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(20.0),
                        child: Column(
                          children: [
                            Text(
                              dateStr,
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                            ),
                            const SizedBox(height: 8),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Chip(
                                  label: Text(weekdayStr),
                                  backgroundColor: Colors.blue.shade50,
                                ),
                                const SizedBox(width: 8),
                                Chip(
                                  label: Text(_dayCategory.label),
                                  backgroundColor: _dayCategory.isWorkday
                                      ? Colors.orange.shade100
                                      : Colors.green.shade100,
                                ),
                              ],
                            ),
                            if (!_dayCategory.isWorkday)
                              Padding(
                                padding: const EdgeInsets.only(top: 8.0),
                                child: Text(
                                  '温馨提示：今日为休息日，默认不发送提醒；但您仍可根据需要手动记录打卡。',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey.shade700,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Task 1: Check In
                    _buildTaskCard(
                      title: '上班签到',
                      icon: Icons.wb_sunny_outlined,
                      accentColor: Colors.blue,
                      hasCompleted: _todayRecord?.hasCheckIn ?? false,
                      recordedTime: _todayRecord?.checkInTime,
                      buttonText: '上班签到',
                      onPressed: (_todayRecord?.hasCheckIn ?? false)
                          ? null
                          : _handleCheckIn,
                      tipText: (_todayRecord?.hasCheckIn ?? false)
                          ? '今日签到已完成，对应提醒已自动取消'
                          : '工作日提醒：08:10、08:16、08:22、08:28',
                    ),

                    const SizedBox(height: 16),

                    // Task 2: Check Out
                    _buildTaskCard(
                      title: '下班签退',
                      icon: Icons.nightlight_round_outlined,
                      accentColor: Colors.indigo,
                      hasCompleted: _todayRecord?.hasCheckOut ?? false,
                      recordedTime: _todayRecord?.checkOutTime,
                      buttonText: '下班签退',
                      onPressed: (_todayRecord?.hasCheckOut ?? false)
                          ? null
                          : _handleCheckOut,
                      tipText: (_todayRecord?.hasCheckOut ?? false)
                          ? '今日签退已完成，对应提醒已自动取消'
                          : '工作日提醒：18:05至19:30循环提醒',
                    ),

                    const SizedBox(height: 24),
                    Text(
                      '注意：App 只证明您在 App 中完成了记录，不负责验证公司打卡系统是否成功。每天仅支持记录一次，时间不可修改。',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                        height: 1.5,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildTaskCard({
    required String title,
    required IconData icon,
    required MaterialColor accentColor,
    required bool hasCompleted,
    required String? recordedTime,
    required String buttonText,
    required VoidCallback? onPressed,
    required String tipText,
  }) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: hasCompleted ? Colors.green.shade300 : Colors.transparent,
          width: 1.5,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: accentColor.shade50,
                  child: Icon(icon, color: accentColor.shade700),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                if (hasCompleted)
                  const Chip(
                    avatar: Icon(Icons.check, color: Colors.white, size: 16),
                    label: Text('已完成', style: TextStyle(color: Colors.white)),
                    backgroundColor: Colors.green,
                  )
                else
                  Chip(
                    label: const Text('未完成'),
                    backgroundColor: Colors.grey.shade200,
                  ),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: hasCompleted ? Colors.green.shade50 : Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(
                    hasCompleted ? Icons.access_time_filled : Icons.access_time,
                    size: 20,
                    color: hasCompleted ? Colors.green.shade800 : Colors.grey.shade600,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    hasCompleted
                        ? '打卡时间：$recordedTime'
                        : '记录状态：未打卡',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: hasCompleted ? Colors.green.shade900 : Colors.grey.shade800,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Text(
              tipText,
              style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton.icon(
                onPressed: onPressed,
                icon: Icon(hasCompleted ? Icons.done_all : Icons.touch_app),
                label: Text(
                  hasCompleted ? '已完成打卡' : buttonText,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: hasCompleted ? Colors.grey.shade300 : accentColor,
                  foregroundColor: hasCompleted ? Colors.grey.shade600 : Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
"""

with open('lib/screens/today_screen.dart', 'w', encoding='utf-8') as f:
    f.write(today_screen_code.strip() + '\n')
print('TodayScreen generated.')
