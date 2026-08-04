<?php
/**
 * Plugin Name: Worker Marketplace
 * Plugin URI: https://example.com/worker-marketplace
 * Description: Complete worker registration and subscription management system
 * Version: 1.0.0
 * Author: TradeFix
 * Author URI: https://example.com
 * License: GPL2
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Requires at least: 5.0
 * Requires PHP: 7.4
 */

if (!defined('ABSPATH')) {
    exit;
}

define('WM_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('WM_PLUGIN_URL', plugin_dir_url(__FILE__));
define('WM_VERSION', '1.0.0');

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
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
        add_action('plugins_loaded', array($this, 'load_plugin'));
    }

    public function load_plugin() {
        WM_DB::init();
        WM_Registration::init();
        WM_Subscription::init();
        WM_Dashboard::init();

        add_action('wp_enqueue_scripts', array($this, 'enqueue_public_assets'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));
        add_shortcode('worker_registration_form', array($this, 'register_shortcode'));
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

    public function enqueue_admin_assets($hook) {
        if (strpos($hook, 'worker-marketplace') === false) {
            return;
        }
        wp_enqueue_style('wm-dashboard', WM_PLUGIN_URL . 'admin/css/dashboard.css', array(), WM_VERSION);
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
            'callback' => array('WM_DB', 'rest_check_postal_code'),
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
