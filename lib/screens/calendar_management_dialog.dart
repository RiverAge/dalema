import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import '../constants/app_theme.dart';
import '../models/calendar_override.dart';
import '../services/calendar_service.dart';
import '../widgets/glass_components.dart';

class CalendarManagementDialog extends StatefulWidget {
  const CalendarManagementDialog({super.key});

  @override
  State<CalendarManagementDialog> createState() =>
      _CalendarManagementDialogState();
}

class _CalendarManagementDialogState extends State<CalendarManagementDialog> {
  final CalendarService _calendarService = CalendarService();
  DateTime _selectedDate = DateTime.now();
  CalendarOverride? _currentOverride;
  List<CalendarOverride> _allOverrides = [];

  @override
  void initState() {
    super.initState();
    _loadDateInfo();
  }

  Future<void> _loadDateInfo() async {
    final override = await _calendarService.getDayOverride(_selectedDate);
    final overrides = await _calendarService.getAllOverrides();

    if (mounted) {
      setState(() {
        _currentOverride = override;
        _allOverrides = overrides;
      });
    }
  }

  Future<void> _selectDate() async {
    HapticFeedback.lightImpact();
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: AppTheme.primaryBlue,
              onPrimary: Colors.white,
              onSurface: Color(0xFF0F172A),
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() {
        _selectedDate = picked;
      });
      _loadDateInfo();
    }
  }

  void _stepDate(int days) {
    HapticFeedback.lightImpact();
    setState(() {
      _selectedDate = _selectedDate.add(Duration(days: days));
    });
    _loadDateInfo();
  }

  Future<void> _applyDayType(DayType type) async {
    HapticFeedback.mediumImpact();
    await _calendarService.setDayOverride(_selectedDate, type);
    await _loadDateInfo();
  }

  @override
  Widget build(BuildContext context) {
    final dateStr = DateFormat('yyyy年 MM月 dd日').format(_selectedDate);
    final weekdayStr = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][_selectedDate.weekday - 1];
    final currentDayType = _currentOverride?.parsedType ?? DayType.defaultRule;

    return Dialog(
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
      elevation: 12,
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 420),
        padding: const EdgeInsets.all(22),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                    // Header
                    Row(
                      children: [
                        Container(
                          width: 42,
                          height: 42,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFF38BDF8), Color(0xFF2563EB)],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(14),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF2563EB).withValues(alpha: 0.3),
                                blurRadius: 8,
                                offset: const Offset(0, 3),
                              ),
                            ],
                          ),
                          child: const Icon(Icons.edit_calendar_rounded, color: Colors.white, size: 22),
                        ),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '工作日历特殊管理',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFF0F172A),
                                ),
                              ),
                              SizedBox(height: 2),
                              Text(
                                '手动将指定日期重置为工作日或休息日',
                                style: TextStyle(fontSize: 12, color: AppTheme.slateGrey),
                              ),
                            ],
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close_rounded, color: AppTheme.slateGrey),
                          onPressed: () => Navigator.of(context).pop(),
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),

                    // Date selector bar
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF8FAFC),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFE2E8F0)),
                      ),
                      child: Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.chevron_left_rounded, size: 22),
                            color: AppTheme.slateGrey,
                            onPressed: () => _stepDate(-1),
                            tooltip: '前一天',
                          ),
                          Expanded(
                            child: InkWell(
                              onTap: _selectDate,
                              borderRadius: BorderRadius.circular(12),
                              child: Padding(
                                padding: const EdgeInsets.symmetric(vertical: 6),
                                child: Column(
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        Text(
                                          dateStr,
                                          style: const TextStyle(
                                            fontSize: 15,
                                            fontWeight: FontWeight.bold,
                                            color: Color(0xFF0F172A),
                                          ),
                                        ),
                                        const SizedBox(width: 6),
                                        Text(
                                          weekdayStr,
                                          style: const TextStyle(
                                            fontSize: 13,
                                            fontWeight: FontWeight.w600,
                                            color: AppTheme.primaryBlue,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      '当前属性：',
                                      style: const TextStyle(fontSize: 11, color: AppTheme.slateGrey),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.chevron_right_rounded, size: 22),
                            color: AppTheme.slateGrey,
                            onPressed: () => _stepDate(1),
                            tooltip: '后一天',
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 18),

                    // Rule Selector Segment
                    const Text(
                      '将该日期设定为：',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
                    ),
                    const SizedBox(height: 10),

                    Row(
                      children: [
                        Expanded(
                          child: _buildRuleButton(
                            title: '工作日',
                            subtitle: '准时提醒打卡',
                            icon: Icons.work_rounded,
                            isSelected: currentDayType == DayType.workday,
                            activeColor: AppTheme.primaryBlue,
                            onTap: () => _applyDayType(DayType.workday),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: _buildRuleButton(
                            title: '休息日',
                            subtitle: '静音不提醒',
                            icon: Icons.weekend_rounded,
                            isSelected: currentDayType == DayType.holiday,
                            activeColor: AppTheme.emeraldGreen,
                            onTap: () => _applyDayType(DayType.holiday),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: _buildRuleButton(
                            title: '默认规则',
                            subtitle: '法定/周末',
                            icon: Icons.auto_mode_rounded,
                            isSelected: currentDayType == DayType.defaultRule,
                            activeColor: const Color(0xFF64748B),
                            onTap: () => _applyDayType(DayType.defaultRule),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),

                    // Override history list
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          '已生效的特殊规则',
                          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
                        ),
                        if (_allOverrides.isNotEmpty)
                          Text(
                            '共  条设置',
                            style: const TextStyle(fontSize: 12, color: AppTheme.slateGrey),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    if (_allOverrides.isEmpty)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 20),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF8FAFC),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFE2E8F0)),
                        ),
                        child: const Column(
                          children: [
                            Icon(Icons.event_available_rounded, size: 32, color: Color(0xFF94A3B8)),
                            SizedBox(height: 6),
                            Text(
                              '暂无手动设置，目前完全遵循法定节假日与周末',
                              style: TextStyle(fontSize: 12, color: AppTheme.slateGrey),
                            ),
                          ],
                        ),
                      )
                    else
                      Container(
                        constraints: const BoxConstraints(maxHeight: 180),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF8FAFC),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFE2E8F0)),
                        ),
                        child: ListView.separated(
                          shrinkWrap: true,
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          itemCount: _allOverrides.length,
                          separatorBuilder: (context, index) => const Divider(height: 1, indent: 16, endIndent: 16),
                          itemBuilder: (context, index) {
                            final o = _allOverrides[index];
                            final isWork = o.parsedType == DayType.workday;

                            return Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                              child: Row(
                                children: [
                                  Text(
                                    o.date,
                                    style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                      color: Color(0xFF0F172A),
                                    ),
                                  ),
                                  const SizedBox(width: 10),
                                  CapsuleBadge(
                                    text: o.parsedType.label,
                                    icon: isWork ? Icons.work_outline_rounded : Icons.weekend_outlined,
                                    color: isWork ? AppTheme.primaryBlue : AppTheme.emeraldGreen,
                                    fontSize: 11,
                                  ),
                                  const Spacer(),
                                  IconButton(
                                    icon: const Icon(Icons.delete_outline_rounded, size: 18, color: AppTheme.roseRed),
                                    tooltip: '移除并恢复默认',
                                    onPressed: () async {
                                      HapticFeedback.lightImpact();
                                      final dt = DateTime.parse(o.date);
                                      await _calendarService.setDayOverride(dt, DayType.defaultRule);
                                      _loadDateInfo();
                                    },
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                      ),

                    const SizedBox(height: 22),

                    // Refined Action Button
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        GlassCapsuleButton(
                          text: '完成保存',
                          icon: Icons.check_rounded,
                          primaryColor: AppTheme.primaryBlue,
                          width: 108,
                          height: 36,
                          fontSize: 13,
                          onPressed: () => Navigator.of(context).pop(),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildRuleButton({
    required String title,
    required String subtitle,
    required IconData icon,
    required bool isSelected,
    required Color activeColor,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 6),
          decoration: BoxDecoration(
            color: isSelected ? activeColor.withValues(alpha: 0.12) : const Color(0xFFF8FAFC),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isSelected ? activeColor : const Color(0xFFE2E8F0),
              width: isSelected ? 1.8 : 1.0,
            ),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: activeColor.withValues(alpha: 0.2),
                      blurRadius: 8,
                      offset: const Offset(0, 3),
                    ),
                  ]
                : null,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 20, color: isSelected ? activeColor : const Color(0xFF64748B)),
              const SizedBox(height: 6),
              Text(
                title,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: isSelected ? activeColor : const Color(0xFF0F172A),
                ),
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: TextStyle(
                  fontSize: 9.5,
                  color: isSelected ? activeColor.withValues(alpha: 0.8) : AppTheme.slateGrey,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
