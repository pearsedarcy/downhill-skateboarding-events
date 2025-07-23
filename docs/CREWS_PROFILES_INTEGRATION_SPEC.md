# Crews & Profiles Integration Specification
*Comprehensive feature specification for uniting the crews and profiles systems*

---

## 🎯 **Executive Summary**

This document outlines the complete integration between the **Crews** and **Profiles** apps to create a seamless, social skateboarding community platform. The integration will transform isolated systems into a unified experience where crew membership enhances social connections and profile relationships strengthen crew dynamics.

**Current Status**: Both apps exist independently with basic models  
**Target Status**: Fully integrated social crew system with advanced invitation, discovery, and interaction features

---

## 📊 **Current System Analysis**

### **✅ What We Have**

#### **Profiles App - COMPLETE**
- ✅ **UserProfile model** with skateboarding-specific fields
- ✅ **Following system** with UserFollow model
- ✅ **Privacy controls** (PUBLIC/COMMUNITY/CREWS/PRIVATE)
- ✅ **Community directory** with follow buttons
- ✅ **Real-time AJAX** follow/unfollow functionality
- ✅ **Profile activity tracking** and display

#### **Crews App - FOUNDATION EXISTS**
- ✅ **Crew model** with basic information and settings
- ✅ **CrewMembership model** with roles and permissions
- ✅ **CrewInvitation model** for basic invitation tracking
- ✅ **Permission system** with crew-specific roles
- ✅ **Activity logging** with CrewActivity model

### **🔄 What Needs Integration**

#### **Missing Core Features**
- ❌ **Profile links in crew member lists**
- ❌ **Crew-aware profile discovery** (find crew mates to follow)
- ❌ **Working invitation system** with UI/UX
- ❌ **Cross-app activity feeds** (crew activities in profile, profile activities in crew)
- ❌ **Crew-based privacy filtering** (CREWS visibility level)
- ❌ **Social crew discovery** (find crews through profile connections)

---

## 🚀 **Feature Specifications**

### **Phase 1: Core Integration (Priority 1)**

#### **1.1 Profile-Linked Crew Members** 🔗
**Status**: Not Implemented  
**Priority**: HIGH  
**Estimated Effort**: 2-3 hours

**Features:**
- **Clickable profile links** in crew member lists
- **Member profile previews** on hover/click in crew management
- **Profile integration** in crew member cards with stats and follow buttons
- **Crew context** in profile displays (show which crew you know them from)

**Technical Requirements:**
```python
# Add to CrewMembership model
class CrewMembership(models.Model):
    # ... existing fields ...
    
    def get_profile_link(self):
        """Get URL to member's profile page"""
        return reverse('profiles:user_profile', args=[self.user.userprofile.slug])
    
    def get_profile_preview_data(self):
        """Get data for profile preview modal/card"""
        profile = self.user.userprofile
        return {
            'display_name': profile.display_name,
            'bio': profile.bio,
            'skating_style': profile.get_skating_style_display(),
            'skill_level': profile.skill_level,
            'follower_count': profile.get_follower_count(),
            'can_follow': True,  # Based on privacy settings
        }
```

**UI/UX Requirements:**
- **Member cards** with profile photos and basic info
- **Quick follow buttons** in crew member lists
- **Profile preview modals** for crew management pages
- **Responsive design** for mobile crew management

#### **1.2 Working Invitation System** 📨
**Status**: Models exist, no UI/UX  
**Priority**: HIGH  
**Estimated Effort**: 4-5 hours

**Features:**
- **Invitation workflow** from crew management to user profiles
- **Invite by username/email** with user search functionality
- **Invitation notifications** in user's profile/dashboard
- **Accept/decline interface** with crew preview
- **Invitation management** for crew admins

**Technical Requirements:**
```python
# Enhanced CrewInvitation model
class CrewInvitation(models.Model):
    # ... existing fields ...
    
    def send_notification(self):
        """Send invitation notification to user"""
        # Email notification + in-app notification
        pass
    
    def accept(self, user):
        """Accept invitation and create membership"""
        if self.invitee_user == user and self.is_pending:
            CrewMembership.objects.create(
                crew=self.crew,
                user=user,
                role=self.proposed_role,
                invited_by=self.inviter
            )
            self.is_accepted = True
            self.responded_at = timezone.now()
            self.save()
            return True
        return False

# New views needed
class SendInvitationView(LoginRequiredMixin, View):
    """Handle sending crew invitations"""
    
class RespondToInvitationView(LoginRequiredMixin, View):
    """Handle accepting/declining invitations"""
```

