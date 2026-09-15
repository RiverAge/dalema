import os

test_code = """import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:dalema/database/database_helper.dart';
import 'package:dalema/screens/today_screen.dart';
import 'package:dalema/screens/history_screen.dart';
import 'package:dalema/screens/settings_screen.dart';
import 'package:dalema/main.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  late Database db;

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
  });

  tearDown(() async {
    await db.close();
  });

  testWidgets('1. TodayScreen builds and displays components', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: TodayScreen()));
    // Let async _loadTodayData complete
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('今日打卡'), findsOneWidget);
    // Button or card title
    expect(find.text('上班签到'), findsWidgets);
    expect(find.text('下班签退'), findsWidgets);
  });

  testWidgets('2. HistoryScreen builds and displays components', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: HistoryScreen()));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('历史记录'), findsOneWidget);
    expect(find.text('按月份筛选'), findsOneWidget);
    expect(find.text('按日期范围筛选'), findsOneWidget);
  });

  testWidgets('3. SettingsScreen builds and displays components', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: SettingsScreen()));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('设置'), findsOneWidget);
    expect(find.text('应用全局通知'), findsOneWidget);
    expect(find.text('工作日历管理'), findsOneWidget);
    expect(find.text('恢复默认提醒配置'), findsOneWidget);
  });

  testWidgets('4. Full Navigation App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const DaleMaApp());
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('今日打卡'), findsWidgets);
    expect(find.text('历史记录'), findsWidgets);
    expect(find.text('设置'), findsWidgets);
  });
}
"""

with open('test/widget_test.dart', 'w', encoding='utf-8') as f:
    f.write(test_code.strip() + '\n')
print('test/widget_test.dart generated.')
