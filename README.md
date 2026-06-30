# ADARES CRM

ADARES CRM is a Django web application for gig workers to manage income, expenses, clients, jobs, invoices, tax estimates, PDF reports, backups, audit logs, and notifications in one place.

## Technology Stack

- Python 3 and Django 4.2
- SQLite for local development
- Django Templates
- Bootstrap 5.3, Bootstrap Icons, HTMX, Alpine.js, Chart.js
- Custom ADARES CSS theme

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Apply migrations:

```bash
./venv/bin/python manage.py migrate
```

Create a superuser:

```bash
./venv/bin/python manage.py createsuperuser
```

Start the development server:

```bash
./venv/bin/python manage.py runserver
```

## Cloudflare Tunnel Demo

For a temporary public demo URL, start Django in one terminal:

```bash
./venv/bin/python manage.py runserver 127.0.0.1:8000
```

In a second terminal, start a Cloudflare Tunnel to the local server:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Open the generated `https://*.trycloudflare.com` URL in a browser. Both terminals must stay open while the demo is live.

Run tests:

```bash
./venv/bin/python manage.py test
```

## Feature Summary

- Accounts: register, email verification, log in, log out, editable profile, and user settings
- Management: administrator-only user management for staff and superusers
- Dashboard: totals, estimated tax, recent records, and unread notifications
- Finance: income and expense CRUD
- CRM: clients and jobs
- Invoicing: invoices, invoice items, statuses, and totals
- Tax: South African progressive individual income tax estimates and history
- Reports: income, expense, and tax summary PDF generation
- Backup: database backup creation and download
- Audit: administrator-only audit history with filters
- Notifications: unread/read notification workflow

## Email Configuration

Local development uses Django's console email backend by default. SMTP can be configured with environment variables:

- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`
- `DEFAULT_FROM_EMAIL`

Do not commit email credentials.
