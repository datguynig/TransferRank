# TransferRank Changelog

## 2025-08-30 - Major UX and Features Update

### 🎨 Visual Polish
- **Updated color palette** to calm theme (slate base, indigo primary, emerald/amber/rose accents)
- **Normalised spacing** and typography with consistent type scale
- **Refined CSS variables** in `static/css/custom.css` for better theme consistency
- **Improved button styles** with subtle hover animations and proper focus states

### 📝 Voice and Copy Refresh  
- **Created centralised copy system** in `static/js/copy.js` with British English tone
- **Refreshed messaging** throughout app with warm, confident, helpful voice
- **Removed hyphens** from UI text and improved microcopy consistency
- **Added tooltip explanations** for scoring metrics

### 🖼️ Image Reliability
- **Built SmartImage component** in `static/js/smart-image.js` for graceful fallbacks
- **Added deterministic avatar generation** using SVG initials when images fail
- **Implemented lazy loading** and proper dimensions to prevent layout shift
- **Created favicon proxy route** at `/api/media/favicon` for source logos
- **Updated all image displays** in leaderboard and landing pages

### 🔐 Admin Authentication Fix
- **Implemented JWT-based login** with proper token handling in `routes.py`
- **Added admin login page** at `/admin/login` with secure authentication
- **Created token validation** decorator for protecting admin routes
- **Added environment configuration** in `.env.example` for ADMIN_PASSWORD and AUTH_SECRET
- **Shows warning banner** when using default admin password

### 💎 Monetisation (Plus Features)
- **Added Plus upgrade system** with contextual, non-blocking prompts
- **Created pricing page** at `/pricing` with clear value proposition  
- **Implemented mock upgrade flow** with local Plus status tracking
- **Added Plus feature gates** for CSV export, saved filters, and analytics
- **Built Plus features manager** in `static/js/plus-features.js`

### 🎯 UX Touch-ups
- **Improved table styling** with sticky headers and better mobile responsiveness
- **Enhanced accessibility** with proper focus states and ARIA attributes
- **Added loading skeletons** and smooth animations under 200ms
- **Created toast notification system** for user feedback
- **Optimised mobile layout** with responsive breakpoints

### ✅ Tests and Quality
- **Added backend tests** in `test_auth.py` for authentication flow
- **Created basic test coverage** for login success/failure scenarios
- **Implemented error handling** for protected route access

### 📁 Files Modified
- `static/css/custom.css` - Updated theme and UX improvements
- `static/js/copy.js` - New centralised copy system
- `static/js/smart-image.js` - New image fallback component  
- `static/js/plus-features.js` - New Plus features management
- `templates/base.html` - Added new scripts and improved structure
- `templates/leaderboard.html` - Updated to use SmartImage
- `templates/landing.html` - Enhanced image handling
- `templates/admin_login.html` - New admin login interface
- `templates/pricing.html` - New pricing and upgrade page
- `routes.py` - Added JWT auth, favicon proxy, pricing routes
- `test_auth.py` - New authentication tests
- `.env.example` - Added environment configuration

### 🏆 Acceptance Checks Passed
✅ Consistent colors, spacing, and typography  
✅ British English copy with personality  
✅ Reliable image rendering with fallbacks  
✅ Working admin login with security warnings  
✅ Non-intrusive Plus monetisation with clear value  
✅ Mobile-friendly responsive design  
✅ Proper accessibility and focus states  
✅ Basic test coverage for core functionality