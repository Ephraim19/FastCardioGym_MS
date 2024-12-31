document.addEventListener('DOMContentLoaded', function() {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const downloadBtn = document.querySelector('.download-btn');

    // Function to fetch and update report data
    function updateReport() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        if (!startDate || !endDate) return;

        // Show loading state
        document.body.style.cursor = 'wait';

        // Create headers with CSRF token
        const headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
        };

        fetch(`/reports/?start_date=${startDate}&end_date=${endDate}`, {
            method: 'GET',
            headers: headers,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Update all statistics
            updateStatistics(data);
        })
        .catch(error => {
            console.error('Error fetching report data:', error);
        })
        .finally(() => {
            document.body.style.cursor = 'default';
        });
    }

    // Function to update statistics in the UI
    function updateStatistics(data) {
        // Update member statistics
        updateElement('.stats-grid .total .amount', data.total_members);
        updateElement('.stats-grid .total .subscribers', `+${data.new_members_this_month} this month`);
        updateElement('.stat-card:nth-of-type(1) .number', data.active_members);
        updateElement('.stat-card:nth-of-type(1) .sub-text', `+${data.new_active_this_month} this month`);
        updateElement('.stat-card:nth-of-type(2) .number', data.active_checkins);
        updateElement('.stat-card:nth-of-type(3) .number', data.not_attending);

        // Update revenue statistics
        updateElement('.subscription-grid .total .amount', `Ksh ${formatNumber(data.total_revenue)}`);
        updateElement('.subscription-grid .total .subscribers', `${data.total_subscriptions} subscriptions`);

        // Update subscription breakdowns
        const subscriptionTypes = [
            { name: 'Daily', amount: data.daily_subscription_amount, subscribers: data.daily_subscribers },
            { name: 'Monthly', amount: data.monthly_subscription_amount, subscribers: data.monthly_subscribers },
            { name: 'Quarterly', amount: data.quarterly_subscription_amount, subscribers: data.quarterly_subscribers },
            { name: 'Biannual', amount: data.biannual_subscription_amount, subscribers: data.biannual_subscribers },
            { name: 'Annual', amount: data.annual_subscription_amount, subscribers: data.annual_subscribers },
            { name: 'Student', amount: data.student_subscription_amount, subscribers: data.student_subscribers }
        ];

        subscriptionTypes.forEach(type => {
            updateSubscriptionData(type.name, type.amount, type.subscribers);
        });
    }

    // Helper function to update subscription card data
    function updateSubscriptionData(type, amount, subscribers) {
        const card = Array.from(document.querySelectorAll('.subscription-card'))
            .find(card => card.querySelector('h3').textContent.includes(type));
        
        if (card) {
            updateElement(card.querySelector('.amount'), `Ksh ${formatNumber(amount)}`);
            updateElement(card.querySelector('.subscribers'), `${subscribers} subscribers`);
        }
    }

    // Helper function to update DOM elements
    function updateElement(selector, value) {
        const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (element) {
            element.textContent = value;
        }
    }

    // Helper function to format numbers
    function formatNumber(number) {
        return parseFloat(number).toFixed(2);
    }

    // Event listeners for date inputs
    startDateInput.addEventListener('change', function() {
        if (endDateInput.value && this.value > endDateInput.value) {
            endDateInput.value = this.value;
        }
        updateReport();
    });

    endDateInput.addEventListener('change', function() {
        if (startDateInput.value && this.value < startDateInput.value) {
            startDateInput.value = this.value;
        }
        updateReport();
    });

    // Download report functionality
    downloadBtn.addEventListener('click', function() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        fetch(`/reports/download/?start_date=${startDate}&end_date=${endDate}`, {
            method: 'GET',
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const downloadUrl = data.download_url;
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = downloadUrl.split('/').pop();
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error downloading report:', error);
        });
    });
});