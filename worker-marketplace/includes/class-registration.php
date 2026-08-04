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

        $errors = self::validate_registration($params);
        if (!empty($errors)) {
            return new WP_REST_Response(array('errors' => $errors), 400);
        }

        if (WM_DB::get_worker_by_email($params['email'])) {
            return new WP_REST_Response(array('error' => 'Email already registered'), 400);
        }

        $postal_code_data = WM_DB::get_postal_code_coordinates($params['postal_code']);
        if (!$postal_code_data) {
            return new WP_REST_Response(array('error' => 'Postal code not available'), 400);
        }

        $user_id = wp_create_user(
            sanitize_user($params['email']),
            wp_generate_password(),
            sanitize_email($params['email'])
        );

        if (is_wp_error($user_id)) {
            return new WP_REST_Response(array('error' => $user_id->get_error_message()), 400);
        }

        $worker_data = array(
            'user_id' => $user_id,
            'first_name' => sanitize_text_field($params['first_name']),
            'last_name' => sanitize_text_field($params['last_name']),
            'email' => sanitize_email($params['email']),
            'phone' => isset($params['phone']) ? sanitize_text_field($params['phone']) : '',
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
            'first_name' => isset($_POST['first_name']) ? sanitize_text_field($_POST['first_name']) : '',
            'last_name' => isset($_POST['last_name']) ? sanitize_text_field($_POST['last_name']) : '',
            'email' => isset($_POST['email']) ? sanitize_email($_POST['email']) : '',
            'phone' => isset($_POST['phone']) ? sanitize_text_field($_POST['phone']) : '',
            'postal_code' => isset($_POST['postal_code']) ? sanitize_text_field($_POST['postal_code']) : '',
            'subscription_tier' => isset($_POST['subscription_tier']) ? sanitize_text_field($_POST['subscription_tier']) : ''
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

        if (WM_DB::insert_worker($worker_id, $worker_data)) {
            wp_send_json_success(array(
                'message' => 'Registration successful! Please wait for approval.',
                'redirect' => home_url('/registration-success')
            ));
        }

        wp_send_json_error(array('general' => 'Failed to create worker record'));
    }

    public static function ajax_validate_postal_code() {
        check_ajax_referer('wm_nonce');

        $postal_code = isset($_POST['postal_code']) ? sanitize_text_field($_POST['postal_code']) : '';
        $exists = WM_DB::get_postal_code_coordinates($postal_code);

        if ($exists) {
            wp_send_json_success(array(
                'available' => true,
                'coordinates' => array(
                    'lat' => floatval($exists->latitude),
                    'lng' => floatval($exists->longitude)
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
        if (!is_email($params['email'] ?? '')) {
            $errors['email'] = 'Valid email is required';
        }
        if (empty($params['postal_code'])) {
            $errors['postal_code'] = 'Postal code is required';
        }
        if (!in_array($params['subscription_tier'] ?? '', array('starter', 'professional', 'enterprise'))) {
            $errors['subscription_tier'] = 'Invalid subscription tier';
        }

        return $errors;
    }
}
