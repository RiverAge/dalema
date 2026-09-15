with open('lib/services/calendar_service.dart', 'r', encoding='utf-8') as f:
    code = f.read()

# Add HolidaySyncService import
code = "import 'holiday_sync_service.dart';\n" + code

# Modify CalendarService constructor to optionally load cached synced config
constructor = """class CalendarService {
  final DatabaseHelper _dbHelper;
  final HolidaySyncService _holidaySyncService;

  CalendarService({DatabaseHelper? dbHelper, HolidaySyncService? holidaySyncService})
      : _dbHelper = dbHelper ?? DatabaseHelper.instance,
        _holidaySyncService = holidaySyncService ?? HolidaySyncService();
"""
code = code.replace("""class CalendarService {
  final DatabaseHelper _dbHelper;

  CalendarService({DatabaseHelper? dbHelper})
      : _dbHelper = dbHelper ?? DatabaseHelper.instance;
""", constructor)

# In getDayCategory, load any locally saved synced holiday config if not already in HolidayData
hook = """  Future<DayCategory> getDayCategory(DateTime date, {String? dateStr}) async {
    final formattedDate = dateStr ?? DateFormat('yyyy-MM-dd').format(date);
    // Check if we have locally cached synced holiday config for this year
    final cached = await _holidaySyncService.getLocalSyncedConfig(date.year);
    if (cached != null) {
      HolidayData.updateConfigForYear(cached);
    }
    final override = await _dbHelper.getOverrideByDate(formattedDate);
    return getDayCategorySync(date, formattedDate, override: override);
  }
"""
code = code.replace("""  Future<DayCategory> getDayCategory(DateTime date, {String? dateStr}) async {
    final formattedDate = dateStr ?? DateFormat('yyyy-MM-dd').format(date);
    final override = await _dbHelper.getOverrideByDate(formattedDate);
    return getDayCategorySync(date, formattedDate, override: override);
  }
""", hook)

with open('lib/services/calendar_service.dart', 'w', encoding='utf-8') as f:
    f.write(code)

print('CalendarService updated to auto-load synced holidays from local storage.')
