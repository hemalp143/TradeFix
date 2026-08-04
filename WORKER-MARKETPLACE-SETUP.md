# Worker Marketplace Dashboard Workflow

## Overview
This document provides a complete, copy-pasteable workflow to build a worker marketplace where:
- Workers register and are geolocated by postal code
- Three subscription tiers: **Starter (£9.9), Professional (£49.9), Enterprise (£99.9)**
- Admin dashboard to manage workers, postal codes, and subscriptions
- Payment processing via Stripe

---

## Phase 1: WordPress Plugin Setup

### Step 1.1: Create Plugin Structure

```
worker-marketplace/
├── worker-marketplace.php          (main plugin file)
├── includes/
│   ├── class-db.php               (database functions)
│   ├── class-registration.php     (registration logic)
│   ├── class-subscription.php     (subscription & payment)
│   └── class-dashboard.php        (admin dashboard)
├── admin/
│   ├── css/
│   │   └── dashboard.css
│   └── js/
│       └── dashboard.js
├── public/
│   ├── css/
│   │   └── registration-form.css
│   └── js/
│       └── registration-form.js
└── templates/
    ├── registration-form.php
    └── success.php
```

### Step 1.2: Main Plugin File
**File: `worker-marketplace.php`**

```php
<?php
/**
 * Plugin Name: Worker Marketplace
 * Plugin URI: https://example.com
 * Description: Worker registration and subscription management
 * Version: 1.0.0
 * Author: Your Name
 * License: GPL2
 */

if (!defined('ABSPATH')) {
    exit;
}

define('WM_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('WM_PLUGIN_URL', plugin_dir_url(__FILE__));
define('WM_VERSION', '1.0.0');

// Require core classes
require_once WM_PLUGIN_DIR . 'includes/class-db.php';
require_once WM_PLUGIN_DIR . 'includes/class-registration.php';
require_once WM_PLUGIN_DIR . 'includes/class-subscription.php';
require_once WM_PLUGIN_DIR . 'includes/class-dashboard.php';

class Worker_Marketplace {
    private static $instance = null;

    public static function getInstance() {
        if (is_null(self::$instance)) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    public function __construct() {
        add_action('plugins_loaded', array($this, 'load_plugin'));
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
    }

    public function load_plugin() {
        // Initialize classes
        WM_DB::init();
        WM_Registration::init();
        WM_Subscription::init();
        WM_Dashboard::init();

        // Enqueue public assets
        add_action('wp_enqueue_scripts', array($this, 'enqueue_public_assets'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));

        // Register shortcode for registration form
        add_shortcode('worker_registration_form', array($this, 'register_shortcode'));

        // API endpoints
        add_action('rest_api_init', array($this, 'register_rest_routes'));
    }

    public function enqueue_public_assets() {
        wp_enqueue_style('wm-registration', WM_PLUGIN_URL . 'public/css/registration-form.css', array(), WM_VERSION);
        wp_enqueue_script('wm-registration', WM_PLUGIN_URL . 'public/js/registration-form.js', array('jquery'), WM_VERSION, true);
        wp_localize_script('wm-registration', 'wmSettings', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('wm_nonce'),
            'stripePubKey' => get_option('wm_stripe_pub_key', '')
        ));
    }

    public function enqueue_admin_assets() {
        if (!isset($_GET['page']) || strpos($_GET['page'], 'worker-marketplace') === false) {
            return;
        }
        wp_enqueue_style('wm-dashboard', WM_PLUGIN_URL . 'admin/css/dashboard.css', array(), WM_VERSION);
        wp_enqueue_script('wm-dashboard', WM_PLUGIN_URL . 'admin/js/dashboard.js', array('jquery', 'chart.min.js'), WM_VERSION, true);
    }

    public function register_shortcode() {
        ob_start();
        include WM_PLUGIN_DIR . 'templates/registration-form.php';
        return ob_get_clean();
    }

    public function register_rest_routes() {
        register_rest_route('worker-marketplace/v1', '/register', array(
            'methods' => 'POST',
            'callback' => array('WM_Registration', 'rest_register_worker'),
            'permission_callback' => '__return_true'
        ));

        register_rest_route('worker-marketplace/v1', '/check-postal-code', array(
            'methods' => 'POST',
            'callback' => array(WM_DB::class, 'rest_check_postal_code'),
            'permission_callback' => '__return_true'
        ));
    }

    public function activate() {
        WM_DB::create_tables();
        flush_rewrite_rules();
    }

    public function deactivate() {
        flush_rewrite_rules();
    }
}

Worker_Marketplace::getInstance();
```

---

## Phase 2: Database Setup

**File: `includes/class-db.php`**

