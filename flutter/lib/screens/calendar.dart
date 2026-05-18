import 'package:tr_business_card_clone1/screens/business_card.dart';
import 'package:tr_business_card_clone1/screens/home.dart';
import 'package:tr_business_card_clone1/screens/qr_scanner.dart';
import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:table_calendar/table_calendar.dart';
import 'dart:io';
import 'package:intl/intl.dart';

import 'barcode_scanner.dart';

class Calendar extends StatefulWidget {
  final String name;
  final String email;
  final String phone;
  final String location;
  final String website;
  final String designation;
  final String company;
  final File? profileImage;

  const Calendar({
    super.key,
    required this.name,
    required this.email,
    required this.phone,
    required this.location,
    required this.website,
    required this.company,
    required this.designation,
    this.profileImage,
  });

  @override
  State<Calendar> createState() => _CalendarState();
}

class _CalendarState extends State<Calendar> {
  DateTime today = DateTime.now();
  late DateTime _focusedDay; // Track focused day separately
  // Variables to store range date
  DateTime? _rangeStart;
  DateTime? _rangeEnd;
  bool _userSelectedDay = false; // Flag to track if user has selected a day
  
  @override
  void initState() {
    super.initState();
    _focusedDay = today; // Initialize focused day to today
  }

  // Filter state variables
  bool _showLeaves = true;
  bool _showMeetings = true;

  // Lists to store leaves and meetings data
  final List<Map<String, dynamic>> _leaves = [];
  final List<Map<String, dynamic>> _meetings = [];

  // Checkboxes
  bool _isFullDay = true;
  bool _isHalfDay = false;

  bool _isOnline = true;
  bool _isOffline = false;

  // Variables to store meeting time
  TimeOfDay _startTime = TimeOfDay.now();
  TimeOfDay _endTime = TimeOfDay(hour: TimeOfDay.now().hour + 1, minute: TimeOfDay.now().minute);
  
  // Text controllers for meeting form
  final TextEditingController _meetingTitleController = TextEditingController();
  final TextEditingController _meetingDescController = TextEditingController();
  
  // Text controllers for leave form
  final TextEditingController _leaveReasonController = TextEditingController();
  final TextEditingController _leaveDescriptionController = TextEditingController();
  
  // Dropdown for leave type
  String _leaveType="Sick Leave";
  final List<String> _leaveTypes=[
    "Sick Leave",
    "Casual Leave",
    "Work from Home"
  ];
  //Dropdown for meeting participants
  String _meetingType = "John Doe";
  final List<String> _meetingTypes = [
    "John Doe",
    "Alice Smith",
    "Rahul Mehra",
    "Fatima Khan",
    "Michael Lee "
  ];

  //Dropdown menu for Reminders
  String _reminderDuration = "15 Mins";
  final List<String> _reminderDurations = [
    "15 Mins",
    "20 Mins",
    "30 Mins",
    "1 Hour",
    "3 Hours",
    "12 Hours",
    "1 Day",
  ];

  // Method to get events for a specific day
  List<dynamic> _getEventsForDay(DateTime day) {
    // Return meetings for this day
    return _meetings.where((meeting) => 
      isSameDay(meeting['date'], day)
    ).toList();
  }
  
  // Method to check if there are leaves for a specific day
  bool _hasLeavesForDay(DateTime day) {
    for (var leave in _leaves) {
      // Check if the day is the exact leave date
      if (isSameDay(leave['date'], day)) {
        return true;
      }
      
      // Check if the day falls within a leave range
      if (leave.containsKey('rangeStart') && leave.containsKey('rangeEnd')) {
        DateTime rangeStart = leave['rangeStart'];
        DateTime rangeEnd = leave['rangeEnd'];
        if ((day.isAfter(rangeStart) || isSameDay(day, rangeStart)) && 
            (day.isBefore(rangeEnd) || isSameDay(day, rangeEnd))) {
          return true;
        }
      }
    }
    return false;
  }

