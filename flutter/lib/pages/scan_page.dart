import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter_easyloading/flutter_easyloading.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:tr_business_card_clone1/models/contact_model.dart';
import 'package:tr_business_card_clone1/providers/contact_provider.dart';
import 'package:tr_business_card_clone1/utils/constants.dart';
import 'package:tr_business_card_clone1/utils/helper_functions.dart';
import 'package:tr_business_card_clone1/utils/text_inference.dart';

import 'home_page.dart';

class ScanPage extends StatefulWidget {
  static const String routeName = 'scan';
  final ContactModel? contactToEdit;
  const ScanPage({super.key, this.contactToEdit});

  @override
  State<ScanPage> createState() => _ScanPageState();
}

class _ScanPageState extends State<ScanPage> {
  bool isScanOver = false;
  List<TextBlock> textBlocks = [];
  ui.Image? uiImage;
  String image = '';
  int? editingId;

  final _formKey = GlobalKey<FormState>();

  final firstNameController = TextEditingController();
  final lastNameController = TextEditingController();
  final mobileController = TextEditingController();
  final emailController = TextEditingController();
  final addressController = TextEditingController();
  final companyController = TextEditingController();
  final designationController = TextEditingController();
  final webController = TextEditingController();
  final linkedinController = TextEditingController();
  final twitterController = TextEditingController();
  final facebookController = TextEditingController();
  final instagramController = TextEditingController();

  @override
  void initState() {
    super.initState();
    if (widget.contactToEdit != null) {
      _prefillFields(widget.contactToEdit!);
    }
  }

  void _prefillFields(ContactModel contact) {
    editingId = contact.id;
    firstNameController.text = contact.firstName;
    lastNameController.text = contact.lastName;
    mobileController.text = contact.mobile;
    emailController.text = contact.email;
    addressController.text = contact.address;
    companyController.text = contact.company;
    designationController.text = contact.designation;
    webController.text = contact.website;
    linkedinController.text = contact.linkedin;
    twitterController.text = contact.twitter;
    facebookController.text = contact.facebook;
    instagramController.text = contact.instagram;
    image = contact.image;
  }

  @override
  void dispose() {
    firstNameController.dispose();
    lastNameController.dispose();
    mobileController.dispose();
    emailController.dispose();
    addressController.dispose();
    companyController.dispose();
    designationController.dispose();
    webController.dispose();
    linkedinController.dispose();
    twitterController.dispose();
    facebookController.dispose();
    instagramController.dispose();
    super.dispose();
  }

