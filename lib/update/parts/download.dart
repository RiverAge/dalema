part of '../app_update_service.dart';

/// [AppUpdateService] 的下载与校验内部实现。
extension AppUpdateServiceDownloadInternal on AppUpdateService {
  Future<File> _downloadAndVerifyPackage({
    required AppUpdateInfo update,
    void Function(int received, int total, double progress)? onProgress,
    void Function(UpdateDownloadStage stage)? onStageChanged,
    void Function(int mirrorIndex, int total)? onMirrorChanged,
  }) async {
    final dir = await getTemporaryDirectory();
    final filePath = p.join(dir.path, _buildDownloadFileName(update));
    final file = File(filePath);

    // 候选下载源：优先 mirrors，否则退化为 downloadUrl 单链。
    final urls = update.mirrors.isNotEmpty
        ? update.mirrors
        : <String>[update.downloadUrl];

    onStageChanged?.call(UpdateDownloadStage.downloading);

    final errors = <String>[];
    for (var i = 0; i < urls.length; i++) {
      final url = urls[i];
      onMirrorChanged?.call(i, urls.length);
      try {
        if (await file.exists()) {
          await file.delete();
        }
        await _downloadFull(
          url: url,
          file: file,
          expectedSize: update.fileSize,
          onProgress: onProgress,
        );
        final verified = await _verifyDownloadedFile(file: file, update: update);
        if (verified) {
          onStageChanged?.call(UpdateDownloadStage.verifying);
          return file;
        }
        if (await file.exists()) {
          await file.delete();
        }
        errors.add('$url: checksum mismatch');
      } catch (e) {
        if (await file.exists()) {
          await file.delete();
        }
        errors.add('$url: $e');
      }
    }

    throw StateError('All download mirrors failed:\n${errors.join('\n')}');
  }

  Future<bool> _verifyDownloadedFile({
    required File file,
    required AppUpdateInfo update,
  }) async {
    final length = await file.length();
    if (length <= 0) return false;
    if (update.fileSize > 0 && length != update.fileSize) return false;

    final checksum = update.sha256.trim().toLowerCase();
    if (checksum.isEmpty) return true;

    final digest = await sha256.bind(file.openRead()).first;
    return digest.toString().toLowerCase() == checksum;
  }

  Future<void> _downloadFull({
    required String url,
    required File file,
    required int expectedSize,
    void Function(int received, int total, double progress)? onProgress,
  }) async {
    await _dio.download(
      url,
      file.path,
      options: Options(
        responseType: ResponseType.bytes,
        headers: const {'User-Agent': 'DaleMa-App', 'Accept': '*/*'},
      ),
      onReceiveProgress: (received, total) {
        final effectiveTotal = total > 0 ? total : expectedSize;
        if (effectiveTotal <= 0) {
          onProgress?.call(received, 0, 0);
          return;
        }
        final progress = (received / effectiveTotal).clamp(0, 1).toDouble();
        onProgress?.call(received, effectiveTotal, progress);
      },
    );
  }
}
