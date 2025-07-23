class ProfileEditor {
    static async updateField(fieldName, newValue, currentValue) {
        if (newValue === currentValue) return false;

        try {
            const response = await fetch(profileConfig.urls.updateProfile, {
                method: 'POST',
                headers: CSRFManager.getHeaders(),
                body: JSON.stringify({ field: fieldName, value: newValue })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Update failed:', error);
            return { status: 'error', message: error.message };
        }
    }

    static createInput(fieldName, currentValue) {
        const input = document.createElement('input');
        input.type = fieldName === 'bio' ? 'textarea' : 'text';
        input.value = currentValue;
        input.className = this.getInputClass(fieldName);
        
        if (fieldName === 'username') {
            input.maxLength = 150;
            input.pattern = '^[\\w.@+-]+$';
        }

        return input;
    }

    static getInputClass(fieldName) {
        const baseClass = 'input input-bordered';
        switch(fieldName) {
            case 'username':
                return `${baseClass} text-3xl font-bold`;
            case 'bio':
                return `${baseClass} w-full min-h-[100px]`;
            default:
                return `${baseClass} w-full`;
        }
    }

    static createDisplayElement(fieldName, value) {
        const element = document.createElement(fieldName === 'bio' ? 'div' : 'span');
        element.className = `${fieldName}-display ` + 
            (fieldName === 'username' ? 'text-3xl font-bold' : '');
        element.textContent = value;
        return element;
    }

    static updateAvatar(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = async (e) => {
                const data = await this.updateField('avatar', e.target.result);
                if (data.status === 'success') {
                    document.getElementById('avatar-image').src = data.avatar_url;
                }
            };
            
            reader.readAsDataURL(input.files[0]);
        }
    }
}

// Global function needed for inline HTML handlers
window.editField = async function(fieldName) {
    const displayElem = document.querySelector(`.${fieldName}-display`);
    if (!displayElem) return;
    
    const currentValue = displayElem.textContent.trim();
    const input = ProfileEditor.createInput(fieldName, currentValue);
    
    displayElem.replaceWith(input);
    input.focus();

    async function saveChanges() {
        const newValue = input.value.trim();
        if (newValue === currentValue) {
            input.replaceWith(displayElem);
            return;
        }

        try {
            const data = await ProfileEditor.updateField(fieldName, newValue, currentValue);
            if (data.status === 'success') {
                const newDisplay = ProfileEditor.createDisplayElement(fieldName, newValue);
                
                if (fieldName === 'instagram') {
                    const link = input.closest('a');
                    if (link) {
                        link.href = `https://instagram.com/${newValue}`;
                    }
                }
                
                input.replaceWith(newDisplay);
            } else {
                throw new Error(data.message || 'Update failed');
            }
        } catch (error) {
            alert(error.message || 'Failed to update field');
            input.replaceWith(displayElem);
        }
    }

    input.addEventListener('blur', saveChanges);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            saveChanges();
        }
        if (e.key === 'Escape') {
            input.replaceWith(displayElem);
        }
    });
};

// Update the avatar handler to show errors properly
window.updateAvatar = function(input) {
    ProfileEditor.updateAvatar(input).catch(error => {
        alert('Failed to update avatar: ' + error.message);
    });
};