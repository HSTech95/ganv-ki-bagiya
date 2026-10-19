import csv
import io
import os
from datetime import date
from decimal import Decimal
from django.conf import settings as django_settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db import models

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_devanagari_fonts():
    """
    Registers Unicode Devanagari fonts with ReportLab so Hindi and English
    render cleanly without turning into black boxes (tofu / ■■■■).
    """
    if "Devanagari" not in pdfmetrics.getRegisteredFontNames():
        font_dir = os.path.join(django_settings.BASE_DIR, "static", "fonts")
        reg_path = os.path.join(font_dir, "Nirmala.ttf")
        bold_path = os.path.join(font_dir, "Nirmala-Bold.ttf")

        # Fallback to Windows system fonts if static fonts are missing
        if not os.path.exists(reg_path):
            if os.path.exists("C:/Windows/Fonts/Nirmala.ttf"):
                reg_path = "C:/Windows/Fonts/Nirmala.ttf"
            elif os.path.exists("C:/Windows/Fonts/mangal.ttf"):
                reg_path = "C:/Windows/Fonts/mangal.ttf"

        if not os.path.exists(bold_path):
            if os.path.exists("C:/Windows/Fonts/NirmalaB.ttf"):
                bold_path = "C:/Windows/Fonts/NirmalaB.ttf"
            elif os.path.exists("C:/Windows/Fonts/mangalb.ttf"):
                bold_path = "C:/Windows/Fonts/mangalb.ttf"
            else:
                bold_path = reg_path

        if os.path.exists(reg_path):
            pdfmetrics.registerFont(TTFont("Devanagari", reg_path))
        if os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont("Devanagari-Bold", bold_path))

from apps.finance.models import FundAccount, LedgerEntry, DailyBalanceSnapshot, BankReconciliation
from apps.finance.services import get_financial_summary
from apps.donations.models import Donation, PaymentStatus
from apps.expenses.models import Expense, ExpensePaymentStatus, ExpenseApprovalStatus
from apps.projects.models import Project
from apps.donors.models import Donor
from apps.content.models import SiteSetting


@login_required
def reports_index(request):
    """
    Central report hub for staff to download and inspect financial reports.
    """
    if not (request.user.is_staff or request.user.role in ["SUPER_ADMIN", "TREASURER", "PRESIDENT"]):
        messages.error(request, "Access restricted.")
        return redirect("public:home")

    summary = get_financial_summary()
    projects = Project.objects.all()
    accounts = FundAccount.objects.all()

    return render(request, "dashboard/reports/index.html", {
        "summary": summary,
        "projects": projects,
        "accounts": accounts,
        "today": timezone.now().date(),
    })


# 1. EXPORT DONATIONS (CSV & EXCEL)
@login_required
def export_donations_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="Ganv_Ki_Bagiya_Donations.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Donation ID", "Receipt Number", "Date", "Donor Name", "Phone",
        "Amount (INR)", "Purpose", "Project", "Payment Method", "Status", "Reference / UTR"
    ])

    for d in Donation.objects.all().order_by("-donation_date"):
        writer.writerow([
            d.donation_id,
            d.receipt_number,
            d.donation_date.strftime("%Y-%m-%d"),
            d.donor_name,
            d.donor_phone,
            f"{d.amount:.2f}",
            d.get_purpose_display(),
            d.related_project.name if d.related_project else "General Fund",
            d.get_payment_method_display(),
            d.get_payment_status_display(),
            d.transaction_reference or "N/A"
        ])
    return response


