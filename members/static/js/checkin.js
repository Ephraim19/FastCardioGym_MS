document.addEventListener('DOMContentLoaded', () => {
    const memberIdInput = document.getElementById('memberIdInput');
    const statusMessage = document.getElementById('statusMessage');
    const historyTableBody = document.getElementById('historyTableBody');
    const checkInBtn = document.querySelector('.check-in-btn');
    const checkOutBtn = document.querySelector('.check-out-btn');
    const memberSelectModal = document.createElement('div');

    // Update placeholder text
    memberIdInput.placeholder = "Enter member name";

    // Set up member selection modal
    memberSelectModal.className = 'modal';
    memberSelectModal.innerHTML = `
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <h2>Select Member</h2>
            <div class="member-list"></div>
        </div>
    `;
    document.body.appendChild(memberSelectModal);

    // Get close button element
    const closeButton = memberSelectModal.querySelector('.close-button');

    function showStatus(message, isSuccess) {
        statusMessage.textContent = message;
        statusMessage.style.display = 'block';
        statusMessage.className = `status-message ${isSuccess ? 'status-success' : 'status-error'}`;

        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, isSuccess ? 5000 : 8000);
    }

    function showMemberSelectionModal(matches, action) {
        const memberList = memberSelectModal.querySelector('.member-list');
        memberList.innerHTML = '';

        matches.forEach(match => {
            const button = document.createElement('button');
            button.className = 'member-select-btn';
            button.textContent = match.name; // Only show name, not phone number
            button.onclick = () => {
                memberIdInput.value = match.name; // Set the name instead of phone
                memberSelectModal.style.display = 'none';
                handleCheckInOut(action, true);
            };
            memberList.appendChild(button);
        });

        memberSelectModal.style.display = 'flex';
    }

    async function handleCheckInOut(action, skipModalCheck = false) {
        const memberName = memberIdInput.value.trim();

        if (!memberName) {
            showStatus('Please enter a member name', false);
            return;
        }

        try {
            const response = await fetch('check-in-out/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: `id=${encodeURIComponent(memberName)}&action=${encodeURIComponent(action)}`
            });

            const data = await response.json();

            if (data.status === 'success') {
                showStatus(data.message, true);
                updateMemberHistory(memberName);
                memberIdInput.value = '';
            } else if (data.status === 'multiple_matches' && !skipModalCheck) {
                showMemberSelectionModal(data.matches, action);
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

    // Rest of the code remains the same...
    // (getCookie, updateMemberHistory, and event listeners)

    // Event Listeners
    checkInBtn.addEventListener('click', () => handleCheckInOut('Check In'));
    checkOutBtn.addEventListener('click', () => handleCheckInOut('Check Out'));

    memberIdInput.addEventListener('input', (event) => {
        const memberName = event.target.value.trim();
        memberIdInput.classList.remove('error');
        updateMemberHistory(memberName);
    });

    memberIdInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            handleCheckInOut('Check In');
        }
    });

    closeButton.addEventListener('click', () => {
        memberSelectModal.style.display = 'none';
    });

    window.onclick = (event) => {
        if (event.target === memberSelectModal) {
            memberSelectModal.style.display = 'none';
        }
    };

    // Load initial records silently
    updateMemberHistory('');

});