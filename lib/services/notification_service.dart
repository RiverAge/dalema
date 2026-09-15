import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import '../database/database_helper.dart';
import '../models/app_settings.dart';
import 'calendar_service.dart';
import 'settings_service.dart';

class NotificationService {
  static final NotificationService instance = NotificationService._init();

  final FlutterLocalNotificationsPlugin _notificationsPlugin =
      FlutterLocalNotificationsPlugin();

  final SettingsService _settingsService;
  final CalendarService _calendarService;
  final DatabaseHelper _dbHelper;

  bool _isInitialized = false;

  NotificationService._init({
    SettingsService? settingsService,
    CalendarService? calendarService,
    DatabaseHelper? dbHelper,
  })  : _settingsService = settingsService ?? SettingsService(),
        _calendarService = calendarService ?? CalendarService(),
        _dbHelper = dbHelper ?? DatabaseHelper.instance;

  // Channel IDs (Alarm-grade channels with USAGE_ALARM to bypass silent mode and play in earphones)
  static const String checkInChannelId = 'dalema_check_in_alarm_v5';
  static const String checkInChannelName = '上班签到闹钟提醒';
  static const String checkInChannelDesc = '用于工作日上班签到打卡强提醒（支持静音震动与耳机播报）';

  static const String checkOutChannelId = 'dalema_check_out_alarm_v5';
  static const String checkOutChannelName = '下班签退闹钟提醒';
  static const String checkOutChannelDesc = '用于工作日下班签退打卡强提醒（支持静音震动与耳机播报）';

  // Base IDs for scheduled notifications
  // Day offset 0..6 (today + next 6 days)
  // Check-in ID range: 1000..1999
  // Check-out ID range: 2000..2999
  static const int checkInBaseId = 1000;
  static const int checkOutBaseId = 2000;

  Future<void> init({void Function(NotificationResponse)? onDidReceiveNotificationResponse}) async {
    if (_isInitialized) return;

    tz.initializeTimeZones();
    // Use local time zone
    try {
      // local timezone initialized
      // Best effort set local location or Asia/Shanghai if available
      final shanghai = tz.getLocation('Asia/Shanghai');
      tz.setLocalLocation(shanghai);
    } catch (_) {
      // Fallback tz.local already initialized
    }

    const AndroidInitializationSettings androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const DarwinInitializationSettings iosSettings = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );

    const InitializationSettings initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _notificationsPlugin.initialize(
      settings: initSettings,
      onDidReceiveNotificationResponse: onDidReceiveNotificationResponse,
    );

    // Create high-priority alarm channels on Android with USAGE_ALARM to bypass silent mode and play in earphones
    if (Platform.isAndroid && !Platform.environment.containsKey('FLUTTER_TEST')) {
      final androidImplementation = _notificationsPlugin
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();
      if (androidImplementation != null) {
        final pattern = Int64List.fromList([200, 600, 200, 600, 200, 600]);
        try {
          await androidImplementation.deleteNotificationChannel(channelId: 'dalema_check_in_channel');
          await androidImplementation.deleteNotificationChannel(channelId: 'dalema_check_out_channel');
          await androidImplementation.deleteNotificationChannel(channelId: 'dalema_check_in_alarm_v3');
          await androidImplementation.deleteNotificationChannel(channelId: 'dalema_check_out_alarm_v3');
          await androidImplementation.deleteNotificationChannel(channelId: 'dalema_check_in_alarm_v4');
          await androidImplementation.deleteNotificationChannel(channelId: 'dalema_check_out_alarm_v4');
        } catch (_) {}

        await androidImplementation.createNotificationChannel(
          AndroidNotificationChannel(
            checkInChannelId,
            checkInChannelName,
            description: checkInChannelDesc,
            importance: Importance.max,
            playSound: true,
            enableVibration: true,
            vibrationPattern: pattern,
            audioAttributesUsage: AudioAttributesUsage.alarm,
          ),
        );

        await androidImplementation.createNotificationChannel(
          AndroidNotificationChannel(
            checkOutChannelId,
            checkOutChannelName,
            description: checkOutChannelDesc,
            importance: Importance.max,
            playSound: true,
            enableVibration: true,
            vibrationPattern: pattern,
            audioAttributesUsage: AudioAttributesUsage.alarm,
          ),
        );
      }
    }

