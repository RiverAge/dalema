part 'parts/release_metadata_parsing.dart';

/// Parses GitHub Release API response and extracts update metadata for Android APK.
class GitHubReleaseParser {
  ParsedUpdateInfo parseRelease({
    required Map<String, dynamic> releaseJson,
  }) {
    final tagName = releaseJson['tag_name'] as String?;
    if (tagName == null || tagName.isEmpty) {
      throw StateError('GitHub Release missing tag_name.');
    }

    final body = releaseJson['body'] as String? ?? '';
    final metadata = _parseMetadataBlock(body);

    final assets = releaseJson['assets'] as List<dynamic>?;
    if (assets == null || assets.isEmpty) {
      throw StateError('GitHub Release has no assets.');
    }

    final assetInfo = _selectAndroidAsset(
      assets: assets,
      metadata: metadata,
    );

    final versionName =
        metadata.versionName ?? _extractVersionFromTag(tagName);
    final versionCode = assetInfo.versionCode ?? metadata.versionCode ?? 0;
    if (versionCode <= 0) {
      throw StateError('Invalid version code in release metadata.');
    }

    final changelog = _extractChangelog(body);
    final mirrors = _buildAutoMirrors(assetInfo.downloadUrl);

    return ParsedUpdateInfo(
      versionName: versionName,
      versionCode: versionCode,
      sha256: assetInfo.sha256,
      fileSize: assetInfo.size,
      downloadUrl: assetInfo.downloadUrl,
      changelog: changelog,
      mirrors: mirrors,
    );
  }

  SelectedAssetInfo _selectAndroidAsset({
    required List<dynamic> assets,
    required ReleaseMetadata metadata,
  }) {
    final platformAssetInfo = metadata.platformAssets['android.apk'] ??
        metadata.platformAssets['android'];
    final expectedAssetName =
        platformAssetInfo?.assetName ?? 'app-release.apk';

    // 1. Exact match
    for (final asset in assets) {
      final assetMap = asset as Map<String, dynamic>;
      final name = assetMap['name'] as String?;
      if (name == expectedAssetName) {
        final downloadUrl = assetMap['browser_download_url'] as String?;
        final assetSize = (assetMap['size'] as num?)?.toInt() ?? 0;

        if (downloadUrl == null || downloadUrl.isEmpty) {
          throw StateError('Asset "$name" missing browser_download_url.');
        }

        return SelectedAssetInfo(
          downloadUrl: downloadUrl,
          versionCode: platformAssetInfo?.versionCode,
          sha256: platformAssetInfo?.sha256 ?? '',
          size: (platformAssetInfo?.size ?? 0) > 0
              ? platformAssetInfo!.size
              : assetSize,
        );
      }
    }

    // 2. Fuzzy match (any asset ending with .apk)
    for (final asset in assets) {
      final assetMap = asset as Map<String, dynamic>;
      final name = (assetMap['name'] as String? ?? '').toLowerCase();
      final downloadUrl = assetMap['browser_download_url'] as String?;
      final assetSize = (assetMap['size'] as num?)?.toInt() ?? 0;

      if (downloadUrl != null && downloadUrl.isNotEmpty && name.endsWith('.apk')) {
        return SelectedAssetInfo(
          downloadUrl: downloadUrl,
          versionCode: platformAssetInfo?.versionCode,
          sha256: platformAssetInfo?.sha256 ?? '',
          size: assetSize,
        );
      }
    }

    throw StateError('No Android APK asset found in release.');
  }

  /// 自动生成 GitHub 常用国内加速代理镜像列表
  List<String> _buildAutoMirrors(String downloadUrl) {
    if (downloadUrl.isEmpty || !downloadUrl.startsWith('https://github.com/')) {
      return downloadUrl.isNotEmpty ? [downloadUrl] : const [];
    }

    return [
      'https://ghfast.top/$downloadUrl',
      'https://ghproxy.net/$downloadUrl',
      'https://gh-proxy.com/$downloadUrl',
      downloadUrl, // 官方直链最后兜底
    ];
  }
}

class ReleaseMetadata {
  ReleaseMetadata({
    this.versionName,
    this.versionCode,
    this.platformAssets = const {},
  });

  final String? versionName;
  final int? versionCode;
  final Map<String, PlatformAssetInfo> platformAssets;
}

class PlatformAssetInfo {
  PlatformAssetInfo({
    this.assetName,
    this.versionCode,
    this.sha256 = '',
    this.size = 0,
  });

  final String? assetName;
  final int? versionCode;
  final String sha256;
  final int size;

  PlatformAssetInfo copyWith({
    String? assetName,
    int? versionCode,
    String? sha256,
    int? size,
  }) {
    return PlatformAssetInfo(
      assetName: assetName ?? this.assetName,
      versionCode: versionCode ?? this.versionCode,
      sha256: sha256 ?? this.sha256,
      size: size ?? this.size,
    );
  }
}

class SelectedAssetInfo {
  SelectedAssetInfo({
    required this.downloadUrl,
    this.versionCode,
    required this.sha256,
    required this.size,
  });

  final String downloadUrl;
  final int? versionCode;
  final String sha256;
  final int size;
}

class ParsedUpdateInfo {
  const ParsedUpdateInfo({
    required this.versionName,
    required this.versionCode,
    required this.sha256,
    required this.fileSize,
    required this.downloadUrl,
    required this.changelog,
    this.mirrors = const <String>[],
  });

  final String versionName;
  final int versionCode;
  final String sha256;
  final int fileSize;
  final String downloadUrl;
  final String changelog;
  final List<String> mirrors;
}
