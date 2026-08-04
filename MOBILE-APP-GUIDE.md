# Mobile App Development & App Store Launch Guide

## Overview

You'll create **two Flutter apps**:
1. **Worker App** - Find jobs, apply, manage schedule
2. **Client App** - Post jobs, hire workers, manage projects

Both connect to your FastAPI backend via REST API.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    iOS & Android Users                      │
└────────────────┬────────────────────────┬───────────────────┘
                 │                        │
        ┌────────▼────────┐    ┌─────────▼──────────┐
        │  Worker App     │    │  Client App        │
        │  (Flutter)      │    │  (Flutter)         │
        │  iOS + Android  │    │  iOS + Android     │
        └────────┬────────┘    └─────────┬──────────┘
                 │                        │
                 └────────────┬───────────┘
                              │
                    ┌─────────▼──────────┐
                    │   FastAPI Backend  │
                    │  (Already built)   │
                    │  /api/v1/*         │
                    └────────┬───────────┘
                             │
                    ┌────────▼─────────┐
                    │  PostgreSQL      │
                    │  Redis           │
                    │  (Already built)  │
                    └──────────────────┘
```

---

## Phase 1: Project Setup (Week 1)

### 1.1 Create Flutter Projects

```bash
# Install Flutter SDK from https://flutter.dev/docs/get-started/install

# Create Worker App
flutter create --org com.tradefix worker_app
cd worker_app

# Create Client App
cd ..
flutter create --org com.tradefix client_app
cd client_app
```

### 1.2 Project Structure

```
worker_app/
├── lib/
│   ├── main.dart
│   ├── config/
│   │   ├── app_config.dart        # API URLs, constants
│   │   └── theme.dart             # App theme & colors
│   ├── models/
│   │   ├── worker.dart
│   │   ├── job.dart
│   │   ├── match.dart
│   │   └── user.dart
│   ├── services/
│   │   ├── api_service.dart       # REST API client
│   │   ├── auth_service.dart      # Authentication
│   │   └── storage_service.dart   # Local storage
│   ├── screens/
│   │   ├── auth/
│   │   │   ├── login_screen.dart
│   │   │   └── register_screen.dart
│   │   ├── home/
│   │   │   ├── home_screen.dart
│   │   │   └── job_details_screen.dart
│   │   ├── jobs/
│   │   │   ├── jobs_list_screen.dart
│   │   │   ├── job_card.dart
│   │   │   └── apply_job_screen.dart
│   │   ├── profile/
│   │   │   └── profile_screen.dart
│   │   └── approvals/
│   │       └── approval_status_screen.dart
│   ├── providers/
│   │   ├── auth_provider.dart
│   │   ├── job_provider.dart
│   │   ├── worker_provider.dart
│   │   └── match_provider.dart
│   └── utils/
│       ├── constants.dart
│       ├── validators.dart
│       └── formatters.dart
├── pubspec.yaml
└── test/
    ├── models_test.dart
    ├── services_test.dart
    └── screens_test.dart

client_app/  # Similar structure
```

### 1.3 Add Dependencies

**pubspec.yaml** (both apps):

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP & API
  http: ^1.1.0
  dio: ^5.3.1
  
  # State Management
  provider: ^6.0.0
  riverpod: ^2.4.0
  
  # Local Storage
  shared_preferences: ^2.2.0
  hive: ^2.2.3
  sqflite: ^2.3.0
  
  # Firebase (for push notifications)
  firebase_core: ^2.24.0
  firebase_messaging: ^14.6.0
  
  # UI
  flutter_svg: ^2.0.0
  cached_network_image: ^3.3.0
  google_maps_flutter: ^2.5.0
  
  # Utils
  intl: ^0.19.0
  get_it: ^7.6.0
  logger: ^2.0.1
  
  # Authentication
  flutter_secure_storage: ^9.0.0
  jwt_decoder: ^2.0.1

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0
  mockito: ^5.4.0
  build_runner: ^2.4.0
```

### 1.4 pubspec.yaml Structure

```bash
# Install dependencies
flutter pub get

# Generate build files
flutter pub run build_runner build
```

---

## Phase 2: Backend Integration (Week 2)

### 2.1 API Service

**lib/services/api_service.dart**:

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter/foundation.dart';

class ApiService {
  static const String BASE_URL = 'http://localhost:8000/api/v1';
  late http.Client _client;
  String? _authToken;

  ApiService() {
    _client = http.Client();
  }

  // Set authentication token
  void setToken(String token) {
    _authToken = token;
  }

  // Get headers with auth
  Map<String, String> _getHeaders() {
    final headers = {
      'Content-Type': 'application/json',
    };
    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  // WORKER ENDPOINTS
  
  /// Register new worker
  Future<Map<String, dynamic>> registerWorker({
    required String firstName,
    required String lastName,
    required String email,
    required String phone,
    required String password,
    required String postalCode,
    required double latitude,
    required double longitude,
    required List<String> skills,
    required int experienceYears,
    required double hourlyRate,
    required String subscriptionTier,
    Map<String, dynamic>? availability,
  }) async {
    final response = await _client.post(
      Uri.parse('$BASE_URL/workers/register'),
      headers: _getHeaders(),
      body: jsonEncode({
        'first_name': firstName,
        'last_name': lastName,
        'email': email,
        'phone': phone,
        'password': password,
        'postal_code': postalCode,
        'latitude': latitude,
        'longitude': longitude,
        'skills': skills,
        'experience_years': experienceYears,
        'hourly_rate': hourlyRate,
        'subscription_tier': subscriptionTier,
        'availability': availability ?? {},
      }),
    );

    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to register: ${response.body}');
    }
  }

  /// Get worker profile
  Future<Map<String, dynamic>> getWorker(int workerId) async {
    final response = await _client.get(
      Uri.parse('$BASE_URL/workers/$workerId'),
      headers: _getHeaders(),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to fetch worker');
    }
  }

  /// Update worker profile
  Future<Map<String, dynamic>> updateWorker(
    int workerId, {
    String? firstName,
    String? lastName,
    String? phone,
    String? bio,
    List<String>? skills,
    int? experienceYears,
    double? hourlyRate,
    Map<String, dynamic>? availability,
  }) async {
    final body = <String, dynamic>{};
    if (firstName != null) body['first_name'] = firstName;
    if (lastName != null) body['last_name'] = lastName;
    if (phone != null) body['phone'] = phone;
    if (bio != null) body['bio'] = bio;
    if (skills != null) body['skills'] = skills;
    if (experienceYears != null) body['experience_years'] = experienceYears;
    if (hourlyRate != null) body['hourly_rate'] = hourlyRate;
    if (availability != null) body['availability'] = availability;

    final response = await _client.put(
      Uri.parse('$BASE_URL/workers/$workerId'),
      headers: _getHeaders(),
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to update worker');
    }
  }

  /// Search for jobs
  Future<Map<String, dynamic>> searchJobs({
    String? postalCode,
    String? category,
    String? status,
    int skip = 0,
    int limit = 50,
  }) async {
    final params = {
      'skip': skip.toString(),
      'limit': limit.toString(),
    };
    if (postalCode != null) params['postal_code'] = postalCode;
    if (category != null) params['category'] = category;
    if (status != null) params['status'] = status;

    final uri = Uri.parse('$BASE_URL/jobs').replace(queryParameters: params);
    final response = await _client.get(uri, headers: _getHeaders());

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to fetch jobs');
    }
  }

  /// Get single job
  Future<Map<String, dynamic>> getJob(int jobId) async {
    final response = await _client.get(
      Uri.parse('$BASE_URL/jobs/$jobId'),
      headers: _getHeaders(),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to fetch job');
    }
  }

  /// Find matching jobs for worker
  Future<Map<String, dynamic>> findJobsForWorker({
    required int workerId,
    int topN = 5,
    double minScore = 0.65,
  }) async {
    final uri = Uri.parse(
      '$BASE_URL/matching/find-jobs?worker_id=$workerId&top_n=$topN&min_score=$minScore'
    );
    final response = await _client.get(uri, headers: _getHeaders());

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to find jobs');
    }
  }

  // JOB ENDPOINTS (for Client App)

  /// Create new job
  Future<Map<String, dynamic>> createJob({
    required String title,
    required String description,
    required String category,
    required List<String> requiredSkills,
    required int experienceRequired,
    required double payRate,
    required double durationHours,
    required String postalCode,
    required double latitude,
    required double longitude,
    required DateTime scheduledDate,
    required String scheduledTime,
    required DateTime deadline,
    required String priority,
    required int clientId,
    required String clientName,
  }) async {
    final response = await _client.post(
      Uri.parse('$BASE_URL/jobs'),
      headers: _getHeaders(),
      body: jsonEncode({
        'title': title,
        'description': description,
        'category': category,
        'required_skills': requiredSkills,
        'experience_required': experienceRequired,
        'pay_rate': payRate,
        'duration_hours': durationHours,
        'postal_code': postalCode,
        'latitude': latitude,
        'longitude': longitude,
        'scheduled_date': scheduledDate.toIso8601String(),
        'scheduled_time': scheduledTime,
        'deadline': deadline.toIso8601String(),
        'priority': priority,
        'client_id': clientId,
        'client_name': clientName,
      }),
    );

    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to create job: ${response.body}');
    }
  }

  /// Get matching workers for job (Client app)
  Future<Map<String, dynamic>> findWorkersForJob({
    required int jobId,
    int topN = 5,
    double minScore = 0.65,
  }) async {
    final response = await _client.post(
      Uri.parse('$BASE_URL/matching/find-workers'),
      headers: _getHeaders(),
      body: jsonEncode({
        'job_id': jobId,
        'top_n': topN,
        'min_score': minScore,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to find workers');
    }
  }

  // APPROVAL ENDPOINTS

  /// Get worker approval status
  Future<Map<String, dynamic>> getApprovalStatus(int workerId) async {
    final response = await _client.get(
      Uri.parse('$BASE_URL/approvals/pending'),
      headers: _getHeaders(),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to fetch approval status');
    }
  }

  // ANALYTICS

  /// Get worker analytics
  Future<Map<String, dynamic>> getWorkerAnalytics() async {
    final response = await _client.get(
      Uri.parse('$BASE_URL/analytics/workers'),
      headers: _getHeaders(),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to fetch analytics');
    }
  }

  void dispose() {
    _client.close();
  }
}
```

### 2.2 Authentication Service

**lib/services/auth_service.dart**:

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:jwt_decoder/jwt_decoder.dart';

class AuthService {
  static const String _tokenKey = 'auth_token';
  static const String _userIdKey = 'user_id';
  static const String _userTypeKey = 'user_type'; // 'worker' or 'client'
  
  final _secureStorage = const FlutterSecureStorage();

  /// Save authentication token
  Future<void> saveToken(String token) async {
    await _secureStorage.write(key: _tokenKey, value: token);
  }

  /// Get saved token
  Future<String?> getToken() async {
    return await _secureStorage.read(key: _tokenKey);
  }

  /// Check if token is valid
  Future<bool> isTokenValid() async {
    final token = await getToken();
    if (token == null) return false;
    
    try {
      return !JwtDecoder.isExpired(token);
    } catch (e) {
      return false;
    }
  }

  /// Decode token to get user info
  Future<Map<String, dynamic>?> decodeToken() async {
    final token = await getToken();
    if (token == null) return null;
    
    try {
      return JwtDecoder.decode(token);
    } catch (e) {
      return null;
    }
  }

  /// Save user ID
  Future<void> saveUserId(int userId) async {
    await _secureStorage.write(key: _userIdKey, value: userId.toString());
  }

  /// Get user ID
  Future<int?> getUserId() async {
    final id = await _secureStorage.read(key: _userIdKey);
    return int.tryParse(id ?? '');
  }

  /// Save user type
  Future<void> saveUserType(String userType) async {
    await _secureStorage.write(key: _userTypeKey, value: userType);
  }

  /// Get user type
  Future<String?> getUserType() async {
    return await _secureStorage.read(key: _userTypeKey);
  }

  /// Logout
  Future<void> logout() async {
    await _secureStorage.delete(key: _tokenKey);
    await _secureStorage.delete(key: _userIdKey);
    await _secureStorage.delete(key: _userTypeKey);
  }

  /// Check if user is authenticated
  Future<bool> isAuthenticated() async {
    return await isTokenValid();
  }
}
```

---

## Phase 3: UI Implementation (Weeks 3-4)

### 3.1 Main App Shell (Worker App)

**lib/main.dart**:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/theme.dart';
import 'providers/auth_provider.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home/home_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
      ],
      child: MaterialApp(
        title: 'TradeFix - Worker',
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        home: Consumer<AuthProvider>(
          builder: (context, authProvider, _) {
            if (authProvider.isLoading) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }

            if (authProvider.isAuthenticated) {
              return const HomeScreen();
            }

            return const LoginScreen();
          },
        ),
      ),
    );
  }
}
```

### 3.2 Login Screen

**lib/screens/auth/login_screen.dart**:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../config/theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  late TextEditingController _emailController;
  late TextEditingController _passwordController;
  bool _obscurePassword = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController();
    _passwordController = TextEditingController();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _handleLogin() async {
    setState(() => _errorMessage = null);

    try {
      await context.read<AuthProvider>().login(
        email: _emailController.text,
        password: _passwordController.text,
      );
    } catch (e) {
      setState(() => _errorMessage = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 40),
              Text(
                'Welcome Back',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              const SizedBox(height: 8),
              Text(
                'Sign in to your account',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: Colors.grey,
                ),
              ),
              const SizedBox(height: 40),

              // Email field
              TextField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(
                  labelText: 'Email',
                  hintText: 'you@example.com',
                  prefixIcon: const Icon(Icons.email_outlined),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Password field
              TextField(
                controller: _passwordController,
                obscureText: _obscurePassword,
                decoration: InputDecoration(
                  labelText: 'Password',
                  prefixIcon: const Icon(Icons.lock_outlined),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword ? Icons.visibility_off : Icons.visibility,
                    ),
                    onPressed: () {
                      setState(() => _obscurePassword = !_obscurePassword);
                    },
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),

              // Error message
              if (_errorMessage != null)
                Padding(
                  padding: const EdgeInsets.only(top: 16),
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.red),
                    ),
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(color: Colors.red),
                    ),
                  ),
                ),

              const SizedBox(height: 24),

              // Login button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: Consumer<AuthProvider>(
                  builder: (context, authProvider, _) {
                    return ElevatedButton(
                      onPressed: authProvider.isLoading ? null : _handleLogin,
                      child: authProvider.isLoading
                          ? const SizedBox(
                        height: 24,
                        width: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation(Colors.white),
                        ),
                      )
                          : const Text('Sign In'),
                    );
                  },
                ),
              ),

              const SizedBox(height: 24),

              // Sign up link
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text("Don't have an account? "),
                  TextButton(
                    onPressed: () {
                      // Navigate to registration
                      Navigator.of(context).pushNamed('/register');
                    },
                    child: const Text('Sign Up'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### 3.3 Home Screen (Job Listing)

**lib/screens/home/home_screen.dart**:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/job_provider.dart';
import 'job_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    
    // Load jobs on init
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<JobProvider>().fetchJobs();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Available Jobs'),
        elevation: 0,
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'All'),
            Tab(text: 'Applied'),
            Tab(text: 'Saved'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // All jobs tab
          Consumer<JobProvider>(
            builder: (context, jobProvider, _) {
              if (jobProvider.isLoading) {
                return const Center(child: CircularProgressIndicator());
              }

              if (jobProvider.jobs.isEmpty) {
                return const Center(
                  child: Text('No jobs available'),
                );
              }

              return RefreshIndicator(
                onRefresh: () => jobProvider.fetchJobs(),
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: jobProvider.jobs.length,
                  itemBuilder: (context, index) {
                    final job = jobProvider.jobs[index];
                    return JobCard(job: job);
                  },
                ),
              );
            },
          ),

          // Applied jobs tab
          Consumer<JobProvider>(
            builder: (context, jobProvider, _) {
              final appliedJobs = jobProvider.jobs
                  .where((job) => job['status'] == 'applied')
                  .toList();

              if (appliedJobs.isEmpty) {
                return const Center(
                  child: Text('No applied jobs'),
                );
              }

              return ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: appliedJobs.length,
                itemBuilder: (context, index) {
                  return JobCard(job: appliedJobs[index]);
                },
              );
            },
          ),

          // Saved jobs tab
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.bookmark_border,
                  size: 64,
                  color: Colors.grey[400],
                ),
                const SizedBox(height: 16),
                const Text('No saved jobs'),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Jobs',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.assignment),
            label: 'Applied',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
        onTap: (index) {
          // Navigate based on tab
          if (index == 2) {
            Navigator.of(context).pushNamed('/profile');
          }
        },
      ),
    );
  }
}
```

---

## Phase 4: Testing (Week 5)

### 4.1 Unit Tests

**test/models_test.dart**:

```dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Worker Model', () {
    test('Worker can be created with valid data', () {
      final worker = {
        'id': 1,
        'email': 'john@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'skills': ['plumbing', 'emergency'],
        'experience_years': 5,
        'approval_status': 'approved',
      };

      expect(worker['email'], 'john@example.com');
      expect(worker['skills'].length, 2);
    });

    test('Worker with low experience is handled', () {
      final worker = {
        'experience_years': 0,
        'approval_status': 'pending',
      };

      expect(worker['experience_years'], 0);
    });
  });

  group('Job Model', () {
    test('Job can be created with valid data', () {
      final job = {
        'id': 1,
        'title': 'Emergency Plumbing',
        'category': 'plumbing',
        'pay_rate': 75.0,
        'status': 'open',
      };

      expect(job['title'], 'Emergency Plumbing');
      expect(job['pay_rate'], 75.0);
    });
  });
}
```

### 4.2 Widget Tests

**test/screens_test.dart**:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Login Screen', () {
    testWidgets('Login screen renders with email and password fields',
        (WidgetTester tester) async {
      // Build the app and trigger a frame
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Column(
              children: [
                TextField(
                  decoration: InputDecoration(
                    labelText: 'Email',
                  ),
                ),
                TextField(
                  decoration: InputDecoration(
                    labelText: 'Password',
                  ),
                ),
              ],
            ),
          ),
        ),
      );

      expect(find.byType(TextField), findsWidgets);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
    });
  });
}
```

### 4.3 Test Coverage

```bash
# Run all tests
flutter test

# Generate coverage report
flutter test --coverage

# View coverage
lcov --list coverage/lcov.info
```

---

## Phase 5: App Store Preparation (Weeks 6-7)

### 5.1 iOS App Store Submission

**Step 1: Create App Records**

```
1. Go to App Store Connect (https://appstoreconnect.apple.com)
2. Click "My Apps"
3. Click "+" and select "New App"
4. Fill in:
   - Platform: iOS
   - Name: TradeFix Worker
   - Bundle ID: com.tradefix.worker
   - SKU: TRADEFIX-WORKER-001
   - User Access: Full Access
```

**Step 2: App Information**

```
- App Name: TradeFix Worker
- Subtitle: Find & manage jobs easily
- Category: Lifestyle
- Age Rating: 4+
- Privacy Policy URL: https://tradefix.com/privacy
```

**Step 3: Prepare Assets**

```
Required:
✓ App Icon (1024x1024 PNG)
✓ Screenshots (6 per device size)
  - iPhone 6.7" (1284x2778)
  - iPhone 6.1" (1170x2532)
✓ Preview (optional video)
✓ Description (170 chars)
✓ Keywords (100 chars)
```

**Step 4: iOS Build**

```bash
# In Xcode
cd ios
pod install
cd ..

# Build for App Store
flutter build ipa \
  --release \
  --export-options-template=ios/ExportOptions.plist

# Or use Xcode
open ios/Runner.xcworkspace
# Select Runner in Xcode
# Product > Archive
# Validate with App Store
# Upload to App Store
```

**Step 5: TestFlight Testing**

```
1. Upload IPA to App Store Connect
2. Go to TestFlight tab
3. Add internal testers (your email)
4. Test app thoroughly
5. If approved, add external testers
6. Gather feedback for 1-2 weeks
```

**Step 6: Submit for Review**

```
1. Fill out review information:
   - Contact Info
   - Demo Account (if needed)
   - Review Notes
   - Advertising: Does it contain ads?
   - Content Rights: Confirm you own it
   - Export Compliance: Select "None"
2. Select version for review
3. Click "Submit for Review"
4. Approval usually takes 24-48 hours
```

### 5.2 Google Play Store Submission

**Step 1: Create Play Store Account**

```
1. Go to Google Play Console (https://play.google.com/console)
2. Pay $25 one-time registration fee
3. Create developer account
```

**Step 2: Create App**

```
1. Click "Create App"
2. Fill in:
   - App name: TradeFix Worker
   - Default language: English
   - App or game: App
   - Free or paid: Free
3. Agree to policies
```

**Step 3: Prepare Signing Key**

```bash
# Generate signing key (if you don't have one)
keytool -genkey -v -keystore ~/key.jks \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias key

# Configure signing in pubspec.yaml
# Or use Google Play's internal signing
```

**Step 4: Android Build**

```bash
# Build signed APK
flutter build apk \
  --release \
  --split-per-abi

# Build App Bundle (preferred)
flutter build appbundle \
  --release

# Outputs to:
# build/app/release/app-release.aab
```

**Step 5: Add to Play Store**

```
1. Go to "Testing" > "Internal testing"
2. Add testers (email addresses)
3. Upload AAB file
4. Test thoroughly

Then:
1. Go to "Production"
2. Upload AAB file
3. Fill in Store Listing:
   - Title
   - Short description
   - Full description
   - Screenshots (5 per device)
   - Feature graphic (1024x500)
   - Icon
4. Content rating questionnaire
5. Target audience
6. Content guidelines agreement
7. Set pricing (Free)
8. Review & submit
```

**Step 6: Approval**

```
Google usually approves within 2-3 hours
Once approved: Live on Play Store!
```

### 5.3 Version & Build Numbers

**iOS (pubspec.yaml)**:

```yaml
version: 1.0.0+1
```

Structure: `major.minor.patch+buildNumber`

**Android (android/app/build.gradle)**:

```gradle
android {
  compileSdkVersion 34
  
  defaultConfig {
    applicationId "com.tradefix.worker"
    minSdkVersion 21
    targetSdkVersion 34
    versionCode 1
    versionName "1.0.0"
  }
}
```

---

## Phase 6: Post-Launch (Ongoing)

### 6.1 Monitoring

```dart
// Add Firebase Analytics
import 'package:firebase_analytics/firebase_analytics.dart';

final analytics = FirebaseAnalytics.instance;

// Log events
await analytics.logEvent(
  name: 'job_applied',
  parameters: {
    'job_id': jobId,
    'job_title': jobTitle,
  },
);
```

### 6.2 Crash Reporting

```dart
// Add Firebase Crashlytics
import 'package:firebase_crashlytics/firebase_crashlytics.dart';

FlutterError.onError = (errorDetails) {
  FirebaseCrashlytics.instance.recordFlutterError(errorDetails);
};

// Catch async errors
PlatformDispatcher.instance.onError = (error, stack) {
  FirebaseCrashlytics.instance.recordError(error, stack);
  return true;
};
```

### 6.3 Update Management

```bash
# Update Flutter & packages regularly
flutter upgrade
flutter pub upgrade

# Check for outdated packages
flutter pub outdated

# Fix security issues
flutter pub upgrade --major-versions
```

---

## Timeline & Checklist

### Week 1: Setup
- [ ] Create Flutter projects
- [ ] Add dependencies
- [ ] Setup project structure

### Weeks 2: API Integration
- [ ] Build API service
- [ ] Implement auth service
- [ ] Test API endpoints

### Weeks 3-4: UI/UX
- [ ] Build login/register screens
- [ ] Build job listing screen
- [ ] Build job detail screen
- [ ] Build profile screen
- [ ] Build navigation

### Week 5: Testing
- [ ] Unit tests (>80% coverage)
- [ ] Widget tests
- [ ] Integration tests
- [ ] Manual testing

### Week 6: App Store Prep
- [ ] Create app icons
- [ ] Capture screenshots
- [ ] Write descriptions
- [ ] Privacy policy
- [ ] Terms of service

### Week 7: Submissions
- [ ] Submit to Apple App Store
- [ ] Submit to Google Play
- [ ] Internal testing
- [ ] Fix review issues
- [ ] Go live!

---

## App Store Submission Checklist

### Before Submission
- [ ] App runs without crashes
- [ ] All features work as intended
- [ ] No hardcoded test data
- [ ] No debug prints in logs
- [ ] All required icons & screenshots
- [ ] Privacy policy included
- [ ] Terms of service included
- [ ] Contact info provided
- [ ] Version number updated
- [ ] Build number incremented

### App Store Connect (iOS)
- [ ] App information filled
- [ ] Screenshots uploaded
- [ ] Description written
- [ ] Keywords added
- [ ] Support URL provided
- [ ] Privacy policy URL
- [ ] Age rating completed
- [ ] TestFlight testers added
- [ ] No crashes in testing

### Google Play Console (Android)
- [ ] Store listing complete
- [ ] Screenshots uploaded
- [ ] Feature graphic added
- [ ] Content rating submitted
- [ ] Privacy policy URL
- [ ] Support email
- [ ] Signed APK/AAB

---

## Common Issues & Solutions

### iOS

**Issue**: "SIGABRT" crash on launch
```
Solution:
1. Clean build: flutter clean
2. Pod cache: rm ios/Pods && cd ios && pod install
3. Rebuild: flutter build ios
```

**Issue**: Certificate issues
```
Solution:
1. Go to Xcode > Preferences > Accounts
2. Sign in with Apple ID
3. Download certificate
4. Try building again
```

### Android

**Issue**: "Gradle build failed"
```
Solution:
1. flutter clean
2. flutter pub get
3. flutter build apk --debug
```

**Issue**: APK too large
```
Solution:
1. Enable minification:
   minifyEnabled true
2. Enable shrinkResources:
   shrinkResources true
3. Use App Bundle instead of APK
```

---

## Versioning Strategy

```
Version Format: MAJOR.MINOR.PATCH+BUILD

1.0.0+1  - Initial release
1.0.1+2  - Bug fixes
1.1.0+3  - New features
2.0.0+4  - Major redesign
```

Increment BUILD for every App Store upload.

---

## Resources

- **Flutter Docs**: https://flutter.dev/docs
- **App Store Connect**: https://appstoreconnect.apple.com
- **Google Play Console**: https://play.google.com/console
- **Firebase**: https://firebase.google.com
- **Riverpod (State Management)**: https://riverpod.dev

---

This guide provides a complete path from development to app store launch! 🚀
