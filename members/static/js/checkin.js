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
        
        if (!memberId) {
            showStatus('Please enter a member phone number', false);
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
                memberIdInput.value = ''; // Clear input after successful check-in/out
            } else {
                showStatus(data.message, false);
                console.log(data.message);
            }
        })
        .catch(error => {
            showStatus('An error occurred', false);
            console.error('Error:', error);
        });
    }

    function updateMemberHistory(memberId) {
        // Check if memberId is empty or contains only whitespace
        const shouldShowAllRecords = !memberId || memberId.trim() === '' || memberId === '0';
        const url = shouldShowAllRecords 
            ? 'member-history/' 
            : `member-history/?id=${encodeURIComponent(memberId)}`;
        
        fetch(url)
        .then(response => response.json())
        .then(data => {
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

                if (shouldShowAllRecords) {
                    showStatus('Showing all check-in and check-out records', true);
                }
            } else {
                showStatus('Error loading history records', false);
            }
        })
        .catch(error => {
            console.error('Error fetching history:', error);
            showStatus('Error loading history records', false);
        });
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
    let timeoutId;
    memberIdInput.addEventListener('input', (event) => {
        // Clear the previous timeout
        if (timeoutId) {
            clearTimeout(timeoutId);
        }

        // Set a new timeout to update history after user stops typing
        timeoutId = setTimeout(() => {
            const memberId = event.target.value.trim();
            if (!memberId || memberId === '0') {
                updateMemberHistory(null);
            } else {
                updateMemberHistory(memberId);
            }
        }, 500); // Wait 500ms after user stops typing
    });

    // Load initial records only if input is empty
    if (!memberIdInput.value.trim()) {
        updateMemberHistory(null);
    }
});