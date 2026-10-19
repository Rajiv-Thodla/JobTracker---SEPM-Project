# JobTracker

A localhost job application tracker built for a SEPM college project using Django, Python, HTML, CSS, JavaScript, and SQLite.

## Features

- Login and logout using Django's built-in authentication.
- Add, edit, delete, search, and filter your own job applications.
- Save recruitment status and OA/interview dates independently with Save Changes.
- View basic application statistics and upcoming/overdue OA and interview dates on Deadlines & Statistics.
- Reschedule dates in your personal tracker.
- Collapsible sidebar and light/dark mode with a saved theme preference.

Rescheduling a date here does not change a company's actual deadline.

## Future Work

Planned for the end-semester evaluation; these features are not available in the current midsem website:

- A GitHub-style application activity heatmap based on application submission dates.
- An interactive monthly calendar for OA deadlines and interview dates.

## Run locally

From PowerShell in the project directory, use the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/ and log in with your existing account.

## Check and test

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test tracker -v 1
```

Django tests use a separate test database. Keep the existing `db.sqlite3` to preserve saved applications.

## Synthetic demonstration data

The midsem snapshot contains 24 synthetic internship applications across 24 companies, dated 12 June to 16 October 2026, with a reference date of 19 October 2026.

| Month | Applications |
|---|---:|
| June 2026 | 2 |
| July 2026 | 3 |
| August 2026 | 6 |
| September 2026 | 8 |
| October 2026, through the 16th | 5 |

There are 22 weekday and 2 weekend applications, including two days with two applications each. Dates are deliberately curated to represent quiet periods, a busier internship search in August/September, and irregular gaps. The fixed random seed varies times of day, seconds, and update intervals reproducibly.

Statuses: 7 Applied, 3 Resume Shortlisted, 3 OA Pending, 2 OA Completed, 3 Interview, 1 Offer Received, 4 Rejected, and 1 Withdrawn. On the reference date, the deadline page has 2 overdue events (1 OA and 1 interview) and 4 upcoming events (2 OAs and 2 interviews).

All generated notes start with `[DEMO]`. Employer roles, assessments, interviews, and outcomes are fictional examples, not claims about actual recruitment. Nimbly Labs, CodeHarbor Labs, and PixelNest Labs are fictional employers. Historical application timestamps simulate an accumulated tracker history; the real local account's creation date and authentication records are preserved separately. Resume filenames are labels, not uploaded files; job URLs are left blank.

Back up the database before regenerating data. Preview without saving:

```powershell
.\.venv\Scripts\python.exe seed_demo.py --username admin --seed 20261019 --as-of 2026-10-19 --dry-run
```

Regenerate the snapshot:

```powershell
.\.venv\Scripts\python.exe seed_demo.py --username admin --seed 20261019 --as-of 2026-10-19
```

The script replaces only the selected user's applications whose notes start with `[DEMO]`. Unmarked applications and other users' records remain untouched. Repeating the command produces the same 24 application values and timestamps without accumulating duplicates; database row IDs may differ. Changing `--as-of` shifts the sample dates together. Overdue/upcoming classifications naturally change as the actual date advances. The heatmap and monthly calendar remain Future Work.

## Project structure

- `config/settings.py`: Django configuration and SQLite connection.
- `config/urls.py`: Main routes, including authentication and the tracker.
- `tracker/models.py`: Job application fields and recruitment statuses.
- `tracker/forms.py`: Application form fields, widgets, and validation through a ModelForm.
- `tracker/views.py`: Application pages, statistics, and form submissions.
- `tracker/urls.py`: Routes for the tracker views.
- `tracker/templates/`: HTML templates with CSS and small theme/sidebar scripts.
- `tracker/tests.py`: Automated tests for existing application behavior.

Data flows from HTML forms to Django views and models, then to SQLite. Pages are rendered with Django templates.
