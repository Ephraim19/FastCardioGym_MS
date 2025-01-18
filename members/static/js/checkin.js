document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('memberSearch');
    const searchResults = document.getElementById('searchResults');
    const selectedMember = document.getElementById('selectedMember');
    const checkInBtn = document.querySelector('.check-in-btn');
    const checkOutBtn = document.querySelector('.check-out-btn');
    const statusMessage = document.getElementById('statusMessage');

    let selectedMemberId = null;

    // Get CSRF token from cookie
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
    const csrfToken = getCookie('csrftoken');

    function showMessage(message, isError = false) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${isError ? 'status-error' : 'status-success'}`;
        statusMessage.style.display = 'block';
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 5000);
    }

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    async function searchMembers(searchTerm) {
        try {
            const response = await fetch(`/search-members/?query=${encodeURIComponent(searchTerm)}`);
            if (!response.ok) throw new Error('Search failed');

            const data = await response.json();

            if (data.length > 0) {
                searchResults.innerHTML = data.map(member => `
                    <div class="search-result-item" data-member-id="${member.id}">
                        <div>${member.first_name} ${member.last_name}</div>
                        <div class="text-sm text-gray-600">${member.phone_number}</div>
                    </div>
                `).join('');
            } else {
                searchResults.innerHTML = '<div class="search-result-item">No members found</div>';
            }
            searchResults.classList.add('active');
        } catch (error) {
            console.error('Error searching members:', error);
            showMessage('Error searching for members', true);
        }
    }

    async function fetchMemberDetails(memberId) {
        try {
            const response = await fetch(`/member-details/${memberId}/`);
            if (!response.ok) throw new Error('Failed to fetch member details');

            const member = await response.json();

            // Update selected member card
            const memberNameEl = selectedMember.querySelector('.member-name');
            const memberPhoneEl = selectedMember.querySelector('.member-phone');
            const memberStatusEl = selectedMember.querySelector('.member-status');

            memberNameEl.textContent = `${member.first_name} ${member.last_name}`;
            memberPhoneEl.textContent = member.phone_number;

            // Update status and button states
            let statusText = 'Status: ';
            if (!member.is_active) {
                statusText += 'Inactive Membership';
                checkInBtn.disabled = checkOutBtn.disabled = true;
            } else if (member.is_frozen) {
                statusText += 'Membership Frozen';
                checkInBtn.disabled = checkOutBtn.disabled = true;
            } else if (member.membership_expiry && new Date(member.membership_expiry) < new Date()) {
                statusText += 'Membership Expired';
                checkInBtn.disabled = checkOutBtn.disabled = true;
            } else {
                statusText += member.current_status === 'check_in' ? 'Checked In' : 'Checked Out';
                checkInBtn.disabled = member.current_status === 'check_in';
                checkOutBtn.disabled = member.current_status === 'check_out';
            }

            memberStatusEl.textContent = statusText;
            selectedMember.style.display = 'block';
            selectedMemberId = memberId;

        } catch (error) {
            console.error('Error fetching member details:', error);
            showMessage('Error fetching member details', true);
        }
    }

    async function performCheckInOut(action) {
        if (!selectedMemberId) return;

        try {
            const response = await fetch('/check-in-out/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    member_id: selectedMemberId,
                    action: action
                })
            });

            const data = await response.json();

            if (response.ok) {
                showMessage(data.message);
                // Refresh member details
                await fetchMemberDetails(selectedMemberId);
                // Refresh history table
                location.reload();
            } else {
                showMessage(data.error, true);
            }
        } catch (error) {
            console.error('Error during check-in/out:', error);
            showMessage('Error processing request', true);
        }
    }

    // Event Listeners
    searchInput.addEventListener('input', debounce(function(e) {
        const searchTerm = e.target.value.trim();
        if (searchTerm.length < 2) {
            searchResults.innerHTML = '';
            searchResults.classList.remove('active');
            return;
        }
        searchMembers(searchTerm);
    }, 300));

    searchResults.addEventListener('click', function(e) {
        const resultItem = e.target.closest('.search-result-item');
        if (!resultItem) return;

        const memberId = resultItem.dataset.memberId;
        if (memberId) {
            fetchMemberDetails(memberId);
            searchResults.classList.remove('active');
            searchInput.value = '';
        }
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchResults.contains(e.target) && !searchInput.contains(e.target)) {
            searchResults.classList.remove('active');
        }
    });

    checkInBtn.addEventListener('click', () => performCheckInOut('check_in'));
    checkOutBtn.addEventListener('click', () => performCheckInOut('check_out'));
});