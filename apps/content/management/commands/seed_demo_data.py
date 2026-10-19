import uuid
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.models import CustomUser, UserRole
from apps.content.models import SiteSetting, Announcement
from apps.finance.models import FundAccount, AccountType, LedgerEntry, LedgerEntryType, DailyBalanceSnapshot
from apps.finance.services import calculate_daily_balance
from apps.projects.models import Project, ProjectStatus
from apps.donors.models import Donor
from apps.donations.models import Donation, PaymentMethod, PaymentStatus, DonationPurpose
from apps.expenses.models import Expense, ExpenseCategory, ExpenseApprovalStatus, ExpensePaymentStatus, ExpenseApprovalLog
from apps.maintenance.models import MaintenanceTask, TaskStatus, TaskPriority, FacilityType, TaskType
from apps.payments.models import UPIReconciliationRecord, PaymentTransaction
from apps.gallery.models import GalleryAlbum, AlbumCategory


class Command(BaseCommand):
    help = "Seeds initial demo data with users, accounts, projects, donations, expenses, and ledger entries."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data for Ganv Ki Bagiya...")

        with transaction.atomic():
            # 1. Site Settings
            settings = SiteSetting.load()
            settings.site_name = "गाँव की बगिया (Ganv Ki Bagiya)"
            settings.tagline = "सामुदायिक बगिया एवं कब्रिस्तान संरक्षण व विकास प्रबंधन"
            settings.about_text = (
                "गाँव की बगिया हमारे ग्रामीण समुदाय की एक पवित्र और ऐतिहासिक पहल है। "
                "ग्रामवासियों एवं समर्थकों के सहयोग से हम अनुपयोगी भूमि को एक हरे-भरे, "
                "सुव्यवस्थित बगीचे तथा कब्रिस्तान में तब्दील कर रहे हैं, जहां प्रत्येक दान "
                "और पाई-पाई का सार्वजनिक हिसाब पूरी पारदर्शिता के साथ उपलब्ध है।"
            )
            settings.contact_email = "committee@bagiya.org"
            settings.contact_phone = "+91 98765 43210"
            settings.village_name = "रामपुर / रामपुर देहात"
            settings.district_state = "सहारनपुर, उत्तर प्रदेश"
            settings.upi_id = "bagiya@upi"
            settings.upi_merchant_name = "Ganv Ki Bagiya Samiti"
            settings.bank_account_name = "Ganv Ki Bagiya Samiti Trust"
            settings.bank_account_number = "50100458923412"
            settings.bank_ifsc_code = "SBIN0001234"
            settings.bank_name = "State Bank of India (SBI)"
            settings.bank_branch = "Rampur Dehat Branch"
            settings.save()
            self.stdout.write(self.style.SUCCESS("[OK] Site settings configured."))

            # 2. Roles & Users
            User = get_user_model()
            users_data = [
                ("admin", "admin@bagiya.org", "Admin@123", UserRole.SUPER_ADMIN, "मोहम्मद", "आरिफ", "+919876543210", True),
                ("treasurer", "treasurer@bagiya.org", "Treasurer@123", UserRole.TREASURER, "हाजी", "मुश्ताक (खजांची)", "+919876543211", True),
                ("president", "president@bagiya.org", "President@123", UserRole.PRESIDENT, "चौधरी", "शमशाद (सदर/अध्यक्ष)", "+919876543212", True),
                ("manager", "manager@bagiya.org", "Manager@123", UserRole.PROJECT_MANAGER, "इमरान", "अहमद (प्रोजेक्ट प्रभारी)", "+919876543213", True),
                ("volunteer1", "volunteer@bagiya.org", "Volunteer@123", UserRole.VOLUNTEER, "दानिश", "अख्तर (स्वयंसेवक)", "+919876543214", False),
            ]

            created_users = {}
            for uname, email, pwd, role, fname, lname, phone, is_staff in users_data:
                u, created = User.objects.get_or_create(username=uname, defaults={
                    "email": email,
                    "role": role,
                    "first_name": fname,
                    "last_name": lname,
                    "phone_number": phone,
                    "is_staff": is_staff,
                    "is_superuser": (role == UserRole.SUPER_ADMIN),
                })
                if created:
                    u.set_password(pwd)
                    u.save()
                created_users[role] = u

            admin_user = created_users[UserRole.SUPER_ADMIN]
            treasurer_user = created_users[UserRole.TREASURER]
            president_user = created_users[UserRole.PRESIDENT]
            manager_user = created_users[UserRole.PROJECT_MANAGER]

            self.stdout.write(self.style.SUCCESS("[OK] 5 Core role users verified."))

            # 3. Fund Accounts
            bank_acc, _ = FundAccount.objects.get_or_create(
                account_type=AccountType.BANK,
                defaults={
                    "name": "Bank of Baroda - जावेद अली",
                    "account_number": "37098100001150",
                    "bank_name": "Bank of Baroda",
                    "ifsc_code": "BARBOPILAKH",
                    "branch_name": "Pilakhwa Branch",
                    "current_balance": Decimal("0.00"),
                    "is_active": True,
                }
            )

            cash_acc, _ = FundAccount.objects.get_or_create(
                account_type=AccountType.CASH,
                defaults={
                    "name": "नकद पेटी (Cash) - जावेद अली",
                    "bank_name": "नकद पेटी (Cash Box)",
                    "branch_name": "कार्यालय / कमेटी",
                    "current_balance": Decimal("0.00"),
                    "is_active": True,
                }
            )

            online_acc, _ = FundAccount.objects.get_or_create(
                account_type=AccountType.UPI,
                defaults={
                    "name": "UPI (8937877789@ybl) - जावेद अली",
                    "account_number": "8937877789@ybl",
                    "bank_name": "UPI / Bank of Baroda",
                    "branch_name": "UPI VPA Pool",
                    "current_balance": Decimal("0.00"),
                    "is_active": True,
                }
            )
            self.stdout.write(self.style.SUCCESS("[OK] 3 Fund accounts initialized for Javed Ali."))

            # 4. Development Projects
            proj1, _ = Project.objects.get_or_create(
                slug="kabristan-boundary-gate",
                defaults={
                    "name": "कब्रिस्तान की पक्की चारदीवारी व मुख्य द्वार",
                    "project_type": ProjectType.KABRISTAN,
                    "description": "कब्रिस्तान की सुरक्षा और आवारा पशुओं की रोकथाम के लिए 7 फीट ऊंची पक्की ईंट की दीवार और बड़ा मजबूत लोहे का मुख्य द्वार निर्माण कार्य।",
                    "objectives": "• 450 फीट लंबी पक्की ईंट की चारदीवारी\n• 10 फीट चौड़ा लोहे का सुरक्षा गेट\n• मिट्टी भराव व समतलीकरण कार्य",
                    "estimated_budget": Decimal("150000.00"),
                    "status": ProjectStatus.ACTIVE,
                    "progress_percentage": 65,
                    "start_date": timezone.now().date() - timedelta(days=90),
                    "manager": manager_user,
                    "is_public": True,
                }
            )

            proj2, _ = Project.objects.get_or_create(
                slug="garden-beautification-plantation",
                defaults={
                    "name": "बगीचा सौंदर्यीकरण एवं सघन वृक्षारोपण",
                    "project_type": ProjectType.GARDEN,
                    "description": "बंजर भूमि पर फलदार, छायादार पौधे रोपना, हरियाली लॉन और वॉकवे का निर्माण करना।",
                    "objectives": "• 500+ छायादार वृक्ष (नीम, पीपल, जामुन, शीशम)\n• पौधों की सुरक्षा के लिए ट्री-गार्ड लगाना\n• नियमित खाद, पानी और निराई-गुड़ाई की व्यवस्था",
                    "estimated_budget": Decimal("60000.00"),
                    "status": ProjectStatus.ACTIVE,
                    "progress_percentage": 75,
                    "start_date": timezone.now().date() - timedelta(days=60),
                    "manager": manager_user,
                    "is_public": True,
                }
            )

            proj3, _ = Project.objects.get_or_create(
                slug="solar-submersible-water-supply",
                defaults={
                    "name": "सोलर सबमर्सिबल बोरिंग एवं पेयजल व्यवस्था",
                    "project_type": ProjectType.INFRASTRUCTURE,
                    "description": "पौधों की सिंचाई और कब्रिस्तान में वुज़ू/हाथ धोने हेतु सोलर सबमर्सिबल पंप एवं पानी की टंकी स्थापना।",
                    "objectives": "• 250 फीट गहरा सबमर्सिबल बोरिंग\n• 3 HP सोलर पंप और 2000L सिंटेक्स टंकी\n• पूरे परिसर में पानी की पाइपलाइन व टोंटियां",
                    "estimated_budget": Decimal("85000.00"),
                    "status": ProjectStatus.COMPLETED,
                    "progress_percentage": 100,
                    "start_date": timezone.now().date() - timedelta(days=120),
                    "target_completion_date": timezone.now().date() - timedelta(days=10),
                    "manager": manager_user,
                    "is_public": True,
                }
            )

            proj4, _ = Project.objects.get_or_create(
                slug="janaza-shed-wudu-facility",
                defaults={
                    "name": "जनाज़ा शेड व वुज़ूखाना निर्माण",
                    "project_type": ProjectType.KABRISTAN,
                    "description": "बारिश और कड़ी धूप के मौसम में जनाज़े की नमाज़ और अकीदतमंदों के बैठने के लिए पक्का कंक्रीट शेड, फर्श टाइल्स और वुज़ू की मुकम्मल व्यवस्था।",
                    "objectives": "• 40x25 फीट पक्का शेड निर्माण\n• फर्श पर कोटा स्टोन/टाइल्स बिछाना\n• 8 नल वाला पक्का वुज़ू चबूतरा",
                    "estimated_budget": Decimal("95000.00"),
                    "status": ProjectStatus.ACTIVE,
                    "progress_percentage": 50,
                    "start_date": timezone.now().date() - timedelta(days=45),
                    "manager": manager_user,
                    "is_public": True,
                }
            )

            proj5, _ = Project.objects.get_or_create(
                slug="garden-walkway-park-benches",
                defaults={
                    "name": "पैदल रास्ता (Walkway) एवं बैठने हेतु पक्की बेंच",
                    "project_type": ProjectType.GARDEN,
                    "description": "बुजुर्गों और गाँव वालों के सुबह-शाम टहलने के लिए इंटरलॉकिंग टाइल्स का सुरक्षित वॉकवे और छायादार पेड़ों के नीचे 8 पक्की सीमेंटेड बेंच लगाना।",
                    "objectives": "• 300 मीटर लंबा इंटरलॉकिंग टाइल पाथवे\n• 8 सीमेंटेड बेंच की स्थापना\n• कूड़ेदान (Dustbins) लगाना",
                    "estimated_budget": Decimal("45000.00"),
                    "status": ProjectStatus.PLANNING,
                    "progress_percentage": 25,
                    "start_date": timezone.now().date() - timedelta(days=20),
                    "manager": manager_user,
                    "is_public": True,
                }
            )

            proj6, _ = Project.objects.get_or_create(
                slug="solar-street-lighting",
                defaults={
                    "name": "सोलर स्ट्रीट लाइट एवं रात्रि प्रकाश व्यवस्था",
                    "project_type": ProjectType.INFRASTRUCTURE,
                    "description": "रात के अंधेरे में सुरक्षा और रोशनी के लिए बगिया के रास्तों और कब्रिस्तान परिसर में 6 ऑटोमैटिक सोलर एलईडी लाइट्स व पोल्स लगाना।",
                    "objectives": "• 6 सोलर पावर्ड एलईडी लाइट्स\n• ऑटो ऑन-ऑफ सेंसर और लिथियम बैटरी\n• 15 फीट ऊंचे जीआई पोल्स की स्थापना",
                    "estimated_budget": Decimal("40000.00"),
                    "status": ProjectStatus.ACTIVE,
                    "progress_percentage": 80,
                    "start_date": timezone.now().date() - timedelta(days=35),
                    "manager": manager_user,
                    "is_public": True,
                }
            )
            self.stdout.write(self.style.SUCCESS("[OK] 6 Community projects initialized."))

            # 5. Donors & Donations
            donors_data = [
                ("हाजी अब्दुल रशीद", "9897112233", "abdul.rashid@example.com", "मेन रोड, रामपुर देहात", False),
                ("मोहम्मद यूनुस (सऊदी अरब)", "9897223344", "younus.ksa@example.com", "रियाद / पैतृक रामपुर", False),
                ("चौधरी अख्तर अली", "9897334455", "", "नजदीक जामा मस्जिद", False),
                ("एक नेक ग्रामीण भाई", "9897445566", "", "रामपुर", True),
                ("मास्टर शफीक अहमद", "9897556677", "shafiq.edu@example.com", "शिक्षक, मोहल्ला कस्साबान", False),
            ]

            created_donors = []
            for name, phone, email, addr, anon in donors_data:
                d, _ = Donor.objects.get_or_create(phone=phone, defaults={
                    "name": name,
                    "email": email,
                    "address": addr,
                    "is_anonymous": anon,
                })
                created_donors.append(d)

            # Sample Confirmed Donations
            sample_donations = [
                (created_donors[0], Decimal("25000.00"), DonationPurpose.KABRISTAN_MAINTENANCE, PaymentMethod.BANK_TRANSFER, proj2, bank_acc, 20),
                (created_donors[1], Decimal("50000.00"), DonationPurpose.GARDEN_DEV, PaymentMethod.ONLINE_GATEWAY, proj1, online_acc, 15),
                (created_donors[2], Decimal("11000.00"), DonationPurpose.TREE_PLANTATION, PaymentMethod.CASH, proj1, cash_acc, 10),
                (created_donors[3], Decimal("15000.00"), DonationPurpose.GENERAL, PaymentMethod.UPI_QR, None, bank_acc, 5),
                (created_donors[4], Decimal("5000.00"), DonationPurpose.WATER_ELEC, PaymentMethod.CASH, proj3, cash_acc, 2),
            ]

            for donor, amt, purpose, method, proj, acc, days_ago in sample_donations:
                d_date = timezone.now().date() - timedelta(days=days_ago)
                don, created = Donation.objects.get_or_create(
                    donor=donor,
                    amount=amt,
                    donation_date=d_date,
                    defaults={
                        "donor_name": donor.name,
                        "donor_phone": donor.phone,
                        "donor_email": donor.email,
                        "donor_address": donor.address,
                        "is_anonymous": donor.is_anonymous,
                        "purpose": purpose,
                        "payment_method": method,
                        "payment_status": PaymentStatus.CONFIRMED,
                        "related_project": proj,
                        "destination_account": acc,
                        "transaction_reference": f"TXN{days_ago}009988",
                        "recorded_by": treasurer_user,
                        "verified_by": treasurer_user,
                        "verified_at": timezone.now() - timedelta(days=days_ago),
                        "message": "ईश्वर हमारे गांव की बगिया व कब्रिस्तान को आबाद रखे।",
                    }
                )
                if created and not don.is_posted_to_ledger:
                    don.post_to_ledger(user=treasurer_user)

            # A pending UPI donation for testing reconciliation
            pending_utr = "329019283746"
            pend_don, created = Donation.objects.get_or_create(
                transaction_reference=pending_utr,
                defaults={
                    "donor": created_donors[0],
                    "donor_name": created_donors[0].name,
                    "donor_phone": created_donors[0].phone,
                    "amount": Decimal("2100.00"),
                    "purpose": DonationPurpose.TREE_PLANTATION,
                    "payment_method": PaymentMethod.UPI_QR,
                    "payment_status": PaymentStatus.PENDING,
                    "related_project": proj1,
                    "destination_account": bank_acc,
                    "donation_date": timezone.now().date() - timedelta(days=1),
                    "message": "पौधों के लिए UPI द्वारा भेजा गया।",
                }
            )

            # Bank reconciliation record corresponding to it for testing auto-match
            UPIReconciliationRecord.objects.get_or_create(
                utr_number=pending_utr,
                defaults={
                    "bank_statement_date": timezone.now().date() - timedelta(days=1),
                    "amount": Decimal("2100.00"),
                    "payer_details": "UPI/329019283746/HajiAbdulRashid",
                    "is_matched": False,
                    "notes": "Bank credit statement entry",
                }
            )

            # An unmatched bank entry
            UPIReconciliationRecord.objects.get_or_create(
                utr_number="419827364512",
                defaults={
                    "bank_statement_date": timezone.now().date(),
                    "amount": Decimal("1500.00"),
                    "payer_details": "UPI/419827364512/SenderUnknown",
                    "is_matched": False,
                    "notes": "Direct bank credit awaiting donor identification",
                }
            )
            self.stdout.write(self.style.SUCCESS("[OK] Donors, donations & reconciliation records seeded."))

            # 6. Expenses
            expenses_data = [
                ("सघन वृक्षारोपण हेतु 120 फलदार व छायादार पौधे क्रय", Decimal("18000.00"), ExpenseCategory.PLANTS, proj1, cash_acc, ExpensePaymentStatus.PAID, 18),
                ("कब्रिस्तान चारदीवारी हेतु 10,000 अव्वल ईंटें एवं बालू", Decimal("72000.00"), ExpenseCategory.CONSTRUCTION, proj2, bank_acc, ExpensePaymentStatus.PAID, 14),
                ("बगीचा व कब्रिस्तान परिसर में खरपतवार सफाई एवं समतलीकरण लेबर", Decimal("6500.00"), ExpenseCategory.LABOR, proj1, cash_acc, ExpensePaymentStatus.PAID, 7),
                ("3 HP सबमर्सिबल सोलर पंप उपकरण भुगतान", Decimal("55000.00"), ExpenseCategory.TOOLS, proj3, bank_acc, ExpensePaymentStatus.PAID, 25),
                ("घास कटाई मशीन एवं वाटर स्प्रिंकलर सेट", Decimal("8500.00"), ExpenseCategory.TOOLS, proj1, cash_acc, ExpensePaymentStatus.APPROVED, 1),
            ]

            for title, amt, cat, proj, acc, pay_status, days_ago in expenses_data:
                e_date = timezone.now().date() - timedelta(days=days_ago)
                exp, created = Expense.objects.get_or_create(
                    title=title,
                    defaults={
                        "category": cat,
                        "amount": amt,
                        "expense_date": e_date,
                        "payee_name": "स्थानीय सप्लायर / मजदूर दल",
                        "related_project": proj,
                        "paid_from_account": acc,
                        "approval_status": ExpenseApprovalStatus.APPROVED,
                        "payment_status": pay_status,
                        "requested_by": manager_user,
                        "approved_by": president_user,
                        "paid_by": treasurer_user if pay_status == ExpensePaymentStatus.PAID else None,
                        "paid_at": timezone.now() - timedelta(days=days_ago) if pay_status == ExpensePaymentStatus.PAID else None,
                        "description": f"समिति की अधिकृत बैठक में पारित व्यय: {title}",
                    }
                )
                if created and pay_status == ExpensePaymentStatus.PAID and not exp.is_posted_to_ledger:
                    exp.post_to_ledger(user=treasurer_user)

            self.stdout.write(self.style.SUCCESS("[OK] Sample expenses created and posted to ledger."))

            # 7. Calculate daily balance snapshots
            for d_offset in range(15, -1, -1):
                snap_date = timezone.now().date() - timedelta(days=d_offset)
                calculate_daily_balance(snap_date)

            self.stdout.write(self.style.SUCCESS("[OK] Daily balances computed."))

            # 8. Maintenance Tasks
            MaintenanceTask.objects.get_or_create(
                title="कब्रिस्तान पूर्वी भाग में झाड़ियों व खरपतवार की नियमित सफाई",
                defaults={
                    "facility": FacilityType.KABRISTAN,
                    "task_type": TaskType.CLEANING,
                    "scheduled_date": timezone.now().date() + timedelta(days=3),
                    "priority": TaskPriority.HIGH,
                    "status": TaskStatus.PENDING,
                    "created_by": manager_user,
                    "description": "जुमे की नमाज़ से पूर्व कब्रिस्तान के रास्तों और पूर्वी भाग की सम्पूर्ण सफाई।",
                }
            )

            MaintenanceTask.objects.get_or_create(
                title="बगीचे में नव-रोपित पौधों की खाद व कीटनाशक उपचार",
                defaults={
                    "facility": FacilityType.GARDEN,
                    "task_type": TaskType.TREE_PLANTATION,
                    "scheduled_date": timezone.now().date() + timedelta(days=5),
                    "priority": TaskPriority.MEDIUM,
                    "status": TaskStatus.PENDING,
                    "created_by": manager_user,
                    "description": "देशी खाद व जैविक कीटनाशक का छिड़काव ताकि पौधे स्वस्थ रहें।",
                }
            )
            self.stdout.write(self.style.SUCCESS("[OK] Maintenance tasks created."))

            # 9. Announcements & Gallery
            Announcement.objects.get_or_create(
                title="गाँव की बगिया वेबसाइट एवं ऑनलाइन दान प्रणाली का शुभारंभ",
                defaults={
                    "content": "सभी ग्रामवासियों व देश-विदेश में रह रहे साथियों को सूचित किया जाता है कि गाँव की बगिया की आधिकारिक वेबसाइट शुरू हो गई है। अब आप हर दान का विवरण, पाई-पाई का खर्च और दैनिक बैलेंस कभी भी ऑनलाइन देख सकते हैं।",
                    "priority": "HIGH",
                    "is_active": True,
                    "publish_date": timezone.now().date(),
                    "created_by": president_user,
                }
            )

            GalleryAlbum.objects.get_or_create(
                title="वृक्षारोपण अभियान - चरण 1",
                defaults={
                    "category": AlbumCategory.TREE_PLANTATION,
                    "description": "ग्रामवासियों और नौजवानों द्वारा बगीचे में फलदार व छायादार पौधे लगाने के खूबसूरत पल।",
                    "created_by": manager_user,
                }
            )
            self.stdout.write(self.style.SUCCESS("[OK] Announcements & gallery album created."))

        self.stdout.write(self.style.SUCCESS("\n Demo data successfully seeded for Ganv Ki Bagiya!"))
        self.stdout.write("Credentials:")
        self.stdout.write("  Super Admin : admin / Admin@123")
        self.stdout.write("  Treasurer   : treasurer / Treasurer@123")
        self.stdout.write("  President   : president / President@123")
        self.stdout.write("  Manager     : manager / Manager@123")
        self.stdout.write("  Volunteer   : volunteer1 / Volunteer@123")
