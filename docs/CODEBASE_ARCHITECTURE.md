# Codebase Architecture Guide
*Detailed technical architecture for developers and LLMs*

## 🏗️ **Project Architecture Overview**

### **High-Level System Design**
```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  Templates  │ │ TailwindCSS │ │  JavaScript │           │
│  │  (Django)   │ │   DaisyUI   │ │   Modules   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
├─────────────────────────────────────────────────────────────┤
│                  Application Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Views     │ │    Forms    │ │   APIs      │           │
│  │  (Django)   │ │ Validation  │ │ (RESTful)   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
├─────────────────────────────────────────────────────────────┤
│                    Business Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Models    │ │  Managers   │ │  Services   │           │
│  │ (Database)  │ │   Utils     │ │   Logic     │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
├─────────────────────────────────────────────────────────────┤
│                     Data Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ PostgreSQL  │ │ Cloudinary  │ │   Redis     │           │
│  │ (Primary)   │ │   (Media)   │ │  (Cache)    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 📱 **App-by-App Architecture**

### **1. Profiles App** (Recently Completed)
**Purpose**: User identity and profile management  
**Status**: ✅ Production-ready with comprehensive features

#### **Model Architecture**
```python
UserProfile (Primary Model)
├── Core Identity Fields
│   ├── user (OneToOne → User)
│   ├── display_name
│   └── bio
├── Skateboarding Profile
│   ├── skating_style
│   ├── skill_level (1-10)
│   ├── years_skating
│   ├── stance (Regular/Goofy)
│   └── primary_setup
├── Location & Contact
│   ├── country (CountryField)
│   ├── city
│   └── timezone
├── Social Media
│   ├── instagram
│   ├── youtube
│   ├── facebook
│   ├── tiktok
│   └── website
└── Privacy & Meta
    ├── profile_visibility
    ├── show_real_name
    ├── show_location
    ├── verification_status
    └── profile_completion_percentage
```

#### **View Hierarchy**
```python
ProfileDetailView (DetailView)
├── Privacy filtering via ProfilePrivacyManager
├── Context: stats, events, social links
└── Template: user_profile.html (single-page)

ProfileEditView (UpdateView)
├── Form: ProfileEditForm
├── Security: LoginRequiredMixin
└── AJAX: ProfileAPIView for real-time updates

ProfileAPIView (View)
├── Actions: update_field, upload_avatar
├── Validation: Field-specific cleaning
└── Response: Standard JSON format
```

#### **Template Structure**
```
user_profile.html (Main)
├── Header Section (avatar, name, stats)
├── partials/events_tab.html
├── partials/activity_tab.html  
├── partials/social_tab.html
├── partials/settings_tab.html
└── partials/edit_modal.html
```

### **2. Events App**
**Purpose**: Event creation, management, and participation  
**Status**: 🔄 Core functionality complete, integration ongoing

#### **Model Relationships**
```python
Event
├── organizer (FK → User)
├── location (CharField + coordinates)
├── event_type (Choices)
├── difficulty_level (1-5)
└── max_participants

EventParticipant (M2M through)
├── user (FK → User)
├── event (FK → Event)  
├── rsvp_status
└── registration_date

EventReview
├── reviewer (FK → User)
├── event (FK → Event)
├── rating (1-5)
└── review_text
```

### **3. Crews App**
**Purpose**: Team/group management with sophisticated permissions  
**Status**: 🔄 Advanced permissions system implemented

#### **Permission Architecture**
```python
Crew
├── name, description, location
├── privacy_level (Public/Private/Invite)
└── max_members

CrewMembership (Through Model)
├── user (FK → User)
├── crew (FK → Crew)
├── role (Member/Admin/Owner)
├── permissions (JSONField)
└── joined_date

CrewPermission (Dynamic System)
├── permission_name
├── description  
├── category
└── requires_approval
```

### **4. Results App**
**Purpose**: Competition timing and results tracking  
**Status**: 🔄 Basic structure, needs integration

#### **Data Structure**
```python
Competition
├── event (FK → Event)
├── competition_type
├── timing_method
└── status

Result
├── competition (FK → Competition)
├── participant (FK → User)
├── time_recorded
├── position
└── verified
```

## 🔐 **Security Architecture**

### **Authentication Flow**
```
User Registration (Enhanced 4-step)
├── Step 1: Basic account (email, password)
├── Step 2: Profile info (name, location)  
├── Step 3: Skateboarding profile
├── Step 4: Social links & preferences
└── Auto-login → Profile completion

Django Allauth Integration
├── Social auth ready (Google, Facebook)
├── Email verification
├── Password reset
└── Account management
```

### **Privacy System**
```python
class ProfilePrivacyManager:
    """Centralized privacy control system"""
    
    VISIBILITY_LEVELS = {
        'PUBLIC': 'Everyone can see',
        'COMMUNITY': 'Logged-in users only', 
        'CREWS': 'Crew members only',
        'PRIVATE': 'Owner only'
    }
    
    def can_view_field(self, field_name):
        # Field-level privacy checking
        
    def filter_content(self, content_dict):
        # Content filtering based on viewer
```

### **CSRF Protection**
```javascript
// Consistent CSRF handling across all AJAX
class CSRFManager {
    static getToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
    
    static getHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getToken()
        };
    }
}
```

## 🎨 **Frontend Architecture**

### **CSS Framework Stack**
```
TailwindCSS (Utility-first)
├── Custom skateboard color scheme
├── Responsive breakpoints (sm, md, lg, xl)
└── Dark mode support

DaisyUI (Component library)
├── Cards, buttons, modals
├── Stats components
├── Navigation elements
└── Form components

