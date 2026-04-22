"""
Seed script for Insurance & Pension module.
Creates 5 insurance policies, 4 claims, 6 pension records, and 8 pension payments.

Usage:
    cd /home/z/my-project/download/erp-system/backend
    python manage.py shell < insurance/seed_insurance.py
"""

from decimal import Decimal

from django.utils import timezone

from insurance.models import (
    InsurancePolicy,
    InsuranceClaim,
    PensionRecord,
    PensionPayment,
)


def seed_insurance():
    """Seed sample insurance and pension data."""
    from users.models import User
    from hr.models import Employee

    print('Creating sample Insurance & Pension data...')

    # Ensure an admin user exists
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        print('  ERROR: No admin user found. Run seed_users first.')
        return

    # Ensure employees exist
    employees = list(Employee.objects.filter(is_active=True)[:6])
    if not employees:
        print('  ERROR: No active employees found. Run seed_hr first.')
        return

    now = timezone.now()
    created_counts = {'policies': 0, 'claims': 0, 'pensions': 0, 'payments': 0}

    # =============================================
    # 1. Create 5 Insurance Policies
    # =============================================
    policies_data = [
        {
            'policy_number': 'INS-2025-001',
            'policy_name': 'تأمين صحي شامل للموظفين',
            'insurance_provider': 'شركة التأمين العربية السعودية (Tawuniya)',
            'insurance_type': 'health',
            'coverage_amount': Decimal('5000000.00'),
            'premium_amount': Decimal('180000.00'),
            'premium_frequency': 'annual',
            'start_date': now.date().replace(month=1, day=1),
            'end_date': now.date().replace(month=12, day=31),
            'status': 'active',
            'insured_entity': 'company',
            'related_entity_id': None,
            'notes': 'بوليصة تأمين صحي جماعية لجميع الموظفين',
        },
        {
            'policy_number': 'INS-2025-002',
            'policy_name': 'تأمين على حياة الموظفين',
            'insurance_provider': 'شركة تكافل الراجحي',
            'insurance_type': 'life',
            'coverage_amount': Decimal('2000000.00'),
            'premium_amount': Decimal('95000.00'),
            'premium_frequency': 'annual',
            'start_date': now.date().replace(month=1, day=1),
            'end_date': now.date().replace(month=12, day=31),
            'status': 'active',
            'insured_entity': 'company',
            'related_entity_id': None,
            'notes': 'تأمين حياة جماعي للموظفين',
        },
        {
            'policy_number': 'INS-2025-003',
            'policy_name': 'تأمين مركبات أسطول الشركة',
            'insurance_provider': 'شركة أروب للتأمين التعاوني',
            'insurance_type': 'vehicle',
            'coverage_amount': Decimal('1000000.00'),
            'premium_amount': Decimal('35000.00'),
            'premium_frequency': 'annual',
            'start_date': now.date().replace(month=3, day=1),
            'end_date': now.date().replace(month=2, day=28).replace(year=now.year + 1),
            'status': 'active',
            'insured_entity': 'vehicle',
            'related_entity_id': 1,
            'notes': 'تأمين شامل لجميع مركبات الشركة',
        },
        {
            'policy_number': 'INS-2025-004',
            'policy_name': 'تأمين المبنى الرئيسي',
            'insurance_provider': 'شركة ساب للتأمين التعاوني',
            'insurance_type': 'property',
            'coverage_amount': Decimal('15000000.00'),
            'premium_amount': Decimal('75000.00'),
            'premium_frequency': 'annual',
            'start_date': now.date().replace(month=1, day=1),
            'end_date': now.date().replace(month=12, day=31),
            'status': 'active',
            'insured_entity': 'asset',
            'related_entity_id': 1,
            'notes': 'تأمين ضد الحريق والكوارث الطبيعية للمبنى الرئيسي',
        },
        {
            'policy_number': 'INS-2024-005',
            'policy_name': 'تأمين إصابات عمل',
            'insurance_provider': 'شركة التعاونية للتأمين',
            'insurance_type': 'workers_comp',
            'coverage_amount': Decimal('3000000.00'),
            'premium_amount': Decimal('45000.00'),
            'premium_frequency': 'annual',
            'start_date': now.date().replace(year=now.year - 1, month=1, day=1),
            'end_date': now.date().replace(year=now.year - 1, month=12, day=31),
            'status': 'expired',
            'insured_entity': 'company',
            'related_entity_id': None,
            'notes': 'بوليصة منتهية الصلاحية - تحتاج للتجديد',
        },
    ]

    created_policies = []
    for data in policies_data:
        policy, created = InsurancePolicy.objects.get_or_create(
            policy_number=data['policy_number'],
            defaults={**data, 'created_by': admin_user},
        )
        if created:
            created_counts['policies'] += 1
            print(f'  Created policy: {policy.policy_number} - {policy.policy_name}')
        else:
            print(f'  Skipped (exists): {policy.policy_number}')
        created_policies.append(policy)

    # =============================================
    # 2. Create 4 Insurance Claims
    # =============================================
    claims_data = [
        {
            'claim_number': 'CLM-2025-001',
            'policy_idx': 0,
            'claim_type': 'partial',
            'incident_date': now.date().replace(month=2, day=15),
            'description': 'طلب تعويض عن مصاريف علاج جراحة لموظف في قسم المحاسبة',
            'claimed_amount': Decimal('25000.00'),
            'approved_amount': Decimal('20000.00'),
            'status': 'approved',
            'submitted_by': admin_user,
            'reviewed_by': admin_user,
            'reviewed_at': now,
            'payment_date': now.date(),
        },
        {
            'claim_number': 'CLM-2025-002',
            'policy_idx': 2,
            'claim_type': 'partial',
            'incident_date': now.date().replace(month=3, day=10),
            'description': 'حادث مركبة الشركة - إصلاح هيكل وطلاء',
            'claimed_amount': Decimal('15000.00'),
            'approved_amount': Decimal('12000.00'),
            'status': 'paid',
            'submitted_by': admin_user,
            'reviewed_by': admin_user,
            'reviewed_at': now,
            'payment_date': now.date().replace(month=4, day=1),
        },
        {
            'claim_number': 'CLM-2025-003',
            'policy_idx': 0,
            'claim_type': 'partial',
            'incident_date': now.date().replace(month=5, day=5),
            'description': 'طلب تعويض عن مصاريف فحوصات طبية متقدمة',
            'claimed_amount': Decimal('8000.00'),
            'approved_amount': Decimal('0'),
            'status': 'under_review',
            'submitted_by': admin_user,
            'reviewed_by': None,
            'reviewed_at': None,
            'payment_date': None,
        },
        {
            'claim_number': 'CLM-2025-004',
            'policy_idx': 1,
            'claim_type': 'full',
            'incident_date': now.date().replace(month=4, day=20),
            'description': 'طلب تعويض تأمين حياة - وفاة موظف سابق',
            'claimed_amount': Decimal('500000.00'),
            'approved_amount': Decimal('0'),
            'status': 'submitted',
            'submitted_by': admin_user,
            'reviewed_by': None,
            'reviewed_at': None,
            'payment_date': None,
        },
    ]

    for data in claims_data:
        policy = created_policies[data['policy_idx']]
        claim, created = InsuranceClaim.objects.get_or_create(
            claim_number=data['claim_number'],
            defaults={
                'policy': policy,
                'claim_type': data['claim_type'],
                'incident_date': data['incident_date'],
                'description': data['description'],
                'claimed_amount': data['claimed_amount'],
                'approved_amount': data['approved_amount'],
                'status': data['status'],
                'submitted_by': data['submitted_by'],
                'reviewed_by': data['reviewed_by'],
                'reviewed_at': data['reviewed_at'],
                'payment_date': data['payment_date'],
                'notes': '',
            },
        )
        if created:
            created_counts['claims'] += 1
            print(f'  Created claim: {claim.claim_number} - {claim.get_status_display()}')
        else:
            print(f'  Skipped (exists): {claim.claim_number}')

    # =============================================
    # 3. Create 6 Pension Records
    # =============================================
    pensions_data = [
        {
            'employee_idx': 0,
            'pension_scheme': 'التأمينات الاجتماعية (GOSI)',
            'contribution_type': 'both',
            'monthly_contribution': Decimal('2250.00'),
            'employer_contribution': Decimal('1350.00'),
            'employee_contribution': Decimal('900.00'),
            'start_date': now.date().replace(year=now.year - 3, month=1, day=1),
            'status': 'active',
            'total_contributions': Decimal('81000.00'),
            'last_contribution_date': now.date(),
        },
        {
            'employee_idx': 1,
            'pension_scheme': 'التأمينات الاجتماعية (GOSI)',
            'contribution_type': 'both',
            'monthly_contribution': Decimal('1800.00'),
            'employer_contribution': Decimal('1080.00'),
            'employee_contribution': Decimal('720.00'),
            'start_date': now.date().replace(year=now.year - 5, month=6, day=1),
            'status': 'active',
            'total_contributions': Decimal('108000.00'),
            'last_contribution_date': now.date(),
        },
        {
            'employee_idx': 2,
            'pension_scheme': 'صندوق التقاعد المدني',
            'contribution_type': 'employer',
            'monthly_contribution': Decimal('1500.00'),
            'employer_contribution': Decimal('1500.00'),
            'employee_contribution': Decimal('0'),
            'start_date': now.date().replace(year=now.year - 10, month=3, day=15),
            'status': 'active',
            'total_contributions': Decimal('180000.00'),
            'last_contribution_date': now.date(),
        },
        {
            'employee_idx': 3,
            'pension_scheme': 'التأمينات الاجتماعية (GOSI)',
            'contribution_type': 'both',
            'monthly_contribution': Decimal('1200.00'),
            'employer_contribution': Decimal('720.00'),
            'employee_contribution': Decimal('480.00'),
            'start_date': now.date().replace(year=now.year - 2, month=9, day=1),
            'status': 'active',
            'total_contributions': Decimal('28800.00'),
            'last_contribution_date': now.date(),
        },
        {
            'employee_idx': 4,
            'pension_scheme': 'صندوق التقاعد العسكري',
            'contribution_type': 'employer',
            'monthly_contribution': Decimal('2000.00'),
            'employer_contribution': Decimal('2000.00'),
            'employee_contribution': Decimal('0'),
            'start_date': now.date().replace(year=now.year - 15, month=1, day=1),
            'end_date': now.date().replace(year=now.year - 1, month=12, day=31),
            'status': 'retired',
            'total_contributions': Decimal('360000.00'),
            'last_contribution_date': now.date().replace(year=now.year - 1, month=12, day=31),
        },
        {
            'employee_idx': 5,
            'pension_scheme': 'التأمينات الاجتماعية (GOSI)',
            'contribution_type': 'both',
            'monthly_contribution': Decimal('900.00'),
            'employer_contribution': Decimal('540.00'),
            'employee_contribution': Decimal('360.00'),
            'start_date': now.date().replace(year=now.year - 1, month=4, day=1),
            'status': 'suspended',
            'total_contributions': Decimal('10800.00'),
            'last_contribution_date': now.date().replace(month=3, day=1),
        },
    ]

    created_pensions = []
    for data in pensions_data:
        idx = data['employee_idx']
        if idx >= len(employees):
            continue
        emp = employees[idx]

        record, created = PensionRecord.objects.get_or_create(
            employee=emp,
            pension_scheme=data['pension_scheme'],
            defaults={
                'contribution_type': data['contribution_type'],
                'monthly_contribution': data['monthly_contribution'],
                'employer_contribution': data['employer_contribution'],
                'employee_contribution': data['employee_contribution'],
                'start_date': data['start_date'],
                'end_date': data.get('end_date'),
                'status': data['status'],
                'total_contributions': data['total_contributions'],
                'last_contribution_date': data['last_contribution_date'],
                'notes': '',
            },
        )
        if created:
            created_counts['pensions'] += 1
            print(f'  Created pension: {emp.full_name} - {record.pension_scheme} ({record.get_status_display()})')
        else:
            print(f'  Skipped (exists): {emp.full_name} - {record.pension_scheme}')
        created_pensions.append(record)

    # =============================================
    # 4. Create 8 Pension Payments
    # =============================================
    payments_data = [
        {'record_idx': 0, 'amount': Decimal('2250.00'), 'month': 1, 'year': now.year, 'status': 'paid'},
        {'record_idx': 0, 'amount': Decimal('2250.00'), 'month': 2, 'year': now.year, 'status': 'paid'},
        {'record_idx': 1, 'amount': Decimal('1800.00'), 'month': 1, 'year': now.year, 'status': 'paid'},
        {'record_idx': 1, 'amount': Decimal('1800.00'), 'month': 2, 'year': now.year, 'status': 'paid'},
        {'record_idx': 2, 'amount': Decimal('1500.00'), 'month': 1, 'year': now.year, 'status': 'paid'},
        {'record_idx': 3, 'amount': Decimal('1200.00'), 'month': 1, 'year': now.year, 'status': 'paid'},
        {'record_idx': 3, 'amount': Decimal('1200.00'), 'month': 2, 'year': now.year, 'status': 'pending'},
        {'record_idx': 5, 'amount': Decimal('900.00'), 'month': 1, 'year': now.year, 'status': 'failed'},
    ]

    for data in payments_data:
        idx = data['record_idx']
        if idx >= len(created_pensions):
            continue
        pension_rec = created_pensions[idx]

        payment, created = PensionPayment.objects.get_or_create(
            pension_record=pension_rec,
            month=data['month'],
            year=data['year'],
            defaults={
                'amount': data['amount'],
                'payment_date': now.date(),
                'payment_method': 'bank_transfer',
                'reference_number': f'REF-{data["year"]}{data["month"]:02d}-{idx + 1}',
                'status': data['status'],
            },
        )
        if created:
            created_counts['payments'] += 1
            print(f'  Created payment: {pension_rec.employee.full_name} - {data["month"]}/{data["year"]} ({payment.get_status_display()})')
        else:
            print(f'  Skipped (exists): {pension_rec.employee.full_name} - {data["month"]}/{data["year"]}')

    # =============================================
    # Summary
    # =============================================
    print('')
    print('=== Seed Summary ===')
    print(f'  Insurance Policies created: {created_counts["policies"]}')
    print(f'  Insurance Claims created: {created_counts["claims"]}')
    print(f'  Pension Records created: {created_counts["pensions"]}')
    print(f'  Pension Payments created: {created_counts["payments"]}')
    print('Done! Insurance & Pension data seeded successfully.')


# Run seed when script is executed
seed_insurance()
