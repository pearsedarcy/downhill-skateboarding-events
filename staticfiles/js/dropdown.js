/**
 * DaisyUI Dropdown Handler
 * Handles dropdown functionality for DaisyUI dropdowns
 */
document.addEventListener('DOMContentLoaded', function() {
    // Handle all dropdowns on the page
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('[role="button"]');
        const content = dropdown.querySelector('.dropdown-content');
        
        if (!trigger || !content) return;
        
        // Toggle dropdown on click
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Close all other dropdowns first
            closeAllDropdowns(dropdown);
            
            // Toggle this dropdown
            const isOpen = dropdown.classList.contains('dropdown-open');
            
            if (isOpen) {
                closeDropdown(dropdown);
            } else {
                openDropdown(dropdown);
            }
        });
        
        // Handle keyboard navigation
        trigger.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                trigger.click();
            } else if (e.key === 'Escape') {
                closeDropdown(dropdown);
            }
        });
        
        // Allow clicks on menu items to work normally
        const menuItems = content.querySelectorAll('li a');
        menuItems.forEach(item => {
            item.addEventListener('click', function(e) {
                // Don't prevent default - allow navigation
                // Just close the dropdown after a small delay
                setTimeout(() => closeDropdown(dropdown), 50);
            });
        });
        
        // Prevent clicks on dropdown content from closing the dropdown
        content.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        const dropdown = e.target.closest('.dropdown');
        if (!dropdown) {
            closeAllDropdowns();
        }
    });
    
    // Close dropdowns on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAllDropdowns();
        }
    });
    
    function openDropdown(dropdown) {
        const trigger = dropdown.querySelector('[role="button"]');
        const content = dropdown.querySelector('.dropdown-content');
        
        if (trigger && content) {
            trigger.setAttribute('tabindex', '0');
            trigger.focus();
            
            // Add active class for styling
            dropdown.classList.add('dropdown-open');
        }
    }
    
    function closeDropdown(dropdown) {
        const trigger = dropdown.querySelector('[role="button"]');
        const content = dropdown.querySelector('.dropdown-content');
        
        if (trigger && content) {
            trigger.setAttribute('tabindex', '-1');
            
            // Remove active class
            dropdown.classList.remove('dropdown-open');
        }
    }
    
    function closeAllDropdowns(except = null) {
        dropdowns.forEach(dropdown => {
            if (dropdown !== except) {
                closeDropdown(dropdown);
            }
        });
    }
});
