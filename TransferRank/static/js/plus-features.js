/**
 * Plus Features Management for TransferRank
 * Handles upgrade prompts, feature gates, and Plus functionality
 */

class PlusFeatures {
    constructor() {
        this.isPlus = localStorage.getItem('isPlus') === 'true';
        this.init();
    }

    init() {
        if (this.isPlus) {
            this.enablePlusFeatures();
        } else {
            this.showUpgradePrompts();
        }
        this.addEventListeners();
    }

    enablePlusFeatures() {
        // Enable export buttons
        const exportBtns = document.querySelectorAll('.export-btn');
        exportBtns.forEach(btn => {
            btn.classList.remove('disabled');
            btn.onclick = () => this.exportData();
        });
        
        // Enable save filter buttons
        const saveFilterBtns = document.querySelectorAll('.save-filter-btn');
        saveFilterBtns.forEach(btn => {
            btn.classList.remove('disabled');
            btn.onclick = () => this.saveFilters();
        });
    }

    showUpgradePrompts() {
        // Add upgrade prompts to gated features
        this.addUpgradePrompt('.export-btn', 'Export any table to CSV');
        this.addUpgradePrompt('.save-filter-btn', 'Save custom filter combinations');
        this.addUpgradePrompt('.analytics-btn', 'Access advanced analytics');
    }

    addUpgradePrompt(selector, feature) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            el.classList.add('disabled');
            el.onclick = () => this.showUpgradeModal(feature);
        });
    }

    showUpgradeModal(feature) {
        const modal = `
            <div class="modal fade" id="upgradePrompt" tabindex="-1">
                <div class="modal-dialog modal-sm">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-crown text-warning me-2"></i>
                                Plus Feature
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <p class="mb-3">${feature}</p>
                            <p class="text-muted small mb-3">Upgrade to Plus to unlock this feature and more.</p>
                            <a href="/pricing" class="btn btn-primary">
                                <i class="fas fa-crown me-1"></i>
                                Try Plus Free
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existing = document.getElementById('upgradePrompt');
        if (existing) existing.remove();
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modal);
        const modalEl = new bootstrap.Modal(document.getElementById('upgradePrompt'));
        modalEl.show();
    }

    exportData() {
        // Mock CSV export functionality
        const csvData = this.generateCSV();
        this.downloadCSV(csvData, 'transferrank-export.csv');
    }

    generateCSV() {
        // Simple CSV generation - in real app this would be more sophisticated
        return "Player,From,To,Fee,Score\nMbappé,PSG,Real Madrid,€200M,95\n";
    }

    downloadCSV(csvContent, filename) {
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    saveFilters() {
        // Mock save filters functionality
        const filters = this.getCurrentFilters();
        localStorage.setItem('savedFilters', JSON.stringify(filters));
        
        // Show success message
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.innerHTML = '<i class="fas fa-check me-2"></i>Filters saved successfully!';
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 3000);
    }

    getCurrentFilters() {
        const form = document.querySelector('form[method="GET"]');
        if (!form) return {};
        
        const formData = new FormData(form);
        const filters = {};
        for (let [key, value] of formData.entries()) {
            if (value) filters[key] = value;
        }
        return filters;
    }

    addEventListeners() {
        // Listen for upgrade success
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('upgraded') === 'true') {
            this.showUpgradeSuccess();
        }
    }

    showUpgradeSuccess() {
        const toast = document.createElement('div');
        toast.className = 'toast-notification success';
        toast.innerHTML = '<i class="fas fa-crown me-2"></i>Welcome to Plus! All features unlocked.';
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
        
        // Update local state
        this.isPlus = true;
        this.enablePlusFeatures();
    }
}

// Initialize Plus features
window.PlusFeatures = PlusFeatures;
document.addEventListener('DOMContentLoaded', () => {
    new PlusFeatures();
});