
let editMode = false;

document.addEventListener('DOMContentLoaded', () => {
    new TabManager();
    
    // Initialize any other necessary components
    document.getElementById('avatar-upload')?.addEventListener('change', (e) => {
        ProfileEditor.updateAvatar(e.target);
    });
});

window.toggleEditMode = function() {
    editMode = !editMode;
    document.querySelectorAll('.edit-button')
        .forEach(btn => btn.classList.toggle('hidden', !editMode));
    
    const toggleBtn = document.getElementById('edit-toggle-btn');
    toggleBtn.classList.toggle('btn-primary', editMode);
    toggleBtn.classList.toggle('btn-ghost', !editMode);
};