with open('lib/screens/history_screen.dart', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace(r'【\$description】', '【$description】')
with open('lib/screens/history_screen.dart', 'w', encoding='utf-8') as f:
    f.write(code)

with open('lib/constants/holiday_data.dart', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace('library holiday_data;\n\n', 'library;\n\n')
with open('lib/constants/holiday_data.dart', 'w', encoding='utf-8') as f:
    f.write(code)

print('Fixed description and library')
