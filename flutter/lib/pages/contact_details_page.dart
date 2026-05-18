import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher_string.dart';
import 'package:tr_business_card_clone1/models/contact_model.dart';
import 'package:tr_business_card_clone1/providers/contact_provider.dart';
import 'package:tr_business_card_clone1/utils/helper_functions.dart';
import 'package:tr_business_card_clone1/pages/home_page.dart';
import 'package:tr_business_card_clone1/pages/scan_page.dart';

class ContactDetailsPage extends StatelessWidget {
  static const String routeName = 'details';
  final int id;
  const ContactDetailsPage({super.key, required this.id});

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<ContactProvider>(context, listen: false);
    return FutureBuilder<ContactModel>(
      future: provider.getContactById(id),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        if (snapshot.hasError) {
          return Scaffold(
            appBar: AppBar(
              backgroundColor: const Color(0xff8160c7),
              title: const Text('Contact Details', style: TextStyle(color: Colors.white)),
            ),
            body: Center(child: Text('Error: ${snapshot.error}')),
          );
        }

        final contact = snapshot.data!;
        return Scaffold(
          appBar: AppBar(
            backgroundColor: const Color(0xff8160c7),
            centerTitle: true,
            iconTheme: const IconThemeData(color: Colors.white),
            title: const Text('Contact Details', style: TextStyle(color: Colors.white)),
            actions: [
              IconButton(
                icon: const Icon(Icons.share, color: Colors.white),
                onPressed: () {
                  final text = _buildShareText(contact);
                  Share.share(text, subject: '${contact.firstName} ${contact.lastName}');
                },
              ),
              IconButton(
                icon: const Icon(Icons.edit, color: Colors.white),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ScanPage(contactToEdit: contact),
                    ),
                  );
                },
              ),
              IconButton(
                icon: const Icon(Icons.delete, color: Colors.white),
                onPressed: () async {
                  final confirmed = await showDialog<bool>(
                    context: context,
                    builder: (_) => AlertDialog(
                      title: const Text('Delete Contact'),
                      content: const Text('Are you sure you want to delete this contact?'),
                      actions: [
                        TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
                        TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
                      ],
                    ),
                  );
                  if (confirmed == true) {
                    await provider.deleteContact(contact.id);
                    await provider.getAllContacts();
                    if (context.mounted) {
                      showMsg(context, 'Contact deleted');
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(builder: (_) => const HomePage()),
                            (route) => false,
                      );
                    }
                  }
                },
              ),
            ],
          ),
          body: ListView(
            padding: const EdgeInsets.all(8.0),
            children: [
              if (contact.image.isNotEmpty && File(contact.image).existsSync())
                Image.file(
                  File(contact.image),
                  width: double.infinity,
                  height: 200,
                  fit: BoxFit.cover,
                ),
              const SizedBox(height: 12),
              _buildInfoTile('Name', '${contact.firstName} ${contact.lastName}'),
              _buildInfoTile('Company', contact.company),
              _buildInfoTile('Designation', contact.designation),
              _buildInfoTile('Mobile', contact.mobile),
              _buildInfoTile('Email', contact.email),
              _buildInfoTile('Address', contact.address),
              _buildInfoTile('Website', contact.website),
              _buildInfoTile('LinkedIn', contact.linkedin),
              _buildInfoTile('Twitter', contact.twitter),
              _buildInfoTile('Facebook', contact.facebook),
              _buildInfoTile('Instagram', contact.instagram),
            ],
          ),
        );
      },
    );
  }

  Widget _buildInfoTile(String title, String value) {
    return ListTile(
      title: Text(title, style: const TextStyle(color: Color(0xff8160c7))),
      subtitle: Text(value.isEmpty ? '-' : value),
    );
  }

  String _buildShareText(ContactModel c) {
    return '''
Name: ${c.firstName} ${c.lastName}
Mobile: ${c.mobile}
Email: ${c.email}
Company: ${c.company}
Designation: ${c.designation}
Address: ${c.address}
Website: ${c.website}
LinkedIn: ${c.linkedin}
Twitter: ${c.twitter}
Facebook: ${c.facebook}
Instagram: ${c.instagram}
''';
  }
}
