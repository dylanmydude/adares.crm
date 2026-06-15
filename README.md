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

Run tests:

```bash
./venv/bin/python manage.py test
```

## Feature Summary

- Accounts: register, log in, log out, and profile placeholder
- Dashboard: totals, estimated tax, recent records, and unread notifications
- Finance: income and expense CRUD
- CRM: clients and jobs
- Invoicing: invoices, invoice items, statuses, and totals
- Tax: estimated tax calculations and history
- Reports: income, expense, and tax summary PDF generation
- Backup: database backup creation and download
- Audit: user action history
- Notifications: unread/read notification workflow

## Project Notes

This project uses document-driven development. The `/docs` folder is the source of truth for module scope, build order, and implementation rules.
