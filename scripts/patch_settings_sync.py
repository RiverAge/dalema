with open('lib/screens/settings_screen.dart', 'r', encoding='utf-8') as f:
    code = f.read()

# Add HolidaySyncService import
code = "import '../services/holiday_sync_service.dart';\n" + code

# Add field inside _SettingsScreenState
code = code.replace(
    "  final AttendanceService _attendanceService = AttendanceService();",
    "  final AttendanceService _attendanceService = AttendanceService();\n  final HolidaySyncService _holidaySyncService = HolidaySyncService();\n  bool _isSyncingHolidays = false;\n  String? _lastSyncTimeInfo;"
)

# Add method _syncOnlineHolidays
sync_method = """  Future<void> _syncOnlineHolidays() async {
    setState(() => _isSyncingHolidays = true);
    final currentYear = DateTime.now().year;
    try {
      final config = await _holidaySyncService.syncHolidaysForYear(currentYear);
      if (config != null) {
        // Update in-memory configuration
        HolidayData.updateConfigForYear(config);
        // Refresh local notifications
        await _notificationService.rescheduleAllNotifications();

        final timeStr = DateFormat('yyyy-MM-dd HH:mm').format(DateTime.now());
        if (mounted) {
          setState(() {
            _lastSyncTimeInfo = timeStr;
            _isSyncingHolidays = false;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('成功联网同步 $currentYear 年法定节假日及调休安排！'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else {
        if (mounted) {
          setState(() => _isSyncingHolidays = false);
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('当前无网络连接或无法访问同步接口，已使用手机本地内置节假日数据。'),
              backgroundColor: Colors.orange,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSyncingHolidays = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('同步失败: $e，已恢复本地内置数据'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
"""

code = code.replace("  Future<void> _openCalendarManagement() async {", sync_method + "\n  Future<void> _openCalendarManagement() async {")

# Add Sync Tile before Calendar Management
sync_tile = """          ListTile(
            leading: _isSyncingHolidays
                ? const SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.cloud_sync, color: Colors.blue),
            title: const Text('联网同步法定节假日'),
            subtitle: Text(
              _lastSyncTimeInfo != null
                  ? '上次同步：$_lastSyncTimeInfo（国务院办公厅权威数据）'
                  : '一键拉取国务院办公厅官方最新休假与调休补班通告',
            ),
            trailing: OutlinedButton(
              onPressed: _isSyncingHolidays ? null : _syncOnlineHolidays,
              child: const Text('同步'),
            ),
          ),
"""

code = code.replace("          ListTile(\n            leading: const Icon(Icons.edit_calendar),", sync_tile + "          ListTile(\n            leading: const Icon(Icons.edit_calendar),")

with open('lib/screens/settings_screen.dart', 'w', encoding='utf-8') as f:
    f.write(code)

print('settings_screen updated with holiday sync tile.')
