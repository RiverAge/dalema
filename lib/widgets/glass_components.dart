import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
    final cardBorderRadius = BorderRadius.circular(borderRadius);

    return Container(
      decoration: BoxDecoration(
        borderRadius: cardBorderRadius,
        boxShadow: shadows ?? AppTheme.softShadow(),
      ),
      child: ClipRRect(
        borderRadius: cardBorderRadius,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color: backgroundColor ?? Colors.white.withValues(alpha: 0.85),
              borderRadius: cardBorderRadius,
              border: border ??
                  Border.all(
                    color: Colors.white.withValues(alpha: 0.9),
                    width: 1.5,
                  ),
            ),
            child: Material(
              type: MaterialType.transparency,
              child: child,
            ),
          ),
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

class CapsuleSwitch extends StatelessWidget {
  final bool value;
  final ValueChanged<bool> onChanged;
  final Color activeColor;
  final Color inactiveColor;

  const CapsuleSwitch({
    super.key,
    required this.value,
    required this.onChanged,
    this.activeColor = AppTheme.primaryBlue,
    this.inactiveColor = const Color(0xFFCBD5E1),
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        HapticFeedback.lightImpact();
        onChanged(!value);
      },
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOutCubic,
        width: 52,
        height: 30,
        padding: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          gradient: value
              ? LinearGradient(
                  colors: [activeColor, activeColor.withValues(alpha: 0.85)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : null,
          color: value ? null : const Color(0xFFE2E8F0),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: value
                ? Colors.white.withValues(alpha: 0.4)
                : const Color(0xFFCBD5E1),
            width: 1.2,
          ),
          boxShadow: value
              ? [
                  BoxShadow(
                    color: activeColor.withValues(alpha: 0.35),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: AnimatedAlign(
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOutCubic,
          alignment: value ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF0F172A).withValues(alpha: 0.18),
                  blurRadius: 5,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class CapsuleActionButton extends StatelessWidget {
  final String text;
  final IconData? icon;
  final VoidCallback? onPressed;
  final bool isLoading;
  final Color primaryColor;
  final Color? secondaryColor;
  final bool isFullWidth;
  final double? height;
  final double fontSize;

  const CapsuleActionButton({
    super.key,
    required this.text,
    this.icon,
    this.onPressed,
    this.isLoading = false,
    this.primaryColor = AppTheme.primaryBlue,
    this.secondaryColor,
    this.isFullWidth = false,
    this.height,
    this.fontSize = 13,
  });

  @override
  Widget build(BuildContext context) {
    final startColor = primaryColor;
    final endColor = secondaryColor ?? primaryColor.withValues(alpha: 0.85);
    final buttonHeight = height ?? (isFullWidth ? 48.0 : null);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: isLoading || onPressed == null
            ? null
            : () {
                HapticFeedback.lightImpact();
                onPressed!();
              },
        borderRadius: BorderRadius.circular(isFullWidth ? 16 : 20),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: isFullWidth ? double.infinity : null,
          height: buttonHeight,
          alignment: Alignment.center,
          padding: EdgeInsets.symmetric(
            horizontal: isFullWidth ? 16 : 14,
            vertical: isFullWidth ? 0 : 7,
          ),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [startColor, endColor],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(isFullWidth ? 16 : 20),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.6),
              width: 1,
            ),
            boxShadow: [
              BoxShadow(
                color: startColor.withValues(alpha: 0.35),
                blurRadius: 8,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: Row(
            mainAxisSize: isFullWidth ? MainAxisSize.max : MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              if (isLoading) ...[
                const SizedBox(
                  width: 15,
                  height: 15,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '处理中',
                  style: TextStyle(
                    fontSize: fontSize,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ] else ...[
                if (icon != null) ...[
                  Icon(icon, size: fontSize + 3, color: Colors.white),
                  const SizedBox(width: 6),
                ],
                Text(
                  text,
                  style: TextStyle(
                    fontSize: fontSize,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    letterSpacing: 0.3,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class GlassCapsuleButton extends StatefulWidget {
  final String text;
  final IconData? icon;
  final VoidCallback? onPressed;
  final bool isSecondary;
  final Color primaryColor;
  final Color? secondaryColor;
  final double? width;
  final double height;
  final double fontSize;
  final bool isLoading;

  const GlassCapsuleButton({
    super.key,
    required this.text,
    this.icon,
    this.onPressed,
    this.isSecondary = false,
    this.primaryColor = AppTheme.primaryBlue,
    this.secondaryColor,
    this.width,
    this.height = 40.0,
    this.fontSize = 13.5,
    this.isLoading = false,
  });

  @override
  State<GlassCapsuleButton> createState() => _GlassCapsuleButtonState();
}

class _GlassCapsuleButtonState extends State<GlassCapsuleButton> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    final startColor = widget.primaryColor;
    final endColor = widget.secondaryColor ?? widget.primaryColor.withValues(alpha: 0.85);
    final borderRadius = BorderRadius.circular(widget.height / 2);

    return GestureDetector(
      onTapDown: widget.onPressed == null || widget.isLoading ? null : (_) => setState(() => _isPressed = true),
      onTapUp: widget.onPressed == null || widget.isLoading
          ? null
          : (_) {
              setState(() => _isPressed = false);
              HapticFeedback.lightImpact();
              widget.onPressed!();
            },
      onTapCancel: () => setState(() => _isPressed = false),
      child: AnimatedScale(
        scale: _isPressed ? 0.95 : 1.0,
        duration: const Duration(milliseconds: 120),
        curve: Curves.easeOutCubic,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          width: widget.width,
          height: widget.height,
          alignment: Alignment.center,
          padding: EdgeInsets.symmetric(horizontal: widget.width != null ? 8 : 16),
          decoration: widget.isSecondary
              ? BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: borderRadius,
                  border: Border.all(
                    color: const Color(0xFFE2E8F0),
                    width: 1.2,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF0F172A).withValues(alpha: 0.04),
                      blurRadius: 6,
                      offset: const Offset(0, 2),
                    ),
                  ],
                )
              : BoxDecoration(
                  gradient: LinearGradient(
                    colors: [startColor, endColor],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: borderRadius,
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.45),
                    width: 1.2,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: startColor.withValues(alpha: 0.38),
                      blurRadius: 14,
                      offset: const Offset(0, 5),
                    ),
                    BoxShadow(
                      color: const Color(0xFF0F172A).withValues(alpha: 0.06),
                      blurRadius: 4,
                      offset: const Offset(0, 1),
                    ),
                  ],
                ),
          child: Row(
            mainAxisSize: widget.width != null ? MainAxisSize.max : MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              if (widget.isLoading) ...[
                SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: widget.isSecondary ? const Color(0xFF64748B) : Colors.white,
                  ),
                ),
                const SizedBox(width: 8),
              ] else if (widget.icon != null) ...[
                Icon(
                  widget.icon,
                  size: widget.fontSize + 3,
                  color: widget.isSecondary ? const Color(0xFF64748B) : Colors.white,
                ),
                const SizedBox(width: 6),
              ],
              Text(
                widget.text,
                style: TextStyle(
                  fontSize: widget.fontSize,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.3,
                  color: widget.isSecondary ? const Color(0xFF475569) : Colors.white,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Ultra-smooth dialog popup with cubic scale and fade transition
Future<T?> showSmoothDialog<T>({
  required BuildContext context,
  required WidgetBuilder builder,
  bool barrierDismissible = true,
  Color barrierColor = const Color(0x660F172A),
}) {
  return showGeneralDialog<T>(
    context: context,
    barrierDismissible: barrierDismissible,
    barrierLabel: 'Dismiss',
    barrierColor: barrierColor,
    transitionDuration: const Duration(milliseconds: 220),
    pageBuilder: (ctx, anim, secAnim) => builder(ctx),
    transitionBuilder: (ctx, anim, secAnim, child) {
      final curvedAnim = CurvedAnimation(
        parent: anim,
        curve: Curves.easeOutCubic,
        reverseCurve: Curves.easeInCubic,
      );
      return FadeTransition(
        opacity: curvedAnim,
        child: ScaleTransition(
          scale: Tween<double>(begin: 0.90, end: 1.0).animate(curvedAnim),
          child: child,
        ),
      );
    },
  );
}

