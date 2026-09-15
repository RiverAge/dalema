import os

files = {
    'lib/models/attendance_record.dart': """class AttendanceRecord {
  final int? id;
  final String date; // YYYY-MM-DD
  final String? checkInTime; // ISO 8601 string in local time
  final String? checkOutTime; // ISO 8601 string in local time
  final String createdAt;
  final String updatedAt;

  const AttendanceRecord({
    this.id,
    required this.date,
    this.checkInTime,
    this.checkOutTime,
    required this.createdAt,
    required this.updatedAt,
  });

  bool get hasCheckIn => checkInTime != null && checkInTime!.isNotEmpty;
  bool get hasCheckOut => checkOutTime != null && checkOutTime!.isNotEmpty;

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'date': date,
      'check_in_time': checkInTime,
      'check_out_time': checkOutTime,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }

  factory AttendanceRecord.fromMap(Map<String, dynamic> map) {
    return AttendanceRecord(
      id: map['id'] as int?,
      date: map['date'] as String,
      checkInTime: map['check_in_time'] as String?,
      checkOutTime: map['check_out_time'] as String?,
      createdAt: map['created_at'] as String,
      updatedAt: map['updated_at'] as String,
    );
  }

  AttendanceRecord copyWith({
    int? id,
    String? date,
    String? checkInTime,
    String? checkOutTime,
    String? createdAt,
    String? updatedAt,
  }) {
    return AttendanceRecord(
      id: id ?? this.id,
      date: date ?? this.date,
      checkInTime: checkInTime ?? this.checkInTime,
      checkOutTime: checkOutTime ?? this.checkOutTime,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}
""",
    'lib/models/calendar_override.dart': """enum DayType {
  workday,
  holiday,
  defaultRule,
}

extension DayTypeExtension on DayType {
  String get value {
    switch (this) {
      case DayType.workday:
        return 'workday';
      case DayType.holiday:
        return 'holiday';
      case DayType.defaultRule:
        return 'default';
    }
  }

  String get label {
    switch (this) {
      case DayType.workday:
        return '工作日';
      case DayType.holiday:
        return '休息日';
      case DayType.defaultRule:
        return '使用默认规则';
    }
  }

  static DayType fromString(String str) {
    switch (str.toLowerCase()) {
      case 'workday':
        return DayType.workday;
      case 'holiday':
        return DayType.holiday;
      case 'default':
      default:
        return DayType.defaultRule;
    }
  }
}

class CalendarOverride {
  final int? id;
  final String date; // YYYY-MM-DD
  final String dayType; // 'workday' | 'holiday' | 'default'
  final String? note;

  const CalendarOverride({
    this.id,
    required this.date,
    required this.dayType,
    this.note,
  });

  DayType get parsedType => DayTypeExtension.fromString(dayType);

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'date': date,
      'day_type': dayType,
      'note': note,
    };
  }

  factory CalendarOverride.fromMap(Map<String, dynamic> map) {
    return CalendarOverride(
      id: map['id'] as int?,
      date: map['date'] as String,
      dayType: map['day_type'] as String,
      note: map['note'] as String?,
    );
  }
}
""",
    'lib/models/app_settings.dart': """class AppSettings {
  final bool checkInEnabled;
  final bool checkOutEnabled;
  final bool notificationEnabled;
  final bool soundEnabled;
  final bool vibrationEnabled;

  // Check in times: list of HH:mm
  final List<String> checkInTimes;

  // Check out times config: start HH:mm, end HH:mm, intervalMinutes
  final String checkOutStartTime;
  final String checkOutEndTime;
  final int checkOutIntervalMinutes;

  const AppSettings({
    this.checkInEnabled = true,
    this.checkOutEnabled = true,
    this.notificationEnabled = true,
    this.soundEnabled = true,
    this.vibrationEnabled = true,
    this.checkInTimes = const ['08:10', '08:16', '08:22', '08:28'],
    this.checkOutStartTime = '18:05',
    this.checkOutEndTime = '19:30',
    this.checkOutIntervalMinutes = 15,
  });

  List<String> getCalculatedCheckOutTimes() {
    final startParts = checkOutStartTime.split(':').map(int.parse).toList();
    final endParts = checkOutEndTime.split(':').map(int.parse).toList();
    final startMins = startParts[0] * 60 + startParts[1];
    final endMins = endParts[0] * 60 + endParts[1];

    if (startMins > endMins || checkOutIntervalMinutes <= 0) {
      return [checkOutStartTime];
    }

    final List<String> times = [];
    int current = startMins;
    while (current < endMins) {
      final h = (current ~/ 60).toString().padLeft(2, '0');
      final m = (current % 60).toString().padLeft(2, '0');
      times.add('$h:$m');
      current += checkOutIntervalMinutes;
    }
    final endH = (endMins ~/ 60).toString().padLeft(2, '0');
    final endM = (endMins % 60).toString().padLeft(2, '0');
    final endStr = '$endH:$endM';
    if (times.isEmpty || times.last != endStr) {
      times.add(endStr);
    }
    return times;
  }

  AppSettings copyWith({
    bool? checkInEnabled,
    bool? checkOutEnabled,
    bool? notificationEnabled,
    bool? soundEnabled,
    bool? vibrationEnabled,
    List<String>? checkInTimes,
    String? checkOutStartTime,
    String? checkOutEndTime,
    int? checkOutIntervalMinutes,
  }) {
    return AppSettings(
      checkInEnabled: checkInEnabled ?? this.checkInEnabled,
      checkOutEnabled: checkOutEnabled ?? this.checkOutEnabled,
      notificationEnabled: notificationEnabled ?? this.notificationEnabled,
      soundEnabled: soundEnabled ?? this.soundEnabled,
      vibrationEnabled: vibrationEnabled ?? this.vibrationEnabled,
      checkInTimes: checkInTimes ?? this.checkInTimes,
      checkOutStartTime: checkOutStartTime ?? this.checkOutStartTime,
      checkOutEndTime: checkOutEndTime ?? this.checkOutEndTime,
      checkOutIntervalMinutes: checkOutIntervalMinutes ?? this.checkOutIntervalMinutes,
    );
  }
}
"""
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
print('Generated models successfully.')
