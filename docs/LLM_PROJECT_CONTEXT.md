# LLM Project Context Guide
*Comprehensive context for AI assistants working on the Downhill Skateboarding Events platform*

## 🎯 **Project Overview**

**Project Name**: Downhill Skateboarding Events Platform  
**Purpose**: Community platform for downhill skateboarding enthusiasts to organize events, form crews, track results, and connect  
**Tech Stack**: Django 4.2+ | PostgreSQL | TailwindCSS | DaisyUI | Cloudinary | Allauth  
**Current Status**: Profile system **COMPLETE** (~95%), Crew joining & invitation system **COMPLETE** (~95%), Email preferences system **COMPLETE** (~100%), **NEXT**: Crews-Profiles Integration phase

## 📁 **Project Structure & App Architecture**

### **Core Django Apps**
```
downhill_skateboarding_events/  # Main project
├── events/          # Event management and organization
├── crews/           # Crew/team management with permissions
├── profiles/        # User profiles with social features (COMPLETED)
├── results/         # Competition results and timing
├── search/          # Site-wide search functionality
└── theme/           # UI/UX theme and styling
```

### **Key Implementation Patterns**

#### **Model Design Philosophy**
- **Skateboarding-Focused**: All models include skateboard-specific fields
- **Privacy-First**: Field-level privacy controls throughout
- **Community-Oriented**: Models designed for social interaction
- **Performance-Aware**: Optimized for query efficiency

#### **View Architecture**
- **Class-Based Views**: Prefer CBVs for consistency
- **API-First**: RESTful endpoints for all major operations  
- **Privacy-Aware**: All views respect user privacy settings
- **Mobile-Optimized**: Responsive design considerations

#### **Template Patterns**
- **Modular Partials**: Break complex templates into reusable components
- **DaisyUI Components**: Use DaisyUI for consistent styling
- **Mobile-First**: Always consider mobile experience first
- **Semantic HTML**: Proper accessibility and SEO structure

## 🏗️ **Recent Major Implementation: Profile System**

### **What Was Just Completed (Dec 2024)**
```python
# Enhanced UserProfile model with skateboarding-specific fields
class UserProfile(SearchableModel):
    # Core identity
    user = OneToOneField(User)
    display_name = CharField(max_length=100)
    bio = TextField(max_length=500)
    
    # Skateboarding profile
    skating_style = CharField(choices=SKATING_STYLES)
    skill_level = IntegerField(1-10 scale)
    years_skating = PositiveIntegerField()
    stance = CharField(choices=['REGULAR', 'GOOFY'])
    primary_setup = TextField(max_length=300)
    
    # Privacy controls
    profile_visibility = CharField(choices=[
        'PUBLIC', 'COMMUNITY', 'CREWS', 'PRIVATE'
    ])
    show_real_name = BooleanField()
    show_location = BooleanField()
    
    # Email communication preferences
    email_event_notifications = BooleanField(default=True)
    email_community_news = BooleanField(default=True)
    email_newsletter = BooleanField(default=True)
    email_crew_invites = BooleanField(default=True)
    email_marketing = BooleanField(default=False)
    
    # Social media integration
    instagram = CharField()
    youtube = URLField()
    facebook = URLField()
    tiktok = CharField()
    website = URLField()
```

### **Key Architecture Decisions Made**
1. **Removed Tab System**: Complex tabs replaced with single-page scrollable layout
2. **Mobile-First Design**: Responsive padding system `p-2 sm:p-3 lg:p-6`
3. **Modular Templates**: 6 partial templates for maintainability
4. **Privacy Manager**: Centralized privacy control system
5. **Real-Time Editing**: AJAX-powered inline editing throughout

### **Template Structure**
```
profiles/templates/profiles/
├── user_profile.html          # Main profile page (single-page layout)
├── users_list.html           # Community directory with following system
├── partials/
│   ├── edit_modal.html        # Profile editing modal
│   ├── events_tab.html        # Events section
│   ├── activity_tab.html      # Activity timeline
│   ├── social_tab.html        # Social links and connections
│   ├── settings_tab.html      # Privacy, email preferences, and account settings
│   └── toast_notifications.html  # Global toast notification system
└── signup_enhanced.html       # 4-step signup flow
```

### **🎉 RECENTLY COMPLETED (December 2024 - January 2025)**

#### **✅ Profile Following System**
- **Full social following functionality**: Follow/unfollow users with real-time AJAX updates
- **Privacy-aware following**: Respects profile visibility settings (PUBLIC/COMMUNITY/CREWS/PRIVATE)
- **Community directory**: Enhanced users list with follow buttons and user stats
- **Database optimization**: Efficient queries with select_related for follower counts
- **Mobile-responsive design**: Touch-friendly follow buttons and user cards

