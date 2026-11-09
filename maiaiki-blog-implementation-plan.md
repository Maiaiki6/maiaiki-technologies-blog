# Maiaiki Technologies Blog — Implementation Plan

## 1. Project Overview

A server-rendered blog for the phone repair shop MAIAIKI TECHNOLOGIES, built solo in 14 days with Django. It works like a small WordPress-style blog with shop features on top: quote requests, repair status lookup, booking requests, and a newsletter. The shop staff write posts and manage everything from the Django admin, so no custom dashboard is needed.

Week 1 ships the launch version (Day 7). Week 2 adds search, tags, scheduling, image resizing, the newsletter, the repair tracker, booking, testimonials, analytics, and the full test suite to the live site.

## 2. Goals & Success Criteria

**Core goals**

- Shop staff can write, schedule, and publish posts without touching code
- Customers can request a quote, book a slot, or look up a repair in under a minute on a phone
- Pages load fast on mobile data and rank for local repair searches
- Customer data (phone numbers, tickets) is protected from guessing and spam

**Success criteria**

| Criteria | Definition of Done |
|---|---|
| Publishing | Staff publish a post from `/admin/` with an image in under 3 minutes |
| Mobile | Every page passes a real-phone check at 360px width, no horizontal scroll |
| Performance | Lighthouse mobile performance 85+ on the homepage and a post page |
| Quote form | Submission saved in the database and emailed to the shop within 1 minute |
| Status tracker | A wrong ticket or phone number returns the same generic message; lookups are rate limited |
| Booking | The same slot can never be confirmed twice (enforced by the database) |
| Tests | `pytest` passes in CI with coverage on models, views, forms, booking, and tracker |
| Security | `manage.py check --deploy` reports no warnings on production settings |

## 3. Tech Stack

**Backend**

| Technology | Role | Why |
|---|---|---|
| Python 3.12 + Django 5.x | Web framework | The built-in admin is the post editor and ticket manager, so there is no CMS to build in 14 days |
| django-ratelimit | Rate limiting | One decorator per view; protects the quote, newsletter, booking, and tracker endpoints |
| django-environ | Settings | Reads secrets from environment variables so nothing sensitive lives in Git |
| Pillow | Image processing | Resizes and compresses uploads on save |
| gunicorn + WhiteNoise | App server and static files | One process serves the app and compressed static files with no separate Nginx |

**Frontend**

| Technology | Role | Why |
|---|---|---|
| Django templates | Page rendering | Server-rendered HTML is fast on weak phones and indexes well |
| Tailwind CSS (CLI build) | Styling | Utility classes keep a one-person design consistent; the CLI avoids a Node-heavy toolchain |
| Plain JS (minimal) | Small interactions | Mobile menu and slot picker only; no framework needed |

**Data**

| Technology | Role | Why |
|---|---|---|
| SQLite | Local development | Zero setup |
| PostgreSQL | Production | Needed for full-text search and the partial unique constraint used by booking |
| Cloudflare R2 or Cloudinary | Media storage | Hosting platforms like Render and Railway have ephemeral disks, so uploaded images must live elsewhere |

**Infrastructure / DevOps**

| Technology | Role | Why |
|---|---|---|
| Render or Railway | Hosting | Git-push deploys, managed Postgres, free SSL |
| GitHub Actions | CI | Runs `pytest` and `manage.py check --deploy` on every push |
| Brevo or Resend (SMTP) | Transactional email | Quote notifications, newsletter confirmation, and booking replies without running a mail server |

**Integrations**

| Technology | Role | Why |
|---|---|---|
| WhatsApp click-to-chat (`wa.me` link) | Customer contact | No API needed; one link with a prefilled message |
| Google Maps embed | Location | Free iframe; no API key needed for a basic embed |
| Plausible or Google Analytics | Analytics | Plausible is cookie-free (no consent banner); GA is free if the owner prefers it |

## 4. System Architecture

