# गाँव की बगिया (Ganv Ki Bagiya)
### Complete Community Website & NGO Management System

[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-Proprietary-green?style=for-the-badge)]()

---

## 1. Project Overview

**गाँव की बगिया (Ganv Ki Bagiya)** is a digital management and public transparency platform for a village community initiative dedicated to transforming unused, barren land into a lush green garden and maintaining the village kabristan (cemetery) with dignity, boundary walls, water supply, and lighting.

The platform functions as a full-fledged NGO management system designed around **financial transparency, segregation of duties, and ease of use for rural communities**.

### Core Capabilities:
- **Donation Tracking:** Record cash, UPI, bank transfers, and online gateway payments with instant digital receipt generation.
- **Strict Financial Ledger:** Immutable double-entry-style ledger where:
  $$\text{Closing Balance} = \text{Opening Balance} + \text{Confirmed Income} - \text{Paid Expenses}$$
- **Public Financial Transparency Portal:** Real-time visibility into every rupee donated and spent, category charts, project summaries, and masked donor privacy.
- **Expense Approval Workflow:** Committee-driven multi-stage approval (Draft $\rightarrow$ Submitted $\rightarrow$ Approved by President $\rightarrow$ Payment recorded by Treasurer $\rightarrow$ Atomic Ledger update).
- **UPI QR & Bank Reconciliation:** Dynamic UPI QR generation with server-side UTR auto-matching against bank statement records.
- **Projects & Maintenance:** Tree plantation counts, watering schedules, boundary wall construction, and before/after comparisons.
- **Reporting Engine:** One-click exports in **CSV**, **Excel (.xlsx)**, and **PDF**.

---

## 2. Technology Stack

- **Backend:** Python 3.12+, Django 5.0+
- **Frontend / UI:** Django Template Language, Bootstrap 5.3, Bootstrap Icons, Chart.js
- **Database:** SQLite (default for development / single-node) & PostgreSQL (production ready)
- **Reporting:** `openpyxl` (Excel), `reportlab` (PDF), Python standard `csv`
- **QR Engine:** `qrcode` & `Pillow`
- **Payment Verification:** Razorpay HMAC-SHA256 authenticated webhooks & UPI UTR reconciliation

---

## 3. Project Architecture & Apps Structure

The repository follows a clean, modular Django architecture located under `apps/`:

```text
Bagiya/
├── apps/
│   ├── accounts/       # CustomUser, Roles (Admin, Treasurer, President, etc.), AuditLog
│   ├── donors/         # Donor directory, historical contributions, anonymous flags
│   ├── donations/      # Donation models, public forms, UPI QR, receipts
│   ├── payments/       # Gateway webhooks, HMAC verification, UPI UTR reconciliation
│   ├── finance/        # Fund accounts (Cash, Bank, Online), LedgerEntry, Daily snapshots, Transfers
│   ├── expenses/       # Expense tracking, approval stages, receipt uploads, payment records
│   ├── projects/       # Garden and Kabristan development projects, budget vs actuals
│   ├── maintenance/    # Recurring tasks, cleaning schedules, volunteer assignments
│   ├── gallery/        # Photo & video albums, before/after transformation comparisons
│   ├── content/        # Site settings, announcements, volunteer & contact forms, seed command
│   └── reports/        # CSV, Excel, and PDF financial statements & registers
├── config/             # Project settings, URL routing, WSGI, ASGI
├── static/             # Custom nature-themed CSS (style.css), JS (main.js)
├── templates/          # Responsive Bootstrap 5 templates (public & staff dashboard)
├── docs/               # Production deployment, backup & restore, checklist guides
├── scripts/            # Database backup automation scripts
├── requirements.txt    # Production dependencies
├── .env.example        # Environment variables template
└── manage.py
```

---

## 4. User Roles & Access Control

The platform enforces strict role-based access control (RBAC) and segregation of financial duties:

| Role | Permissions & Responsibilities |
|---|---|
| **Super Admin** | Full system configuration, user creation, settings, and database management. |
| **Treasurer (खजांची)** | Records manual donations, records actual expense payments, executes fund transfers, posts to ledger. *Cannot approve expenses.* |
| **Committee President (सदर/अध्यक्ष)** | Approves or rejects submitted expenses, reviews project financial summaries. *Cannot record payments.* |
| **Project Manager (कार्य प्रभारी)** | Submits expense proposals with bills, manages garden/kabristan tasks, updates progress. |
| **Volunteer (स्वयंसेवक)** | Views assigned maintenance tasks, submits ground completion notes. |
| **Public Visitor** | Views public website, donates online, views transparency ledger, submits volunteer form. |

---

## 5. Quick Start Guide (Local Setup)

### Prerequisites
- Python 3.10+ installed
- Git installed (optional)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
Copy `.env.example` to `.env` or run directly with default development settings:
```bash
cp .env.example .env
```

### Step 3: Run Database Migrations
```bash
python manage.py migrate
```

### Step 4: Seed Demo Data
Populate the database with pre-configured committee accounts, fund balances, active projects, sample donations, expenses, and ledger entries:
```bash
python manage.py seed_demo_data
```

### Step 5: Start Development Server
```bash
python manage.py runserver
```

Open your browser at **`http://127.0.0.1:8000/`**.

---

## 6. Pre-Configured Demo Credentials

Once `seed_demo_data` has run, you can log in at **`http://127.0.0.1:8000/accounts/login/`** using any of the following accounts:

| Role | Username | Password | Notes |
|---|---|---|---|
| **Super Admin** | `admin` | `Admin@123` | Full administrative control |
| **Treasurer** | `treasurer` | `Treasurer@123` | Haji Mushtaq (Manages ledger & payments) |
| **President** | `president` | `President@123` | Chaudhry Shamshad (Approves expenses) |
| **Project Manager** | `manager` | `Manager@123` | Imran Ahmad (Submits bills & tasks) |
| **Volunteer** | `volunteer1` | `Volunteer@123` | Danish Akhtar |

---

## 7. Running Automated Tests

Run the comprehensive test suite verifying accounting formulas, role permissions, webhooks, and reports:

```bash
python manage.py test
```

---

## 8. Documentation Links

- [Database Backup and Restoration Guide](docs/BACKUP_AND_RESTORE.md)
- [Production Readiness Checklist](docs/PRODUCTION_CHECKLIST.md)

---

## 9. License & Credits

Developed for the community initiative **गाँव की बगिया (Ganv Ki Bagiya)**. Designed for financial transparency, communal harmony, and environmental sustainability.
