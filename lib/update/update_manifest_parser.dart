import 'github_release_parser.dart';

/// Parses the static update manifest (update.json) for Android with ABI split support.
class UpdateManifestParser {
  ParsedUpdateInfo parseManifest({
    required Map<String, dynamic> manifestJson,
    String? abi,
  }) {
    final versionName = manifestJson['versionName'] as String?;
    final versionCode = (manifestJson['versionCode'] as num?)?.toInt();
    if (versionName == null || versionName.isEmpty) {
      throw StateError('Update manifest missing versionName.');
    }
    if (versionCode == null || versionCode <= 0) {
      throw StateError('Update manifest has invalid versionCode.');
    }

    final platforms = manifestJson['platforms'] as Map<String, dynamic>?;
    if (platforms == null || platforms.isEmpty) {
      throw StateError('Update manifest missing platforms.');
    }

    final platformPayload = (platforms['android'] ?? platforms['android.apk']) as Map<String, dynamic>?;
    if (platformPayload == null) {
      throw StateError('Update manifest missing platform=android.');
    }

    // Check if ABI split exists in manifest
    Map<String, dynamic>? abiPayload;
    if (abi != null && abi.isNotEmpty) {
      final abis = platformPayload['abis'];
      if (abis is Map<String, dynamic> && abis[abi] is Map<String, dynamic>) {
        abiPayload = abis[abi] as Map<String, dynamic>;
      }
    }

    final activePayload = abiPayload ?? platformPayload;

    final platformVersionCode =
        (activePayload['versionCode'] as num?)?.toInt() ?? versionCode;
    if (platformVersionCode <= 0) {
      throw StateError('Update manifest has invalid platform versionCode.');
    }

    final downloadUrl = _readDownloadUrl(
      manifestJson: manifestJson,
      platformPayload: platformPayload,
      abiPayload: abiPayload,
    );
    final fileSize =
        (activePayload['fileSize'] as num?)?.toInt() ??
        (activePayload['size'] as num?)?.toInt() ??
        0;
    final mirrors = _readMirrors(
      activePayload,
      fallbackUrl: downloadUrl,
    );

    return ParsedUpdateInfo(
      versionName: versionName,
      versionCode: platformVersionCode,
      sha256: activePayload['sha256'] as String? ?? '',
      fileSize: fileSize,
      downloadUrl: downloadUrl,
      changelog: manifestJson['changelog'] as String? ?? '',
      mirrors: mirrors,
    );
  }

  List<String> _readMirrors(
    Map<String, dynamic> payload, {
    required String fallbackUrl,
  }) {
    final raw = payload['mirrors'];
    if (raw is List<dynamic>) {
      final list = raw
          .whereType<String>()
          .map((s) => s.trim())
          .where((s) => s.isNotEmpty)
          .toList(growable: false);
      if (list.isNotEmpty) return list;
    }
    if (fallbackUrl.isNotEmpty) {
      if (fallbackUrl.startsWith('https://github.com/')) {
        return [
          'https://ghfast.top/$fallbackUrl',
          'https://ghproxy.net/$fallbackUrl',
          'https://gh-proxy.com/$fallbackUrl',
          fallbackUrl,
        ];
      }
      return <String>[fallbackUrl];
    }
    return const <String>[];
  }

  String _readDownloadUrl({
    required Map<String, dynamic> manifestJson,
    required Map<String, dynamic> platformPayload,
    Map<String, dynamic>? abiPayload,
  }) {
    final directUrl = (abiPayload?['downloadUrl'] as String?) ??
        (platformPayload['downloadUrl'] as String?);
    if (directUrl != null && directUrl.isNotEmpty) {
      return directUrl;
    }

    final repository = (manifestJson['repository'] as String?) ?? 'RiverAge/DaleMa';
    final tagName = manifestJson['tagName'] as String?;
    final assetName = (abiPayload?['assetName'] as String?) ??
        (platformPayload['assetName'] as String?) ??
        'app-release.apk';
    if (tagName == null || tagName.isEmpty) {
      throw StateError('Update manifest missing tagName.');
    }

    return 'https://github.com/$repository/releases/download/$tagName/$assetName';
  }
}
