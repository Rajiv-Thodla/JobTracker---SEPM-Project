from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import JobApplicationForm
from .models import JobApplication


@login_required
@require_POST
def update_event_date(request, pk):
    application = get_object_or_404(
        JobApplication,
        pk=pk,
        user=request.user
    )

    field = request.POST.get("event_field")
    if field is None:
        if application.status == JobApplication.Status.INTERVIEW:
            field = "interview_date"
        elif application.status == JobApplication.Status.OA_PENDING:
            field = "oa_deadline"
    if field not in ["oa_deadline", "interview_date"]:
        return HttpResponseBadRequest("Invalid date field.")

    value = request.POST.get("event_date", "").strip()

    try:
        if value:
            new_date = date.fromisoformat(value)
        else:
            new_date = None
    except ValueError:
        return HttpResponseBadRequest("Invalid date")

    setattr(application, field, new_date)
    application.save(update_fields=[field, "updated_at"])

    if request.POST.get("return_to") == "activity":
        return redirect("tracker:activity")
    return redirect("tracker:dashboard")


@login_required
def activity(request):
    today = timezone.localdate()
    applications = JobApplication.objects.filter(user=request.user)
    status_totals = (
        applications.values("status")
        .annotate(count=Count("id"))
    )
    status_counts = {}
    for row in status_totals:
        status_counts[row["status"]] = row["count"]

    statistics = [
        ("Total applications", applications.count()),
        ("OA Pending", status_counts.get(JobApplication.Status.OA_PENDING, 0)),
        ("Interviews", status_counts.get(JobApplication.Status.INTERVIEW, 0)),
        ("Offers received", status_counts.get(JobApplication.Status.OFFER, 0)),
        ("Rejected", status_counts.get(JobApplication.Status.REJECTED, 0)),
    ]
    past_events = []
    upcoming_events = []
    for application in applications:
        for field, event_type, event_date in [
            ("oa_deadline", "OA", application.oa_deadline),
            ("interview_date", "Interview", application.interview_date),
        ]:
            if event_date is None:
                continue
            event = {
                "application": application,
                "date": event_date,
                "type": event_type,
                "field": field,
            }
            if event_date >= today:
                upcoming_events.append(event)
            else:
                past_events.append(event)

    past_events.sort(key=lambda event: (event["date"], event["application"].company_name))
    upcoming_events.sort(key=lambda event: (event["date"], event["application"].company_name))
    return render(request, "tracker/activity.html", {
        "statistics": statistics,
        "today": today,
        "deadline_groups": [
            ("Past dates (including overdue)", past_events),
            ("Today & upcoming", upcoming_events),
        ],
    })


@login_required
def dashboard(request):
    applications = JobApplication.objects.filter(
        user=request.user
    ).order_by("-application_date")

    search = request.GET.get("search", "").strip()

    if search:
        applications = applications.filter(
            Q(company_name__icontains=search) |
            Q(job_title__icontains=search)
        )

    status = request.GET.get("status", "")

    if status:
        applications = applications.filter(status=status)

    for application in applications:
        application.date_events = []
        if application.oa_deadline:
            application.date_events.append({
                "label": "OA", "field": "oa_deadline", "date": application.oa_deadline,
            })
        if application.interview_date:
            application.date_events.append({
                "label": "Interview", "field": "interview_date", "date": application.interview_date,
            })
        if not application.date_events:
            if application.status == JobApplication.Status.OA_PENDING:
                application.date_events.append({"label": "OA", "field": "oa_deadline", "date": None})
            elif application.status == JobApplication.Status.INTERVIEW:
                application.date_events.append({"label": "Interview", "field": "interview_date", "date": None})

    context = {
        "applications": applications,
        "search": search,
        "selected_status": status,
        "status_choices": JobApplication.Status.choices,
    }

    return render(request, "tracker/dashboard.html", context)


@login_required
def add_application(request):
    if request.method == "POST":
        form = JobApplicationForm(request.POST)

        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()

            return redirect("tracker:dashboard")

    else:
        form = JobApplicationForm()

    return render(
        request,
        "tracker/application_form.html",
        {
            "form": form,
            "title": "Add Job Application",
        },
    )


@login_required
def edit_application(request, pk):
    application = get_object_or_404(
        JobApplication,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        form = JobApplicationForm(
            request.POST,
            instance=application,
        )

        if form.is_valid():
            form.save()
            return redirect("tracker:dashboard")

    else:
        form = JobApplicationForm(instance=application)

    return render(
        request,
        "tracker/application_form.html",
        {
            "form": form,
            "title": "Edit Job Application",
        },
    )


@login_required
def delete_application(request, pk):
    application = get_object_or_404(
        JobApplication,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        application.delete()
        return redirect("tracker:dashboard")

    return render(
        request,
        "tracker/confirm_delete.html",
        {"application": application},
    )


@login_required
@require_POST
def update_status(request, pk):
    application = get_object_or_404(
        JobApplication,
        pk=pk,
        user=request.user
    )

    new_status = request.POST.get("status")

    if new_status not in JobApplication.Status.values:
        return HttpResponseBadRequest("Invalid status")

    application.status = new_status
    application.save(update_fields=["status", "updated_at"])

    return redirect("tracker:dashboard")
