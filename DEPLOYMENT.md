# Deployment guide for Maiaiki Blog

This project is ready for a Django deployment on a managed host such as Render or Railway.

## 1. Production environment variables

Set these in your host dashboard or `.env` file before deployment:

```env
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
ALLOWED_HOSTS=maiaiki.example.com,www.maiaiki.example.com
SITE_URL=https://maiaiki.example.com
DATABASE_URL=postgres://user:password@host:5432/maiaiki
ADMIN_EMAIL=hello@maiaiki.com
DEFAULT_FROM_EMAIL=noreply@maiaiki.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CSRF_TRUSTED_ORIGINS=https://maiaiki.example.com,https://www.maiaiki.example.com
```

Notes:
- Keep `DEBUG=False` in production.
- Use the domain(s) that your host serves, not just `localhost`.
- For `CSRF_TRUSTED_ORIGINS`, include the full HTTPS origin(s) used by Django.

## 2. Hosting setup

### Render
1. Create a new Web Service from this repository.
2. Set the runtime to Python 3.12.
3. Use the existing `Procfile`.
4. Add the environment variables listed above.
5. Add a Postgres database and copy the `DATABASE_URL` into the app environment.
6. Deploy the service.

### Railway
1. Create a new project and attach the GitHub repo.
2. Add a PostgreSQL service.
3. Add the environment variables listed above.
4. Ensure the web service uses the Python runtime and starts with the included `Procfile`.
5. Deploy and watch the logs.

## 3. Static files and media

Static files are served via WhiteNoise and should work on managed hosts with the current configuration.

For uploaded files:
- use Cloudflare R2 or Cloudinary
- add the storage credentials as environment variables if you later add cloud object storage
- do not rely on the local filesystem for uploaded media in production

## 4. Deploy checks

Before launch, run:

```bash
python manage.py test
python manage.py check --deploy
```

These should pass before the site is published to production.

## 5. Launch checklist

- [ ] production `SECRET_KEY` set
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` includes the live domain
- [ ] Postgres database attached
- [ ] `SITE_URL` and `CSRF_TRUSTED_ORIGINS` point to the live HTTPS origin
- [ ] secure cookies and HSTS enabled
- [ ] static files served successfully
- [ ] homepage loads over HTTPS
- [ ] quote form submits and saves to the database
- [ ] admin can log in and publish posts

## 6. Recommended next phase

After the live deployment is stable, move to the content-discovery work from the plan:
- search
- tag pages
- publishing schedule (`publish_at`)
- image pipeline optimization
- newsletter and repair tracker
