import argparse
import os
import random
from collections import Counter
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

from tracker.models import JobApplication


REFERENCE_DATE = date(2026, 10, 19)
DEMO_MARKER = "[DEMO] Synthetic JobTracker demonstration data. "


def build_demo_records(as_of, seed):
    random_generator = random.Random(seed)
    date_shift = as_of - REFERENCE_DATE
    local_timezone = ZoneInfo("Asia/Kolkata")
    samples = [
        ("Infosys", "Software Engineering Intern", "2026-06-12", "rejected", None, None, "2026-06-25",
         "Applied through a campus interest form; did not progress after resume review."),
        ("Nimbly Labs", "Python Developer Intern", "2026-06-26", "applied", None, None, "2026-06-26",
         "Fictional small employer. Sent a project portfolio by email; no response recorded."),
        ("CodeHarbor Labs", "Web Development Intern", "2026-07-07", "withdrawn", "2026-07-15", None, "2026-07-12",
         "Fictional small employer. Withdrew because the proposed hours conflicted with classes."),
        ("PixelNest Labs", "Frontend Developer Intern", "2026-07-22", "offer", "2026-08-01", "2026-08-12", "2026-08-20",
         "Fictional small employer. Accepted a part-time internship offer after a portfolio discussion; kept for reference."),
        ("Zoho", "Software Developer Intern", "2026-07-30", "rejected", "2026-08-05", None, "2026-08-08",
         "Completed the assessment; received a rejection email three days later."),
        ("Freshworks", "Backend Developer Intern", "2026-08-04", "applied", None, None, "2026-08-04",
         "Submitted a backend-focused resume; no further response recorded."),
        ("Atlassian", "Backend Engineering Intern", "2026-08-11", "rejected", "2026-08-24", None, "2026-08-27",
         "Attempted the coding assessment; did not advance to an interview."),
        ("Cognizant", "Software Development Intern", "2026-08-18", "applied", None, None, "2026-08-19",
         "Applied after a college careers notice; added the confirmation details the following day."),
        ("Paytm", "Backend Developer Intern", "2026-08-18", "rejected", "2026-08-30", None, "2026-09-03",
         "Applied during the same evening search session; rejected after the assessment."),
        ("BrowserStack", "Software Engineering Intern", "2026-08-27", "applied", None, None, "2026-08-27",
         "Included a testing project in the application; no response recorded."),
        ("Razorpay", "Backend Engineering Intern", "2026-08-29", "shortlisted", None, None, "2026-09-04",
         "Resume shortlisted; awaiting assessment instructions."),
        ("Adobe", "Software Engineer Intern", "2026-09-02", "oa_completed", "2026-09-19", None, "2026-09-21",
         "Finished the OA before its deadline; awaiting the next-stage decision."),
        ("Accenture", "Software Engineering Intern", "2026-09-08", "interview", "2026-09-20", "2026-10-16", "2026-10-12",
         "Interview date has passed; outcome has not yet been entered in the tracker."),
        ("Capgemini", "Application Development Intern", "2026-09-09", "applied", None, None, "2026-09-09",
         "Applied after a placement-cell briefing; confirmation received, no next stage recorded."),
        ("Flipkart", "Software Development Intern", "2026-09-09", "shortlisted", None, None, "2026-09-19",
         "Applied during a busy placement week; resume shortlisted ten days later."),
        ("Oracle", "Software Development Intern", "2026-09-14", "oa_completed", "2026-09-26", None, "2026-09-28",
         "Assessment submitted; waiting for the result while continuing other applications."),
        ("Microsoft", "Software Engineer Intern", "2026-09-21", "interview", "2026-10-08", "2026-10-23", "2026-10-12",
         "OA cleared; preparing to discuss data structures and a Django project."),
        ("Juspay", "Software Developer Intern", "2026-09-25", "oa_pending", "2026-10-17", None, "2026-10-10",
         "Assessment invitation arrived after a delay; deadline passed and completion is not recorded."),
        ("Deloitte", "Technology Intern", "2026-09-30", "shortlisted", None, None, "2026-10-08",
         "Resume shortlisted; waiting for the next-round schedule."),
        ("IBM", "Software Developer Intern", "2026-10-02", "applied", None, None, "2026-10-02",
         "Applied during a short break between coursework; no further update yet."),
        ("Amazon", "Software Development Engineer Intern", "2026-10-07", "interview", "2026-10-16", "2026-10-26", "2026-10-18",
         "Completed the coding assessment; interview scheduled for the following week."),
        ("Walmart Global Tech", "Software Engineering Intern", "2026-10-10", "oa_pending", "2026-10-22", None, "2026-10-15",
         "Weekend application; OA invitation received five days later."),
        ("Google", "Software Engineering Intern", "2026-10-14", "oa_pending", "2026-10-27", None, "2026-10-18",
         "Coding assessment invitation received; revising arrays, strings, and basic graphs."),
        ("SAP", "Developer Intern", "2026-10-16", "applied", None, None, "2026-10-16",
         "Recent application using an updated project section; awaiting a response."),
    ]

    records = []
    for company, role, applied, status, oa, interview, updated, note in samples:
        application_date = date.fromisoformat(applied) + date_shift
        update_date = date.fromisoformat(updated) + date_shift
        oa_deadline = None
        if oa:
            oa_deadline = date.fromisoformat(oa) + date_shift
        interview_date = None
        if interview:
            interview_date = date.fromisoformat(interview) + date_shift

        application_time = time(
            random_generator.choice([12, 13, 18, 19, 20, 21]),
            random_generator.randrange(60),
            random_generator.randrange(60),
            random_generator.randrange(1000000),
        )
        created_at = datetime.combine(application_date, application_time, local_timezone)
        if update_date == application_date:
            updated_at = created_at + timedelta(minutes=random_generator.randint(2, 43))
        else:
            update_time = time(
                random_generator.randint(9, 21),
                random_generator.randrange(60),
                random_generator.randrange(60),
                random_generator.randrange(1000000),
            )
            updated_at = datetime.combine(update_date, update_time, local_timezone)

        if application_date < date(2026, 8, 15) + date_shift:
            resume_version = 1
        elif application_date < date(2026, 9, 15) + date_shift:
            resume_version = 2
        else:
            resume_version = 3
        resume_type = "General"
        if "Backend" in role or "Python" in role:
            resume_type = "Backend"

        records.append({
            "company_name": company,
            "job_title": role,
            "application_date": application_date,
            "status": status,
            "oa_deadline": oa_deadline,
            "interview_date": interview_date,
            "resume_version": f"Resume_{resume_type}_Intern_v{resume_version}.pdf",
            "job_url": "",
            "notes": DEMO_MARKER + note + " Employer roles and outcomes are illustrative, not actual vacancies or offers.",
            "created_at": created_at,
            "updated_at": updated_at,
        })
    return records