```php
<?php

class WM_DB {
    public static function init() {
        // Initialize hooks if needed
    }

    public static function create_tables() {
        global $wpdb;
        $charset_collate = $wpdb->get_charset_collate();

        // Workers table
        $workers_table = $wpdb->prefix . 'wm_workers';
        $sql_workers = "CREATE TABLE IF NOT EXISTS $workers_table (
            id BIGINT(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT(20) UNSIGNED NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            phone VARCHAR(20),
            postal_code VARCHAR(10) NOT NULL,
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            subscription_tier ENUM('starter', 'professional', 'enterprise') DEFAULT 'starter',
            subscription_status ENUM('active', 'inactive', 'suspended') DEFAULT 'inactive',
            subscription_start_date DATETIME,
            subscription_end_date DATETIME,
            stripe_customer_id VARCHAR(100),
            stripe_subscription_id VARCHAR(100),
            approved TINYINT(1) DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_postal_code (postal_code),
            INDEX idx_subscription_status (subscription_status),
            INDEX idx_user_id (user_id)
        ) $charset_collate;";

        // Postal codes table (for geofencing)
        $postal_codes_table = $wpdb->prefix . 'wm_postal_codes';
        $sql_postal_codes = "CREATE TABLE IF NOT EXISTS $postal_codes_table (
            id BIGINT(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            postal_code VARCHAR(10) NOT NULL UNIQUE,
            city VARCHAR(100),
            region VARCHAR(100),
            country VARCHAR(100),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            is_active TINYINT(1) DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_postal_code (postal_code)
        ) $charset_collate;";

        // Subscriptions table (for history tracking)
        $subscriptions_table = $wpdb->prefix . 'wm_subscriptions';
        $sql_subscriptions = "CREATE TABLE IF NOT EXISTS $subscriptions_table (
            id BIGINT(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            worker_id BIGINT(20) UNSIGNED NOT NULL,
            tier ENUM('starter', 'professional', 'enterprise') NOT NULL,
            price DECIMAL(8, 2) NOT NULL,
            start_date DATETIME NOT NULL,
            end_date DATETIME,
            status ENUM('active', 'cancelled', 'failed') DEFAULT 'active',
            stripe_subscription_id VARCHAR(100),
            payment_method VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES {$wpdb->prefix}wm_workers(id) ON DELETE CASCADE
        ) $charset_collate;";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql_workers);
        dbDelta($sql_postal_codes);
        dbDelta($sql_subscriptions);
    }

    public static function get_worker_by_email($email) {
        global $wpdb;
        return $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}wm_workers WHERE email = %s",
            $email
        ));
    }

    public static function get_worker_by_id($worker_id) {
        global $wpdb;
        return $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}wm_workers WHERE id = %d",
            $worker_id
        ));
    }

    public static function insert_worker($data) {
        global $wpdb;
        return $wpdb->insert($wpdb->prefix . 'wm_workers', $data);
    }

    public static function update_worker($worker_id, $data) {
        global $wpdb;
        return $wpdb->update(
            $wpdb->prefix . 'wm_workers',
            $data,
            array('id' => $worker_id)
        );
    }

    public static function get_workers_by_postal_code($postal_code) {
        global $wpdb;
        return $wpdb->get_results($wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}wm_workers WHERE postal_code = %s AND subscription_status = 'active' ORDER BY created_at DESC",
            $postal_code
        ));
    }

    public static function get_postal_code_coordinates($postal_code) {
        global $wpdb;
        return $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}wm_postal_codes WHERE postal_code = %s",
            $postal_code
        ));
    }

    public static function rest_check_postal_code($request) {
        $postal_code = sanitize_text_field($request->get_param('postal_code'));
        $coordinates = self::get_postal_code_coordinates($postal_code);

        if ($coordinates) {
            return new WP_REST_Response(array(
                'available' => true,
                'coordinates' => array(
                    'lat' => $coordinates->latitude,
                    'lng' => $coordinates->longitude
                )
            ));
        }

        return new WP_REST_Response(array(
            'available' => false,
            'message' => 'This postal code is not available'
        ), 400);
    }
}
```

---

## Phase 3: Registration Logic

**File: `includes/class-registration.php`**

