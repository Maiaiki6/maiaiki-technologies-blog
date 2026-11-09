# Maiaiki Technologies Blog: 14-Day Plan

A web app blog for the phone repair shop MAIAIKI TECHNOLOGIES. Solo developer, two-week deadline.

Two weeks fits the full plan: the core blog goes live on Day 7, and every feature that was cut from the one-week version ships to the live site in Week 2.

## Scope

Everything from the wish list is in. Week 1 ships the launch version; Week 2 adds the features that were cut from the one-week plan, straight to the live site.

**Launch version (Week 1)**

- Blog list and post pages, with categories
- Admin panel for writing and publishing posts
- Services page, contact info, and a quote request form
- Click-to-call and WhatsApp buttons
- Mobile-friendly design, basic SEO, security hardening, and deployment

**After launch (Week 2)**

- Search, tags, and post scheduling
- Image resizing
- Newsletter signup
- Repair status tracker
- Online booking and a testimonials section
- Analytics and the full test suite

## Week 1: Build and Launch

### Day 1: Setup & Design

- [ ] Create the Django project, repo, and virtual environment
- [ ] Define the models: Post, Category, QuoteRequest
- [ ] Pick the branding: logo text "MAIAIKI TECHNOLOGIES", colors, and fonts
- [ ] Sketch the pages quickly (Home, Blog, Post, Services, Contact)
- [ ] Set up Tailwind and a `base.html` with the header and footer
- [ ] Do a throwaway deploy of the empty project so hosting problems show up early

### Day 2: Blog Core

- [ ] Run migrations and customize the admin (title, slug, body, image, category, published flag)
- [ ] Build the blog list view with pagination
- [ ] Build the post detail page with clean slug URLs

### Day 3: Blog Frontend

- [ ] Style the list and post pages with Tailwind
- [ ] Add category filtering
- [ ] Build the homepage with a hero section and a latest-posts block
- [ ] Write 3 starter posts (e.g., "5 signs your phone battery needs replacing", "What to do if your phone gets wet", "Cracked screen: repair or replace?")

### Day 4: Shop Features

- [ ] Build the Services and Pricing page
- [ ] Build the quote request form (name, phone, device model, issue) and save it to the database
- [ ] Add email notification to the shop, or view requests in the admin
- [ ] Add the call and WhatsApp buttons and a map embed with opening hours

### Day 5: Mobile, SEO Basics & Security

- [ ] Test every page on a real phone and fix layout issues
- [ ] Add page titles, meta descriptions, a sitemap, and robots.txt
- [ ] Add a honeypot to the quote form to block spam
- [ ] Set `DEBUG=False`, move secrets to environment variables, and set `ALLOWED_HOSTS`

### Day 6: Deploy

- [ ] Deploy to Render, Railway, or a VPS with PostgreSQL
- [ ] Connect the domain and enable HTTPS
- [ ] Set up static and media file handling and database backups
- [ ] Do a full test pass on the live site

### Day 7: Launch & Buffer

- [ ] Fix bugs found in the live test
- [ ] Publish the starter posts
- [ ] Write a short guide on how to publish a post from the admin
- [ ] Submit the sitemap to Google Search Console

Day 7 is deliberately a buffer. Deployments almost always hit a surprise, so protect it. The site is live at the end of this day.

## Week 2: Post-Launch Features

### Day 8: Search & Tags

- [ ] Add a Tag model and tag pages
- [ ] Add a search box using Django's built-in text search (or PostgreSQL full-text search)
- [ ] Show tags and search results in the same card layout as the blog list

### Day 9: Scheduling & Image Resizing

- [ ] Add a `publish_at` field so posts can be scheduled, and a small scheduled task that publishes them
- [ ] Resize and compress uploaded images automatically with Pillow (thumbnail, card, and full sizes)
- [ ] Re-process the images on the existing starter posts

### Day 10: Newsletter Signup

- [ ] Build a signup form (email only) with a honeypot and rate limiting
- [ ] Save subscribers to the database and add a CSV export in the admin
- [ ] Add confirmation emails and an unsubscribe link

### Day 11: Repair Status Tracker

- [ ] Add a RepairTicket model (ticket number, device, status, last updated)
- [ ] Let the shop update status from the admin (Received, Diagnosing, Repairing, Ready for pickup)
- [ ] Build a lookup page where a customer enters a ticket number and phone number
- [ ] Rate-limit the lookup so ticket numbers can't be guessed

### Day 12: Booking & Testimonials

- [ ] Build a booking request form with date and time slot choice
- [ ] Block slots that are already taken, and let the shop confirm or decline in the admin
- [ ] Add a Testimonial model and a testimonials section on the homepage

### Day 13: Analytics & Test Suite

- [ ] Add analytics (Google Analytics or a privacy-friendly alternative)
- [ ] Write tests for models, views, the quote form, booking, and the status tracker
- [ ] Run a security check on the new forms (CSRF, input validation, rate limits)

### Day 14: Final QA & Handover

- [ ] Test every feature again on real phones, on the live site
- [ ] Fix remaining bugs and tidy the admin labels
- [ ] Update the admin guide to cover tags, scheduling, tickets, bookings, and testimonials
- [ ] Hand over the logins and walk through the admin

## Milestones

| Milestone | Target |
| --- | --- |
| Project skeleton and models done | End of Day 1 |
| Blog working end to end | End of Day 3 |
| Quote form and contact features done | End of Day 4 |
| Live on a public URL | End of Day 6 |
| Launch complete | End of Day 7 |
| Search, tags, scheduling, and image resizing live | End of Day 9 |
| Newsletter and repair tracker live | End of Day 11 |
| Booking, testimonials, analytics, and tests done | End of Day 13 |
| Handover complete | Day 14 |

## Risks & Mitigations

- **Deployment problems eat your time.** The throwaway deploy on Day 1 shows config issues early.
- **Week 2 features stack up.** Each feature is one day. If one runs over, cut its extras (for example, skip unsubscribe analytics) rather than pushing the next day.
- **The status tracker leaks customer info.** Require both the ticket number and the phone number, and rate-limit lookups.
- **Booking creates double bookings.** Check slot availability on the server when the form is submitted, not only in the page.
- **Design takes too long.** Use a Tailwind template or component set instead of designing from scratch.
- **No content for launch.** Write the three starter posts on Day 3, and don't wait on anyone else.

## Tech Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Backend | Django (Python) | Built-in admin panel gives a post editor for free, plus auth and security defaults |
| Database | SQLite for dev, PostgreSQL for production | Simple to start, reliable to deploy |
| Frontend | Django templates + Tailwind CSS | Server-rendered pages are fast and SEO-friendly |
| Hosting | Render or Railway | Low cost, easy deploys |
| Testing | pytest + pytest-django | Standard and quick to set up |

## Suggested File Structure

```
repair_blog/
├── manage.py
├── config/          # settings, urls, wsgi
├── blog/            # models, views, admin, templates
├── shop/            # services, quote requests
├── templates/       # base.html, shared partials
├── static/          # css, js, images
├── tests/
└── requirements.txt
```
