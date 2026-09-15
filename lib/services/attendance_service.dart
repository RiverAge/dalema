import 'package:intl/intl.dart';
import '../database/database_helper.dart';
import '../models/attendance_record.dart';
import 'notification_service.dart';

class AttendanceService {
  final DatabaseHelper _dbHelper;
  final NotificationService _notificationService;

  AttendanceService({
    DatabaseHelper? dbHelper,
    NotificationService? notificationService,
  })  : _dbHelper = dbHelper ?? DatabaseHelper.instance,
        _notificationService = notificationService ?? NotificationService.instance;

  String getTodayDateString([DateTime? date]) {
    final d = date ?? DateTime.now();
    return DateFormat('yyyy-MM-dd').format(d);
  }

  String getCurrentTimeString([DateTime? date]) {
    final d = date ?? DateTime.now();
    return DateFormat('HH:mm:ss').format(d);
  }

  Future<AttendanceRecord?> getTodayRecord([DateTime? date]) async {
    final dateStr = getTodayDateString(date);
    return await _dbHelper.getRecordByDate(dateStr);
  }

  /// Perform Check In for today
  /// Returns: updated AttendanceRecord, or throws exception if already checked in
  Future<AttendanceRecord> checkIn({DateTime? customNow}) async {
    final now = customNow ?? DateTime.now();
    final dateStr = getTodayDateString(now);
    final timeStr = getCurrentTimeString(now);
    final nowIso = now.toIso8601String();

    final existing = await _dbHelper.getRecordByDate(dateStr);
    if (existing != null && existing.hasCheckIn) {
      throw StateError('今日已完成上班签到，不可重复签到！');
    }

    await _dbHelper.insertOrUpdateCheckIn(
      date: dateStr,
      checkInTime: timeStr,
      nowIso: nowIso,
    );

    // Cancel remaining check-in notifications for today
    try {
      await _notificationService.cancelTodayCheckInNotifications();
    } catch (_) {}

    final updated = await _dbHelper.getRecordByDate(dateStr);
    return updated!;
  }

  /// Perform Check Out for today
  /// Returns: updated AttendanceRecord, or throws exception if already checked out
  Future<AttendanceRecord> checkOut({DateTime? customNow}) async {
    final now = customNow ?? DateTime.now();
    final dateStr = getTodayDateString(now);
    final timeStr = getCurrentTimeString(now);
    final nowIso = now.toIso8601String();

    final existing = await _dbHelper.getRecordByDate(dateStr);
    if (existing != null && existing.hasCheckOut) {
      throw StateError('今日已完成下班签退，不可重复签退！');
    }

    await _dbHelper.insertOrUpdateCheckOut(
      date: dateStr,
      checkOutTime: timeStr,
      nowIso: nowIso,
    );

    // Cancel remaining check-out notifications for today
    try {
      await _notificationService.cancelTodayCheckOutNotifications();
    } catch (_) {}

    final updated = await _dbHelper.getRecordByDate(dateStr);
    return updated!;
  }

  Future<List<AttendanceRecord>> getRecordsByMonth(String yearMonth) async {
    return await _dbHelper.getRecordsByMonth(yearMonth);
  }

  Future<List<AttendanceRecord>> getRecordsByRange(String startDate, String endDate) async {
    return await _dbHelper.getRecordsByRange(startDate, endDate);
  }

  Future<int> deleteRecordsByMonth(String yearMonth) async {
    return await _dbHelper.deleteRecordsByMonth(yearMonth);
  }

  Future<int> deleteRecordsByRange(String startDate, String endDate) async {
    return await _dbHelper.deleteRecordsByRange(startDate, endDate);
  }
}
