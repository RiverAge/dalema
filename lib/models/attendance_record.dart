class AttendanceRecord {
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