**UI/UX Requirements:**
- **"Invite Members" button** in crew management
- **User search modal** with skateboarding community filtering
- **Invitation cards** in user profile with crew preview
- **Email templates** for invitation notifications
- **Success/error feedback** with toast notifications

#### **1.3 Crew-Aware Profile Discovery** 🔍
**Status**: Not Implemented  
**Priority**: MEDIUM  
**Estimated Effort**: 3-4 hours

**Features:**
- **"Crew Mates" section** in profile sidebar showing fellow crew members
- **"Find Crew Mates"** suggestion system based on shared crews
- **Crew context indicators** in users list (show shared crews)
- **Follow suggestions** based on crew membership overlap

**Technical Requirements:**
```python
# Add to UserProfile model
class UserProfile(SearchableModel):
    # ... existing fields ...
    
    def get_crew_mates(self):
        """Get users who are in the same crews"""
        user_crews = self.user.crew_memberships.values_list('crew', flat=True)
        crew_mate_ids = CrewMembership.objects.filter(
            crew__in=user_crews
        ).exclude(user=self.user).values_list('user', flat=True).distinct()
        
        return UserProfile.objects.filter(user__in=crew_mate_ids)
    
    def get_shared_crews_with_user(self, other_user):
        """Get crews that both users belong to"""
        my_crews = set(self.user.crew_memberships.values_list('crew', flat=True))
        their_crews = set(other_user.crew_memberships.values_list('crew', flat=True))
        shared_crew_ids = my_crews.intersection(their_crews)
        
        return Crew.objects.filter(id__in=shared_crew_ids)
```

**UI/UX Requirements:**
- **"Crew Mates" widget** in profile sidebar
- **Shared crew badges** in user cards
- **Enhanced users list** with crew context
- **"Suggested Follows" section** based on crew relationships

---

### **Phase 2: Advanced Social Features (Priority 2)**

#### **2.1 Cross-App Activity Feeds** 📰
**Status**: Partially Implemented  
**Priority**: MEDIUM  
**Estimated Effort**: 4-5 hours

**Features:**
- **Crew activities in profile feed** (joined crew, promoted in crew, crew event participation)
- **Profile activities in crew feed** (member achievements, profile updates, external content)
- **Unified activity timeline** showing both personal and crew activities
- **Activity privacy controls** respecting both profile and crew privacy settings

#### **2.2 Enhanced Crew Discovery** 🗺️
**Status**: Not Implemented  
**Priority**: MEDIUM  
**Estimated Effort**: 3-4 hours

**Features:**
- **"Crews Your Friends Are In"** discovery section
- **Crew recommendations** based on skating style and location
- **"Similar Crews" suggestions** based on current crew memberships
- **Crew member preview** before requesting to join

#### **2.3 Advanced Privacy Integration** 🔒
**Status**: Models ready, needs implementation  
**Priority**: HIGH  
**Estimated Effort**: 2-3 hours

**Features:**
- **CREWS visibility level** implementation in profile privacy
- **Crew-only content** visible only to crew members
- **Crew member directory** respecting individual privacy settings
- **Granular crew privacy** (different visibility for different crews)

---

### **Phase 3: Community Enhancement (Priority 3)**

#### **3.1 Crew Social Features** 👥
**Status**: Not Implemented  
**Priority**: LOW  
**Estimated Effort**: 5-6 hours

**Features:**
- **Crew member mentorship** system (experienced members guide newcomers)
- **Member spotlights** and featured profiles within crews
- **Crew skill level analytics** and member progression tracking
- **Internal crew messaging** and announcements

#### **3.2 Cross-Crew Collaboration** 🤝
**Status**: Not Implemented  
**Priority**: LOW  
**Estimated Effort**: 4-5 hours

**Features:**
- **Crew partnerships** and alliance system
- **Joint events** between multiple crews
- **Crew challenges** and competitions
- **Inter-crew member exchanges** and guest memberships

---

## 🗄️ **Database Schema Enhancements**

### **Required Model Changes**

