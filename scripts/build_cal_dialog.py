import os

cal_dialog_code = """import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/calendar_override.dart';
import '../services/calendar_service.dart';

class CalendarManagementDialog extends StatefulWidget {
  const CalendarManagementDialog({super.key});

  @override
  State<CalendarManagementDialog> createState() =>
      _CalendarManagementDialogState();
}

class _CalendarManagementDialogState extends State<CalendarManagementDialog> {
  final CalendarService _calendarService = CalendarService();
  DateTime _selectedDate = DateTime.now();
  DayCategory _currentCategory = DayCategory.workday;
  CalendarOverride? _currentOverride;
  List<CalendarOverride> _allOverrides = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDateInfo();
  }

  Future<void> _loadDateInfo() async {
    setState(() => _isLoading = true);
    final override = await _calendarService.getDayOverride(_selectedDate);
    final cat = await _calendarService.getDayCategory(_selectedDate);
    final overrides = await _calendarService.getAllOverrides();

    if (mounted) {
      setState(() {
        _currentOverride = override;
        _currentCategory = cat;
        _allOverrides = overrides;
        _isLoading = false;
      });
    }
  }

  Future<void> _selectDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
    );
    if (picked != null) {
      setState(() {
        _selectedDate = picked;
      });
      _loadDateInfo();
    }
  }

  Future<void> _applyDayType(DayType type) async {
    await _calendarService.setDayOverride(_selectedDate, type);
    await _loadDateInfo();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('已将 ${DateFormat('yyyy-MM-dd').format(_selectedDate)} 设置为：${type.label}'),
          backgroundColor: Colors.green,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);

    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.calendar_month, color: Colors.blue),
          SizedBox(width: 8),
          Text('工作日历管理', style: TextStyle(fontSize: 18)),
        ],
      ),
      content: SizedBox(
        width: double.maxFinite,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Date Selector
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(
                        '选择日期：$dateStr',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      subtitle: Text('当前状态：${_currentCategory.label}'),
                      trailing: ElevatedButton(
                        onPressed: _selectDate,
                        child: const Text('选日期'),
                      ),
                    ),
                    const Divider(),
                    const Text(
                      '设置该日期规则：',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),

                    RadioListTile<DayType>(
                      title: const Text('工作日（提醒打卡）'),
                      value: DayType.workday,
                      groupValue: _currentOverride?.parsedType ?? DayType.defaultRule,
                      onChanged: (val) => _applyDayType(DayType.workday),
                    ),
                    RadioListTile<DayType>(
                      title: const Text('休息日（不提醒）'),
                      value: DayType.holiday,
                      groupValue: _currentOverride?.parsedType ?? DayType.defaultRule,
                      onChanged: (val) => _applyDayType(DayType.holiday),
                    ),
                    RadioListTile<DayType>(
                      title: const Text('使用默认规则（法定节假日/周末）'),
                      value: DayType.defaultRule,
                      groupValue: _currentOverride == null
                          ? DayType.defaultRule
                          : _currentOverride!.parsedType,
                      onChanged: (val) => _applyDayType(DayType.defaultRule),
                    ),

                    const Divider(),
                    const Text(
                      '已保存的手动特殊配置：',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    if (_allOverrides.isEmpty)
                      const Text(
                        '暂无手动特殊设置，当前均使用系统内置法定节假日及周末规则。',
                        style: TextStyle(fontSize: 12, color: Colors.grey),
                      )
                    else
                      Container(
                        constraints: const BoxConstraints(maxHeight: 160),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey.shade300),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: ListView.separated(
                          shrinkWrap: true,
                          itemCount: _allOverrides.length,
                          separatorBuilder: (_, __) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final o = _allOverrides[index];
                            return ListTile(
                              dense: true,
                              title: Text(o.date),
                              subtitle: Text(o.parsedType.label),
                              trailing: IconButton(
                                icon: const Icon(Icons.delete, size: 18, color: Colors.red),
                                tooltip: '恢复默认',
                                onPressed: () async {
                                  final dt = DateTime.parse(o.date);
                                  await _calendarService.setDayOverride(dt, DayType.defaultRule);
                                  _loadDateInfo();
                                },
                              ),
                            );
                          },
                        ),
                      ),
                  ],
                ),
              ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('完成'),
        ),
      ],
    );
  }
}
"""

with open('lib/screens/calendar_management_dialog.dart', 'w', encoding='utf-8') as f:
    f.write(cal_dialog_code.strip() + '\n')
print('CalendarManagementDialog generated.')
