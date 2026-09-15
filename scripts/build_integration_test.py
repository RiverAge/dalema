import os

test_code = """import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:dalema/database/database_helper.dart';
import 'package:dalema/services/attendance_service.dart';
import 'package:dalema/services/calendar_service.dart';
import 'package:dalema/services/settings_service.dart';
import 'package:dalema/models/app_settings.dart';
import 'package:dalema/models/calendar_override.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  late Database db;
  late AttendanceService attendanceService;
  late CalendarService calendarService;
  late SettingsService settingsService;

  setUp(() async {
    db = await databaseFactory.openDatabase(
      inMemoryDatabasePath,
      options: OpenDatabaseOptions(
        version: 1,
        onCreate: (db, version) async {
          await db.execute('''
            CREATE TABLE attendance_records (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              date TEXT NOT NULL UNIQUE,
              check_in_time TEXT,
              check_out_time TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
          ''');
          await db.execute('''
            CREATE TABLE calendar_overrides (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              date TEXT NOT NULL UNIQUE,
              day_type TEXT NOT NULL,
              note TEXT
            )
          ''');
          await db.execute('''
            CREATE TABLE settings (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            )
          ''');
        },
      ),
    );
    DatabaseHelper.setDatabaseForTesting(db);
    attendanceService = AttendanceService();
    calendarService = CalendarService();
    settingsService = SettingsService();
  });

  tearDown(() async {
    await db.close();
  });

  group('Full Service Integration Tests', () {
    test('1. Check In & Check Out Complete Flow', () async {
      final morning = DateTime(2026, 9, 11, 8, 15, 0);
      final evening = DateTime(2026, 9, 11, 18, 10, 0);

      // 1. Initial today record is null
      var record = await attendanceService.getTodayRecord(morning);
      expect(record, isNull);

      // 2. Perform check in
      record = await attendanceService.checkIn(customNow: morning);
      expect(record.hasCheckIn, isTrue);
      expect(record.checkInTime, equals('08:15:00'));
      expect(record.hasCheckOut, isFalse);

      // 3. Perform check out
      record = await attendanceService.checkOut(customNow: evening);
      expect(record.hasCheckIn, isTrue);
      expect(record.hasCheckOut, isTrue);
      expect(record.checkOutTime, equals('18:10:00'));

      // 4. Repeated operations rejected
      expect(() async => await attendanceService.checkIn(customNow: morning), throwsA(isA<StateError>()));
      expect(() async => await attendanceService.checkOut(customNow: evening), throwsA(isA<StateError>()));
    });

    test('2. Settings persistence and restoration flow', () async {
      var s = await settingsService.getSettings();
      expect(s.notificationEnabled, isTrue);
      expect(s.checkInEnabled, isTrue);
      expect(s.checkOutEnabled, isTrue);

      // Modify settings
      final updated = s.copyWith(
        checkInTimes: ['08:00', '08:15', '08:30'],
        checkOutStartTime: '17:30',
        checkOutEndTime: '19:00',
        checkOutIntervalMinutes: 30,
        soundEnabled: false,
      );
      await settingsService.saveSettings(updated);

      final reloaded = await settingsService.getSettings();
      expect(reloaded.checkInTimes, equals(['08:00', '08:15', '08:30']));
      expect(reloaded.checkOutStartTime, equals('17:30'));
      expect(reloaded.soundEnabled, isFalse);
      expect(reloaded.getCalculatedCheckOutTimes(), equals(['17:30', '18:00', '18:30', '19:00']));

      // Restore defaults
      await settingsService.restoreDefaults();
      final restored = await settingsService.getSettings();
      expect(restored.soundEnabled, isTrue);
      expect(restored.checkInTimes, equals(['08:10', '08:16', '08:22', '08:28']));
    });

    test('3. Calendar management override persistence', () async {
      final date = DateTime(2026, 5, 2); // Saturday
      expect(await calendarService.isWorkday(date), isFalse); // default weekend

      // Override to workday
      await calendarService.setDayOverride(date, DayType.workday, note: '公司团建补班');
      expect(await calendarService.isWorkday(date), isTrue);

      // Override back to default
      await calendarService.setDayOverride(date, DayType.defaultRule);
      expect(await calendarService.isWorkday(date), isFalse);
    });
  });
}
"""

with open('test/service_integration_test.dart', 'w', encoding='utf-8') as f:
    f.write(test_code.strip() + '\n')
print('test/service_integration_test.dart generated.')