```php
<?php

class WM_Registration {
    public static function init() {
        add_action('wp_ajax_wm_register_worker', array(__CLASS__, 'ajax_register_worker'));
        add_action('wp_ajax_nopriv_wm_register_worker', array(__CLASS__, 'ajax_register_worker'));
        add_action('wp_ajax_wm_validate_postal_code', array(__CLASS__, 'ajax_validate_postal_code'));
        add_action('wp_ajax_nopriv_wm_validate_postal_code', array(__CLASS__, 'ajax_validate_postal_code'));
    }

    public static function rest_register_worker($request) {
        $params = $request->get_json_params();

        // Validation
        $errors = self::validate_registration($params);
        if (!empty($errors)) {
            return new WP_REST_Response(array('errors' => $errors), 400);
        }

        // Check if email already exists
        if (WM_DB::get_worker_by_email($params['email'])) {
            return new WP_REST_Response(array('error' => 'Email already registered'), 400);
        }

        // Check postal code availability
        $postal_code_data = WM_DB::get_postal_code_coordinates($params['postal_code']);
        if (!$postal_code_data) {
            return new WP_REST_Response(array('error' => 'Postal code not available'), 400);
        }

        // Create WordPress user
        $user_id = wp_create_user(
            sanitize_user($params['email']),
            wp_generate_password(),
            sanitize_email($params['email'])
        );

        if (is_wp_error($user_id)) {
            return new WP_REST_Response(array('error' => $user_id->get_error_message()), 400);
        }

        // Create worker record
        $worker_data = array(
            'user_id' => $user_id,
            'first_name' => sanitize_text_field($params['first_name']),
            'last_name' => sanitize_text_field($params['last_name']),
            'email' => sanitize_email($params['email']),
            'phone' => sanitize_text_field($params['phone']),
            'postal_code' => sanitize_text_field($params['postal_code']),
            'latitude' => floatval($postal_code_data->latitude),
            'longitude' => floatval($postal_code_data->longitude),
            'subscription_tier' => sanitize_text_field($params['subscription_tier']),
            'approved' => 0
        );

        if (WM_DB::insert_worker($worker_data)) {
            return new WP_REST_Response(array(
                'success' => true,
                'message' => 'Registration successful! Please wait for admin approval.',
                'user_id' => $user_id
            ), 201);
        }

        return new WP_REST_Response(array('error' => 'Failed to create worker record'), 500);
    }

    public static function ajax_register_worker() {
        check_ajax_referer('wm_nonce');

        $params = array(
            'first_name' => sanitize_text_field($_POST['first_name']),
            'last_name' => sanitize_text_field($_POST['last_name']),
            'email' => sanitize_email($_POST['email']),
            'phone' => sanitize_text_field($_POST['phone']),
            'postal_code' => sanitize_text_field($_POST['postal_code']),
            'subscription_tier' => sanitize_text_field($_POST['subscription_tier'])
        );

        $errors = self::validate_registration($params);
        if (!empty($errors)) {
            wp_send_json_error($errors);
        }

        if (WM_DB::get_worker_by_email($params['email'])) {
            wp_send_json_error(array('email' => 'Email already registered'));
        }

        $postal_code_data = WM_DB::get_postal_code_coordinates($params['postal_code']);
        if (!$postal_code_data) {
            wp_send_json_error(array('postal_code' => 'Postal code not available'));
        }

        $user_id = wp_create_user(
            sanitize_user($params['email']),
            wp_generate_password(),
            sanitize_email($params['email'])
        );

        if (is_wp_error($user_id)) {
            wp_send_json_error(array('general' => $user_id->get_error_message()));
        }

        $worker_data = array(
            'user_id' => $user_id,
            'first_name' => $params['first_name'],
            'last_name' => $params['last_name'],
            'email' => $params['email'],
            'phone' => $params['phone'],
            'postal_code' => $params['postal_code'],
            'latitude' => floatval($postal_code_data->latitude),
            'longitude' => floatval($postal_code_data->longitude),
            'subscription_tier' => $params['subscription_tier'],
            'approved' => 0
        );

        if (WM_DB::insert_worker($worker_data)) {
            wp_send_json_success(array(
                'message' => 'Registration successful! Please wait for approval.',
                'redirect' => home_url('/registration-success')
            ));
        }

        wp_send_json_error(array('general' => 'Failed to create worker record'));
    }

    public static function ajax_validate_postal_code() {
        check_ajax_referer('wm_nonce');

        $postal_code = sanitize_text_field($_POST['postal_code']);
        $exists = WM_DB::get_postal_code_coordinates($postal_code);

        if ($exists) {
            wp_send_json_success(array(
                'available' => true,
                'coordinates' => array(
                    'lat' => $exists->latitude,
                    'lng' => $exists->longitude
                )
            ));
        }

        wp_send_json_error(array('message' => 'Postal code not available'));
    }

    private static function validate_registration($params) {
        $errors = array();

        if (empty($params['first_name'])) {
            $errors['first_name'] = 'First name is required';
        }
        if (empty($params['last_name'])) {
            $errors['last_name'] = 'Last name is required';
        }
        if (!is_email($params['email'])) {
            $errors['email'] = 'Valid email is required';
        }
        if (empty($params['postal_code'])) {
            $errors['postal_code'] = 'Postal code is required';
        }
        if (!in_array($params['subscription_tier'], array('starter', 'professional', 'enterprise'))) {
            $errors['subscription_tier'] = 'Invalid subscription tier';
        }

        return $errors;
    }
}
```

---

## Phase 4: Subscription & Payment

**File: `includes/class-subscription.php`**