def main():
    parser = argparse.ArgumentParser(description="Replace only the selected user's [DEMO] applications with synthetic data.")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--as-of", type=date.fromisoformat, default=REFERENCE_DATE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    user = get_user_model().objects.get(username=args.username)
    records = build_demo_records(args.as_of, args.seed)

    for record in records:
        fields = record.copy()
        fields.pop("created_at")
        fields.pop("updated_at")
        JobApplication(user=user, **fields).full_clean()
        assert record["application_date"] <= record["updated_at"].date() <= args.as_of
        assert record["created_at"] <= record["updated_at"]
        for field in ["oa_deadline", "interview_date"]:
            if record[field]:
                assert record[field] >= record["application_date"]
        if record["oa_deadline"] and record["interview_date"]:
            assert record["oa_deadline"] <= record["interview_date"]

    demo_applications = JobApplication.objects.filter(user=user, notes__startswith="[DEMO]")
    print(f"Marked demo records to replace: {demo_applications.count()}")
    print(f"Unmarked records preserved: {user.job_applications.exclude(notes__startswith='[DEMO]').count()}")
    if not args.dry_run:
        with transaction.atomic():
            demo_applications.delete()
            for record in records:
                fields = record.copy()
                created_at = fields.pop("created_at")
                updated_at = fields.pop("updated_at")
                application = JobApplication.objects.create(user=user, **fields)
                JobApplication.objects.filter(pk=application.pk).update(
                    created_at=created_at, updated_at=updated_at,
                )

    print("Synthetic demonstration dataset (dry run):" if args.dry_run else "Synthetic demonstration dataset saved:")
    print(f"Applications: {len(records)}; companies: {len(set(row['company_name'] for row in records))}")
    print(f"Application date range: {min(row['application_date'] for row in records)} to {max(row['application_date'] for row in records)}")
    print("Monthly applications:", dict(sorted(Counter(row["application_date"].strftime("%Y-%m") for row in records).items())))
    print("Statuses:", dict(sorted(Counter(row["status"] for row in records).items())))
    weekend_count = sum(row["application_date"].weekday() >= 5 for row in records)
    print(f"Weekday applications: {len(records) - weekend_count}; weekend applications: {weekend_count}")
    print(f"Seed: {args.seed}; as-of date: {args.as_of}")


if __name__ == "__main__":
    main()
