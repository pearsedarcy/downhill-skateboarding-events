from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, BooleanField
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
import logging
from .models import Event, Favorite, RSVP
from .forms import EventForm, LocationForm
from django_countries import countries
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

def event_list(request):
    today = timezone.now().date()
    
    # Get featured events
    featured_events = Event.objects.filter(
        published=True,
        featured=True,
        start_date__gte=today
    ).order_by('start_date')[:5]
    
    # Base query
    event_list = Event.objects.annotate(
        is_future=Case(
            When(start_date__gte=today, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    )
    
    # Filter logic
    if request.user.is_authenticated:
        event_list = event_list.filter(Q(published=True) | Q(organizer=request.user.profile))
    else:
        event_list = event_list.filter(published=True)
    
    # Apply filters from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    event_type = request.GET.get('event_type')
    country = request.GET.get('country')

    if start_date:
        event_list = event_list.filter(start_date__gte=start_date)
    if end_date:
        event_list = event_list.filter(start_date__lte=end_date)
    if event_type:
        event_list = event_list.filter(event_type=event_type)
    if country:
        event_list = event_list.filter(location__country=country)
    
    # Ordering
    event_list = event_list.order_by("-is_future", "start_date", "-created")
    
    # Pagination
    paginator = Paginator(event_list, 6)
    page_number = request.GET.get("page", 1)
    events = paginator.get_page(page_number)
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            event_cards_html = ''
            for event in events:
                event_cards_html += render_to_string(
                    'events/partials/_event_card.html',
                    {'event': event},  # Change: pass single event instead of events queryset
                    request=request
                )
            return JsonResponse({
                'html': event_cards_html,
                'has_next': events.has_next(),
                'next_page': events.next_page_number() if events.has_next() else None,
            })
        except Exception as e:
            print(f"AJAX Error: {str(e)}")  # Debug print
            return JsonResponse({'error': str(e)}, status=500)

    context = {
        'events': events,
        'featured_events': featured_events,
        'event_types': Event._meta.get_field('event_type').choices,
        'countries': list(countries),
    }
    return render(request, "events/event_list.html", context)


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

    maps_api_key = settings.GOOGLE_MAPS_API_KEY
    if not maps_api_key:
        logger.error("Google Maps API key is not configured")

    return render(
        request,
        "events/event_details.html",
        {
            "event": event,
            "is_favorited": is_favorited,
            "rsvp_status": rsvp_status,
            "rsvp_count": event.rsvps.count(),
            "maps_api_key": maps_api_key,
        },
    )


@login_required
def event_submission(request, slug=None):
    event = None
    location = None
    if (slug):
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

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    context = {
        'event': event,
        'maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    return render(request, 'events/event_detail.html', context)

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

