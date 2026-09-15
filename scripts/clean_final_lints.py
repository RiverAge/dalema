with open('lib/screens/settings_screen.dart', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace("    final calculatedCheckOut = _settings.getCalculatedCheckOutTimes();\n", "")
code = code.replace("    final holidayInfo = _calendarService.getCurrentYearHolidayInfo(DateTime.now().year);\n", "")
code = code.replace("activeColor: AppTheme.primaryBlue,", "activeThumbColor: AppTheme.primaryBlue,")

with open('lib/screens/settings_screen.dart', 'w', encoding='utf-8') as f:
    f.write(code)

with open('test/calendar_rules_test.dart', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace("import 'package:dalema/constants/holiday_data.dart';\n", "")
with open('test/calendar_rules_test.dart', 'w', encoding='utf-8') as f:
    f.write(code)

with open('test/service_integration_test.dart', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace("import 'package:dalema/models/app_settings.dart';\n", "")
with open('test/service_integration_test.dart', 'w', encoding='utf-8') as f:
    f.write(code)

print('Cleaned warnings in settings and tests.')