  void saveContact() async {
    if (_formKey.currentState!.validate()) {
      final contact = ContactModel(
        id: editingId ?? -1,
        firstName: firstNameController.text,
        lastName: lastNameController.text,
        mobile: mobileController.text,
        email: emailController.text,
        address: addressController.text,
        company: companyController.text,
        designation: designationController.text,
        website: webController.text,
        linkedin: linkedinController.text,
        twitter: twitterController.text,
        facebook: facebookController.text,
        instagram: instagramController.text,
        image: image,
      );

      final provider = Provider.of<ContactProvider>(context, listen: false);

      if (editingId != null) {
        await provider.updateContact(contact);
        showMsg(context, 'Contact updated');
      } else {
        final id = await provider.insertContact(contact);
        if (id > 0) {
          showMsg(context, 'Saved');
        } else {
          showMsg(context, 'Failed to save');
        }
      }

      if (mounted) {
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (_) => const HomePage()),
              (route) => false,
        );
      }
    }
  }

  void autoFillFields(Map<String, String> inferred) {
    firstNameController.text = inferred[ContactProperties.firstName] ?? '';
    lastNameController.text = inferred[ContactProperties.lastName] ?? '';
    mobileController.text = inferred[ContactProperties.mobile] ?? '';
    emailController.text = inferred[ContactProperties.email] ?? '';
    addressController.text = inferred[ContactProperties.address] ?? '';
    companyController.text = inferred[ContactProperties.company] ?? '';
    designationController.text = inferred[ContactProperties.designation] ?? '';
    webController.text = inferred[ContactProperties.website] ?? '';
    linkedinController.text = inferred[ContactProperties.linkedin] ?? '';
    twitterController.text = inferred[ContactProperties.twitter] ?? '';
    facebookController.text = inferred[ContactProperties.facebook] ?? '';
    instagramController.text = inferred[ContactProperties.instagram] ?? '';
  }

  void getImage(ImageSource source) async {
    final xFile = await ImagePicker().pickImage(source: source);
    if (xFile != null) {
      setState(() {
        image = xFile.path;
        isScanOver = false;
        textBlocks.clear();
        uiImage = null;
      });

      EasyLoading.show(status: 'Please wait');

      final inputImage = InputImage.fromFile(File(xFile.path));
      final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
      final result = await recognizer.processImage(inputImage);

      final byteData = await File(xFile.path).readAsBytes();
      final codec = await ui.instantiateImageCodec(byteData);
      final frame = await codec.getNextFrame();

      final fullText = result.blocks.map((b) => b.text).join('\n');
      final inferred = await inferContactFieldsFromText(fullText);
      autoFillFields(inferred);

      EasyLoading.dismiss();

      setState(() {
        textBlocks = result.blocks;
        uiImage = frame.image;
        isScanOver = true;
      });
    }
  }

  Widget _buildDraggableTargetField(TextEditingController controller, String label,
      {TextInputType? type, String? Function(String?)? validator, int? minLines, int? maxLines}) {
    return DragTarget<String>(
      onAccept: (data) => controller.text = data,
      builder: (context, _, __) => TextFormField(
        controller: controller,
        decoration: InputDecoration(labelText: label, alignLabelWithHint: minLines != null),
        keyboardType: type,
        validator: validator,
        minLines: minLines,
        maxLines: maxLines,
      ),
    );
  }

  Widget buildEditableForm() {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          _buildDraggableTargetField(firstNameController, 'First Name', validator: (v) => v == null || v.isEmpty ? emptyFieldErrMsg : null),
          _buildDraggableTargetField(lastNameController, 'Last Name'),
          _buildDraggableTargetField(mobileController, 'Mobile', type: TextInputType.phone, validator: (v) => v == null || v.isEmpty ? emptyFieldErrMsg : null),
          _buildDraggableTargetField(emailController, 'Email', type: TextInputType.emailAddress),
          _buildDraggableTargetField(addressController, 'Address', type: TextInputType.multiline, minLines: 2, maxLines: null),
          _buildDraggableTargetField(companyController, 'Company'),
          _buildDraggableTargetField(designationController, 'Designation'),
          _buildDraggableTargetField(webController, 'Website', type: TextInputType.url),
          _buildDraggableTargetField(linkedinController, 'LinkedIn', type: TextInputType.url),
          _buildDraggableTargetField(twitterController, 'Twitter', type: TextInputType.url),
          _buildDraggableTargetField(facebookController, 'Facebook', type: TextInputType.url),
          _buildDraggableTargetField(instagramController, 'Instagram', type: TextInputType.url),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        iconTheme: const IconThemeData(color: Colors.white),
        backgroundColor: const Color(0xff8160c7),
        title: Text(
          widget.contactToEdit != null ? 'Edit Page' : 'Scan Page',
          style: const TextStyle(color: Colors.white),
        ),
        actions: [
          IconButton(
            onPressed: image.isEmpty && widget.contactToEdit == null ? null : saveContact,
            icon: const Icon(Icons.save, color: Colors.white),
          )
        ],
      ),

      body: ListView(
        padding: const EdgeInsets.all(8.0),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextButton.icon(
                onPressed: () => getImage(ImageSource.camera),
                icon: const Icon(Icons.camera),
                label: const Text('Capture'),
              ),
              TextButton.icon(
                onPressed: () => getImage(ImageSource.gallery),
                icon: const Icon(Icons.photo_album),
                label: const Text('Gallery'),
              ),
            ],
          ),
          if (uiImage != null && textBlocks.isNotEmpty) ...[
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8.0),
              child: BusinessCardWithBoxes(image: uiImage!, blocks: textBlocks),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: Text("Detected Texts (Drag any to a field)", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Wrap(
                spacing: 4,
                runSpacing: 4,
                children: textBlocks.map((block) {
                  return Draggable<String>(
                    data: block.text,
                    feedback: Material(
                      color: Colors.transparent,
                      child: Chip(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        label: Text(block.text, style: const TextStyle(fontSize: 12, color: Colors.white)),
                        backgroundColor: Colors.deepPurpleAccent,
                      ),
                    ),
                    child: Chip(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      label: Text(block.text, style: const TextStyle(fontSize: 12)),
                    ),
                    childWhenDragging: Opacity(
                      opacity: 0.3,
                      child: Chip(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        label: Text(block.text, style: const TextStyle(fontSize: 12)),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
          if (isScanOver || widget.contactToEdit != null) buildEditableForm(),
        ],
      ),
    );
  }
}

class BusinessCardWithBoxes extends StatelessWidget {
  final ui.Image image;
  final List<TextBlock> blocks;

  const BusinessCardWithBoxes({super.key, required this.image, required this.blocks});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final displayWidth = constraints.maxWidth;
        final displayHeight = displayWidth * (image.height / image.width);

        return SizedBox(
          width: displayWidth,
          height: displayHeight,
          child: Stack(
            children: [
              RawImage(image: image, fit: BoxFit.contain),
              ...blocks.map((block) {
                final rect = block.boundingBox;
                if (rect == null) return const SizedBox.shrink();

                final scaleX = displayWidth / image.width;
                final scaleY = displayHeight / image.height;

                final left = rect.left * scaleX;
                final top = rect.top * scaleY;
                final width = rect.width * scaleX;
                final height = rect.height * scaleY;

                return Positioned(
                  left: left,
                  top: top,
                  width: width,
                  height: height,
                  child: Container(
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.deepPurpleAccent, width: 2),
                    ),
                  ),
                );
              }).toList(),
            ],
          ),
        );
      },
    );
  }
}
