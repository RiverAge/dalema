import '../constants/holiday_data.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import '../constants/app_theme.dart';
import '../models/app_settings.dart';
import '../models/app_update_info.dart';
import '../services/attendance_service.dart';
import '../services/holiday_sync_service.dart';
import '../services/notification_service.dart';
import '../services/settings_service.dart';
import '../update/update_flow_controller.dart';
import '../widgets/glass_components.dart';
import '../widgets/glass_time_picker.dart';
import '../widgets/update_dialog.dart';
import 'calendar_management_dialog.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final SettingsService _settingsService = SettingsService();
  final NotificationService _notificationService = NotificationService.instance;
  final AttendanceService _attendanceService = AttendanceService();
  final HolidaySyncService _holidaySyncService = HolidaySyncService();
  final UpdateFlowController _updateController = UpdateFlowController.instance;

  AppSettings _settings = const AppSettings();
  bool _isLoading = true;
  bool _isNotificationPermissionGranted = true;
  bool _isSyncingHolidays = false;
  String? _lastSyncTimeInfo;

  @override
  void initState() {
    super.initState();
    _updateController.addListener(_onUpdateControllerChanged);
    _updateController.initCurrentVersion();
    _loadSettings();
  }

  @override
  void dispose() {
    _updateController.removeListener(_onUpdateControllerChanged);
    super.dispose();
  }

  void _onUpdateControllerChanged() {
    if (mounted) setState(() {});
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
    final updatedTimes = await showSmoothDialog<List<String>>(
      context: context,
      builder: (ctx) => CheckInTimesEditDialog(initialTimes: _settings.checkInTimes),
    );

    if (updatedTimes != null && updatedTimes.isNotEmpty) {
      final updated = _settings.copyWith(checkInTimes: updatedTimes);
      await _updateSettings(updated);
    }
  }

  Future<void> _editCheckOutConfig() async {
    final res = await showSmoothDialog<Map<String, dynamic>>(
      context: context,
      builder: (ctx) => CheckOutConfigEditDialog(
        initialStartTime: _settings.checkOutStartTime,
        initialEndTime: _settings.checkOutEndTime,
        initialInterval: _settings.checkOutIntervalMinutes,
      ),
    );

    if (res != null) {
      final updated = _settings.copyWith(
        checkOutStartTime: res['start'] as String,
        checkOutEndTime: res['end'] as String,
        checkOutIntervalMinutes: res['interval'] as int,
      );
      await _updateSettings(updated);
    }
  }

  Future<void> _restoreDefaults() async {
    final confirmed = await showSmoothDialog<bool>(
      context: context,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        insetPadding: const EdgeInsets.symmetric(horizontal: 24),
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppTheme.amberOrange.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.restart_alt_rounded, color: AppTheme.amberOrange, size: 24),
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    '恢复出厂设置',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              const Text(
                '确定将所有打卡提醒配置、提醒时间点与批次重置为默认值吗？\n（历史考勤记录不会被清除）',
                style: TextStyle(fontSize: 13, color: AppTheme.slateGrey, height: 1.4),
              ),
              const SizedBox(height: 22),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.of(ctx).pop(false),
                    child: const Text('取消', style: TextStyle(color: AppTheme.slateGrey)),
                  ),
                  const SizedBox(width: 8),
                  CapsuleActionButton(
                    text: '确认恢复',
                    primaryColor: AppTheme.amberOrange,
                    secondaryColor: const Color(0xFFD97706),
                    onPressed: () => Navigator.of(ctx).pop(true),
                  ),
                ],
              ),
            ],
          ),
        ),
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
    await showSmoothDialog(
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

      final confirmed = await showSmoothDialog<bool>(
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
            '确定要删除 $startStr 至 $endStr 范围内的本地打卡数据吗？\n\n该操作仅影响本地存储且不可撤销！',
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
                  const Divider(height: 1, indent: 60),
                  _buildNavTile(
                    icon: Icons.notifications_active_rounded,
                    color: AppTheme.primaryBlue,
                    title: '立即测试提醒与震动',
                    subtitle: '一键发送即时强提醒，验证耳机声音与手机震动',
                    trailing: CapsuleActionButton(
                      text: '立即测试',
                      icon: Icons.play_arrow_rounded,
                      primaryColor: AppTheme.primaryBlue,
                      fontSize: 12,
                      onPressed: () async {
                        await _notificationService.sendInstantTestNotification();
                        if (!context.mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: const Text('已触发强提醒测试，请查看手机横幅与震动！'),
                            backgroundColor: AppTheme.primaryBlue,
                            behavior: SnackBarBehavior.floating,
                          ),
                        );
                      },
                    ),
                    onTap: () async {
                      await _notificationService.sendInstantTestNotification();
                      if (!context.mounted) return;
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: const Text('已触发强提醒测试，请查看手机横幅与震动！'),
                          backgroundColor: AppTheme.primaryBlue,
                          behavior: SnackBarBehavior.floating,
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),

            // Tip note for long pressing notification to access categories
            Padding(
              padding: const EdgeInsets.only(top: 8, left: 6, right: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.tips_and_updates_outlined, size: 14, color: AppTheme.primaryBlue),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      '澎湃OS/小米排查秘籍：收到通知时，长按通知横幅 -> 点击设置齿轮即可直达【通知类别】，一键打开此提醒的「振动」与「声音」！',
                      style: TextStyle(
                        fontSize: 11.5,
                        color: AppTheme.slateGrey.withValues(alpha: 0.9),
                        height: 1.4,
                      ),
                    ),
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
                    trailing: CapsuleActionButton(
                      text: '立即同步',
                      icon: Icons.sync_rounded,
                      isLoading: _isSyncingHolidays,
                      primaryColor: AppTheme.accentCyan,
                      secondaryColor: AppTheme.primaryBlue,
                      onPressed: _syncOnlineHolidays,
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

            const SizedBox(height: 20),

            // Group 5: App Version & Updates
            _buildSectionHeader('软件版本与更新'),
            GlassCard(
              padding: const EdgeInsets.symmetric(vertical: 4),
              borderRadius: 22,
              child: Column(
                children: [
                  _buildUpdateTile(),
                ],
              ),
            ),

            const SizedBox(height: 100), // Bottom padding for floating navigation island
          ],
        ),
      ),
    );
  }

  Future<void> _checkAppUpdate({bool manual = true}) async {
    try {
      final result = await _updateController.checkForUpdate(silent: !manual);
      if (mounted && manual) {
        if (result.hasUpdate && result.remote != null) {
          UpdateDialog.show(
            context: context,
            update: result.remote!,
            currentVersion: result.currentVersionName,
            controller: _updateController,
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('当前已是最新版本 (v${result.currentVersionName})'),
              backgroundColor: AppTheme.emeraldGreen,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted && manual) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('检查更新失败: $e'),
            backgroundColor: AppTheme.roseRed,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  String _formatUpdateBytes(int bytes) {
    if (bytes <= 0) return '0B';
    const double kb = 1024;
    const double mb = kb * 1024;
    if (bytes >= mb) return '${(bytes / mb).toStringAsFixed(1)}M';
    if (bytes >= kb) return '${(bytes / kb).toStringAsFixed(0)}K';
    return '${bytes}B';
  }

  String _formatUpdateSpeed(double bytesPerSecond) {
    if (bytesPerSecond <= 0) return '';
    const double kb = 1024;
    const double mb = kb * 1024;
    if (bytesPerSecond >= mb) return '${(bytesPerSecond / mb).toStringAsFixed(1)}M/s';
    if (bytesPerSecond >= kb) return '${(bytesPerSecond / kb).toStringAsFixed(0)}K/s';
    return '${bytesPerSecond.toStringAsFixed(0)}B/s';
  }

  Widget _buildUpdateTile() {
    final ctrl = _updateController;
    final currentVer = ctrl.currentVersionName != null
        ? 'v${ctrl.currentVersionName}${ctrl.currentVersionCode != null ? ' (${ctrl.currentVersionCode})' : ''}'
        : '打卡了吗';

    String subtitle;
    if (ctrl.isChecking) {
      subtitle = '正在检查 GitHub 最新版本...';
    } else if (ctrl.stage == UpdateUiStage.readyToInstall) {
      subtitle = '更新包已就绪，点击重启并应用更新';
    } else if (ctrl.stage == UpdateUiStage.verifying) {
      subtitle = '正在校验安装包完整性...';
    } else if (ctrl.stage == UpdateUiStage.openingInstaller) {
      subtitle = '正在启动安装程序...';
    } else if (ctrl.isUpdating) {
      final percent = '${ctrl.downloadProgressPercent.toStringAsFixed(0)}%';
      final downloaded = _formatUpdateBytes(ctrl.downloadedBytes);
      final total = _formatUpdateBytes(ctrl.totalBytes > 0 ? ctrl.totalBytes : (ctrl.availableUpdate?.fileSize ?? 0));
      final speed = _formatUpdateSpeed(ctrl.downloadBytesPerSecond);
      subtitle = '$percent | $downloaded/$total ${speed.isNotEmpty ? '| $speed' : ''}';
    } else if (ctrl.availableUpdate != null) {
      final update = ctrl.availableUpdate!;
      subtitle = '发现新版本 v${update.versionName} (${_formatUpdateBytes(update.fileSize)})，点击查看';
    } else if (ctrl.hasChecked) {
      subtitle = '当前已是最新版本 ($currentVer)';
    } else if (ctrl.checkError != null) {
      subtitle = '检查更新失败，点击重试';
    } else {
      subtitle = '当前版本：$currentVer · 点击联网检查更新';
    }

    Widget trailingWidget;
    if (ctrl.isChecking) {
      trailingWidget = const SizedBox(
        width: 20,
        height: 20,
        child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primaryBlue),
      );
    } else if (ctrl.stage == UpdateUiStage.readyToInstall) {
      trailingWidget = CapsuleActionButton(
        text: '重启安装',
        icon: Icons.refresh_rounded,
        primaryColor: AppTheme.emeraldGreen,
        fontSize: 12,
        onPressed: () => ctrl.installPendingPackage(),
      );
    } else if (ctrl.isUpdating) {
      trailingWidget = CapsuleBadge(
        text: '${ctrl.downloadProgressPercent.toStringAsFixed(0)}%',
        color: AppTheme.primaryBlue,
        fontSize: 12,
      );
    } else if (ctrl.availableUpdate != null) {
      trailingWidget = CapsuleActionButton(
        text: '立即更新',
        icon: Icons.download_rounded,
        primaryColor: AppTheme.primaryBlue,
        secondaryColor: AppTheme.accentCyan,
        fontSize: 12,
        onPressed: () {
          UpdateDialog.show(
            context: context,
            update: ctrl.availableUpdate!,
            currentVersion: ctrl.currentVersionName,
            controller: _updateController,
          );
        },
      );
    } else {
      trailingWidget = CapsuleActionButton(
        text: '检查更新',
        icon: Icons.sync_rounded,
        primaryColor: AppTheme.primaryBlue,
        fontSize: 12,
        onPressed: () => _checkAppUpdate(manual: true),
      );
    }

    return InkWell(
      onTap: ctrl.isUpdating
          ? null
          : () {
              HapticFeedback.lightImpact();
              if (ctrl.availableUpdate != null) {
                UpdateDialog.show(
                  context: context,
                  update: ctrl.availableUpdate!,
                  currentVersion: ctrl.currentVersionName,
                  controller: _updateController,
                );
              } else {
                _checkAppUpdate(manual: true);
              }
            },
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          children: [
            Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        AppTheme.primaryBlue.withValues(alpha: 0.18),
                        AppTheme.primaryBlue.withValues(alpha: 0.08),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: AppTheme.primaryBlue.withValues(alpha: 0.28),
                      width: 1,
                    ),
                  ),
                  child: const Icon(Icons.system_update_rounded, color: AppTheme.primaryBlue, size: 20),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Text(
                            '软件版本与更新',
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 15,
                              color: Color(0xFF0F172A),
                            ),
                          ),
                          if (ctrl.availableUpdate != null) ...[
                            const SizedBox(width: 6),
                            Container(
                              width: 8,
                              height: 8,
                              decoration: const BoxDecoration(
                                color: AppTheme.roseRed,
                                shape: BoxShape.circle,
                              ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        subtitle,
                        style: TextStyle(
                          fontSize: 12,
                          color: ctrl.checkError != null ? AppTheme.roseRed : AppTheme.slateGrey,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                trailingWidget,
              ],
            ),
            if (ctrl.isUpdating && ctrl.stage == UpdateUiStage.downloading) ...[
              const SizedBox(height: 10),
              ClipRRect(
                borderRadius: BorderRadius.circular(999),
                child: LinearProgressIndicator(
                  minHeight: 5,
                  value: (ctrl.downloadProgressPercent / 100).clamp(0.0, 1.0),
                  backgroundColor: const Color(0xFFE2E8F0),
                  valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryBlue),
                ),
              ),
            ],
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
            CapsuleActionButton(
              text: '去授权',
              icon: Icons.security_rounded,
              primaryColor: AppTheme.amberOrange,
              secondaryColor: const Color(0xFFD97706),
              onPressed: _requestNotificationPermission,
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
    return InkWell(
      onTap: () {
        HapticFeedback.lightImpact();
        onChanged(!value);
      },
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    color.withValues(alpha: 0.18),
                    color.withValues(alpha: 0.08),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: color.withValues(alpha: 0.28),
                  width: 1,
                ),
              ),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                      color: Color(0xFF0F172A),
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppTheme.slateGrey,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            CapsuleSwitch(
              value: value,
              onChanged: onChanged,
              activeColor: color,
            ),
          ],
        ),
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
    return InkWell(
      onTap: onTap != null
          ? () {
              HapticFeedback.lightImpact();
              onTap();
            }
          : null,
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    color.withValues(alpha: 0.18),
                    color.withValues(alpha: 0.08),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: color.withValues(alpha: 0.28),
                  width: 1,
                ),
              ),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                      color: Color(0xFF0F172A),
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppTheme.slateGrey,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            trailing ??
                Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(9),
                  ),
                  child: const Icon(
                    Icons.arrow_forward_ios_rounded,
                    size: 13,
                    color: AppTheme.slateGrey,
                  ),
                ),
          ],
        ),
      ),
    );
  }
}