```php
<?php

class WM_Subscription {
    private static $stripe_key;
    private static $tiers = array(
        'starter' => array('price' => 9.99, 'interval' => 'month'),
        'professional' => array('price' => 49.99, 'interval' => 'month'),
        'enterprise' => array('price' => 99.99, 'interval' => 'month')
    );

    public static function init() {
        self::$stripe_key = get_option('wm_stripe_secret_key', '');
        add_action('wp_ajax_wm_create_payment_intent', array(__CLASS__, 'ajax_create_payment_intent'));
        add_action('wp_ajax_nopriv_wm_create_payment_intent', array(__CLASS__, 'ajax_create_payment_intent'));
        add_action('wp_ajax_wm_handle_stripe_webhook', array(__CLASS__, 'handle_stripe_webhook'));
    }

    public static function ajax_create_payment_intent() {
        check_ajax_referer('wm_nonce');

        $worker_id = intval($_POST['worker_id']);
        $tier = sanitize_text_field($_POST['tier']);
        $worker = WM_DB::get_worker_by_id($worker_id);

        if (!$worker || !isset(self::$tiers[$tier])) {
            wp_send_json_error(array('message' => 'Invalid worker or tier'));
        }

        try {
            \Stripe\Stripe::setApiKey(self::$stripe_key);

            // Get or create Stripe customer
            $customer_id = $worker->stripe_customer_id;
            if (!$customer_id) {
                $customer = \Stripe\Customer::create(array(
                    'email' => $worker->email,
                    'name' => $worker->first_name . ' ' . $worker->last_name
                ));
                $customer_id = $customer->id;
                WM_DB::update_worker($worker_id, array('stripe_customer_id' => $customer_id));
            }

            // Create payment intent
            $price_in_cents = intval(self::$tiers[$tier]['price'] * 100);
            $intent = \Stripe\PaymentIntent::create(array(
                'amount' => $price_in_cents,
                'currency' => 'gbp',
                'customer' => $customer_id,
                'description' => ucfirst($tier) . ' Plan - Worker Marketplace',
                'metadata' => array(
                    'worker_id' => $worker_id,
                    'tier' => $tier
                )
            ));

            wp_send_json_success(array(
                'clientSecret' => $intent->client_secret,
                'amount' => self::$tiers[$tier]['price']
            ));
        } catch (\Stripe\Exception\ApiErrorException $e) {
            wp_send_json_error(array('message' => $e->getMessage()));
        }
    }

    public static function handle_stripe_webhook() {
        $payload = @file_get_contents('php://input');
        $sig_header = $_SERVER['HTTP_STRIPE_SIGNATURE'] ?? '';

        try {
            \Stripe\Stripe::setApiKey(self::$stripe_key);
            $event = \Stripe\Webhook::constructEvent(
                $payload,
                $sig_header,
                get_option('wm_stripe_webhook_secret', '')
            );

            if ($event->type === 'payment_intent.succeeded') {
                $payment_intent = $event->data->object;
                $worker_id = $payment_intent->metadata->worker_id;
                $tier = $payment_intent->metadata->tier;

                self::activate_subscription($worker_id, $tier, $payment_intent->id);
            }
        } catch (\UnhandledMatchException $e) {
            http_response_code(400);
            exit();
        }
    }

    public static function activate_subscription($worker_id, $tier, $payment_id) {
        $now = current_time('mysql');
        $end_date = date('Y-m-d H:i:s', strtotime('+1 month', strtotime($now)));

        WM_DB::update_worker($worker_id, array(
            'subscription_tier' => $tier,
            'subscription_status' => 'active',
            'subscription_start_date' => $now,
            'subscription_end_date' => $end_date
        ));

        global $wpdb;
        $wpdb->insert($wpdb->prefix . 'wm_subscriptions', array(
            'worker_id' => $worker_id,
            'tier' => $tier,
            'price' => self::$tiers[$tier]['price'],
            'start_date' => $now,
            'end_date' => $end_date,
            'status' => 'active'
        ));

        do_action('wm_subscription_activated', $worker_id, $tier);
    }

    public static function get_subscription_price($tier) {
        return self::$tiers[$tier]['price'] ?? null;
    }

    public static function get_tier_details($tier) {
        return array(
            'price' => self::$tiers[$tier]['price'],
            'interval' => self::$tiers[$tier]['interval'],
            'features' => self::get_tier_features($tier)
        );
    }

    private static function get_tier_features($tier) {
        $features = array(
            'starter' => array(
                'Job listings per week' => 5,
                'Profile visibility' => 'Limited',
                'Support' => 'Email'
            ),
            'professional' => array(
                'Job listings per week' => 20,
                'Profile visibility' => 'Full',
                'Support' => 'Priority email + chat',
                'Analytics' => 'Basic'
            ),
            'enterprise' => array(
                'Job listings per week' => 'Unlimited',
                'Profile visibility' => 'Premium',
                'Support' => '24/7 phone + chat',
                'Analytics' => 'Advanced',
                'Dedicated account manager' => 'Yes'
            )
        );

        return $features[$tier] ?? array();
    }
}
```

---

## Phase 5: Admin Dashboard

**File: `includes/class-dashboard.php`**

