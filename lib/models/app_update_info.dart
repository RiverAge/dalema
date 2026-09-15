class AppUpdateInfo {
  final String versionName;
  final int versionCode;
  final String sha256;
  final int fileSize;
  final String downloadUrl;
  final String changelog;
  /// 备用下载镜像列表。客户端按序逐个尝试，失败/校验不过自动切下一个。
  /// 为空时退化成单链下载（用 downloadUrl）。GitHub 直链通常放最后兜底。
  final List<String> mirrors;

  const AppUpdateInfo({
    required this.versionName,
    required this.versionCode,
    required this.sha256,
    required this.fileSize,
    required this.downloadUrl,
    required this.changelog,
    this.mirrors = const <String>[],
  });

  AppUpdateInfo copyWith({
    String? versionName,
    int? versionCode,
    String? sha256,
    int? fileSize,
    String? downloadUrl,
    String? changelog,
    List<String>? mirrors,
  }) {
    return AppUpdateInfo(
      versionName: versionName ?? this.versionName,
      versionCode: versionCode ?? this.versionCode,
      sha256: sha256 ?? this.sha256,
      fileSize: fileSize ?? this.fileSize,
      downloadUrl: downloadUrl ?? this.downloadUrl,
      changelog: changelog ?? this.changelog,
      mirrors: mirrors ?? this.mirrors,
    );
  }

  factory AppUpdateInfo.fromJson(Map<String, dynamic> json) {
    final rawMirrors = json['mirrors'];
    List<String> mirrorsList = const <String>[];
    if (rawMirrors is List) {
      mirrorsList = rawMirrors
          .whereType<String>()
          .map((e) => e.trim())
          .where((e) => e.isNotEmpty)
          .toList(growable: false);
    }

    return AppUpdateInfo(
      versionName: (json['versionName'] as String?) ?? '',
      versionCode: (json['versionCode'] as num?)?.toInt() ?? 0,
      sha256: (json['sha256'] as String?) ?? '',
      fileSize: (json['fileSize'] as num?)?.toInt() ?? (json['size'] as num?)?.toInt() ?? 0,
      downloadUrl: (json['downloadUrl'] as String?) ?? '',
      changelog: (json['changelog'] as String?) ?? '',
      mirrors: mirrorsList,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'versionName': versionName,
      'versionCode': versionCode,
      'sha256': sha256,
      'fileSize': fileSize,
      'downloadUrl': downloadUrl,
      'changelog': changelog,
      'mirrors': mirrors,
    };
  }
}

class AppUpdateCheckResult {
  final String currentVersionName;
  final int currentVersionCode;
  final AppUpdateInfo? remote;
  final bool hasUpdate;

  const AppUpdateCheckResult({
    required this.currentVersionName,
    required this.currentVersionCode,
    required this.remote,
    required this.hasUpdate,
  });
}

enum UpdateDownloadStage {
  downloading,
  verifying,
}

enum UpdateUiStage {
  idle,
  downloading,
  verifying,
  readyToInstall,
  openingInstaller,
}

enum InstallCapability {
  supported,
  notSupported,
  permissionRequired,
}
