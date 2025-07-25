# Email Preferences Feature Documentation

## Overview
The Email Preferences system provides users with granular control over the types of email notifications they receive from the Downhill Skateboarding Events platform. This feature is integrated into the user profile settings and provides a professional, mobile-responsive interface for managing email communications.

## Features Implemented

### 1. Granular Email Controls
Users can individually control the following email types:
- **Community Updates**: News, features, and community highlights
- **Event Notifications**: New events, registrations, and reminders  
- **Newsletter**: Monthly curated content and skating tips
- **Crew Activity**: Invitations, updates, and crew messages
- **Marketing & Promotions**: Gear deals, sponsors, and special offers

### 2. Professional Unsubscribe Interface
- **DaisyUI Modal**: Replaces browser confirm dialogs with professional modal
- **Detailed Explanation**: Lists exactly what emails will be affected
- **Visual Feedback**: Loading states and success/error messages
- **Bulk Operations**: "Unsubscribe All" function with individual API calls

### 3. Real-Time Updates
- **AJAX-Powered**: All preference changes happen without page refresh
- **Visual Feedback**: Toggles show loading states during updates
- **Error Handling**: Failed updates revert toggles and show error messages
- **Toast Notifications**: Success/error messages with appropriate icons

## Technical Implementation

### Database Schema
```python
# profiles/models.py
class UserProfile(SearchableModel):
    # Email Communication Preferences
    email_event_notifications = models.BooleanField(
        default=True,
        help_text="Receive notifications about new events and event updates"
    )
    email_community_news = models.BooleanField(
        default=True,
        help_text="Receive community news, featured riders, and safety updates"
    )
    email_newsletter = models.BooleanField(
        default=True,
        help_text="Receive monthly newsletter with curated content and tips"
    )
    email_crew_invites = models.BooleanField(
        default=True,
        help_text="Receive notifications about crew invitations and activities"
    )
    email_marketing = models.BooleanField(
        default=False,
        help_text="Receive marketing emails and promotional offers"
    )
```

### API Endpoint
```python
# profiles/views.py
def update_profile_api(request):
    """Enhanced API endpoint for updating profile fields with email preferences"""
    field_validations = {
        # ... existing fields ...
        # Email preference fields
        'email_event_notifications': {'type': 'boolean'},
        'email_community_news': {'type': 'boolean'},
        'email_newsletter': {'type': 'boolean'},
        'email_crew_invites': {'type': 'boolean'},
        'email_marketing': {'type': 'boolean'}
    }
```

### Frontend Implementation
```javascript
// Real-time toggle updates
function updateToggle(element) {
    const field = element.dataset.field;
    const value = element.checked;
    
    fetch('/profiles/api/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ field: field, value: value })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Email preferences updated!`, 'success');
        } else {
            element.checked = !value; // Revert on error
            showToast(`Error: ${data.error}`, 'error');
        }
    });
}
```

### Modal Interface
```html
<!-- Professional unsubscribe confirmation modal -->
<dialog id="unsubscribe_modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">
            <i class="fas fa-envelope-slash text-warning mr-2"></i>
            Unsubscribe from All Emails
        </h3>
        <p class="py-4">Are you sure you want to unsubscribe from all email notifications?</p>
        <ul class="list-disc list-inside space-y-1 text-sm mb-6">
            <li>Community updates and news</li>
            <li>Event notifications and reminders</li>
            <li>Monthly newsletter</li>
            <li>Crew activity and invitations</li>
            <li>Marketing and promotional emails</li>
        </ul>
        <div class="modal-action">
            <button class="btn btn-ghost" onclick="closeUnsubscribeModal()">Cancel</button>
            <button class="btn btn-warning" onclick="confirmUnsubscribeAll()">
                Yes, Unsubscribe All
            </button>
        </div>
    </div>
</dialog>
```

## UI/UX Design

### Mobile-First Layout
- **Responsive Grid**: 1 column on mobile, 2 columns on medium screens
- **Touch-Friendly Toggles**: Large DaisyUI toggle switches
- **Clear Descriptions**: Each email type has descriptive text
- **Visual Hierarchy**: Info color scheme for email preferences section

### Error Handling
- **Graceful Degradation**: Falls back to alert() if toast system unavailable
- **Visual Feedback**: Toggles revert to previous state on API failures
- **Loading States**: Toggles disabled during API requests
- **Console Logging**: Detailed error logging for debugging

## Integration Points

### Email Service Integration
The email preferences connect with the existing email service system:
```python
# profiles/email_service.py
class EmailService:
    def should_send_email(self, user, email_type):
        """Check if user wants to receive this type of email"""
        profile = user.profile
        preferences = {
            'event': profile.email_event_notifications,
            'community': profile.email_community_news,
            'newsletter': profile.email_newsletter,
            'crew': profile.email_crew_invites,
            'marketing': profile.email_marketing
        }
        return preferences.get(email_type, False)
```

### Crew System Integration
Crew invitations respect the `email_crew_invites` preference:
```python
# crews/email_service.py
def send_invitation_email(self, invitation):
    if invitation.invitee.profile.email_crew_invites:
        # Send invitation email
        pass
    else:
        # Skip email, user has disabled crew notifications
        pass
```

## Testing Considerations

### Frontend Testing
- Test toggle functionality with network failures
- Verify modal backdrop click behavior
- Test unsubscribe all function with mixed toggle states
- Validate mobile touch interactions

### Backend Testing
- Test API endpoint with invalid field names
- Verify boolean field validation
- Test concurrent updates to preferences
- Validate CSRF protection

### Integration Testing
- Test email service respects preferences
- Verify crew invitation system integration
- Test email preferences in signup flow
- Validate preference persistence across sessions

## Security Considerations

### CSRF Protection
All AJAX requests include CSRF tokens from either:
- Form hidden input: `document.querySelector('[name=csrfmiddlewaretoken]')`
- Cookie fallback: `document.cookie` parsing for `csrftoken`

### Field Validation
Server-side validation ensures only valid email preference fields can be updated:
```python
field_validations = {
    'email_event_notifications': {'type': 'boolean'},
    # ... other validated fields
}
if field not in field_validations:
    return JsonResponse({'success': False, 'error': 'Invalid field'})
```

### Privacy Compliance
- Users have full control over email communications
- Clear descriptions of what each email type contains
- Easy unsubscribe mechanism for all emails
- Preferences persist and are respected by all email systems

## Future Enhancements

### Possible Additions
1. **Email Frequency Control**: Daily, weekly, monthly batching options
2. **Smart Defaults**: AI-powered preference suggestions based on user activity
3. **Email Preview**: Show examples of each email type before subscribing
4. **Temporary Quiet Mode**: Pause all emails for a specified duration
5. **Advanced Filtering**: Keyword-based filtering for community updates
6. **Email Analytics**: Show user their email engagement statistics

### Technical Improvements
1. **Batch Updates**: Single API call for multiple preference changes
2. **WebSocket Integration**: Real-time preference sync across multiple devices
3. **Email Templates**: Dynamic email content based on user preferences
4. **A/B Testing**: Framework for testing different email preference interfaces