#### **✅ Complete Crew Joining & Invitation System**
- **Direct crew joining/leaving**: One-click join/leave with membership reactivation for returning members
- **Comprehensive invitation system**: Email/username invitations with role assignment and management page
- **Modern UX patterns**: DaisyUI modals replace browser confirms, AJAX operations, toast notifications
- **Membership status indicators**: Visual badges on crew lists and detail pages showing user's membership status
- **Database integrity**: Proper handling of unique constraints, soft-delete patterns, and audit logging
- **Mobile-optimized interface**: Responsive design with touch-friendly interactions

#### **✅ Toast Notification System Enhancement**
- **Modal-aware notifications**: Toast messages appear above DaisyUI modals instead of underneath
- **Dynamic container detection**: Automatically detects active modals and creates in-modal toast containers
- **Z-index conflict resolution**: Intelligent toast positioning with fallback to global container
- **Crew permission integration**: Seamless user feedback for permission toggle operations
- **Cross-browser compatibility**: Works with all DaisyUI modal implementations

#### **✅ Email Preferences System**
- **Granular email controls**: Individual toggles for event notifications, community news, newsletter, crew invites, and marketing emails
- **Professional unsubscribe modal**: DaisyUI modal interface replacing browser confirm dialogs with detailed explanation of affected email types
- **Real-time preference updates**: AJAX-powered toggles with visual feedback and error handling
- **Backend validation**: Secure API endpoint with proper field validation and error responses
- **Mobile-optimized interface**: Touch-friendly toggles with clear descriptions and responsive grid layout
- **Integration with existing systems**: Email preferences connect with crew invitation and event notification systems

#### **✅ Technical Infrastructure Improvements**
- **Enhanced UserProfile model**: Complete skateboarding-specific fields with privacy controls
- **Advanced privacy manager**: Field-level privacy control with viewer-specific filtering
- **Template modularization**: Reusable profile and crew partial templates for maintainability
- **AJAX-powered interactions**: Real-time updates without page refreshes throughout platform
- **Performance optimizations**: Efficient database queries and caching strategies
## 🎨 **Design System & Styling**

### **DaisyUI + TailwindCSS Pattern**
```html
<!-- Standard Card Pattern -->
<div class="card bg-base-100 shadow-xl">
    <div class="card-body p-2 sm:p-3 lg:p-6">
        <h2 class="card-title text-sm sm:text-base lg:text-lg">Title</h2>
        <p class="text-xs sm:text-sm lg:text-base">Content</p>
    </div>
</div>

<!-- Stats Card Pattern -->
<div class="stats stats-vertical lg:stats-horizontal bg-base-200">
    <div class="stat">
        <div class="stat-title text-xs">Metric</div>
        <div class="stat-value text-sm sm:text-lg">Value</div>
    </div>
</div>
```

### **Responsive Design Philosophy**
- **Mobile-First**: Start with mobile constraints
- **Progressive Enhancement**: Add desktop features
- **Consistent Spacing**: Use responsive padding system
- **Touch-Friendly**: Minimum 44px touch targets

### **Skateboard Theme Elements**
```css
/* Custom color scheme for skateboarding */
:root {
    --skateboard-primary: #ff6b35;    /* Orange/red for energy */
    --skateboard-secondary: #004e89;  /* Deep blue for trust */
    --skateboard-accent: #f7931e;     /* Bright orange for action */
}
```

## 🔐 **Security & Privacy Patterns**

### **Privacy Manager System**
```python
class ProfilePrivacyManager:
    def __init__(self, profile, viewer):
        self.profile = profile
        self.viewer = viewer
    
    def can_view_field(self, field_name):
        """Determine if viewer can see specific profile field"""
        # Implementation handles privacy levels
    
    def filter_content(self, content_dict):
        """Filter content based on privacy settings"""
        # Returns filtered data based on viewer permissions
```

### **CSRF Protection Pattern**
```javascript
// Standard CSRF handling for AJAX requests
class CSRFManager {
    static getHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        };
    }
}
```

## 🗄️ **Database Design Patterns**

### **Search Optimization**
```python
# All major models inherit SearchableModel
class SearchableModel(models.Model):
    search_fields = ['field1', 'field2']
    search_field_weights = {
        'field1': 'A',  # Highest priority
        'field2': 'B'   # Medium priority
    }
    
    class Meta:
        abstract = True
```

### **Relationship Patterns**
- **User Profile**: OneToOne with User model
- **Privacy Aware**: All relationships consider visibility
- **Soft Relationships**: Use JSONField for flexible associations
- **Activity Tracking**: Generic foreign keys for polymorphic relationships

## 🔄 **API Design Patterns**

### **RESTful Endpoint Structure**
```python
# Standard API view pattern
class ProfileAPIView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        if action == 'update_field':
            return self.update_field(request)
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    def update_field(self, request):
        # Validate, update, return JSON response
        return JsonResponse({'status': 'success', 'data': {}})
```

### **Response Format Standards**
```json
{
    "status": "success|error",
    "message": "Human readable message",
    "data": {}, 
    "errors": {},
    "redirect_url": "/optional/redirect/"
}
```

## 🎭 **User Experience Patterns**