#### **1. Enhanced CrewMembership**
```python
class CrewMembership(models.Model):
    # ... existing fields ...
    
    # New fields for profile integration
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('PUBLIC', 'Show publicly in crew'),
            ('CREW_ONLY', 'Show only to crew members'),
            ('HIDDEN', 'Don\'t show in crew lists')
        ],
        default='PUBLIC'
    )
    
    # Social integration
    allow_crew_invitations = models.BooleanField(
        default=True,
        help_text="Allow other crew members to see and invite your connections"
    )
    
    # Activity tracking
    last_active_in_crew = models.DateTimeField(auto_now=True)
```

#### **2. New Models Needed**

```python
class CrewInvitationBatch(models.Model):
    """For sending multiple invitations at once"""
    crew = models.ForeignKey(Crew, on_delete=models.CASCADE)
    inviter = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_sent = models.PositiveIntegerField(default=0)
    total_accepted = models.PositiveIntegerField(default=0)

class CrewFollowSuggestion(models.Model):
    """Track follow suggestions based on crew membership"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crew_follow_suggestions')
    suggested_user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50)  # 'SHARED_CREW', 'CREW_MATE_FOLLOWS', etc.
    crews_in_common = models.ManyToManyField(Crew, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_dismissed = models.BooleanField(default=False)
    is_followed = models.BooleanField(default=False)

class CrewMembershipRequest(models.Model):
    """For users requesting to join crews"""
    crew = models.ForeignKey(Crew, on_delete=models.CASCADE, related_name='membership_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crew_membership_requests')
    message = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_denied = models.BooleanField(default=False)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('crew', 'user')
```

#### **3. Enhanced UserProfile for Crew Integration**
```python
class UserProfile(SearchableModel):
    # ... existing fields ...
    
    # Crew preferences
    open_to_crew_invitations = models.BooleanField(
        default=True,
        help_text="Allow crew members to send you invitations"
    )
    
    max_crews = models.PositiveIntegerField(
        default=5,
        help_text="Maximum number of crews you want to be in"
    )
    
    # Social integration
    show_crew_memberships = models.BooleanField(
        default=True,
        help_text="Show your crew memberships in your profile"
    )
    
    def get_active_crews(self):
        """Get crews where user is active member"""
        return self.user.crew_memberships.filter(
            is_active=True
        ).select_related('crew')
    
    def can_join_more_crews(self):
        """Check if user can join additional crews"""
        current_count = self.user.crew_memberships.filter(is_active=True).count()
        return current_count < self.max_crews
```

---

## 🎨 **UI/UX Design Specifications**

### **Crew Member Cards Enhancement**
```html
<!-- Enhanced crew member card with profile integration -->
<div class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow">
    <div class="card-body p-4">
        <div class="flex items-center space-x-3">
            <!-- Profile Photo -->
            <div class="avatar">
                <div class="w-12 h-12 rounded-full">
                    <img src="{{ member.user.userprofile.profile_picture.url }}" 
                         alt="{{ member.user.userprofile.display_name }}">
                </div>
            </div>
            
            <!-- Member Info -->
            <div class="flex-1">
                <div class="flex items-center space-x-2">
                    <a href="{{ member.get_profile_link }}" 
                       class="font-semibold text-primary hover:text-primary-focus">
                        {{ member.user.userprofile.display_name }}
                    </a>
                    <span class="badge badge-outline badge-sm">{{ member.get_role_display }}</span>
                </div>
                <p class="text-sm text-base-content/70">
                    {{ member.user.userprofile.skating_style|title }} • 
                    Level {{ member.user.userprofile.skill_level }}
                </p>
                {% if member.nickname %}
                    <p class="text-xs text-base-content/60">"{{ member.nickname }}"</p>
                {% endif %}
            </div>
            
            <!-- Action Buttons -->
            <div class="flex space-x-1">
                <!-- Follow Button (if not following and can view) -->
                {% if not user in member.user.userprofile.followers.all and member.user != user %}
                    <button class="btn btn-sm btn-outline btn-primary follow-btn" 
                            data-user-id="{{ member.user.id }}">
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                        Follow
                    </button>
                {% endif %}
                
                <!-- Profile Preview Button -->
                <button class="btn btn-sm btn-ghost profile-preview-btn" 
                        data-user-id="{{ member.user.id }}">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                    </svg>
                </button>
            </div>
        </div>
    </div>
</div>
```

