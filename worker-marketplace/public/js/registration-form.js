(function($) {
    'use strict';

    const form = document.getElementById('wm-registration-form');
    const postalCodeInput = document.getElementById('postal_code');

    if (!form) return;

    postalCodeInput.addEventListener('blur', function() {
        if (this.value.length > 0) {
            validatePostalCode(this.value);
        }
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        if (!validateForm()) return;

        const formData = new FormData(form);
        const tier = formData.get('subscription_tier');
        const email = formData.get('email');

        createPaymentIntent(email, tier);
    });

    function validatePostalCode(postalCode) {
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
                    showSuccess('postal_code', '✓ Postal code is available');
                }
            },
            error: function(xhr) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    showError('postal_code', response.data?.message || 'Invalid postal code');
                } catch (e) {
                    showError('postal_code', 'Unable to validate postal code');
                }
            }
        });
    }

    function validateForm() {
        let isValid = true;

        document.querySelectorAll('.error-message').forEach(el => {
            el.style.display = 'none';
        });

        const fields = ['first_name', 'last_name', 'email', 'postal_code'];
        fields.forEach(field => {
            const input = document.getElementById(field);
            if (!input || !input.value.trim()) {
                const fieldName = field.replace('_', ' ');
                showError(field, fieldName.charAt(0).toUpperCase() + fieldName.slice(1) + ' is required');
                isValid = false;
            }
        });

        if (!document.getElementById('terms').checked) {
            showError('terms', 'You must accept the terms and conditions');
            isValid = false;
        }

        return isValid;
    }

    function showError(fieldName, message) {
        const field = document.getElementById(fieldName);
        if (!field) return;

        const container = field.closest('.form-group, .checkbox, .wm-tier-selector');
        if (!container) return;

        const errorEl = container.querySelector('.error-message');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            field.classList.add('error');
        }
    }

    function showSuccess(fieldName, message) {
        const field = document.getElementById(fieldName);
        if (!field) return;

        const container = field.closest('.form-group');
        if (!container) return;

        const successEl = container.querySelector('.help-text');
        if (successEl) {
            successEl.textContent = message;
            successEl.style.display = 'block';
            field.classList.remove('error');
        }
    }

    function createPaymentIntent(email, tier) {
        $.ajax({
            url: wmSettings.ajaxUrl,
            type: 'POST',
            data: {
                action: 'wm_create_payment_intent',
                nonce: wmSettings.nonce,
                worker_email: email,
                tier: tier
            },
            success: function(response) {
                if (response.success) {
                    showPaymentModal(response.data.amount);
                } else {
                    showError('general', response.data?.message || 'Payment setup failed');
                }
            },
            error: function() {
                showError('general', 'Unable to create payment. Please try again.');
            }
        });
    }

    function showPaymentModal(amount) {
        const modal = document.getElementById('wm-payment-modal');
        if (!modal) return;

        const tierName = document.querySelector('input[name="subscription_tier"]:checked').value;
        const tierDisplay = tierName.charAt(0).toUpperCase() + tierName.slice(1);

        document.getElementById('payment-amount').innerHTML =
            `<strong>${tierDisplay} Plan:</strong> £${amount.toFixed(2)}/month`;
        modal.style.display = 'flex';
    }

})(jQuery);
