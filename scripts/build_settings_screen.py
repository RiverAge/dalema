import os

settings_screen_code = """import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/app_settings.dart';
import '../services/attendance_service.dart';
import '../services/calendar_service.dart';
import '../services/notification_service.dart';
import '../services/settings_service.dart';
import 'calendar_management_dialog.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final SettingsService _settingsService = SettingsService();
  final CalendarService _calendarService = CalendarService();
  final NotificationService _notificationService = NotificationService.instance;
  final AttendanceService _attendanceService = AttendanceService();

  AppSettings _settings = const AppSettings();
  bool _isLoading = true;
  bool _isNotificationPermissionGranted = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    setState(() => _isLoading = true);
    final settings = await _settingsService.getSettings();
    final permStatus = await _notificationService.checkPermissionStatus();

    if (mounted) {
      setState(() {
        _settings = settings;
        _isNotificationPermissionGranted = permStatus;
        _isLoading = false;
      });
    }
  }

  Future<void> _updateSettings(AppSettings newSettings) async {
    setState(() {
      _settings = newSettings;
    });
    await _settingsService.saveSettings(newSettings);
    // Automatically recalculate and reschedule local notifications
    await _notificationService.rescheduleAllNotifications();
  }

  Future<void> _requestNotificationPermission() async {
    final granted = await _notificationService.requestPermissions();
    setState(() {
      _isNotificationPermissionGranted = granted;
    });
    if (granted) {
      await _notificationService.rescheduleAllNotifications();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('通知与精确闹钟权限已获取成功'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('通知权限被拒绝，请在系统设置中允许通知以接收打卡提醒！'),
            backgroundColor: Colors.orange,
          ),
        );
      }
    }
  }

  Future<void> _editCheckInTimes() async {
    final TextEditingController controller = TextEditingController(
      text: _settings.checkInTimes.join(', '),
    );

    final result = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('配置上班签到提醒时间'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '请输入提醒时间（24小时制 HH:mm），多个时间用英文逗号隔开：',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: '例如: 08:10, 08:16, 08:22, 08:28',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(null),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(controller.text),
            child: const Text('保存'),
          ),
        ],
      ),
    );

    if (result != null) {
      final parsed = result
          .split(',')
          .map((s) => s.trim())
          .where((s) => RegExp(r'^\d{2}:\d{2}$').hasMatch(s))
          .toList();

      if (parsed.isNotEmpty) {
        parsed.sort();
        final updated = _settings.copyWith(checkInTimes: parsed);
        await _updateSettings(updated);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('上班签到时间已更新并重置通知计划'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('输入格式不正确，需形如 08:10'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  Future<void> _editCheckOutConfig() async {
    final startCtrl = TextEditingController(text: _settings.checkOutStartTime);
    final endCtrl = TextEditingController(text: _settings.checkOutEndTime);
    final intervalCtrl = TextEditingController(
        text: _settings.checkOutIntervalMinutes.toString());

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('配置下班签退提醒时间'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: startCtrl,
                decoration: const InputDecoration(
                  labelText: '开始提醒时间 (HH:mm)',
                  hintText: '18:05',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: endCtrl,
                decoration: const InputDecoration(
                  labelText: '结束提醒时间 (HH:mm)',
                  hintText: '19:30',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: intervalCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: '提醒间隔分钟数',
                  hintText: '15',
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('保存'),
          ),
        ],
      ),
    );

    if (saved == true) {
      final start = startCtrl.text.trim();
      final end = endCtrl.text.trim();
      final interval = int.tryParse(intervalCtrl.text.trim()) ?? 15;

      if (RegExp(r'^\d{2}:\d{2}$').hasMatch(start) &&
          RegExp(r'^\d{2}:\d{2}$').hasMatch(end) &&
          interval > 0) {
        final updated = _settings.copyWith(
          checkOutStartTime: start,
          checkOutEndTime: end,
          checkOutIntervalMinutes: interval,
        );
        await _updateSettings(updated);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('下班签退配置已更新并重置通知计划'),
              backgroundColor: Colors.green,
            ),
          );
        }
      }
    }
  }

  Future<void> _restoreDefaults() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('恢复默认设置'),
        content: const Text('确定要将所有提醒设置和时间恢复为系统初始默认配置吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('确定恢复'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _settingsService.restoreDefaults();
      await _loadSettings();
      await _notificationService.rescheduleAllNotifications();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('已恢复默认提醒配置'),
            backgroundColor: Colors.green,
          ),
        );
      }
    }
  }

  Future<void> _openCalendarManagement() async {
    await showDialog(
      context: context,
      builder: (ctx) => const CalendarManagementDialog(),
    );
    // After calendar change, refresh notifications
    await _notificationService.rescheduleAllNotifications();
  }

  Future<void> _openDeleteDataDialog() async {
    DateTimeRange? range = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
      helpText: '选择要删除的打卡时间范围',
    );

    if (range != null) {
      final startStr = DateFormat('yyyy-MM-dd').format(range.start);
      final endStr = DateFormat('yyyy-MM-dd').format(range.end);

      final confirmed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.warning, color: Colors.red),
              SizedBox(width: 8),
              Text('二次确认删除'),
            ],
          ),
          content: Text(
            '确定要删除 $startStr 至 $endStr 范围内的本地打卡数据吗？\n该操作仅影响本地存储且不可撤销！',
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
              child: const Text('删除', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      );

      if (confirmed == true) {
        final count = await _attendanceService.deleteRecordsByRange(startStr, endStr);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('成功删除 $count 条打卡记录'),
              backgroundColor: Colors.green,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final calculatedCheckOut = _settings.getCalculatedCheckOutTimes();
    final holidayInfo = _calendarService.getCurrentYearHolidayInfo(DateTime.now().year);

    return Scaffold(
      appBar: AppBar(
        title: const Text('设置'),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 8),
        children: [
          // 10. App 当前通知权限状态
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: _isNotificationPermissionGranted
                  ? Colors.green.shade50
                  : Colors.amber.shade50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: _isNotificationPermissionGranted
                    ? Colors.green.shade300
                    : Colors.amber.shade400,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  _isNotificationPermissionGranted
                      ? Icons.notifications_active
                      : Icons.notifications_off,
                  color: _isNotificationPermissionGranted
                      ? Colors.green.shade800
                      : Colors.amber.shade900,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _isNotificationPermissionGranted
                            ? '通知权限：已正常开启'
                            : '通知权限：未开启或被系统受限',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: _isNotificationPermissionGranted
                              ? Colors.green.shade900
                              : Colors.amber.shade900,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _isNotificationPermissionGranted
                            ? '提醒可在设定时间准时发送，建议保持后台电池无限制。'
                            : '请点击右侧按钮重新申请权限，或前往系统应用管理中手动开启通知与闹钟。',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade700,
                        ),
                      ),
                    ],
                  ),
                ),
                if (!_isNotificationPermissionGranted)
                  ElevatedButton(
                    onPressed: _requestNotificationPermission,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.amber.shade800,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('授权'),
                  ),
              ],
            ),
          ),

          // Section: 基础提醒开关
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text(
              '提醒开关配置',
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue),
            ),
          ),
          SwitchListTile(
            secondary: const Icon(Icons.notifications),
            title: const Text('应用全局通知'),
            subtitle: const Text('总开关：关闭后将停用所有本地通知'),
            value: _settings.notificationEnabled,
            onChanged: (val) {
              _updateSettings(_settings.copyWith(notificationEnabled: val));
            },
          ),
          SwitchListTile(
            secondary: const Icon(Icons.wb_sunny_outlined),
            title: const Text('上班签到提醒'),
            subtitle: const Text('仅在工作日生效，完成签到后自动取消当天提醒'),
            value: _settings.checkInEnabled,
            onChanged: (val) {
              _updateSettings(_settings.copyWith(checkInEnabled: val));
            },
          ),
          SwitchListTile(
            secondary: const Icon(Icons.nightlight_round_outlined),
            title: const Text('下班签退提醒'),
            subtitle: const Text('仅在工作日生效，完成签退后自动取消当天提醒'),
            value: _settings.checkOutEnabled,
            onChanged: (val) {
              _updateSettings(_settings.copyWith(checkOutEnabled: val));
            },
          ),
          SwitchListTile(
            secondary: const Icon(Icons.volume_up),
            title: const Text('提醒声音'),
            subtitle: const Text('通知触发时播放系统提示音'),
            value: _settings.soundEnabled,
            onChanged: (val) {
              _updateSettings(_settings.copyWith(soundEnabled: val));
            },
          ),
          SwitchListTile(
            secondary: const Icon(Icons.vibration),
            title: const Text('提醒震动'),
            subtitle: const Text('通知触发时设备震动提醒'),
            value: _settings.vibrationEnabled,
            onChanged: (val) {
              _updateSettings(_settings.copyWith(vibrationEnabled: val));
            },
          ),

          const Divider(),

          // Section: 提醒时间配置
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Text(
              '时间与计划配置',
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.alarm),
            title: const Text('签到提醒时间点'),
            subtitle: Text('当前：${_settings.checkInTimes.join(', ')}'),
            trailing: const Icon(Icons.chevron_right),
            onPressed: _editCheckInTimes,
          ),
          ListTile(
            leading: const Icon(Icons.timer_outlined),
            title: const Text('签退提醒时间范围及间隔'),
            subtitle: Text(
              '开始: ${_settings.checkOutStartTime}  结束: ${_settings.checkOutEndTime}  间隔: ${_settings.checkOutIntervalMinutes}分钟\\n生成批次: ${calculatedCheckOut.join(', ')}',
            ),
            isThreeLine: true,
            trailing: const Icon(Icons.chevron_right),
            onPressed: _editCheckOutConfig,
          ),

          const Divider(),

          // Section: 工作日历与节假日
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Text(
              '工作日历与节假日',
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Text(
              holidayInfo,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade700, height: 1.4),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.edit_calendar),
            title: const Text('工作日历管理'),
            subtitle: const Text('手动标记某天为工作日、休息日或使用默认规则'),
            trailing: const Icon(Icons.chevron_right),
            onTap: _openCalendarManagement,
          ),

          const Divider(),

          // Section: 数据管理与重置
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Text(
              '数据管理与重置',
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.delete_sweep, color: Colors.red),
            title: const Text('数据删除入口'),
            subtitle: const Text('选择时间范围删除本地历史打卡数据（需二次确认）'),
            trailing: const Icon(Icons.chevron_right),
            onTap: _openDeleteDataDialog,
          ),
          ListTile(
            leading: const Icon(Icons.restore, color: Colors.orange),
            title: const Text('恢复默认提醒配置'),
            subtitle: const Text('重置开关、签到与签退时间为出厂默认设置'),
            onTap: _restoreDefaults,
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}
"""

with open('lib/screens/settings_screen.dart', 'w', encoding='utf-8') as f:
    f.write(settings_screen_code.strip() + '\n')
print('SettingsScreen generated.')
