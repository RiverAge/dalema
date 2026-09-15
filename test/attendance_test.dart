import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:dalema/database/database_helper.dart';
import 'package:dalema/services/attendance_service.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  late Database db;
  late AttendanceService attendanceService;

  setUp(() async {
    // In-memory database for isolated unit testing
    db = await databaseFactory.openDatabase(inMemoryDatabasePath);
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

    DatabaseHelper.setDatabaseForTesting(db);
    attendanceService = AttendanceService();
  });

  tearDown(() async {
    await db.close();
  });

  group('Attendance & Database Operations Tests', () {
    test('1. Check In records time correctly and prevents duplicate check-in', () async {
      final testTime = DateTime(2026, 9, 11, 8, 20, 0);

      // First check-in succeeds
      final record = await attendanceService.checkIn(customNow: testTime);
      expect(record.date, equals('2026-09-11'));
      expect(record.hasCheckIn, isTrue);
      expect(record.checkInTime, equals('08:20:00'));

      // Second check-in on the same day must throw StateError
      expect(
        () async => await attendanceService.checkIn(customNow: testTime),
        throwsA(isA<StateError>()),
      );
    });

    test('2. Check Out records time correctly and prevents duplicate check-out', () async {
      final checkInTime = DateTime(2026, 9, 11, 8, 25, 0);
      final checkOutTime = DateTime(2026, 9, 11, 18, 30, 0);

      await attendanceService.checkIn(customNow: checkInTime);
      final outRecord = await attendanceService.checkOut(customNow: checkOutTime);

      expect(outRecord.hasCheckIn, isTrue);
      expect(outRecord.hasCheckOut, isTrue);
      expect(outRecord.checkOutTime, equals('18:30:00'));

      // Duplicate check-out must throw StateError
      expect(
        () async => await attendanceService.checkOut(customNow: checkOutTime),
        throwsA(isA<StateError>()),
      );
    });

    test('3. Query attendance records by month', () async {
      // Insert records across different dates
      await attendanceService.checkIn(customNow: DateTime(2026, 9, 1, 8, 30));
      await attendanceService.checkIn(customNow: DateTime(2026, 9, 15, 8, 30));
      await attendanceService.checkIn(customNow: DateTime(2026, 10, 1, 8, 30));

      final sepRecords = await attendanceService.getRecordsByMonth('2026-09');
      expect(sepRecords.length, equals(2));
      expect(sepRecords.first.date, equals('2026-09-01'));
      expect(sepRecords.last.date, equals('2026-09-15'));

      final octRecords = await attendanceService.getRecordsByMonth('2026-10');
      expect(octRecords.length, equals(1));
      expect(octRecords.first.date, equals('2026-10-01'));
    });

    test('4. Delete records by date range with confirmation support', () async {
      await attendanceService.checkIn(customNow: DateTime(2026, 9, 10, 8, 30));
      await attendanceService.checkIn(customNow: DateTime(2026, 9, 11, 8, 30));
      await attendanceService.checkIn(customNow: DateTime(2026, 9, 12, 8, 30));
      await attendanceService.checkIn(customNow: DateTime(2026, 9, 20, 8, 30));

      // Delete records between 2026-09-10 and 2026-09-12
      final deletedCount = await attendanceService.deleteRecordsByRange('2026-09-10', '2026-09-12');
      expect(deletedCount, equals(3));

      // 2026-09-20 should still exist
      final remaining = await attendanceService.getRecordsByMonth('2026-09');
      expect(remaining.length, equals(1));
      expect(remaining.first.date, equals('2026-09-20'));
    });

    test('5. Delete records by month', () async {
      await attendanceService.checkIn(customNow: DateTime(2026, 8, 1, 8, 30));
      await attendanceService.checkIn(customNow: DateTime(2026, 8, 2, 8, 30));
      await attendanceService.checkIn(customNow: DateTime(2026, 9, 1, 8, 30));

      final deletedCount = await attendanceService.deleteRecordsByMonth('2026-08');
      expect(deletedCount, equals(2));

      final augRecords = await attendanceService.getRecordsByMonth('2026-08');
      expect(augRecords, isEmpty);

      final sepRecords = await attendanceService.getRecordsByMonth('2026-09');
      expect(sepRecords.length, equals(1));
    });
  });
}
