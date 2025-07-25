# Development Patterns & Best Practices
*Coding standards and patterns for consistent development*

## 🎯 **Core Development Principles**

### **1. Skateboarding-First Design**
Every feature should consider the skateboarding community context:
```python
# ✅ Good: Skateboarding-specific choices
STANCE_CHOICES = [
    ('REGULAR', 'Regular'),
    ('GOOFY', 'Goofy'),
    ('SWITCH', 'Switch'),
]

# ❌ Avoid: Generic sports terminology
POSITION_CHOICES = [
    ('LEFT', 'Left'),
    ('RIGHT', 'Right'),
]
```

### **2. Privacy by Design**
All features must respect user privacy from the ground up:
```python
# ✅ Good: Privacy-aware query
def get_visible_profiles(viewer):
    if viewer.is_authenticated:
        return UserProfile.objects.filter(
            Q(profile_visibility='PUBLIC') |
            Q(profile_visibility='COMMUNITY') |
            Q(user=viewer)
        )
    return UserProfile.objects.filter(profile_visibility='PUBLIC')

# ❌ Avoid: Exposing all data
def get_all_profiles():
    return UserProfile.objects.all()  # No privacy consideration
```

### **3. Mobile-First Responsive Design**
Always design for mobile, then enhance for desktop:
```html
<!-- ✅ Good: Mobile-first responsive classes -->
<div class="p-2 sm:p-4 lg:p-6">
    <h1 class="text-lg sm:text-xl lg:text-2xl">Title</h1>
    <img class="w-16 h-16 sm:w-24 sm:h-24 lg:w-32 lg:h-32" />
</div>

<!-- ❌ Avoid: Desktop-first or fixed sizes -->
<div class="p-8">
    <h1 class="text-3xl">Title</h1>
    <img class="w-64 h-64" />
</div>
```

## 🏗️ **Model Design Patterns**

### **Standard Model Structure**
```python
class SkateboardingModel(models.Model):
    """Base class for skateboarding-related models"""
    
    # Core fields first
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    
    # Skateboarding-specific fields
    difficulty_level = models.IntegerField(
        choices=[(i, f"Level {i}") for i in range(1, 6)],
        help_text="1=Beginner, 5=Expert"
    )
    
    # Privacy and visibility
    is_public = models.BooleanField(default=True)
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='PUBLIC'
    )
    
    # Metadata (always last)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['visibility', 'is_public']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('model_detail', args=[self.pk])
```

### **Privacy-Aware Manager Pattern**
```python
class PrivacyAwareManager(models.Manager):
    """Manager that respects privacy settings"""
    
    def visible_to(self, user=None):
        """Return queryset filtered by privacy rules"""
        queryset = self.get_queryset()
        
        if user and user.is_authenticated:
            return queryset.filter(
                Q(visibility='PUBLIC') |
                Q(visibility='COMMUNITY') |
                Q(created_by=user)
            )
        return queryset.filter(visibility='PUBLIC')
    
    def for_user(self, user):
        """Return objects owned by user"""
        return self.get_queryset().filter(created_by=user)

class UserProfile(models.Model):
    # ... model fields ...
    
    objects = PrivacyAwareManager()
```

### **Search Integration Pattern**
```python
class SearchableModel(models.Model):
    """Mixin for full-text search capability"""
    search_vector = SearchVectorField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    @classmethod
    def get_search_fields(cls):
        """Override in subclasses to define search fields"""
        return getattr(cls, 'search_fields', [])
    
    @classmethod
    def get_search_weights(cls):
        """Override in subclasses to define field weights"""
        return getattr(cls, 'search_field_weights', {})
    
    def update_search_vector(self):
        """Update the search vector for this instance"""
        fields = self.get_search_fields()
        if fields:
            search_vector = SearchVector(*fields)
            self.__class__.objects.filter(pk=self.pk).update(
                search_vector=search_vector
            )

# Usage example
class UserProfile(SearchableModel):
    search_fields = ['user__username', 'display_name', 'bio']
    search_field_weights = {
        'user__username': 'A',
        'display_name': 'A',
        'bio': 'B',
    }
```

## 🎛️ **View Design Patterns**

