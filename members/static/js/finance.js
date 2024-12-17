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
        monthlySubs: {
            valueElem: document.querySelector('.finance-card:nth-child(2) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(2) p')
        },
        quarterlySubs: {
            valueElem: document.querySelector('.finance-card:nth-child(3) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(3) p')
        },
        yearlySubs: {
            valueElem: document.querySelector('.finance-card:nth-child(4) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(4) p')
        },
        studentSubs: {
            valueElem: document.querySelector('.finance-card:nth-child(5) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(5) p')
        },
        additionalServices: {
            valueElem: document.querySelector('.finance-card:nth-child(6) .card-value'),
            detailElem: document.querySelector('.finance-card:nth-child(6) p')
        }
    };

    // Fetch revenue data function
    function fetchRevenueData(startDate, endDate) {
        const url = `/revenue-summary/?start_date=${startDate}&end_date=${endDate}`;
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Revenue Data:', data); // Log to check the returned data

                // Check if the necessary data exists
                if (data && data.membership_types) {
                    // Update Total Revenue
                    updateSubscriptionCard('totalRevenue', data.total_revenue, `+${data.total_revenue_growth}% from last month`);
                    
                    // Update Subscription Types
                    data.membership_types.forEach(item => {
                        const planKey = item.plan.toLowerCase() + 'Subs'; // Use 'monthlySubs', 'quarterlySubs', etc.
                        updateSubscriptionCard(planKey, item.total_amount, item.count, 'Subscribers');
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
                card.valueElem.textContent = 'Error Loading';
                if (card.detailElem) {
                    card.detailElem.textContent = 'Unable to fetch data';
                }
            }
        });
    }

    // Helper function to update subscription card
    function updateSubscriptionCard(cardKey, value, detail, detailPrefix = '') {
        const card = subscriptionCards[cardKey];
        
        // Update value
        if (card.valueElem && value !== undefined) {
            card.valueElem.textContent = `Ksh ${formatNumber(value)}`;
        }
        
        // Update detail
        if (card.detailElem && detail !== undefined) {
            if (typeof detail === 'number') {
                card.detailElem.textContent = `${detailPrefix}: ${detail}`;
            } else {
                card.detailElem.textContent = detail;
            }
        }
    }

    // Helper function to format large numbers
    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toFixed(0);
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
