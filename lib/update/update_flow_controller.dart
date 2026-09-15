import 'package:flutter/foundation.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'app_update_service.dart';

class _DownloadProgressSnapshot {
  const _DownloadProgressSnapshot({
    required this.percent,
    required this.receivedBytes,
    required this.totalBytes,
    required this.speedBytesPerSecond,
    required this.etaSeconds,
  });

  final double percent;
  final int receivedBytes;
  final int totalBytes;
  final double speedBytesPerSecond;
  final int? etaSeconds;
}

class _DownloadProgressTracker {
  final List<({DateTime time, int bytes})> _samples = [];
  double _speedBytesPerSecond = 0;
  DateTime? _lastUiTickAt;

  static const Duration _window = Duration(seconds: 2);
  static const Duration _minSpan = Duration(milliseconds: 200);

  _DownloadProgressSnapshot? compute({
    required int received,
    required int total,
    required double progress,
    required double currentUiPercent,
  }) {
    final double percent = (progress * 100).clamp(0, 100).toDouble();
    final DateTime now = DateTime.now();
    _updateSpeed(now: now, received: received);

    final int lastIntPercent = currentUiPercent.floor();
    final int newIntPercent = percent.floor();
    final bool crossedIntPercent = newIntPercent > lastIntPercent;
    final bool shouldThrottle =
        _lastUiTickAt != null &&
        now.difference(_lastUiTickAt!).inMilliseconds < 500 &&
        !crossedIntPercent;
    if (shouldThrottle) {
      return null;
    }

    _lastUiTickAt = now;
    return _DownloadProgressSnapshot(
      percent: percent,
      receivedBytes: received,
      totalBytes: total,
      speedBytesPerSecond: _speedBytesPerSecond,
      etaSeconds: _estimateEtaSeconds(received: received, total: total),
    );
  }

  void _updateSpeed({required DateTime now, required int received}) {
    if (_samples.isNotEmpty && received < _samples.last.bytes) {
      return;
    }

    _samples.add((time: now, bytes: received));
    _evict(now);

    if (_samples.length < 2) {
      return;
    }

    final newest = _samples.last;
    final oldest = _samples.first;
    final int deltaMs = newest.time.difference(oldest.time).inMilliseconds;
    if (deltaMs < _minSpan.inMilliseconds) {
      return;
    }
    final int deltaBytes = newest.bytes - oldest.bytes;
    final double windowSpeed = deltaBytes / (deltaMs / 1000);
    if (windowSpeed < 0) {
      _speedBytesPerSecond = 0;
      return;
    }
    final double last = _speedBytesPerSecond;
    if (last > 0 && windowSpeed < last && (last - windowSpeed) / last <= 0.15) {
      return;
    }
    _speedBytesPerSecond = windowSpeed;
  }

  void _evict(DateTime now) {
    final DateTime cutoff = now.subtract(_window);
    int i = 0;
    while (i < _samples.length && _samples[i].time.isBefore(cutoff)) {
      i++;
    }
    if (i > 1) {
      _samples.removeRange(0, i - 1);
    }
  }

  int? _estimateEtaSeconds({required int received, int total = 0}) {
    if (_speedBytesPerSecond <= 0 || total <= 0) {
      return null;
    }
    final int rawEta =
        ((total - received).clamp(0, total) / _speedBytesPerSecond).ceil();
    return ((rawEta / 5).round() * 5);
  }
}

class UpdateFlowController extends ChangeNotifier {
  static final UpdateFlowController instance = UpdateFlowController();

  final AppUpdateService _service;

  UpdateFlowController({AppUpdateService? service})
      : _service = service ?? AppUpdateService();

  bool _hasChecked = false;
  bool _isChecking = false;
  bool _isUpdating = false;
  double _downloadProgressPercent = 0;
  int _downloadedBytes = 0;
  int _totalBytes = 0;
  double _downloadBytesPerSecond = 0;
  int? _etaSeconds;
  UpdateUiStage _stage = UpdateUiStage.idle;
  String? _pendingPackagePath;
  String? _pendingVersionName;
  int? _pendingVersionCode;
  AppUpdateInfo? _availableUpdate;
  String? _currentVersionName;
  int? _currentVersionCode;
  String? _checkError;
  String? _downloadMirrorHint;

  bool get hasChecked => _hasChecked;
  bool get isChecking => _isChecking;
  bool get isUpdating => _isUpdating;
  double get downloadProgressPercent => _downloadProgressPercent;
  int get downloadedBytes => _downloadedBytes;
  int get totalBytes => _totalBytes;
  double get downloadBytesPerSecond => _downloadBytesPerSecond;
  int? get etaSeconds => _etaSeconds;
  UpdateUiStage get stage => _stage;
  String? get pendingPackagePath => _pendingPackagePath;
  String? get pendingVersionName => _pendingVersionName;
  int? get pendingVersionCode => _pendingVersionCode;
  AppUpdateInfo? get availableUpdate => _availableUpdate;
  String? get currentVersionName => _currentVersionName;
  int? get currentVersionCode => _currentVersionCode;
  String? get checkError => _checkError;
  String? get downloadMirrorHint => _downloadMirrorHint;

