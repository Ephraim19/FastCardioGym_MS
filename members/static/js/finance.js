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

    function createMonthlyRevenueChart(data) {
        const ctx = document.getElementById('monthlyRevenueChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.monthlyRevenueChart instanceof Chart) {
            window.monthlyRevenueChart.destroy();
        }
    
        const monthlyData = data.monthly_revenue || [];
        const months = monthlyData.map(item => item.month);
        const revenues = monthlyData.map(item => item.revenue);
        const subscriptions = monthlyData.map(item => item.subscriptions);

        // Function to create and update the monthly revenue chart
        window.monthlyRevenueChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Revenue',
                        data: revenues,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        yAxisID: 'y',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Subscriptions',
                        data: subscriptions,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        yAxisID: 'y1',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Revenue (Ksh)'
                        },
                        ticks: {
                            callback: function(value) {
                                return 'Ksh ' + value.toLocaleString();
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Number of Subscriptions'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.dataset.label === 'Revenue') {
                                    return `Revenue: Ksh ${context.raw.toLocaleString()}`;
                                } else {
                                    return `Subscriptions: ${context.raw}`;
                                }
                            }
                        }
                    },
                    legend: {
                        position: 'top'
                    },
                    title: {
                        display: true,
                        text: 'Monthly Revenue and Subscriptions Trend'
                    }
                }
            }
        });
    }
    

    // Function to create and update the expense chart
    function createExpenseChart(data) {
        const ctx = document.getElementById('expenseChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.expenseChart instanceof Chart) {
            window.expenseChart.destroy();
        }

        // Create the new chart
        window.expenseChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Rent', 'Salary', 'Water', 'Cleaners', 'Food', 'Other', 'Total'],
                datasets: [{
                    label: 'Monthly Expenses',
                    data: [
                        data.expenses.rent || 0,
                        data.expenses.salary || 0,
                        data.expenses.water || 0,
                        data.expenses.cleaners || 0,
                        data.expenses.food || 0,
                        data.expenses.other || 0,
                        data.total_expenses || 0,

                    ],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 159, 64, 0.7)',
                        'rgba(201, 203, 207, 0.7)',
                        'rgba(255, 255, 0, 0.7)'

                    ],
                    borderColor: [
                        'rgb(255, 99, 132)',
                        'rgb(54, 162, 235)',
                        'rgb(75, 192, 192)',
                        'rgb(153, 102, 255)',
                        'rgb(255, 159, 64)',
                        'rgb(201, 203, 207)',
                        'rgba(255, 255, 0)'

                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'Ksh ' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Ksh ' + context.raw.toLocaleString();
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

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
                    updateSubscriptionCard('additionalServices', data.additional_services || 0, 'Personal Training, Classes, Merchandise');

                    // Update the expense chart with the new data
                    if (data.expenses) {
                        createExpenseChart(data);
                    }

                    // Update the monthly revenue chart
                    if (data.monthly_revenue) {
                        createMonthlyRevenueChart(data);
                    }

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