// Charts functionality for TransferRank

// Chart configuration
const ChartConfig = {
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                display: false,
                grid: {
                    display: false
                }
            },
            y: {
                display: false,
                grid: {
                    display: false
                }
            }
        },
        elements: {
            point: {
                radius: 0,
                hoverRadius: 2
            },
            line: {
                borderWidth: 1.5,
                tension: 0.4
            }
        },
        interaction: {
            intersect: false,
            mode: 'index'
        }
    },

    sparklineOptions: {
        responsive: true,
        maintainAspectRatio: false,
        aspectRatio: 2.5,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                enabled: false
            }
        },
        scales: {
            x: {
                display: false,
                grid: {
                    display: false
                }
            },
            y: {
                display: false,
                grid: {
                    display: false
                },
                beginAtZero: true,
                max: 100
            }
        },
        elements: {
            point: {
                radius: 0
            },
            line: {
                borderWidth: 1,
                tension: 0.3
            }
        },
        animation: {
            duration: 0
        }
    }
};

// Sparkline Chart Manager
const SparklineManager = {
    charts: new Map(),
    initialized: false,

    // Initialize all sparklines on the page
    init: () => {
        // Prevent multiple initializations
        if (SparklineManager.initialized) {
            console.log('Sparklines already initialized, skipping');
            return;
        }

        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded, retrying sparkline initialization in 500ms');
            setTimeout(() => {
                SparklineManager.init();
            }, 500);
            return;
        }

        const sparklines = document.querySelectorAll('.momentum-sparkline');
        console.log(`Found ${sparklines.length} sparkline canvases to initialize`);
        
        // Destroy any existing charts first
        SparklineManager.destroy();
        
        sparklines.forEach((canvas, index) => {
            // Add a small delay between chart creations to prevent overwhelming
            setTimeout(() => {
                SparklineManager.createSparkline(canvas);
            }, index * 50);
        });
        
        SparklineManager.initialized = true;
    },

    // Create a single sparkline chart
    createSparkline: async (canvas) => {
        const rumourId = canvas.dataset.rumourId;
        if (!rumourId) {
            console.warn('No rumour ID found for sparkline');
            return;
        }

        // Check if we already have a chart for this rumour
        if (SparklineManager.charts.has(rumourId)) {
            console.log('Chart already exists for rumour', rumourId, ', skipping');
            return;
        }

        // Check if Chart.js is available
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js is not loaded yet, skipping sparkline creation');
            return;
        }

        try {
            // Check if canvas is visible and has proper dimensions
            if (canvas.offsetWidth === 0 || canvas.offsetHeight === 0) {
                console.warn('Canvas has zero dimensions, skipping sparkline creation for rumour', rumourId);
                return;
            }

            // Check if canvas context is available
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                console.warn('Cannot get 2D context for sparkline canvas');
                return;
            }

            // Generate sample momentum data (in a real app, this would come from the API)
            const data = SparklineManager.generateSampleData();
            
            // Ensure data is valid
            if (!data || !data.labels || !data.values || data.labels.length === 0) {
                console.warn('Invalid data for sparkline, skipping creation for rumour', rumourId);
                return;
            }
            
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.values,
                        borderColor: '#0dcaf0',
                        backgroundColor: 'rgba(13, 202, 240, 0.1)',
                        fill: true
                    }]
                },
                options: ChartConfig.sparklineOptions
            });

            SparklineManager.charts.set(rumourId, chart);
            console.log('Successfully created sparkline for rumour', rumourId);
        } catch (error) {
            console.warn('Sparkline creation failed for rumour', rumourId, ', hiding canvas:', error.message);
            // Hide the canvas if chart creation fails to prevent visual issues
            canvas.style.display = 'none';
        }
    },

    // Generate sample momentum data for demonstration
    generateSampleData: () => {
        const labels = [];
        const values = [];
        const baseValue = 30 + Math.random() * 40; // Random base between 30-70

        for (let i = 0; i < 30; i++) {
            labels.push(i);
            // Create trending data with some randomness
            const trend = Math.sin(i * 0.2) * 15;
            const noise = (Math.random() - 0.5) * 10;
            const value = Math.max(0, Math.min(100, baseValue + trend + noise));
            values.push(value);
        }

        return { labels, values };
    },

    // Destroy all sparkline charts
    destroy: () => {
        console.log('Destroying existing sparkline charts');
        SparklineManager.charts.forEach((chart, rumourId) => {
            try {
                chart.destroy();
            } catch (error) {
                console.warn('Error destroying chart for rumour', rumourId, ':', error.message);
            }
        });
        SparklineManager.charts.clear();
        SparklineManager.initialized = false;
    }
};

