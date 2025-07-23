# LLM Project Context Guide
*Comprehensive context for AI assistants working on the Downhill Skateboarding Events platform*

## 🎯 **Project Overview**

**Project Name**: Downhill Skateboarding Events Platform  
**Purpose**: Community platform for downhill skateboarding enthusiasts to organize events, form crews, track results, and connect  
**Tech Stack**: Django 4.2+ | PostgreSQL | TailwindCSS | DaisyUI | Cloudinary | Allauth  
**Current Status**: Profile system with social features **COMPLETE** (~85%), crew permission system enhanced, ready for events system development

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
│   ├── settings_tab.html      # Privacy and preferences
│   └── toast_notifications.html  # Global toast notification system
└── signup_enhanced.html       # 4-step signup flow
```

### **🎉 RECENTLY COMPLETED (December 2024)**

#### **✅ Profile Following System**
- **Full social following functionality**: Follow/unfollow users with real-time AJAX updates
- **Privacy-aware following**: Respects profile visibility settings (PUBLIC/COMMUNITY/CREWS/PRIVATE)
- **Community directory**: Enhanced users list with follow buttons and user stats
- **Database optimization**: Efficient queries with select_related for follower counts
- **Mobile-responsive design**: Touch-friendly follow buttons and user cards

#### **✅ Toast Notification System Enhancement**
- **Modal-aware notifications**: Toast messages appear above DaisyUI modals instead of underneath
- **Dynamic container detection**: Automatically detects active modals and creates in-modal toast containers
- **Z-index conflict resolution**: Intelligent toast positioning with fallback to global container
- **Crew permission integration**: Seamless user feedback for permission toggle operations
- **Cross-browser compatibility**: Works with all DaisyUI modal implementations

#### **✅ Technical Infrastructure Improvements**
- **Enhanced UserProfile model**: Complete skateboarding-specific fields with privacy controls
- **Advanced privacy manager**: Field-level privacy control with viewer-specific filtering
- **Template modularization**: 7 reusable profile partial templates for maintainability
- **AJAX-powered interactions**: Real-time updates without page refreshes
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

## 🔮 **Next Development Phase: Social Features**

### **Immediate Priorities**
1. **Profile Following System** - Users can follow each other
2. **Activity Feed** - Track and display user activities  
3. **Recommendations** - AI-powered profile suggestions
4. **Verification System** - Badge system for verified users

### **Technical Approach for Social Features**
```python
# Follow system model structure
class ProfileFollow(models.Model):
    follower = ForeignKey(User, related_name='following')
    following = ForeignKey(User, related_name='followers')
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')

# Activity tracking
class ProfileActivity(models.Model):
    profile = ForeignKey(UserProfile, related_name='activities')
    activity_type = CharField(max_length=30)
    description = TextField()
    related_object_id = PositiveIntegerField(null=True)
    is_public = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
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