@login_required
def export_donations_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Donations Collection"

    # Header Title
    ws.merge_cells("A1:J1")
    title_cell = ws["A1"]
    title_cell.value = "गाँव की बगिया (Ganv Ki Bagiya) — Donations Collection Register"
    title_cell.font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="1B5E20", end_color="1B5E20", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    headers = [
        "Donation ID", "Receipt No", "Date", "Donor Name", "Mobile",
        "Amount (₹)", "Purpose", "Payment Mode", "Status", "UTR / Ref"
    ]
    ws.append(headers)

    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    for col_idx in range(1, 11):
        cell = ws.cell(row=2, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    total_amount = Decimal("0.00")
    for d in Donation.objects.all().order_by("-donation_date"):
        ws.append([
            d.donation_id,
            d.receipt_number,
            d.donation_date.strftime("%Y-%m-%d"),
            d.donor_name,
            d.donor_phone,
            float(d.amount),
            str(d.get_purpose_display()),
            str(d.get_payment_method_display()),
            str(d.get_payment_status_display()),
            d.transaction_reference or "-"
        ])
        if d.payment_status == PaymentStatus.CONFIRMED:
            total_amount += d.amount

    # Total Row
    row_num = ws.max_row + 1
    ws.cell(row=row_num, column=4, value="TOTAL CONFIRMED:").font = Font(bold=True)
    total_cell = ws.cell(row=row_num, column=6, value=float(total_amount))
    total_cell.font = Font(bold=True, color="1B5E20")

    # Column widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max((len(str(cell.value or "")) for cell in col[1:]), default=10)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="Ganv_Ki_Bagiya_Donations.xlsx"'
    wb.save(response)
    return response


# 2. EXPORT EXPENSES (CSV & EXCEL)
@login_required
def export_expenses_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="Ganv_Ki_Bagiya_Expenses.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Expense ID", "Date", "Category", "Description", "Amount (INR)",
        "Vendor", "Bill No", "Project", "Approval Status", "Payment Status", "Paid From"
    ])

    for e in Expense.objects.all().order_by("-expense_date"):
        writer.writerow([
            e.expense_id,
            e.expense_date.strftime("%Y-%m-%d"),
            e.get_category_display(),
            e.description,
            f"{e.amount:.2f}",
            e.vendor_name,
            e.bill_number or "N/A",
            e.related_project.name if e.related_project else "General",
            e.get_approval_status_display(),
            e.get_payment_status_display(),
            e.paid_from_account.name if e.paid_from_account else "Unpaid"
        ])
    return response


