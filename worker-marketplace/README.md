# Worker Marketplace Plugin

A complete WordPress plugin for worker registration and subscription management with Stripe payment integration.

## Features

- **Worker Registration**: Postal code-based registration with validation
- **Three Subscription Tiers**: Starter (£9.99), Professional (£49.99), Enterprise (£99.99)
- **Stripe Payment Integration**: Secure payment processing
- **Admin Dashboard**: Manage workers, postal codes, and subscriptions
- **Postal Code Management**: Control service areas by postal code
- **Revenue Tracking**: Monthly revenue reporting and analytics

## Installation

1. Extract plugin into `/wp-content/plugins/worker-marketplace/`
2. Go to Plugins > Installed Plugins
3. Click "Activate" next to Worker Marketplace
4. Plugin creates required database tables automatically

## Configuration

### 1. Get Stripe API Keys

1. Visit https://dashboard.stripe.com/apikeys
2. Copy your Publishable and Secret keys
3. Go to WordPress Admin > Worker Marketplace > Settings
4. Paste keys into the settings form
5. Save

### 2. Seed Postal Codes

Option A: Via Admin Panel
1. Go to Worker Marketplace > Postal Codes
2. Click "Add Postal Code"
3. Enter postal code, city, and coordinates
4. Click "Add Postal Code"

Option B: Via SQL
```sql
INSERT INTO wp_wm_postal_codes (postal_code, city, region, latitude, longitude, is_active) VALUES
('SW1A 1AA', 'London', 'England', 51.5007, -0.1246, 1),
('M1 1AE', 'Manchester', 'England', 53.4829, -2.2244, 1),
('B1 1AA', 'Birmingham', 'England', 52.5086, -1.8853, 1);
```

## Usage

### Add Registration Form to Page

1. Edit any page
2. Add shortcode: `[worker_registration_form]`
3. Publish

### Admin Tasks

**Manage Workers**
- Go to Worker Marketplace > Workers
- View all registered workers
- Filter by status and subscription tier
- Approve pending registrations
- Suspend active subscriptions

**Manage Postal Codes**
- Go to Worker Marketplace > Postal Codes
- Add new service areas
- View worker count per postal code

**View Settings**
- Go to Worker Marketplace > Settings
- Update Stripe API keys
- View subscription tier pricing

## Database Schema

### wp_wm_workers
- `id` - Worker ID
- `user_id` - WordPress user ID
- `first_name`, `last_name`, `email`, `phone`
- `postal_code` - Service area
- `latitude`, `longitude` - Geolocation
- `subscription_tier` - Subscription level
- `subscription_status` - active/inactive/suspended
- `subscription_start_date`, `subscription_end_date`
- `stripe_customer_id`, `stripe_subscription_id`
- `approved` - Admin approval status
- `created_at`, `updated_at`

### wp_wm_postal_codes
- `id` - Postal code ID
- `postal_code` - Code (e.g., SW1A 1AA)
- `city`, `region`, `country`
- `latitude`, `longitude`
- `is_active` - Service availability
- `created_at`

### wp_wm_subscriptions
- `id` - Subscription record ID
- `worker_id` - Reference to worker
- `tier` - Subscription tier
- `price` - Amount paid
- `start_date`, `end_date`
- `status` - active/cancelled/failed
- `stripe_subscription_id`
- `created_at`

## Subscription Tiers

### Starter (£9.99/month)
- 5 job listings per week
- Limited profile visibility
- Email support

### Professional (£49.99/month)
- 20 job listings per week
- Full profile visibility
- Priority email + chat support
- Basic analytics

### Enterprise (£99.99/month)
- Unlimited job listings
- Premium profile visibility
- 24/7 phone + chat support
- Advanced analytics
- Dedicated account manager

## Testing

### Stripe Test Cards
- Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., 12/25)
- CVC: Any 3 digits (e.g., 123)

Get test keys: https://dashboard.stripe.com/test/apikeys

### Test Workflow
1. Visit registration page
2. Fill form with test data
3. Select subscription tier
4. Enter Stripe test card
5. Confirm worker appears in admin dashboard

## Customization

### Change Subscription Price
Edit `includes/class-subscription.php`:
```php
private static $tiers = array(
    'starter' => array('price' => 9.99, 'interval' => 'month'),
    // Modify prices here
);
```

### Add Email Notifications
Add to `includes/class-registration.php`:
```php
wp_mail($worker->email, 'Welcome', 'Your registration has been received');
```

### Customize Tier Features
Edit `WM_Subscription::get_tier_features()` in `includes/class-subscription.php`

## API Endpoints

### REST API

**Register Worker**
```
POST /wp-json/worker-marketplace/v1/register
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "07700 900000",
  "postal_code": "SW1A 1AA",
  "subscription_tier": "professional"
}
```

**Check Postal Code**
```
POST /wp-json/worker-marketplace/v1/check-postal-code
{
  "postal_code": "SW1A 1AA"
}
```

## Troubleshooting

**Payment not processing?**
- Verify Stripe keys are correct in Settings
- Check WordPress error log: `/wp-content/debug.log`
- Ensure HTTPS is enabled

**Postal code validation failing?**
- Verify postal codes are seeded in database
- Check postal code format matches table entries

**Registration form not showing?**
- Confirm plugin is activated
- Verify shortcode is correctly placed: `[worker_registration_form]`
- Check for plugin conflicts

## Support

For issues, error logs, and configuration help:
1. Check WordPress error log: `wp-content/debug.log`
2. Verify Stripe connectivity in plugin settings
3. Test with Stripe test keys first

## License

GPL2 - See LICENSE file

## Support & Documentation

- Full implementation guide: `WORKER-MARKETPLACE-SETUP.md`
- Quick start (15 minutes): `QUICK-START.md`
