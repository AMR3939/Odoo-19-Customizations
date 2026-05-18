import 'dart:io';
import 'package:tr_business_card_clone1/screens/barcode_scanner.dart';
import 'package:tr_business_card_clone1/screens/calendar.dart';
import 'package:tr_business_card_clone1/screens/qr_scanner.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:screenshot/screenshot.dart';
import 'home.dart';

class BusinessCardUI extends StatefulWidget {
  final String name;
  final String email;
  final String phone;
  final String location;
  final String website;
  final String designation;
  final String company;

  const BusinessCardUI({
    super.key,
    required this.name,
    required this.email,
    required this.phone,
    required this.location,
    required this.website,
    required this.designation,
    required this.company,
  });

  @override
  State<BusinessCardUI> createState() => _BusinessCardUIState();
}

class _BusinessCardUIState extends State<BusinessCardUI> {
  File? _profileImage; // new variable to store the profile image

  // Add screenshot controller for capturing business card
  final ScreenshotController screenshotController = ScreenshotController();

  // Method to pick an image from gallery
  Future<void> _pickProfileImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? pickedFile = await picker.pickImage(
      source: ImageSource.gallery,
    );
    if (pickedFile != null) {
      setState(() {
        _profileImage = File(pickedFile.path);
      });
    }
  }

  // Method to launch URLs
  Future<void> _launchURL(String url) async {
    final Uri uri = Uri.parse(url);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      throw Exception('Could not launch $url');
    }
  }

  // Method to make phone call
  Future<void> _makePhoneCall(String phoneNumber) async {
    final Uri uri = Uri(scheme: 'tel', path: phoneNumber);
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Could not launch phone app")),
        );
      }
    } catch (e) {
      print("Error making phone call: $e");
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Failed to make call: $e")));
    }
  }

  // Method to send email
  Future<void> _sendEmail(String email) async {
    final Uri uri = Uri(scheme: 'mailto', path: email);
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Could not launch email app")),
        );
      }
    } catch (e) {
      print("Error sending email: $e");
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Failed to send email: $e")));
    }
  }

  // Show options with both save to files and copy to clipboard
  void _showShareOptions() {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return Container(
          child: Wrap(
            children: <Widget>[
              ListTile(
                leading: Icon(Icons.save),
                title: Text('Save to Files'),
                onTap: () {
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: Icon(Icons.copy),
                title: Text('Copy to Clipboard'),
                onTap: () {
                  Navigator.pop(context);
                },
              ),
            ],
          ),
        );
      },
    );
  }

  late TextEditingController nameController;
  late TextEditingController companyController;
  late TextEditingController emailController;
  late TextEditingController phoneController;
  late TextEditingController locationController;
  late TextEditingController designationController;
  late TextEditingController websiteController;
  late TextEditingController linkedinController;

  late String _name;
  late String _company;
  late String _email;
  late String _phone;
  late String _location;
  late String _designation;
  late String _website;
  late String _linkedin;

  @override
  void initState() {
    super.initState();
    //initializing current values
    _name = widget.name;
    _company = widget.company;
    _email = widget.email;
    _phone = widget.phone;
    _designation = widget.designation;
    _location = widget.location;
    _website = widget.website;
    _linkedin = "";
    //initializing current values into controller
    nameController = TextEditingController(text: _name);
    companyController = TextEditingController(text: _company);
    emailController = TextEditingController(text: _email);
    phoneController = TextEditingController(text: _phone);
    designationController = TextEditingController(text: _designation);
    locationController = TextEditingController(text: _location);
    websiteController = TextEditingController(text: _website);
    linkedinController = TextEditingController(text: _linkedin);
  }

  @override
  void dispose() {
    super.dispose();
    nameController.dispose();
    companyController.dispose();
    emailController.dispose();
    phoneController.dispose();
    designationController.dispose();
    locationController.dispose();
    websiteController.dispose();
    linkedinController.dispose();
  }

  void _showDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text("Edit Business Card"),
          content: SingleChildScrollView(
            child: Column(
              children: [
                TextField(
                  controller: nameController,
                  decoration: InputDecoration(labelText: "Full Name"),
                ),
              TextField(
              controller: designationController,
              decoration: InputDecoration(labelText: "Designation"),
        ),
                TextField(
                  controller: companyController,
                  decoration: InputDecoration(labelText: "Company"),
                ),
                TextField(
                  controller: emailController,
                  decoration: InputDecoration(labelText: "Email"),
                ),
                TextField(
                  controller: phoneController,
                  decoration: InputDecoration(labelText: "Phone Number"),
                ),
                TextField(
                  controller: locationController,
                  decoration: InputDecoration(labelText: "Location"),
                ),
                TextField(
                  controller: websiteController,
                  decoration: InputDecoration(labelText: "Website"),
                ),
                TextField(
                  controller: linkedinController,
                  decoration: InputDecoration(labelText: "LinkedIn URL"),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text("Cancel"),
            ),
            TextButton(
              onPressed: () {
                setState(() {
                  _name = nameController.text;
                  _company = companyController.text;
                  _email = emailController.text;
                  _phone = phoneController.text;
                  _location = locationController.text;
                  _designation = designationController.text;
                  _website = websiteController.text;
                });
                Navigator.of(context).pop();
              },
              child: Text("Save"),
            ),
          ],
        );
      },
    );
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
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
                    backgroundImage:
                        _profileImage != null
                            ? FileImage(_profileImage!)
                            : AssetImage("images/User.png") as ImageProvider,
                  ),
                  SizedBox(height: 10),
                  Text(
                    _name,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                    ), // Changed text color to white
                  ),
                  Text(
                    _email,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                    ), // Changed text color to white with opacity
                  ),
                ],
              ),
            ),
            ListTile(
              leading: Icon(Icons.home),
              title: Text("Home"),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => Home()),
                );
              },
            ),
            ListTile(
              leading: Icon(Icons.person),
              title: Text("Business Card"),
              selected: true,
              onTap: () {
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: Icon(Icons.document_scanner),
              title: Text("Business Card Scanner"),
              onTap: () {
                Navigator.pop(context);
                Navigator.pushNamed(context, '/business-card-scanner');
              },
            ),
            ListTile(
              leading: Icon(Icons.calendar_month),
              title: Text("Calendar"),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder:
                        (context) => Calendar(
                          name: _name,
                          email: _email,
                          phone: _phone,
                          website: _website,
                          location: _location,
                          designation: _designation,
                          company: _company,
                          profileImage: _profileImage,
                        ),
                  ),
                );
              },
            ),
            ListTile(
              leading: Icon(Icons.qr_code),
              title: Text("QR Scanner"),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => QRScanner()),
                );
              },
            ),
            ListTile(
              leading: Icon(FontAwesomeIcons.barcode),
              title: Text("Barcode Scanner"),
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
      ),
      appBar: AppBar(
        //automaticallyImplyLeading: false,
        // This will remove the back button
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
          IconButton(onPressed: _showDialog, icon: Icon(Icons.edit)),
          IconButton(
            onPressed: _showShareOptions,
            icon: Icon(Icons.share),
            tooltip: "Share",
          ),
        ],
      ),
      body: Screenshot(
        controller: screenshotController,
        child: Container(
          width: MediaQuery.of(context).size.width,
          height: MediaQuery.of(context).size.height,
          color: Colors.white,
          child: CustomPaint(
            painter: CurvePainter(),
            child: Column(
              children: [
                SizedBox(height: MediaQuery.of(context).size.width * 0.38),
                Container(
                  padding: EdgeInsets.fromLTRB(10, 0, 0, 0),
                  child: CircleAvatar(
                    radius: MediaQuery.of(context).size.width * 0.09,
                    backgroundColor: Colors.white,
                    child: GestureDetector(
                      onTap: _pickProfileImage,
                      child: CircleAvatar(
                        radius: MediaQuery.of(context).size.width * 0.08,
                        backgroundImage:
                            _profileImage != null
                                ? FileImage(_profileImage!)
                                : AssetImage("images/User.png")
                                    as ImageProvider,
                      ),
                    ),
                  ),
                ),
                SizedBox(height: 10),
                Text(
                  _name,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                SizedBox(height: 1),
                Text(_designation, style: TextStyle(color: Colors.black)),
                SizedBox(height: 1),
                Text(_company, style: TextStyle(color: Colors.black)),
                SizedBox(height: 1),
                Text(
                  _location,
                  style: TextStyle(color: Colors.black, letterSpacing: 1),
                ),
                SizedBox(height: 10),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    GestureDetector(
                      onTap: () => _makePhoneCall(_phone),
                      child: Container(
                        padding: EdgeInsets.fromLTRB(2, 1, 1, 3),
                        width: MediaQuery.of(context).size.width * 0.08,
                        height: MediaQuery.of(context).size.width * 0.08,
                        decoration: BoxDecoration(
                          color: Colors.green,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          CupertinoIcons.phone,
                          color: Colors.white,
                          size: 18,
                        ),
                      ),
                    ),
                    SizedBox(width: MediaQuery.of(context).size.width * 0.05),
                    GestureDetector(
                      onTap: () => _sendEmail(_email),
                      child: Container(
                        padding: EdgeInsets.fromLTRB(2, 1, 1, 3),
                        width: MediaQuery.of(context).size.width * 0.08,
                        height: MediaQuery.of(context).size.width * 0.08,
                        decoration: BoxDecoration(
                          color: Colors.redAccent.shade200,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          CupertinoIcons.mail,
                          color: Colors.white,
                          size: 18,
                        ),
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 20),
                Divider(
                  thickness: 1.15,
                  indent: MediaQuery.of(context).size.width * 0.1,
                  endIndent: MediaQuery.of(context).size.width * 0.1,
                  color: Colors.grey.shade400,
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    SizedBox(width: MediaQuery.of(context).size.width * 0.12),
                    Text(
                      "OVERVIEW",
                      style: TextStyle(
                        fontSize: 14,
                        letterSpacing: 1.15,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 10),
                GestureDetector(
                  onTap: () {},
                  child: Container(
                    width: MediaQuery.of(context).size.width * 0.7,
                    padding: EdgeInsets.fromLTRB(20, 3, 1, 3),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      border: Border.all(color: Colors.grey.shade200, width: 1),
                      borderRadius: BorderRadius.all(Radius.circular(20)),
                    ),
                    child: Row(
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "PHONE",
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                            SizedBox(height: 3),
                            Text(
                              _phone,
                              style: TextStyle(
                                color: Colors.black,
                                fontSize: 12,
                                letterSpacing: 1.1,
                              ),
                            ),
                          ],
                        ),
                        Spacer(),
                        Container(
                          width: MediaQuery.of(context).size.width * 0.12,
                          height: MediaQuery.of(context).size.width * 0.07,
                          decoration: BoxDecoration(
                            color: Colors.green,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            CupertinoIcons.phone,
                            size: 18,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 10),
                GestureDetector(
                  onTap: () => _sendEmail(_email),
                  child: Container(
                    width: MediaQuery.of(context).size.width * 0.7,
                    padding: EdgeInsets.fromLTRB(20, 3, 1, 3),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      border: Border.all(color: Colors.grey.shade200),
                      borderRadius: BorderRadius.all(Radius.circular(20)),
                    ),
                    child: Row(
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "EMAIL",
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                            SizedBox(height: 3),
                            Text(
                              _email,
                              style: TextStyle(
                                color: Colors.black,
                                fontSize: 12,
                                letterSpacing: 1.0,
                              ),
                            ),
                          ],
                        ),
                        Spacer(),
                        Container(
                          width: MediaQuery.of(context).size.width * 0.12,
                          height: MediaQuery.of(context).size.width * 0.07,
                          decoration: BoxDecoration(
                            color: Colors.redAccent.shade200,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            CupertinoIcons.mail,
                            size: 18,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 10),
                GestureDetector(
                  onTap: () {
                    if (_website.isNotEmpty) {
                      String url = _website;
                      if (!url.startsWith('http://') &&
                          !url.startsWith('https://')) {
                        url = 'https://$url';
                      }
                      _launchURL(url);
                    }
                  },
                  child: Container(
                    width: MediaQuery.of(context).size.width * 0.7,
                    padding: EdgeInsets.fromLTRB(20, 3, 1, 3),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      border: Border.all(color: Colors.grey.shade200, width: 1),
                      borderRadius: BorderRadius.all(Radius.circular(20)),
                    ),
                    child: Row(
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "WEBSITE",
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                            SizedBox(height: 3),
                            Text(
                              _website,
                              style: TextStyle(
                                color: Colors.black,
                                fontSize: 12,
                                letterSpacing: 1.0,
                              ),
                            ),
                          ],
                        ),
                        Spacer(),
                        Container(
                          width: MediaQuery.of(context).size.width * 0.12,
                          height: MediaQuery.of(context).size.width * 0.07,
                          decoration: BoxDecoration(
                            color: Colors.deepPurple.shade300,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            CupertinoIcons.globe,
                            size: 18,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 20),
                Divider(
                  indent: MediaQuery.of(context).size.width * 0.1,
                  endIndent: MediaQuery.of(context).size.width * 0.1,
                  color: Colors.grey.shade400,
                  thickness: 1,
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    SizedBox(width: MediaQuery.of(context).size.width * 0.12),
                    Text(
                      "SOCIAL",
                      style: TextStyle(
                        fontSize: 14,
                        letterSpacing: 1.15,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 15),
                Container(
                  padding: EdgeInsets.symmetric(vertical: 5, horizontal: 65),
                  child: Row(
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          GestureDetector(
                            onTap: () {
                              _launchURL(
                                _linkedin.isNotEmpty
                                    ? _linkedin
                                    : "https://www.linkedin.com",
                              );
                            },
                            child: Row(
                              children: [
                                SizedBox(
                                  width:
                                      MediaQuery.of(context).size.width * 0.09,
                                  height:
                                      MediaQuery.of(context).size.width * 0.09,
                                  child: Image(
                                    image: AssetImage("images/linkedin.png"),
                                  ),
                                ),
                                SizedBox(width: 10),
                                Text(
                                  _linkedin.isNotEmpty
                                      ? _linkedin
                                          .replaceAll("https://", "")
                                          .replaceAll("www.", "")
                                      : "linkedin.com",
                                  style: TextStyle(
                                    fontSize: 17,
                                    color: Colors.black,
                                  ),
                                ),
                              ],
                            ),
                          ), //LinkedIn
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class CurvePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    // TODO: implement paint
    final paint = Paint();
    final path = Path();
    paint.style = PaintingStyle.fill;
    paint.shader = LinearGradient(
      colors: [Color(0xff8160c7), Color(0xff8f77dc), Color(0xff8f67bc)],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ).createShader(
      Rect.fromLTRB(
        size.width * 0.1,
        size.height * 0.15,
        size.width,
        size.height * 0.20,
      ),
    );
    path.moveTo(0, size.width * 0.25);
    path.quadraticBezierTo(
      size.width * 0.3,
      size.height * 0.3,
      size.width,
      size.height * 0.22,
    );
    path.quadraticBezierTo(
      size.width * 0.9,
      size.height * 0.38,
      size.width,
      size.height * 0.22,
    );
    path.lineTo(size.width, 0);
    path.lineTo(0, 0);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}