@login_required
def export_expenses_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Expenses Record"

    ws.merge_cells("A1:K1")
    title_cell = ws["A1"]
    title_cell.value = "गाँव की बगिया (Ganv Ki Bagiya) — Expenditure & Disbursement Register"
    title_cell.font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="8D6E63", end_color="8D6E63", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    headers = [
        "Expense ID", "Date", "Category", "Description", "Amount (₹)",
        "Payee / Vendor", "Bill No", "Project", "Approval", "Payment", "Account"
    ]
    ws.append(headers)

    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4E342E", end_color="4E342E", fill_type="solid")
    for col_idx in range(1, 12):
        cell = ws.cell(row=2, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill

    total_paid = Decimal("0.00")
    for e in Expense.objects.all().order_by("-expense_date"):
        ws.append([
            e.expense_id,
            e.expense_date.strftime("%Y-%m-%d"),
            str(e.get_category_display()),
            e.description,
            float(e.amount),
            e.vendor_name,
            e.bill_number or "-",
            e.related_project.name if e.related_project else "General",
            str(e.get_approval_status_display()),
            str(e.get_payment_status_display()),
            e.paid_from_account.name if e.paid_from_account else "Unpaid"
        ])
        if e.payment_status == ExpensePaymentStatus.PAID:
            total_paid += e.amount

    row_num = ws.max_row + 1
    ws.cell(row=row_num, column=4, value="TOTAL PAID EXPENSES:").font = Font(bold=True)
    total_cell = ws.cell(row=row_num, column=5, value=float(total_paid))
    total_cell.font = Font(bold=True, color="B71C1C")

    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max((len(str(cell.value or "")) for cell in col[1:]), default=10)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="Ganv_Ki_Bagiya_Expenses.xlsx"'
    wb.save(response)
    return response


# 3. EXPORT GENERAL LEDGER (CSV & EXCEL)
@login_required
def export_ledger_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "General Ledger"

    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = "गाँव की बगिया (Ganv Ki Bagiya) — Official Financial Ledger"
    title_cell.font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="0F5132", end_color="0F5132", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    headers = ["Entry ID", "Date", "Account", "Type", "Amount (₹)", "Balance After (₹)", "Narration / Description"]
    ws.append(headers)

    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="198754", end_color="198754", fill_type="solid")
    for col_idx in range(1, 8):
        cell = ws.cell(row=2, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill

    for entry in LedgerEntry.objects.all().order_by("entry_date", "created_at"):
        ws.append([
            entry.entry_id,
            entry.entry_date.strftime("%Y-%m-%d"),
            entry.account.name,
            str(entry.get_entry_type_display()),
            float(entry.amount),
            float(entry.balance_after),
            entry.description
        ])

    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max((len(str(cell.value or "")) for cell in col[1:]), default=10)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="Ganv_Ki_Bagiya_Ledger.xlsx"'
    wb.save(response)
    return response


# 4. EXPORT FINANCIAL SUMMARY PDF (ReportLab)
@login_required
def export_financial_statement_pdf(request):
    """
    Generates high-quality downloadable PDF statement with Devanagari Hindi font support.
    """
    register_devanagari_fonts()

    # Determine registered font names with fallback
    font_regular = "Devanagari" if "Devanagari" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    font_bold = "Devanagari-Bold" if "Devanagari-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName=font_bold,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f5132"),
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName=font_regular,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#3e2723"),
        alignment=1,
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName=font_bold,
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1b5e20"),
        spaceBefore=12,
        spaceAfter=6,
    )

    settings = SiteSetting.load()
    elements.append(Paragraph(settings.ngo_name, title_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("गाँव का विकास और खुला हिसाब-किताब (Financial Audit Statement)", subtitle_style))
    elements.append(Paragraph(f"रिपोर्ट जारी करने की तारीख: {timezone.now().strftime('%d %B %Y, %I:%M %p')}", subtitle_style))
    elements.append(Spacer(1, 15))

    # Executive Summary Box
    summary = get_financial_summary()
    summary_data = [
        ["खाते का विवरण (Financial Parameter)", "रुपये / Amount (INR)"],
        ["कुल आया दान (Total Donations Received)", f"₹ {summary['total_confirmed_donations']:,.2f}"],
        ["कुल हुआ खर्च (Total Expenses Paid)", f"₹ {summary['total_expenses_paid']:,.2f}"],
        ["मौजूदा बचा बैलेंस (Net Book Balance)", f"₹ {summary['current_book_balance']:,.2f}"],
        ["नकद बैलेंस (Cash in Hand)", f"₹ {summary['cash_balance']:,.2f}"],
        ["बैंक खातों में बैलेंस (Bank Accounts Total)", f"₹ {summary['bank_balance']:,.2f}"],
        ["ऑनलाइन गेटवे बैलेंस (Online / Gateway Pool)", f"₹ {summary['online_balance']:,.2f}"],
        ["मंज़ूर लेकिन बाकी खर्च (Pending Unpaid Expenses)", f"₹ {summary['pending_payments_amount']:,.2f}"],
        ["कुल दानदाता (Total Registered Donors)", f"{summary['donor_count']} लोग"],
    ]

    t_summary = Table(summary_data, colWidths=[330, 190])
    t_summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b5e20")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), font_bold),
        ("FONTNAME", (0, 1), (-1, -1), font_regular),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8e6c9")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f1f8e9")),
        ("FONTNAME", (0, 3), (-1, 3), font_bold),
        ("TEXTCOLOR", (0, 3), (-1, 3), colors.HexColor("#0f5132")),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 18))

    # Project Summary Table
    elements.append(Paragraph("गाँव के प्रोजेक्ट्स और खर्च (Development Projects Status)", section_style))
    proj_rows = [["प्रोजेक्ट का नाम (Project)", "प्रकार (Type)", "अनुमानित बजट", "कुल खर्च", "प्रगति"]]
    for p in Project.objects.filter(is_public=True):
        proj_rows.append([
            p.name[:35],
            str(p.get_project_type_display())[:20],
            f"₹ {p.estimated_budget:,.0f}",
            f"₹ {p.actual_expenditure:,.0f}",
            f"{p.progress_percentage}%"
        ])
    if len(proj_rows) == 1:
        proj_rows.append(["कोई प्रोजेक्ट दर्ज नहीं है", "-", "₹ 0", "₹ 0", "0%"])

    t_proj = Table(proj_rows, colWidths=[180, 110, 100, 90, 40])
    t_proj.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), font_bold),
        ("FONTNAME", (0, 1), (-1, -1), font_regular),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_proj)
    elements.append(Spacer(1, 22))

    # Committee Verification Seal
    seal_data = [
        ["जाँचकर्ता (Certified By):", "सत्यापित (Verified By):", "जारीकर्ता कमेटी (Authority):"],
        [settings.treasurer_name, settings.president_name, settings.ngo_name],
        ["खज़ांची (Treasurer)", "सदर / अध्यक्ष (President)", "गाँव की बगिया कमेटी"]
    ]
    t_seal = Table(seal_data, colWidths=[175, 175, 170])
    t_seal.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), font_bold),
        ("FONTNAME", (0, 1), (-1, -1), font_regular),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_seal)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Ganv_Ki_Bagiya_Financial_Audit_Report.pdf"'
    return response
