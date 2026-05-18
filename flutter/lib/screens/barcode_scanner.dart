import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class BarcodeScanner extends StatefulWidget {
  const BarcodeScanner({super.key});

  @override
  State<BarcodeScanner> createState() => _BarcodeScannerState();
}

class _BarcodeScannerState extends State<BarcodeScanner> {
  final MobileScannerController controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    // Specify only linear barcode formats (excluding QR)
    formats: [
      BarcodeFormat.code128,
      BarcodeFormat.code39,
      BarcodeFormat.code93,
      BarcodeFormat.ean13,
      BarcodeFormat.ean8,
      BarcodeFormat.upcA,
      BarcodeFormat.upcE,
      BarcodeFormat.codabar,
    ],
  );

  bool _isScanning = true;
  String _scanResult = "Scan a barcode";
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
        title: const Text('Barcode Scanner'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        flexibleSpace: Container(
          decoration: const BoxDecoration(
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
                          final Barcode barcode = barcodes.first;

                          // Verify it's a linear barcode (not a QR)
                          if (barcode.format != BarcodeFormat.qrCode) {
                            final String code =
                                barcode.rawValue ?? "Unknown code";
                            debugPrint('Barcode found: $code');
                            setState(() {
                              _scanResult = code;
                              _isScanning = false;
                            });
                          }
                        }
                      },
                    )
                    : Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text(
                            'Barcode Result:',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 10),
                          Text(_scanResult, style: TextStyle(fontSize: 16)),
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
                child: const Text('Scan Another Barcode'),
              ),
            ),
        ],
      ),
    );
  }
}
