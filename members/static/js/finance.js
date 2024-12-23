document.addEventListener('DOMContentLoaded', function () {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const selectedRangeElem = document.getElementById('selected-range');

    // Select the elements for each subscription card
    const subscriptionCards = {
        totalRevenue: {
            valueElem: document.querySelector('.finance-card:nth-child(1) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(1) p')
        },
        dailySubs: {
            valueElem: document.querySelector('.finance-card:nth-child(2) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(2) p')
        },
        monthlySubs: {
            valueElem: document.querySelector('.finance-card:nth-child(3) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(3) p')
        },
        quarterlySubs: {
            valueElem: document.querySelector('.finance-card:nth-child(4) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(4) p')
        },
        biannuallySubs: {
            valueElem: document.querySelector('.finance-card:nth-child(5) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(5) p')
        },
        annuallySubs: {
            valueElem: document.querySelector('.finance-card:nth-child(6) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(6) p')
        },
        studentSubs: {
            valueElem: document.querySelector('.finance-card:nth-child(7) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(7) p')
        },
        additionalServices: {
            valueElem: document.querySelector('.finance-card:nth-child(8) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(8) p')
        }
    };

    // Fetch revenue data function
    function fetchRevenueData(startDate, endDate) {
        const url = `/revenue-summary/?start_date=${startDate}&end_date=${endDate}`;
        
        // Reset all cards before fetching new data
        resetAllCards();
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Revenue Data:', data);

                // Ensure all subscription cards are reset first
                Object.keys(subscriptionCards).forEach(key => {
                    if (key !== 'totalRevenue') {
                        updateSubscriptionCard(key, 0, 0);
                    }
                });

                // Check if the necessary data exists
                if (data && data.membership_types) {
                    // Update Total Revenue
                    updateSubscriptionCard('totalRevenue', data.total_revenue,
                         `${data.total_subscribers} subscriptions`);
                    
                    // Explicitly map and update each subscription type
                    const subscriptionMap = {
                        'daily': 'dailySubs',
                        'monthly': 'monthlySubs',
                        'quarterly': 'quarterlySubs',
                        'biannually': 'biannuallySubs',
                        'annually': 'annuallySubs',
                        'student': 'studentSubs'
                    };

                    // Update Subscription Types with explicit mapping
                    data.membership_types.forEach(item => {
                        const normalizedPlan = item.plan.toLowerCase();
                        const cardKey = subscriptionMap[normalizedPlan];
                        
                        if (cardKey) {
                            updateSubscriptionCard(cardKey, item.total_amount, item.count, 'Subscribers');
                        }
                    });

                    // Update Additional Services
                    updateSubscriptionCard('additionalServices', data.additional_services, 'Personal Training, Classes, Merchandise');
                } else {
                    console.error('Invalid or incomplete data returned from the server');
                    resetAllCards();
                }
            })
            .catch(error => {
                console.error('Error fetching revenue data:', error);
                resetAllCards();
            });
    }

    // Helper function to reset all cards to the error state
    function resetAllCards() {
        Object.keys(subscriptionCards).forEach(key => {
            const card = subscriptionCards[key];
            if (card.valueElem) {
                card.valueElem.textContent = 'Loading...';
                if (card.detailElem) {
                    card.detailElem.textContent = 'Fetching data';
                }
            }
        });
    }

    // Helper function to update subscription card
    function updateSubscriptionCard(cardKey, value, detail, detailPrefix = '') {
        const card = subscriptionCards[cardKey];
        
        // Update value
        if (card.valueElem && value !== undefined) {
            card.valueElem.textContent = `Ksh ${value.toLocaleString()}`;
        }
        
        // Update detail
        if (card.detailElem && detail !== undefined) {
            if (typeof detail === 'number') {
                card.detailElem.textContent = `${detailPrefix}: ${detail.toLocaleString()}`;
            } else {
                card.detailElem.textContent = detail;
            }
        }
    }

    // Update date range display and fetch data
    function updateDateRange() {
        selectedRangeElem.textContent = `Date Range: ${startDateInput.value} - ${endDateInput.value}`;
        fetchRevenueData(startDateInput.value, endDateInput.value);
    }

    // Initial fetch with the default date range
    const initialStartDate = startDateInput.value;
    const initialEndDate = endDateInput.value;
    fetchRevenueData(initialStartDate, initialEndDate);

    // Event listeners for date range changes
    startDateInput.addEventListener('change', updateDateRange);
    endDateInput.addEventListener('change', updateDateRange);
});