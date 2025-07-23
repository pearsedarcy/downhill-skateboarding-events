# Feature Implementation Guide
*Step-by-step guide for implementing new features*

## 🎯 **Feature Development Workflow**

### **Phase 1: Planning & Design (Always start here)**

#### **1.1 Feature Specification**
```markdown
# Feature: [Name]

## Purpose
- What problem does this solve?
- How does it benefit the skateboarding community?

## User Stories
- As a [user type], I want [goal] so that [benefit]
- As a [user type], I want [goal] so that [benefit]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Requirements
- Privacy considerations
- Mobile responsiveness requirements
- Performance requirements
- Integration points

## Out of Scope
- What this feature will NOT include
```

#### **1.2 Database Design**
```python
# Model planning (pseudocode)
class NewFeatureModel(models.Model):
    # Core fields
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Skateboarding-specific fields
    difficulty_level = models.IntegerField(choices=DIFFICULTY_CHOICES)
    skateboard_category = models.CharField(choices=CATEGORY_CHOICES)
    
    # Privacy fields (required for all features)
    visibility = models.CharField(choices=VISIBILITY_CHOICES)
    is_public = models.BooleanField(default=True)
    
    # Relationships
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    related_profiles = models.ManyToManyField(UserProfile)
    
    # Metadata (always include)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### **1.3 API Design**
```python
# API endpoints planning
/api/new-feature/                 # GET: List, POST: Create
/api/new-feature/<id>/           # GET: Detail, PUT: Update, DELETE: Delete
/api/new-feature/<id>/action/    # POST: Specific actions
/api/new-feature/search/         # GET: Search with filters

# Response format (consistent across all APIs)
{
    "status": "success|error",
    "data": {},
    "message": "Human readable message", 
    "meta": {
        "timestamp": "ISO timestamp",
        "pagination": {}, # If applicable
    }
}
```

### **Phase 2: Implementation**

#### **2.1 Create Branch**
```bash
git checkout -b feature/new-feature-name
```

#### **2.2 Database Models**
```python
# app/models.py
class NewFeature(models.Model):
    """Feature description for skateboarding community"""
    
    # Follow patterns from DEVELOPMENT_PATTERNS.md
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    
    # Skateboarding context
    difficulty_level = models.IntegerField(
        choices=[(i, f"Level {i}") for i in range(1, 6)],
        help_text="1=Beginner, 5=Expert"
    )
    
    # Privacy (REQUIRED)
    visibility = models.CharField(
        max_length=20,
        choices=[
            ('PUBLIC', 'Public to all'),
            ('COMMUNITY', 'Skateboarding community only'),
            ('PRIVATE', 'Owner only'),
        ],
        default='PUBLIC'
    )
    
    # Relationships
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='owned_features'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager for privacy
    objects = PrivacyAwareManager()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['visibility']),
            models.Index(fields=['owner', '-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('app:feature_detail', args=[self.pk])
    
    def can_be_viewed_by(self, user):
        """Privacy-aware visibility check"""
        if self.visibility == 'PUBLIC':
            return True
        if self.visibility == 'COMMUNITY' and user and user.is_authenticated:
            return True
        if user == self.owner:
            return True
        return False
```

#### **2.3 Forms**
```python
# app/forms.py
class NewFeatureForm(forms.ModelForm):
    """Form for creating/editing features"""
    
    class Meta:
        model = NewFeature
        fields = [
            'name', 'description', 'difficulty_level', 
            'visibility'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe your feature...'
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add CSS classes
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'input input-bordered w-full'
            })
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError('Name must be at least 3 characters.')
        return name
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.owner = self.user
        if commit:
            instance.save()
        return instance
```

#### **2.4 Views**
```python
# app/views.py
class NewFeatureListView(ListView):
    """List all visible features"""
    model = NewFeature
    template_name = 'app/feature_list.html'
    context_object_name = 'features'
    paginate_by = 12
    
    def get_queryset(self):
        """Return privacy-filtered features"""
        return NewFeature.objects.visible_to(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Skateboarding Features',
            'create_url': reverse('app:feature_create'),
        })
        return context

