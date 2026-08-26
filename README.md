<<<<<<< HEAD
# iSchool LMS — Django Edition

A from-scratch **Django** rebuild of the original PHP/MySQL "iSchool" project.

The original PHP app was a paid-course marketplace (login/signup, cart, Paytm
payment gateway). This rebuild keeps the *learning management* idea but
reshapes it into what you actually asked for:

- **No accounts. No login/signup for visitors. No payment gateway.**
- Two sides only: an **Admin** (Django Admin, Jazzmin-themed) who manages
  content, and **public visitors** who browse it for free.
- Content is organized the way a real degree is structured:

  ```
  Program (BSIT, BSCS, ...)
    └── Semester (1..8)
          └── Subject (e.g. "Programming Fundamentals")
                ├── Topic 1..30  (text notes, 2-6 images, YouTube link, Drive doc link)
                ├── Topic 2
                └── ...
                └── Past Papers (by year, e.g. 2019-2025 — only years the admin adds)
                      question paper = Drive link
                      solution = text OR image/Drive link
  ```
- Frontend: server-rendered HTML + CSS + **HTMX** (search-as-you-type,
  the contact form) with only a few lines of vanilla JS for the mobile menu.
- Pages an AdSense review expects are already there: Home, Courses,
  Past Papers, About, Contact, Privacy Policy, Terms of Service, Disclaimer,
  `sitemap.xml`, `robots.txt`, `ads.txt`.

---

## 1. Project layout

```
lms/
├── config/                 # Django project (settings, urls, wsgi/asgi)
├── apps/
│   ├── core/                # Home/About/Contact/Legal pages, site settings, robots/ads.txt
│   └── academics/            # Program/Semester/Subject/Topic/PastPaper models, views, admin
├── templates/                # All HTML templates (base + per-app + HTMX partials)
├── static/                   # style.css, main.js, favicon
├── media/                    # Uploaded images (created at runtime)
├── requirements.txt
├── .env.example               # Copy to .env and fill in
└── manage.py
```

## 2. Quick start (local development)

```bash
# 1. Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# open .env and set DJANGO_SECRET_KEY to something random

# 4. Create the database tables
python manage.py migrate

# 5. Create an admin account
python manage.py createsuperuser

# 6. (Optional) Load a small demo dataset so you can see the site working
python manage.py seed_demo_data

# 7. Run the dev server
python manage.py runserver
```



## 6. Deploying to production

```bash
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

```bash
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Static files are served via **WhiteNoise** (already wired in
`MIDDLEWARE`/`STORAGES`), so you don't need a separate static file server
for small/medium traffic. Put Nginx/Caddy in front of Gunicorn for TLS.

For uploaded media (topic images, solution images) at scale, point
`DEFAULT_FILE_STORAGE` at S3/Cloudinary/etc. — the code doesn't assume
local disk beyond Django's defaults, so this is a drop-in change in
`settings.py` if you outgrow local storage.

## 7. What was intentionally removed from the original PHP project

- Student/Admin login & registration 
## 8. Security notes

- `DEBUG=False` in production automatically turns on HSTS, secure cookies,
  and `X-Frame-Options: DENY` 

ab past paper waly sy kuch kuch changes krni ha sb se phle yeh ke question paper ki picture drive pr ha to kya iss tarah kr skte jo picture drive wo get krke 
=======
# CourseDex
