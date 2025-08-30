// Main JavaScript functionality for TransferRank

// Global configuration
const TRANSFERRANK = {
    config: {
        refreshInterval: 300000, // 5 minutes
        chartColors: {
            primary: '#0d6efd',
            success: '#198754',
            warning: '#ffc107',
            danger: '#dc3545',
            info: '#0dcaf0'
        }
    }
};

// Utility functions
const Utils = {
    // Format currency
    formatCurrency: (amount, currency = '€', suffix = 'M') => {
        if (!amount) return 'Undisclosed';
        return `${currency}${Math.round(amount)}${suffix}`;
    },

    // Format date
    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: 'numeric'
        });
    },

    // Truncate text
    truncateText: (text, maxLength = 50) => {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    },

    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// API helper functions
const API = {
    // Rate a rumour
    rateRumour: async (rumourId, rating) => {
        try {
            const response = await fetch('/api/rate_rumour', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    rumour_id: rumourId,
                    rating: rating
                })
            });

            if (!response.ok) {
                throw new Error('Failed to submit rating');
            }

            return await response.json();
        } catch (error) {
            console.error('Error rating rumour:', error);
            throw error;
        }
    },

    // Get momentum data
    getMomentumData: async (rumourId) => {
        try {
            const response = await fetch(`/api/momentum_data/${rumourId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch momentum data');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching momentum data:', error);
            return [];
        }
    }
};

// Filter management
const FilterManager = {
    init: () => {
        const form = document.querySelector('form[method="GET"]');
        if (!form) return;

        // Auto-submit on filter change (with debounce)
        const debouncedSubmit = Utils.debounce(() => {
            form.submit();
        }, 500);

        form.querySelectorAll('input, select').forEach(input => {
            if (input.type === 'text') {
                input.addEventListener('input', debouncedSubmit);
            } else {
                input.addEventListener('change', debouncedSubmit);
            }
        });
    },

    // Clear all filters
    clearFilters: () => {
        window.location.href = window.location.pathname;
    }
};

// Table management
const TableManager = {
    init: () => {
        // Make table rows clickable
        document.querySelectorAll('tr[onclick]').forEach(row => {
            row.style.cursor = 'pointer';
            row.addEventListener('click', function() {
                // Extract URL from onclick attribute
                const onclickValue = this.getAttribute('onclick');
                const urlMatch = onclickValue.match(/window\.location='([^']+)'/);
                if (urlMatch) {
                    window.location.href = urlMatch[1];
                }
            });
        });

        // Add loading state for table updates
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function() {
                const table = document.querySelector('table');
                if (table) {
                    table.classList.add('loading');
                }
            });
        });
    },

    // Refresh table data
    refresh: () => {
        window.location.reload();
    }
};

// Loading states
const LoadingManager = {
    show: (element) => {
        element.classList.add('loading');
        element.style.pointerEvents = 'none';
    },

    hide: (element) => {
        element.classList.remove('loading');
        element.style.pointerEvents = 'auto';
    },

    // Show loading for form submissions
    initForms: () => {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function() {
                const submitButton = this.querySelector('button[type="submit"]');
                if (submitButton) {
                    const originalText = submitButton.innerHTML;
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
                    submitButton.disabled = true;
                    
                    // Reset after 10 seconds as fallback
                    setTimeout(() => {
                        submitButton.innerHTML = originalText;
                        submitButton.disabled = false;
                    }, 10000);
                }
            });
        });
    }
};

// Notification system
const NotificationManager = {
    show: (message, type = 'info', duration = 5000) => {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    },

    success: (message) => NotificationManager.show(message, 'success'),
    error: (message) => NotificationManager.show(message, 'danger'),
    warning: (message) => NotificationManager.show(message, 'warning'),
    info: (message) => NotificationManager.show(message, 'info')
};

// URL management
const URLManager = {
    // Update URL without page reload
    updateQueryParams: (params) => {
        const url = new URL(window.location);
        Object.keys(params).forEach(key => {
            if (params[key]) {
                url.searchParams.set(key, params[key]);
            } else {
                url.searchParams.delete(key);
            }
        });
        window.history.replaceState({}, '', url);
    },

    // Get query parameter
    getQueryParam: (param) => {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }
};

// Copy to clipboard functionality
const ClipboardManager = {
    copy: async (text) => {
        try {
            await navigator.clipboard.writeText(text);
            NotificationManager.success('Copied to clipboard!');
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            NotificationManager.success('Copied to clipboard!');
        }
    }
};

// Auto-refresh functionality
const AutoRefresh = {
    intervalId: null,
    
    start: (interval = TRANSFERRANK.config.refreshInterval) => {
        AutoRefresh.stop(); // Clear any existing interval
        AutoRefresh.intervalId = setInterval(() => {
            // Only refresh if the page is visible
            if (!document.hidden) {
                window.location.reload();
            }
        }, interval);
    },
    
    stop: () => {
        if (AutoRefresh.intervalId) {
            clearInterval(AutoRefresh.intervalId);
            AutoRefresh.intervalId = null;
        }
    }
};

// Page visibility handling
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        AutoRefresh.stop();
    } else {
        // Restart auto-refresh when page becomes visible
        if (window.location.pathname === '/') {
            AutoRefresh.start();
        }
    }
});

// Keyboard shortcuts
const KeyboardManager = {
    init: () => {
        document.addEventListener('keydown', (e) => {
            // Only trigger if not in an input field
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            switch (e.key) {
                case 'h':
                    window.location.href = '/';
                    break;
                case 'a':
                    window.location.href = '/add_rumour';
                    break;
                case 'u':
                    window.location.href = '/upload_csv';
                    break;
                case 'r':
                    window.location.reload();
                    break;
                case '?':
                    // Show keyboard shortcuts modal if it exists
                    const shortcutsModal = document.getElementById('shortcutsModal');
                    if (shortcutsModal) {
                        const modal = new bootstrap.Modal(shortcutsModal);
                        modal.show();
                    }
                    break;
            }
        });
    }
};

// Form validation enhancement
const FormValidator = {
    init: () => {
        // Add Bootstrap validation classes
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });

        // Real-time validation for specific fields
        FormValidator.initRealTimeValidation();
    },

    initRealTimeValidation: () => {
        // Fee validation
        const feeInputs = document.querySelectorAll('input[name*="fee"]');
        feeInputs.forEach(input => {
            input.addEventListener('input', function() {
                const value = parseFloat(this.value);
                if (value && (value < 0 || value > 500)) {
                    this.setCustomValidity('Transfer fee should be between 0 and 500 million');
                } else {
                    this.setCustomValidity('');
                }
            });
        });

        // URL validation
        const urlInputs = document.querySelectorAll('input[type="url"]');
        urlInputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value && !this.value.startsWith('http')) {
                    this.value = 'https://' + this.value;
                }
            });
        });
    }
};

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all managers
    FilterManager.init();
    TableManager.init();
    LoadingManager.initForms();
    KeyboardManager.init();
    FormValidator.init();

    // Start auto-refresh on leaderboard page
    if (window.location.pathname === '/') {
        AutoRefresh.start();
    }

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    console.log('TransferRank initialized successfully');
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    AutoRefresh.stop();
});

// Export for use in other scripts
window.TRANSFERRANK = {
    ...TRANSFERRANK,
    Utils,
    API,
    FilterManager,
    TableManager,
    LoadingManager,
    NotificationManager,
    URLManager,
    ClipboardManager,
    AutoRefresh,
    KeyboardManager,
    FormValidator
};
