import os

glass_card_code = """import 'dart:ui';
import 'package:flutter/material.dart';
import '../constants/app_theme.dart';

class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double borderRadius;
  final Color? backgroundColor;
  final Border? border;
  final List<BoxShadow>? shadows;
  final double blur;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.borderRadius = 24,
    this.backgroundColor,
    this.border,
    this.shadows,
    this.blur = 16,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: backgroundColor ?? Colors.white.withValues(alpha: 0.82),
            borderRadius: BorderRadius.circular(borderRadius),
            border: border ??
                Border.all(
                  color: Colors.white.withValues(alpha: 0.9),
                  width: 1.5,
                ),
            boxShadow: shadows ?? AppTheme.softShadow(),
          ),
          child: child,
        ),
      ),
    );
  }
}

class CapsuleBadge extends StatelessWidget {
  final String text;
  final IconData? icon;
  final Color color;
  final Color? backgroundColor;
  final double fontSize;

  const CapsuleBadge({
    super.key,
    required this.text,
    this.icon,
    this.color = AppTheme.primaryBlue,
    this.backgroundColor,
    this.fontSize = 12,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: backgroundColor ?? color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(
          color: color.withValues(alpha: 0.25),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: fontSize + 2, color: color),
            const SizedBox(width: 4),
          ],
          Text(
            text,
            style: TextStyle(
              fontSize: fontSize,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
"""

with open('lib/widgets/glass_components.dart', 'w', encoding='utf-8') as f:
    f.write(glass_card_code.strip() + '\n')
print('glass_components written.')
