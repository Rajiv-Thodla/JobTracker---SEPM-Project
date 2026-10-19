
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import JobApplication


class JobApplicationTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="testuser",
            password="TestPass123!"
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            password="TestPass456!"
        )

        self.client.force_login(self.user)

        self.application = JobApplication.objects.create(
            user=self.user,
            company_name="Google",
            job_title="Software Engineer Intern",
            application_date=date(2026, 10, 1),
            status="applied"
        )

    def test_dashboard_loads(self):
        response = self.client.get(
            reverse("tracker:dashboard")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google")

    def test_add_application(self):
        response = self.client.post(
            reverse("tracker:add_application"),
            {
                "company_name": "Microsoft",
                "job_title": "SDE Intern",
                "application_date": "2026-10-10",
                "status": "oa_pending",
            }
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            JobApplication.objects.filter(
                user=self.user,
                company_name="Microsoft"
            ).exists()
        )

    def test_edit_application(self):
        response = self.client.post(
            reverse(
                "tracker:edit_application",
                args=[self.application.pk]
            ),
            {
                "company_name": "Google",
                "job_title": "Software Engineer Intern",
                "application_date": "2026-10-01",
                "status": "oa_completed",
            }
        )

        self.assertEqual(response.status_code, 302)

        self.application.refresh_from_db()

        self.assertEqual(
            self.application.status,
            "oa_completed"
        )

    def test_delete_application(self):
        response = self.client.post(
            reverse(
                "tracker:delete_application",
                args=[self.application.pk]
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            JobApplication.objects.filter(
                pk=self.application.pk
            ).exists()
        )

    def test_search(self):
        response = self.client.get(
            reverse("tracker:dashboard"),
            {"search": "Google"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google")

    def test_status_filter(self):
        response = self.client.get(
            reverse("tracker:dashboard"),
            {"status": "applied"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google")

    def test_invalid_application(self):
        response = self.client.post(
            reverse("tracker:add_application"),
            {
                "company_name": "",
                "job_title": "",
                "application_date": "2026-10-10",
                "status": "applied",
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            JobApplication.objects.filter(
                user=self.user
            ).count(),
            1
        )

    def test_user_data_is_private(self):
        other_application = JobApplication.objects.create(
            user=self.other_user,
            company_name="Private Company",
            job_title="Developer",
            status="applied"
        )

        response = self.client.get(
            reverse("tracker:dashboard")
        )

        self.assertNotContains(
            response,
            "Private Company"
        )

        edit_response = self.client.get(
            reverse(
                "tracker:edit_application",
                args=[other_application.pk]
            )
        )

        self.assertEqual(edit_response.status_code, 404)

        delete_response = self.client.post(
            reverse(
                "tracker:delete_application",
                args=[other_application.pk]
            )
        )

        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(
            JobApplication.objects.filter(
                pk=other_application.pk
            ).exists()
        )

    def test_statistics_are_private(self):
        JobApplication.objects.create(
            user=self.user, company_name="Second", job_title="Developer",
            application_date=date(2026, 10, 1), status="oa_pending",
        )
        JobApplication.objects.create(
            user=self.other_user, company_name="Private Activity", job_title="Developer",
            application_date=date(2026, 10, 1), status="offer",
            interview_date=date(2026, 10, 25),
        )
        response = self.client.get(reverse("tracker:activity"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(dict(response.context["statistics"]), {
            "Total applications": 2, "OA Pending": 1, "Interviews": 0,
            "Offers received": 0, "Rejected": 0,
        })
        self.assertContains(response, "Deadlines &amp; Statistics")
        self.assertNotContains(response, "Private Activity")

    @patch("tracker.views.timezone.localdate", return_value=date(2026, 10, 19))
    def test_deadlines_are_relevant_private_and_sorted(self, localdate):
        records = [
            (self.user, "Later interview", "interview", date(2026, 10, 23)),
            (self.user, "Overdue OA", "oa_pending", date(2026, 10, 18)),
            (self.user, "Today OA", "oa_pending", date(2026, 10, 19)),
            (self.user, "Completed OA", "oa_completed", date(2026, 10, 18)),
            (self.user, "Old interview", "interview", date(2026, 10, 17)),
            (self.other_user, "Private deadline", "oa_pending", date(2026, 10, 20)),
        ]
        for user, company, status, event_date in records:
            JobApplication.objects.create(
                user=user, company_name=company, job_title="Developer", status=status,
                oa_deadline=event_date, interview_date=event_date,
            )
        response = self.client.get(reverse("tracker:activity"))
        groups = response.context["deadline_groups"]
        overdue_companies = []
        for event in groups[0][1]:
            overdue_companies.append(event["application"].company_name)

        upcoming_companies = []
        for event in groups[1][1]:
            upcoming_companies.append(event["application"].company_name)

        self.assertEqual(overdue_companies, [
            "Old interview", "Old interview", "Completed OA", "Completed OA", "Overdue OA", "Overdue OA",
        ])
        self.assertEqual(upcoming_companies, ["Today OA", "Today OA", "Later interview", "Later interview"])
        self.assertNotContains(response, "Private deadline")

    def test_deadlines_page_requires_login_and_handles_empty_user(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("tracker:activity"))
        self.assertEqual(dict(response.context["statistics"])["Total applications"], 0)
        self.assertContains(response, "No past dates (including overdue).")
        self.client.logout()
        self.assertRedirects(
            self.client.get(reverse("tracker:activity")),
            reverse("login") + "?next=" + reverse("tracker:activity"),
        )

    def test_status_and_date_updates_require_post(self):
        for name in ["update_status", "update_event_date"]:
            response = self.client.get(reverse("tracker:" + name, args=[self.application.pk]))
            self.assertEqual(response.status_code, 405)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "applied")
        self.assertIsNone(self.application.oa_deadline)

    def test_status_and_date_saves_are_independent(self):
        status_url = reverse("tracker:update_status", args=[self.application.pk])
        date_url = reverse("tracker:update_event_date", args=[self.application.pk])
        response = self.client.post(status_url, {
            "status": "oa_pending", "event_date": "2026-10-25",
        })
        self.assertRedirects(response, reverse("tracker:dashboard"))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "oa_pending")
        self.assertIsNone(self.application.oa_deadline)
        response = self.client.post(date_url, {
            "event_date": "2026-10-25", "status": "offer", "return_to": "activity",
        })
        self.assertRedirects(response, reverse("tracker:activity"))
        self.application.refresh_from_db()
        self.assertEqual(self.application.oa_deadline, date(2026, 10, 25))
        self.assertEqual(self.application.status, "oa_pending")
        self.assertContains(self.client.get(reverse("tracker:dashboard")), "OA: 25 Oct 2026")
        self.assertContains(self.client.get(reverse("tracker:activity")), "OA: 25 Oct 2026")

    def test_interview_reschedule_and_clear_date(self):
        self.application.status = "interview"
        self.application.oa_deadline = date(2026, 10, 20)
        self.application.save()
        url = reverse("tracker:update_event_date", args=[self.application.pk])
        response = self.client.post(url, {"event_date": "2026-10-26", "return_to": "https://example.com"})
        self.assertRedirects(response, reverse("tracker:dashboard"))
        self.application.refresh_from_db()
        self.assertEqual(self.application.interview_date, date(2026, 10, 26))
        self.assertEqual(self.application.oa_deadline, date(2026, 10, 20))
        self.client.post(url, {"event_date": ""})
        self.application.refresh_from_db()
        self.assertIsNone(self.application.interview_date)

    def test_update_validation(self):
        status_url = reverse("tracker:update_status", args=[self.application.pk])
        date_url = reverse("tracker:update_event_date", args=[self.application.pk])
        self.assertEqual(self.client.post(status_url, {"status": "unknown"}).status_code, 400)
        self.assertEqual(self.client.post(date_url, {"event_date": "2026-10-25"}).status_code, 400)
        self.application.status = "oa_pending"
        self.application.save()
        self.assertEqual(self.client.post(date_url, {"event_date": "invalid"}).status_code, 400)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "oa_pending")
        self.assertIsNone(self.application.oa_deadline)

    def test_update_endpoints_reject_other_users_and_anonymous_users(self):
        other_application = JobApplication.objects.create(
            user=self.other_user, company_name="Private", job_title="Developer", status="oa_pending",
        )
        for name, data in [
            ("update_status", {"status": "offer"}),
            ("update_event_date", {"event_date": "2026-10-25"}),
        ]:
            url = reverse("tracker:" + name, args=[other_application.pk])
            self.assertEqual(self.client.post(url, data).status_code, 404)
            self.assertEqual(Client().post(url, data).status_code, 302)
        other_application.refresh_from_db()
        self.assertEqual(other_application.status, "oa_pending")
        self.assertIsNone(other_application.oa_deadline)

    def test_update_endpoints_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for name in ["update_status", "update_event_date"]:
            self.assertEqual(client.post(reverse("tracker:" + name, args=[self.application.pk]), {}).status_code, 403)

    def test_dashboard_contains_separate_explicit_save_forms(self):
        self.application.status = "oa_pending"
        self.application.save()
        response = self.client.get(reverse("tracker:dashboard"))
        html = response.content.decode()
        forms = []
        for section in html.split("<form")[1:]:
            forms.append(section.split("</form>", 1)[0])

        for endpoint, expected_field, other_field in [
            ("update_status", "status", "event_date"),
            ("update_event_date", "event_date", "status"),
        ]:
            url = reverse("tracker:" + endpoint, args=[self.application.pk])
            matching_forms = []
            for form in forms:
                if f'action="{url}"' in form:
                    matching_forms.append(form)

            self.assertEqual(len(matching_forms), 1)
            form = matching_forms[0]
            self.assertIn('method="post"', form)
            self.assertIn(f'name="{expected_field}"', form)
            self.assertNotIn(f'name="{other_field}"', form)
            self.assertEqual(form.count('<button type="submit"'), 1)
            self.assertEqual(form.count("Save Changes"), 1)

        self.assertNotIn("onchange=", html)
        self.assertNotIn("oninput=", html)
        self.assertContains(response, "OA / Interview")
        self.assertContains(response, "Save Changes", count=2)

    @patch("tracker.views.timezone.localdate", return_value=date(2026, 10, 19))
    def test_both_pages_show_saved_dates_for_every_status(self, localdate):
        date_combinations = [
            (None, None),
            (date(2026, 10, 22), None),
            (None, date(2026, 10, 23)),
            (date(2026, 10, 22), date(2026, 10, 23)),
        ]
        for status in JobApplication.Status.values:
            for oa_date, interview_date in date_combinations:
                with self.subTest(status=status, oa=oa_date, interview=interview_date):
                    self.application.status = status
                    self.application.oa_deadline = oa_date
                    self.application.interview_date = interview_date
                    self.application.save()
                    before = JobApplication.objects.values().get(pk=self.application.pk)
                    dashboard = self.client.get(reverse("tracker:dashboard"))
                    saved_application = dashboard.context["applications"][0]
                    self.assertEqual(saved_application.oa_deadline, oa_date)
                    self.assertEqual(saved_application.interview_date, interview_date)
                    if oa_date:
                        self.assertContains(dashboard, "OA: 22 Oct 2026")
                    else:
                        self.assertNotContains(dashboard, "OA:")
                    if interview_date:
                        self.assertContains(dashboard, "Interview: 23 Oct 2026")
                    else:
                        self.assertNotContains(dashboard, "Interview:")
                    if not oa_date and not interview_date:
                        date_cell = dashboard.content.decode().split("<tbody>")[1].split("<td")[6].split("</td>")[0]
                        self.assertRegex(date_cell, r">\s*-\s*(?:<|▾|$)")

                    deadlines = self.client.get(reverse("tracker:activity"))
                    events = []
                    for heading, group in deadlines.context["deadline_groups"]:
                        events.extend(group)
                    expected = []
                    if oa_date:
                        expected.append(("oa_deadline", oa_date))
                    if interview_date:
                        expected.append(("interview_date", interview_date))
                    self.assertEqual([(event["field"], event["date"]) for event in events], expected)
                    for field, event_date in expected:
                        self.assertContains(deadlines, f'id="event-{self.application.pk}-{field}"', count=1)
                    self.assertEqual(before, JobApplication.objects.values().get(pk=self.application.pk))

    def test_explicit_date_saves_are_independent_of_status(self):
        url = reverse("tracker:update_event_date", args=[self.application.pk])
        for status in JobApplication.Status.values:
            for field in ["oa_deadline", "interview_date"]:
                with self.subTest(status=status, field=field):
                    self.application.status = status
                    self.application.oa_deadline = date(2026, 10, 22)
                    self.application.interview_date = date(2026, 10, 23)
                    self.application.save()
                    other_field = "interview_date" if field == "oa_deadline" else "oa_deadline"
                    other_date = getattr(self.application, other_field)
                    response = self.client.post(url, {
                        "event_field": field, "event_date": "2026-10-29",
                        "return_to": "activity", "status": "offer",
                    })
                    self.assertRedirects(response, reverse("tracker:activity"))
                    self.application.refresh_from_db()
                    self.assertEqual(getattr(self.application, field), date(2026, 10, 29))
                    self.assertEqual(getattr(self.application, other_field), other_date)
                    self.assertEqual(self.application.status, status)
                    self.client.post(url, {"event_field": field, "event_date": ""})
                    self.application.refresh_from_db()
                    self.assertIsNone(getattr(self.application, field))
                    self.assertEqual(getattr(self.application, other_field), other_date)

    def test_date_update_rejects_invalid_field_and_other_owner(self):
        url = reverse("tracker:update_event_date", args=[self.application.pk])
        before = JobApplication.objects.values().get(pk=self.application.pk)
        for field in ["status", "user_id", "notes", "", "unknown"]:
            with self.subTest(field=field):
                self.assertEqual(self.client.post(url, {
                    "event_field": field, "event_date": "2026-10-29",
                }).status_code, 400)
        self.assertEqual(self.client.post(url, {
            "event_field": "oa_deadline", "event_date": "2026-02-30",
        }).status_code, 400)
        self.assertEqual(before, JobApplication.objects.values().get(pk=self.application.pk))
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.post(url, {
            "event_field": "oa_deadline", "event_date": "2026-10-29",
        }).status_code, 404)
