// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if they exist
    initializeCharts();
});

// Function to toggle data entry form visibility
function toggleDataEntry() {
    const dataEntry = document.getElementById('dataEntry');
    if (!dataEntry) return; // Guard clause in case element doesn't exist
    
    // Toggle display between 'block' and 'none'
    if (dataEntry.style.display === 'none' || !dataEntry.style.display) {
        dataEntry.style.display = 'block';
        // Scroll to the form
        dataEntry.scrollIntoView({ behavior: 'smooth' });
    } else {
        dataEntry.style.display = 'none';
    }
}

// Function to handle form submission
function handleSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const memberId = document.getElementById('member-id').value;


    // Get form data
    const formData = {
        weight : form.querySelector('input[name="weight"]').value ,
        body_fat: form.querySelector('input[name="body_fat"]').value,
        muscle_mass: form.querySelector('input[name="muscle_mass"]').value,
        chest: form.querySelector('input[name="chest"]').value,
        waist: form.querySelector('input[name="waist"]').value,
        notes: form.querySelector('textarea[name="notes"]')?.value
    };

    // Send data to server
    fetch(`/member/${memberId}/progress/add/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Server error occurred');
                });
            } else {
                throw new Error(`Server error: ${response.status}`);
            }
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification('Progress data saved successfully!', 'success');
            form.reset();
            toggleDataEntry(); // Hide form after successful submission
            updateCharts(data); // Update charts with new data
            updateCurrentStats(data); // Update the current stats display
        } else {
            throw new Error(data.error || 'Failed to save progress data');
        }
    })
    .catch(error => {
        showNotification(error.message, 'error');
        console.error('Error:', error);
    });
}

// Function to show notifications
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to initialize charts
function initializeCharts() {
    const weightData = JSON.parse(document.getElementById('weight-data')?.textContent || '{}');
    const measurementsData = JSON.parse(document.getElementById('measurements-data')?.textContent || '{}');
    
    // Initialize Weight Chart
    if (document.getElementById('weightChart')) {
        new Chart(document.getElementById('weightChart'), {
            type: 'line',
            data: {
                labels: weightData.labels || [],
                datasets: [{
                    label: 'Weight (kg)',
                    data: weightData.values || [],
                    borderColor: '#ff69b4',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }

    // Initialize Measurements Chart
    if (document.getElementById('measurementsChart')) {
        new Chart(document.getElementById('measurementsChart'), {
            type: 'line',
            data: {
                labels: measurementsData.labels || [],
                datasets: [
                    {
                        label: 'Chest (cm)',
                        data: measurementsData.chest || [],
                        borderColor: '#2196F3',
                        tension: 0.1
                    },
                    {
                        label: 'Waist (cm)',
                        data: measurementsData.waist || [],
                        borderColor: '#ff1493',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }
}

// Function to update current stats display
function updateCurrentStats(data) {
    const statsElements = {
        weight: document.querySelector('.info-card:nth-child(1) p'),
        bodyFat: document.querySelector('.info-card:nth-child(2) p'),
        muscleMass: document.querySelector('.info-card:nth-child(3) p')
    };

    if (data.weight && statsElements.weight) {
        statsElements.weight.textContent = `${data.weight} kg`;
    }
    if (data.body_fat && statsElements.bodyFat) {
        statsElements.bodyFat.textContent = `${data.body_fat}%`;
    }
    if (data.muscle_mass && statsElements.muscleMass) {
        statsElements.muscleMass.textContent = `${data.muscle_mass} kg`;
    }
}

// Function to update charts with new data
function updateCharts(newData) {
    // Refresh the page to show updated charts
    // In a more sophisticated implementation, you would update the charts directly
    window.location.reload();
}