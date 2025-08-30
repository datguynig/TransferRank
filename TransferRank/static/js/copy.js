/**
 * Centralised copy for TransferRank 
 * Tone: Warm, confident, helpful. British English. No hyphens in UI text.
 */

const Copy = {
    // Main headings and hero copy
    hero: {
        title: "Where Football Transfer Rumours Meet Reality",
        subtitle: "Get the most reliable transfer news ranked by credibility, club fit, value, and momentum",
        cta: "Explore Rankings"
    },

    // Scoring tooltips and explanations
    scoring: {
        credibility: "How trustworthy is the source reporting this rumour?",
        fit: "How well does this player match the club's current needs?", 
        value: "Is the reported fee reasonable for this player's quality?",
        momentum: "How much activity and buzz is this rumour generating?",
        overall: "Combined score weighing all factors for rumour likelihood"
    },

    // British friendly messages
    messages: {
        welcome: "Welcome to TransferRank! Let's explore the latest transfer buzz.",
        loading: "Fetching the latest rumours...",
        noResults: "No rumours match your search. Try adjusting your filters.",
        uploadSuccess: "Brilliant! Your CSV has been processed successfully.",
        uploadError: "Something went wrong with your upload. Please check the format and try again.",
        loginRequired: "You'll need to log in to access admin features.",
        loginSuccess: "Welcome back! You're now logged in as an administrator.",
        defaultPassword: "⚠️ You're using the default admin password. Please change it for security."
    },

    // Navigation and UI elements
    ui: {
        search: "Search players, clubs, or sources...",
        filters: "Refine Your Search",
        clearFilters: "Clear All",
        sortBy: "Sort by",
        viewDetails: "View Details",
        uploadImage: "Add Photo",
        exportData: "Export to CSV",
        saveFilters: "Save These Filters"
    },

    // Empty states
    empty: {
        noRumours: {
            title: "No Transfer Rumours Yet",
            description: "Be the first to add some exciting transfer news to get things started.",
            action: "Add First Rumour"
        },
        noPlayers: {
            title: "No Players Found", 
            description: "Try adjusting your search or filters to discover more transfer targets.",
            action: "Clear Filters"
        },
        noSources: {
            title: "No Sources Available",
            description: "Add some reliable sources to start tracking transfer rumours properly.",
            action: "Add Source"
        }
    },

    // Plus/Premium features
    plus: {
        title: "Upgrade to TransferRank Plus",
        tagline: "Get the complete transfer intelligence experience",
        features: [
            "Save custom filter combinations",
            "Email alerts for tracked players", 
            "Export any table to CSV",
            "Advanced analytics dashboard",
            "Source reliability trends"
        ],
        cta: "Try Plus Free",
        valueProps: {
            alerts: "Never miss a big transfer story",
            export: "Take your data anywhere", 
            analytics: "Spot trends before they happen",
            reliability: "Know which sources to trust"
        }
    },

    // Form validation
    validation: {
        required: "This field is required",
        email: "Please enter a valid email address",
        minLength: "Must be at least {min} characters",
        fileType: "Please upload a PNG, JPG, or WebP image",
        fileSize: "File must be under 5MB",
        csvFormat: "CSV format not recognised. Please check the template."
    },

    // British terms and phrases
    terms: {
        rumour: "rumour",
        rumours: "rumours", 
        favourite: "favourite",
        colour: "colour",
        centre: "centre",
        defence: "defence",
        analyse: "analyse",
        realise: "realise",
        organisation: "organisation"
    }
};

// Export for use in other scripts
window.Copy = Copy;