### **Invitation Interface**
```html
<!-- Crew invitation modal -->
<div class="modal" id="invite-modal">
    <div class="modal-box w-11/12 max-w-2xl">
        <h3 class="font-bold text-lg mb-4">Invite Members to {{ crew.name }}</h3>
        
        <!-- User Search -->
        <div class="form-control mb-4">
            <label class="label">
                <span class="label-text">Search for skaters</span>
            </label>
            <div class="relative">
                <input type="text" 
                       class="input input-bordered w-full pr-10" 
                       placeholder="Search by username or name..."
                       id="user-search">
                <button class="absolute right-2 top-2 btn btn-sm btn-ghost">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                </button>
            </div>
        </div>
        
        <!-- Search Results -->
        <div id="search-results" class="space-y-2 mb-4 max-h-60 overflow-y-auto">
            <!-- Dynamic search results will be populated here -->
        </div>
        
        <!-- Invitation Message -->
        <div class="form-control mb-4">
            <label class="label">
                <span class="label-text">Personal message (optional)</span>
            </label>
            <textarea class="textarea textarea-bordered" 
                      placeholder="Why should they join our crew?"></textarea>
        </div>
        
        <!-- Role Selection -->
        <div class="form-control mb-6">
            <label class="label">
                <span class="label-text">Proposed role</span>
            </label>
            <select class="select select-bordered">
                <option value="MEMBER">Member</option>
                <option value="EVENT_MANAGER">Event Manager</option>
                {% if user_can_assign_admin %}
                    <option value="ADMIN">Admin</option>
                {% endif %}
            </select>
        </div>
        
        <!-- Actions -->
        <div class="modal-action">
            <button class="btn btn-primary" id="send-invitation">Send Invitation</button>
            <button class="btn" onclick="closeModal('invite-modal')">Cancel</button>
        </div>
    </div>
</div>
```

---

## 🔄 **API Endpoints Specification**

### **New API Endpoints Needed**

```python
# URLs to add to crews/urls.py
urlpatterns = [
    # ... existing patterns ...
    
    # Member profile integration
    path('api/member/<int:user_id>/profile-preview/', views.MemberProfilePreviewAPI.as_view(), name='member_profile_preview'),
    path('api/member/<int:user_id>/follow/', views.ToggleMemberFollowAPI.as_view(), name='toggle_member_follow'),
    
    # Invitation system
    path('api/<slug:crew_slug>/invite/', views.SendInvitationAPI.as_view(), name='send_invitation'),
    path('api/invitation/<int:invitation_id>/respond/', views.RespondToInvitationAPI.as_view(), name='respond_invitation'),
    path('api/user/search/', views.UserSearchAPI.as_view(), name='user_search'),
    
    # Crew discovery
    path('api/<slug:crew_slug>/suggest-members/', views.SuggestMembersAPI.as_view(), name='suggest_members'),
    path('api/user/<int:user_id>/crew-mates/', views.CrewMatesAPI.as_view(), name='crew_mates'),
]

# URLs to add to profiles/urls.py
urlpatterns = [
    # ... existing patterns ...
    
    # Crew integration
    path('api/user/<slug:profile_slug>/crews/', views.UserCrewsAPI.as_view(), name='user_crews'),
    path('api/user/<slug:profile_slug>/crew-mates/', views.ProfileCrewMatesAPI.as_view(), name='profile_crew_mates'),
    path('api/invitations/', views.UserInvitationsAPI.as_view(), name='user_invitations'),
]
```

### **API Response Formats**

```json
// Member profile preview response
{
    "status": "success",
    "data": {
        "user_id": 123,
        "display_name": "RiderMike",
        "bio": "Downhill enthusiast from Colorado",
        "skating_style": "Downhill",
        "skill_level": 7,
        "years_skating": 5,
        "profile_picture_url": "/media/profiles/...",
        "follower_count": 45,
        "following_count": 32,
        "is_following": false,
        "can_follow": true,
        "shared_crews": [
            {
                "id": 5,
                "name": "Colorado Bombers",
                "slug": "colorado-bombers"
            }
        ],
        "profile_url": "/profiles/ridermike/"
    }
}

// User search response
{
    "status": "success",
    "data": {
        "users": [
            {
                "id": 124,
                "username": "speedracer",
                "display_name": "Speed Racer",
                "profile_picture_url": "/media/profiles/...",
                "skating_style": "Downhill",
                "location": "California, USA",
                "is_crew_member": false,
                "shared_crews": [],
                "mutual_follows": 3
            }
        ],
        "total_results": 15,
        "has_more": true
    }
}

// Send invitation response
{
    "status": "success",
    "message": "Invitation sent to Speed Racer",
    "data": {
        "invitation_id": 67,
        "expires_at": "2024-01-15T10:30:00Z"
    }
}
```

