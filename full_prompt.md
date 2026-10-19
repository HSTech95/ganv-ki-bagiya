<USER_REQUEST>
# Project Prompt: Ganv Ki Bagiya — Complete Django Website & NGO Management System

## 1. Project Overview

Build a complete, production-ready website for **Ganv Ki Bagiya**, a village community initiative dedicated to transforming unused land into a beautiful garden and a properly maintained kabristan (cemetery).

The initiative receives donations from villagers and supporters. We need a digital system to manage:

- Who donated, how much, and when.
- Why the donation was made.
- Where the money was spent.
- Daily income, expenses, opening balance, and closing balance.
- Online donations using UPI QR codes
- Garden and kabristan development projects.
- Photos, videos, announcements, and community activities.
- Public financial transparency and downloadable reports.

The objective is to build a trustworthy community website that works like a small NGO management system.

## 2. Technology Stack

Use the following technologies only:

- **Backend:** Python and Django.
- **UI:** Django Templates with Django Template Language.
- **Frontend:** HTML5, CSS3, Bootstrap 5, and vanilla JavaScript.
- **Database:** SQLITE.
- **Icons:** Bootstrap Icons or Lucide icons.
- **Charts:** Chart.js.
- **Forms:** Django Forms and ModelForms.
- **Authentication:** Django's built-in authentication system.
- **Payments:** UPI QR code and Razorpay integration, where eligible.
- **Media:** Django media storage for photos, bills, receipts, and documents.
- **Reports:** CSV, Excel, and PDF exports.
- **Deployment:** Gunicorn, Nginx, HTTPS, environment variables, and automated database backups.

Do not use React, Next.js, Vue, Angular, or a separate frontend application.

Render all pages on the server using Django templates. Use AJAX or Fetch API only where dynamic interaction improves usability.

## 3. UI and Design Requirements

Create a modern, clean, professional, nature-inspired interface.

Design style:
- Primary color: natural green.
- Secondary colors: white, light green, and earthy neutral tones.
- Responsive Bootstrap 5 grid system.
- Mobile-first design.
- Reusable Django base templates and partials.
- Clean typography and accessible color contrast.
- Attractive cards, tables, charts, forms, and modal dialogs.
- Simple navigation for village residents of different age groups.
- Indian currency formatting, such as ₹1,50,000.
- Hindi and English language support, preferably using Django internationalization.
- Clear success, error, validation, and empty-state messages.

Create separate layouts for the public website and the administration dashboard.

Use Bootstrap components consistently. Avoid unnecessary animations and excessive visual effects.

## 4. Public Website Pages

### A. Home Page

Create a homepage containing:

- Hero section introducing Ganv Ki Bagiya.
- Mission and purpose.
- Donate Now button.
- View Financial Reports button.
- Total confirmed donations.
- Total expenses.
- Current reported balance.
- Number of contributors.
- Garden and kabristan development projects.
- Before-and-after photographs.
- Recent development activities.
- Gallery preview.
- Latest announcements.
- Volunteer registration.
- Contact information and footer.

All financial statistics must come from the database, never hardcoded values.

### B. About Us

Include:
- Background and mission.
- Garden development goals.
- Kabristan maintenance goals.
- Committee details.
- Community participation.
- Future plans.

Make content editable from the admin dashboard.

### C. Donation Page

Build a complete donation workflow.

Donation form fields:
- Donor name.
- Mobile number.
- Email address (optional).
- Donation amount.
- Donation purpose.
- Payment method.
- Optional message.
- Anonymous donation checkbox.

Donation purposes:
- General Fund.
- Garden Development.
- Tree Plantation.
- Garden Maintenance.
- Kabristan Maintenance.
- Boundary Wall and Construction.
- Water and Electricity.
- Other Approved Projects.

Features:
- Suggested donation amounts.
- Custom donation amount.
- UPI QR code.
- Online payment gateway.
- Payment status.
- Transaction reference.
- Digital receipt.
- Thank-you page.

Verify gateway payments server-side using authenticated webhooks or the payment provider's verification API.

Never treat a browser redirect, uploaded screenshot, or user-submitted payment reference as sufficient proof of payment.

For static UPI QR payments, provide a reconciliation workflow before confirming the donation.

### D. Financial Transparency Page