### **Standard Class-Based View Pattern**
```python
class SkateboardingDetailView(DetailView):
    """Standard detail view with privacy controls"""
    model = UserProfile
    template_name = 'app/model_detail.html'
    context_object_name = 'object'
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions before processing request"""
        self.object = self.get_object()
        if not self.can_view_object(request.user):
            raise PermissionDenied("You don't have permission to view this.")
        return super().dispatch(request, *args, **kwargs)
    
    def can_view_object(self, user):
        """Implement privacy logic"""
        if self.object.visibility == 'PUBLIC':
            return True
        if self.object.visibility == 'COMMUNITY' and user.is_authenticated:
            return True
        if self.object.created_by == user:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        """Add skateboarding-specific context"""
        context = super().get_context_data(**kwargs)
        context.update({
            'related_objects': self.get_related_objects(),
            'user_can_edit': self.can_edit_object(self.request.user),
            'skateboarding_stats': self.get_skateboarding_stats(),
        })
        return context
    
    def get_related_objects(self):
        """Get related objects with privacy filtering"""
        # Implementation specific to model
        pass
    
    def can_edit_object(self, user):
        """Check if user can edit this object"""
        return self.object.created_by == user or user.is_staff
```

### **API View Pattern**
```python
class SkateboardingAPIView(LoginRequiredMixin, View):
    """Standard API view for AJAX operations"""
    
    def post(self, request, *args, **kwargs):
        """Handle API requests with action routing"""
        try:
            action = request.POST.get('action')
            handler = getattr(self, f'handle_{action}', None)
            
            if not handler:
                return self.error_response('Invalid action')
            
            return handler(request)
            
        except Exception as e:
            logger.exception(f"API error in {self.__class__.__name__}")
            return self.error_response('Internal server error')
    
    def handle_update_field(self, request):
        """Update a single field"""
        field_name = request.POST.get('field')
        field_value = request.POST.get('value')
        
        # Validate field
        if not self.is_valid_field(field_name):
            return self.error_response('Invalid field')
        
        # Update object
        obj = self.get_object()
        setattr(obj, field_name, field_value)
        obj.full_clean()  # Validate
        obj.save()
        
        return self.success_response({
            'field': field_name,
            'value': field_value,
            'message': f'{field_name.title()} updated successfully'
        })
    
    def success_response(self, data=None):
        """Standard success response"""
        return JsonResponse({
            'status': 'success',
            'data': data or {},
            'timestamp': timezone.now().isoformat()
        })
    
    def error_response(self, message, errors=None):
        """Standard error response"""
        return JsonResponse({
            'status': 'error',
            'message': message,
            'errors': errors or {},
            'timestamp': timezone.now().isoformat()
        }, status=400)
```

## 🎨 **Template Patterns**

### **Base Template Structure**
```html
<!-- base.html pattern -->
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Downhill Skateboarding Events{% endblock %}</title>
    
    <!-- CSS -->
    <link href="{% static 'css/dist/styles.css' %}" rel="stylesheet">
    {% block extra_css %}{% endblock %}
</head>
<body class="min-h-screen bg-base-100">
    <!-- Navigation -->
    {% include 'partials/navigation.html' %}
    
    <!-- Main content -->
    <main class="container mx-auto px-2 sm:px-4 lg:px-6 py-4">
        <!-- Breadcrumbs -->
        {% block breadcrumbs %}
        <div class="breadcrumbs text-sm mb-4">
            <ul>
                <li><a href="{% url 'home' %}">🛹 Home</a></li>
                {% block breadcrumb_items %}{% endblock %}
            </ul>
        </div>
        {% endblock %}
        
        <!-- Messages -->
        {% include 'partials/messages.html' %}
        
        <!-- Page content -->
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    {% include 'partials/footer.html' %}
    
    <!-- JavaScript -->
    <script src="{% static 'js/base.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### **Card Component Pattern**
```html
<!-- reusable_card.html -->
<div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow">
    {% if image_url %}
    <figure class="aspect-video">
        <img src="{{ image_url }}" alt="{{ title }}" 
             class="w-full h-full object-cover" />
    </figure>
    {% endif %}
    
    <div class="card-body p-2 sm:p-4 lg:p-6">
        <h2 class="card-title text-sm sm:text-base lg:text-lg">
            {{ title }}
            {% if badge %}
            <div class="badge badge-secondary">{{ badge }}</div>
            {% endif %}
        </h2>
        
        <p class="text-xs sm:text-sm text-base-content/70">
            {{ description|truncatewords:20 }}
        </p>
        
        {% if tags %}
        <div class="flex flex-wrap gap-1 mt-2">
            {% for tag in tags %}
            <span class="badge badge-outline badge-xs">{{ tag }}</span>
            {% endfor %}
        </div>
        {% endif %}
        
        <div class="card-actions justify-end mt-4">
            {% if primary_action %}
            <a href="{{ primary_action.url }}" 
               class="btn btn-primary btn-sm">
                {{ primary_action.text }}
            </a>
            {% endif %}
            
            {% if secondary_action %}
            <a href="{{ secondary_action.url }}" 
               class="btn btn-outline btn-sm">
                {{ secondary_action.text }}
            </a>
            {% endif %}
        </div>
    </div>
