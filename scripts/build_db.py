import os

database_code = """import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';
import '../models/attendance_record.dart';
import '../models/calendar_override.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('dalema.db');
    return _database!;
  }

  // Allow injecting custom database factory / instance for testing
  static void setDatabaseForTesting(Database db) {
    _database = db;
  }

  Future<Database> _initDB(String filePath) async {
    try {
      final dbPath = await getDatabasesPath();
      final path = join(dbPath, filePath);
      return await openDatabase(
        path,
        version: 1,
        onCreate: _createDB,
      );
    } catch (e) {
      // Graceful error handling for missing db or initialization failure
      rethrow;
    }
  }

  Future<void> _createDB(Database db, int version) async {
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
  }

  // ==================== Attendance Records ====================

  Future<AttendanceRecord?> getRecordByDate(String date) async {
    final db = await database;
    final maps = await db.query(
      'attendance_records',
      where: 'date = ?',
      whereArgs: [date],
      limit: 1,
    );
    if (maps.isNotEmpty) {
      return AttendanceRecord.fromMap(maps.first);
    }
    return null;
  }

  Future<int> insertOrUpdateCheckIn({
    required String date,
    required String checkInTime,
    required String nowIso,
  }) async {
    final db = await database;
    final existing = await getRecordByDate(date);
    if (existing == null) {
      final record = AttendanceRecord(
        date: date,
        checkInTime: checkInTime,
        createdAt: nowIso,
        updatedAt: nowIso,
      );
      return await db.insert('attendance_records', record.toMap());
    } else {
      // If already has check-in, do not overwrite (cannot modify recorded time)
      if (existing.hasCheckIn) {
        return existing.id ?? 0;
      }
      return await db.update(
        'attendance_records',
        {
          'check_in_time': checkInTime,
          'updated_at': nowIso,
        },
        where: 'date = ?',
        whereArgs: [date],
      );
    }
  }

  Future<int> insertOrUpdateCheckOut({
    required String date,
    required String checkOutTime,
    required String nowIso,
  }) async {
    final db = await database;
    final existing = await getRecordByDate(date);
    if (existing == null) {
      final record = AttendanceRecord(
        date: date,
        checkOutTime: checkOutTime,
        createdAt: nowIso,
        updatedAt: nowIso,
      );
      return await db.insert('attendance_records', record.toMap());
    } else {
      // If already has check-out, do not overwrite
      if (existing.hasCheckOut) {
        return existing.id ?? 0;
      }
      return await db.update(
        'attendance_records',
        {
          'check_out_time': checkOutTime,
          'updated_at': nowIso,
        },
        where: 'date = ?',
        whereArgs: [date],
      );
    }
  }

  Future<List<AttendanceRecord>> getRecordsByMonth(String yearMonth) async {
    final db = await database;
    // yearMonth is format "YYYY-MM"
    final maps = await db.query(
      'attendance_records',
      where: 'date LIKE ?',
      whereArgs: ['$yearMonth%'],
      orderBy: 'date ASC',
    );
    return maps.map((m) => AttendanceRecord.fromMap(m)).toList();
  }

  Future<List<AttendanceRecord>> getRecordsByRange(String startDate, String endDate) async {
    final db = await database;
    final maps = await db.query(
      'attendance_records',
      where: 'date >= ? AND date <= ?',
      whereArgs: [startDate, endDate],
      orderBy: 'date ASC',
    );
    return maps.map((m) => AttendanceRecord.fromMap(m)).toList();
  }

  Future<int> deleteRecordsByMonth(String yearMonth) async {
    final db = await database;
    return await db.delete(
      'attendance_records',
      where: 'date LIKE ?',
      whereArgs: ['$yearMonth%'],
    );
  }

  Future<int> deleteRecordsByRange(String startDate, String endDate) async {
    final db = await database;
    return await db.delete(
      'attendance_records',
      where: 'date >= ? AND date <= ?',
      whereArgs: [startDate, endDate],
    );
  }

  // ==================== Calendar Overrides ====================

  Future<CalendarOverride?> getOverrideByDate(String date) async {
    final db = await database;
    final maps = await db.query(
      'calendar_overrides',
      where: 'date = ?',
      whereArgs: [date],
      limit: 1,
    );
    if (maps.isNotEmpty) {
      return CalendarOverride.fromMap(maps.first);
    }
    return null;
  }

  Future<List<CalendarOverride>> getAllOverrides() async {
    final db = await database;
    final maps = await db.query('calendar_overrides', orderBy: 'date ASC');
    return maps.map((m) => CalendarOverride.fromMap(m)).toList();
  }

  Future<void> setOverride(String date, DayType type, {String? note}) async {
    final db = await database;
    if (type == DayType.defaultRule) {
      await db.delete(
        'calendar_overrides',
        where: 'date = ?',
        whereArgs: [date],
      );
    } else {
      await db.insert(
        'calendar_overrides',
        {
          'date': date,
          'day_type': type.value,
          'note': note,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
  }

  // ==================== Settings ====================

  Future<String?> getSetting(String key) async {
    final db = await database;
    final maps = await db.query(
      'settings',
      columns: ['value'],
      where: 'key = ?',
      whereArgs: [key],
      limit: 1,
    );
    if (maps.isNotEmpty) {
      return maps.first['value'] as String;
    }
    return null;
  }

  Future<void> setSetting(String key, String value) async {
    final db = await database;
    await db.insert(
      'settings',
      {'key': key, 'value': value},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<Map<String, String>> getAllSettings() async {
    final db = await database;
    final maps = await db.query('settings');
    final Map<String, String> res = {};
    for (final row in maps) {
      res[row['key'] as String] = row['value'] as String;
    }
    return res;
  }

  Future<void> close() async {
    final db = _database;
    if (db != null) {
      await db.close();
      _database = null;
    }
  }
}
"""

with open('lib/database/database_helper.dart', 'w', encoding='utf-8') as f:
    f.write(database_code.strip() + '\n')
print('DatabaseHelper generated.')