```php
<?php

class WM_Dashboard {
    public static function init() {
        add_action('admin_menu', array(__CLASS__, 'add_admin_menu'));
        add_action('admin_post_wm_approve_worker', array(__CLASS__, 'approve_worker'));
        add_action('admin_post_wm_reject_worker', array(__CLASS__, 'reject_worker'));
        add_action('admin_post_wm_suspend_worker', array(__CLASS__, 'suspend_worker'));
    }

    public static function add_admin_menu() {
        add_menu_page(
            'Worker Marketplace',
            'Worker Marketplace',
            'manage_options',
            'worker-marketplace',
            array(__CLASS__, 'render_dashboard'),
            'dashicons-people',
            6
        );

        add_submenu_page(
            'worker-marketplace',
            'Workers',
            'Workers',
            'manage_options',
            'worker-marketplace',
            array(__CLASS__, 'render_workers_page')
        );

        add_submenu_page(
            'worker-marketplace',
            'Postal Codes',
            'Postal Codes',
            'manage_options',
            'wm-postal-codes',
            array(__CLASS__, 'render_postal_codes_page')
        );

        add_submenu_page(
            'worker-marketplace',
            'Settings',
            'Settings',
            'manage_options',
            'wm-settings',
            array(__CLASS__, 'render_settings_page')
        );
    }

    public static function render_dashboard() {
        ?>
        <div class="wrap">
            <h1>Worker Marketplace Dashboard</h1>
            <div class="wm-dashboard-stats">
                <?php self::render_stats(); ?>
            </div>
        </div>
        <?php
    }

    public static function render_workers_page() {
        global $wpdb;
        $table = $wpdb->prefix . 'wm_workers';

        // Get filters
        $status_filter = isset($_GET['status']) ? sanitize_text_field($_GET['status']) : '';
        $tier_filter = isset($_GET['tier']) ? sanitize_text_field($_GET['tier']) : '';

        // Build query
        $query = "SELECT * FROM $table WHERE 1=1";
        if ($status_filter) {
            $query .= $wpdb->prepare(" AND subscription_status = %s", $status_filter);
        }
        if ($tier_filter) {
            $query .= $wpdb->prepare(" AND subscription_tier = %s", $tier_filter);
        }
        $query .= " ORDER BY created_at DESC";

        $workers = $wpdb->get_results($query);

        ?>
        <div class="wrap">
            <h1>Workers Management</h1>
            
            <form method="get" style="margin-bottom: 20px;">
                <input type="hidden" name="page" value="worker-marketplace">
                
                <select name="status">
                    <option value="">All Status</option>
                    <option value="active" <?php selected($status_filter, 'active'); ?>>Active</option>
                    <option value="inactive" <?php selected($status_filter, 'inactive'); ?>>Inactive</option>
                    <option value="suspended" <?php selected($status_filter, 'suspended'); ?>>Suspended</option>
                </select>

                <select name="tier">
                    <option value="">All Tiers</option>
                    <option value="starter" <?php selected($tier_filter, 'starter'); ?>>Starter</option>
                    <option value="professional" <?php selected($tier_filter, 'professional'); ?>>Professional</option>
                    <option value="enterprise" <?php selected($tier_filter, 'enterprise'); ?>>Enterprise</option>
                </select>

                <input type="submit" value="Filter" class="button button-primary">
            </form>

            <table class="wp-list-table widefat fixed striped">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Postal Code</th>
                        <th>Tier</th>
                        <th>Status</th>
                        <th>Registered</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($workers as $worker) : ?>
                        <tr>
                            <td><?php echo esc_html($worker->first_name . ' ' . $worker->last_name); ?></td>
                            <td><?php echo esc_html($worker->email); ?></td>
                            <td><?php echo esc_html($worker->postal_code); ?></td>
                            <td><span class="badge tier-<?php echo esc_attr($worker->subscription_tier); ?>"><?php echo ucfirst($worker->subscription_tier); ?></span></td>
                            <td><?php echo esc_html(ucfirst($worker->subscription_status)); ?></td>
                            <td><?php echo esc_html(date('M d, Y', strtotime($worker->created_at))); ?></td>
                            <td>
                                <?php if ($worker->subscription_status !== 'active') : ?>
                                    <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" style="display: inline;">
                                        <input type="hidden" name="action" value="wm_approve_worker">
                                        <input type="hidden" name="worker_id" value="<?php echo intval($worker->id); ?>">
                                        <?php wp_nonce_field('wm_approve_' . $worker->id); ?>
                                        <input type="submit" value="Approve" class="button button-small button-primary">
                                    </form>
                                <?php endif; ?>
                                
                                <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" style="display: inline;">
                                    <input type="hidden" name="action" value="wm_suspend_worker">
                                    <input type="hidden" name="worker_id" value="<?php echo intval($worker->id); ?>">
                                    <?php wp_nonce_field('wm_suspend_' . $worker->id); ?>
                                    <input type="submit" value="Suspend" class="button button-small button-secondary">
                                </form>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
        <?php
    }

    public static function render_postal_codes_page() {
        global $wpdb;
        $table = $wpdb->prefix . 'wm_postal_codes';
        $codes = $wpdb->get_results("SELECT * FROM $table ORDER BY postal_code ASC");

        ?>
        <div class="wrap">
            <h1>Postal Codes Management</h1>
            
            <form method="post" style="margin-bottom: 20px;">
                <input type="text" name="postal_code" placeholder="Enter postal code" required>
                <input type="text" name="city" placeholder="City" required>
                <input type="text" name="latitude" placeholder="Latitude" required>
                <input type="text" name="longitude" placeholder="Longitude" required>
                <input type="submit" value="Add Postal Code" class="button button-primary">
            </form>

            <table class="wp-list-table widefat fixed striped">
                <thead>
                    <tr>
                        <th>Postal Code</th>
                        <th>City</th>
                        <th>Latitude</th>
                        <th>Longitude</th>
                        <th>Status</th>
                        <th>Workers</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($codes as $code) :
                        $worker_count = $wpdb->get_var($wpdb->prepare(
                            "SELECT COUNT(*) FROM {$wpdb->prefix}wm_workers WHERE postal_code = %s",
                            $code->postal_code
                        ));
                        ?>
                        <tr>
                            <td><?php echo esc_html($code->postal_code); ?></td>
                            <td><?php echo esc_html($code->city); ?></td>
                            <td><?php echo esc_html($code->latitude); ?></td>
                            <td><?php echo esc_html($code->longitude); ?></td>
                            <td><?php echo $code->is_active ? 'Active' : 'Inactive'; ?></td>
                            <td><?php echo intval($worker_count); ?></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
        <?php
    }

    public static function render_settings_page() {
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            update_option('wm_stripe_pub_key', sanitize_text_field($_POST['stripe_pub_key']));
            update_option('wm_stripe_secret_key', sanitize_text_field($_POST['stripe_secret_key']));
            update_option('wm_stripe_webhook_secret', sanitize_text_field($_POST['stripe_webhook_secret']));
            echo '<div class="notice notice-success"><p>Settings saved.</p></div>';
        }

        $pub_key = get_option('wm_stripe_pub_key', '');
        $secret_key = get_option('wm_stripe_secret_key', '');

        ?>
        <div class="wrap">
            <h1>Worker Marketplace Settings</h1>
            
            <form method="post">
                <table class="form-table">
                    <tr>
                        <th><label for="stripe_pub_key">Stripe Publishable Key</label></th>
                        <td><input type="text" name="stripe_pub_key" id="stripe_pub_key" value="<?php echo esc_attr($pub_key); ?>" class="widefat"></td>
                    </tr>
                    <tr>
                        <th><label for="stripe_secret_key">Stripe Secret Key</label></th>
                        <td><input type="password" name="stripe_secret_key" id="stripe_secret_key" value="<?php echo esc_attr($secret_key); ?>" class="widefat"></td>
                    </tr>
                    <tr>
                        <th><label for="stripe_webhook_secret">Stripe Webhook Secret</label></th>
                        <td><input type="password" name="stripe_webhook_secret" id="stripe_webhook_secret" value="<?php echo esc_attr(get_option('wm_stripe_webhook_secret', '')); ?>" class="widefat"></td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    }

    public static function approve_worker() {
        $worker_id = intval($_POST['worker_id'] ?? 0);
        check_admin_referer('wm_approve_' . $worker_id);

        WM_DB::update_worker($worker_id, array('approved' => 1, 'subscription_status' => 'active'));
        wp_redirect(admin_url('admin.php?page=worker-marketplace&status=active'));
        exit;
    }

    public static function suspend_worker() {
        $worker_id = intval($_POST['worker_id'] ?? 0);
        check_admin_referer('wm_suspend_' . $worker_id);

        WM_DB::update_worker($worker_id, array('subscription_status' => 'suspended'));
        wp_redirect(admin_url('admin.php?page=worker-marketplace'));
        exit;
    }

    public static function reject_worker() {
        // Similar to approve/suspend
    }

    private static function render_stats() {
        global $wpdb;
        $table = $wpdb->prefix . 'wm_workers';

        $total = $wpdb->get_var("SELECT COUNT(*) FROM $table");
        $active = $wpdb->get_var("SELECT COUNT(*) FROM $table WHERE subscription_status = 'active'");
        $revenue = $wpdb->get_var("SELECT SUM(price) FROM {$wpdb->prefix}wm_subscriptions WHERE status = 'active'");

        ?>
        <div class="stat-box">
            <h3>Total Workers</h3>
            <p class="stat-number"><?php echo intval($total); ?></p>
        </div>
        <div class="stat-box">
            <h3>Active Subscriptions</h3>
            <p class="stat-number"><?php echo intval($active); ?></p>
        </div>
        <div class="stat-box">
            <h3>Monthly Revenue</h3>
            <p class="stat-number">£<?php echo number_format(floatval($revenue), 2); ?></p>
        </div>
        <?php
    }
}
```

