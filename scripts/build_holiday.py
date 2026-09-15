import os

holiday_code = """/// Chinese Statutory Holiday & Adjusted Workday Configuration
/// Built-in data configuration for 2025 and 2026.
/// Data is cleanly decoupled and easily maintained.

class HolidayConfig {
  final int year;
  final String versionInfo;
  /// Dates that are statutory holidays (rest day even if Mon-Fri)
  /// Format: 'YYYY-MM-DD'
  final Set<String> holidays;
  /// Dates that are adjusted workdays (work day even if Sat-Sun)
  /// Format: 'YYYY-MM-DD'
  final Set<String> workdays;

  const HolidayConfig({
    required this.year,
    required this.versionInfo,
    required this.holidays,
    required this.workdays,
  });
}

class HolidayData {
  /// 2025 China Statutory Holiday Configuration
  static const HolidayConfig config2025 = HolidayConfig(
    year: 2025,
    versionInfo: '2025年国务院办公厅节假日安排',
    holidays: {
      // 元旦: 1月1日
      '2025-01-01',
      // 春节: 1月28日至2月4日
      '2025-01-28', '2025-01-29', '2025-01-30', '2025-01-31',
      '2025-02-01', '2025-02-02', '2025-02-03', '2025-02-04',
      // 清明节: 4月4日至4月6日
      '2025-04-04', '2025-04-05', '2025-04-06',
      // 劳动节: 5月1日至5月5日
      '2025-05-01', '2025-05-02', '2025-05-03', '2025-05-04', '2025-05-05',
      // 端午节: 5月31日至6月2日
      '2025-05-31', '2025-06-01', '2025-06-02',
      // 中秋节、国庆节: 10月1日至10月8日
      '2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04',
      '2025-10-05', '2025-10-06', '2025-10-07', '2025-10-08',
    },
    workdays: {
      // 春节调休
      '2025-01-26', '2025-02-08',
      // 劳动节调休
      '2025-04-27',
      // 国庆节调休
      '2025-09-28', '2025-10-11',
    },
  );

  /// 2026 China Statutory Holiday Configuration (Official standard schedule)
  static const HolidayConfig config2026 = HolidayConfig(
    year: 2026,
    versionInfo: '2026年法定节假日配置标准',
    holidays: {
      // 元旦: 1月1日至1月3日
      '2026-01-01', '2026-01-02', '2026-01-03',
      // 春节: 2月16日至2月22日
      '2026-02-16', '2026-02-17', '2026-02-18', '2026-02-19',
      '2026-02-20', '2026-02-21', '2026-02-22',
      // 清明节: 4月4日至4月6日
      '2026-04-04', '2026-04-05', '2026-04-06',
      // 劳动节: 5月1日至5月5日
      '2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05',
      // 端午节: 6月19日至6月21日
      '2026-06-19', '2026-06-20', '2026-06-21',
      // 中秋节: 9月25日至9月27日
      '2026-09-25', '2026-09-26', '2026-09-27',
      // 国庆节: 10月1日至10月7日
      '2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04',
      '2026-10-05', '2026-10-06', '2026-10-07',
    },
    workdays: {
      // 元旦调休
      '2026-01-04',
      // 春节调休
      '2026-02-15', '2026-02-28',
      // 劳动节调休
      '2026-04-26', '2026-05-09',
      // 国庆节调休
      '2026-09-20', '2026-10-10',
    },
  );

  static final Map<int, HolidayConfig> _configs = {
    2025: config2025,
    2026: config2026,
  };

  static HolidayConfig? getConfigForYear(int year) {
    return _configs[year];
  }

  static String getAvailableYearsInfo() {
    return _configs.keys.map((y) => '$y年 (${_configs[y]!.versionInfo})').join(', ');
  }
}
"""

with open('lib/constants/holiday_data.dart', 'w', encoding='utf-8') as f:
    f.write(holiday_code.strip() + '\n')
print('HolidayData generated.')
