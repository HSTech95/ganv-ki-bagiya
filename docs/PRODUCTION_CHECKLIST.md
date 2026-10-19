# Ganv Ki Bagiya — Production-Readiness Checklist

Use this checklist before taking the application live on a production server.

---

## 1. Security & Django Settings

- [ ] **Secret Key:** Set a unique, cryptographically random `DJANGO_SECRET_KEY` in `.env` (min 50 chars). Never commit it to git.
- [ ] **Debug Mode:** Confirm `DJANGO_DEBUG=False` in `.env`.
- [ ] **Allowed Hosts:** Set `ALLOWED_HOSTS=bagiya.org,www.bagiya.org,127.0.0.1` in `.env`.
- [ ] **HTTPS & SSL:**
  - [ ] SSL certificate installed (e.g. Let's Encrypt / Certbot).
  - [ ] `SECURE_SSL_REDIRECT=True`
  - [ ] `SESSION_COOKIE_SECURE=True`
  - [ ] `CSRF_COOKIE_SECURE=True`
  - [ ] `SECURE_HSTS_SECONDS=31536000`
- [ ] **Admin URL:** Consider changing `/django-admin/` or disabling default django-admin for non-superuser IPs.
- [ ] **Default Passwords:** Change default demo passwords immediately (`admin`, `treasurer`, `president`, `manager`, `volunteer1`).

---

## 2. Database & Data Protection

- [ ] **Database Connection:** Configure PostgreSQL via `DATABASE_URL` for multi-worker concurrency.
- [ ] **Migrations:** All migrations applied (`python manage.py migrate`).
- [ ] **Automated Backups:** `scripts/backup_db.py` configured via Cron/Task Scheduler daily.
- [ ] **Media Storage:** Regular offsite synchronization for `media/bills/`, `media/receipts/`, and `media/donation_proofs/`.

---

## 3. Payments & Reconciliations

- [ ] **Razorpay Live Keys:** Set live `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
- [ ] **Webhook Endpoint:** Configure `https://bagiya.org/payments/webhook/razorpay/` in Razorpay Dashboard.
- [ ] **Webhook Secret:** Set `RAZORPAY_WEBHOOK_SECRET` matching Razorpay dashboard.
- [ ] **UPI ID:** Set official committee UPI ID and Merchant Name in Site Settings (`/dashboard/settings/`).

---

## 4. Web Server & Reverse Proxy (Nginx + Gunicorn)

- [ ] **Gunicorn Service:** Set up systemd service with 3–4 workers (`gunicorn config.wsgi:application -w 3 -b 127.0.0.1:8000`).
- [ ] **Nginx Reverse Proxy:** Reverse proxy requests to Gunicorn.
- [ ] **Static Assets:** Collect static files (`python manage.py collectstatic --noinput`) and serve directly from Nginx.
- [ ] **Media Assets:** Nginx configured to serve `/media/` with upload size limit matching Django (`client_max_body_size 10M;`).

### Sample Nginx Configuration Snippet:
```nginx
server {
    server_name bagiya.org www.bagiya.org;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/bagiya/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /var/www/bagiya/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl;
    # SSL cert directives...
}
```

---

## 5. Automated Verification Test
Run automated suite to guarantee zero regression:
```bash
python manage.py test
```
All tests must pass with `OK`.
