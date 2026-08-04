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
    }

    public static function ajax_create_payment_intent() {
        check_ajax_referer('wm_nonce');

        $worker_email = isset($_POST['worker_email']) ? sanitize_email($_POST['worker_email']) : '';
        $tier = isset($_POST['tier']) ? sanitize_text_field($_POST['tier']) : '';

        $worker = WM_DB::get_worker_by_email($worker_email);

        if (!$worker || !isset(self::$tiers[$tier])) {
            wp_send_json_error(array('message' => 'Invalid worker or tier'));
        }

        if (!self::$stripe_key) {
            wp_send_json_error(array('message' => 'Stripe is not configured'));
        }

        try {
            require_once WM_PLUGIN_DIR . 'vendor/autoload.php';
            \Stripe\Stripe::setApiKey(self::$stripe_key);

            $customer_id = $worker->stripe_customer_id;
            if (!$customer_id) {
                $customer = \Stripe\Customer::create(array(
                    'email' => $worker->email,
                    'name' => $worker->first_name . ' ' . $worker->last_name
                ));
                $customer_id = $customer->id;
                WM_DB::update_worker($worker->id, array('stripe_customer_id' => $customer_id));
            }

            $price_in_cents = intval(self::$tiers[$tier]['price'] * 100);
            $intent = \Stripe\PaymentIntent::create(array(
                'amount' => $price_in_cents,
                'currency' => 'gbp',
                'customer' => $customer_id,
                'description' => ucfirst($tier) . ' Plan - Worker Marketplace'
            ));

            wp_send_json_success(array(
                'clientSecret' => $intent->client_secret,
                'amount' => self::$tiers[$tier]['price']
            ));
        } catch (Exception $e) {
            wp_send_json_error(array('message' => $e->getMessage()));
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
        return isset(self::$tiers[$tier]) ? self::$tiers[$tier]['price'] : null;
    }

    public static function get_tier_details($tier) {
        return array(
            'price' => self::$tiers[$tier]['price'] ?? null,
            'interval' => self::$tiers[$tier]['interval'] ?? 'month',
            'features' => self::get_tier_features($tier)
        );
    }

    private static function get_tier_features($tier) {
        $features = array(
            'starter' => array(
                'Job listings per week' => '5',
                'Profile visibility' => 'Limited',
                'Support' => 'Email'
            ),
            'professional' => array(
                'Job listings per week' => '20',
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
