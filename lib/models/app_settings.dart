class AppSettings {
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
