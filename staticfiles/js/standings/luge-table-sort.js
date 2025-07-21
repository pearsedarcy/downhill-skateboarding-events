// Initialize sorting directions for luge table
let sortDirectionsLuge = {
    0: 'desc',  // Rank - initially descending
    1: 'desc',  // Name - initially descending
    2: 'asc',   // Points - initially ascending
    3: 'desc',  // Events - initially descending
    4: 'desc',  // Avg. Rank - initially descending
    5: 'asc',   // Alva - initially ascending
    6: 'asc',   // Veko - initially ascending
    7: 'asc',   // Vercors - initially ascending
    8: 'asc',   // Sornetan - initially ascending
    9: 'asc'    // Arena - initially ascending
};

// Initialize table when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Set default sort direction for each column
    const table = document.querySelector('.table');
    const headers = table.querySelectorAll('thead th');
    
    // Make sure all headers have sort icons
    headers.forEach((header, index) => {
        const sortIcon = header.querySelector('.sort-icon');
        if (!sortIcon) {
            const span = document.createElement('span');
            span.className = 'sort-icon';
            span.textContent = '↕';
            header.appendChild(span);
        }
    });
});

function sortTableLuge(columnIndex) {
    const table = document.querySelector('.table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const headers = table.querySelectorAll('thead th');
    
    // Update sort direction
    sortDirectionsLuge[columnIndex] = sortDirectionsLuge[columnIndex] === 'asc' ? 'desc' : 'asc';
    
    // Reset all sort icons
    headers.forEach(header => {
        const sortIcon = header.querySelector('.sort-icon');
        if (sortIcon) {
            sortIcon.textContent = '↕';
        }
    });
    
    // Update clicked header's sort icon
    const clickedSortIcon = headers[columnIndex]?.querySelector('.sort-icon');
    if (clickedSortIcon) {
        clickedSortIcon.textContent = sortDirectionsLuge[columnIndex] === 'asc' ? '↑' : '↓';
    }

    // Sort the rows - only sort rows that have actual data
    const validRows = rows.filter(row => row.cells.length >= 2);
    
    validRows.sort((a, b) => {
        let aValue, bValue;
        
        // Make sure cells exist at the specified index
        if (!a.cells[columnIndex] || !b.cells[columnIndex]) {
            return 0;
        }
        
        if (columnIndex === 0) {  // Rank
            // Handle medal emojis in the first column
            const aText = a.cells[0].textContent.trim();
            const bText = b.cells[0].textContent.trim();
            
            // Check if the cell contains medal emoji
            if (aText.includes('🥇')) aValue = 1;
            else if (aText.includes('🥈')) aValue = 2;
            else if (aText.includes('🥉')) aValue = 3;
            else aValue = parseInt(aText) || 999;
            
            if (bText.includes('🥇')) bValue = 1;
            else if (bText.includes('🥈')) bValue = 2;
            else if (bText.includes('🥉')) bValue = 3;
            else bValue = parseInt(bText) || 999;
            
        } else if (columnIndex === 1) {  // Name
            aValue = a.cells[1].textContent.trim();
            bValue = b.cells[1].textContent.trim();
            
        } else if (columnIndex >= 2 && columnIndex <= 4) {  // Points, Events, Avg. Rank
            const aBadge = a.cells[columnIndex].querySelector('.badge');
            const bBadge = b.cells[columnIndex].querySelector('.badge');
            
            aValue = aBadge ? parseInt(aBadge.textContent.trim()) : parseInt(a.cells[columnIndex].textContent.trim());
            bValue = bBadge ? parseInt(bBadge.textContent.trim()) : parseInt(b.cells[columnIndex].textContent.trim());
            
            if (isNaN(aValue)) aValue = -1;
            if (isNaN(bValue)) bValue = -1;
            
        } else {  // Alva, Veko, Vercors, Sornetan
            const aText = a.cells[columnIndex].textContent.trim();
            const bText = b.cells[columnIndex].textContent.trim();
            
            if (aText === '-') {
                aValue = -1;
            } else {
                const aMatch = aText.match(/(\d+)/);
                aValue = aMatch ? parseInt(aMatch[0]) : -1;
            }
            
            if (bText === '-') {
                bValue = -1;
            } else {
                const bMatch = bText.match(/(\d+)/);
                bValue = bMatch ? parseInt(bMatch[0]) : -1;
            }
        }
        
        // Compare the values
        if (columnIndex === 1) {  // String comparison for names
            return sortDirectionsLuge[columnIndex] === 'asc' 
                ? aValue.localeCompare(bValue)
                : bValue.localeCompare(aValue);
        } else {  // Numeric comparison for other columns
            return sortDirectionsLuge[columnIndex] === 'asc'
                ? aValue - bValue
                : bValue - aValue;
        }
    });

    // Reorder only the valid rows, leaving any spacer or header rows in place
    const nonSortableRows = rows.filter(row => row.cells.length < 2);
    tbody.innerHTML = '';
    
    // First add back any non-sortable rows at the top
    nonSortableRows.forEach(row => tbody.appendChild(row));
    
    // Then add the sorted data rows
    validRows.forEach(row => tbody.appendChild(row));
}