</div>
```

### **Form Pattern with Validation**
```html
<!-- form_with_validation.html -->
<form method="post" class="space-y-4" novalidate>
    {% csrf_token %}
    
    {% for field in form %}
    <div class="form-control">
        <label class="label" for="{{ field.id_for_label }}">
            <span class="label-text">{{ field.label }}</span>
            {% if field.field.required %}
            <span class="label-text-alt text-error">*</span>
            {% endif %}
        </label>
        
        {{ field|add_class:"input input-bordered w-full" }}
        
        {% if field.help_text %}
        <label class="label">
            <span class="label-text-alt">{{ field.help_text }}</span>
        </label>
        {% endif %}
        
        {% if field.errors %}
        <label class="label">
            <span class="label-text-alt text-error">
                {{ field.errors.0 }}
            </span>
        </label>
        {% endif %}
    </div>
    {% endfor %}
    
    <div class="form-control mt-6">
        <button type="submit" class="btn btn-primary">
            {{ submit_text|default:"Save Changes" }}
        </button>
    </div>
</form>
```

## 💾 **JavaScript Patterns**

### **Module Organization Pattern**
```javascript
// ModuleName.js
class ModuleName {
    constructor(options = {}) {
        this.options = {
            // Default options
            endpoint: '/api/endpoint/',
            timeout: 5000,
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialData();
    }
    
    bindEvents() {
        // Event delegation pattern
        document.addEventListener('click', (e) => {
            if (e.target.matches('.js-action-button')) {
                this.handleAction(e);
            }
        });
    }
    
    async handleAction(event) {
        event.preventDefault();
        
        try {
            const response = await this.makeRequest();
            this.handleSuccess(response);
        } catch (error) {
            this.handleError(error);
        }
    }
    
    async makeRequest(data = {}) {
        const response = await fetch(this.options.endpoint, {
            method: 'POST',
            headers: CSRFManager.getHeaders(),
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return response.json();
    }
    
    handleSuccess(data) {
        // Update UI
        this.showMessage(data.message, 'success');
    }
    
    handleError(error) {
        console.error('Module error:', error);
        this.showMessage('Something went wrong. Please try again.', 'error');
    }
    
    showMessage(message, type = 'info') {
        // Toast notification or similar
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.js-module-trigger')) {
        new ModuleName();
    }
});
```

### **AJAX Form Handling Pattern**
```javascript
class FormHandler {
    static async submitForm(form, options = {}) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        try {
            const response = await fetch(form.action || window.location.href, {
                method: form.method || 'POST',
                headers: CSRFManager.getHeaders(),
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.handleSuccess(form, result, options);
            } else {
                this.handleErrors(form, result.errors || {});
            }
            
            return result;
            
        } catch (error) {
            console.error('Form submission error:', error);
            this.showError('Network error. Please check your connection.');
        }
    }
    
    static handleSuccess(form, result, options) {
        // Clear form errors
        form.querySelectorAll('.error').forEach(el => el.remove());
        
        // Show success message
        if (result.message) {
            this.showSuccess(result.message);
        }
        
        // Handle redirect
        if (result.redirect_url) {
            window.location.href = result.redirect_url;
        } else if (options.onSuccess) {
            options.onSuccess(result);
        }
    }
    
    static handleErrors(form, errors) {
        // Clear previous errors
        form.querySelectorAll('.error').forEach(el => el.remove());
        
        // Display field errors
        Object.entries(errors).forEach(([field, messages]) => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error text-error text-sm mt-1';
                errorDiv.textContent = Array.isArray(messages) ? messages[0] : messages;
                input.parentNode.appendChild(errorDiv);
            }
        });
    }
}
```

### **Email Preferences Management Pattern**
```javascript
// Real-time preference toggling with proper error handling
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
            // Show success feedback
            if (window.showToast) {
                window.showToast(`${field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} updated!`, 'success', 2000);
            }
        } else {
            // Revert toggle and show error
            element.checked = !value;
            if (window.showToast) {
                window.showToast(`Error: ${data.error}`, 'error');
            }
        }
    })
    .catch(error => {
        // Revert toggle and show network error
        element.checked = !value;
        console.error('Error:', error);
        if (window.showToast) {
            window.showToast('An error occurred while updating.', 'error');
        }
    });
}