```
                         HTTPS (Render/Railway TLS)
 Customer phone ───────────────────────────────────────┐
 (browser)                                              ▼
                                         ┌──────────────────────────┐
 Shop staff ── HTTPS /admin/ ──────────► │  gunicorn + Django app   │
 (browser)                               │  ┌────────┬──────┬─────┐ │
                                         │  │ blog   │ shop │ ... │ │
                                         │  └────────┴──────┴─────┘ │
                                         │  WhiteNoise serves /static│
                                         └───┬──────────┬───────┬───┘
                                             │          │       │
                       SQL (psycopg)         │          │       │ SMTP (TLS)
                    ┌────────────────────────┘          │       └────────► Brevo / Resend
                    ▼                                   │                   (quote alerts,
           ┌─────────────────┐        S3 API (boto3)    │                    newsletter, booking)
           │  PostgreSQL     │                          ▼
           │  posts, tickets,│                ┌───────────────────┐
           │  bookings, ...  │                │ Cloudflare R2 /   │
           └─────────────────┘                │ Cloudinary (media)│
                                              └───────────────────┘
```

**Key architectural decisions**

- **One Django project, two apps (`blog`, `shop`).** Content and customer transactions have different change rates; splitting them keeps models and tests tidy without microservice overhead.
- **Scheduling without a scheduler.** Posts have a `publish_at` timestamp and the public queryset filters `publish_at <= now()`. No cron job or worker is needed, and a missed run can't leave a post unpublished.
- **Media in object storage.** Platform disks are wiped on redeploy, so uploads go to R2/Cloudinary from day one rather than being migrated later.
- **Server-side enforcement for anything that matters.** Slot availability, rate limits, and ticket checks run on the server; the page only mirrors them.

## 5. Domain-Specific Deep Dives

### 5.1 Publishing, scheduling, and images

A post is visible when `status == "published"` and `publish_at <= now()`. Put this in a custom manager so no view can forget it.

```python
# blog/models.py
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            status="published", publish_at__lte=timezone.now()
        )

class Post(models.Model):
    ...
    objects = models.Manager()
    live = PublishedManager()   # use Post.live in every public view
```

Image pipeline (on `save()`): open with Pillow, fix EXIF rotation, cap the long edge at 1600px, convert to WebP at quality 80, and also store a 480px thumbnail for list cards. Always set `width`/`height` attributes in templates to avoid layout shift.

**Failure modes:** very large uploads (set `DATA_UPLOAD_MAX_MEMORY_SIZE` and validate file type), HEIC photos from iPhones (convert or reject with a clear message), and re-saving an unchanged post re-processing the image (only process when the file field changed).

### 5.2 Search and tags

- **Dev (SQLite):** `title__icontains` / `body__icontains`.
- **Production (Postgres):** `SearchVector("title", "body")` with `SearchQuery`, ranked by `SearchRank`, plus a GIN index on a stored `search_vector` field if the post count grows.
- Tags are a `ManyToManyField`; tag pages live at `/blog/tag/<slug>/`.

### 5.3 Quote requests and spam protection

```python
# shop/views.py
@ratelimit(key="ip", rate="5/h", method="POST", block=True)
def quote_request(request):
    form = QuoteRequestForm(request.POST or None)
    if form.is_valid() and not form.cleaned_data["website"]:   # honeypot field
        quote = form.save()
        send_quote_email.delay(quote.id) if USE_QUEUE else send_quote_email(quote.id)
        return redirect("shop:quote_thanks")
    return render(request, "shop/quote.html", {"form": form})
```

Layers: honeypot field named `website` (hidden with CSS; bots fill it), IP rate limit, and server-side phone number validation. If spam still gets through, add Cloudflare Turnstile (free, less annoying than reCAPTCHA).

**Failure modes:** email provider outage (save the quote first, send the email second, and show it in the admin regardless) and bots spamming the form (rate limit plus honeypot).

### 5.4 Newsletter (double opt-in)

1. Visitor submits their email, and a `Subscriber` row is created with `confirmed=False`.
2. A confirmation email contains a signed link made with `django.core.signing.TimestampSigner`.
3. Clicking the link sets `confirmed=True`.
4. Every email carries a signed unsubscribe link; the admin has a "Export confirmed subscribers (CSV)" action.

Double opt-in stops people subscribing someone else's address and keeps the list clean.

### 5.5 Repair status tracker

Customers look up a repair with **ticket code + the last 4 digits of the phone number**.

- Ticket codes are random 8-character strings from an unambiguous alphabet (no `0/O`, `1/I`), not sequential IDs.
- The lookup returns the same message ("We couldn't find a repair with those details") for a wrong code, a wrong phone, or both, so attackers can't tell which part was right.
- Rate limit: 10 lookups per hour per IP.
- Only expose device, status, and last-updated time; never the full phone number or customer name.

