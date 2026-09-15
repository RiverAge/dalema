import re

# 1. Patch history_screen.dart
with open('lib/screens/history_screen.dart', 'r', encoding='utf-8') as f:
    hist_content = f.read()

# Fix multi-line string issue
hist_content = re.sub(
    r"'您确定要删除【\$description】吗？\s*注意：此操作只删除手机本地数据，不可撤销！'",
    r"'您确定要删除【' + description + '】吗？\\n\\n注意：此操作只删除手机本地数据，不可撤销！'",
    hist_content
)

# Fix border: Border.override(...)
hist_content = hist_content.replace(
    '''border: Border.override(
                                            border: Border.all(
                                              color: item.isWorkday ? Colors.orange.shade200 : Colors.green.shade200,
                                            ),
                                          ),''',
    '''border: Border.all(
                                            color: item.isWorkday ? Colors.orange.shade200 : Colors.green.shade200,
                                          ),'''
)

# Fix deprecated surfaceVariant and withOpacity
hist_content = hist_content.replace('Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.4)', 'Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.4)')
hist_content = hist_content.replace('item.status.color.withOpacity(0.12)', 'item.status.color.withValues(alpha: 0.12)')
hist_content = hist_content.replace('separatorBuilder: (_, __) => const SizedBox(height: 8),', 'separatorBuilder: (context, index) => const SizedBox(height: 8),')

with open('lib/screens/history_screen.dart', 'w', encoding='utf-8') as f:
    f.write(hist_content)
print('history_screen patched.')

# 2. Patch settings_screen.dart
with open('lib/screens/settings_screen.dart', 'r', encoding='utf-8') as f:
    set_content = f.read()

set_content = re.sub(
    r"'确定要删除 \$startStr 至 \$endStr 范围内的本地打卡数据吗？\s*该操作仅影响本地存储且不可撤销！'",
    r"'确定要删除 ' + startStr + ' 至 ' + endStr + ' 范围内的本地打卡数据吗？\\n\\n该操作仅影响本地存储且不可撤销！'",
    set_content
)

set_content = set_content.replace('onPressed: _editCheckInTimes,', 'onTap: _editCheckInTimes,')
set_content = set_content.replace('onPressed: _editCheckOutConfig,', 'onTap: _editCheckOutConfig,')

with open('lib/screens/settings_screen.dart', 'w', encoding='utf-8') as f:
    f.write(set_content)
print('settings_screen patched.')

# 3. Patch test/widget_test.dart to smoke test DaleMaApp
test_code = """import 'package:flutter_test/flutter_test.dart';
import 'package:dalema/main.dart';

void main() {
  testWidgets('App launch smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const DaleMaApp());
    expect(find.text('今日打卡'), findsWidgets);
    expect(find.text('历史记录'), findsWidgets);
    expect(find.text('设置'), findsWidgets);
  });
}
"""
with open('test/widget_test.dart', 'w', encoding='utf-8') as f:
    f.write(test_code)
print('widget_test patched.')
