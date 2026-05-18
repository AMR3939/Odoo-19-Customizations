import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:tr_business_card_clone1/screens/barcode_scanner.dart';
import 'package:tr_business_card_clone1/screens/login_screen.dart';
import 'package:tr_business_card_clone1/screens/qr_scanner.dart';
import 'calendar.dart';

Drawer buildDrawer(BuildContext context) {
  return Drawer(
    child: ListView(
      padding: EdgeInsets.zero,
      children: [
        const DrawerHeader(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                Color(0xff8160c7),
                Color(0xff8f77dc),
                Color(0xff8f67bc),
              ],
              begin: Alignment.bottomLeft,
              end: Alignment.topRight,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 30,
                backgroundColor: Colors.white,
                backgroundImage: AssetImage("images/User.png"),
              ),
            ],
          ),
        ),
        ListTile(
          leading: const Icon(Icons.home),
          title: const Text("Home"),
          selected: true,
          onTap: () {
            Navigator.pop(context);
          },
        ),
        ListTile(
          leading: const Icon(Icons.person),
          title: const Text("Business Card"),
          onTap: () {
            Navigator.pop(context);
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const LoginScreen()),
            );
          },
        ),
        ListTile(
          leading: const Icon(Icons.document_scanner),
          title: const Text("Business Card Scanner"),
          onTap: () {
            Navigator.pop(context);
            Navigator.pushNamed(context, '/business-card-scanner');
          },
        ),
        ListTile(
          leading: const Icon(Icons.calendar_month),
          title: const Text("Calendar"),
          onTap: () {
            Navigator.pop(context);
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const Calendar(
                  name: '',
                  email: '',
                  phone: '',
                  location: '',
                  website: '',
                  company: '',
                  designation: '',
                ),
              ),
            );
          },
        ),
        ListTile(
          leading: const Icon(Icons.qr_code),
          title: const Text("QR Scanner"),
          onTap: () {
            Navigator.pop(context);
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => QRScanner()),
            );
          },
        ),
        ListTile(
          leading: const Icon(FontAwesomeIcons.barcode),
          title: const Text("Barcode Scanner"),
          onTap: () {
            Navigator.pop(context);
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => BarcodeScanner()),
            );
          },
        ),
      ],
    ),
  );
}

class Home extends StatelessWidget {
  const Home({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: buildDrawer(context),
      appBar: AppBar(
        title: const Text("GEEA"),
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
      ),
    );
  }
}

