# Let us run a targeted probe to understand what is hanging
import os

probe_test = """import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:dalema/database/database_helper.dart';
import 'package:dalema/screens/today_screen.dart';
import 'package:dalema/screens/history_screen.dart';
import 'package:dalema/screens/settings_screen.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  setUp(() async {
    final db = await databaseFactory.openDatabase(inMemoryDatabasePath);
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
  });

  testWidgets('TodayScreen builds and loads', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: TodayScreen()));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.text('今日打卡'), findsOneWidget);
    expect(find.text('上班签到'), findsOneWidget);
    expect(find.text('下班签退'), findsOneWidget);
  });

  testWidgets('HistoryScreen builds and loads', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: HistoryScreen()));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.text('历史记录'), findsOneWidget);
    expect(find.text('按月份筛选'), findsOneWidget);
  });

  testWidgets('SettingsScreen builds and loads', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: SettingsScreen()));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.text('设置'), findsOneWidget);
    expect(find.text('应用全局通知'), findsOneWidget);
  });
}
"""

with open('test/widget_test.dart', 'w', encoding='utf-8') as f:
    f.write(probe_test.strip() + '\n')
print('Probing test written.')
