# Crew Email Notification System

## Overview
Complete email notification system for crew-related activities, providing professional HTML/text emails for all major crew interactions.

## Architecture

### Email Service (`crews/email_service.py`)
Centralized service class `CrewEmailService` handles all crew-related email notifications:

```python
from crews.email_service import CrewEmailService

email_service = CrewEmailService()
email_service.send_crew_invitation(invitation)
```

### Email Types

1. **Crew Invitation** (`crew_invitation.html`)
   - Sent when a member invites someone to join
   - Includes crew details, inviter info, accept/decline buttons
   
2. **Welcome Message** (`welcome_to_crew.html`)
   - Sent when someone joins a crew
   - Includes membership details and next steps
   
3. **Role Changed** (`role_changed.html`)
   - Sent when a member's role is updated
   - Shows old/new roles and new privileges
   
4. **Member Joined** (`member_joined.html`)
   - Sent to crew admins when someone joins
   - Notifies leadership of new member
   
5. **Member Left** (`member_left.html`)
   - Sent to crew admins when someone leaves
   - Updates on crew member count

## Configuration

### Django Settings
```python
# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Development
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'   # Production

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@skatedownhills.com')
```

### Environment Variables (.env)
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@skatedownhills.com
```

## Template Structure

### Base Template (`base_email.html`)
- Responsive design
- Email-safe CSS
- Brand consistency
- Mobile-friendly layout

### Common Elements
- Header with site logo
- Professional styling
- Call-to-action buttons
- Footer with site links
- Brand colors (#e74c3c)

## Integration Points

### Views Integration
Email notifications are automatically triggered from:
- `join_crew` - Sends welcome + member joined emails
- `invite_member` - Sends invitation email
- `accept_invitation` - Sends welcome + member joined emails
- `leave_crew` - Sends member left email
- `edit_member` - Sends role changed email (if role changes)

### Example Usage
```python
# In view
if form.is_valid():
    membership = form.save()
    
    # Send email notification
    try:
        email_service = CrewEmailService()
        email_service.send_welcome_message(membership)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
```

## Testing

### Management Command
Test all email types with:
```bash
python manage.py test_crew_emails --crew-slug=your-crew --user-email=test@example.com --test-type=all
```

### Individual Email Types
```bash
python manage.py test_crew_emails --crew-slug=your-crew --user-email=test@example.com --test-type=invitation
python manage.py test_crew_emails --crew-slug=your-crew --user-email=test@example.com --test-type=welcome
python manage.py test_crew_emails --crew-slug=your-crew --user-email=test@example.com --test-type=role_change
python manage.py test_crew_emails --crew-slug=your-crew --user-email=test@example.com --test-type=member_left
```

## Development vs Production

### Development
- Uses `console` backend
- Emails displayed in terminal
- No SMTP configuration needed

### Production
- Uses `smtp` backend
- Requires SMTP server configuration
- Set environment variables for email credentials

## Email Features

### Professional Design
- Responsive layout
- Brand consistency
- Mobile-friendly
- Professional typography

### Content
- Personalized messages
- Crew-specific information
- Clear call-to-action buttons
- Helpful next steps

### Security
- Safe email rendering
- XSS protection
- Proper encoding

## Future Enhancements

### Potential Improvements
1. Email preferences/unsubscribe system
2. Email templates for bulk operations
3. Rich text editor for custom crew messages
4. Email analytics and tracking
5. Scheduled email notifications

### Bulk Operations
Consider adding email notifications for:
- Bulk member imports
- Crew announcements
- Event notifications
- Achievement notifications

## Troubleshooting

### Common Issues
1. **Emails not sending**: Check SMTP configuration
2. **Template errors**: Verify template syntax
3. **Missing crew data**: Ensure crew exists
4. **Permission errors**: Check user permissions

### Debug Steps
1. Test with console backend first
2. Verify SMTP credentials
3. Check email logs
4. Test with management command

## Maintenance

### Regular Tasks
- Monitor email delivery rates
- Update templates for new features
- Review and optimize email content
- Test with different email clients

### Code Quality
- All email methods include error handling
- Templates are well-documented
- Service class is easily extensible
- Tests cover all email types