class CheckInTimesEditDialog extends StatefulWidget {
  final List<String> initialTimes;

  const CheckInTimesEditDialog({super.key, required this.initialTimes});

  @override
  State<CheckInTimesEditDialog> createState() => _CheckInTimesEditDialogState();
}

class _CheckInTimesEditDialogState extends State<CheckInTimesEditDialog> {
  late List<String> _times;

  @override
  void initState() {
    super.initState();
    _times = List<String>.from(widget.initialTimes)..sort();
  }

  Future<void> _addTime() async {
    HapticFeedback.lightImpact();
    final now = TimeOfDay.now();
    final picked = await showGlassTimePicker(
      context: context,
      initialTime: now,
      title: '添加上班签到时间点',
      subtitle: '准时推送提醒，签到后自动取消后续',
      primaryColor: AppTheme.primaryBlue,
      quickPresets: ['08:00', '08:10', '08:16', '08:22', '08:28', '08:35', '08:50', '09:00'],
    );

    if (picked != null) {
      final hourStr = picked.hour.toString().padLeft(2, '0');
      final minStr = picked.minute.toString().padLeft(2, '0');
      final timeStr = '$hourStr:$minStr';

      if (!_times.contains(timeStr)) {
        setState(() {
          _times.add(timeStr);
          _times.sort();
        });
      }
    }
  }