Statuses: `received → diagnosing → repairing → ready → collected`.

### 5.6 Booking requests

A booking is a request that the shop confirms or declines in the admin. Double-booking is prevented by the database, not the page:

```python
class Booking(models.Model):
    ...
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date", "slot"],
                condition=Q(status__in=["pending", "confirmed"]),
                name="one_active_booking_per_slot",
            )
        ]
```

Wrap the create in `try/except IntegrityError` and show "That slot was just taken, please pick another." Slots are generated from opening hours stored in settings, minus active bookings and past times.

**Failure modes:** two people submitting the same slot at once (the constraint handles it), timezone mistakes (store UTC, display in the shop's local timezone set in `TIME_ZONE`), and slots offered on closed days.

## 6. Phase Breakdown

### Phase 1 — Foundations & Core Blog (Days 1–3)
**Duration:** 3 days · **Depends on:** nothing

- [ ] Create the repo, virtualenv, Django project (`config`), and apps (`blog`, `shop`)
- [ ] Split settings into environment variables via django-environ
- [ ] Create models: `Category`, `Post`, `QuoteRequest`; run migrations
- [ ] Register models in the admin with list filters, search, and slug auto-fill
- [ ] Build `base.html` with the header, footer, and "MAIAIKI TECHNOLOGIES" branding
- [ ] Set up the Tailwind CLI build and commit the built CSS
- [ ] Build blog list (paginated, 9 per page), post detail, and category pages
- [ ] Build the homepage with hero and latest posts
- [ ] Throwaway-deploy the empty project to the host to catch config problems early
- [ ] Write 3 starter posts

**Deliverable:** staff can publish a post in the admin and visitors can read it on a phone.

### Phase 2 — Shop Features & Hardening (Days 4–5)
**Depends on:** Phase 1

- [ ] Build the Services and Pricing page
- [ ] Build the quote form with honeypot, rate limit, and email notification
- [ ] Add click-to-call (`tel:`), WhatsApp (`wa.me`), and Maps embed with opening hours
- [ ] Add page titles, meta descriptions, Open Graph tags, `sitemap.xml`, and `robots.txt`
- [ ] Add JSON-LD `LocalBusiness` markup on the home and contact pages
- [ ] Test on a real phone and fix layout issues
- [ ] Production settings: `DEBUG=False`, `ALLOWED_HOSTS`, secure cookies, HSTS, `SECURE_SSL_REDIRECT`

**Deliverable:** customers can contact the shop and request a quote; the site passes `check --deploy`.

### Phase 3 — Deploy & Launch (Days 6–7)
**Depends on:** Phase 2

- [ ] Provision Postgres and the web service; set environment variables
- [ ] Configure R2/Cloudinary for media and WhiteNoise for static files
- [ ] Connect the domain, enable HTTPS, and set up daily database backups
- [ ] Run a full test pass on the live site
- [ ] Publish the starter posts and write a one-page admin guide
- [ ] Submit the sitemap to Google Search Console

**Deliverable:** the blog is live on the real domain.

### Phase 4 — Content Discovery & Media (Days 8–9)
**Depends on:** Phase 3

- [ ] Add `Tag` model, tag pages, and tag chips on cards
- [ ] Add search (icontains in dev, full-text search in production)
- [ ] Add `publish_at` and the `Post.live` manager; verify scheduled posts appear on time
- [ ] Build the Pillow image pipeline and re-process existing images
- [ ] Add a data migration for existing posts (`publish_at = created_at`)

**Deliverable:** visitors can search and filter posts, and staff can schedule them.

### Phase 5 — Audience & Customer Tools (Days 10–11)
**Depends on:** Phase 4

- [ ] Build the newsletter signup, double opt-in emails, and unsubscribe
- [ ] Add the CSV export admin action for confirmed subscribers
- [ ] Add the `RepairTicket` model with status choices and admin editing
- [ ] Build the lookup page (ticket code + last 4 digits of phone, rate limited)
- [ ] Add an optional "email the customer when status changes to ready" admin action

**Deliverable:** shop can grow an email list and customers can check repair progress.

### Phase 6 — Booking, Testimonials & Quality (Days 12–14)
**Depends on:** Phase 5

- [ ] Add `Booking` with the partial unique constraint and a slot picker
- [ ] Add admin actions to confirm or decline bookings, with email to the customer
- [ ] Add `Testimonial` model and homepage section
- [ ] Add analytics script (respecting consent if using GA)
- [ ] Write tests: models, managers, views, forms, booking race condition, tracker rate limit
- [ ] Run a security review of every public form (CSRF, validation, rate limits)
- [ ] Final real-phone QA, update the admin guide, hand over logins

**Deliverable:** all features live, tested, and handed over.

## 7. Milestones

| # | Milestone | Target | Status |
|---|---|---|---|
| 1 | Models, admin, and base template working locally | End of Day 1–2 | ⬜ Pending |
| 2 | Blog readable end to end with starter posts | End of Day 3 | ⬜ Pending |
| 3 | Quote form, contact buttons, and SEO basics done | End of Day 5 | ⬜ Pending |
| 4 | Live on the real domain over HTTPS | End of Day 6 | ⬜ Pending |
| 5 | Launch complete | End of Day 7 | ⬜ Pending |
| 6 | Search, tags, scheduling, and image pipeline live | End of Day 9 | ⬜ Pending |
| 7 | Newsletter and repair tracker live | End of Day 11 | ⬜ Pending |
| 8 | Booking and testimonials live | End of Day 12 | ⬜ Pending |
| 9 | Tests, analytics, and security review done | End of Day 13 | ⬜ Pending |
| 10 | Handover complete | Day 14 | ⬜ Pending |

## 8. Database Schema

```sql
-- Blog content
Category
  id            PK
  name          varchar(80) UNIQUE
  slug          slug UNIQUE

Tag
  id            PK
  name          varchar(50) UNIQUE
  slug          slug UNIQUE

Post
  id            PK
  title         varchar(200)
  slug          slug UNIQUE                -- index
  excerpt       varchar(300)
  body          text
  cover_image   image (R2/Cloudinary path)
  cover_thumb   image
  category_id   → Category.id
  author_id     → auth_user.id
  status        enum('draft','published')
  publish_at    timestamptz                -- index (public queries filter on this)
  created_at    timestamptz
  updated_at    timestamptz
  search_vector tsvector                   -- GIN index (production only)

Post_tags
  post_id       → Post.id
  tag_id        → Tag.id                   -- UNIQUE(post_id, tag_id)

-- Customer-facing shop data
QuoteRequest
  id            PK
  name          varchar(100)
  phone         varchar(20)
  email         varchar(254) NULL
  device_model  varchar(100)
  issue         text
  status        enum('new','contacted','closed')
  created_at    timestamptz                -- index

RepairTicket
  id            PK
  code          char(8) UNIQUE             -- random, unambiguous alphabet
  customer_name varchar(100)
  phone_last4   char(4)                    -- only the last 4 digits are stored for lookup
  device        varchar(100)
  status        enum('received','diagnosing','repairing','ready','collected')
  updated_at    timestamptz

Booking
  id            PK
  name          varchar(100)
  phone         varchar(20)
  device_model  varchar(100)
  issue         text
  date          date
  slot          time
  status        enum('pending','confirmed','declined','cancelled')
  created_at    timestamptz
  -- UNIQUE(date, slot) WHERE status IN ('pending','confirmed')

Testimonial
  id            PK
  customer_name varchar(100)
  quote         varchar(400)
  rating        smallint (1–5) NULL
  is_visible    boolean                    -- staff approve before it shows
  created_at    timestamptz

Subscriber
  id            PK
  email         varchar(254) UNIQUE
  confirmed     boolean default false
  created_at    timestamptz
  unsubscribed_at timestamptz NULL
```

## 9. Folder Structure

```
maiaiki_blog/
├── manage.py
├── requirements.txt
├── .env.example               # placeholder values only
├── config/                    # project settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py            # security flags, storage, email
│   ├── urls.py
│   └── wsgi.py
├── blog/                      # content app
│   ├── models.py              # Post, Category, Tag, PublishedManager
│   ├── views.py               # list, detail, category, tag, search
│   ├── admin.py
│   ├── images.py              # Pillow resize/convert helpers
│   └── sitemaps.py
├── shop/                      # customer-transaction app
│   ├── models.py              # QuoteRequest, RepairTicket, Booking, Testimonial, Subscriber
│   ├── forms.py               # includes honeypot field
│   ├── views.py               # quote, tracker, booking, newsletter
│   ├── emails.py              # send_quote_email, confirmation emails
│   └── admin.py               # actions: confirm booking, export CSV
├── templates/                 # base.html, partials/, blog/, shop/
├── static/                    # compiled CSS, small JS, favicon
├── tailwind/                  # tailwind.config.js and input.css
└── tests/
    ├── test_blog.py
    ├── test_quote.py
    ├── test_booking.py
    └── test_tracker.py
```

## 10. Risks & Mitigations

| Risk | Impact | Mitigation strategy |
|---|---|---|
| Uploaded images disappear after a redeploy because the host's disk is ephemeral | High | Configure R2/Cloudinary storage on Day 1 and test an upload on the throwaway deploy |
| Repair tickets or phone numbers are guessed or scraped | High | Random codes, ticket + last 4 digits, uniform error message, 10/hour rate limit, expose minimal fields |
| Quote or booking forms flooded with spam | Medium | Honeypot, IP rate limit, and Cloudflare Turnstile if needed |
| Two customers book the same slot | Medium | Partial unique constraint in Postgres plus a friendly error on `IntegrityError` |
| Week 2 features overrun their single day | Medium | Cut extras first (unsubscribe polish, email on status change) and keep the core flow; never move into the next day's work |
| Email lands in spam or the provider is down | Medium | Verified sender domain (SPF/DKIM), save the record before sending, and show all requests in the admin |
| SQLite and Postgres behave differently (search, constraints) | Medium | Run Postgres locally via Docker or use the managed dev database from Day 4 onward; CI runs against Postgres |
| Owner changes scope mid-build | Low | Freeze the page list on Day 1; log new ideas in a post-launch backlog |

## 11. Deployment Plan

### Development environment

```bash
# one-time setup
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install django django-environ django-ratelimit pillow psycopg[binary] \
            whitenoise gunicorn django-storages boto3 pytest pytest-django
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser

# every day
python manage.py runserver                             # Django on :8000
npx tailwindcss -i tailwind/input.css -o static/css/app.css --watch
pytest                                                 # run before each commit
```

### Production deployment

| Service | Platform | Notes |
|---|---|---|
| Web app | Render or Railway | Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput`; start: `gunicorn config.wsgi` |
| Database | Managed PostgreSQL | Enable daily backups; run `migrate` as a release command |
| Media | Cloudflare R2 or Cloudinary | Public read, write only from the app's credentials |
| Email | Brevo or Resend | Verify the sender domain (SPF and DKIM) before launch |
| Domain and TLS | Registrar DNS to the host | HTTPS is automatic; set `SECURE_SSL_REDIRECT=True` |
| CI | GitHub Actions | Run `pytest` and `python manage.py check --deploy` on every push |

### `.env` template

```
DJANGO_SETTINGS_MODULE=config.settings.prod
SECRET_KEY=change-me-long-random-string
DEBUG=False
ALLOWED_HOSTS=maiaiki.example,www.maiaiki.example
CSRF_TRUSTED_ORIGINS=https://maiaiki.example,https://www.maiaiki.example
DATABASE_URL=postgres://user:password@host:5432/dbname

# media storage
AWS_ACCESS_KEY_ID=placeholder
AWS_SECRET_ACCESS_KEY=placeholder
AWS_STORAGE_BUCKET_NAME=maiaiki-media
AWS_S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com

# email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=placeholder
EMAIL_HOST_PASSWORD=placeholder
DEFAULT_FROM_EMAIL=MAIAIKI TECHNOLOGIES <hello@maiaiki.example>
SHOP_NOTIFY_EMAIL=owner@maiaiki.example

# shop details
SHOP_WHATSAPP_NUMBER=2340000000000
ANALYTICS_DOMAIN=maiaiki.example
```

### Pre-launch checklist

- [ ] `python manage.py check --deploy` shows no warnings
- [ ] `DEBUG=False` and a unique `SECRET_KEY` in production
- [ ] Test upload, quote email, and newsletter confirmation on the live site
- [ ] Backup restore tested once
- [ ] Admin URL is behind a strong password (consider moving it off `/admin/`)
- [ ] Sitemap submitted to Google Search Console
