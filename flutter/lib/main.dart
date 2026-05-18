import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:tr_business_card_clone1/screens/home.dart';
import 'package:tr_business_card_clone1/pages/home_page.dart';
import 'package:tr_business_card_clone1/providers/contact_provider.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (_) => ContactProvider(),
      child: MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Unified Business App',
      initialRoute: '/',
      routes: {
        '/': (context) => const Home(),
        '/business-card-scanner': (context) => const HomePage(),
      },
    );
  }
}
