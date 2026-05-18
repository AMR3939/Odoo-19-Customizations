const String tableContact = 'tbl_contact';
const String tblContactColId = 'id';
const String tblContactColFirstName = 'first_name';
const String tblContactColLastName = 'last_name';
const String tblContactColMobile = 'mobile';
const String tblContactColEmail = 'email';
const String tblContactColAddress = 'address';
const String tblContactColCompany = 'company';
const String tblContactColDesignation = 'designation';
const String tblContactColWebsite = 'website';
const String tblContactColLinkedIn = 'linkedin';
const String tblContactColTwitter = 'twitter';
const String tblContactColFacebook = 'facebook';
const String tblContactColInstagram = 'instagram';
const String tblContactColImage = 'image';
const String tblContactColFavorite = 'favorite';

class ContactModel {
  int id;
  String firstName;
  String lastName;
  String mobile;
  String email;
  String address;
  String company;
  String designation;
  String website;
  String linkedin;
  String twitter;
  String facebook;
  String instagram;
  String image;
  bool favorite;

  ContactModel({
    this.id = -1,
    required this.firstName,
    required this.lastName,
    required this.mobile,
    this.email = '',
    this.address = '',
    this.company = '',
    this.designation = '',
    this.website = '',
    this.linkedin = '',
    this.twitter = '',
    this.facebook = '',
    this.instagram = '',
    this.image = '',
    this.favorite = false,
  });

  Map<String, dynamic> toMap() {
    final map = <String, dynamic>{
      tblContactColFirstName: firstName,
      tblContactColLastName: lastName,
      tblContactColMobile: mobile,
      tblContactColEmail: email,
      tblContactColAddress: address,
      tblContactColCompany: company,
      tblContactColDesignation: designation,
      tblContactColWebsite: website,
      tblContactColLinkedIn: linkedin,
      tblContactColTwitter: twitter,
      tblContactColFacebook: facebook,
      tblContactColInstagram: instagram,
      tblContactColImage: image,
      tblContactColFavorite: favorite ? 1 : 0,
    };
    if (id > 0) {
      map[tblContactColId] = id;
    }
    return map;
  }

  factory ContactModel.fromMap(Map<String, dynamic> map) => ContactModel(
    id: map[tblContactColId],
    firstName: map[tblContactColFirstName],
    lastName: map[tblContactColLastName],
    mobile: map[tblContactColMobile],
    email: map[tblContactColEmail],
    address: map[tblContactColAddress],
    company: map[tblContactColCompany],
    designation: map[tblContactColDesignation],
    website: map[tblContactColWebsite],
    linkedin: map[tblContactColLinkedIn],
    twitter: map[tblContactColTwitter],
    facebook: map[tblContactColFacebook],
    instagram: map[tblContactColInstagram],
    image: map[tblContactColImage],
    favorite: map[tblContactColFavorite] == 1,
  );

  @override
  String toString() {
    return 'ContactModel{id: $id, firstName: $firstName, lastName: $lastName, mobile: $mobile, email: $email, '
        'address: $address, company: $company, designation: $designation, website: $website, linkedin: $linkedin, '
        'twitter: $twitter, facebook: $facebook, instagram: $instagram, image: $image, favorite: $favorite}';
  }
}
