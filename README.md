# Pharmacy Expiry Watchlist

A small, focused web app for a medical store owner to track medicine batches and
catch the ones about to expire. Built with Django (server-rendered templates).

> Brief: enter batches → see the full list → soon-to-expire and already-expired
> stock jumps out → delete what's sold or cleared → the whole thing behind a
> password. (From the conversation with Iqbal Bhai.)

## What it does

- **Add a batch** — medicine name, batch number, expiry date, quantity, supplier.
- **Full list, soonest expiry first** — that's how stock gets checked anyway.
- **Expired batches shown separately** at the top, in red — impossible to miss.
- **Expiring within 90 days** is clearly flagged in amber with a "N days left" badge.
- **Delete** a batch when it's sold out or cleared (with a confirm step). No history kept.
- **Password lock** — one simple password unlocks the list; customers at the
  counter can't see the stock. A **Lock** button hides it again.
- **Search** by medicine, batch number, or supplier.
- A summary bar shows totals: in stock / expiring soon / expired.

The 90-day window lives in one place: `EXPIRY_WARNING_DAYS` in `watchlist/models.py`.

## Tech

- Django 5.2 (templates, models, forms, the admin) + SQLite by default.
- WhiteNoise for static files, gunicorn + `DATABASE_URL` (Postgres) for production.
- No JavaScript framework — just the Django template language and one CSS file.

## Run it locally

Requires Python 3.12+.

```bash
cd pharmacy-expiry-watchlist
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Optional: set your own password (defaults to "iqbal123" if you skip this)
cp .env.example .env        # then edit WATCHLIST_PASSWORD

python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/ and unlock with your password.

### Tests

```bash
python manage.py test
```

### Admin (optional)

The batches are also editable through Django's admin:

```bash
python manage.py createsuperuser
# then visit /admin/
```

## Configuration (environment variables)

All config is via environment variables (see `.env.example`). Sensible defaults
let it run locally with zero setup.

| Variable | What it's for | Default |
|---|---|---|
| `WATCHLIST_PASSWORD` | The password that unlocks the list | `iqbal123` (change it!) |
| `SECRET_KEY` | Django secret key | insecure dev key |
| `DEBUG` | `True` locally, `False` in production | `True` |
| `ALLOWED_HOSTS` | Comma-separated hostnames in production | localhost in DEBUG |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated `https://…` origins in production | empty |
| `DATABASE_URL` | Managed DB URL (e.g. Postgres). If unset, SQLite is used | SQLite file |
| `TIME_ZONE` | Timezone for "days until expiry" | `Asia/Kolkata` |

## Deploy

This repo is deploy-ready: `requirements.txt`, `Procfile`, `render.yaml`, env-based
settings, WhiteNoise static serving, and gunicorn are all set up.

**Important:** for real stock data, use a persistent database. Free web hosts have
an ephemeral filesystem, so a SQLite file would be wiped on restart. The app reads
`DATABASE_URL`, so attach a managed Postgres and it just works — `render.yaml` wires
a free Postgres in automatically.

### Render (one click, via `render.yaml`)

1. Push this repo to GitHub (see below).
2. On Render: **New → Blueprint**, pick the repo. It reads `render.yaml`, creates the
   web service + a free Postgres, and generates a `SECRET_KEY`.
3. Set **`WATCHLIST_PASSWORD`** in the service's Environment tab.
4. Deploy. (Migrations run automatically via `preDeployCommand`; the Render hostname
   is added to `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` for you.)

### Any other host (Railway / Fly / a VPS)

Set the environment variables from the table above, then:

```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn pharmacy.wsgi          # the Procfile already declares this
```

## Project layout

```
pharmacy/            Django project (settings, urls, wsgi)
watchlist/           the app
  models.py          Batch model + expiry helpers
  views.py           list / add / delete / unlock / lock
  forms.py           BatchForm, UnlockForm
  gate.py            the simple password gate (session-based)
  urls.py            routes
  admin.py           admin registration
  templates/watchlist/   base, list, add, unlock, batch card
  static/watchlist/      style.css
  tests.py           16 tests covering model, gate, and workflow
render.yaml          Render blueprint
Procfile             release (migrate) + web (gunicorn) commands
```