  void _removeTime(String time) {
    HapticFeedback.lightImpact();
    if (_times.length <= 1) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('至少需要保留一个提醒时间点'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    setState(() {
      _times.remove(time);
    });
  }

  void _applyPreset(List<String> preset) {
    HapticFeedback.selectionClick();
    setState(() {
      _times = List<String>.from(preset)..sort();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 420),
        padding: const EdgeInsets.all(22),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF2563EB).withValues(alpha: 0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: const Icon(Icons.alarm_add_rounded, color: Colors.white, size: 22),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '上班签到时间批次',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF0F172A),
                        ),
                      ),
                      SizedBox(height: 2),
                      Text(
                        '到达各时间点准时提醒，签到后自动取消后续',
                        style: TextStyle(fontSize: 12, color: AppTheme.slateGrey),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded, color: AppTheme.slateGrey),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),

            const SizedBox(height: 20),

            const Text(
              '当前设定的提醒时间点：',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
            ),
            const SizedBox(height: 10),

            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  ..._times.map((time) => Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              AppTheme.primaryBlue.withValues(alpha: 0.12),
                              AppTheme.primaryBlue.withValues(alpha: 0.05),
                            ],
                          ),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: AppTheme.primaryBlue.withValues(alpha: 0.3),
                            width: 1,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.access_time_filled_rounded, size: 14, color: AppTheme.primaryBlue),
                            const SizedBox(width: 5),
                            Text(
                              time,
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF0F172A),
                              ),
                            ),
                            const SizedBox(width: 6),
                            GestureDetector(
                              onTap: () => _removeTime(time),
                              child: Container(
                                padding: const EdgeInsets.all(2),
                                decoration: BoxDecoration(
                                  color: Colors.black.withValues(alpha: 0.08),
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(Icons.close_rounded, size: 12, color: Color(0xFF64748B)),
                              ),
                            ),
                          ],
                        ),
                      )),
                  InkWell(
                    onTap: _addTime,
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: AppTheme.primaryBlue,
                          width: 1.2,
                        ),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.add_rounded, size: 16, color: AppTheme.primaryBlue),
                          SizedBox(width: 4),
                          Text(
                            '添加时间',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.primaryBlue,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            const Text(
              '一键快捷方案：',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
            ),
            const SizedBox(height: 8),

            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                _buildPresetChip(
                  label: '标准四连 (08:10, 08:16, 08:22, 08:28)',
                  preset: ['08:10', '08:16', '08:22', '08:28'],
                ),
                _buildPresetChip(
                  label: '九点前三连 (08:35, 08:45, 08:55)',
                  preset: ['08:35', '08:45', '08:55'],
                ),
                _buildPresetChip(
                  label: '单次提醒 (08:20)',
                  preset: ['08:20'],
                ),
              ],
            ),

            const SizedBox(height: 24),

            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                GlassCapsuleButton(
                  text: '取消',
                  isSecondary: true,
                  width: 78,
                  height: 36,
                  fontSize: 13,
                  onPressed: () => Navigator.of(context).pop(),
                ),
                const SizedBox(width: 10),
                GlassCapsuleButton(
                  text: '保存配置',
                  icon: Icons.check_rounded,
                  primaryColor: AppTheme.primaryBlue,
                  width: 108,
                  height: 36,
                  fontSize: 13,
                  onPressed: () => Navigator.of(context).pop(_times),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPresetChip({required String label, required List<String> preset}) {
    return ActionChip(
      label: Text(label, style: const TextStyle(fontSize: 11)),
      backgroundColor: const Color(0xFFF1F5F9),
      side: const BorderSide(color: Color(0xFFE2E8F0)),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      onPressed: () => _applyPreset(preset),
    );
  }
}

