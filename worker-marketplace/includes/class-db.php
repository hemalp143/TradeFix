<?php

class WM_DB {
    public static function init() {
    }

    public static function create_tables() {
        global $wpdb;
        $charset_collate = $wpdb->get_charset_collate();

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

        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
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
                    'lat' => floatval($coordinates->latitude),
                    'lng' => floatval($coordinates->longitude)
                )
            ));
        }

        return new WP_REST_Response(array(
            'available' => false,
            'message' => 'This postal code is not available'
        ), 400);
    }

    public static function get_all_workers($limit = 50, $offset = 0) {
        global $wpdb;
        return $wpdb->get_results($wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}wm_workers ORDER BY created_at DESC LIMIT %d OFFSET %d",
            $limit,
            $offset
        ));
    }

    public static function get_workers_count() {
        global $wpdb;
        return $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->prefix}wm_workers");
    }

    public static function get_active_workers_count() {
        global $wpdb;
        return $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->prefix}wm_workers WHERE subscription_status = 'active'");
    }

    public static function get_monthly_revenue() {
        global $wpdb;
        return $wpdb->get_var("SELECT SUM(price) FROM {$wpdb->prefix}wm_subscriptions WHERE status = 'active'");
    }
}
