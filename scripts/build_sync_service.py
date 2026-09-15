import os

holiday_sync_service_code = """import 'dart:convert';
import 'package:http/http.dart' as http;
import '../constants/holiday_data.dart';
import '../database/database_helper.dart';

class HolidaySyncService {
  final DatabaseHelper _dbHelper;

  HolidaySyncService({DatabaseHelper? dbHelper})
      : _dbHelper = dbHelper ?? DatabaseHelper.instance;

  static const String _keySyncedPrefix = 'synced_holidays_';
  static const String _keySyncTimePrefix = 'synced_time_';

  /// Fetch statutory holidays and compensatory workdays for [year].
  /// Uses the widely accepted open-source authoritative API (timor.tech holiday API or holiday-cn).
  /// Falls back smoothly if offline.
  Future<HolidayConfig?> syncHolidaysForYear(int year) async {
    try {
      // Endpoint 1: Timor Tech Holiday API (standard public JSON API for China holidays)
      final url = Uri.parse('https://timor.tech/api/holiday/year/$year/');
      final response = await http.get(url).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        final code = data['code'];
        if (code == 0 && data['holiday'] is Map) {
          final holidayMap = data['holiday'] as Map<String, dynamic>;

          final Set<String> holidays = {};
          final Set<String> workdays = {};

          holidayMap.forEach((dateKey, val) {
            if (val is Map) {
              final isHoliday = val['holiday'] == true;
              final dateStr = '$year-$dateKey';
              if (isHoliday) {
                holidays.add(dateStr);
              } else {
                workdays.add(dateStr);
              }
            }
          });

          final config = HolidayConfig(
            year: year,
            versionInfo: '$year年国务院办公厅官方通告 (联网已同步)',
            holidays: holidays,
            workdays: workdays,
          );

          // Save to local database
          await _saveSyncedConfig(year, config);
          return config;
        }
      }
    } catch (_) {
      // In case of timeout or offline, check if we previously synced this year
    }

    return await getLocalSyncedConfig(year);
  }

  Future<void> _saveSyncedConfig(int year, HolidayConfig config) async {
    final payload = json.encode({
      'year': config.year,
      'versionInfo': config.versionInfo,
      'holidays': config.holidays.toList(),
      'workdays': config.workdays.toList(),
    });
    await _dbHelper.setSetting('$_keySyncedPrefix$year', payload);
    await _dbHelper.setSetting('$_keySyncTimePrefix$year', DateTime.now().toIso8601String());
  }

  Future<HolidayConfig?> getLocalSyncedConfig(int year) async {
    final raw = await _dbHelper.getSetting('$_keySyncedPrefix$year');
    if (raw == null || raw.isEmpty) return null;
    try {
      final map = json.decode(raw) as Map<String, dynamic>;
      return HolidayConfig(
        year: map['year'] as int,
        versionInfo: map['versionInfo'] as String,
        holidays: Set<String>.from(map['holidays'] as List),
        workdays: Set<String>.from(map['workdays'] as List),
      );
    } catch (_) {
      return null;
    }
  }

  Future<String?> getLastSyncTime(int year) async {
    return await _dbHelper.getSetting('$_keySyncTimePrefix$year');
  }
}
"""

with open('lib/services/holiday_sync_service.dart', 'w', encoding='utf-8') as f:
    f.write(holiday_sync_service_code.strip() + '\n')
print('HolidaySyncService generated.')
