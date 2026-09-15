import 'dart:async';
import 'dart:convert';
import 'dart:ffi';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:open_filex/open_filex.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/app_update_info.dart';
import 'github_release_parser.dart';
import 'update_manifest_parser.dart';

export '../models/app_update_info.dart';

part 'parts/download.dart';

class AppUpdateService {
  AppUpdateService({
    this.manifestUrl =
        'https://github.com/RiverAge/DaleMa/releases/latest/download/update.json',
    this.checkUrl =
        'https://api.github.com/repos/RiverAge/DaleMa/releases/latest',
    Dio? dio,
  }) : _dio = dio ?? Dio();

  final String manifestUrl;
  final String checkUrl;
  final Dio _dio;
  final GitHubReleaseParser _releaseParser = GitHubReleaseParser();
  final UpdateManifestParser _manifestParser = UpdateManifestParser();

  /// 纯 Dart 零依赖检测本机 CPU 架构（arm64-v8a / armeabi-v7a / x86_64）
  String? get currentDeviceAbi {
    if (!Platform.isAndroid) return null;
    try {
      switch (Abi.current()) {
        case Abi.androidArm64:
          return 'arm64-v8a';
        case Abi.androidArm:
          return 'armeabi-v7a';
        case Abi.androidX64:
          return 'x86_64';
        case Abi.androidIA32:
          return 'x86';
        default:
          return null;
      }
    } catch (_) {
      return null;
    }
  }

  Future<void> installDownloadedPackagePath(String filePath) async {
    final result = await OpenFilex.open(
      filePath,
      type: 'application/vnd.android.package-archive',
    );
    if (result.type != ResultType.done) {
      throw StateError('调起安装程序失败: ${result.message}');
    }
  }

  Future<void> openUpdateDownloadPage(AppUpdateInfo update) async {
    final rawUrl = update.downloadUrl.trim();
    if (rawUrl.isEmpty) {
      throw StateError('Download URL is empty.');
    }
    final result = await OpenFilex.open(rawUrl);
    if (result.type != ResultType.done) {
      throw StateError('打开下载页面失败: ${result.message}');
    }
  }

  Future<AppUpdateCheckResult> checkForUpdate() async {
    final packageInfo = await PackageInfo.fromPlatform();
    final currentVersionCode = int.tryParse(packageInfo.buildNumber) ?? 0;
    final abi = currentDeviceAbi;
    ParsedUpdateInfo parsedInfo;
    try {
      parsedInfo = await _fetchManifestUpdateInfo(abi: abi);
    } catch (manifestError) {
      try {
        parsedInfo = await _fetchGitHubReleaseUpdateInfo(abi: abi);
      } catch (apiError) {
        throw StateError(
          'Update check failed. '
          'manifestUrl=$manifestUrl, '
          'manifestError=${_summarizeUpdateCheckError(manifestError)}; '
          'apiUrl=$checkUrl, '
          'apiError=${_summarizeUpdateCheckError(apiError)}',
        );
      }
    }

    final remote = AppUpdateInfo(
      versionName: parsedInfo.versionName,
      versionCode: parsedInfo.versionCode,
      sha256: parsedInfo.sha256,
      fileSize: parsedInfo.fileSize,
      downloadUrl: parsedInfo.downloadUrl,
      changelog: parsedInfo.changelog,
      mirrors: parsedInfo.mirrors,
    );

    if (remote.versionCode <= 0 || remote.downloadUrl.isEmpty) {
      throw StateError('Invalid update payload.');
    }

    return AppUpdateCheckResult(
      currentVersionName: packageInfo.version,
      currentVersionCode: currentVersionCode,
      remote: remote,
      hasUpdate: remote.versionCode > currentVersionCode,
    );
  }

  Future<ParsedUpdateInfo> _fetchManifestUpdateInfo({String? abi}) async {
    final payload = await _getJsonMap(
      manifestUrl,
      headers: const <String, String>{
        'User-Agent': 'DaleMa-App',
        'Accept': 'application/json, */*',
      },
    );
    return _manifestParser.parseManifest(manifestJson: payload, abi: abi);
  }

  Future<ParsedUpdateInfo> _fetchGitHubReleaseUpdateInfo({String? abi}) async {
    final payload = await _getJsonMap(
      checkUrl,
      headers: const <String, String>{
        'User-Agent': 'DaleMa-App',
        'Accept': 'application/vnd.github.v3+json',
      },
    );
    return _releaseParser.parseRelease(releaseJson: payload, abi: abi);
  }

  Future<Map<String, dynamic>> _getJsonMap(
    String url, {
    required Map<String, String> headers,
  }) async {
    final response = await _dio.get<dynamic>(
      url,
      options: Options(responseType: ResponseType.plain, headers: headers),
    );
    final data = response.data;
    if (data is Map<String, dynamic>) {
      return data;
    }
    if (data is String) {
      final decoded = jsonDecode(data);
      if (decoded is Map<String, dynamic>) {
        return decoded;
      }
    }
    throw StateError('Expected JSON object from $url.');
  }

  Future<File> downloadAndVerifyPackage({
    required AppUpdateInfo update,
    void Function(int received, int total, double progress)? onProgress,
    void Function(UpdateDownloadStage stage)? onStageChanged,
    void Function(int mirrorIndex, int total)? onMirrorChanged,
  }) {
    if (update.downloadUrl.isEmpty) {
      throw StateError('Download URL is empty.');
    }

    return _downloadAndVerifyPackage(
      update: update,
      onProgress: onProgress,
      onStageChanged: onStageChanged,
      onMirrorChanged: onMirrorChanged,
    );
  }

  Future<String> downloadAndVerifyPackagePath({
    required AppUpdateInfo update,
    void Function(int received, int total, double progress)? onProgress,
    void Function(UpdateDownloadStage stage)? onStageChanged,
    void Function(int mirrorIndex, int total)? onMirrorChanged,
  }) async {
    final file = await downloadAndVerifyPackage(
      update: update,
      onProgress: onProgress,
      onStageChanged: onStageChanged,
      onMirrorChanged: onMirrorChanged,
    );
    return file.path;
  }

  String _buildDownloadFileName(AppUpdateInfo update) {
    final uri = Uri.tryParse(update.downloadUrl);
    final candidate = uri == null ? '' : p.basename(uri.path);
    if (candidate.isNotEmpty && candidate.endsWith('.apk')) {
      return candidate;
    }

    final abi = currentDeviceAbi;
    final suffix = (abi != null && abi.isNotEmpty) ? '-$abi' : '';
    return 'dalema-${update.versionName}+${update.versionCode}$suffix.apk';
  }

  String _summarizeUpdateCheckError(dynamic error) {
    if (error is DioException) {
      final statusCode = error.response?.statusCode;
      final responseData = error.response?.data;
      return 'DioException(statusCode=$statusCode, '
          'message=${error.message}, response=${_stringifyResponseData(responseData)})';
    }
    return '$error';
  }

  String _stringifyResponseData(dynamic data) {
    if (data == null) {
      return '';
    }
    final text = data is String ? data : data.toString();
    const maxLength = 300;
    if (text.length <= maxLength) {
      return text;
    }
    return '${text.substring(0, maxLength)}...';
  }
}
