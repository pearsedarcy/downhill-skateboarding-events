document.addEventListener('DOMContentLoaded', function() {
    const favoriteBtn = document.getElementById('favoriteBtn');
    const rsvpBtn = document.getElementById('rsvpBtn');

    if (favoriteBtn) {
        favoriteBtn.addEventListener('click', function() {
            fetch(favoriteBtn.dataset.url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
            })
            .then(response => response.json())
            .then(data => {
                const btnText = document.getElementById('favoriteBtnText');
                
                if (data.is_favorited) {
                    favoriteBtn.classList.remove('btn-ghost');
                    favoriteBtn.classList.add('btn-primary');
                    btnText.textContent = 'Favorited';
                } else {
                    favoriteBtn.classList.remove('btn-primary');
                    favoriteBtn.classList.add('btn-ghost');
                    btnText.textContent = 'Add to Favorites';
                }
            });
        });
    }

    if (rsvpBtn) {
        function updateRSVP(status) {
            const formData = new FormData();
            formData.append('status', status);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
            
            fetch(rsvpBtn.dataset.url, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const btnText = document.getElementById('rsvpBtnText');
                const dropdownMenu = rsvpBtn.nextElementSibling;
                const menuItems = dropdownMenu.getElementsByTagName('a');
                
                // Update button state
                if (data.status) {
                    rsvpBtn.className = `btn btn-lg gap-2 ${
                        data.status === 'Going' ? 'btn-primary' : 
                        data.status === 'Not interested' ? 'btn-error' : 
                        'btn-secondary'
                    }`;
                    btnText.textContent = data.status;
                    
                    // Update icon
                    const icon = rsvpBtn.querySelector('i:first-child');
                    icon.className = `fas ${
                        data.status === 'Going' ? 'fa-check-circle' :
                        data.status === 'Not interested' ? 'fa-times-circle' :
                        'fa-star'
                    }`;
                } else {
                    rsvpBtn.className = 'btn btn-ghost btn-lg gap-2';
                    btnText.textContent = 'RSVP';
                }
                
                // Update checkmarks
                Array.from(menuItems).forEach(item => {
                    const checkIcon = item.querySelector('.fa-check');
                    if (checkIcon) checkIcon.remove();
                    
                    if (item.textContent.trim().includes(data.status)) {
                        item.innerHTML += ' <i class="fas fa-check text-success"></i>';
                    }
                });
                
                // Close dropdown
                dropdownMenu.blur();
            });
        }

        const dropdownMenu = rsvpBtn.nextElementSibling;
        const menuItems = dropdownMenu.getElementsByTagName('a');
        Array.from(menuItems).forEach(item => {
            item.addEventListener('click', function() {
                updateRSVP(item.textContent.trim());
            });
        });
    }
});
