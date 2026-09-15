enum DayType {
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