// Professional bulk unsubscribe with modal confirmation
function confirmUnsubscribeAll() {
    const emailFields = [
        'email_community_news',
        'email_event_notifications', 
        'email_newsletter',
        'email_crew_invites',
        'email_marketing'
    ];
    
    let updatesCompleted = 0;
    const totalUpdates = emailFields.length;
    
    emailFields.forEach(fieldName => {
        const toggle = document.querySelector(`input[data-field="${fieldName}"]`);
        if (toggle && toggle.checked) {
            toggle.disabled = true;
            toggle.checked = false;
            
            fetch('/profiles/api/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ field: fieldName, value: false })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    toggle.checked = true; // Revert on error
                    console.error(`Failed to update ${fieldName}:`, data.error);
                }
            })
            .finally(() => {
                toggle.disabled = false;
                updatesCompleted++;
                
                if (updatesCompleted === totalUpdates) {
                    if (window.showToast) {
                        window.showToast('✅ Successfully unsubscribed from all emails', 'success', 4000);
                    }
                }
            });
        }
    });
}
```

### **DaisyUI Modal Pattern for Confirmations**
```html
<!-- Replace browser confirm() with professional modal -->
<dialog id="confirmation_modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">
            <i class="fas fa-exclamation-triangle text-warning mr-2"></i>
            Confirm Action
        </h3>
        <p class="py-4">Detailed explanation of what will happen...</p>
        <ul class="list-disc list-inside space-y-1 text-sm mb-6">
            <li>Specific consequence 1</li>
            <li>Specific consequence 2</li>
            <li>Specific consequence 3</li>
        </ul>
        <p class="text-sm text-base-content/70 mb-6">
            <i class="fas fa-info-circle text-info mr-2"></i>
            Additional helpful information
        </p>
        <div class="modal-action">
            <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
            <button class="btn btn-warning" onclick="confirmAction()">
                <i class="fas fa-check mr-2"></i>Yes, Continue
            </button>
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button onclick="closeModal()">close</button>
    </form>
