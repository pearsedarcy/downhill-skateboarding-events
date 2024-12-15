from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, BooleanField
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Event, Favorite, RSVP
from .forms import EventForm, LocationForm

def event_list(request):
    today = timezone.now().date()
    
    # Base query
    events_list = Event.objects.annotate(
        is_future=Case(
            When(start_date__gte=today, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    )
    
    # Filter logic
    if request.user.is_authenticated:
        # Show published events + user's own unpublished events
        events_list = events_list.filter(
            Q(published=True) | 
            Q(organizer=request.user.profile)
        )
    else:
        # Show only published events
        events_list = events_list.filter(published=True)
    
    events_list = events_list.order_by("-is_future", "start_date", "-created")
    
    paginator = Paginator(events_list, 6)
    page_number = request.GET.get("page")
    events = paginator.get_page(page_number)
    return render(request, "events/event_list.html", {"events": events})


@login_required
def toggle_favorite(request, slug):
    event = get_object_or_404(Event, slug=slug)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user.profile, event=event
    )

    if not created:
        favorite.delete()
        is_favorited = False
    else:
        is_favorited = True

    return JsonResponse(
        {"is_favorited": is_favorited, "count": event.favorites.count()}
    )


@login_required
def toggle_rsvp(request, slug):
    event = get_object_or_404(Event, slug=slug)
    status = request.POST.get("status", "Going")

    rsvp, created = RSVP.objects.get_or_create(
        user=request.user.profile, event=event, defaults={"status": status}
    )

    if not created:
        if rsvp.status != status:
            rsvp.status = status
            rsvp.save()
        else:
            rsvp.delete()
            status = None

    return JsonResponse({"status": status, "count": event.rsvps.count()})


def event_details(request, slug):
    if request.user.is_authenticated:
        event = get_object_or_404(
            Event.objects.filter(
                Q(published=True) | 
                Q(organizer=request.user.profile)
            ),
            slug=slug
        )
    else:
        event = get_object_or_404(Event, slug=slug, published=True)
        
    is_favorited = False
    rsvp_status = None

    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(
            user=request.user.profile, 
            event=event
        ).exists()
        rsvp = RSVP.objects.filter(
            user=request.user.profile, 
            event=event
        ).first()
        if rsvp:
            rsvp_status = rsvp.status

    return render(
        request,
        "events/event_details.html",
        {
            "event": event,
            "is_favorited": is_favorited,
            "rsvp_status": rsvp_status,
            "rsvp_count": event.rsvps.count(),
        },
    )


@login_required
def event_submission(request, slug=None):
    event = None
    location = None
    if slug:
        event = get_object_or_404(Event, slug=slug)
        if event.organizer != request.user.profile:
            return redirect('events:event_list')
        location = event.location

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        location_form = LocationForm(request.POST, instance=location)
        
        if form.is_valid() and location_form.is_valid():
            try:
                # Save location first
                location = location_form.save()
                
                # Save event without committing to set organizer and location
                event = form.save(commit=False)
                event.organizer = request.user.profile
                event.location = location
                
                # Save event to generate slug
                event.save()
                form.save_m2m()  # Save many-to-many relationships if any
                
                return redirect('events:event_details', slug=event.slug)
            except Exception as e:
                # If something goes wrong, delete the location if it was just created
                if location and not location.pk:
                    location.delete()
                raise e
    else:
        form = EventForm(instance=event)
        location_form = LocationForm(instance=location)

    return render(request, 'events/event_submission.html', {
        'form': form,
        'location_form': location_form,
        'edit_mode': bool(event),
        'event': event
    })

@login_required
def edit_event(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if event.organizer.user != request.user:
        raise Http404("You don't have permission to edit this event")
    
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        location_form = LocationForm(request.POST, instance=event.location)
        
        if form.is_valid() and location_form.is_valid():
            try:
                location = location_form.save()
                event = form.save(commit=False)
                
                # Handle cover image and filename
                if 'cover_image' in request.FILES:
                    event._cover_image_changed = True
                    event.cover_image = request.FILES['cover_image']
                    event.cover_image_filename = request.FILES['cover_image'].name
                
                event.location = location
                event.save()
                form.save_m2m()
                
                return redirect('events:event_details', slug=event.slug)
            except Exception as e:
                print(f"Error updating event: {str(e)}")
                form.add_error(None, f"Error updating event: {str(e)}")
    else:
        form = EventForm(instance=event)
        location_form = LocationForm(instance=event.location)

    return render(request, 'events/event_submission.html', {
        'form': form,
        'location_form': location_form,
        'edit_mode': True,
        'event': event
    })

@login_required
def event_delete(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    # Check if user is the organizer
    if event.organizer != request.user.profile:
        raise Http404("You don't have permission to delete this event")
    
    if request.method == "POST":
        # Store the location to delete after the event
        location = event.location
        
        # Delete the event
        event.delete()
        
        # Delete the location if it's not used by other events
        if location and not Event.objects.filter(location=location).exists():
            location.delete()
        
        return redirect('events:event_list')
    
    raise Http404("Invalid request method")