// Momentum Chart Manager (for detail pages)
const MomentumChartManager = {
    chart: null,

    // Initialize momentum chart on rumour detail page
    init: (rumourId) => {
        const canvas = document.getElementById('momentumChart');
        if (!canvas || !rumourId) return;

        MomentumChartManager.createChart(canvas, rumourId);
    },

    // Create detailed momentum chart
    createChart: async (canvas, rumourId) => {
        try {
            // In a real app, this would fetch from /api/momentum_data/${rumourId}
            const data = await MomentumChartManager.generateDetailedData();
            
            // Fallback colors if TRANSFERRANK not loaded yet
            const colors = window.TRANSFERRANK?.config?.chartColors || {
                info: '#0dcaf0',
                primary: '#0d6efd'
            };
            
            MomentumChartManager.chart = new Chart(canvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Momentum Score',
                        data: data.values,
                        borderColor: colors.info,
                        backgroundColor: colors.info + '20',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: colors.info,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    ...ChartConfig.defaultOptions,
                    scales: {
                        x: {
                            display: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'var(--bs-body-color)',
                                maxTicksLimit: 8
                            }
                        },
                        y: {
                            display: true,
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'var(--bs-body-color)',
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: 'var(--bs-body-color)'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'var(--bs-dark)',
                            titleColor: 'var(--bs-light)',
                            bodyColor: 'var(--bs-light)',
                            borderColor: 'var(--bs-border-color)',
                            borderWidth: 1,
                            callbacks: {
                                label: function(context) {
                                    return `Momentum: ${context.parsed.y}%`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating momentum chart:', error);
        }
    },

    // Generate detailed momentum data
    generateDetailedData: async () => {
        const labels = [];
        const values = [];
        const baseValue = 40 + Math.random() * 30;

        for (let i = 29; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
            }));

            // Create realistic momentum progression
            const daysSinceStart = 29 - i;
            let value = baseValue;
            
            // Add some events that boost or reduce momentum
            if (daysSinceStart === 5) value += 20; // Initial report
            if (daysSinceStart === 12) value += 15; // Corroboration
            if (daysSinceStart === 18) value -= 10; // Contradiction
            if (daysSinceStart === 25) value += 25; // New development
            
            // Add natural decay and noise
            value -= daysSinceStart * 0.5; // Gradual decay
            value += (Math.random() - 0.5) * 8; // Random noise
            
            values.push(Math.max(5, Math.min(95, value)));
        }

        return { labels, values };
    },

    // Destroy momentum chart
    destroy: () => {
        if (MomentumChartManager.chart) {
            MomentumChartManager.chart.destroy();
            MomentumChartManager.chart = null;
        }
    }
};

// Credibility Trend Chart (for source pages)
const CredibilityChartManager = {
    chart: null,

    // Initialize credibility trend chart
    init: (sourceId, currentCredibility) => {
        const canvas = document.getElementById('credibilityChart');
        if (!canvas) return;

        CredibilityChartManager.createChart(canvas, currentCredibility);
    },

    // Create credibility trend chart
    createChart: (canvas, currentCredibility) => {
        try {
            const data = CredibilityChartManager.generateTrendData(currentCredibility);
            
            // Fallback colors if TRANSFERRANK not loaded yet
            const colors = window.TRANSFERRANK?.config?.chartColors || {
                info: '#0dcaf0',
                primary: '#0d6efd'
            };
            
            CredibilityChartManager.chart = new Chart(canvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Credibility Score',
                        data: data.values,
                        borderColor: colors.primary,
                        backgroundColor: colors.primary + '20',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: colors.primary,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 1,
                        pointRadius: 2,
                        pointHoverRadius: 4
                    }]
                },
                options: {
                    ...ChartConfig.defaultOptions,
                    scales: {
                        x: {
                            display: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'var(--bs-body-color)',
                                maxTicksLimit: 8
                            }
                        },
                        y: {
                            display: true,
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: 'var(--bs-body-color)',
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'var(--bs-dark)',
                            titleColor: 'var(--bs-light)',
                            bodyColor: 'var(--bs-light)',
                            borderColor: 'var(--bs-border-color)',
                            borderWidth: 1
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating credibility chart:', error);
        }
    },

    // Generate credibility trend data
    generateTrendData: (baseValue) => {
        const labels = [];
        const values = [];

        for (let i = 29; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
            }));

            // Add realistic variation around the base value
            const variation = (Math.random() - 0.5) * 10;
            const value = Math.max(0, Math.min(100, baseValue + variation));
            values.push(value);
        }

        return { labels, values };
    },

    // Destroy credibility chart
    destroy: () => {
        if (CredibilityChartManager.chart) {
            CredibilityChartManager.chart.destroy();
            CredibilityChartManager.chart = null;
        }
    }
};

// Global chart initialization functions
function initializeSparklines() {
    // Add a small delay to ensure DOM is fully ready
    setTimeout(() => {
        SparklineManager.init();
    }, 100);
}

function initializeMomentumChart(rumourId) {
    MomentumChartManager.init(rumourId);
}

function initializeCredibilityChart(sourceId, currentCredibility) {
    CredibilityChartManager.init(sourceId, currentCredibility);
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    SparklineManager.destroy();
    MomentumChartManager.destroy();
    CredibilityChartManager.destroy();
});

// Export managers for external use
window.TRANSFERRANK = {
    ...window.TRANSFERRANK,
    Charts: {
        SparklineManager,
        MomentumChartManager,
        CredibilityChartManager,
        ChartConfig
    }
};

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're not already initialized
    if (!SparklineManager.initialized) {
        // Wait a bit for Chart.js to be available
        setTimeout(() => {
            // Initialize sparklines if present
            const sparklineElements = document.querySelectorAll('.momentum-sparkline');
            if (sparklineElements.length > 0) {
                console.log('Initializing sparklines after DOM ready');
                initializeSparklines();
            }
        }, 200);
    }
    
    // Initialize rating system
    if (typeof RatingManager !== 'undefined') {
        RatingManager.init();
    }
});
