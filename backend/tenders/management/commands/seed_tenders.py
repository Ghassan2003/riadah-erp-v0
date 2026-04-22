"""
Management command to seed sample Tender Management data.
Creates Tenders, TenderDocuments, TenderBids, TenderEvaluations, and TenderAwards
for development and testing.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from tenders.models import (
    Tender,
    TenderDocument,
    TenderBid,
    TenderEvaluation,
    TenderAward,
)


class Command(BaseCommand):
    help = 'Seed sample tender management data for the ERP system'

    def handle(self, *args, **options):
        from purchases.models import Supplier
        from users.models import User

        self.stdout.write('Creating sample Tender Management data...')

        # Ensure suppliers exist
        suppliers = list(Supplier.objects.all()[:4])
        if not suppliers:
            self.stdout.write(self.style.ERROR('  No suppliers found. Run seed_purchases first.'))
            return

        # Get an admin user for created_by fields
        admin_user = User.objects.filter(role='admin').first()

        now = timezone.now()

        # =============================================
        # 1. Create Tenders (4 records)
        # =============================================
        tenders_data = [
            {
                'tender_number': 'TND-2025-001',
                'title': 'مناقصة توريد أجهزة حاسب آلي',
                'description': 'توريد 50 جهاز حاسب آلي محمول للموظفين مع ضمان لمدة 3 سنوات',
                'tender_type': 'open',
                'status': 'published',
                'publish_date': now.date(),
                'closing_date': now.date(),
                'opening_date': now.date(),
                'estimated_value': Decimal('250000.00'),
                'terms_conditions': 'يجب تقديم ضمان لمدة 3 سنوات شاملاً الصيانة',
            },
            {
                'tender_number': 'TND-2025-002',
                'title': 'مناقصة أعمال صيانة المبنى الرئيسي',
                'description': 'صيانة شاملة للمبنى الرئيسي تشمل الكهرباء والسباكة والتكييف',
                'tender_type': 'restricted',
                'status': 'evaluation',
                'publish_date': now.date(),
                'closing_date': now.date(),
                'opening_date': now.date(),
                'estimated_value': Decimal('180000.00'),
                'terms_conditions': 'يجب أن تكون الشركة حاصلة على تصنيف في مجال الصيانة',
            },
            {
                'tender_number': 'TND-2025-003',
                'title': 'مناقصة تصميم وتنفيذ موقع إلكتروني',
                'description': 'تصميم وتطوير موقع إلكتروني متجاوب للشركة',
                'tender_type': 'invitation',
                'status': 'awarded',
                'publish_date': now.date(),
                'closing_date': now.date(),
                'opening_date': now.date(),
                'estimated_value': Decimal('95000.00'),
                'terms_conditions': 'يجب تسليم المشروع خلال 6 أشهر من تاريخ توقيع العقد',
            },
            {
                'tender_number': 'TND-2025-004',
                'title': 'مناقصة توريد معدات مكتبية',
                'description': 'توريد أثاث ومعدات مكتبية للفرع الجديد',
                'tender_type': 'open',
                'status': 'draft',
                'estimated_value': Decimal('75000.00'),
                'terms_conditions': 'التوريد خلال 30 يوماً من تاريخ الترسية',
            },
        ]

        tenders = []
        tender_count = 0
        for data in tenders_data:
            tender, created = Tender.objects.get_or_create(
                tender_number=data['tender_number'],
                defaults={
                    'title': data['title'],
                    'description': data.get('description', ''),
                    'tender_type': data['tender_type'],
                    'status': data['status'],
                    'publish_date': data.get('publish_date'),
                    'closing_date': data.get('closing_date'),
                    'opening_date': data.get('opening_date'),
                    'estimated_value': data['estimated_value'],
                    'terms_conditions': data.get('terms_conditions', ''),
                    'created_by': admin_user,
                },
            )
            tenders.append(tender)
            if created:
                tender_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created tender: {tender.tender_number} - {tender.title}'))
            else:
                self.stdout.write(f'  Skipped (exists): {tender.tender_number}')

        # =============================================
        # 2. Create TenderDocuments (5 records)
        # =============================================
        documents_data = [
            {'tender_idx': 0, 'title': 'كتاب الشروط والمواصفات', 'description': 'الملف الفني لكتاب الشروط'},
            {'tender_idx': 0, 'title': 'نموذج العرض الفني', 'description': 'النموذج المعتمد لتقديم العرض الفني'},
            {'tender_idx': 1, 'title': 'مخططات المبنى', 'description': 'المخططات الهندسية للمبنى الرئيسي'},
            {'tender_idx': 1, 'title': 'تقرير حالة المبنى', 'description': 'تقرير فحص حالة المبنى الحالي'},
            {'tender_idx': 2, 'title': 'مستندات متطلبات الموقع', 'description': 'المتطلبات الوظيفية والتصميمية للموقع'},
        ]

        doc_count = 0
        for data in documents_data:
            idx = data['tender_idx']
            if idx >= len(tenders):
                continue
            tender = tenders[idx]

            doc, created = TenderDocument.objects.get_or_create(
                tender=tender,
                title=data['title'],
                defaults={
                    'description': data.get('description', ''),
                },
            )
            if created:
                doc_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created document: {doc.title} - {doc.tender.tender_number}'))
            else:
                self.stdout.write(f'  Skipped (exists): {doc.title}')

        # =============================================
        # 3. Create TenderBids (8 records)
        # =============================================
        bids_data = [
            {'tender_idx': 0, 'supplier_idx': 0, 'bid_number': 'BID-2025-001', 'status': 'qualified', 'total_amount': Decimal('245000.00'), 'validity_days': 90, 'technical_score': Decimal('85.50'), 'financial_score': Decimal('90.00'), 'total_score': Decimal('87.75')},
            {'tender_idx': 0, 'supplier_idx': 1, 'bid_number': 'BID-2025-002', 'status': 'qualified', 'total_amount': Decimal('238000.00'), 'validity_days': 120, 'technical_score': Decimal('80.00'), 'financial_score': Decimal('95.00'), 'total_score': Decimal('87.50')},
            {'tender_idx': 0, 'supplier_idx': 2, 'bid_number': 'BID-2025-003', 'status': 'submitted', 'total_amount': Decimal('260000.00'), 'validity_days': 60},
            {'tender_idx': 1, 'supplier_idx': 0, 'bid_number': 'BID-2025-004', 'status': 'qualified', 'total_amount': Decimal('175000.00'), 'validity_days': 90, 'technical_score': Decimal('92.00'), 'financial_score': Decimal('88.00'), 'total_score': Decimal('90.00')},
            {'tender_idx': 1, 'supplier_idx': 3, 'bid_number': 'BID-2025-005', 'status': 'disqualified', 'total_amount': Decimal('190000.00'), 'validity_days': 90},
            {'tender_idx': 2, 'supplier_idx': 1, 'bid_number': 'BID-2025-006', 'status': 'selected', 'total_amount': Decimal('88000.00'), 'validity_days': 180, 'technical_score': Decimal('95.00'), 'financial_score': Decimal('92.00'), 'total_score': Decimal('93.50')},
            {'tender_idx': 2, 'supplier_idx': 2, 'bid_number': 'BID-2025-007', 'status': 'rejected', 'total_amount': Decimal('120000.00'), 'validity_days': 90},
            {'tender_idx': 2, 'supplier_idx': 3, 'bid_number': 'BID-2025-008', 'status': 'rejected', 'total_amount': Decimal('110000.00'), 'validity_days': 60},
        ]

        bids = []
        bid_count = 0
        for data in bids_data:
            t_idx = data['tender_idx']
            s_idx = data['supplier_idx']
            if t_idx >= len(tenders) or s_idx >= len(suppliers):
                continue
            tender = tenders[t_idx]
            supplier = suppliers[s_idx]

            bid, created = TenderBid.objects.get_or_create(
                bid_number=data['bid_number'],
                defaults={
                    'tender': tender,
                    'supplier': supplier,
                    'submission_date': now.date(),
                    'status': data['status'],
                    'total_amount': data['total_amount'],
                    'validity_days': data['validity_days'],
                    'technical_score': data.get('technical_score'),
                    'financial_score': data.get('financial_score'),
                    'total_score': data.get('total_score'),
                },
            )
            bids.append(bid)
            if created:
                bid_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created bid: {bid.bid_number} - {bid.supplier.name}'))
            else:
                self.stdout.write(f'  Skipped (exists): {bid.bid_number}')

        # =============================================
        # 4. Create TenderEvaluations (12 records)
        # =============================================
        evaluations_data = [
            {'bid_idx': 0, 'criterion': 'الخبرة الفنية', 'weight': Decimal('25.00'), 'score': Decimal('90.00'), 'weighted_score': Decimal('22.50')},
            {'bid_idx': 0, 'criterion': 'السعر التنافسي', 'weight': Decimal('35.00'), 'score': Decimal('85.00'), 'weighted_score': Decimal('29.75')},
            {'bid_idx': 0, 'criterion': 'ضمان الجودة', 'weight': Decimal('20.00'), 'score': Decimal('80.00'), 'weighted_score': Decimal('16.00')},
            {'bid_idx': 1, 'criterion': 'الخبرة الفنية', 'weight': Decimal('25.00'), 'score': Decimal('85.00'), 'weighted_score': Decimal('21.25')},
            {'bid_idx': 1, 'criterion': 'السعر التنافسي', 'weight': Decimal('35.00'), 'score': Decimal('92.00'), 'weighted_score': Decimal('32.20')},
            {'bid_idx': 1, 'criterion': 'ضمان الجودة', 'weight': Decimal('20.00'), 'score': Decimal('75.00'), 'weighted_score': Decimal('15.00')},
            {'bid_idx': 3, 'criterion': 'الخبرة الفنية', 'weight': Decimal('30.00'), 'score': Decimal('95.00'), 'weighted_score': Decimal('28.50')},
            {'bid_idx': 3, 'criterion': 'السعر التنافسي', 'weight': Decimal('30.00'), 'score': Decimal('88.00'), 'weighted_score': Decimal('26.40')},
            {'bid_idx': 3, 'criterion': 'مدة التنفيذ', 'weight': Decimal('20.00'), 'score': Decimal('90.00'), 'weighted_score': Decimal('18.00')},
            {'bid_idx': 5, 'criterion': 'الخبرة التقنية', 'weight': Decimal('30.00'), 'score': Decimal('98.00'), 'weighted_score': Decimal('29.40')},
            {'bid_idx': 5, 'criterion': 'السعر التنافسي', 'weight': Decimal('30.00'), 'score': Decimal('90.00'), 'weighted_score': Decimal('27.00')},
            {'bid_idx': 5, 'criterion': 'جودة التصميم', 'weight': Decimal('20.00'), 'score': Decimal('95.00'), 'weighted_score': Decimal('19.00')},
        ]

        eval_count = 0
        for data in evaluations_data:
            b_idx = data['bid_idx']
            if b_idx >= len(bids):
                continue
            bid = bids[b_idx]

            evaluation, created = TenderEvaluation.objects.get_or_create(
                bid=bid,
                criterion=data['criterion'],
                defaults={
                    'weight': data['weight'],
                    'score': data['score'],
                    'weighted_score': data['weighted_score'],
                    'evaluator': admin_user,
                },
            )
            if created:
                eval_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created evaluation: {evaluation.criterion} - {bid.bid_number}'))
            else:
                self.stdout.write(f'  Skipped (exists): {evaluation.criterion} - {bid.bid_number}')

        # =============================================
        # 5. Create TenderAwards (2 records)
        # =============================================
        awards_data = [
            {'tender_idx': 2, 'bid_idx': 5, 'contract_value': Decimal('88000.00'), 'contract_duration_days': 180, 'status': 'approved'},
            {'tender_idx': 1, 'bid_idx': 3, 'contract_value': Decimal('175000.00'), 'contract_duration_days': 365, 'status': 'pending'},
        ]

        award_count = 0
        for data in awards_data:
            t_idx = data['tender_idx']
            b_idx = data['bid_idx']
            if t_idx >= len(tenders) or b_idx >= len(bids):
                continue
            tender = tenders[t_idx]
            bid = bids[b_idx]

            award, created = TenderAward.objects.get_or_create(
                tender=tender,
                bid=bid,
                defaults={
                    'award_date': now.date(),
                    'contract_value': data['contract_value'],
                    'contract_duration_days': data['contract_duration_days'],
                    'terms': 'الشروط والأحكام حسب كتاب الشروط المرفق',
                    'status': data['status'],
                    'approved_by': admin_user if data['status'] == 'approved' else None,
                },
            )
            if created:
                award_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created award: {tender.tender_number} - {bid.supplier.name} ({award.get_status_display()})'))
            else:
                self.stdout.write(f'  Skipped (exists): {tender.tender_number} - {bid.supplier.name}')

        # =============================================
        # Summary
        # =============================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Seed Summary ==='))
        self.stdout.write(f'  Tenders created: {tender_count}')
        self.stdout.write(f'  Tender Documents created: {doc_count}')
        self.stdout.write(f'  Tender Bids created: {bid_count}')
        self.stdout.write(f'  Tender Evaluations created: {eval_count}')
        self.stdout.write(f'  Tender Awards created: {award_count}')
        self.stdout.write(self.style.SUCCESS('Done! Tender Management data seeded successfully.'))
