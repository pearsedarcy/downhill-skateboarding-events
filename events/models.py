from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.utils import timezone
from django_countries.fields import CountryField


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    avatar = CloudinaryField("avatar", null=True, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


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

    def __str__(self):
        return self.title


class Location(models.Model):
    start_line = models.CharField(max_length=200, null=True, blank=True)
    finish_line = models.CharField(max_length=200, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    country = CountryField(blank_label="(select country)", null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
