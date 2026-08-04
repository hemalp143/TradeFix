<?php

class WM_Dashboard {
    public static function init() {
        add_action('admin_menu', array(__CLASS__, 'add_admin_menu'));
        add_action('admin_post_wm_approve_worker', array(__CLASS__, 'approve_worker'));
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
        <style>
            .wm-dashboard-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .stat-box {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .stat-box h3 {
                margin: 0 0 10px;
                color: #666;
                font-size: 14px;
            }
            .stat-number {
                font-size: 32px;
                font-weight: bold;
                color: #007cba;
                margin: 0;
            }
        </style>
        <?php
    }

    public static function render_workers_page() {
        global $wpdb;
        $table = $wpdb->prefix . 'wm_workers';

        $status_filter = isset($_GET['status']) ? sanitize_text_field($_GET['status']) : '';
        $tier_filter = isset($_GET['tier']) ? sanitize_text_field($_GET['tier']) : '';

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
                    <option value="starter" <?php selected($tier_filter, 'starter'); ?>>Starter (£9.99)</option>
                    <option value="professional" <?php selected($tier_filter, 'professional'); ?>>Professional (£49.99)</option>
                    <option value="enterprise" <?php selected($tier_filter, 'enterprise'); ?>>Enterprise (£99.99)</option>
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
                    <?php if ($workers) : ?>
                        <?php foreach ($workers as $worker) : ?>
                            <tr>
                                <td><?php echo esc_html($worker->first_name . ' ' . $worker->last_name); ?></td>
                                <td><?php echo esc_html($worker->email); ?></td>
                                <td><?php echo esc_html($worker->postal_code); ?></td>
                                <td><strong><?php echo ucfirst(esc_html($worker->subscription_tier)); ?></strong></td>
                                <td><span style="color: <?php echo $worker->subscription_status === 'active' ? 'green' : 'orange'; ?>;"><?php echo ucfirst(esc_html($worker->subscription_status)); ?></span></td>
                                <td><?php echo esc_html(date('M d, Y', strtotime($worker->created_at))); ?></td>
                                <td>
                                    <?php if ($worker->subscription_status !== 'active') : ?>
                                        <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" style="display: inline;">
                                            <input type="hidden" name="action" value="wm_approve_worker">
                                            <input type="hidden" name="worker_id" value="<?php echo intval($worker->id); ?>">
                                            <?php wp_nonce_field('wm_approve_' . $worker->id); ?>
                                            <input type="submit" value="Approve" class="button button-small button-primary">
                                        </form>
                                    <?php endif; ?>

                                    <?php if ($worker->subscription_status === 'active') : ?>
                                        <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" style="display: inline;">
                                            <input type="hidden" name="action" value="wm_suspend_worker">
                                            <input type="hidden" name="worker_id" value="<?php echo intval($worker->id); ?>">
                                            <?php wp_nonce_field('wm_suspend_' . $worker->id); ?>
                                            <input type="submit" value="Suspend" class="button button-small button-secondary">
                                        </form>
                                    <?php endif; ?>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    <?php else : ?>
                        <tr><td colspan="7">No workers found.</td></tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
        <?php
    }

    public static function render_postal_codes_page() {
        global $wpdb;
        $table = $wpdb->prefix . 'wm_postal_codes';

        if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['postal_code'])) {
            $wpdb->insert($table, array(
                'postal_code' => sanitize_text_field($_POST['postal_code']),
                'city' => sanitize_text_field($_POST['city'] ?? ''),
                'latitude' => floatval($_POST['latitude'] ?? 0),
                'longitude' => floatval($_POST['longitude'] ?? 0),
                'is_active' => 1
            ));
            echo '<div class="notice notice-success"><p>Postal code added.</p></div>';
        }

        $codes = $wpdb->get_results("SELECT * FROM $table ORDER BY postal_code ASC");

        ?>
        <div class="wrap">
            <h1>Postal Codes Management</h1>

