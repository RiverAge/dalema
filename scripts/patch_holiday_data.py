with open('lib/constants/holiday_data.dart', 'r', encoding='utf-8') as f:
    code = f.read()

# Add method to dynamically update config from network
update_method = """  static void updateConfigForYear(HolidayConfig config) {
    _configs[config.year] = config;
  }
"""

if 'updateConfigForYear' not in code:
    code = code.replace("  static HolidayConfig? getConfigForYear(int year) {", update_method + "\n  static HolidayConfig? getConfigForYear(int year) {")

with open('lib/constants/holiday_data.dart', 'w', encoding='utf-8') as f:
    f.write(code)

print('HolidayData updateConfigForYear added.')
