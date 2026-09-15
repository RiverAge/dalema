import os

calendar_service_code = """import 'package:intl/intl.dart';
import '../constants/holiday_data.dart';
import '../database/database_helper.dart';
import '../models/calendar_override.dart';

enum DayCategory {
  workday,
  weekendRest,
  statutoryHoliday,
  adjustedWorkday,
  manualWorkday,
  manualHoliday,
}

extension DayCategoryExtension on DayCategory {
  bool get isWorkday =>
      this == DayCategory.workday ||
      this == DayCategory.adjustedWorkday ||
      this == DayCategory.manualWorkday;

  String get label {
    switch (this) {
      case DayCategory.workday:
        return '普通工作日';
      case DayCategory.weekendRest:
        return '周末休息';
      case DayCategory.statutoryHoliday:
        return '法定节假日';
      case DayCategory.adjustedWorkday:
        return '调休工作日';
      case DayCategory.manualWorkday:
        return '手动设为工作日';
      case DayCategory.manualHoliday:
        return '手动设为休息日';
    }
  }
}

class CalendarService {
  final DatabaseHelper _dbHelper;

  CalendarService({DatabaseHelper? dbHelper})
      : _dbHelper = dbHelper ?? DatabaseHelper.instance;

  /// Determine whether a given DateTime is a workday according to:
  /// 1. Manual user override in SQLite (calendar_overrides)
  /// 2. Statutory holidays (rest day even if Mon-Fri)
  /// 3. Adjusted workdays (work day even if Sat-Sun)
  /// 4. Default: Monday-Friday is workday, Saturday-Sunday is rest day
  Future<bool> isWorkday(DateTime date) async {
    final dateStr = DateFormat('yyyy-MM-dd').format(date);
    final category = await getDayCategory(date, dateStr: dateStr);
    return category.isWorkday;
  }

  /// Synchronous version when override is already known or passed
  bool isWorkdaySync(DateTime date, {CalendarOverride? override}) {
    final dateStr = DateFormat('yyyy-MM-dd').format(date);
    final category = getDayCategorySync(date, dateStr, override: override);
    return category.isWorkday;
  }

  Future<DayCategory> getDayCategory(DateTime date, {String? dateStr}) async {
    final formattedDate = dateStr ?? DateFormat('yyyy-MM-dd').format(date);
    final override = await _dbHelper.getOverrideByDate(formattedDate);
    return getDayCategorySync(date, formattedDate, override: override);
  }

  DayCategory getDayCategorySync(
    DateTime date,
    String dateStr, {
    CalendarOverride? override,
  }) {
    // 1. User manual override takes highest precedence
    if (override != null) {
      if (override.parsedType == DayType.workday) {
        return DayCategory.manualWorkday;
      } else if (override.parsedType == DayType.holiday) {
        return DayCategory.manualHoliday;
      }
    }

    final year = date.year;
    final holidayConfig = HolidayData.getConfigForYear(year);

    if (holidayConfig != null) {
      // 2. Statutory holiday configuration check
      if (holidayConfig.holidays.contains(dateStr)) {
        return DayCategory.statutoryHoliday;
      }
      // 3. Adjusted workday configuration check
      if (holidayConfig.workdays.contains(dateStr)) {
        return DayCategory.adjustedWorkday;
      }
    }

    // 4. Default rule: Mon(1) - Fri(5) is workday, Sat(6) - Sun(7) is rest day
    if (date.weekday >= DateTime.monday && date.weekday <= DateTime.friday) {
      return DayCategory.workday;
    } else {
      return DayCategory.weekendRest;
    }
  }

  Future<void> setDayOverride(DateTime date, DayType type, {String? note}) async {
    final dateStr = DateFormat('yyyy-MM-dd').format(date);
    await _dbHelper.setOverride(dateStr, type, note: note);
  }

  Future<CalendarOverride?> getDayOverride(DateTime date) async {
    final dateStr = DateFormat('yyyy-MM-dd').format(date);
    return await _dbHelper.getOverrideByDate(dateStr);
  }

  Future<List<CalendarOverride>> getAllOverrides() async {
    return await _dbHelper.getAllOverrides();
  }

  String getCurrentYearHolidayInfo(int year) {
    final config = HolidayData.getConfigForYear(year);
    if (config != null) {
      return '$year年已内置配置：${config.versionInfo}（法定休假${config.holidays.length}天，调休上班${config.workdays.length}天）';
    }
    return '$year年未内置节假日配置，目前按周一至周五默认工作日规则处理。支持手动在工作日历中设置。';
  }
}
"""

with open('lib/services/calendar_service.dart', 'w', encoding='utf-8') as f:
    f.write(calendar_service_code.strip() + '\n')
print('CalendarService generated.')
