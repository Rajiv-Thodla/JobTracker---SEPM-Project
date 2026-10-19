
from django import forms
from .models import JobApplication


class JobApplicationForm(forms.ModelForm):

    class Meta:
        model = JobApplication

        fields = [
            "company_name",
            "job_title",
            "application_date",
            "status",
            "resume_version",
            "job_url",
            "oa_deadline",
            "interview_date",
            "notes",
        ]

        widgets = {
            "company_name": forms.TextInput(
                attrs={"placeholder": "e.g. Google"}
            ),

            "job_title": forms.TextInput(
                attrs={"placeholder": "e.g. Software Engineer Intern"}
            ),

            "application_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"}
            ),

            "oa_deadline": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"}
            ),

            "interview_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"}
            ),

            "resume_version": forms.TextInput(
                attrs={"placeholder": "e.g. Resume_v2.pdf"}
            ),

            "job_url": forms.URLInput(
                attrs={"placeholder": "https://example.com/job"}
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Additional details..."
                }
            ),
        }