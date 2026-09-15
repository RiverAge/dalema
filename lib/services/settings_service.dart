import '../database/database_helper.dart';
import '../models/app_settings.dart';

class SettingsService {
  final DatabaseHelper _dbHelper;

  SettingsService({DatabaseHelper? dbHelper})
      : _dbHelper = dbHelper ?? DatabaseHelper.instance;

  static const _keyCheckInEnabled = 'check_in_enabled';
  static const _keyCheckOutEnabled = 'check_out_enabled';
  static const _keyNotificationEnabled = 'notification_enabled';
  static const _keySoundEnabled = 'sound_enabled';
  static const _keyVibrationEnabled = 'vibration_enabled';
  static const _keyCheckInTimes = 'check_in_times';
  static const _keyCheckOutStartTime = 'check_out_start_time';
  static const _keyCheckOutEndTime = 'check_out_end_time';
  static const _keyCheckOutInterval = 'check_out_interval';

  Future<AppSettings> getSettings() async {
    final settingsMap = await _dbHelper.getAllSettings();
    if (settingsMap.isEmpty) {
      return const AppSettings();
    }

    final checkInEnabled = settingsMap[_keyCheckInEnabled] == null
        ? true
        : settingsMap[_keyCheckInEnabled] == 'true';
    final checkOutEnabled = settingsMap[_keyCheckOutEnabled] == null
        ? true
        : settingsMap[_keyCheckOutEnabled] == 'true';
    final notificationEnabled = settingsMap[_keyNotificationEnabled] == null
        ? true
        : settingsMap[_keyNotificationEnabled] == 'true';
    final soundEnabled = settingsMap[_keySoundEnabled] == null
        ? true
        : settingsMap[_keySoundEnabled] == 'true';
    final vibrationEnabled = settingsMap[_keyVibrationEnabled] == null
        ? true
        : settingsMap[_keyVibrationEnabled] == 'true';

    final checkInTimesStr = settingsMap[_keyCheckInTimes];
    final checkInTimes = checkInTimesStr != null && checkInTimesStr.isNotEmpty
        ? checkInTimesStr.split(',')
        : const ['08:10', '08:16', '08:22', '08:28'];

    final checkOutStartTime =
        settingsMap[_keyCheckOutStartTime] ?? '18:05';
    final checkOutEndTime =
        settingsMap[_keyCheckOutEndTime] ?? '19:30';
    final checkOutInterval =
        int.tryParse(settingsMap[_keyCheckOutInterval] ?? '15') ?? 15;

    return AppSettings(
      checkInEnabled: checkInEnabled,
      checkOutEnabled: checkOutEnabled,
      notificationEnabled: notificationEnabled,
      soundEnabled: soundEnabled,
      vibrationEnabled: vibrationEnabled,
      checkInTimes: checkInTimes,
      checkOutStartTime: checkOutStartTime,
      checkOutEndTime: checkOutEndTime,
      checkOutIntervalMinutes: checkOutInterval,
    );
  }

  Future<void> saveSettings(AppSettings settings) async {
    await _dbHelper.setSetting(_keyCheckInEnabled, settings.checkInEnabled.toString());
    await _dbHelper.setSetting(_keyCheckOutEnabled, settings.checkOutEnabled.toString());
    await _dbHelper.setSetting(_keyNotificationEnabled, settings.notificationEnabled.toString());
    await _dbHelper.setSetting(_keySoundEnabled, settings.soundEnabled.toString());
    await _dbHelper.setSetting(_keyVibrationEnabled, settings.vibrationEnabled.toString());
    await _dbHelper.setSetting(_keyCheckInTimes, settings.checkInTimes.join(','));
    await _dbHelper.setSetting(_keyCheckOutStartTime, settings.checkOutStartTime);
    await _dbHelper.setSetting(_keyCheckOutEndTime, settings.checkOutEndTime);
    await _dbHelper.setSetting(_keyCheckOutInterval, settings.checkOutIntervalMinutes.toString());
  }

  Future<void> restoreDefaults() async {
    await saveSettings(const AppSettings());
  }
}
