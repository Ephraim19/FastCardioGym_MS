let previousData = null;
let fetchTimeout = null;

async function fetchExpenseData() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    // Only fetch if we have both dates
    if (!startDate || !endDate) return;

    try {
        const queryParams = new URLSearchParams();
        queryParams.append('start_date', startDate);
        queryParams.append('end_date', endDate);

        const response = await fetch(`/revenue-summary/?${queryParams.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch expense data');

        const data = await response.json();
        updateDashboard(data);
        previousData = data;
    } catch (error) {
        console.error('Error fetching expense data:', error);
    }
}

function debounceUpdate() {
    // Clear any existing timeout
    if (fetchTimeout) {
        clearTimeout(fetchTimeout);
    }

    // Set a new timeout to fetch data after 500ms of no changes
    fetchTimeout = setTimeout(fetchExpenseData, 500);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        maximumFractionDigits: 0
    }).format(amount);
}

function calculateChange(currentValue, previousValue) {
    if (!previousValue) return "No previous data";

    const change = ((currentValue - previousValue) / previousValue) * 100;
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(1)}%`;
}

function updateCard(cardId, value, previousValue = null) {
    const card = document.getElementById(cardId);
    const valueElement = card.querySelector('.card-value');
    const changeElement = card.querySelector('.card-change');

    valueElement.textContent = formatCurrency(value);

    const change = calculateChange(value, previousValue);
    changeElement.textContent = change;
    changeElement.className = 'card-change';
    changeElement.classList.add(value >= (previousValue || value) ? 'positive' : 'negative');
}

function updateDashboard(data) {
    const expenses = data.expenses;
    const totalExpenses = data.total_expenses;

    // Update total expenses card
    updateCard('total-card', totalExpenses, previousData ? .total_expenses);

    // Update individual expense cards
    const expenseTypes = [
        'rent',
        'salary',
        'water',
        'cleaners',
        'food',
        'maintenance',
        'electricity',
        'capital-expenditure',
        'other'
    ];

    expenseTypes.forEach(type => {
        const cardId = `${type}-card`;
        const currentValue = expenses[type] || 0;
        const previousValue = previousData ? .expenses ? .[type];
        updateCard(cardId, currentValue, previousValue);
    });
}

function validateDateRange() {
    const startDate = document.getElementById('start-date');
    const endDate = document.getElementById('end-date');

    // Ensure end date isn't before start date
    if (startDate.value && endDate.value && endDate.value < startDate.value) {
        endDate.value = startDate.value;
    }
}

// Initialize date range and fetch data when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');

    // Set initial dates for the current month
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    startDateInput.value = firstDay.toISOString().split('T')[0];
    endDateInput.value = lastDay.toISOString().split('T')[0];

    // Add event listeners for date changes
    startDateInput.addEventListener('change', () => {
        validateDateRange();
        debounceUpdate();
    });

    endDateInput.addEventListener('change', () => {
        validateDateRange();
        debounceUpdate();
    });

    // Fetch initial data
    fetchExpenseData();
});