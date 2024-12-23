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
        
        const timeout = isSuccess ? 5000 : 8000;
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, timeout);
    }

    async function handleCheckInOut(action) {
        const memberId = memberIdInput.value.trim();
        
        if (!memberId) {
            showStatus('Please enter a member phone number', false);
            return;
        }

        try {
            const response = await fetch('check-in-out/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: `id=${encodeURIComponent(memberId)}&action=${encodeURIComponent(action)}`
            });

            const data = await response.json();

            if (data.status === 'success') {
                showStatus(data.message, true);
                updateMemberHistory(memberId);
            } else {
                showStatus(data.message || 'An error occurred', false);
                if (response.status === 404) {
                    memberIdInput.classList.add('error');
                    setTimeout(() => memberIdInput.classList.remove('error'), 3000);
                }
            }
        } catch (error) {
            showStatus('An error occurred while processing your request', false);
            console.error('Error:', error);
        }
    }

    async function updateMemberHistory(memberId) {
        const url = (!memberId || memberId.trim() === '') 
            ? 'member-history/' 
            : `member-history/?id=${encodeURIComponent(memberId)}`;

        try {
            const response = await fetch(url);
            const data = await response.json();

            if (data.status === 'success') {
                historyTableBody.innerHTML = '';
                
                data.records.forEach(record => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${record.member || ''}</td>
                        <td>${record.action || ''}</td>
                        <td>${record.timestamp || ''}</td>
                    `;
                    historyTableBody.appendChild(row);
                });
            }
        } catch (error) {
            console.error('Error fetching history:', error);
        }
    }

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

    // Add event listener for changes in the memberIdInput field
    memberIdInput.addEventListener('input', (event) => {
        const memberId = event.target.value.trim();
        memberIdInput.classList.remove('error');
        updateMemberHistory(memberId);
    });

    // Load initial records silently
    updateMemberHistory('');
});