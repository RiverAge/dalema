import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../constants/app_theme.dart';
import 'glass_components.dart';

Future<TimeOfDay?> showGlassTimePicker({
  required BuildContext context,
  required TimeOfDay initialTime,
  String title = '选择时间',
  String subtitle = '滑动滚轮设定24小时制时间',
  Color primaryColor = AppTheme.primaryBlue,
  List<String>? quickPresets,
}) {
  return showSmoothDialog<TimeOfDay>(
    context: context,
    barrierDismissible: true,
    builder: (ctx) => _GlassTimePickerDialog(
      initialTime: initialTime,
      title: title,
      subtitle: subtitle,
      primaryColor: primaryColor,
      quickPresets: quickPresets,
    ),
  );
}

class _GlassTimePickerDialog extends StatefulWidget {
  final TimeOfDay initialTime;
  final String title;
  final String subtitle;
  final Color primaryColor;
  final List<String>? quickPresets;

  const _GlassTimePickerDialog({
    required this.initialTime,
    required this.title,
    required this.subtitle,
    required this.primaryColor,
    this.quickPresets,
  });

  @override
  State<_GlassTimePickerDialog> createState() => _GlassTimePickerDialogState();
}

class _GlassTimePickerDialogState extends State<_GlassTimePickerDialog> {
  late FixedExtentScrollController _hourController;
  late FixedExtentScrollController _minuteController;
  late int _selectedHour;
  late int _selectedMinute;

  @override
  void initState() {
    super.initState();
    _selectedHour = widget.initialTime.hour;
    _selectedMinute = widget.initialTime.minute;
    _hourController = FixedExtentScrollController(initialItem: _selectedHour);
    _minuteController = FixedExtentScrollController(initialItem: _selectedMinute);
  }

  @override
  void dispose() {
    _hourController.dispose();
    _minuteController.dispose();
    super.dispose();
  }

  void _applyPreset(String preset) {
    HapticFeedback.lightImpact();
    final parts = preset.split(':');
    if (parts.length == 2) {
      final h = int.tryParse(parts[0]) ?? _selectedHour;
      final m = int.tryParse(parts[1]) ?? _selectedMinute;
      setState(() {
        _selectedHour = h;
        _selectedMinute = m;
      });
      _hourController.animateToItem(h, duration: const Duration(milliseconds: 250), curve: Curves.easeOutCubic);
      _minuteController.animateToItem(m, duration: const Duration(milliseconds: 250), curve: Curves.easeOutCubic);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
      insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 380),
        padding: const EdgeInsets.all(22),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        widget.primaryColor,
                        widget.primaryColor.withValues(alpha: 0.8),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(13),
                    boxShadow: [
                      BoxShadow(
                        color: widget.primaryColor.withValues(alpha: 0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: const Icon(Icons.access_time_filled_rounded, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.title,
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF0F172A),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        widget.subtitle,
                        style: const TextStyle(fontSize: 11.5, color: AppTheme.slateGrey),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded, color: AppTheme.slateGrey, size: 20),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),

            const SizedBox(height: 18),

            // Time Preview Badge
            Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                decoration: BoxDecoration(
                  color: widget.primaryColor.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: widget.primaryColor.withValues(alpha: 0.25),
                    width: 1.2,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '${_selectedHour.toString().padLeft(2, '0')}:${_selectedMinute.toString().padLeft(2, '0')}',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 2.0,
                        color: widget.primaryColor,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: widget.primaryColor.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        _selectedHour < 12 ? '上午' : '下午',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: widget.primaryColor,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Wheel Scroll Picker Container
            Container(
              height: 160,
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Stack(
                children: [
                  // Center selection indicator highlight capsule
                  Center(
                    child: Container(
                      height: 42,
                      margin: const EdgeInsets.symmetric(horizontal: 14),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: widget.primaryColor.withValues(alpha: 0.35),
                          width: 1.2,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: widget.primaryColor.withValues(alpha: 0.1),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Wheels
                  Row(
                    children: [
                      // Hours Wheel (00 - 23)
                      Expanded(
                        child: CupertinoPicker(
                          scrollController: _hourController,
                          itemExtent: 42,
                          selectionOverlay: null,
                          onSelectedItemChanged: (index) {
                            HapticFeedback.selectionClick();
                            setState(() => _selectedHour = index);
                          },
                          children: List.generate(24, (i) {
                            final isSelected = i == _selectedHour;
                            return Center(
                              child: Text(
                                '${i.toString().padLeft(2, '0')} 时',
                                style: TextStyle(
                                  fontSize: isSelected ? 19 : 15,
                                  fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                                  color: isSelected ? widget.primaryColor : const Color(0xFF94A3B8),
                                ),
                              ),
                            );
                          }),
                        ),
                      ),

                      // Colon separator
                      Text(
                        ':',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: widget.primaryColor.withValues(alpha: 0.6),
                        ),
                      ),

                      // Minutes Wheel (00 - 59)
                      Expanded(
                        child: CupertinoPicker(
                          scrollController: _minuteController,
                          itemExtent: 42,
                          selectionOverlay: null,
                          onSelectedItemChanged: (index) {
                            HapticFeedback.selectionClick();
                            setState(() => _selectedMinute = index);
                          },
                          children: List.generate(60, (i) {
                            final isSelected = i == _selectedMinute;
                            return Center(
                              child: Text(
                                '${i.toString().padLeft(2, '0')} 分',
                                style: TextStyle(
                                  fontSize: isSelected ? 19 : 15,
                                  fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                                  color: isSelected ? widget.primaryColor : const Color(0xFF94A3B8),
                                ),
                              ),
                            );
                          }),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Optional Quick Presets
            if (widget.quickPresets != null && widget.quickPresets!.isNotEmpty) ...[
              const SizedBox(height: 14),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: widget.quickPresets!.map((preset) {
                  final parts = preset.split(':');
                  final isCurrent = parts.length == 2 &&
                      int.tryParse(parts[0]) == _selectedHour &&
                      int.tryParse(parts[1]) == _selectedMinute;
                  return InkWell(
                    onTap: () => _applyPreset(preset),
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: isCurrent ? widget.primaryColor.withValues(alpha: 0.12) : const Color(0xFFF1F5F9),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: isCurrent ? widget.primaryColor : const Color(0xFFE2E8F0),
                          width: 1,
                        ),
                      ),
                      child: Text(
                        preset,
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: isCurrent ? FontWeight.bold : FontWeight.w600,
                          color: isCurrent ? widget.primaryColor : const Color(0xFF475569),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ],

            const SizedBox(height: 20),

            // Action Buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                GlassCapsuleButton(
                  text: '取消',
                  isSecondary: true,
                  width: 78,
                  height: 36,
                  fontSize: 13,
                  onPressed: () => Navigator.of(context).pop(),
                ),
                const SizedBox(width: 10),
                GlassCapsuleButton(
                  text: '确认时间',
                  icon: Icons.check_rounded,
                  primaryColor: widget.primaryColor,
                  width: 108,
                  height: 36,
                  fontSize: 13,
                  onPressed: () => Navigator.of(context).pop(TimeOfDay(hour: _selectedHour, minute: _selectedMinute)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
