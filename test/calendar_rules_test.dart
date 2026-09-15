import 'package:flutter_test/flutter_test.dart';
import 'package:dalema/models/calendar_override.dart';
import 'package:dalema/services/calendar_service.dart';

void main() {
  group('Calendar and Workday Rules Tests', () {
    late CalendarService calendarService;

    setUp(() {
      calendarService = CalendarService();
    });

    test('1. Default Workday Rule: Mon-Fri is workday, Sat-Sun is rest day', () {
      // 2026-03-09 is Monday (ordinary workday, no holiday)
      final monday = DateTime(2026, 3, 9);
      expect(calendarService.isWorkdaySync(monday), isTrue);

      // 2026-03-14 is Saturday (ordinary weekend)
      final saturday = DateTime(2026, 3, 14);
      expect(calendarService.isWorkdaySync(saturday), isFalse);

      // 2026-03-15 is Sunday (ordinary weekend)
      final sunday = DateTime(2026, 3, 15);
      expect(calendarService.isWorkdaySync(sunday), isFalse);
    });

    test('2. Statutory Holiday Rule: Holiday on Mon-Fri should NOT be a workday', () {
      // 2026-01-01 is New Year Day (Thursday, normally a weekday)
      final newYearDay = DateTime(2026, 1, 1);
      expect(calendarService.isWorkdaySync(newYearDay), isFalse);

      final cat = calendarService.getDayCategorySync(newYearDay, '2026-01-01');
      expect(cat, equals(DayCategory.statutoryHoliday));
    });

    test('3. Adjusted Workday Rule: Compensatory workday on weekend IS a workday', () {
      // 2026-01-04 is Sunday, but an adjusted workday for New Year
      final adjustedSun = DateTime(2026, 1, 4);
      expect(calendarService.isWorkdaySync(adjustedSun), isTrue);

      final cat = calendarService.getDayCategorySync(adjustedSun, '2026-01-04');
      expect(cat, equals(DayCategory.adjustedWorkday));
    });

    test('4. Manual Override Rule: Highest priority for user manual settings', () {
      // Take 2026-03-10 (Tuesday, normally workday) and set manual holiday
      final tuesday = DateTime(2026, 3, 10);
      final overrideHoliday = const CalendarOverride(
        date: '2026-03-10',
        dayType: 'holiday',
      );
      expect(calendarService.isWorkdaySync(tuesday, override: overrideHoliday), isFalse);

      // Take 2026-03-15 (Sunday, normally rest) and set manual workday
      final sunday = DateTime(2026, 3, 15);
      final overrideWorkday = const CalendarOverride(
        date: '2026-03-15',
        dayType: 'workday',
      );
      expect(calendarService.isWorkdaySync(sunday, override: overrideWorkday), isTrue);
    });
  });
}