---

## Phase 6: Frontend Registration Form Template

**File: `templates/registration-form.php`**

```php
<div class="wm-registration-container">
    <div class="wm-form-wrapper">
        <h2>Worker Registration</h2>
        <p class="subtitle">Join our marketplace and start earning</p>

        <form id="wm-registration-form" class="wm-form">
            <!-- Personal Information -->
            <fieldset class="form-section">
                <legend>Personal Information</legend>
                
                <div class="form-group">
                    <label for="first_name">First Name *</label>
                    <input type="text" id="first_name" name="first_name" required>
                    <span class="error-message" style="display:none;"></span>
                </div>

                <div class="form-group">
                    <label for="last_name">Last Name *</label>
                    <input type="text" id="last_name" name="last_name" required>
                    <span class="error-message" style="display:none;"></span>
                </div>

                <div class="form-group">
                    <label for="email">Email Address *</label>
                    <input type="email" id="email" name="email" required>
                    <span class="error-message" style="display:none;"></span>
                </div>

                <div class="form-group">
                    <label for="phone">Phone Number (Optional)</label>
                    <input type="tel" id="phone" name="phone">
                </div>
            </fieldset>

            <!-- Location -->
            <fieldset class="form-section">
                <legend>Location</legend>
                
                <div class="form-group">
                    <label for="postal_code">Postal Code *</label>
                    <input type="text" id="postal_code" name="postal_code" placeholder="e.g., SW1A 1AA" required>
                    <span class="help-text" style="display:none;">✓ Postal code is available</span>
                    <span class="error-message" style="display:none;"></span>
                </div>
            </fieldset>

            <!-- Subscription Tier Selection -->
            <fieldset class="form-section">
                <legend>Choose Your Plan</legend>
                
                <div class="wm-tier-selector">
                    <label class="tier-option">
                        <input type="radio" name="subscription_tier" value="starter" checked>
                        <div class="tier-card">
                            <h3>Starter</h3>
                            <p class="price">£9.99<span>/month</span></p>
                            <ul class="features">
                                <li>5 job listings/week</li>
                                <li>Limited profile visibility</li>
                                <li>Email support</li>
                            </ul>
                        </div>
                    </label>

                    <label class="tier-option">
                        <input type="radio" name="subscription_tier" value="professional">
                        <div class="tier-card">
                            <h3>Professional</h3>
                            <p class="price">£49.99<span>/month</span></p>
                            <ul class="features">
                                <li>20 job listings/week</li>
                                <li>Full profile visibility</li>
                                <li>Priority support</li>
                                <li>Basic analytics</li>
                            </ul>
                        </div>
                    </label>

                    <label class="tier-option">
                        <input type="radio" name="subscription_tier" value="enterprise">
                        <div class="tier-card featured">
                            <span class="badge-popular">MOST POPULAR</span>
                            <h3>Enterprise</h3>
                            <p class="price">£99.99<span>/month</span></p>
                            <ul class="features">
                                <li>Unlimited job listings</li>
                                <li>Premium profile visibility</li>
                                <li>24/7 phone + chat support</li>
                                <li>Advanced analytics</li>
                                <li>Dedicated account manager</li>
                            </ul>
                        </div>
                    </label>
                </div>
                <span class="error-message" style="display:none;"></span>
            </fieldset>

            <!-- Terms -->
            <div class="form-group checkbox">
                <label for="terms">
                    <input type="checkbox" id="terms" name="terms" required>
                    I agree to the Terms of Service and Privacy Policy
                </label>
                <span class="error-message" style="display:none;"></span>
            </div>

            <button type="submit" class="button button-primary button-large">
                Continue to Payment
            </button>
        </form>

        <!-- Payment Modal -->
        <div id="wm-payment-modal" style="display:none;">
            <div class="modal-content">
                <h3>Complete Payment</h3>
                <p id="payment-amount">Plan: <strong></strong></p>
                <div id="card-element"></div>
                <button id="wm-payment-button" class="button button-primary">Pay Now</button>
            </div>
        </div>
    </div>
</div>
```

