<?php
if (!defined('ABSPATH')) {
    exit;
}
?>
<div class="wm-registration-container">
    <div class="wm-form-wrapper">
        <h2>Worker Registration</h2>
        <p class="subtitle">Join our marketplace and start earning today</p>

        <form id="wm-registration-form" class="wm-form">
            <fieldset class="form-section">
                <legend>Personal Information</legend>

                <div class="form-group">
                    <label for="first_name">First Name <span class="required">*</span></label>
                    <input type="text" id="first_name" name="first_name" required>
                    <span class="error-message" style="display:none;"></span>
                </div>

                <div class="form-group">
                    <label for="last_name">Last Name <span class="required">*</span></label>
                    <input type="text" id="last_name" name="last_name" required>
                    <span class="error-message" style="display:none;"></span>
                </div>

                <div class="form-group">
                    <label for="email">Email Address <span class="required">*</span></label>
                    <input type="email" id="email" name="email" required>
                    <span class="error-message" style="display:none;"></span>
                </div>

                <div class="form-group">
                    <label for="phone">Phone Number (Optional)</label>
                    <input type="tel" id="phone" name="phone">
                </div>
            </fieldset>

            <fieldset class="form-section">
                <legend>Location</legend>

                <div class="form-group">
                    <label for="postal_code">Postal Code <span class="required">*</span></label>
                    <input type="text" id="postal_code" name="postal_code" placeholder="e.g., SW1A 1AA" required>
                    <span class="help-text" style="display:none;">✓ Postal code is available</span>
                    <span class="error-message" style="display:none;"></span>
                </div>
            </fieldset>

            <fieldset class="form-section">
                <legend>Choose Your Plan</legend>

                <div class="wm-tier-selector">
                    <label class="tier-option">
                        <input type="radio" name="subscription_tier" value="starter" checked>
                        <div class="tier-card">
                            <h3>Starter</h3>
                            <p class="price">£9.99<span>/month</span></p>
                            <ul class="features">
                                <li>✓ 5 job listings/week</li>
                                <li>✓ Limited profile visibility</li>
                                <li>✓ Email support</li>
                            </ul>
                        </div>
                    </label>

                    <label class="tier-option">
                        <input type="radio" name="subscription_tier" value="professional">
                        <div class="tier-card">
                            <h3>Professional</h3>
                            <p class="price">£49.99<span>/month</span></p>
                            <ul class="features">
                                <li>✓ 20 job listings/week</li>
                                <li>✓ Full profile visibility</li>
                                <li>✓ Priority support</li>
                                <li>✓ Basic analytics</li>
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
                                <li>✓ Unlimited job listings</li>
                                <li>✓ Premium profile visibility</li>
                                <li>✓ 24/7 phone & chat support</li>
                                <li>✓ Advanced analytics</li>
                                <li>✓ Dedicated account manager</li>
                            </ul>
                        </div>
                    </label>
                </div>
                <span class="error-message" style="display:none;"></span>
            </fieldset>

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
    </div>
</div>
