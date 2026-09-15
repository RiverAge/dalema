import 'package:flutter/material.dart';

class AppTheme {
  // Brand Colors
  static const Color primaryBlue = Color(0xFF3B82F6);
  static const Color deepNavy = Color(0xFF0F172A);
  static const Color accentCyan = Color(0xFF06B6D4);
  static const Color emeraldGreen = Color(0xFF10B981);
  static const Color amberOrange = Color(0xFFF59E0B);
  static const Color roseRed = Color(0xFFF43F5E);
  static const Color slateGrey = Color(0xFF64748B);

  // Background Gradients
  static const LinearGradient ambientBg = LinearGradient(
    colors: [
      Color(0xFFF0F4FD),
      Color(0xFFF8FAFC),
      Color(0xFFEDF4FF),
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Soft shadows
  static List<BoxShadow> softShadow({Color? color, double blur = 20, Offset offset = const Offset(0, 8)}) {
    return [
      BoxShadow(
        color: (color ?? const Color(0xFF1E293B)).withValues(alpha: 0.07),
        blurRadius: blur,
        offset: offset,
      ),
    ];
  }

  static List<BoxShadow> glowShadow(Color color, {double blur = 18}) {
    return [
      BoxShadow(
        color: color.withValues(alpha: 0.35),
        blurRadius: blur,
        offset: const Offset(0, 6),
      ),
    ];
  }
}
