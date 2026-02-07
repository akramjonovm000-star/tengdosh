import 'dart:io';

class DirectHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..findProxy = (uri) {
        // Force direct connection, bypassing any system proxies (Charles, etc.)
        return "DIRECT";
      }
      ..badCertificateCallback = (X509Certificate cert, String host, int port) => true; // Allow self-signed for dev
  }
}
