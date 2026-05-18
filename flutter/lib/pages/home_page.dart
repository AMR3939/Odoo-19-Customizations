import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:tr_business_card_clone1/pages/contact_details_page.dart';
import 'package:tr_business_card_clone1/pages/scan_page.dart';
import 'package:tr_business_card_clone1/providers/contact_provider.dart';
import 'package:tr_business_card_clone1/utils/helper_functions.dart';
import 'package:tr_business_card_clone1/screens/home.dart';

class HomePage extends StatefulWidget {
  static const String routeName = '/';
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int selectedIndex = 0;

  final Color themeColor = const Color(0xff8160c7);

  @override
  void didChangeDependencies() {
    Provider.of<ContactProvider>(context, listen: false).getAllContacts();
    super.didChangeDependencies();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: buildDrawer(context),

      appBar: AppBar(
        leading: Builder(
          builder: (context) => IconButton(
            icon: const Icon(Icons.menu),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
        backgroundColor: themeColor,
        title: const Text('Contact List', style: TextStyle(color: Colors.white)),
        centerTitle: true,
        iconTheme: const IconThemeData(color: Colors.white),
      ),

      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      floatingActionButton: FloatingActionButton(
        foregroundColor: Colors.white,
        backgroundColor: themeColor,
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const ScanPage()),
          );
        },
        shape: const CircleBorder(),
        child: const Icon(Icons.add),
      ),

      bottomNavigationBar: BottomAppBar(
        elevation: 8,
        padding: EdgeInsets.zero,
        shape: const CircularNotchedRectangle(),
        notchMargin: 10,
        clipBehavior: Clip.antiAlias,
        child: BottomNavigationBar(
          backgroundColor: const Color(0xffede7f6), // Light purple
          selectedItemColor: themeColor,
          unselectedItemColor: Colors.black54,
          selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold),
          currentIndex: selectedIndex,
          onTap: (index) {
            setState(() {
              selectedIndex = index;
            });
            _fetchData();
          },
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.person),
              label: 'All',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.favorite),
              label: 'Favorites',
            ),
          ],
        ),
      ),

      body: Consumer<ContactProvider>(
        builder: (context, provider, child) => ListView.builder(
          itemCount: provider.contactList.length,
          itemBuilder: (context, index) {
            final contact = provider.contactList[index];
            return Dismissible(
              key: UniqueKey(),
              direction: DismissDirection.endToStart,
              background: Container(
                padding: const EdgeInsets.only(right: 20),
                alignment: Alignment.centerRight,
                color: Colors.red,
                child: const Icon(Icons.delete, size: 25, color: Colors.white),
              ),
              confirmDismiss: _showConfirmationDialog,
              onDismissed: (_) async {
                await provider.deleteContact(contact.id);
                showMsg(context, 'Deleted');
              },
              child: ListTile(
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ContactDetailsPage(id: contact.id),
                    ),
                  );
                },
                title: Text('${contact.firstName} ${contact.lastName}'),
                trailing: IconButton(
                  onPressed: () {
                    provider.updateFavorite(contact);
                  },
                  icon: Icon(
                    contact.favorite ? Icons.favorite : Icons.favorite_border,
                    color: contact.favorite ? themeColor : null,
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Future<bool?> _showConfirmationDialog(DismissDirection direction) {
    return showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Contact'),
        content: const Text('Are you sure to delete this contact?'),
        actions: [
          OutlinedButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('NO'),
          ),
          OutlinedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('YES'),
          ),
        ],
      ),
    );
  }

  void _fetchData() {
    final provider = Provider.of<ContactProvider>(context, listen: false);
    if (selectedIndex == 0) {
      provider.getAllContacts();
    } else {
      provider.getAllFavoriteContacts();
    }
  }
}