Custom CSS
├── Skateboard-specific styling
├── Animation and transitions
└── Print styles
```

### **JavaScript Architecture**
```
Module Organization
├── CSRFManager.js (CSRF token handling)
├── ProfileEditor.js (Profile editing logic)
├── FormValidation.js (Real-time validation)
└── ModalManager.js (Modal controls)

Design Patterns
├── Class-based modules
├── Event delegation
├── Progressive enhancement
└── Error handling
```

### **Responsive Design System**
```css
/* Mobile-first responsive padding system */
.responsive-padding {
    @apply p-2 sm:p-3 lg:p-6;
}

/* Typography scaling */
.responsive-text {
    @apply text-xs sm:text-sm lg:text-base;
}

/* Component sizing */
.responsive-avatar {
    @apply w-20 h-20 sm:w-28 sm:h-28 md:w-40 md:h-40;
}
```

## 🗄️ **Database Architecture**

### **Core Relationships**
```sql
-- User is the central entity
User (Django Auth)
├── UserProfile (1:1)
├── CrewMembership (1:M)
├── EventParticipant (1:M)
├── Results (1:M)
└── Activities (1:M)

-- Privacy-aware queries
SELECT * FROM profiles_userprofile 
WHERE profile_visibility = 'PUBLIC' 
   OR (profile_visibility = 'COMMUNITY' AND viewer_is_authenticated)
   OR (id = viewer_profile_id);
```

### **Search Implementation**
```python
# Full-text search with weights
class SearchableModel(models.Model):
    search_vector = SearchVectorField(null=True)
    search_fields = []  # Override in subclasses
    search_field_weights = {}  # Field importance
    
    def update_search_vector(self):
        # Update search index with weighted fields
```

### **Performance Optimizations**
```python
# Standard query optimization patterns
profiles = UserProfile.objects.select_related('user').prefetch_related(
    'crew_memberships__crew',
    'events_organized',
    'event_participations__event'
)

# Caching strategy
@cache_result(timeout=3600, key_prefix='profile_stats')
def get_profile_statistics(profile_id):
    # Expensive calculations cached
```

## 🔄 **API Architecture**

### **RESTful Endpoint Design**
```python
# Standard API patterns
/api/profiles/              # GET: List profiles
/api/profiles/<username>/   # GET: Profile detail
/api/profiles/me/          # GET/PUT: Current user profile
/api/profiles/me/avatar/   # POST: Avatar upload
/api/profiles/me/privacy/  # PUT: Privacy settings

# Response format standard
{
    "status": "success|error",
    "data": {},
    "message": "Human readable message",
    "errors": {},
    "meta": {
        "timestamp": "2024-12-19T10:30:00Z",
        "version": "v1"
    }
}
```

### **AJAX Request Patterns**
```javascript
// Standard AJAX request structure
async function updateProfile(field, value) {
    try {
        const response = await fetch('/api/profiles/me/', {
            method: 'PUT',
            headers: CSRFManager.getHeaders(),
            body: JSON.stringify({
                action: 'update_field',
                field: field,
                value: value
            })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            // Update UI
        } else {
            // Handle errors
        }
    } catch (error) {
        // Handle network errors
    }
}
```

## 🧪 **Testing Architecture**

### **Test Data Management**
```python
# Management commands for test data
class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create test users (IDs 100-113)
        # Set consistent passwords
        # Load realistic skateboarding data
        # Respect privacy settings in test data
```

### **Test Coverage Strategy**
```python
# Model tests
class UserProfileModelTests(TestCase):
    def test_profile_completion_calculation(self):
        # Test completion percentage logic
    
    def test_privacy_field_visibility(self):
        # Test privacy manager functionality

# View tests  
class ProfileViewTests(TestCase):
    def test_profile_privacy_restrictions(self):
        # Test view access controls
    
    def test_api_field_updates(self):
        # Test AJAX update functionality
```

## 📈 **Performance Architecture**

### **Caching Strategy**
```python
# Multi-level caching
class ProfileCacheManager:
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def cache_profile_stats(profile_id, stats):
        cache.set(f'profile_stats:{profile_id}', stats, timeout)
    
    @staticmethod
    def invalidate_profile_cache(profile_id):
        cache.delete_many([
            f'profile_stats:{profile_id}',
            f'profile_detail:{profile_id}',
            f'profile_activities:{profile_id}'
        ])
```

### **Database Optimization**
```sql
-- Key indexes for performance
CREATE INDEX idx_profile_visibility ON profiles_userprofile(profile_visibility);
CREATE INDEX idx_profile_location ON profiles_userprofile(country, city);
CREATE INDEX idx_profile_activity ON profiles_userprofile(last_activity);
CREATE INDEX idx_profile_search ON profiles_userprofile USING gin(search_vector);
```

## 🔮 **Planned Architecture Extensions**

### **Social Features Layer**
```python
# Next phase architecture
ProfileFollow (M2M through)
├── follower (FK → User)
├── following (FK → User)
└── created_at

ActivityFeed
├── actor (FK → User)
├── verb (CharField)
├── target (Generic FK)
└── timestamp

Notification
├── recipient (FK → User)
├── message (TextField)
├── read (BooleanField)
└── created_at
```

### **AI/ML Integration Points**
```python
# Future AI features
class RecommendationEngine:
    def suggest_connections(self, user):
        # Profile similarity algorithm
    
    def recommend_events(self, user):
        # Event matching based on preferences
    
    def analyze_activity_patterns(self, user):
        # Usage analytics and insights
```

---

*This architecture guide should be referenced when making significant changes to maintain consistency and patterns.*
