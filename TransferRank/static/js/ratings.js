// User rating functionality for TransferRank

// Rating system configuration
const RatingConfig = {
    maxRating: 5,
    animationDuration: 200,
    hoverClass: 'text-warning-emphasis',
    activeClass: 'text-warning',
    inactiveClass: 'text-muted'
};

// Rating Manager
const RatingManager = {
    // Initialize all rating components on the page
    init: () => {
        // Initialize interactive star ratings
        document.querySelectorAll('.star-rating.interactive').forEach(container => {
            RatingManager.initInteractiveRating(container);
        });

        // Initialize readonly star ratings
        document.querySelectorAll('.star-rating.readonly').forEach(container => {
            RatingManager.initReadonlyRating(container);
        });
    },

    // Initialize interactive rating component
    initInteractiveRating: (container) => {
        const rumourId = container.dataset.rumourId;
        if (!rumourId) return;

        // Add ARIA attributes to container
        container.setAttribute('role', 'radiogroup');
        container.setAttribute('aria-label', 'Rate this transfer rumour');

        const stars = container.querySelectorAll('.fa-star');
        let currentRating = 0;
        let hoverRating = 0;
        
        // Add accessibility attributes to stars
        stars.forEach((star, index) => {
            star.setAttribute('role', 'radio');
            star.setAttribute('aria-checked', 'false');
            star.setAttribute('aria-label', `Rate ${index + 1} stars`);
            star.setAttribute('tabindex', '0');
        });

        // Add click handlers
        stars.forEach((star, index) => {
            const rating = index + 1;
            
            // Click to rate
            star.addEventListener('click', async (e) => {
                e.preventDefault();
                await RatingManager.submitRating(rumourId, rating, container);
            });
            
            // Keyboard navigation support
            star.addEventListener('keydown', async (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    await RatingManager.submitRating(rumourId, rating, container);
                }
                // Arrow key navigation
                else if (e.key === 'ArrowLeft' && index > 0) {
                    e.preventDefault();
                    stars[index - 1].focus();
                }
                else if (e.key === 'ArrowRight' && index < stars.length - 1) {
                    e.preventDefault();
                    stars[index + 1].focus();
                }
            });

            // Hover effects
            star.addEventListener('mouseenter', () => {
                hoverRating = rating;
                RatingManager.updateStarDisplay(stars, hoverRating);
            });

            star.addEventListener('mouseleave', () => {
                hoverRating = 0;
                RatingManager.updateStarDisplay(stars, currentRating);
            });
        });

        // Reset on container leave
        container.addEventListener('mouseleave', () => {
            hoverRating = 0;
            RatingManager.updateStarDisplay(stars, currentRating);
        });

        // Store reference for later updates
        container._ratingManager = {
            rumourId,
            stars,
            currentRating,
            updateRating: (rating) => {
                currentRating = rating;
                RatingManager.updateStarDisplay(stars, rating);
            }
        };
    },

    // Initialize readonly rating display
    initReadonlyRating: (container) => {
        const rating = parseFloat(container.dataset.rating) || 0;
        const stars = container.querySelectorAll('.fa-star');
        
        RatingManager.updateStarDisplay(stars, rating, true);
    },

    // Update star display based on rating
    updateStarDisplay: (stars, rating, readonly = false) => {
        stars.forEach((star, index) => {
            const starValue = index + 1;
            star.classList.remove(
                RatingConfig.activeClass, 
                RatingConfig.inactiveClass, 
                RatingConfig.hoverClass
            );

            if (rating >= starValue) {
                star.classList.add(readonly ? RatingConfig.activeClass : RatingConfig.hoverClass);
            } else if (rating >= starValue - 0.5) {
                // Half star effect for readonly displays
                star.classList.add('fas', 'fa-star-half-alt', RatingConfig.activeClass);
            } else {
                star.classList.add(RatingConfig.inactiveClass);
            }
        });
    },

    // Submit rating to server
    submitRating: async (rumourId, rating, container) => {
        try {
            // Show loading state
            container.style.pointerEvents = 'none';
            const originalHTML = container.innerHTML;
            container.innerHTML = '<i class="fas fa-spinner fa-spin text-muted"></i> Rating...';

            const response = await window.TRANSFERRANK.API.rateRumour(rumourId, rating);
            
            if (response.success) {
                // Update the rating display
                container._ratingManager.updateRating(rating);
                
                // Update the page with new average if available
                RatingManager.updateAverageRating(rumourId, response.average_rating, response.rating_count);
                
                // Show success feedback
                window.TRANSFERRANK.NotificationManager.success('Rating submitted successfully!');
                
                // Disable further rating (one per IP)
                container.classList.remove('interactive');
                container.classList.add('readonly');
                container.style.pointerEvents = 'none';
                
                // Add a small thank you message
                const thankYou = document.createElement('small');
                thankYou.className = 'text-muted d-block mt-1';
                thankYou.textContent = 'Thank you for rating!';
                container.parentNode.appendChild(thankYou);
                
            } else {
                throw new Error(response.error || 'Failed to submit rating');
            }
        } catch (error) {
            console.error('Error submitting rating:', error);
            window.TRANSFERRANK.NotificationManager.error('Failed to submit rating. Please try again');
        } finally {
            // Restore original state
            container.style.pointerEvents = 'auto';
            if (container._ratingManager) {
                const stars = container._ratingManager.stars;
                container.innerHTML = '';
                stars.forEach(star => container.appendChild(star));
            }
        }
    },

    // Update average rating display on the page
    updateAverageRating: (rumourId, averageRating, ratingCount) => {
        // Update in table rows
        document.querySelectorAll(`[data-rumour-id="${rumourId}"] .rating-display`).forEach(display => {
            const readonly = display.querySelector('.star-rating.readonly');
            if (readonly) {
                readonly.dataset.rating = averageRating;
                RatingManager.initReadonlyRating(readonly);
                
                const countElement = display.querySelector('small');
                if (countElement) {
                    countElement.textContent = `${ratingCount} ratings`;
                }
            }
        });

        // Update in detail pages
        const currentRatingSection = document.querySelector('.current-rating');
        if (currentRatingSection) {
            const ratingValue = currentRatingSection.querySelector('strong');
            const ratingText = currentRatingSection.querySelector('small');
            
            if (ratingValue) {
                ratingValue.textContent = averageRating.toFixed(1);
            }
            if (ratingText) {
                ratingText.textContent = `Based on ${ratingCount} ratings`;
            }
        }
    },

    // Get rating statistics for a rumour
    getRatingStats: (rumourId) => {
        const displays = document.querySelectorAll(`[data-rumour-id="${rumourId}"] .star-rating`);
        let totalRating = 0;
        let count = 0;

        displays.forEach(display => {
            const rating = parseFloat(display.dataset.rating);
            if (!isNaN(rating)) {
                totalRating += rating;
                count++;
            }
        });

        return {
            average: count > 0 ? totalRating / count : 0,
            count: count
        };
    }
};

