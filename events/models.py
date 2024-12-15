from django.db import models
from django.utils import timezone
from django_countries.fields import CountryField
from profiles.models import UserProfile
from cloudinary.models import CloudinaryField
from django.utils.text import slugify


class Event(models.Model):
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
        "Location", on_delete=models.CASCADE, related_name="event"
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
    skill_level = models.CharField(
        max_length=50,
        choices=[
            ("Beginner", "Beginner"),
            ("Intermediate", "Intermediate"),
            ("Advanced", "Advanced"),
            ("Professional", "Professional"),
        ],
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


class Location(models.Model):
    start_line = models.CharField(max_length=200, null=True, blank=True)
    finish_line = models.CharField(max_length=200, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    country = CountryField(blank_label="(select country)", null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)


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
