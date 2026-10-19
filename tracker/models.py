
from django.conf import settings
from django.db import models
from django.utils import timezone


class JobApplication(models.Model):

    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SHORTLISTED = "shortlisted", "Resume Shortlisted"
        OA_PENDING = "oa_pending", "OA Pending"
        OA_COMPLETED = "oa_completed", "OA Completed"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer Received"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications"
    )

    company_name = models.CharField(max_length=150)
    job_title = models.CharField(max_length=150)

    application_date = models.DateField(
        default=timezone.localdate
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.APPLIED
    )

    resume_version = models.CharField(
        max_length=100,
        blank=True
    )

    job_url = models.URLField(blank=True)

    oa_deadline = models.DateField(
        null=True,
        blank=True
    )

    interview_date = models.DateField(
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.job_title}"
