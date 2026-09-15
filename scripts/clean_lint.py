# 1. lib/constants/holiday_data.dart
with open('lib/constants/holiday_data.dart', 'r', encoding='utf-8') as f:
    code = f.read()
code = 'library holiday_data;\n\n' + code
with open('lib/constants/holiday_data.dart', 'w', encoding='utf-8') as f:
    f.write(code)

# 2. lib/services/notification_service.dart
with open('lib/services/notification_service.dart', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace('final now = DateTime.now();\n      // local timezone initialized', '// local timezone initialized')
with open('lib/services/notification_service.dart', 'w', encoding='utf-8') as f:
    f.write(code)

# 3. lib/screens/settings_screen.dart (context across async gap & string interpolation)
with open('lib/screens/settings_screen.dart', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace(
    "'确定要删除 ' + startStr + ' 至 ' + endStr + ' 范围内的本地打卡数据吗？\\n\\n该操作仅影响本地存储且不可撤销！'",
    "'确定要删除 \$startStr 至 \$endStr 范围内的本地打卡数据吗？\\n\\n该操作仅影响本地存储且不可撤销！'"
)
code = code.replace(
    "if (range != null) {",
    "if (range != null && mounted) {"
)
with open('lib/screens/settings_screen.dart', 'w', encoding='utf-8') as f:
    f.write(code)

# 4. lib/screens/history_screen.dart (string interpolation)
with open('lib/screens/history_screen.dart', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace(
    "'您确定要删除【' + description + '】吗？\\n\\n注意：此操作只删除手机本地数据，不可撤销！'",
    "'您确定要删除【\$description】吗？\\n\\n注意：此操作只删除手机本地数据，不可撤销！'"
)
with open('lib/screens/history_screen.dart', 'w', encoding='utf-8') as f:
    f.write(code)

# 5. lib/screens/calendar_management_dialog.dart (unnecessary_underscores)
with open('lib/screens/calendar_management_dialog.dart', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace('separatorBuilder: (_, __) => const Divider(height: 1),', 'separatorBuilder: (context, index) => const Divider(height: 1),')
with open('lib/screens/calendar_management_dialog.dart', 'w', encoding='utf-8') as f:
    f.write(code)

print('Cleaned lint issues.')