// Form integration for user rating forms
const RatingFormManager = {
    // Initialize rating forms (alternative to star clicking)
    init: () => {
        document.querySelectorAll('form').forEach(form => {
            const ratingInput = form.querySelector('input[name="rating"]');
            if (ratingInput) {
                RatingFormManager.initRatingForm(form, ratingInput);
            }
        });
    },

    // Initialize a rating form
    initRatingForm: (form, ratingInput) => {
        const starContainer = form.querySelector('.star-rating');
        if (!starContainer) return;

        const stars = starContainer.querySelectorAll('.fa-star');
        
        stars.forEach((star, index) => {
            const rating = index + 1;
            
            star.addEventListener('click', () => {
                ratingInput.value = rating;
                RatingManager.updateStarDisplay(stars, rating);
                
                // Auto-submit the form
                setTimeout(() => {
                    form.submit();
                }, 300);
            });
        });
    }
};

// Bulk rating operations
const BulkRatingManager = {
    // Rate multiple rumours (for admin use)
    rateMultiple: async (ratings) => {
        const results = [];
        
        for (const { rumourId, rating } of ratings) {
            try {
                const result = await window.TRANSFERRANK.API.rateRumour(rumourId, rating);
                results.push({ rumourId, success: result.success, ...result });
            } catch (error) {
                results.push({ rumourId, success: false, error: error.message });
            }
        }
        
        return results;
    },

    // Get average ratings for multiple rumours
    getAverageRatings: (rumourIds) => {
        return rumourIds.map(id => {
            const stats = RatingManager.getRatingStats(id);
            return { rumourId: id, ...stats };
        });
    }
};

// Rating analytics
const RatingAnalytics = {
    // Track rating events for analytics
    trackRating: (rumourId, rating, userAgent = navigator.userAgent) => {
        const event = {
            type: 'rating_submitted',
            rumourId: rumourId,
            rating: rating,
            timestamp: new Date().toISOString(),
            userAgent: userAgent,
            page: window.location.pathname
        };
        
        // Store in localStorage for now (could be sent to analytics service)
        const events = JSON.parse(localStorage.getItem('transferrank_events') || '[]');
        events.push(event);
        
        // Keep only last 100 events
        if (events.length > 100) {
            events.splice(0, events.length - 100);
        }
        
        localStorage.setItem('transferrank_events', JSON.stringify(events));
    },

    // Get rating analytics
    getAnalytics: () => {
        const events = JSON.parse(localStorage.getItem('transferrank_events') || '[]');
        const ratingEvents = events.filter(e => e.type === 'rating_submitted');
        
        return {
            totalRatings: ratingEvents.length,
            averageRating: ratingEvents.reduce((sum, e) => sum + e.rating, 0) / ratingEvents.length || 0,
            ratingDistribution: RatingAnalytics.getRatingDistribution(ratingEvents),
            ratingsPerDay: RatingAnalytics.getRatingsPerDay(ratingEvents)
        };
    },

    // Get rating distribution
    getRatingDistribution: (events) => {
        const distribution = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
        events.forEach(event => {
            distribution[event.rating] = (distribution[event.rating] || 0) + 1;
        });
        return distribution;
    },

    // Get ratings per day
    getRatingsPerDay: (events) => {
        const perDay = {};
        events.forEach(event => {
            const date = event.timestamp.split('T')[0];
            perDay[date] = (perDay[date] || 0) + 1;
        });
        return perDay;
    }
};

// Export managers
window.TRANSFERRANK = {
    ...window.TRANSFERRANK,
    Rating: {
        RatingManager,
        RatingFormManager,
        BulkRatingManager,
        RatingAnalytics,
        RatingConfig
    }
};

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    RatingManager.init();
    RatingFormManager.init();
});

// Override the API rateRumour function to include analytics when available
document.addEventListener('DOMContentLoaded', () => {
    if (window.TRANSFERRANK && window.TRANSFERRANK.API && window.TRANSFERRANK.API.rateRumour) {
        const originalRateRumour = window.TRANSFERRANK.API.rateRumour;
        window.TRANSFERRANK.API.rateRumour = async (rumourId, rating) => {
            const result = await originalRateRumour(rumourId, rating);
            if (result.success) {
                RatingAnalytics.trackRating(rumourId, rating);
            }
            return result;
        };
    }
});