    _isInitialized = true;
  }

  /// Request permissions for Android 13+ (POST_NOTIFICATIONS) and iOS
  Future<bool> requestPermissions() async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) return true;
    if (kIsWeb) return false;

    if (Platform.isAndroid) {
      final androidImplementation = _notificationsPlugin
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();
      if (androidImplementation != null) {
        final granted =
            await androidImplementation.requestNotificationsPermission();
        await androidImplementation.requestExactAlarmsPermission();
        return granted ?? false;
      }
    } else if (Platform.isIOS) {
      final iosImplementation = _notificationsPlugin
          .resolvePlatformSpecificImplementation<
              IOSFlutterLocalNotificationsPlugin>();
      if (iosImplementation != null) {
        final granted = await iosImplementation.requestPermissions(
          alert: true,
          badge: true,
          sound: true,
        );
        return granted ?? false;
      }
    }
    return true;
  }

  /// Check whether notifications are permitted
  Future<bool> checkPermissionStatus() async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) return true;
    if (kIsWeb) return false;

    if (Platform.isAndroid) {
      final androidImplementation = _notificationsPlugin
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();
      if (androidImplementation != null) {
        final areEnabled =
            await androidImplementation.areNotificationsEnabled();
        return areEnabled ?? false;
      }
    }
    return true;
  }

  /// Reschedule all upcoming notifications based on:
  /// - Current settings (enabled/disabled, sound, vibration, schedules)
  /// - Calendar workdays/holidays for the next 7 days
  /// - Actual database check-in/out records for today
  Future<void> rescheduleAllNotifications() async {
    // In headless test environments or platforms without notification plugin initialized, skip
    if (Platform.environment.containsKey('FLUTTER_TEST')) {
      return;
    }
    // 1. Cancel all existing scheduled notifications
    await _notificationsPlugin.cancelAll();

    final settings = await _settingsService.getSettings();
    if (!settings.notificationEnabled) {
      return;
    }

    final now = DateTime.now();
    // Schedule for next 7 days (today is day 0)
    for (int dayOffset = 0; dayOffset < 7; dayOffset++) {
      final targetDate = now.add(Duration(days: dayOffset));
      final dateStr =
          '${targetDate.year.toString().padLeft(4, '0')}-${targetDate.month.toString().padLeft(2, '0')}-${targetDate.day.toString().padLeft(2, '0')}';

      // Check if it's a workday
      final isWorkday = await _calendarService.isWorkday(targetDate);
      if (!isWorkday) {
        // Statutory holiday or weekend rest without adjustment -> do not schedule
        continue;
      }

      // Check attendance record from database
      final record = await _dbHelper.getRecordByDate(dateStr);

      // 1. Check In schedule
      if (settings.checkInEnabled) {
        final hasCheckedIn = record?.hasCheckIn ?? false;
        if (!hasCheckedIn) {
          await _scheduleCheckInTimes(
            targetDate: targetDate,
            dayOffset: dayOffset,
            settings: settings,
            now: now,
          );
        }
      }

      // 2. Check Out schedule
      if (settings.checkOutEnabled) {
        final hasCheckedOut = record?.hasCheckOut ?? false;
        if (!hasCheckedOut) {
          await _scheduleCheckOutTimes(
            targetDate: targetDate,
            dayOffset: dayOffset,
            settings: settings,
            now: now,
          );
        }
      }
    }
  }

  Future<void> _scheduleCheckInTimes({
    required DateTime targetDate,
    required int dayOffset,
    required AppSettings settings,
    required DateTime now,
  }) async {
    final times = settings.checkInTimes;
    for (int i = 0; i < times.length; i++) {
      final timeStr = times[i];
      final parts = timeStr.split(':').map(int.parse).toList();
      final scheduleDateTime = DateTime(
        targetDate.year,
        targetDate.month,
        targetDate.day,
        parts[0],
        parts[1],
      );

      // If scheduled time has already passed, skip
      if (scheduleDateTime.isBefore(now)) {
        continue;
      }

      final id = checkInBaseId + (dayOffset * 20) + i;
      final tzScheduledTime = tz.TZDateTime.from(scheduleDateTime, tz.local);

      final pattern = Int64List.fromList([200, 600, 200, 600, 200, 600]);
      final androidDetails = AndroidNotificationDetails(
        checkInChannelId,
        checkInChannelName,
        channelDescription: checkInChannelDesc,
        importance: Importance.max,
        priority: Priority.max,
        playSound: settings.soundEnabled,
        enableVibration: settings.vibrationEnabled,
        vibrationPattern: settings.vibrationEnabled ? pattern : null,
        audioAttributesUsage: AudioAttributesUsage.alarm,
        icon: '@mipmap/ic_launcher',
        category: AndroidNotificationCategory.alarm,
        fullScreenIntent: true,
        actions: const [
          AndroidNotificationAction('open_app', '打开 App 打卡'),
        ],
      );

      const iosDetails = DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
      );

      final notifDetails = NotificationDetails(
        android: androidDetails,
        iOS: iosDetails,
      );

      try {
        await _notificationsPlugin.zonedSchedule(
          id: id,
          title: '上班签到提醒',
          body: '新的一天开始了，请及时打开 App 完成上班签到！',
          scheduledDate: tzScheduledTime,
          notificationDetails: notifDetails,
          androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        );
      } catch (e) {
        // Fallback for non-exact alarm restrictions if any
        if (kDebugMode) {
          print('Schedule check-in error: $e');
        }
      }
    }
  }

  Future<void> _scheduleCheckOutTimes({
    required DateTime targetDate,
    required int dayOffset,
    required AppSettings settings,
    required DateTime now,
  }) async {
    final times = settings.getCalculatedCheckOutTimes();
    for (int i = 0; i < times.length; i++) {
      final timeStr = times[i];
      final parts = timeStr.split(':').map(int.parse).toList();
      final scheduleDateTime = DateTime(
        targetDate.year,
        targetDate.month,
        targetDate.day,
        parts[0],
        parts[1],
      );

      if (scheduleDateTime.isBefore(now)) {
        continue;
      }

      final id = checkOutBaseId + (dayOffset * 50) + i;
      final tzScheduledTime = tz.TZDateTime.from(scheduleDateTime, tz.local);

      final pattern = Int64List.fromList([200, 600, 200, 600, 200, 600]);
      final androidDetails = AndroidNotificationDetails(
        checkOutChannelId,
        checkOutChannelName,
        channelDescription: checkOutChannelDesc,
        importance: Importance.max,
        priority: Priority.max,
        playSound: settings.soundEnabled,
        enableVibration: settings.vibrationEnabled,
        vibrationPattern: settings.vibrationEnabled ? pattern : null,
        audioAttributesUsage: AudioAttributesUsage.alarm,
        icon: '@mipmap/ic_launcher',
        category: AndroidNotificationCategory.alarm,
        fullScreenIntent: true,
        actions: const [
          AndroidNotificationAction('open_app', '打开 App 打卡'),
        ],
      );

      const iosDetails = DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
      );

      final notifDetails = NotificationDetails(
        android: androidDetails,
        iOS: iosDetails,
      );

      try {
        await _notificationsPlugin.zonedSchedule(
          id: id,
          title: '下班签退提醒',
          body: '辛苦了一天，别忘了打开 App 完成下班签退！',
          scheduledDate: tzScheduledTime,
          notificationDetails: notifDetails,
          androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        );
      } catch (e) {
        if (kDebugMode) {
          print('Schedule check-out error: $e');
        }
      }
    }
  }

  /// Cancel all today check-in notifications when user checks in
  Future<void> cancelTodayCheckInNotifications() async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) return;
    // DayOffset 0 IDs are checkInBaseId .. checkInBaseId + 19
    for (int i = 0; i < 20; i++) {
      await _notificationsPlugin.cancel(id: checkInBaseId + i);
    }
  }

  /// Cancel all today check-out notifications when user checks out
  Future<void> cancelTodayCheckOutNotifications() async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) return;
    // DayOffset 0 IDs are checkOutBaseId .. checkOutBaseId + 49
    for (int i = 0; i < 50; i++) {
      await _notificationsPlugin.cancel(id: checkOutBaseId + i);
    }
  }

  /// Send an immediate high-priority test notification (fires right away)
  Future<void> sendInstantTestNotification({bool isCheckIn = false}) async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) return;

    final pattern = Int64List.fromList([100, 800, 250, 800, 250, 1000]);
    final channelId = isCheckIn ? checkInChannelId : checkOutChannelId;
    final channelName = isCheckIn ? checkInChannelName : checkOutChannelName;

    final androidDetails = AndroidNotificationDetails(
      channelId,
      channelName,
      channelDescription: '测试强提醒通知通道',
      importance: Importance.max,
      priority: Priority.max,
      playSound: true,
      enableVibration: true,
      vibrationPattern: pattern,
      audioAttributesUsage: AudioAttributesUsage.alarm,
      icon: '@mipmap/ic_launcher',
      category: AndroidNotificationCategory.alarm,
      fullScreenIntent: true,
      actions: const [
        AndroidNotificationAction('open_app', '打开 App 查看'),
      ],
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final notifDetails = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _notificationsPlugin.show(
      id: 9999,
      title: isCheckIn ? '🔔【测试】上班签到强提醒' : '🌙【测试】下班签退强提醒',
      body: '这是一条高优先级测试推送，已触发强震动与闹钟级提示音！',
      notificationDetails: notifDetails,
    );
  }
}