### **Form Handling Philosophy**
- **Real-Time Validation**: Immediate feedback on input
- **Progressive Enhancement**: Works without JavaScript
- **Clear Error Messages**: User-friendly error communication
- **Auto-Save**: Prevent data loss on long forms

### **Navigation Patterns**
```html
<!-- Breadcrumb Pattern -->
<div class="breadcrumbs text-sm">
    <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/profiles/">Profiles</a></li>
        <li>{{ profile.display_name }}</li>
    </ul>
</div>
```

### **Modal System**
```html
<!-- Standard Modal Pattern -->
<div class="modal" id="editModal">
    <div class="modal-box w-11/12 max-w-2xl">
        <form method="post" class="space-y-4">
            {% csrf_token %}
            <!-- Form content -->
            <div class="modal-action">
                <button type="submit" class="btn btn-primary">Save</button>
                <button type="button" class="btn" onclick="closeModal()">Cancel</button>
            </div>
        </form>
    </div>
</div>
```

## 🧪 **Testing Patterns**

### **Test User Management**
```python
# Management command for test data
class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create test users (IDs 100-113)
        # Set consistent passwords for easy testing
        # Load realistic test data
```

### **Test Data Philosophy**
- **Realistic Data**: Use actual skateboarding terms and locations
- **Privacy Testing**: Test all privacy level combinations
- **Edge Cases**: Empty profiles, maxed out profiles, etc.

## 📈 **Performance Considerations**

### **Query Optimization**
```python
# Always use select_related/prefetch_related
profiles = UserProfile.objects.select_related('user').prefetch_related(
    'events_organized', 'crew_memberships'
)
```

### **Caching Strategy**
```python
# Profile data caching pattern
@cache_result(timeout=3600)
def get_profile_stats(profile_id):
    # Expensive calculations cached for 1 hour
    return stats_data
```

## 🔮 **Next Development Phase: Crews-Profiles Integration**

### **Immediate Priorities**
1. **Profile-Linked Crew Members** - Clickable profile links in crew member lists with preview functionality
2. **Working Invitation System** - Complete UI/UX for crew invitations with user search and notifications  
3. **Crew-Aware Profile Discovery** - Find crew mates to follow and crew context in user lists
4. **Enhanced Privacy Integration** - CREWS visibility level implementation across both apps

### **Technical Approach for Integration**
```python
# Enhanced CrewMembership with profile integration
class CrewMembership(models.Model):
    # ... existing fields ...
    
    profile_visibility = models.CharField(max_length=20, choices=[
        ('PUBLIC', 'Show publicly in crew'),
        ('CREW_ONLY', 'Show only to crew members'),
        ('HIDDEN', 'Don\'t show in crew lists')
    ], default='PUBLIC')
    
    def get_profile_link(self):
        return reverse('profiles:user_profile', args=[self.user.userprofile.slug])
    
    def get_profile_preview_data(self):
        """Get data for profile preview modal/card"""
        return {
            'display_name': self.user.userprofile.display_name,
            'skating_style': self.user.userprofile.get_skating_style_display(),
            'skill_level': self.user.userprofile.skill_level,
            'can_follow': True,  # Based on privacy settings
        }

# Enhanced UserProfile for crew integration
class UserProfile(SearchableModel):
    # ... existing fields ...
    
    def get_crew_mates(self):
        """Get users who are in the same crews"""
        user_crews = self.user.crew_memberships.values_list('crew', flat=True)
        crew_mate_ids = CrewMembership.objects.filter(
            crew__in=user_crews
        ).exclude(user=self.user).values_list('user', flat=True).distinct()
        
        return UserProfile.objects.filter(user__in=crew_mate_ids)
```

## 🎯 **Key Success Metrics**

### **User Engagement Goals**
- Profile completion rate: 80% complete at least 60% of profile
- Monthly active users engaging with profiles
- Cross-profile interactions (follows, messages, etc.)

### **Technical Performance Goals**
- Profile page load time: <2 seconds
- API response time: <500ms
- Mobile performance score: >90

## 🛠️ **Development Guidelines for LLMs**

### **When Adding New Features**
1. **Check Privacy**: Does this feature respect user privacy settings?
2. **Mobile First**: How does this look/work on mobile?
3. **Downhill Skateboarding (Longboarding) Context**: Is this relevant to the skateboarding community?
4. **Performance**: Will this impact page load times?
5. **Accessibility**: Is this usable by all users?

### **Code Style Preferences**
- **Python**: Use type hints, descriptive variable names
- **JavaScript**: ES6+ syntax, class-based organization  
- **HTML**: Semantic structure, DaisyUI components
- **CSS**: Utility-first with TailwindCSS

### **Documentation Standards**
- **Docstrings**: All functions and classes documented
- **Comments**: Explain why, not what
- **README Updates**: Keep documentation current
- **Test Coverage**: Write tests for new functionality

---

*This document is the primary context source for LLMs working on this project. Keep it updated as the project evolves.*
