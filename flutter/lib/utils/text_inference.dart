import 'package:google_mlkit_entity_extraction/google_mlkit_entity_extraction.dart';
import 'constants.dart';

Future<Map<String, String>> inferContactFieldsFromText(String fullText) async {
  final result = <String, String>{};
  final entityExtractor = EntityExtractor(language: EntityExtractorLanguage.english);

  final annotations = await entityExtractor.annotateText(fullText);

  for (final annotation in annotations) {
    for (final entity in annotation.entities) {
      switch (entity.type) {
        case EntityType.phone:
          result[ContactProperties.mobile] ??= annotation.text;
          break;
        case EntityType.email:
          result[ContactProperties.email] ??= annotation.text;
          break;
        case EntityType.address:
          result[ContactProperties.address] ??= annotation.text;
          break;
        case EntityType.url:
          final url = annotation.text.toLowerCase();
          if (url.contains("linkedin")) {
            result[ContactProperties.linkedin] ??= annotation.text;
          } else if (url.contains("twitter")) {
            result[ContactProperties.twitter] ??= annotation.text;
          } else if (url.contains("instagram")) {
            result[ContactProperties.instagram] ??= annotation.text;
          } else if (url.contains("facebook")) {
            result[ContactProperties.facebook] ??= annotation.text;
          } else {
            result[ContactProperties.website] ??= annotation.text;
          }
          break;
        default:
          break;
      }
    }
  }

  await entityExtractor.close();

  final fallback = _extractDesignationAndCompany(fullText);
  result.addAll(fallback);

  return result;
}

Map<String, String> _extractDesignationAndCompany(String fullText) {
  final result = <String, String>{};
  final lines = fullText.split('\n').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();

  // Designation
  final jobTitles = [
    'ceo', 'cto', 'cfo', 'coo', 'president', 'vice president', 'vp',
    'director', 'executive', 'founder', 'manager', 'developer', 'engineer',
    'consultant', 'analyst', 'specialist', 'lead', 'supervisor',
    'architect', 'intern', 'trainee','agent','agents'
  ];

  for (final line in lines) {
    if (jobTitles.any((title) => line.toLowerCase().contains(title))) {
      result[ContactProperties.designation] = line;
      break;
    }
  }

  // Company
  final companyIndicators = ['pvt', 'ltd', 'inc', 'corp', 'technologies', 'solution','solutions', 'systems','company'];
  for (final line in lines) {
    if (companyIndicators.any((word) => line.toLowerCase().contains(word))) {
      result[ContactProperties.company] = line;
      break;
    }
  }

  return result;
}