  // Custom widget to build markers
  Widget _buildEventsMarker(DateTime date, List events) {
    return Padding(
      padding: const EdgeInsets.only(top: 3.0),
      child: Container(
        width: 6.0,
        height: 6.0,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Color(0xff8160c7), // Use the app's primary color for consistency
        ),
      ),
    );
  }
  
  // Custom widget to build leave markers
  Widget _buildLeaveMarker(DateTime date) {
    return Padding(
      padding: const EdgeInsets.only(top: 3.0),
      child: Container(
        width: 6.0,
        height: 6.0,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.red, // Red color for leave indicators
        ),
      )
    );
  }

  void _onDaySelected(DateTime day, DateTime focusedDay) {
    setState(() {
      today = day;
      _focusedDay = focusedDay; // Update focused day
      _userSelectedDay = true; // Mark that user has selected a day
    });
  }

  void _onRangeSelected(DateTime? start, DateTime? end, DateTime? focusedDay) {
    setState(() {
      _rangeStart = start;
      _rangeEnd = end;
      _focusedDay = focusedDay ?? today; // Update focused day or use today if null
      
      // Also update the single day display (for the button)
      // When a range is selected, we'll use the focused day for the button display
      if (focusedDay != null) {
        today = focusedDay;
        _userSelectedDay = true; // Mark that user has selected a day
      }
    });
  }
  
  // Method to show start time picker dialog
  Future<void> _selectStartTime(BuildContext context, StateSetter setState) async {
    final TimeOfDay? pickedTime = await showTimePicker(
      context: context,
      initialTime: _startTime,
      builder: (BuildContext context, Widget? child) {
        return Theme(
          data: ThemeData.light().copyWith(
            colorScheme: ColorScheme.light(
              primary: Color(0xff8160c7), // Header background color
              onPrimary: Colors.white, // Header text color
              onSurface: Colors.black, // Dial text color
            ),
            buttonTheme: ButtonThemeData(
              textTheme: ButtonTextTheme.primary,
              colorScheme: ColorScheme.light(primary: Color(0xff8160c7)),
            ),
            // Customize time picker theme specifically for the AM/PM toggle
            timePickerTheme: TimePickerThemeData(
              dayPeriodColor: WidgetStateColor.resolveWith((states) {
                if (states.contains(WidgetState.selected)) {
                  return Color(0xff8160c7); // Selected AM/PM background color
                }
                return Colors.grey.shade200; // Unselected background
              }),
              dayPeriodTextColor: WidgetStateColor.resolveWith((states) {
                if (states.contains(WidgetState.selected)) {
                  return Colors.white; // Selected AM/PM text color
                }
                return Colors.black87; // Unselected text color
              }),
              dayPeriodBorderSide: BorderSide(color: Color(0xff8160c7)),
            ),
          ),
          child: child!,
        );
      },
    );

    if (pickedTime != null && pickedTime != _startTime) {
      setState(() {
        _startTime = pickedTime;
        
        // If end time is earlier than start time, adjust end time
        if (_endTime.hour < _startTime.hour || 
            (_endTime.hour == _startTime.hour && _endTime.minute < _startTime.minute)) {
          _endTime = TimeOfDay(
            hour: _startTime.hour + 1,
            minute: _startTime.minute,
          );
        }
      });
    }
  }
  
  // Method to show end time picker dialog
  Future<void> _selectEndTime(BuildContext context, StateSetter setState) async {
    final TimeOfDay? pickedTime = await showTimePicker(
      context: context,
      initialTime: _endTime,
      builder: (BuildContext context, Widget? child) {
        return Theme(
          data: ThemeData.light().copyWith(
            colorScheme: ColorScheme.light(
              primary: Color(0xff8160c7), // Header background color
              onPrimary: Colors.white, // Header text color
              onSurface: Colors.black, // Dial text color
            ),
            buttonTheme: ButtonThemeData(
              textTheme: ButtonTextTheme.primary,
              colorScheme: ColorScheme.light(primary: Color(0xff8160c7)),
            ),
            timePickerTheme: TimePickerThemeData(
              dayPeriodColor: WidgetStateColor.resolveWith((states) {
                if (states.contains(WidgetState.selected)) {
                  return Color(0xff8160c7); // Selected AM/PM background color
                }
                return Colors.grey.shade200; // Unselected background
              }),
              dayPeriodTextColor: WidgetStateColor.resolveWith((states) {
                if (states.contains(WidgetState.selected)) {
                  return Colors.white; // Selected AM/PM text color
                }
                return Colors.black87; // Unselected text color
              }),
              dayPeriodBorderSide: BorderSide(color: Color(0xff8160c7)),
            ),
          ),
          child: child!,
        );
      },
    );

    if (pickedTime != null && pickedTime != _endTime) {
      setState(() {
        _endTime = pickedTime;
      });
    }
  }

  // Helper method to get all leave entries for display
  List<Map<String, dynamic>> _getExpandedLeaves() {
    List<Map<String, dynamic>> expandedLeaves = [];
    
    for (var leave in _leaves) {
      // For range leaves, create individual entries for each date in the range
      if (leave.containsKey('rangeStart') && leave.containsKey('rangeEnd')) {
        DateTime start = leave['rangeStart'];
        DateTime end = leave['rangeEnd'];
        
        // Create a copy of the current date to iterate through
        DateTime currentDate = DateTime(start.year, start.month, start.day);
        
        // Loop through each day in the range
        while (currentDate.isBefore(end) || isSameDay(currentDate, end)) {
          // Create a new leave entry for this specific date
          Map<String, dynamic> dailyLeave = Map.from(leave);
          dailyLeave['date'] = DateTime(currentDate.year, currentDate.month, currentDate.day);
          
          // Only show if it's for the currently selected single date
          if (isSameDay(dailyLeave['date'], today)) {
            expandedLeaves.add(dailyLeave);
          }
          
          // Move to the next day
          currentDate = currentDate.add(Duration(days: 1));
        }
      } else {
        // For single-day leaves, only show if it's for the selected date
        if (isSameDay(leave['date'], today)) {
          expandedLeaves.add(leave);
        }
      }
    }
    
    // Sort the expanded leaves by date
    expandedLeaves.sort((a, b) => a['date'].compareTo(b['date']));
    
    return expandedLeaves;
  }

  // Method to build the leaves section
  Widget _buildLeavesSection() {
    List<Map<String, dynamic>> expandedLeaves = _getExpandedLeaves();
    
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Divider(thickness: 1.0),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8.0),
            child: Text(
              'Applied Leaves',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xff8160c7),
              ),
            ),
          ),
          ...expandedLeaves.map((leave) {
            return Card(
              elevation: 2.0,
              margin: EdgeInsets.only(bottom: 12.0),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12.0),
                side: BorderSide(color: Color(0xffd2c7ed), width: 1.0),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      leave['type'],
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: Color(0xff8160c7),
                      ),
                    ),
                    SizedBox(height: 8.0),
                    Row(
                      children: [
                        Icon(Icons.calendar_today, size: 14, color: Colors.grey),
                        SizedBox(width: 6.0),
                        Text(
                          DateFormat('dd MMM, yyyy').format(leave['date']),
                          style: TextStyle(color: Colors.grey.shade700),
                        ),
                      ],
                    ),
                    SizedBox(height: 8.0),
                    Text(
                      'Reason: ${leave['reason']}',
                      style: TextStyle(fontSize: 14),
                    ),
                  ],
                ),
              ),
            );
          }),
          if (expandedLeaves.isEmpty)
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Center(
                child: Text(
                  'No leaves for the selected date',
                  style: TextStyle(color: Colors.grey),
                ),
              ),
            ),
        ],
      ),
    );
  }

  // Method to build the meetings section
  Widget _buildMeetingsSection() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Divider(thickness: 1.0),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8.0),
            child: Text(
              'Scheduled Meetings',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xff8160c7),
              ),
            ),
          ),
          ..._meetings.map((meeting) {
            // Only show meetings for the currently selected single date
            if (isSameDay(meeting['date'], today)) {
              return Card(
                elevation: 2.0,
                margin: EdgeInsets.only(bottom: 12.0),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12.0),
                  side: BorderSide(color: Color(0xffd2c7ed), width: 1.0),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        meeting['title'],
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                          color: Color(0xff8160c7),
                        ),
                      ),
                      SizedBox(height: 8.0),
                      Row(
                        children: [
                          Icon(Icons.calendar_today, size: 14, color: Colors.grey),
                          SizedBox(width: 6.0),
                          Text(
                            DateFormat('dd MMM, yyyy').format(meeting['date']),
                            style: TextStyle(color: Colors.grey.shade700),
                          ),
                        ],
                      ),
                      SizedBox(height: 4.0),
                      // Starting Time row
                      Row(
                        children: [
                          Icon(Icons.access_time, size: 14, color: Colors.grey),
                          SizedBox(width: 6.0),
                          Text(
                            'Starting Time: ',
                            style: TextStyle(
                              color: Colors.grey.shade700,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                          Text(
                            '${meeting['startTime'].format(context)}',
                            style: TextStyle(color: Colors.grey.shade700),
                          ),
                        ],
                      ),
                      SizedBox(height: 4.0),
                      // Duration row (calculated in hours and minutes)
                      Row(
                        children: [
                          Icon(Icons.timelapse, size: 14, color: Colors.grey),
                          SizedBox(width: 6.0),
                          Text(
                            'Duration: ',
                            style: TextStyle(
                              color: Colors.grey.shade700,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                          Text(
                            _calculateDuration(meeting['startTime'], meeting['endTime']),
                            style: TextStyle(color: Colors.grey.shade700),
                          ),
                        ],
                      ),
                      SizedBox(height: 4.0),
                      // Meeting mode tag
                      Row(
                        children: [
                          Icon(meeting['mode'] == 'Online' ? Icons.videocam : Icons.person, size: 14, color: Colors.grey),
                          SizedBox(width: 6.0),
                          Container(
                            padding: EdgeInsets.symmetric(horizontal: 8.0, vertical: 2.0),
                            decoration: BoxDecoration(
                              color: meeting['mode'] == 'Online' 
                                ? Colors.blue.shade50 
                                : Colors.amber.shade50,
                              borderRadius: BorderRadius.circular(12.0),
                            ),
                            child: Text(
                              meeting['mode'],
                              style: TextStyle(
                                color: meeting['mode'] == 'Online' 
                                  ? Colors.blue.shade700 
                                  : Colors.amber.shade700,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (meeting['description'] != null && meeting['description'].toString().isNotEmpty)
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(height: 8.0),
                            Text(
                              'Description: ${meeting['description']}',
                              style: TextStyle(fontSize: 14),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              );
            } else {
              return SizedBox.shrink(); // Don't show this meeting
            }
          }),
          if (_meetings.where((meeting) => isSameDay(meeting['date'], today)).isEmpty)
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Center(
                child: Text(
                  'No meetings for the selected date',
                  style: TextStyle(color: Colors.grey),
                ),
              ),
            ),
        ],
      ),
    );
  }

  // Method to calculate duration between start and end times
  String _calculateDuration(TimeOfDay startTime, TimeOfDay endTime) {
    // Convert TimeOfDay to minutes since midnight
    int startMinutes = startTime.hour * 60 + startTime.minute;
    int endMinutes = endTime.hour * 60 + endTime.minute;
    
    // Handle case where end time is on the next day
    if (endMinutes < startMinutes) {
      endMinutes += 24 * 60; // Add a day in minutes
    }
    
    // Calculate duration in minutes
    int durationMinutes = endMinutes - startMinutes;
    
    // Convert to hours and minutes
    int hours = durationMinutes ~/ 60;
    int minutes = durationMinutes % 60;
    
    // Format the result
    if (hours > 0 && minutes > 0) {
      return '$hours hr $minutes min';
    } else if (hours > 0) {
      return '$hours hr';
    } else {
      return '$minutes min';
    }
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
                    widget.profileImage != null
                        ? FileImage(widget.profileImage!)
                        : AssetImage("images/User.png") as ImageProvider,
                  ),
                  SizedBox(height: 10),
                  Text(
                    widget.name,
                    style: TextStyle(color: Colors.white, fontSize: 18),
                  ),
                  Text(
                    widget.email,
                    style: TextStyle(color: Colors.white, fontSize: 14),
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
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => BusinessCardUI(name: widget.name, email: widget.email, phone: widget.phone, location: widget.location, website: widget.website, designation: widget.designation, company: widget.company,)),
                );
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
              selected: true,
              onTap: () {
                Navigator.pop(context);
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
        title: Text("Calendar"),
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
      ),
      body: Container(
        child: SingleChildScrollView(
          child: Column(
            children: [
              SizedBox(height: 10),
              Align(
                alignment: Alignment.center,
                child: ElevatedButton(
                  onPressed: () {
                    // Just show the current selected date without showing a calendar picker
                    // This button will update when a date is selected from the calendar below
                  },
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.calendar_today, size: 16),
                      SizedBox(width: 8),
                      Text(
                        DateFormat('dd-MM-yyyy').format(today),
                        style: TextStyle(fontWeight: FontWeight.w500),
                      ),
                    ],
                  ),
                ),
              ),
              // Filter chips for leaves and meetings
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                child: Column(
                  children: [
                    Wrap(
                      spacing: 8.0,
                      children: [
                        FilterChip(
                          label: Text("Applied Leaves"),
                          selected: _showLeaves,
                          selectedColor: Color(0xffd2c7ed),
                          showCheckmark: false,
                          avatar: CircleAvatar(
                            backgroundColor: Colors.transparent,
                            child: Icon(Icons.work_off, color: Color(0xff8160c7), size: 18),
                          ),
                          onSelected: (bool selected) {
                            setState(() {
                              _showLeaves = selected;
                            });
                          },
                        ),
                        FilterChip(
                          label: Text("Scheduled Meetings"),
                          selected: _showMeetings,
                          selectedColor: Color(0xffd2c7ed),
                          showCheckmark: false,
                          avatar: CircleAvatar(
                            backgroundColor: Colors.transparent,
                            child: Icon(Icons.event, color: Color(0xff8160c7), size: 18),
                          ),
                          onSelected: (bool selected) {
                            setState(() {
                              _showMeetings = selected;
                            });
                          },
                        ),
                      ],
                    ),
                    // Calendar legend
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4.0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 8.0,
                                height: 8.0,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: Color(0xff8160c7),
                                ),
                              ),
                              SizedBox(width: 4),
                              Text('Meeting', style: TextStyle(fontSize: 12)),
                            ],
                          ),
                          SizedBox(width: 16),
                          Row(
                            children: [
                              Container(
                                width: 8.0,
                                height: 8.0,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: Colors.red,
                                ),
                              ),
                              SizedBox(width: 4),
                              Text('Leave', style: TextStyle(fontSize: 12)),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              TableCalendar(
                focusedDay: _focusedDay, // Use our tracked focused day
                headerStyle: HeaderStyle(
                  formatButtonVisible: false,
                  titleCentered: true,
                ),
                calendarStyle: CalendarStyle(
                  // Set cell margin to ensure consistent cell sizes
                  cellMargin: EdgeInsets.all(4.0),

                  // Today's date styling
                  todayDecoration: BoxDecoration(
                    color: Colors.green,
                    shape: BoxShape.circle,
                    // Add explicit size constraints to ensure consistent sizing
                    border: Border.all(color: Colors.green, width: 0),
                  ),
                  todayTextStyle: TextStyle(
                    color: Colors.white, 
                    fontSize: 16,
                    fontWeight: FontWeight.normal,
                  ),
                  // Selected day styling - important for consistency
                  selectedDecoration: BoxDecoration(
                    color: Color(0xff8160c7),
                    shape: BoxShape.circle,
                    // Add explicit size constraints to ensure consistent sizing
                    border: Border.all(color: Color(0xff8160c7), width: 0),
                  ),
                  selectedTextStyle: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.normal,
                  ),
                  // Styling for the range of dates
                  rangeHighlightColor: Color(0xffd2c7ed).withOpacity(0.6),
                  rangeStartDecoration: BoxDecoration(
                    color: Color(0xff8160c7),
                    shape: BoxShape.circle,
                    // Add explicit size constraints to ensure consistent sizing
                    border: Border.all(color: Color(0xff8160c7), width: 0),
                  ),
                  rangeStartTextStyle: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.normal,
                  ),
                  rangeEndDecoration: BoxDecoration(
                    color: Color(0xFF674C9F),
                    shape: BoxShape.circle,
                    // Add explicit size constraints to ensure consistent sizing
                    border: Border.all(color: Color(0xFF674C9F), width: 0),
                  ),
                  rangeEndTextStyle: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.normal,
                  ),
                  withinRangeTextStyle: TextStyle(
                    color: Colors.black,
                  ),
                ),
                availableGestures: AvailableGestures.all,
                firstDay: DateTime(2010, 1, 31),
                lastDay: DateTime(2030, 12, 31),
                onDaySelected: _onDaySelected,
                selectedDayPredicate: (day) => _userSelectedDay && isSameDay(day, today), // Only show selection after user selects a day
                //Date Range
                rangeStartDay: _rangeStart,
                rangeEndDay: _rangeEnd,
                onRangeSelected: _onRangeSelected,
                rangeSelectionMode: RangeSelectionMode.enforced,
                // Event loader to display markers under meeting dates
                eventLoader: _getEventsForDay,
                calendarBuilders: CalendarBuilders(
                  // Custom day builder to make dates appear unfocused when calendar opens
                  defaultBuilder: (context, day, focusedDay) {
                    return Container(
                      margin: const EdgeInsets.all(8.0),
                      alignment: Alignment.center,
                      width: 36.0, // Consistent size
                      height: 36.0, // Consistent size
                      child: Text(
                        day.day.toString(),
                        style: TextStyle(color: Colors.black87),
                      ),
                    );
                  },
                  // Custom builder for selected day to ensure consistent sizing
                  selectedBuilder: (context, day, focusedDay) {
                    return Container(
                      margin: const EdgeInsets.all(8.0),
                      alignment: Alignment.center,
                      width: 36.0, // Consistent size
                      height: 36.0, // Consistent size
                      decoration: BoxDecoration(
                        color: Color(0xff8160c7),
                        shape: BoxShape.circle,
                        // Adding a zero-width border to ensure consistent rendering
                        border: Border.all(color: Color(0xff8160c7), width: 0),
                      ),
                      child: Text(
                        day.day.toString(),
                        style: TextStyle(color: Colors.white),
                      ),
                    );
                  },
                  // Customize today's appearance
                  todayBuilder: (context, day, focusedDay) {
                    return Container(
                      margin: const EdgeInsets.all(8.0),
                      alignment: Alignment.center,
                      width: 36.0, // Consistent size
                      height: 36.0, // Consistent size
                      decoration: BoxDecoration(
                        color: Colors.green,
                        shape: BoxShape.circle,
                        // Adding a zero-width border to ensure consistent rendering 
                        border: Border.all(color: Colors.green, width: 0),
                      ),
                      child: Text(
                        day.day.toString(),
                        style: TextStyle(color: Colors.white),
                      ),
                    );
                  },
                  // Custom builders for range start and end to match today's circle size
                  rangeStartBuilder: (context, day, focusedDay) {
                    return Container(
                      margin: const EdgeInsets.all(8.0),
                      alignment: Alignment.center,
                      width: 36.0, // Consistent size
                      height: 36.0, // Consistent size
                      decoration: BoxDecoration(
                        color: Color(0xff8160c7),
                        shape: BoxShape.circle,
                        // Adding a zero-width border to ensure consistent rendering
                        border: Border.all(color: Color(0xff8160c7), width: 0),
                      ),
                      child: Text(
                        day.day.toString(),
                        style: TextStyle(color: Colors.white),
                      ),
                    );
                  },
                  rangeEndBuilder: (context, day, focusedDay) {
                    return Container(
                      margin: const EdgeInsets.all(8.0),
                      alignment: Alignment.center,
                      width: 36.0, // Consistent size
                      height: 36.0, // Consistent size
                      decoration: BoxDecoration(
                        color: Color(0xff8160c7),
                        shape: BoxShape.circle,
                        // Adding a zero-width border to ensure consistent rendering
                        border: Border.all(color: Color(0xff8160c7), width: 0),
                      ),
                      child: Text(
                        day.day.toString(),
                        style: TextStyle(color: Colors.white),
                      ),
                    );
                  },
                  // Custom marker builder
                  markerBuilder: (context, date, events) {
                    List<Widget> markers = [];
                    
                    // Add meeting marker if there are events
                    if (events.isNotEmpty) {
                      markers.add(_buildEventsMarker(date, events));
                    }
                    
                    // Add leave marker if there are leaves for this day
                    if (_hasLeavesForDay(date)) {
                      markers.add(_buildLeaveMarker(date));
                    }
                    
                    if (markers.isEmpty) {
                      return null;
                    }
                    
                    return Padding(
                      padding: const EdgeInsets.only(top: 3.0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: markers.map((marker) => Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 1.0),
                          child: marker,
                        )).toList(),
                      ),
                    );
                  },
                ),
              ),
              
              // Display section for leaves and meetings based on filter selection
              if (_showLeaves) _buildLeavesSection(),
              if (_showMeetings) _buildMeetingsSection(),
              
              // Add some space at the bottom for better spacing
              SizedBox(height: 20),
            ],
          ),
        ),
      ),
      //Apply for leaves and Schedule meetings
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Show a modal bottom sheet with options
          showModalBottomSheet(
            context: context,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
            ),
            builder: (BuildContext context) {
              return Container(
                padding: EdgeInsets.symmetric(vertical: 20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    //Apply for Leaves
                    ListTile(
                      leading: Icon(Icons.work_off, color: Color(0xff8160c7)),
                      title: Text('Apply for Leave'),
                      onTap: () {
                        Navigator.pop(context);
                        // Show leave application dialog
                        showDialog(
                          context: context,
                          builder: (context) {
                            bool isFullDay = _isFullDay;
                            bool isHalfDay = _isHalfDay;
                            return StatefulBuilder(
                              builder:
                                  (context, setState) => AlertDialog(
                                title: Text('Apply for Leave'),
                                content: SizedBox(
                                  width: 300,
                                  height: 360,
                                  child: Column(
                                    children: [
                                      // Add form fields for leave application
                                      SizedBox(height: 10),
                                      TextField(
                                        controller: _leaveReasonController,
                                        decoration: InputDecoration(
                                          labelText: 'Reason for leave',
                                          border: OutlineInputBorder(),
                                        ),
                                      ),
                                      SizedBox(height: 10),
                                      //Dropdown for leave type
                                      Align(
                                        alignment: Alignment.centerLeft,
                                        child: Text("Leave Type:"),
                                      ),
                                      Container(
                                        height: 55,
                                        decoration: BoxDecoration(
                                          borderRadius:
                                          BorderRadius.circular(4),
                                          border: Border.all(
                                            color: Colors.black38,
                                          ),
                                        ),
                                        child: DropdownButton<String>(
                                          items:
                                          _leaveTypes.map<
                                              DropdownMenuItem<String>
                                          >((String value) {
                                            return DropdownMenuItem<
                                                String
                                            >(
                                              value: value,
                                              child: Text(value),
                                            );
                                          }).toList(),
                                          value: _leaveType,
                                          underline: Container(),
                                          icon: Icon(
                                            Icons.arrow_drop_down,
                                          ),
                                          isExpanded: true,
                                          onChanged: (String? newValue) {
                                            setState(() {
                                              _leaveType =
                                              newValue!;
                                            });
                                          },
                                        ),
                                      ),
                                      SizedBox(height: 10),
                                      Align(
                                        alignment: Alignment.centerLeft,
                                        child: Text("Duration of Leave:"),
                                      ),
                                      Container(
                                        padding: EdgeInsets.all(12),
                                        decoration: BoxDecoration(
                                          borderRadius:
                                          BorderRadius.circular(8),
                                          border: Border.all(
                                            color: Colors.black38,
                                          ),
                                        ),
                                        child: Column(
                                          crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              "Selected Date:",
                                              style: TextStyle(
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                            _rangeStart != null &&
                                                _rangeEnd != null
                                                ? Row(
                                              children: [
                                                Icon(
                                                  Icons.date_range,
                                                  color: Color(
                                                    0xff8160c7,
                                                  ),
                                                  size: 16,
                                                ),
                                                SizedBox(width: 5),
                                                Expanded(
                                                  child: Text(
                                                    "${DateFormat('dd-MM-yyyy').format(_rangeStart!)} to ${DateFormat('dd-MM-yyyy').format(_rangeEnd!)}",
                                                    style: TextStyle(
                                                      fontWeight:
                                                      FontWeight
                                                          .w500,
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            )
                                                : Row(
                                              children: [
                                                Icon(
                                                  Icons.calendar_today,
                                                  color: Color(
                                                    0xff8160c7,
                                                  ),
                                                  size: 16,
                                                ),
                                                SizedBox(width: 5),
                                                Text(
                                                  DateFormat(
                                                    'dd-MM-yyyy',
                                                  ).format(today),
                                                  style: TextStyle(
                                                    fontWeight:
                                                    FontWeight.w500,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ],
                                        ),
                                      ),
                                      Row(
                                        children: [
                                          Checkbox(
                                            value: isHalfDay,
                                            onChanged: (value) {
                                              setState(() {
                                                isHalfDay = value!;
                                                if (isHalfDay) {
                                                  isFullDay = false;
                                                }
                                              });
                                            },
                                          ),
                                          Text("Half Day"),
                                        ],
                                      ),
                                      SizedBox(height: 5),
                                      TextField(
                                        controller: _leaveDescriptionController,
                                        decoration: InputDecoration(
                                          labelText: 'Description',
                                          border: OutlineInputBorder(),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                actions: [
                                  TextButton(
                                    onPressed: () => Navigator.pop(context),
                                    child: Text('Cancel'),
                                  ),
                                  TextButton(
                                    onPressed: () {
                                      // Process leave application
                                      _isFullDay = isFullDay;
                                      _isHalfDay = isHalfDay;
                                      
                                      // Get the selected date or date range
                                      final DateTime selectedDate = _rangeStart != null
                                          ? _rangeStart!  // Use start date for range
                                          : today;
                                      
                                      // Create a new leave entry
                                      final newLeave = {
                                        'type': _leaveType,
                                        'reason': _leaveReasonController.text,
                                        'description': _leaveDescriptionController.text,
                                        'date': selectedDate,
                                        'duration': isHalfDay ? 'Half Day' : 'Full Day',
                                        'dateRange': _rangeStart != null && _rangeEnd != null
                                            ? '${DateFormat('dd-MM-yyyy').format(_rangeStart!)} to ${DateFormat('dd-MM-yyyy').format(_rangeEnd!)}'
                                            : DateFormat('dd-MM-yyyy').format(selectedDate),
                                      };
                                      
                                      // Store DateTime objects for date ranges
                                      if (_rangeStart != null && _rangeEnd != null) {
                                        newLeave['rangeStart'] = _rangeStart!;
                                        newLeave['rangeEnd'] = _rangeEnd!;
                                      }
                                      
                                      // First close the dialog
                                      Navigator.pop(context);
                                      
                                      // Then add the leave in the parent's context to ensure proper state refresh
                                      // This refers to the state of the Calendar widget, not the dialog
                                      this.setState(() {
                                        _leaves.add(newLeave);
                                        // Reset the calendar state but don't trigger selection
                                        // Just update the date for display in the button
                                        DateTime now = DateTime.now();
                                        _focusedDay = now; // Update focused day to today
                                        today = now;
                                        _rangeStart = null;
                                        _rangeEnd = null;
                                        _userSelectedDay = false; // Important: unmark selection state
                                      });
                                      
                                      // Clear form fields
                                      _leaveReasonController.clear();
                                      _leaveDescriptionController.clear();
                                    },
                                    child: Text('Apply'),
                                  ),
                                ],
                              ),
                            );
                          },
                        );
                      },
                    ),
                    //Schedule Meetings
                    ListTile(
                      leading: Icon(Icons.event, color: Color(0xff8160c7)),
                      title: Text('Schedule a Meeting'),
                      onTap: () {
                        Navigator.pop(context);
                        showDialog(
                          context: context,
                          builder: (context) {
                            bool isOffline = _isOffline;
                            bool isOnline = _isOnline;
                            return StatefulBuilder(
                              builder:
                                  (context, setState) => AlertDialog(
                                title: Text('Schedule a Meeting'),
                                content: SizedBox(
                                  width: 300,
                                  child: SingleChildScrollView(
                                    child: Column(
                                      children: [
                                        // Add form fields for meeting scheduling
                                        Text(
                                          DateFormat(
                                            'dd-MM-yyyy',
                                          ).format(today),
                                        ),
                                        SizedBox(height: 10),
                                        TextField(
                                          controller: _meetingTitleController,
                                          decoration: InputDecoration(
                                            labelText: 'Meeting Title',
                                            border: OutlineInputBorder(),
                                          ),
                                        ),
                                        SizedBox(height: 10),
                                        TextField(
                                          controller: _meetingDescController,
                                          decoration: InputDecoration(
                                            labelText: 'Description',
                                            border: OutlineInputBorder(),
                                          ),
                                        ),
                                        SizedBox(height: 10),
                                        Align(
                                          alignment: Alignment.centerLeft,
                                          child: Text("Participants:"),
                                        ),
                                        Container(
                                          height: 55,
                                          decoration: BoxDecoration(
                                            borderRadius:
                                            BorderRadius.circular(4),
                                            border: Border.all(
                                              color: Colors.black38,
                                            ),
                                          ),
                                          child: DropdownButton<String>(
                                            items:
                                            _meetingTypes.map<
                                                DropdownMenuItem<String>
                                            >((String value) {
                                              return DropdownMenuItem<
                                                  String
                                              >(
                                                value: value,
                                                child: Text(value),
                                              );
                                            }).toList(),
                                            value: _meetingType,
                                            underline: Container(),
                                            icon: Icon(
                                              Icons.arrow_drop_down,
                                            ),
                                            isExpanded: true,
                                            onChanged: (String? newValue) {
                                              setState(() {
                                                _meetingType = newValue!;
                                              });
                                            },
                                          ),
                                        ),
                                        SizedBox(height: 10),
                                        Row(
                                          children: [
                                            // Start time column
                                            Expanded(
                                              child: Column(
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                  // Start time label
                                                  Padding(
                                                    padding: const EdgeInsets.only(bottom: 4.0, left: 4.0),
                                                    child: Text(
                                                      "Start Time",
                                                    ),
                                                  ),
                                                  // Start time picker button
                                                  InkWell(
                                                    onTap: () {
                                                      _selectStartTime(context, setState);
                                                    },
                                                    child: Container(
                                                      padding: EdgeInsets.symmetric(vertical: 12, horizontal: 15),
                                                      decoration: BoxDecoration(
                                                        borderRadius: BorderRadius.circular(4),
                                                        border: Border.all(color: Colors.black38),
                                                      ),
                                                      child: Center(
                                                        child: Text(
                                                          _startTime.format(context),
                                                          style: TextStyle(fontSize: 16),
                                                        ),
                                                      ),
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ),
                                            SizedBox(width: 10), // Space between the time pickers
                                            // End time column
                                            Expanded(
                                              child: Column(
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                  // End time label
                                                  Padding(
                                                    padding: const EdgeInsets.only(bottom: 4.0, left: 4.0),
                                                    child: Text(
                                                      "End Time",
                                                    ),
                                                  ),
                                                  // End time picker button
                                                  InkWell(
                                                    onTap: () {
                                                      _selectEndTime(context, setState);
                                                    },
                                                    child: Container(
                                                      padding: EdgeInsets.symmetric(vertical: 12, horizontal: 15),
                                                      decoration: BoxDecoration(
                                                        borderRadius: BorderRadius.circular(4),
                                                        border: Border.all(color: Colors.black38),
                                                      ),
                                                      child: Center(
                                                        child: Text(
                                                          _endTime.format(context),
                                                          style: TextStyle(fontSize: 16),
                                                        ),
                                                      ),
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ],
                                        ),
                                        SizedBox(height: 10),
                                        Align(
                                          alignment: Alignment.centerLeft,
                                          child: Text("Meeting Mode:"),
                                        ),

                                        //Checkboxes
                                        Row(
                                          children: [
                                            Checkbox(
                                              value: isOnline,
                                              onChanged: (value) {
                                                setState(() {
                                                  isOnline = value!;
                                                  if (isOnline) {
                                                    isOffline = false;
                                                  }
                                                });
                                              },
                                            ),
                                            Text("Online"),
                                            Checkbox(
                                              value: isOffline,
                                              onChanged: (value) {
                                                setState(() {
                                                  isOffline = value!;
                                                  if (isOffline) {
                                                    isOnline = false;
                                                  }
                                                });
                                              },
                                            ),
                                            Text("Offline"),
                                          ],
                                        ),
                                        Align(
                                          alignment: Alignment.centerLeft,
                                          child: Text("Reminder:"),
                                        ),
                                        //drop down menu for Reminder
                                        Container(
                                          height: 55,
                                          decoration: BoxDecoration(
                                            borderRadius:
                                            BorderRadius.circular(4),
                                            border: Border.all(
                                              color: Colors.black38,
                                            ),
                                          ),
                                          child: DropdownButton<String>(
                                            items:
                                            _reminderDurations.map<
                                                DropdownMenuItem<String>
                                            >((String value) {
                                              return DropdownMenuItem<
                                                  String
                                              >(
                                                value: value,
                                                child: Text(value),
                                              );
                                            }).toList(),
                                            value: _reminderDuration,
                                            underline: Container(),
                                            icon: Icon(
                                              Icons.arrow_drop_down,
                                            ),
                                            isExpanded: true,
                                            onChanged: (String? newValue) {
                                              setState(() {
                                                _reminderDuration =
                                                newValue!;
                                              });
                                            },
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                                actions: [
                                  TextButton(
                                    onPressed: () => Navigator.pop(context),
                                    child: Text('Cancel'),
                                  ),
                                  TextButton(
                                    onPressed: () {
                                      // Process meeting scheduling
                                      _isOnline = isOnline;
                                      _isOffline = isOffline;
                                      
                                      // Create a new meeting entry
                                      final newMeeting = {
                                        'title': _meetingTitleController.text.isNotEmpty ? _meetingTitleController.text : 'Untitled Meeting',
                                        'description': _meetingDescController.text,
                                        'date': today,
                                        'startTime': _startTime,
                                        'endTime': _endTime, 
                                        'participant': _meetingType,
                                        'mode': isOnline ? 'Online' : 'Offline',
                                        'reminder': _reminderDuration
                                      };
                                      
                                      // First close the dialog
                                      Navigator.pop(context);

                                      // Then add the meeting in the parent's context to ensure proper state refresh
                                      // This refers to the state of the Calendar widget, not the dialog
                                      this.setState(() {
                                        _meetings.add(newMeeting);
                                        // Reset the calendar state but don't trigger selection
                                        // Just update the date for display in the button
                                        DateTime now = DateTime.now();
                                        _focusedDay = now; // Update focused day to today
                                        today = now; 
                                        _rangeStart = null;
                                        _rangeEnd = null;
                                        _userSelectedDay = false; // Important: unmark selection state
                                      });
                                      
                                      // Clear form fields
                                      _meetingTitleController.clear();
                                      _meetingDescController.clear();
                                    },
                                    child: Text('Schedule'),
                                  ),
                                ],
                              ),
                            );
                          },
                        );
                      },
                    ),
                  ],
                ),
              );
            },
          );
        },
        backgroundColor: Color(0xff8160c7),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
        child: Icon(Icons.add, color: Colors.white),
      ),
    );
  }
  
  @override
  void dispose() {
    // Clean up the controllers when the widget is disposed
    _meetingTitleController.dispose();
    _meetingDescController.dispose();
    _leaveReasonController.dispose();
    _leaveDescriptionController.dispose();
    super.dispose();
  }
}