</dialog>
```

## 🧪 **Testing Patterns**

### **Model Testing Pattern**
```python
class UserProfileModelTests(TestCase):
    """Test UserProfile model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testskater',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)
    
    def test_profile_completion_calculation(self):
        """Test profile completion percentage calculation"""
        # Empty profile should have low completion
        self.assertLess(self.profile.calculate_completion_percentage(), 30)
        
        # Fill in core fields
        self.profile.display_name = "Test Skater"
        self.profile.bio = "I love downhill skateboarding"
        self.profile.skating_style = "DOWNHILL"
        self.profile.skill_level = 7
        self.profile.save()
        
        # Should have higher completion
        self.assertGreater(self.profile.calculate_completion_percentage(), 60)
    
    def test_privacy_visibility(self):
        """Test privacy visibility logic"""
        # Test different visibility levels
        test_cases = [
            ('PUBLIC', True, True),     # Public visible to all
            ('COMMUNITY', False, True), # Community visible to authenticated
            ('PRIVATE', False, False),  # Private visible to owner only
        ]
        
        for visibility, anonymous_can_see, authenticated_can_see in test_cases:
            with self.subTest(visibility=visibility):
                self.profile.profile_visibility = visibility
                self.profile.save()
                
                # Test anonymous user
                self.assertEqual(
                    self.profile.can_be_viewed_by(None), 
                    anonymous_can_see
                )
                
                # Test authenticated user
                other_user = User.objects.create_user(
                    username='other', 
                    email='other@example.com'
                )
                self.assertEqual(
                    self.profile.can_be_viewed_by(other_user), 
                    authenticated_can_see
                )
```

### **View Testing Pattern**
```python
class ProfileViewTests(TestCase):
    """Test profile views"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com', 
            password='testpass123'
        )
        self.profile = self.user.profile
        self.client.login(username='testuser', password='testpass123')
    
    def test_profile_detail_view(self):
        """Test profile detail view renders correctly"""
        url = reverse('profiles:user_profile', args=[self.user.username])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)
        self.assertContains(response, 'Profile Completion')
    
    def test_profile_privacy_restrictions(self):
        """Test privacy restrictions work correctly"""
        # Set profile to private
        self.profile.profile_visibility = 'PRIVATE'
        self.profile.save()
        
        # Other user shouldn't see private profile
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='otherpass'
        )
        self.client.login(username='other', password='otherpass')
        
        url = reverse('profiles:user_profile', args=[self.user.username])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
    
    def test_api_field_update(self):
        """Test API field update functionality"""
        url = reverse('profiles:api_update')
        data = {
            'action': 'update_field',
            'field': 'bio',
            'value': 'Updated bio text'
        }
        
        response = self.client.post(
            url, 
            json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertEqual(result['status'], 'success')
        
        # Verify field was updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Updated bio text')
```

## 📊 **Performance Patterns**

### **Query Optimization Pattern**
```python
# ✅ Good: Optimized queries with select_related/prefetch_related
def get_profiles_with_stats(visibility='PUBLIC'):
    return UserProfile.objects.filter(
        profile_visibility=visibility
    ).select_related(
        'user'
    ).prefetch_related(
        'crew_memberships__crew',
        'events_organized',
        'event_participations__event'
    ).annotate(
        events_count=Count('events_organized'),
        crews_count=Count('crew_memberships', distinct=True)
    )

# ❌ Avoid: N+1 queries
def get_profiles_bad():
    profiles = UserProfile.objects.all()
    for profile in profiles:
        events = profile.events_organized.count()  # Database hit for each profile
        crews = profile.crew_memberships.count()   # Another database hit
```

### **Caching Pattern**
```python
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class ProfileStatsManager:
    """Manage profile statistics with caching"""
    
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_cache_key(cls, profile_id, stat_type):
        return f'profile_stats:{profile_id}:{stat_type}'
    
    @classmethod
    def get_stats(cls, profile, stat_type='basic'):
        cache_key = cls.get_cache_key(profile.id, stat_type)
        stats = cache.get(cache_key)
        
        if stats is None:
            stats = cls.calculate_stats(profile, stat_type)
            cache.set(cache_key, stats, cls.CACHE_TIMEOUT)
        
        return stats
    
    @classmethod
    def invalidate_stats(cls, profile):
        """Clear all cached stats for a profile"""
        keys = [
            cls.get_cache_key(profile.id, 'basic'),
            cls.get_cache_key(profile.id, 'detailed'),
            cls.get_cache_key(profile.id, 'social'),
        ]
        cache.delete_many(keys)
    
    @classmethod
    def calculate_stats(cls, profile, stat_type):
        """Calculate statistics - expensive operation"""
        # Implementation depends on stat_type
        pass

# Use in views
@method_decorator(cache_page(300), name='dispatch')  # 5 minute page cache
class ProfileListView(ListView):
    model = UserProfile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add cached stats for each profile
        for profile in context['object_list']:
            profile.cached_stats = ProfileStatsManager.get_stats(profile)
        
        return context
```

---

*These patterns should be followed consistently across the codebase to maintain quality and predictability.*
