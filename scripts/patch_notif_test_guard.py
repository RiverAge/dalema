with open('lib/services/notification_service.dart', 'r', encoding='utf-8') as f:
    code = f.read()

# Add test mode guard to avoid invoking platform channels in unit/widget test environments
guard = """  Future<void> rescheduleAllNotifications() async {
    // In headless test environments or platforms without notification plugin initialized, skip
    if (Platform.environment.containsKey('FLUTTER_TEST')) {
      return;
    }
"""
code = code.replace("  Future<void> rescheduleAllNotifications() async {\n", guard)

cancel_guard = """  Future<void> cancelTodayCheckInNotifications() async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) return;
"""
code = code.replace("  Future<void> cancelTodayCheckInNotifications() async {\n", cancel_guard)

cancel_out_guard = """  Future<void> cancelTodayCheckOutNotifications() async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) return;
"""
code = code.replace("  Future<void> cancelTodayCheckOutNotifications() async {\n", cancel_out_guard)

with open('lib/services/notification_service.dart', 'w', encoding='utf-8') as f:
    f.write(code)
print('notification_service updated with test environment guards.')