---

## 🧪 **Testing Strategy**

### **Unit Tests Required**

```python
# tests/test_crew_profile_integration.py
class CrewProfileIntegrationTests(TestCase):
    
    def test_crew_member_profile_preview(self):
        """Test profile preview data for crew members"""
        
    def test_crew_invitation_workflow(self):
        """Test complete invitation send/accept workflow"""
        
    def test_crew_mate_discovery(self):
        """Test finding crew mates functionality"""
        
    def test_privacy_integration(self):
        """Test crew visibility with profile privacy settings"""
        
    def test_follow_suggestions_from_crews(self):
        """Test follow suggestions based on crew membership"""

# tests/test_invitation_system.py
class InvitationSystemTests(TestCase):
    
    def test_send_invitation_permissions(self):
        """Test who can send invitations"""
        
    def test_invitation_expiration(self):
        """Test invitation expiration logic"""
        
    def test_duplicate_invitation_prevention(self):
        """Test preventing duplicate invitations"""
        
    def test_invitation_notifications(self):
        """Test invitation notification system"""
```

### **Integration Tests**

```python
# tests/test_ui_integration.py
class UIIntegrationTests(StaticLiveServerTestCase):
    
    def test_crew_member_follow_button(self):
        """Test follow button in crew member lists"""
        
    def test_invitation_modal_workflow(self):
        """Test complete invitation modal workflow"""
        
    def test_profile_preview_modal(self):
        """Test profile preview modal in crew context"""
```

---

## 📱 **Mobile Considerations**

### **Responsive Design Requirements**
- **Touch-friendly** invitation interface
- **Swipe gestures** for crew member cards
- **Mobile-optimized** search and filtering
- **Progressive enhancement** for offline crew browsing
- **Performance optimization** for crew member lists

### **Mobile-Specific Features**
- **Quick actions** for member management
- **Simplified invitation flow** for mobile
- **Touch-optimized** profile previews
- **Mobile notifications** for invitations

---

## 🚀 **Implementation Roadmap**

### **Week 1: Core Integration**
- ✅ **Day 1-2**: Profile links in crew member lists
- ✅ **Day 3-4**: Basic invitation UI/UX
- ✅ **Day 5**: Crew-aware profile discovery basics

### **Week 2: Advanced Features**
- ✅ **Day 1-2**: Complete invitation workflow
- ✅ **Day 3-4**: Privacy integration (CREWS visibility)
- ✅ **Day 5**: Cross-app activity feeds

### **Week 3: Polish & Testing**
- ✅ **Day 1-2**: Mobile optimization
- ✅ **Day 3-4**: Comprehensive testing
- ✅ **Day 5**: Performance optimization and documentation

---

## 🎯 **Success Metrics**

### **User Engagement**
- **Profile visits from crew pages**: Target 40% increase
- **Follow rate between crew members**: Target 60% of crew pairs
- **Invitation acceptance rate**: Target 70%
- **Cross-crew connections**: Target 25% of users

### **Technical Performance**
- **Page load time**: <2 seconds for crew member lists
- **API response time**: <300ms for profile previews
- **Mobile performance**: >85 Lighthouse score

### **Community Growth**
- **Active crew participation**: Target 80% of crew members active monthly
- **Crew discovery**: Target 30% of users discover new crews through profiles
- **Member retention**: Target 90% of invited members stay active >30 days

---

## 🔮 **Future Enhancements**

### **Advanced Social Features**
- **Crew member ratings** and endorsements
- **Skill progression tracking** within crews
- **Mentorship matching** between experienced and new members
- **Crew achievement badges** and recognition system

### **AI-Powered Features**
- **Smart member suggestions** based on compatibility
- **Crew recommendation engine** using ML
- **Activity-based follow suggestions**
- **Crew culture analysis** and matching

---

*This specification serves as the complete roadmap for integrating the crews and profiles systems into a unified, social skateboarding community platform. Each feature is designed to enhance user engagement while maintaining the skateboarding-specific focus of the platform.*