class CheckOutConfigEditDialog extends StatefulWidget {
  final String initialStartTime;
  final String initialEndTime;
  final int initialInterval;

  const CheckOutConfigEditDialog({
    super.key,
    required this.initialStartTime,
    required this.initialEndTime,
    required this.initialInterval,
  });

  @override
  State<CheckOutConfigEditDialog> createState() => _CheckOutConfigEditDialogState();
}

class _CheckOutConfigEditDialogState extends State<CheckOutConfigEditDialog> {
  late String _startTime;
  late String _endTime;
  late int _interval;

  @override
  void initState() {
    super.initState();
    _startTime = widget.initialStartTime;
    _endTime = widget.initialEndTime;
    _interval = widget.initialInterval;
  }

  Future<void> _pickTime(bool isStart) async {
    HapticFeedback.lightImpact();
    final currentStr = isStart ? _startTime : _endTime;
    final parts = currentStr.split(':');
    final initial = TimeOfDay(
      hour: int.tryParse(parts[0]) ?? (isStart ? 18 : 19),
      minute: int.tryParse(parts[1]) ?? (isStart ? 5 : 30),
    );

    final picked = await showGlassTimePicker(
      context: context,
      initialTime: initial,
      title: isStart ? '设置开始签退提醒时间' : '设置结束签退提醒时间',
      subtitle: isStart ? '进入该时间段后触发打卡提醒' : '超过此时间点停止提醒',
      primaryColor: const Color(0xFF6366F1),
      quickPresets: isStart
          ? ['17:30', '18:00', '18:05', '18:30']
          : ['18:30', '19:00', '19:30', '20:00'],
    );

    if (picked != null) {
      final hourStr = picked.hour.toString().padLeft(2, '0');
      final minStr = picked.minute.toString().padLeft(2, '0');
      final res = '$hourStr:$minStr';

      setState(() {
        if (isStart) {
          _startTime = res;
        } else {
          _endTime = res;
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final intervals = [5, 10, 15, 20, 30];

    return Dialog(
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 420),
        padding: const EdgeInsets.all(22),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF818CF8), Color(0xFF4F46E5)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF6366F1).withValues(alpha: 0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: const Icon(Icons.timer_rounded, color: Colors.white, size: 22),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '下班签退提醒规划',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF0F172A),
                        ),
                      ),
                      SizedBox(height: 2),
                      Text(
                        '时间窗口内循环提醒，签退后自动终止',
                        style: TextStyle(fontSize: 12, color: AppTheme.slateGrey),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded, color: AppTheme.slateGrey),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),

