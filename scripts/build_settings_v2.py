import os

settings_redesign_code = """import '../services/holiday_sync_service.dart';
import '../constants/holiday_data.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../constants/app_theme.dart';
import '../models/app_settings.dart';
import '../services/attendance_service.dart';
import '../services/calendar_service.dart';
import '../services/notification_service.dart';
import '../services/settings_service.dart';
import '../widgets/glass_components.dart';
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
  final HolidaySyncService _holidaySyncService = HolidaySyncService();

  AppSettings _settings = const AppSettings();
  bool _isLoading = true;
  bool _isNotificationPermissionGranted = true;
  bool _isSyncingHolidays = false;
  String? _lastSyncTimeInfo;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    setState(() => _isLoading = true);
    final settings = await _settingsService.getSettings();
    final permStatus = await _notificationService.checkPermissionStatus();
    final lastSync = await _holidaySyncService.getLastSyncTime(DateTime.now().year);

    if (mounted) {
      setState(() {
        _settings = settings;
        _isNotificationPermissionGranted = permStatus;
        if (lastSync != null) {
          try {
            final dt = DateTime.parse(lastSync);
            _lastSyncTimeInfo = DateFormat('yyyy-MM-dd HH:mm').format(dt);
          } catch (_) {}
        }
        _isLoading = false;
      });
    }
  }

  Future<void> _updateSettings(AppSettings newSettings) async {
    setState(() {
      _settings = newSettings;
    });
    await _settingsService.saveSettings(newSettings);
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
          SnackBar(
            content: const Text('通知与精确闹钟权限已获取成功'),
            backgroundColor: AppTheme.emeraldGreen,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('通知权限被拒绝，请在系统应用设置中开启通知以接收提醒！'),
            backgroundColor: AppTheme.amberOrange,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  Future<void> _syncOnlineHolidays() async {
    setState(() => _isSyncingHolidays = true);
    final currentYear = DateTime.now().year;
    try {
      final config = await _holidaySyncService.syncHolidaysForYear(currentYear);
      if (config != null) {
        HolidayData.updateConfigForYear(config);
        await _notificationService.rescheduleAllNotifications();

        final timeStr = DateFormat('yyyy-MM-dd HH:mm').format(DateTime.now());
        if (mounted) {
          setState(() {
            _lastSyncTimeInfo = timeStr;
            _isSyncingHolidays = false;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('已联网同步 $currentYear 年法定节假日及调休安排！'),
              backgroundColor: AppTheme.emeraldGreen,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      } else {
        if (mounted) {
          setState(() => _isSyncingHolidays = false);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text('无网络连接，当前使用手机本地节假日数据。'),
              backgroundColor: AppTheme.amberOrange,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSyncingHolidays = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('同步失败: $e，已使用本地数据保底'),
            backgroundColor: AppTheme.roseRed,
            behavior: SnackBarBehavior.floating,
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
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        title: const Text('配置上班签到提醒时间', style: TextStyle(fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '请输入提醒时间（HH:mm），多个时间用逗号隔开：',
              style: TextStyle(fontSize: 13, color: AppTheme.slateGrey),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: InputDecoration(
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
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
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryBlue),
            child: const Text('保存', style: TextStyle(color: Colors.white)),
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
      }
    }
  }

  Future<void> _editCheckOutConfig() async {
    final startCtrl = TextEditingController(text: _settings.checkOutStartTime);
    final endCtrl = TextEditingController(text: _settings.checkOutEndTime);
    final intervalCtrl = TextEditingController(text: _settings.checkOutIntervalMinutes.toString());

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        title: const Text('配置下班签退提醒时间', style: TextStyle(fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: startCtrl,
                decoration: InputDecoration(
                  labelText: '开始时间 (HH:mm)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: endCtrl,
                decoration: InputDecoration(
                  labelText: '结束时间 (HH:mm)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: intervalCtrl,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: '提醒间隔分钟数',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
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
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryBlue),
            child: const Text('保存', style: TextStyle(color: Colors.white)),
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
      }
    }
  }

  Future<void> _restoreDefaults() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        title: const Text('恢复默认设置', style: TextStyle(fontWeight: FontWeight.bold)),
        content: const Text('确定将所有打卡提醒配置与时间重置为系统出厂默认值吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.amberOrange),
            child: const Text('确定恢复', style: TextStyle(color: Colors.white)),
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
          SnackBar(
            content: const Text('已恢复系统默认提醒设置'),
            backgroundColor: AppTheme.emeraldGreen,
            behavior: SnackBarBehavior.floating,
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
    await _notificationService.rescheduleAllNotifications();
  }

  Future<void> _openDeleteDataDialog() async {
    DateTimeRange? range = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
      helpText: '选择删除打卡记录的时间范围',
    );

    if (range != null && mounted) {
      final startStr = DateFormat('yyyy-MM-dd').format(range.start);
      final endStr = DateFormat('yyyy-MM-dd').format(range.end);

      final confirmed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
          title: const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: AppTheme.roseRed),
              SizedBox(width: 8),
              Text('二次确认删除', style: TextStyle(fontWeight: FontWeight.bold)),
            ],
          ),
          content: Text(
            '确定要删除 $startStr 至 $endStr 范围内的本地打卡数据吗？\\n\\n该操作仅影响本地存储且不可撤销！',
            style: const TextStyle(height: 1.5),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: const Text('取消'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.roseRed),
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
              content: Text('已清除 $count 条本地打卡记录'),
              backgroundColor: AppTheme.emeraldGreen,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final calculatedCheckOut = _settings.getCalculatedCheckOutTimes();
    final holidayInfo = _calendarService.getCurrentYearHolidayInfo(DateTime.now().year);

    return Container(
      decoration: const BoxDecoration(
        gradient: AppTheme.ambientBg,
      ),
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text('设置与偏好', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 19)),
          centerTitle: true,
          backgroundColor: Colors.transparent,
          surfaceTintColor: Colors.transparent,
          elevation: 0,
        ),
        body: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 8.0),
          children: [
            // Notification Permission Banner Card
            _buildPermissionBannerCard(),

            const SizedBox(height: 18),

            // Group 1: Reminders & Alerts Inset Card
            _buildSectionHeader('提醒通知开关'),
            GlassCard(
              padding: const EdgeInsets.symmetric(vertical: 6),
              borderRadius: 22,
              child: Column(
                children: [
                  _buildSwitchTile(
                    icon: Icons.notifications_active_rounded,
                    color: AppTheme.primaryBlue,
                    title: '应用全局通知',
                    subtitle: '总开关：控制所有打卡提醒推送',
                    value: _settings.notificationEnabled,
                    onChanged: (val) => _updateSettings(_settings.copyWith(notificationEnabled: val)),
                  ),
                  const Divider(height: 1, indent: 60),
                  _buildSwitchTile(
                    icon: Icons.wb_sunny_rounded,
                    color: const Color(0xFF3B82F6),
                    title: '上班签到提醒',
                    subtitle: '工作日 08:10 起循环，签到后自动取消',
                    value: _settings.checkInEnabled,
                    onChanged: (val) => _updateSettings(_settings.copyWith(checkInEnabled: val)),
                  ),
                  const Divider(height: 1, indent: 60),
                  _buildSwitchTile(
                    icon: Icons.nightlight_round,
                    color: const Color(0xFF6366F1),
                    title: '下班签退提醒',
                    subtitle: '工作日 18:05 起循环，签退后自动取消',
                    value: _settings.checkOutEnabled,
                    onChanged: (val) => _updateSettings(_settings.copyWith(checkOutEnabled: val)),
                  ),
                  const Divider(height: 1, indent: 60),
                  _buildSwitchTile(
                    icon: Icons.volume_up_rounded,
                    color: AppTheme.emeraldGreen,
                    title: '提示声音',
                    subtitle: '提醒时播放系统提示音',
                    value: _settings.soundEnabled,
                    onChanged: (val) => _updateSettings(_settings.copyWith(soundEnabled: val)),
                  ),
                  const Divider(height: 1, indent: 60),
                  _buildSwitchTile(
                    icon: Icons.vibration_rounded,
                    color: AppTheme.amberOrange,
                    title: '提示振动',
                    subtitle: '提醒时设备轻微振动',
                    value: _settings.vibrationEnabled,
                    onChanged: (val) => _updateSettings(_settings.copyWith(vibrationEnabled: val)),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Group 2: Time Schedule Inset Card
            _buildSectionHeader('时间与批次规划'),
            GlassCard(
              padding: const EdgeInsets.symmetric(vertical: 4),
              borderRadius: 22,
              child: Column(
                children: [
                  _buildNavTile(
                    icon: Icons.alarm_rounded,
                    color: AppTheme.primaryBlue,
                    title: '上班签到时间点',
                    subtitle: _settings.checkInTimes.join(', '),
                    onTap: _editCheckInTimes,
                  ),
                  const Divider(height: 1, indent: 60),
                  _buildNavTile(
                    icon: Icons.timer_outlined,
                    color: const Color(0xFF6366F1),
                    title: '下班签退时间范围与间隔',
                    subtitle: '${_settings.checkOutStartTime} - ${_settings.checkOutEndTime}（每隔${_settings.checkOutIntervalMinutes}分钟）',
                    onTap: _editCheckOutConfig,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Group 3: Holidays & Calendar Management
            _buildSectionHeader('官方节假日与日历'),
            GlassCard(
              padding: const EdgeInsets.symmetric(vertical: 4),
              borderRadius: 22,
              child: Column(
                children: [
                  _buildNavTile(
                    icon: Icons.cloud_sync_rounded,
                    color: AppTheme.accentCyan,
                    title: '联网同步法定节假日',
                    subtitle: _lastSyncTimeInfo != null
                        ? '上次同步：$_lastSyncTimeInfo（国务院官方通告）'
                        : '一键拉取国务院最新官方休假与调休补班数据',
                    trailing: _isSyncingHolidays
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : ElevatedButton(
                            onPressed: _syncOnlineHolidays,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.primaryBlue,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                            child: const Text('同步', style: TextStyle(fontSize: 12)),
                          ),
                    onTap: _isSyncingHolidays ? null : _syncOnlineHolidays,
                  ),
                  const Divider(height: 1, indent: 60),
                  _buildNavTile(
                    icon: Icons.edit_calendar_rounded,
                    color: AppTheme.emeraldGreen,
                    title: '工作日历特殊管理',
                    subtitle: '手动将某一天设定为工作日或休息日',
                    onTap: _openCalendarManagement,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Group 4: Local Storage & Reset
            _buildSectionHeader('数据管理与重置'),
            GlassCard(
              padding: const EdgeInsets.symmetric(vertical: 4),
              borderRadius: 22,
              child: Column(
                children: [
                  _buildNavTile(
                    icon: Icons.delete_sweep_rounded,
                    color: AppTheme.roseRed,
                    title: '删除本地打卡数据',
                    subtitle: '选择时间范围彻底清除本地考勤数据',
                    onTap: _openDeleteDataDialog,
                  ),
                  const Divider(height: 1, indent: 60),
                  _buildNavTile(
                    icon: Icons.restart_alt_rounded,
                    color: AppTheme.amberOrange,
                    title: '恢复默认提醒设置',
                    subtitle: '恢复至初始提醒时间与开关状态',
                    onTap: _restoreDefaults,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 100), // Bottom padding for floating navigation island
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 6, bottom: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.bold,
          color: AppTheme.slateGrey,
        ),
      ),
    );
  }

  Widget _buildPermissionBannerCard() {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      borderRadius: 22,
      backgroundColor: _isNotificationPermissionGranted
          ? AppTheme.emeraldGreen.withValues(alpha: 0.1)
          : AppTheme.amberOrange.withValues(alpha: 0.12),
      border: Border.all(
        color: _isNotificationPermissionGranted
            ? AppTheme.emeraldGreen.withValues(alpha: 0.3)
            : AppTheme.amberOrange.withValues(alpha: 0.4),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: _isNotificationPermissionGranted ? AppTheme.emeraldGreen : AppTheme.amberOrange,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(
              _isNotificationPermissionGranted ? Icons.notifications_active : Icons.notifications_off,
              color: Colors.white,
              size: 20,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _isNotificationPermissionGranted ? '通知与闹钟权限正常' : '通知权限受限或未开启',
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                ),
                const SizedBox(height: 2),
                Text(
                  _isNotificationPermissionGranted ? '已在系统层登记，杀后台亦能准时提醒' : '建议开启权限以确保到点准时弹出提醒',
                  style: const TextStyle(fontSize: 12, color: AppTheme.slateGrey),
                ),
              ],
            ),
          ),
          if (!_isNotificationPermissionGranted)
            ElevatedButton(
              onPressed: _requestNotificationPermission,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.amberOrange,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text('授权'),
            ),
        ],
      ),
    );
  }

  Widget _buildSwitchTile({
    required IconData icon,
    required Color color,
    required String title,
    required String subtitle,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(icon, color: color, size: 20),
      ),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15, color: Color(0xFF0F172A))),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12, color: AppTheme.slateGrey)),
      trailing: Switch(
        value: value,
        activeColor: AppTheme.primaryBlue,
        onChanged: onChanged,
      ),
    );
  }

  Widget _buildNavTile({
    required IconData icon,
    required Color color,
    required String title,
    required String subtitle,
    Widget? trailing,
    VoidCallback? onTap,
  }) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(icon, color: color, size: 20),
      ),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15, color: Color(0xFF0F172A))),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12, color: AppTheme.slateGrey)),
      trailing: trailing ?? const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: AppTheme.slateGrey),
      onTap: onTap,
    );
  }
}
"""

with open('lib/screens/settings_screen.dart', 'w', encoding='utf-8') as f:
    f.write(settings_redesign_code.strip() + '\n')
print('settings_screen redesigned with iOS style inset glass cards.')
