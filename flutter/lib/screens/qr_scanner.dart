import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class QRScanner extends StatefulWidget {
  const QRScanner({super.key});

  @override
  State<QRScanner> createState() => _QRScannerState();
}

class _QRScannerState extends State<QRScanner> {
  final MobileScannerController controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    formats: [BarcodeFormat.qrCode], // QR code only
  );

  bool _isScanning = true;
  String _scanResult = "Scan a QR code";
  bool _isTorchOn = false;

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('QR Code Scanner'),
          backgroundColor: Colors.transparent,
          elevation: 0,
          flexibleSpace: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xff8160c7), Color(0xff8f77dc), Color(0xff8f67bc)],
                begin: Alignment.bottomLeft,
                end: Alignment.topRight,
              ),
            ),
          ),
        actions: [
          IconButton(
            icon: Icon(_isTorchOn ? Icons.flash_on : Icons.flash_off),
            onPressed: () {
              setState(() {
                _isTorchOn = !_isTorchOn;
                controller.toggleTorch();
              });
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child:
                _isScanning
                    ? MobileScanner(
                      controller: controller,
                      onDetect: (capture) {
                        final List<Barcode> barcodes = capture.barcodes;
                        if (barcodes.isNotEmpty) {
                          final Barcode qrCode = barcodes.first;
                          // Since we've restricted to QR only in controller, this should always be QR
                          final String code =
                              qrCode.rawValue ?? "Unknown QR code";
                          debugPrint('QR code found: $code');
                          setState(() {
                            _scanResult = code;
                            _isScanning = false;
                          });
                        }
                      },
                    )
                    : Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            'QR Scan Result:',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 10),
                          Text(_scanResult, style: TextStyle(fontSize: 16)),
                          const SizedBox(height: 20),
                          // Add AR visualization here if needed
                        ],
                      ),
                    ),
          ),
          if (!_isScanning)
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: ElevatedButton(
                onPressed: () {
                  setState(() {
                    _isScanning = true;
                  });
                },
                child: const Text('Scan Another QR Code'),
              ),
            ),
        ],
      ),
    );
  }
}
