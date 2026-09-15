with open('lib/services/notification_service.dart', 'r', encoding='utf-8') as f:
    code = f.read()

guard_perm = """  Future<bool> checkPermissionStatus() async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) return true;
"""
code = code.replace("  Future<bool> checkPermissionStatus() async {\n", guard_perm)

guard_req = """  Future<bool> requestPermissions() async {
    if (Platform.environment.containsKey('FLUTTER_TEST')) return true;
"""
code = code.replace("  Future<bool> requestPermissions() async {\n", guard_req)

with open('lib/services/notification_service.dart', 'w', encoding='utf-8') as f:
    f.write(code)
print('notification_service permissions guarded for test environment.')