Display:
- Opening balance.
- Total confirmed income.
- Total expenses paid.
- Current reported balance.
- Last reconciliation date.
- Monthly income and expense chart.
- Category-wise expense chart.
- Project-wise financial summary.
- Recent public financial activity.
- Monthly and annual downloadable reports.

Add filters for:
- Date range.
- Financial year.
- Project.
- Expense category.

Never expose private donor details, personal mobile numbers, bank information, or payment credentials.

### E. Projects Page

Display:
- Garden development.
- Tree plantation.
- Garden maintenance.
- Kabristan cleaning.
- Boundary wall construction.
- Water supply and drainage.
- Lighting and pathways.
- Other community projects.

Each project should show:
- Project name and description.
- Objectives.
- Budget.
- Actual expenditure.
- Remaining budget.
- Start and expected completion dates.
- Status.
- Progress percentage.
- Photos and progress updates.
- Public financial summary.

Track restricted donations separately and respect their stated purpose.

### F. Gallery

Create:
- Photo gallery.
- Video gallery.
- Event albums.
- Project albums.
- Before-and-after comparisons.
- Captions and dates.
- Image lightbox.
- Category filters.

Allow administrators to upload, edit, publish, and remove media according to permissions.

### G. Contact Page

Include:
- Contact number.
- Email address.
- Village address.
- Map link.
- Committee information.
- Contact form.
- Volunteer registration.
- Suggestions and complaints form.

All contact details should be editable through the admin panel.

## 5. Django Admin Management Dashboard

Build a dedicated staff dashboard using Django templates and Bootstrap 5.

The dashboard should contain:

### Summary cards
- Total confirmed donations.
- Total expenses paid.
- Current book balance.
- Cash balance.
- Bank balance.
- Pending payments.
- Pending expense approvals.
- Number of donors.
- Active projects.

### Charts
- Monthly income versus expenses.
- Daily donation collection.
- Expense category breakdown.
- Project-wise spending.

### Recent activity
- Latest donations.
- Recent expenses.
- Pending approvals.
- Recent project updates.
- Upcoming maintenance tasks.

Use Django ORM aggregation and optimized queries. Avoid calculating totals repeatedly in templates or creating N+1 database queries.

Implement separate dashboard views for authorized staff and public visitors.

## 6. Donation Management

Create Django models and CRUD views for donors and donations.

Each donation must include:
- Unique donation ID.
- Receipt number.
- Donor reference.
- Donation date.
- Amount using DecimalField.
- Donation purpose.
- Payment method.
- Payment transaction reference.
- Payment status.
- Verification status.
- Recorded-by user for manual entries.
- Notes and supporting evidence.
- Creation and update timestamps.

Support:
- Cash donations.
- Bank transfers.
- UPI donations.
- Verified online payments.
- Anonymous donations.

Provide:
- Add, edit, search, and filter donations.
- Donor history.
- Date-range reports.
- Digital receipt generation.
- Donation purpose filters.
- CSV and Excel exports.
- Duplicate payment prevention.

Only confirmed and properly posted donations should affect the financial ledger.

## 7. Expense Management

Create an expense management module with the following fields:

- Expense ID.
- Expense date.
- Description.
- Category.
- Amount.
- Vendor or recipient.
- Payment method.
- Fund account.
- Related project.
- Bill or receipt upload.
- Recorded-by user.
- Approval status.
- Approver details.
- Payment status.
- Notes.

Expense categories:
- Garden maintenance.
- Tree plantation.
- Water and electricity.
- Labour charges.
- Construction and repairs.
- Boundary wall and gate.
- Kabristan maintenance.
- Tools and equipment.
- Community events.
- Administrative expenses.
- Miscellaneous expenses.

Features:
- Create and edit draft expenses.
- Submit for approval.
- Approve or reject expenses.
- Record actual payments.
- Upload supporting bills.
- Search and filter expenses.
- Export reports.
- Maintain a permanent audit history.

An approved expense is not necessarily a paid expense. Reduce the available balance only when the payment is actually recorded.

Never silently delete posted transactions. Use authorized reversal or adjustment entries to correct errors.

## 8. Financial Accounting and Ledger

This is the most critical part of the application.

Build a date-wise financial ledger using Django models and database transactions.

Formula:

Closing balance = Opening balance + Confirmed income − Paid expenses, with appropriate treatment for refunds, account transfers, and adjustments.

Requirements:
- Daily opening and closing balances.
- Daily, weekly, monthly, yearly, and custom-date reports.
- Separate cash, bank, and payment accounts.
- Complete transaction history.
- Account transfers without double-counting income or expenses.
- Duplicate posting prevention.
- Reversal and adjustment entries.
- Bank and UPI reconciliation.
- Financial discrepancy alerts.
- Downloadable reports.
- Audit logs for important actions.

Use `DecimalField` for all monetary amounts.

Use database transactions and appropriate row locking or other concurrency controls to prevent incorrect balances during simultaneous transactions.

Posted ledger entries must be immutable. Do not allow direct editing or deletion of posted financial entries.

The ledger must be the source of truth for financial reports.

Distinguish the calculated book balance from the reconciled actual cash or bank balance.

## 9. Expense Approval Workflow

Implement the following workflow:

1. A committee member creates an expense.
2. The supporting bill is uploaded.
3. The expense is submitted.
4. An authorized person reviews it.
5. The expense is approved or rejected.
6. The actual payment is recorded.
7. The ledger and account balance update atomically.
8. The public report updates according to the disclosure policy.

Allow configurable approval thresholds.

Where required, prevent users from approving their own expenses.

Record the approver, approval timestamp, decision, and reason.

## 10. User Roles and Permissions

Implement role-based access control.

### Super Admin
- Full system configuration.
- User and role management.
- All financial and project records.
- System settings.

### Treasurer
- Donations.
- Expenses.
- Ledger.
- Reconciliation.
- Financial reports.

### Committee President
- Financial oversight.
- Expense approvals.
- Reports and project reviews.

### Project Manager
- Assigned projects.
- Maintenance tasks.
- Project budgets and updates.
- Photos and activity records.

### Volunteer
- Assigned tasks.
- Permitted project updates.

### Public Visitor
- View published website content.
- Donate online.
- View public financial reports.
- Submit volunteer and contact forms.

Enforce permissions in Django views, forms, querysets, and APIs if any are added. Hiding buttons in templates is not sufficient security.

Use Django Groups and Permissions or a well-defined custom role model.

## 11. Garden and Kabristan Management

Create a project and maintenance management module.

Garden features:
- Tree plantation records.
- Watering schedules.
- Cleaning schedules.
- Garden maintenance tasks.
- Plants, tools, and material records.
- Assigned volunteers.
- Before-and-after photographs.

Kabristan features:
- Cleaning and maintenance schedules.
- Boundary wall and gate work.
- Water and lighting maintenance.
- Pathway and drainage projects.
- Repair records.
- Assigned volunteers.

Allow recurring maintenance tasks, due dates, reminders, completion notes, and photos.

Keep garden and kabristan expenses separate, with a shared general fund.

## 12. Gallery and Content Management

Create Django models for:
- Gallery albums.
- Gallery items.
- Announcements.
- Project updates.
- Public website content.
- Contact submissions.

Provide dashboard forms for uploading images, adding captions, assigning categories, and publishing updates.

Validate file types and file sizes. Protect uploaded files and avoid accepting executable content.

## 13. Suggested Django Project Structure

Organize the project into reusable Django apps.

Example structure:

```text
ganv_ki_bagiya/
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/
│   ├── donors/
│   ├── donations/
│   ├── payments/
│   ├── finance/
│   ├── expenses/
│   ├── projects/
│   ├── maintenance/
│   ├── gallery/
│   ├── content/
│   └── reports/
├── templates/
│   ├── base.html
│   ├── public/
│   ├── dashboard/
│   ├── donations/
│   ├── expenses/
│   ├── finance/
│   ├── projects/
│   ├── gallery/
│   └── includes/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── media/
├── requirements.txt
├── .env.example
└── README.md
```

Adjust the structure when necessary, but keep apps modular and avoid placing all business logic in a single Django app or view.

Use Django templates with reusable components such as:
- Base templates.
- Navbar and sidebar.
- Footer.
- Dashboard cards.
- Pagination.
- Forms.
- Tables.
- Confirmation modals.
- Messages and alerts.

## 14. Database Models

Design normalized models for:

- User and Role.
- Donor.
- Donation.
- PaymentTransaction.
- FundAccount.
- LedgerEntry.
- Expense.
- ExpenseAttachment.
- ExpenseApproval.
- Project.
- ProjectBudget.
- MaintenanceTask.
- VolunteerAssignment.
- DonationReceipt.
- GalleryAlbum.
- GalleryItem.
- Announcement.
- ContactSubmission.
- BankReconciliation.
- AuditLog.

Use appropriate foreign keys, constraints, indexes, timestamps, unique transaction references, and database migrations.

## 15. Reports and Exports

Implement:
- Daily collection report.
- Daily expenditure report.
- Daily opening and closing balance.
- Monthly financial summary.
- Annual financial statement.
- Donor contribution history.
- Expense category report.
- Project-wise financial statement.
- Cash and bank account statement.
- Pending approval report.
- Bank reconciliation report.

Support CSV and Excel exports. Generate PDF reports with a professional layout and the Ganv Ki Bagiya name.

Use the same accounting logic for dashboard figures and exported reports.

## 16. Security Requirements

Implement:
- Django authentication.
- Strong password policies.
- Secure session configuration.
- CSRF protection.
- HTTPS in production.
- Server-side form validation.
- Login rate limiting.
- Secure media uploads.
- Environment-based secrets.
- Role-based access.
- Audit logging.
- Database backups.
- Protection against SQL injection and XSS.
- Verified payment webhooks.
- Idempotent payment processing.
- Privacy-conscious data retention.

Never put gateway secrets in templates or JavaScript.

## 17. Testing Requirements

Write automated Django tests for:
- Donation creation and confirmation.
- Duplicate payment webhooks.
- Failed and refunded payments.
- Expense approval.
- Paid versus unpaid expenses.
- Daily balance calculations.
- Account transfers.
- Ledger reversals.
- Date-range reports.
- Role-based access.
- Anonymous donations.
- Public data privacy.
- Concurrent financial transactions.
- Invalid payment references.

Use demo data for development only and clearly identify it as test data.

## 18. Development Workflow

Implement the project incrementally.

Phase 1: Project setup, authentication, base templates, public website, and dashboard layout.

Phase 2: Donor management, donation entry, expense management, and receipt generation.

Phase 3: Financial ledger, automatic balance calculations, approval workflows, and reports.

Phase 4: UPI QR donations, online payment integration, and reconciliation.

Phase 5: Projects, gallery, maintenance schedules, volunteers, and announcements.

Phase 6: Testing, security review, performance optimization, deployment, and backups.

After every phase:
- Run migrations.
- Run automated tests.
- Check permissions.
- Verify financial calculations.
- Test responsive layouts.
- Fix errors before moving forward.

## 19. Final Deliverables

Produce:
1. Complete Django application.
2. Complete Bootstrap 5 Django template UI.
3. PostgreSQL models and migrations.
4. Public website.
5. Admin dashboard.
6. Donation and expense management.
7. Financial ledger and reporting.
8. Payment gateway integration.
9. UPI QR donation workflow.
10. Gallery and project management.
11. Automated tests.
12. Environment configuration example.
13. Setup and deployment instructions.
14. Database backup and restoration instructions.
15. Production-readiness checklist.

## Final Instruction

Build a functional, secure, maintainable Django application using Django Templates and Bootstrap 5.

Do not use React or any separate frontend framework.

Do not hardcode financial totals or create nonfunctional placeholder buttons for core features.

Prioritize financial correctness, transparency, data integrity, security, and usability.

Start by inspecting the existing repository. Then create the implementation plan, database models, base templates, URL structure, and authentication. Build the application module by module and test every critical feature.

The final website must make it easy for the Ganv Ki Bagiya committee to record every donation, track every expense, calculate daily balances, manage garden and kabristan projects, and demonstrate responsible use of community contributions.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-10-09T16:08:12+05:30.

The user's current state is as follows:
Active Document: /Untitled-1 (LANGUAGE_UNSPECIFIED)
Cursor is on line: 1
</ADDITIONAL_METADATA>
<USER_SETTINGS_CHANGE>
The user changed setting `Model Selection` from None to Gemini 3.8 Flash (High). No need to comment on this change if the user doesn't ask about it. If reporting what model you are, please use a human readable name instead of the exact string.
</USER_SETTINGS_CHANGE>