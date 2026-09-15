import 'package:flutter/material.dart';
import '../constants/app_theme.dart';
import '../models/app_update_info.dart';
import '../update/update_flow_controller.dart';
import 'glass_components.dart';

class UpdateDialog extends StatefulWidget {
  final AppUpdateInfo update;
  final String? currentVersion;
  final UpdateFlowController controller;

  const UpdateDialog({
    super.key,
    required this.update,
    this.currentVersion,
    required this.controller,
  });

  static Future<void> show({
    required BuildContext context,
    required AppUpdateInfo update,
    String? currentVersion,
    UpdateFlowController? controller,
  }) {
    final ctrl = controller ?? UpdateFlowController.instance;
    return showSmoothDialog(
      context: context,
      builder: (ctx) => UpdateDialog(
        update: update,
        currentVersion: currentVersion,
        controller: ctrl,
      ),
    );
  }

  @override
  State<UpdateDialog> createState() => _UpdateDialogState();
}

class _UpdateDialogState extends State<UpdateDialog> {
  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onControllerChange);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onControllerChange);
    super.dispose();
  }

  void _onControllerChange() {
    if (mounted) setState(() {});
  }

  String _formatBytes(int bytes) {
    if (bytes <= 0) return '0B';
    const double kb = 1024;
    const double mb = kb * 1024;
    if (bytes >= mb) {
      return '${(bytes / mb).toStringAsFixed(1)} MB';
    }
    if (bytes >= kb) {
      return '${(bytes / kb).toStringAsFixed(1)} KB';
    }
    return '$bytes B';
  }

  String _formatSpeed(double bytesPerSec) {
    if (bytesPerSec <= 0) return '';
    const double kb = 1024;
    const double mb = kb * 1024;
    if (bytesPerSec >= mb) {
      return '${(bytesPerSec / mb).toStringAsFixed(1)} MB/s';
    }
    if (bytesPerSec >= kb) {
      return '${(bytesPerSec / kb).toStringAsFixed(1)} KB/s';
    }
    return '${bytesPerSec.toStringAsFixed(0)} B/s';
  }

  Future<void> _handleStartUpdate() async {
    final controller = widget.controller;
    final error = await controller.downloadAndInstall(widget.update);
    if (mounted && error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('更新失败: $error'),
          backgroundColor: AppTheme.roseRed,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Future<void> _handleInstallPending() async {
    final controller = widget.controller;
    final error = await controller.installPendingPackage();
    if (mounted && error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('安装失败: $error'),
          backgroundColor: AppTheme.roseRed,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final ctrl = widget.controller;
    final isUpdating = ctrl.isUpdating;
    final stage = ctrl.stage;

    return Dialog(
      backgroundColor: Colors.transparent,
      elevation: 0,
      insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
      child: GlassCard(
        padding: const EdgeInsets.all(22),
        borderRadius: 24,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [AppTheme.primaryBlue, AppTheme.accentCyan],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: AppTheme.glowShadow(AppTheme.primaryBlue),
                  ),
                  child: const Icon(
                    Icons.system_update_rounded,
                    color: Colors.white,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '发现新版本',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF0F172A),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          if (widget.currentVersion != null) ...[
                            Text(
                              'v${widget.currentVersion}',
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppTheme.slateGrey,
                              ),
                            ),
                            const Text(' → ', style: TextStyle(fontSize: 12, color: AppTheme.slateGrey)),
                          ],
                          Text(
                            'v${widget.update.versionName}',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.primaryBlue,
                            ),
                          ),
                          if (widget.update.fileSize > 0) ...[
                            const SizedBox(width: 8),
                            CapsuleBadge(
                              text: _formatBytes(widget.update.fileSize),
                              color: AppTheme.accentCyan,
                              fontSize: 10,
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
                if (!isUpdating)
                  IconButton(
                    icon: const Icon(Icons.close_rounded, color: AppTheme.slateGrey, size: 20),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
              ],
            ),

            const SizedBox(height: 16),

            // Changelog
            const Text(
              '更新日志',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: Color(0xFF334155),
              ),
            ),
            const SizedBox(height: 8),
            Container(
              constraints: const BoxConstraints(maxHeight: 180),
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: SingleChildScrollView(
                child: Text(
                  widget.update.changelog.isNotEmpty
                      ? widget.update.changelog
                      : '暂无详细更新日志。',
                  style: const TextStyle(
                    fontSize: 13,
                    color: Color(0xFF475569),
                    height: 1.5,
                  ),
                ),
              ),
            ),

            if (ctrl.downloadMirrorHint != null) ...[
              const SizedBox(height: 10),
              Row(
                children: [
                  const SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(strokeWidth: 1.5, color: AppTheme.amberOrange),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    ctrl.downloadMirrorHint!,
                    style: const TextStyle(fontSize: 11, color: AppTheme.amberOrange),
                  ),
                ],
              ),
            ],

            // Progress Indicator during download
            if (isUpdating && stage == UpdateUiStage.downloading) ...[
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '正在下载 (${ctrl.downloadProgressPercent.toStringAsFixed(0)}%)',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryBlue),
                  ),
                  Text(
                    '${_formatBytes(ctrl.downloadedBytes)} / ${_formatBytes(ctrl.totalBytes > 0 ? ctrl.totalBytes : widget.update.fileSize)}',
                    style: const TextStyle(fontSize: 11, color: AppTheme.slateGrey),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(999),
                child: LinearProgressIndicator(
                  minHeight: 7,
                  value: (ctrl.downloadProgressPercent / 100).clamp(0.0, 1.0),
                  backgroundColor: const Color(0xFFE2E8F0),
                  valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryBlue),
                ),
              ),
              const SizedBox(height: 4),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  if (ctrl.downloadBytesPerSecond > 0)
                    Text(
                      '下载速度: ${_formatSpeed(ctrl.downloadBytesPerSecond)}',
                      style: const TextStyle(fontSize: 11, color: AppTheme.slateGrey),
                    )
                  else
                    const SizedBox(),
                  if (ctrl.etaSeconds != null && ctrl.etaSeconds! > 0)
                    Text(
                      '预计剩余: ${ctrl.etaSeconds}s',
                      style: const TextStyle(fontSize: 11, color: AppTheme.slateGrey),
                    ),
                ],
              ),
            ],

            if (stage == UpdateUiStage.verifying) ...[
              const SizedBox(height: 14),
              const Row(
                children: [
                  SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.emeraldGreen),
                  ),
                  SizedBox(width: 8),
                  Text('正在校验安装包完整性 (SHA-256)...', style: TextStyle(fontSize: 12, color: AppTheme.emeraldGreen)),
                ],
              ),
            ],

            if (stage == UpdateUiStage.openingInstaller) ...[
              const SizedBox(height: 14),
              const Row(
                children: [
                  SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primaryBlue),
                  ),
                  SizedBox(width: 8),
                  Text('正在启动安装程序...', style: TextStyle(fontSize: 12, color: AppTheme.primaryBlue)),
                ],
              ),
            ],

            const SizedBox(height: 20),

            // Action Buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                if (!isUpdating) ...[
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('稍后再说', style: TextStyle(color: AppTheme.slateGrey)),
                  ),
                  const SizedBox(width: 8),
                ],
                if (stage == UpdateUiStage.readyToInstall) ...[
                  CapsuleActionButton(
                    text: '立即重启并安装',
                    icon: Icons.refresh_rounded,
                    primaryColor: AppTheme.emeraldGreen,
                    onPressed: _handleInstallPending,
                  ),
                ] else ...[
                  CapsuleActionButton(
                    text: isUpdating ? '正在更新...' : '立即下载并更新',
                    icon: isUpdating ? null : Icons.download_rounded,
                    isLoading: isUpdating,
                    primaryColor: AppTheme.primaryBlue,
                    secondaryColor: AppTheme.accentCyan,
                    onPressed: isUpdating ? null : _handleStartUpdate,
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}
