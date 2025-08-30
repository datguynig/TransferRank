/**
 * SmartImage Component for TransferRank
 * Handles image loading with graceful fallbacks to initials-based avatars
 */

class SmartImage {
    constructor() {
        this.initializeImages();
        this.createInitialsGenerator();
    }

    // Initialize all images on page load
    initializeImages() {
        document.addEventListener('DOMContentLoaded', () => {
            const images = document.querySelectorAll('img[data-smart-image]');
            images.forEach(img => this.setupImage(img));
        });
    }

    // Set up individual image with error handling
    setupImage(img) {
        const originalSrc = img.src;
        const fallbackName = img.getAttribute('data-fallback-name') || img.alt || 'Unknown';
        
        // Add loading and error event listeners
        img.addEventListener('error', () => {
            this.handleImageError(img, fallbackName);
        });

        // Add lazy loading if not already present
        if (!img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
        }

        // Set proper dimensions to prevent layout shift
        if (!img.width && !img.height) {
            img.style.width = '60px';
            img.style.height = '60px';
        }
    }

    // Handle image loading errors
    handleImageError(img, name) {
        const avatarSvg = this.generateInitialsAvatar(name);
        const svgBlob = new Blob([avatarSvg], { type: 'image/svg+xml' });
        const svgUrl = URL.createObjectURL(svgBlob);
        
        img.src = svgUrl;
        img.classList.add('smart-image-fallback');
        
        // Clean up the blob URL after a delay
        setTimeout(() => {
            URL.revokeObjectURL(svgUrl);
        }, 1000);
    }

    // Generate SVG avatar with initials
    generateInitialsAvatar(name) {
        const initials = this.getInitials(name);
        const colors = this.getColorFromName(name);
        
        return `
            <svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
                <rect width="60" height="60" fill="${colors.bg}" rx="8"/>
                <text x="30" y="38" text-anchor="middle" font-family="Inter, sans-serif" 
                      font-size="20" font-weight="600" fill="${colors.text}">
                    ${initials}
                </text>
            </svg>
        `;
    }

    // Extract initials from name
    getInitials(name) {
        if (!name) return '?';
        
        const words = name.trim().split(/\s+/);
        if (words.length === 1) {
            return words[0].charAt(0).toUpperCase();
        }
        
        return (words[0].charAt(0) + words[words.length - 1].charAt(0)).toUpperCase();
    }

    // Generate consistent colors based on name
    getColorFromName(name) {
        const colors = [
            { bg: '#3B82F6', text: '#FFFFFF' }, // blue
            { bg: '#10B981', text: '#FFFFFF' }, // emerald
            { bg: '#F59E0B', text: '#FFFFFF' }, // amber
            { bg: '#EF4444', text: '#FFFFFF' }, // red
            { bg: '#8B5CF6', text: '#FFFFFF' }, // violet
            { bg: '#06B6D4', text: '#FFFFFF' }, // cyan
            { bg: '#84CC16', text: '#FFFFFF' }, // lime
            { bg: '#F97316', text: '#FFFFFF' }  // orange
        ];
        
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        
        return colors[Math.abs(hash) % colors.length];
    }

    // Create initials generator for seed/default images
    createInitialsGenerator() {
        window.generateInitialsAvatar = (name, size = 60) => {
            const initials = this.getInitials(name);
            const colors = this.getColorFromName(name);
            
            return `
                <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
                    <rect width="${size}" height="${size}" fill="${colors.bg}" rx="${size * 0.13}"/>
                    <text x="${size/2}" y="${size * 0.63}" text-anchor="middle" 
                          font-family="Inter, sans-serif" font-size="${size * 0.33}" 
                          font-weight="600" fill="${colors.text}">
                        ${initials}
                    </text>
                </svg>
            `;
        };
    }

    // Static method to replace an image element with SmartImage
    static replace(imgElement, src, alt, fallbackName) {
        imgElement.src = src;
        imgElement.alt = alt;
        imgElement.setAttribute('data-smart-image', 'true');
        imgElement.setAttribute('data-fallback-name', fallbackName || alt);
        
        const smartImage = new SmartImage();
        smartImage.setupImage(imgElement);
    }
}

// Initialize SmartImage system
window.SmartImage = SmartImage;
document.addEventListener('DOMContentLoaded', () => {
    new SmartImage();
});

// Helper function for templates
window.setupSmartImages = () => {
    new SmartImage();
};