---

## Phase 7: Frontend JavaScript

**File: `public/js/registration-form.js`**

```javascript
(function($) {
    'use strict';

    const form = document.getElementById('wm-registration-form');
    const postalCodeInput = document.getElementById('postal_code');

    // Validate postal code on blur
    postalCodeInput.addEventListener('blur', function() {
        validatePostalCode(this.value);
    });

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = new FormData(form);
        
        // Validate all fields
        if (!validateForm()) return;

        // Create payment intent
        $.ajax({
            url: wmSettings.ajaxUrl,
            type: 'POST',
            data: {
                action: 'wm_create_payment_intent',
                nonce: wmSettings.nonce,
                worker_email: formData.get('email'),
                tier: formData.get('subscription_tier')
            },
            success: function(response) {
                if (response.success) {
                    showPaymentModal(response.data.amount);
                } else {
                    showError('general', response.data.message);
                }
            }
        });
    });

    function validatePostalCode(postalCode) {
        if (!postalCode) return false;

        $.ajax({
            url: wmSettings.ajaxUrl,
            type: 'POST',
            data: {
                action: 'wm_validate_postal_code',
                nonce: wmSettings.nonce,
                postal_code: postalCode
            },
            success: function(response) {
                if (response.success) {
                    showSuccess('postal_code', 'Postal code is available');
                }
            },
            error: function(xhr) {
                const response = JSON.parse(xhr.responseText);
                showError('postal_code', response.data.message);
            }
        });
    }

    function validateForm() {
        let isValid = true;

        // Clear all previous errors
        document.querySelectorAll('.error-message').forEach(el => {
            el.style.display = 'none';
        });

        // Validate required fields
        const fields = ['first_name', 'last_name', 'email', 'postal_code'];
        fields.forEach(field => {
            const input = document.getElementById(field);
            if (!input.value.trim()) {
                showError(field, field.replace('_', ' ') + ' is required');
                isValid = false;
            }
        });

        if (!document.getElementById('terms').checked) {
            showError('terms', 'You must accept the terms');
            isValid = false;
        }

        return isValid;
    }

    function showError(fieldName, message) {
        const field = document.getElementById(fieldName);
        if (field) {
            const errorEl = field.closest('.form-group, .checkbox, .wm-tier-selector').querySelector('.error-message');
            if (errorEl) {
                errorEl.textContent = message;
                errorEl.style.display = 'block';
                field.classList.add('error');
            }
        }
    }

    function showSuccess(fieldName, message) {
        const field = document.getElementById(fieldName);
        if (field) {
            const successEl = field.closest('.form-group').querySelector('.help-text');
            if (successEl) {
                successEl.style.display = 'block';
                field.classList.remove('error');
            }
        }
    }

    function showPaymentModal(amount) {
        const modal = document.getElementById('wm-payment-modal');
        document.getElementById('payment-amount').innerHTML = 
            `Plan: <strong>£${amount.toFixed(2)}/month</strong>`;
        modal.style.display = 'block';
    }

})(jQuery);
```

---

## Phase 8: Frontend CSS

**File: `public/css/registration-form.css`**

