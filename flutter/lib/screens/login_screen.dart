import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tr_business_card_clone1/screens/business_card.dart';
import 'package:tr_business_card_clone1/screens/home.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formkey = GlobalKey<FormState>();
  TextEditingController nameController = TextEditingController();
  TextEditingController companyController = TextEditingController();
  TextEditingController phoneController = TextEditingController();
  TextEditingController emailController = TextEditingController();
  TextEditingController locationController = TextEditingController();
  TextEditingController designationController = TextEditingController();
  TextEditingController websiteController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _saveUserData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('name', nameController.text);
    await prefs.setString('company', companyController.text);
    await prefs.setString('email', emailController.text);
    await prefs.setString('phone', phoneController.text);
    await prefs.setString('location', locationController.text);
    await prefs.setString('designation', designationController.text);
    await prefs.setString('website', websiteController.text);
  }

  Future<void> _loadUserData() async {
    final prefs = await SharedPreferences.getInstance();
    String? name = prefs.getString('name');
    if (name != null && name.isNotEmpty) {
      setState(() {
        nameController.text = name;
        companyController.text = prefs.getString('company') ?? '';
        emailController.text = prefs.getString('email') ?? '';
        phoneController.text = prefs.getString('phone') ?? '';
        locationController.text = prefs.getString('location') ?? '';
        designationController.text = prefs.getString('designation') ?? '';
        websiteController.text = prefs.getString('website') ?? '';
      });
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _navigateToBusinessCard();
      });
    }
  }

  void _navigateToBusinessCard() {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => BusinessCardUI(
          name: nameController.text,
          email: emailController.text,
          company: companyController.text,
          phone: phoneController.text,
          location: locationController.text,
          website: websiteController.text,
          designation: designationController.text,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: buildDrawer(context), //
      appBar: AppBar(
        title: const Text("Details"),
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
      body: SingleChildScrollView(
        child: Container(
          width: MediaQuery.of(context).size.width,
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xff8160c7), Color(0xff8f77dc), Color(0xff8f67bc)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.all(25),
            child: Form(
              key: _formkey,
              child: Column(
                children: [
                  _buildTextField("Enter your name", nameController, Icons.person, validator: true),
                  const SizedBox(height: 15),
                  _buildTextField("Designation", designationController, Icons.work, validator: true),
                  const SizedBox(height: 15),
                  _buildTextField("Company", companyController, Icons.business, validator: true),
                  const SizedBox(height: 15),
                  _buildTextField("Phone Number", phoneController, Icons.phone, validator: true, phone: true),
                  const SizedBox(height: 15),
                  _buildTextField("Enter your mail", emailController, Icons.mail, validator: true, email: true),
                  const SizedBox(height: 15),
                  _buildTextField("Location", locationController, Icons.location_on, validator: true),
                  const SizedBox(height: 15),
                  _buildTextField("Website", websiteController, Icons.web_asset, validator: true),
                  const SizedBox(height: 10),
                  ElevatedButton(
                    onPressed: () async {
                      if (_formkey.currentState!.validate()) {
                        await _saveUserData();
                        _navigateToBusinessCard();
                      }
                    },
                    child: const Text("Submit"),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller, IconData icon,
      {bool validator = false, bool phone = false, bool email = false}) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: Colors.black),
        color: Colors.white,
      ),
      child: TextFormField(
        controller: controller,
        decoration: InputDecoration(
          prefixIcon: Icon(icon),
          labelText: label,
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          errorStyle: const TextStyle(color: Colors.red, fontSize: 15),
        ),
        validator: validator
            ? (value) {
          if (value == null || value.isEmpty) return 'Please enter $label';
          if (email &&
              !RegExp(r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$").hasMatch(value)) {
            return 'Please enter a valid email';
          }
          if (phone && !RegExp(r'^\d{10}$').hasMatch(value)) {
            return 'Phone number must be exactly 10 digits';
          }
          return null;
        }
            : null,
      ),
    );
  }
}
