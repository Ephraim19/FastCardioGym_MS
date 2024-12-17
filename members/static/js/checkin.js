document.addEventListener('DOMContentLoaded', () => {
    const memberIdInput = document.getElementById('memberIdInput');
    const statusMessage = document.getElementById('statusMessage');
    const historyTableBody = document.getElementById('historyTableBody');
    const checkInBtn = document.querySelector('.check-in-btn');
    const checkOutBtn = document.querySelector('.check-out-btn');

    function showStatus(message, isSuccess) {
        statusMessage.textContent = message;
        statusMessage.style.display = 'block';
        statusMessage.className = `status-message ${isSuccess ? 'status-success' : 'status-error'}`;
        
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 5000);
    }

    function handleCheckInOut(action) {
        const memberId = memberIdInput.value.trim();
        console.log(memberId)
        
        if (!memberId) {
            showStatus('Please enter a Member ID', false);
            return;
        }

        fetch('check-in-out/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `id=${encodeURIComponent(memberId)}&action=${encodeURIComponent(action)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showStatus(data.message, true);
                updateMemberHistory(memberId);
            } else {
                showStatus(data.message, false);
                console.log(data.message)
            }
        })
        .catch(error => {
            showStatus('An error occurred', false);
            console.error('Error:', error);
        });
    }

    function updateMemberHistory(memberId) {
        fetch(`member-history/?id=${encodeURIComponent(memberId)}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                historyTableBody.innerHTML = ''; // Clear existing rows
                
                data.records.forEach(record => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${memberId}</td>
                        <td>${record.action}</td>
                        <td>${record.timestamp}</td>
                    `;
                    historyTableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching history:', error);
        });
    }

    // Helper function to get CSRF token from cookies
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

    // Event Listeners
    checkInBtn.addEventListener('click', () => handleCheckInOut('Check In'));
    checkOutBtn.addEventListener('click', () => handleCheckInOut('Check Out'));
});