class NewFeatureDetailView(DetailView):
    """Detail view with privacy controls"""
    model = NewFeature
    template_name = 'app/feature_detail.html'
    context_object_name = 'feature'
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions before rendering"""
        self.object = self.get_object()
        if not self.object.can_be_viewed_by(request.user):
            raise PermissionDenied("You don't have permission to view this.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'user_can_edit': self.object.owner == self.request.user,
            'related_features': self.get_related_features(),
        })
        return context
    
    def get_related_features(self):
        """Get related features for this user"""
        return NewFeature.objects.visible_to(self.request.user).exclude(
            pk=self.object.pk
        )[:3]

class NewFeatureCreateView(LoginRequiredMixin, CreateView):
    """Create new feature"""
    model = NewFeature
    form_class = NewFeatureForm
    template_name = 'app/feature_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Feature created successfully!')
        return super().form_valid(form)

class NewFeatureAPIView(LoginRequiredMixin, View):
    """API for AJAX operations"""
    
    def post(self, request, *args, **kwargs):
        try:
            action = request.POST.get('action')
            feature_id = kwargs.get('pk')
            
            if action == 'update_field':
                return self.update_field(request, feature_id)
            elif action == 'toggle_favorite':
                return self.toggle_favorite(request, feature_id)
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except Exception as e:
            logger.exception(f"API error: {e}")
            return JsonResponse({'error': 'Server error'}, status=500)
    
    def update_field(self, request, feature_id):
        """Update a single field"""
        feature = get_object_or_404(NewFeature, pk=feature_id)
        
        # Check permissions
        if feature.owner != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        field = request.POST.get('field')
        value = request.POST.get('value')
        
        # Validate field
        if field not in ['name', 'description', 'difficulty_level']:
            return JsonResponse({'error': 'Invalid field'}, status=400)
        
        # Update
        setattr(feature, field, value)
        feature.full_clean()
        feature.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'{field.title()} updated successfully'
        })
```

#### **2.5 Templates**
```html
<!-- app/templates/app/feature_list.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}{{ page_title }} - {{ block.super }}{% endblock %}

{% block breadcrumb_items %}
<li>Features</li>
{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold">🛹 Skateboarding Features</h1>
        {% if user.is_authenticated %}
        <a href="{{ create_url }}" class="btn btn-primary">
            ➕ Create Feature
        </a>
        {% endif %}
    </div>
    
    <!-- Features Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {% for feature in features %}
        <div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow">
            <div class="card-body p-4">
                <h2 class="card-title text-lg">
                    {{ feature.name }}
                    <div class="badge badge-secondary">
                        Level {{ feature.difficulty_level }}
                    </div>
                </h2>
                
                <p class="text-sm text-base-content/70">
                    {{ feature.description|truncatewords:15 }}
                </p>
                
                <div class="flex justify-between items-center text-xs text-base-content/60 mt-2">
                    <span>By {{ feature.owner.username }}</span>
                    <span>{{ feature.created_at|date:"M d" }}</span>
                </div>
                
                <div class="card-actions justify-end mt-4">
                    <a href="{{ feature.get_absolute_url }}" 
                       class="btn btn-primary btn-sm">
                        View Details
                    </a>
                </div>
            </div>
        </div>
        {% empty %}
        <div class="col-span-full text-center py-12">
            <p class="text-lg text-base-content/60">No features found.</p>
            {% if user.is_authenticated %}
            <a href="{{ create_url }}" class="btn btn-primary mt-4">
                Create the First Feature
            </a>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    
    <!-- Pagination -->
    {% if is_paginated %}
    <div class="flex justify-center">
        <div class="btn-group">
            {% if page_obj.has_previous %}
            <a href="?page={{ page_obj.previous_page_number }}" 
               class="btn">Previous</a>
            {% endif %}
            
            <span class="btn btn-active">
                Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}
            </span>
            
            {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}" 
               class="btn">Next</a>
            {% endif %}
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
```

#### **2.6 URLs**
```python
# app/urls.py
from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    # List and detail views
    path('', views.NewFeatureListView.as_view(), name='feature_list'),
    path('<int:pk>/', views.NewFeatureDetailView.as_view(), name='feature_detail'),
    
    # CRUD operations
    path('create/', views.NewFeatureCreateView.as_view(), name='feature_create'),
    path('<int:pk>/edit/', views.NewFeatureUpdateView.as_view(), name='feature_edit'),
    path('<int:pk>/delete/', views.NewFeatureDeleteView.as_view(), name='feature_delete'),
    
    # API endpoints
    path('api/<int:pk>/', views.NewFeatureAPIView.as_view(), name='feature_api'),
]
```

### **Phase 3: Testing**

#### **3.1 Model Tests**
```python
# app/tests/test_models.py
class NewFeatureModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_feature_creation(self):
        """Test basic feature creation"""
        feature = NewFeature.objects.create(
            name='Test Feature',
            description='Test description',
            difficulty_level=3,
            owner=self.user
        )
        
        self.assertEqual(feature.name, 'Test Feature')
        self.assertEqual(feature.difficulty_level, 3)
        self.assertEqual(feature.owner, self.user)
        self.assertEqual(feature.visibility, 'PUBLIC')  # Default
    
    def test_privacy_visibility(self):
        """Test privacy controls work correctly"""
        feature = NewFeature.objects.create(
            name='Private Feature',
            visibility='PRIVATE',
            owner=self.user
        )
        
        # Owner can see
        self.assertTrue(feature.can_be_viewed_by(self.user))
        
        # Other user cannot see
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com'
        )
        self.assertFalse(feature.can_be_viewed_by(other_user))
        
        # Anonymous cannot see
        self.assertFalse(feature.can_be_viewed_by(None))
```

#### **3.2 View Tests**
```python
# app/tests/test_views.py
class NewFeatureViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.feature = NewFeature.objects.create(
            name='Test Feature',
            description='Test description',
            owner=self.user
        )
        
    def test_list_view(self):
        """Test feature list view"""
        url = reverse('app:feature_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Feature')
    
    def test_detail_view_permissions(self):
        """Test detail view respects privacy"""
        # Public feature should be visible
        url = reverse('app:feature_detail', args=[self.feature.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Private feature should require permission
        self.feature.visibility = 'PRIVATE'
        self.feature.save()
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Owner should still see it
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
```

### **Phase 4: Integration**

#### **4.1 Admin Interface**
```python
# app/admin.py
@admin.register(NewFeature)
class NewFeatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'difficulty_level', 'visibility', 'created_at']
    list_filter = ['difficulty_level', 'visibility', 'created_at']
    search_fields = ['name', 'description', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'difficulty_level')
        }),
        ('Privacy & Ownership', {
            'fields': ('owner', 'visibility')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')
```

#### **4.2 Search Integration**
```python
# Add to search/views.py
class UnifiedSearchView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        
        if query:
            # Add new feature to search results
            features = NewFeature.objects.visible_to(
                self.request.user
            ).filter(
                name__icontains=query
            )[:5]
            
            context['features'] = features
        
        return context
```

### **Phase 5: Documentation & Deployment**

#### **5.1 Update Documentation**
```markdown
# Add to FEATURE_LIST.md

## New Feature System
**Status**: ✅ Implemented  
**Version**: 1.0

### Purpose
Allows users to create and share skateboarding-related features with the community.

### Key Features
- Privacy-controlled visibility
- Difficulty level ratings
- Mobile-responsive interface
- Search integration

### API Endpoints
- `GET /api/features/` - List features
- `POST /api/features/` - Create feature
- `GET /api/features/<id>/` - Feature detail
- `PUT /api/features/<id>/` - Update feature

### Usage Examples
```python
# Create a feature
feature = NewFeature.objects.create(
    name='Awesome Trick',
    difficulty_level=4,
    owner=user
)
```

#### **5.2 Migration & Deployment**
```bash
# Create migrations
python manage.py makemigrations app

# Review migration file
python manage.py sqlmigrate app 0001

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Run tests
python manage.py test app.tests
```

## 🔍 **Feature Quality Checklist**

### **Functionality** ✅
- [ ] Core functionality works as specified
- [ ] All user stories are satisfied
- [ ] Edge cases are handled gracefully
- [ ] Error messages are user-friendly

### **Privacy & Security** 🔒
- [ ] Privacy controls implemented and tested
- [ ] CSRF protection on all forms
- [ ] User input sanitized and validated
- [ ] Permission checks on all sensitive operations

### **Mobile Experience** 📱
- [ ] Responsive design implemented
- [ ] Touch-friendly interface
- [ ] Fast loading on mobile networks
- [ ] Accessible to screen readers

### **Performance** ⚡
- [ ] Database queries optimized
- [ ] No N+1 query problems
- [ ] Appropriate caching implemented
- [ ] Images optimized for web

### **Testing** 🧪
- [ ] Unit tests for models
- [ ] Integration tests for views
- [ ] Privacy restrictions tested
- [ ] API endpoints tested

### **Documentation** 📚
- [ ] Code is well-documented
- [ ] API endpoints documented
- [ ] User guide updated
- [ ] Admin documentation updated

### **Integration** 🔌
- [ ] Search integration working
- [ ] Admin interface functional
- [ ] URLs properly configured
- [ ] Static files served correctly

---

*Follow this guide for consistent, high-quality feature implementation across the project.*