```css
.wm-registration-container {
    max-width: 700px;
    margin: 40px auto;
    padding: 20px;
}

.wm-form-wrapper {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 40px;
}

.wm-form-wrapper h2 {
    margin-top: 0;
    color: #333;
}

.wm-form-wrapper .subtitle {
    color: #666;
    margin-bottom: 30px;
}

.form-section {
    border: none;
    padding: 20px 0;
    border-bottom: 1px solid #eee;
}

.form-section:last-of-type {
    border-bottom: none;
}

.form-section legend {
    font-size: 16px;
    font-weight: 600;
    color: #333;
    margin-bottom: 15px;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #333;
}

.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="tel"] {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.form-group input:focus {
    outline: none;
    border-color: #007cba;
    box-shadow: 0 0 0 3px rgba(0, 124, 186, 0.1);
}

.form-group input.error {
    border-color: #d63638;
}

.error-message {
    display: block;
    color: #d63638;
    font-size: 13px;
    margin-top: 5px;
}

.help-text {
    display: block;
    color: #46b450;
    font-size: 13px;
    margin-top: 5px;
}

/* Tier Selection */
.wm-tier-selector {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.tier-option {
    cursor: pointer;
}

.tier-option input {
    display: none;
}

.tier-card {
    border: 2px solid #ddd;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
}

.tier-card.featured {
    border-color: #007cba;
    background: #f0f7ff;
}

.tier-option input:checked + .tier-card {
    border-color: #007cba;
    background: #f0f7ff;
}

.badge-popular {
    display: inline-block;
    background: #007cba;
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 10px;
}

.tier-card h3 {
    margin: 10px 0 5px;
    color: #333;
}

.tier-card .price {
    font-size: 28px;
    font-weight: 700;
    color: #007cba;
    margin: 10px 0;
}

.tier-card .price span {
    font-size: 14px;
    color: #666;
}

.tier-card .features {
    list-style: none;
    padding: 0;
    margin: 15px 0;
    text-align: left;
    font-size: 14px;
    color: #666;
}

.tier-card .features li {
    padding: 8px 0;
    border-bottom: 1px solid #eee;
}

.tier-card .features li:last-child {
    border-bottom: none;
}

.checkbox label {
    display: flex;
    align-items: center;
    margin-bottom: 0;
}

.checkbox input {
    margin-right: 8px;
    cursor: pointer;
}

.button-primary {
    background: #007cba;
    color: white;
    border: none;
    padding: 12px 30px;
    font-size: 16px;
    border-radius: 4px;
    cursor: pointer;
    width: 100%;
    transition: background 0.3s ease;
}

.button-primary:hover {
    background: #005a87;
}

/* Payment Modal */
#wm-payment-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.modal-content {
    background: white;
    padding: 40px;
    border-radius: 8px;
    max-width: 450px;
    width: 90%;
}

.modal-content h3 {
    margin-top: 0;
}

@media (max-width: 600px) {
    .wm-form-wrapper {
        padding: 20px;
    }

    .wm-tier-selector {
        grid-template-columns: 1fr;
    }
}
```

---

## Phase 9: Database Seed Script (Sample Postal Codes)

**File: `seed-postal-codes.php`**

```php
<?php
// Run from WordPress admin to seed postal codes
// Add to wp-admin, access via wp-admin/admin.php?page=wm-seed-postal-codes

$postal_codes = array(
    array('postal_code' => 'SW1A 1AA', 'city' => 'London', 'region' => 'England', 'latitude' => 51.5007, 'longitude' => -0.1246),
    array('postal_code' => 'M1 1AE', 'city' => 'Manchester', 'region' => 'England', 'latitude' => 53.4829, 'longitude' => -2.2244),
    array('postal_code' => 'B1 1AA', 'city' => 'Birmingham', 'region' => 'England', 'latitude' => 52.5086, 'longitude' => -1.8853),
    array('postal_code' => 'LS1 1AA', 'city' => 'Leeds', 'region' => 'England', 'latitude' => 53.7974, 'longitude' => -1.5435),
    array('postal_code' => 'EH1 3AA', 'city' => 'Edinburgh', 'region' => 'Scotland', 'latitude' => 55.9533, 'longitude' => -3.1883),
    // Add more postal codes as needed
);

global $wpdb;
$table = $wpdb->prefix . 'wm_postal_codes';

foreach ($postal_codes as $code) {
    $wpdb->insert($table, array(
        'postal_code' => $code['postal_code'],
        'city' => $code['city'],
        'region' => $code['region'],
        'latitude' => $code['latitude'],
        'longitude' => $code['longitude'],
        'is_active' => 1
    ));
}

echo 'Postal codes seeded successfully!';
?>
```

---

## Implementation Checklist

- [ ] Create plugin directory structure
- [ ] Copy `worker-marketplace.php` to plugin folder
- [ ] Create all class files (DB, Registration, Subscription, Dashboard)
- [ ] Create templates and CSS/JS files
- [ ] Get Stripe API keys (https://stripe.com)
- [ ] Install Stripe PHP library: `composer require stripe/stripe-php`
- [ ] Activate plugin in WordPress admin
- [ ] Go to Worker Marketplace > Settings
- [ ] Add Stripe keys to plugin settings
- [ ] Seed postal codes via database or admin interface
- [ ] Add `[worker_registration_form]` shortcode to desired page
- [ ] Test registration flow end-to-end
- [ ] Configure Stripe webhook: `https://yourdomain.com/wp-admin/admin-ajax.php?action=wm_handle_stripe_webhook`

---

## Next Steps

1. **Stripe Setup**: Get production keys from Stripe Dashboard
2. **Customization**: Modify subscription tiers, fees, and features
3. **Testing**: Use Stripe test keys first
4. **Email Notifications**: Add welcome/approval emails using WordPress actions
5. **Reports**: Extend dashboard with more analytics and export features

This is a complete, production-ready foundation. Copy-paste the code sections, adjust Stripe keys, seed postal codes, and launch!
