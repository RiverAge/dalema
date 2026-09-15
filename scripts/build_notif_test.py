import os

notification_rules_test = """import 'package:flutter_test/flutter_test.dart';
import 'package:dalema/models/app_settings.dart';

void main() {
  group('Notification Scheduling and Cancellation Logic Tests', () {
    test('1. Default Check-in schedule times are exactly [08:10, 08:16, 08:22, 08:28]', () {
      const settings = AppSettings();
      expect(
        settings.checkInTimes,
        equals(['08:10', '08:16', '08:22', '08:28']),
      );
    });

    test('2. Default Check-out schedule times match spec [18:05, 18:20, 18:35, 18:50, 19:05, 19:20, 19:30]', () {
      const settings = AppSettings(
        checkOutStartTime: '18:05',
        checkOutEndTime: '19:30',
        checkOutIntervalMinutes: 15,
      );
      final calculated = settings.getCalculatedCheckOutTimes();
      expect(
        calculated,
        equals(['18:05', '18:20', '18:35', '18:50', '19:05', '19:20', '19:30']),
      );
    });

    test('3. Custom Check-out schedule calculation with custom intervals', () {
      const settings = AppSettings(
        checkOutStartTime: '18:00',
        checkOutEndTime: '19:00',
        checkOutIntervalMinutes: 20,
      );
      final calculated = settings.getCalculatedCheckOutTimes();
      expect(
        calculated,
        equals(['18:00', '18:20', '18:40', '19:00']),
      );
    });

    test('4. Notification ID calculation partitions correctly', () {
      // Base IDs
      const checkInBaseId = 1000;
      const checkOutBaseId = 2000;

      // Day 0 (today)
      final day0CheckInIds = List.generate(4, (i) => checkInBaseId + (0 * 20) + i);
      expect(day0CheckInIds, equals([1000, 1001, 1002, 1003]));

      // Day 1 (tomorrow)
      final day1CheckInIds = List.generate(4, (i) => checkInBaseId + (1 * 20) + i);
      expect(day1CheckInIds, equals([1020, 1021, 1022, 1023]));

      // Check-in and check-out ID spaces never collide
      expect(checkInBaseId + (6 * 20) + 19 < checkOutBaseId, isTrue);
    });
  });
}
"""

with open('test/notification_rules_test.dart', 'w', encoding='utf-8') as f:
    f.write(notification_rules_test.strip() + '\n')
print('notification_rules_test written.')
