from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Event, Favorite, RSVP
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Case, When, Value, BooleanField
from django.contrib.auth.models import User


def event_list(request):
    today = timezone.now().date()
    events_list = (
        Event.objects.filter(published=True)
        .annotate(
            is_future=Case(
                When(start_date__gte=today, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .order_by("-is_future", "start_date", "-created")
    )

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
    event = get_object_or_404(Event, slug=slug, published=True)
    is_favorited = False
    rsvp_status = None

    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(
            user=request.user.profile, event=event
        ).exists()
        rsvp = RSVP.objects.filter(user=request.user.profile, event=event).first()
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


def user_profile(request, username=None):
    if username is None:
        if not request.user.is_authenticated:
            return redirect("account_login")
        user = request.user
    else:
        user = get_object_or_404(User, username=username)

    profile = user.profile
    attending_events = profile.attending_events.all()[:3]
    # Get RSVP statuses for the attending events
    rsvp_statuses = {
        rsvp.event_id: rsvp.status
        for rsvp in RSVP.objects.filter(user=profile, event__in=attending_events)
    }

    context = {
        "profile": profile,
        "organized_events": profile.organized_events.all()[:3],
        "attending_events": attending_events,
        "rsvp_statuses": rsvp_statuses,
        "reviews": profile.reviews.all()[:3],
        "favorites": profile.favorites.all()[:3],
    }
    return render(request, "events/user_profile.html", context)
