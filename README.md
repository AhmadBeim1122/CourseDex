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

Visit:
- Public site → http://127.0.0.1:8000/
- Admin panel → http://127.0.0.1:8000/admin/

> **This zip already includes a demo `db.sqlite3`** with seeded sample
> data (2 programs, a few subjects/topics/past papers) and a demo admin
> account so you can explore immediately:
> - Username: `admin`
> - Password: `admin12345`
>
> **Change this password immediately** (`python manage.py changepassword admin`)
> or delete `db.sqlite3` and start fresh with `python manage.py migrate`.


This project ships with SQLite by default — **zero extra setup**. The
original project used MySQL; to switch back to MySQL, set in `.env`:

```
DB_ENGINE=mysql
DB_NAME=lms_db
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=127.0.0.1
DB_PORT=3306
```

then `pip install mysqlclient` and re-run `python manage.py migrate`.

## 3. Using the Admin Panel

Log into `/admin/` with the superuser you created. You'll see, in order:

1. **Programs** — add "BSIT", "BSCS", etc. Set `total_semesters` (e.g. 8) —
   saving a Program **automatically creates all its Semester rows** for you.
2. **Semesters** — open one from the Program page (inline) or its own list;
   add Subjects to it directly from the Semester edit screen (inline).
3. **Subjects** — add topics and past papers directly from the Subject edit
   screen using the inline tables at the bottom (no need to jump between
   screens for routine data entry).
4. **Topics** — the "Study content" tab holds the notes text; "Media &
   resources" holds the YouTube link and a Google Drive document link.
   Add up to 6 images per topic using the inline image table at the bottom
   of the topic form — each image can either be **uploaded** or given a
   **Drive share link** (leave the file blank and fill the Drive link
   instead).
5. **Past Papers** — pick the Subject, Year, and Exam Type, paste the
   Google Drive link to the scanned question paper, then choose a
   Solution Type:
   - *No solution yet* — only the question paper link shows on the site.
   - *Written solution (text)* — type the solution in the text box.
   - *Solution image(s) / Drive link* — upload one image and/or paste a
     Drive folder link with the full solution.

   Only years that have at least one **published** past paper will appear
   on the public "Past Papers" year picker for that subject — exactly the
   "jitne bhi admin se add ho wo show hote jae" behavior you asked for.

6. **Site Settings** (singleton) — edit the About page text, contact email/
   phone, and social links shown in the footer, without editing code.
7. **Contact Messages** — read-only inbox of messages submitted through the
   public Contact page.

Every content model has an `is_published` checkbox — uncheck it to hide a
Program/Semester/Subject/Topic/Past Paper from the public site without
deleting it.

## 4. Frontend routes (all public, no login)

```
/                                                          Home
/courses/                                                  Programs
/courses/<program>/                                        Semesters
/courses/<program>/<semester>/                              Subjects
/courses/<program>/<semester>/<subject>/                    Topic outline
/courses/<program>/<semester>/<subject>/<topic>/             Topic detail

/past-papers/                                               Programs
/past-papers/<program>/                                      Semesters
/past-papers/<program>/<semester>/                            Subjects
/past-papers/<program>/<semester>/<subject>/                  Years available
/past-papers/<program>/<semester>/<subject>/<year>/            Papers + solutions

/about/  /contact/  /privacy-policy/  /terms-of-service/  /disclaimer/
/sitemap.xml  /robots.txt  /ads.txt
```

## 5. Google AdSense

1. Apply for AdSense once the site has enough real content (a handful of
   full programs/subjects/topics, plus the legal pages already included).
2. In `.env`, set `ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX` — this
   automatically:
   - loads the AdSense script in every page's `<head>`,
   - serves a correct `/ads.txt`,
   - activates the ad slots already placed on topic pages and past-paper
     pages (`<ins class="adsbygoogle">` in the templates).
3. (Optional) set `GOOGLE_SITE_VERIFICATION` and `GOOGLE_ANALYTICS_ID`.

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

- Student/Admin login & registration (`loginorsignup.php`, `studentRegistration.php`)
- Shopping cart / checkout / Paytm payment integration (`checkout.php`,
  `PaytmKit/`, `paymentstatus.php`)
- The flat "buy a video course" model — replaced entirely by the
  Program → Semester → Subject → Topic structure you described.

## 8. Security notes

- `DEBUG=False` in production automatically turns on HSTS, secure cookies,
  and `X-Frame-Options: DENY` (see bottom of `config/settings.py`).
- CSRF protection is on for the contact form (Django's default).
- The admin panel is the *only* authenticated area — keep the superuser
  password strong and consider putting `/admin/` behind an extra layer
  (VPN, IP allowlist, or a renamed admin URL) for extra safety.


ab past paper waly sy kuch kuch changes krni ha sb se phle yeh ke question paper ki picture drive pr ha to kya iss tarah kr skte jo picture drive wo get krke 