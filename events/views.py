from django.shortcuts import render
from .models import Event
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Case, When, Value, BooleanField


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
