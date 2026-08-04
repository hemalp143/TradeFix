# Quick Start Guide - 15 Minutes to Live

## 1. Install Stripe PHP Library (1 min)
```bash
composer require stripe/stripe-php
```

## 2. Create Plugin File Structure (2 min)
```bash
mkdir -p worker-marketplace/includes
mkdir -p worker-marketplace/admin/{css,js}
mkdir -p worker-marketplace/public/{css,js}
mkdir -p worker-marketplace/templates
```

## 3. Copy Core Files (5 min)
Copy all files from `WORKER-MARKETPLACE-SETUP.md` into their respective directories:
- `worker-marketplace.php` → root
- Class files → `includes/`
- CSS/JS → `public/` and `admin/`
- Templates → `templates/`

## 4. Activate & Configure (3 min)

### In WordPress Admin:
1. Plugins > Add New > Upload Plugin
2. Select zip file with worker-marketplace folder
3. Activate plugin
4. Go to **Worker Marketplace > Settings**
5. Add Stripe keys:
   - Get from: https://dashboard.stripe.com/apikeys
   - Add **Publishable** and **Secret** keys
   - Add **Webhook Secret**

## 5. Seed Postal Codes (2 min)

Run this SQL in phpMyAdmin or WP-CLI:

```sql
INSERT INTO wp_wm_postal_codes (postal_code, city, region, latitude, longitude, is_active) VALUES
('SW1A 1AA', 'London', 'England', 51.5007, -0.1246, 1),
('M1 1AE', 'Manchester', 'England', 53.4829, -2.2244, 1),
('B1 1AA', 'Birmingham', 'England', 52.5086, -1.8853, 1),
('LS1 1AA', 'Leeds', 'England', 53.7974, -1.5435, 1),
('EH1 3AA', 'Edinburgh', 'Scotland', 55.9533, -3.1883, 1),
('CF10 1AA', 'Cardiff', 'Wales', 51.4829, -3.1839, 1),
('BT1 1AA', 'Belfast', 'Northern Ireland', 54.5973, -5.9301, 1);
```

## 6. Add Registration Form to Page (1 min)

1. Go to Pages > Create New
2. Add shortcode: `[worker_registration_form]`
3. Publish

## 7. Test End-to-End (2 min)

1. Visit the page with registration form
2. Fill form with test data
3. Use Stripe test card: `4242 4242 4242 4242`
4. Confirm worker appears in admin dashboard

---

## Stripe Test Credentials

**Use these for testing:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits
- Get test keys: https://dashboard.stripe.com/test/apikeys

---

## Pricing Tiers (Locked in Plugin)
- **Starter**: £9.99/month (5 listings/week, limited visibility, email support)
- **Professional**: £49.99/month (20 listings/week, full visibility, priority support)
- **Enterprise**: £99.99/month (unlimited listings, premium visibility, 24/7 support)

---

## Admin Features Ready
✓ View all workers  
✓ Filter by status & tier  
✓ Approve/suspend workers  
✓ Manage postal codes  
✓ View revenue & stats  
✓ Stripe webhook integration  

---

## Common Customizations

### Change Subscription Price
File: `includes/class-subscription.php`, line ~13
```php
private static $tiers = array(
    'starter' => array('price' => 9.99, 'interval' => 'month'),  // Edit here
    // ...
);
```

### Add New Postal Code
WordPress Admin > Worker Marketplace > Postal Codes > Add Postal Code

### Customize Approval Flow
File: `includes/class-dashboard.php`, method `approve_worker()`

### Add Email Notifications
Add to `includes/class-registration.php`:
```php
wp_mail($worker->email, 'Welcome!', 'Your registration is pending approval');
```

---

## Troubleshooting

**Payment not processing?**
- Check Stripe keys in Settings
- Verify webhook is configured
- Check WordPress error log

**Postal code not available?**
- Seed postal codes table
- Verify postal code format matches table

**Registration form not showing?**
- Confirm plugin is activated
- Verify shortcode is on page
- Check for plugin conflicts

---

## Production Checklist
- [ ] Use Stripe production keys (not test)
- [ ] Enable SSL/HTTPS
- [ ] Test webhook with production URL
- [ ] Add email notifications
- [ ] Set up backup & monitoring
- [ ] Configure SMTP for email delivery
- [ ] Add privacy policy & terms page
- [ ] Test payment refunds process