  Future<void> initCurrentVersion() async {
    try {
      final info = await PackageInfo.fromPlatform();
      _currentVersionName = info.version;
      _currentVersionCode = int.tryParse(info.buildNumber) ?? 0;
      notifyListeners();
    } catch (_) {}
  }

  Future<AppUpdateCheckResult> checkForUpdate({bool silent = false}) async {
    _isChecking = !silent;
    _checkError = null;
    _availableUpdate = null;
    notifyListeners();

    try {
      final AppUpdateCheckResult result = await _service.checkForUpdate();
      _hasChecked = true;
      _currentVersionName = result.currentVersionName;
      _currentVersionCode = result.currentVersionCode;
      _availableUpdate = result.hasUpdate ? result.remote : null;
      _isChecking = false;
      notifyListeners();
      return result;
    } catch (err) {
      _hasChecked = true;
      _checkError = '$err';
      _availableUpdate = null;
      _isChecking = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<String?> openDownloadPage(AppUpdateInfo update) async {
    try {
      await _service.openUpdateDownloadPage(update);
      return null;
    } catch (err) {
      return '$err';
    }
  }

  Future<String?> downloadAndInstall(AppUpdateInfo update) async {
    if (_isUpdating) return 'Update is already in progress.';

    _isUpdating = true;
    _downloadProgressPercent = 0;
    _downloadedBytes = 0;
    _totalBytes = update.fileSize;
    _downloadBytesPerSecond = 0;
    _etaSeconds = null;
    _stage = UpdateUiStage.downloading;
    _pendingPackagePath = null;
    _pendingVersionName = null;
    _pendingVersionCode = null;
    _availableUpdate = update;
    _checkError = null;
    _downloadMirrorHint = null;
    notifyListeners();

    final tracker = _DownloadProgressTracker();
    try {
      final String packagePath = await _service.downloadAndVerifyPackagePath(
        update: update,
        onStageChanged: (UpdateDownloadStage s) {
          if (s == UpdateDownloadStage.downloading) {
            _stage = UpdateUiStage.downloading;
          } else {
            _stage = UpdateUiStage.verifying;
            _downloadBytesPerSecond = 0;
            _etaSeconds = null;
          }
          notifyListeners();
        },
        onProgress: (int received, int total, double progress) {
          final snapshot = tracker.compute(
            received: received,
            total: total,
            progress: progress,
            currentUiPercent: _downloadProgressPercent,
          );
          if (snapshot == null) return;
          _downloadProgressPercent = snapshot.percent;
          _downloadedBytes = snapshot.receivedBytes;
          _totalBytes = snapshot.totalBytes > 0 ? snapshot.totalBytes : update.fileSize;
          _downloadBytesPerSecond = snapshot.speedBytesPerSecond;
          _etaSeconds = snapshot.etaSeconds;
          notifyListeners();
        },
        onMirrorChanged: (int index, int total) {
          if (index <= 0) {
            _downloadMirrorHint = null;
          } else {
            _downloadMirrorHint = '正在尝试备用镜像 ${index + 1}/$total';
          }
          notifyListeners();
        },
      );

      _downloadProgressPercent = 100;
      _downloadedBytes = _totalBytes > 0 ? _totalBytes : update.fileSize;
      _stage = UpdateUiStage.readyToInstall;
      _pendingPackagePath = packagePath;
      _pendingVersionName = update.versionName;
      _pendingVersionCode = update.versionCode;
      _downloadBytesPerSecond = 0;
      _etaSeconds = null;
      notifyListeners();

      // Open APK installer on download complete
      await _service.installDownloadedPackagePath(packagePath);
      return null;
    } catch (err) {
      if (_pendingPackagePath != null) {
        _stage = UpdateUiStage.readyToInstall;
      }
      return '$err';
    } finally {
      _isUpdating = false;
      if (_stage != UpdateUiStage.readyToInstall) {
        _stage = UpdateUiStage.idle;
      }
      _downloadBytesPerSecond = 0;
      _etaSeconds = null;
      _downloadMirrorHint = null;
      notifyListeners();
    }
  }

  Future<String?> installPendingPackage() async {
    final String? packagePath = _pendingPackagePath;
    if (packagePath == null || packagePath.isEmpty) {
      return 'No downloaded update package is ready.';
    }
    if (_isUpdating) return 'Update is already in progress.';

    _isUpdating = true;
    _stage = UpdateUiStage.openingInstaller;
    _downloadBytesPerSecond = 0;
    _etaSeconds = null;
    notifyListeners();

    try {
      await _service.installDownloadedPackagePath(packagePath);
      return null;
    } catch (err) {
      _isUpdating = false;
      _stage = UpdateUiStage.readyToInstall;
      notifyListeners();
      return '$err';
    }
  }
}
