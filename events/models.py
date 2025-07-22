from django.db import models
from django.utils import timezone
from django_countries.fields import CountryField
from profiles.models import UserProfile
from cloudinary.models import CloudinaryField
from django.utils.text import slugify
from search.models import SearchableModel


class Event(SearchableModel):
    CONTINENT_CHOICES = [
        ('AF', 'Africa'),
        ('AS', 'Asia'),
        ('EU', 'Europe'),
        ('NA', 'North America'),
        ('SA', 'South America'),
        ('OC', 'Oceania'),
        ('AN', 'Antarctica'),
    ]

    CLASS_CHOICES = [
        ('LOCAL', 'Local'),
        ('REGIONAL', 'Regional'),
        ('NATIONAL', 'National'),
        ('CONTINENTAL', 'Continental'),
        ('WORLD', 'World'),
    ]
    
    organizer = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="organized_events",
        null=True,
        blank=True,
        default="",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(default="", blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True, default=None)
    location = models.ForeignKey(
        "Location", on_delete=models.CASCADE, related_name="event",
        null=True, blank=True  # Allow null in development for easier migrations
    )
    event_type = models.CharField(
        max_length=200,
        choices=[
            ("Freeride", "Freeride"),
            ("Race", "Race"),
            ("Local Meetup", "Local Meetup"),
            ("Demo", "Demo"),
            ("Workshop", "Workshop"),
            ("Camp", "Camp"),
            ("Film Screening", "Film Screening"),
            ("Charity Event", "Charity Event"),
            ("Other", "Other"),
        ],
        default=None,
    )
    event_class = models.CharField(
        max_length=20,
        choices=CLASS_CHOICES,
        default='LOCAL',
        verbose_name="Event Class"
    )
    continent = models.CharField(
        max_length=2,
        choices=CONTINENT_CHOICES,
        null=True,
        blank=True,
    )
    skill_level = models.CharField(
        max_length=50,
        choices=[
            ("Beginner", "Beginner"),
            ("Intermediate", "Intermediate"),
            ("Advanced", "Advanced"),
            ("Professional", "Professional"),
        ],
    )
    # Removed direct league foreign key to prevent circular dependency
    # Events are linked to leagues through the LeagueEvent model in results app
    
    # Crew ownership
    created_by_crew = models.ForeignKey(
        'crews.Crew', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_events',
        help_text="Crew that created and manages this event"
    )
    
    tickets_link = models.URLField(null=True, blank=True)
    cover_image = CloudinaryField("image", null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    attendees = models.ManyToManyField(
        UserProfile, through="RSVP", related_name="attending_events"
    )
    cost = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, default=0.00
    )
    max_attendees = models.IntegerField(null=True, blank=True, default=0)
    featured = models.BooleanField(default=False)
    has_results = models.BooleanField(default=False)

    search_fields = ['title', 'description', 'location', 'event_type']
    search_field_weights = {
        'title': 'A',
        'description': 'B',
        'location': 'C',
        'event_type': 'D'
    }

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate initial slug from title
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            # Keep trying until we find a unique slug
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        super().save(*args, **kwargs)

    @classmethod
    def generate_missing_slugs(cls):
        for event in cls.objects.filter(slug__isnull=True):
            event.save()  # This will trigger the save method to generate a slug

    def __str__(self):
        return self.title

    def has_time_trial_results(self):
        return self.results.filter(result_type='TIME_TRIAL').exists()

    def get_time_trial_results(self):
        return self.results.filter(result_type='TIME_TRIAL').first()

    def has_knockout_results(self):
        return self.results.filter(result_type='KNOCKOUT').exists()

    def get_knockout_results(self):
        return self.results.filter(result_type='KNOCKOUT').first()
    
    def can_manage(self, user):
        """Check if a user can manage this event."""
        if not user.is_authenticated:
            return False
        
        # Check if user is the original organizer
        if self.organizer and self.organizer.user == user:
            return True
            
        # If no crew is assigned, only organizer/admin can manage
        if not self.created_by_crew:
            return user.is_superuser
            
        # Check crew permissions
        return self.created_by_crew.can_create_events(user)


class Location(models.Model):
    location_title = models.CharField(max_length=50, null=True, blank=True)
    start_latitude = models.DecimalField(max_digits=20, decimal_places=17, null=True, blank=True)
    start_longitude = models.DecimalField(max_digits=20, decimal_places=17, null=True, blank=True)
    finish_latitude = models.DecimalField(max_digits=20, decimal_places=17, null=True, blank=True)
    finish_longitude = models.DecimalField(max_digits=20, decimal_places=17, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    country = CountryField(blank_label="(select country)", null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)


class RSVP(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="rsvps"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    status = models.CharField(
        max_length=50, choices=[("Going", "Going"), ("Interested", "Interested")]
    )

    def __str__(self):
        return f"{self.user.user.username} - {self.event.title} - {self.status}"


class Review(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="reviews"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField()
    comment = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.user.username} for {self.event.title}"


class Favorite(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="favorites"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="favorites")
    favorited_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} favorited {self.event.title}"


class Notification(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="notifications"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    message = models.TextField()
    notification_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[("Sent", "Sent"), ("Read", "Read"), ("Unread", "Unread")],
        default="Unread",
    )

    def __str__(self):
        return f"Notification for {self.user.user.username}"


class EventAnalytics(models.Model):
    event = models.OneToOneField(
        Event, on_delete=models.CASCADE, related_name="analytics"
    )
    views = models.IntegerField(default=0)
    rsvps_count = models.IntegerField(default=0)
    favorites_count = models.IntegerField(default=0)
    attendance_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Analytics for {self.event.title}"
