widget_test_code = """import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:dalema/database/database_helper.dart';
import 'package:dalema/main.dart';

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

  testWidgets('App launch and bottom navigation smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const DaleMaApp());
    await tester.pumpAndSettle();

    expect(find.text('今日打卡'), findsWidgets);
    expect(find.text('历史记录'), findsWidgets);
    expect(find.text('设置'), findsWidgets);

    // Switch to History tab
    await tester.tap(find.text('历史记录'));
    await tester.pumpAndSettle();
    expect(find.text('按月份筛选'), findsOneWidget);

    // Switch to Settings tab
    await tester.tap(find.text('设置'));
    await tester.pumpAndSettle();
    expect(find.text('上班签到提醒'), findsOneWidget);
    expect(find.text('工作日历管理'), findsOneWidget);
  });
}
"""

with open('test/widget_test.dart', 'w', encoding='utf-8') as f:
    f.write(widget_test_code.strip() + '\n')
print('test/widget_test.dart updated.')