            <form method="post" style="margin-bottom: 30px; background: #f1f1f1; padding: 20px; border-radius: 5px;">
                <table>
                    <tr>
                        <td><input type="text" name="postal_code" placeholder="Postal Code (e.g., SW1A 1AA)" required style="padding: 8px; margin-right: 10px;"></td>
                        <td><input type="text" name="city" placeholder="City" required style="padding: 8px; margin-right: 10px;"></td>
                        <td><input type="text" name="latitude" placeholder="Latitude" required style="padding: 8px; margin-right: 10px;"></td>
                        <td><input type="text" name="longitude" placeholder="Longitude" required style="padding: 8px; margin-right: 10px;"></td>
                        <td><input type="submit" value="Add Postal Code" class="button button-primary"></td>
                    </tr>
                </table>
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
                            <td><strong><?php echo esc_html($code->postal_code); ?></strong></td>
                            <td><?php echo esc_html($code->city); ?></td>
                            <td><?php echo esc_html($code->latitude); ?></td>
                            <td><?php echo esc_html($code->longitude); ?></td>
                            <td><?php echo $code->is_active ? '<span style="color: green;">Active</span>' : '<span style="color: red;">Inactive</span>'; ?></td>
                            <td><?php echo intval($worker_count); ?></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
        <?php
    }

    public static function render_settings_page() {
        if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['stripe_pub_key'])) {
            update_option('wm_stripe_pub_key', sanitize_text_field($_POST['stripe_pub_key']));
            update_option('wm_stripe_secret_key', sanitize_text_field($_POST['stripe_secret_key']));
            echo '<div class="notice notice-success"><p>Settings saved successfully.</p></div>';
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
                        <td><input type="text" name="stripe_pub_key" id="stripe_pub_key" value="<?php echo esc_attr($pub_key); ?>" class="widefat" required></td>
                    </tr>
                    <tr>
                        <th><label for="stripe_secret_key">Stripe Secret Key</label></th>
                        <td><input type="password" name="stripe_secret_key" id="stripe_secret_key" value="<?php echo esc_attr($secret_key); ?>" class="widefat" required></td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>

            <hr>
            <h2>Subscription Tiers</h2>
            <table class="wp-list-table widefat fixed striped">
                <thead>
                    <tr>
                        <th>Tier</th>
                        <th>Price</th>
                        <th>Interval</th>
                        <th>Features</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Starter</td>
                        <td>£9.99</td>
                        <td>Per month</td>
                        <td>5 listings/week, Limited visibility, Email support</td>
                    </tr>
                    <tr>
                        <td>Professional</td>
                        <td>£49.99</td>
                        <td>Per month</td>
                        <td>20 listings/week, Full visibility, Priority support, Basic analytics</td>
                    </tr>
                    <tr>
                        <td>Enterprise</td>
                        <td>£99.99</td>
                        <td>Per month</td>
                        <td>Unlimited listings, Premium visibility, 24/7 support, Advanced analytics, Dedicated manager</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <?php
    }

    public static function approve_worker() {
        $worker_id = intval($_POST['worker_id'] ?? 0);
        if (!$worker_id) {
            wp_die('Invalid worker ID');
        }
        check_admin_referer('wm_approve_' . $worker_id);

        WM_DB::update_worker($worker_id, array('approved' => 1, 'subscription_status' => 'active'));
        wp_redirect(admin_url('admin.php?page=worker-marketplace&status=active'));
        exit;
    }

    public static function suspend_worker() {
        $worker_id = intval($_POST['worker_id'] ?? 0);
        if (!$worker_id) {
            wp_die('Invalid worker ID');
        }
        check_admin_referer('wm_suspend_' . $worker_id);

        WM_DB::update_worker($worker_id, array('subscription_status' => 'suspended'));
        wp_redirect(admin_url('admin.php?page=worker-marketplace'));
        exit;
    }

    private static function render_stats() {
        $total = WM_DB::get_workers_count();
        $active = WM_DB::get_active_workers_count();
        $revenue = WM_DB::get_monthly_revenue();

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