            const SizedBox(height: 20),

            Row(
              children: [
                Expanded(
                  child: _buildTimeCard(
                    title: '开始签退提醒',
                    time: _startTime,
                    icon: Icons.logout_rounded,
                    onTap: () => _pickTime(true),
                  ),
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 8),
                  child: Icon(Icons.arrow_forward_rounded, color: AppTheme.slateGrey, size: 18),
                ),
                Expanded(
                  child: _buildTimeCard(
                    title: '结束签退提醒',
                    time: _endTime,
                    icon: Icons.nightlight_round,
                    onTap: () => _pickTime(false),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 18),

            const Text(
              '提醒间隔频率：',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
            ),
            const SizedBox(height: 8),

            Row(
              children: intervals.map((m) {
                final isSelected = _interval == m;
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: InkWell(
                      onTap: () {
                        HapticFeedback.selectionClick();
                        setState(() => _interval = m);
                      },
                      borderRadius: BorderRadius.circular(12),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 180),
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        decoration: BoxDecoration(
                          gradient: isSelected
                              ? const LinearGradient(
                                  colors: [Color(0xFF6366F1), Color(0xFF4F46E5)],
                                )
                              : null,
                          color: isSelected ? null : const Color(0xFFF1F5F9),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: isSelected ? Colors.transparent : const Color(0xFFE2E8F0),
                          ),
                          boxShadow: isSelected
                              ? [
                                  BoxShadow(
                                    color: const Color(0xFF6366F1).withValues(alpha: 0.3),
                                    blurRadius: 6,
                                    offset: const Offset(0, 2),
                                  ),
                                ]
                              : null,
                        ),
                        child: Center(
                          child: Text(
                            '$m分',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: isSelected ? Colors.white : const Color(0xFF475569),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),

            const SizedBox(height: 16),

            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF6366F1).withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF6366F1).withValues(alpha: 0.2)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline_rounded, size: 16, color: Color(0xFF4F46E5)),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '工作日将在 $_startTime 至 $_endTime 期间，每隔 $_interval 分钟提醒一次打卡。',
                      style: const TextStyle(fontSize: 11.5, color: Color(0xFF4F46E5), height: 1.3),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 22),

            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                GlassCapsuleButton(
                  text: '取消',
                  isSecondary: true,
                  width: 78,
                  height: 36,
                  fontSize: 13,
                  onPressed: () => Navigator.of(context).pop(),
                ),
                const SizedBox(width: 10),
                GlassCapsuleButton(
                  text: '保存配置',
                  icon: Icons.check_rounded,
                  primaryColor: const Color(0xFF6366F1),
                  secondaryColor: const Color(0xFF4F46E5),
                  width: 108,
                  height: 36,
                  fontSize: 13,
                  onPressed: () {
                    Navigator.of(context).pop({
                      'start': _startTime,
                      'end': _endTime,
                      'interval': _interval,
                    });
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeCard({
    required String title,
    required String time,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
        decoration: BoxDecoration(
          color: const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Column(
          children: [
            Text(title, style: const TextStyle(fontSize: 11, color: AppTheme.slateGrey)),
            const SizedBox(height: 6),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 16, color: const Color(0xFF6366F1)),
                const SizedBox(width: 6),
                Text(
                  time,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF0F172A),
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
