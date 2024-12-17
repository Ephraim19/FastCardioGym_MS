document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const memberTableBody = document.getElementById('memberTableBody');
    
    if (searchInput && memberTableBody) {
        searchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const rows = memberTableBody.getElementsByTagName('tr');
            
            Array.from(rows).forEach(row => {
                const cells = row.getElementsByTagName('td');
                const rowText = Array.from(cells)
                    .map(cell => cell.textContent.toLowerCase())
                    .join(' ');
                
                row.style.display = rowText.includes(searchValue) ? '' : 'none';
            });
        });
    }
});