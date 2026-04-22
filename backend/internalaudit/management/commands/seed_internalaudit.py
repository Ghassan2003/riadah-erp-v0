"""
Management command to seed sample Internal Audit data.
Creates AuditPlans, AuditFindings, AuditEvidence, AuditActions, and ComplianceChecks
for development and testing.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from internalaudit.models import (
    AuditPlan,
    AuditFinding,
    AuditEvidence,
    AuditAction,
    ComplianceCheck,
)


class Command(BaseCommand):
    help = 'Seed sample internal audit data for the ERP system'

    def handle(self, *args, **options):
        from users.models import User
        from hr.models import Department

        self.stdout.write('Creating sample Internal Audit data...')

        # Get an admin user
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('  No admin user found. Run seed_users first.'))
            return

        # Get additional users for assignments
        users = list(User.objects.all()[:5])
        if len(users) < 2:
            self.stdout.write(self.style.ERROR('  Not enough users found. Run seed_users first.'))
            return

        # Get departments
        departments = list(Department.objects.all()[:4])

        now = timezone.now()

        # =============================================
        # 1. Create Audit Plans (3)
        # =============================================
        plans_data = [
            {
                'name': 'خطة التدقيق المالي السنوي',
                'description': 'خطة التدقيق المالي الشاملة للسنة المالية',
                'fiscal_year': now.year,
                'department': departments[0] if len(departments) > 0 else None,
                'audit_type': 'financial',
                'status': 'in_progress',
                'start_date': now.date().replace(month=1, day=1),
                'end_date': None,
                'lead_auditor': admin_user,
                'team_members': 'أحمد محمد، سارة علي، خالد عبدالله',
                'scope': 'مراجعة كافة العمليات المالية والتحقق من دقة السجلات',
                'objectives': 'ضمان دقة البيانات المالية والامتثال للأنظمة',
                'risk_level': 'high',
                'budget_hours': Decimal('240.00'),
                'actual_hours': Decimal('120.50'),
            },
            {
                'name': 'تدقيق توافق هيئة الزكاة',
                'description': 'خطة التدقيق للتحقق من التوافق مع متطلبات هيئة الزكاة والضريبة والجمارك',
                'fiscal_year': now.year,
                'department': departments[1] if len(departments) > 1 else None,
                'audit_type': 'compliance',
                'status': 'in_progress',
                'start_date': now.date().replace(month=3, day=1),
                'end_date': None,
                'lead_auditor': users[1] if len(users) > 1 else admin_user,
                'team_members': 'فاطمة أحمد، عبدالرحمن سعيد',
                'scope': 'مراجعة تقارير ضريبة القيمة المضافة وعمليات تحصيل الزكاة',
                'objectives': 'ضمان التوافق الكامل مع متطلبات هيئة الزكاة',
                'risk_level': 'critical',
                'budget_hours': Decimal('160.00'),
                'actual_hours': Decimal('85.00'),
            },
            {
                'name': 'تدقيق تقنية المعلومات',
                'description': 'خطة تدقيق الأنظمة التقنية والبنية التحتية لتقنية المعلومات',
                'fiscal_year': now.year,
                'department': departments[2] if len(departments) > 2 else None,
                'audit_type': 'it',
                'status': 'draft',
                'start_date': now.date().replace(month=6, day=1),
                'end_date': None,
                'lead_auditor': users[0] if len(users) > 0 else admin_user,
                'team_members': 'محمد سالم، نورة عبدالعزيز',
                'scope': 'مراجعة سياسات أمن المعلومات وأنظمة النسخ الاحتياطي',
                'objectives': 'تقييم كفاءة البنية التحتية التقنية وأمن البيانات',
                'risk_level': 'medium',
                'budget_hours': Decimal('120.00'),
                'actual_hours': Decimal('0.00'),
            },
        ]

        plans = []
        for data in plans_data:
            plan, created = AuditPlan.objects.get_or_create(
                name=data['name'],
                fiscal_year=data['fiscal_year'],
                defaults=data,
            )
            plans.append(plan)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created plan: {plan.name}'))
            else:
                self.stdout.write(f'  Skipped (exists): {plan.name}')

        # =============================================
        # 2. Create Audit Findings (10)
        # =============================================
        findings_data = [
            {
                'plan_idx': 0, 'finding_number': 'FA-2025-001',
                'title': 'ضعف في إجراءات الموافقة على المصروفات',
                'description': 'تم رصد عدة مصروفات تمت الموافقة عليها دون اتباع الإجراءات المعتمدة',
                'severity': 'high', 'category': 'control',
                'condition': 'لا تتطلب بعض المصروفات موافقة ثنائية حسب اللائحة المالية',
                'criteria': 'يجب أن تحصل جميع المصروفات التي تتجاوز 5000 ريال على موافقة ثنائية',
                'cause': 'عدم تطبيق السياسة المالية بشكل متسق من قبل الموظفين المختصين',
                'effect': 'احتمالية وجود مصروفات غير مشروعة أو غير ضرورية',
                'recommendation': 'تفعيل نظام الموافقات الإلكترونية وإلزام جميع الأقسام بالتطبيق',
                'status': 'open',
                'responsible_user_idx': 1,
                'due_date_offset_days': 30,
            },
            {
                'plan_idx': 0, 'finding_number': 'FA-2025-002',
                'title': 'تأخر في تسجيل القيود المحاسبية',
                'description': 'تأخر تسجيل بعض القيود المحاسبية لأكثر من شهر من تاريخ العملية',
                'severity': 'medium', 'category': 'operational',
                'condition': 'تسجيل القيود المحاسبية يتم بشكل دوري وليس يومياً',
                'criteria': 'يجب تسجيل جميع القيود المحاسبية خلال 3 أيام عمل من تاريخ العملية',
                'cause': 'نقص في الكوادر المحاسبية وتكدس المعاملات',
                'effect': 'تأخر في إعداد التقارير المالية وعدم دقة البيانات الفورية',
                'recommendation': 'توظيف محاسب إضافي وتطبيق نظام إدخال يومي للقيود',
                'status': 'in_progress',
                'responsible_user_idx': 0,
                'due_date_offset_days': 45,
            },
            {
                'plan_idx': 0, 'finding_number': 'FA-2025-003',
                'title': 'عدم مطابقة أرصدة البنوك شهرياً',
                'description': 'لم يتم إجراء مطابقة بنكية لعدة أشهر متتالية',
                'severity': 'high', 'category': 'financial',
                'condition': 'لا يتم إجراء مطابقة بنكية بشكل شهري',
                'criteria': 'يجب إجراء مطابقة بنكية في نهاية كل شهر مالي',
                'cause': 'غياب إجراء واضح وتكليف محدد بالمسؤولية',
                'effect': 'احتمالية عدم اكتشاف أخطاء أو تلاعب في الحسابات البنكية',
                'recommendation': 'تعيين مسؤول للمطابقة البنكية وإعداد نموذج مطابقة معتمد',
                'status': 'open',
                'responsible_user_idx': 1,
                'due_date_offset_days': 15,
            },
            {
                'plan_idx': 0, 'finding_number': 'FA-2025-004',
                'title': 'نقص في التوثيق supporting documents',
                'description': 'بعض المعاملات المالية تفتقر إلى المستندات المؤيدة الكاملة',
                'severity': 'low', 'category': 'control',
                'condition': 'توجد معاملات بدون فواتير أو أوامر شراء معتمدة',
                'criteria': 'يجب أن تكون جميع المعاملات المالية مؤيدة بمستندات كاملة',
                'cause': 'إهمال في جمع المستندات من قبل الموظفين المعنيين',
                'effect': 'صعوبة في التحقق من صحة المعاملات أثناء التدقيق',
                'recommendation': 'تطبيق سياسة عدم صرف أي مبلغ دون مستندات مؤيدة',
                'status': 'resolved',
                'responsible_user_idx': 0,
                'due_date_offset_days': -10,
            },
            {
                'plan_idx': 1, 'finding_number': 'ZT-2025-001',
                'title': 'عدم تقديم إقرارات ضريبة القيمة المضافة في الموعد',
                'description': 'تأخر في تقديم إقرار ضريبة القيمة المضافة للربع الأول',
                'severity': 'critical', 'category': 'compliance',
                'condition': 'تم تقديم الإقرار بعد الموعد النهائي بـ 15 يوماً',
                'criteria': 'يجب تقديم إقرارات ضريبة القيمة المضافة خلال 30 يوماً من نهاية كل ربع',
                'cause': 'عدم تنظيم جدول زمني واضح للاستعدادات الضريبية',
                'effect': 'تعرض الشركة لغرامات تأخير ومخالفة نظامية',
                'recommendation': 'إعداد تقويم سنوي لمواعيد التقديم وتعيين منسق ضريبي',
                'status': 'open',
                'responsible_user_idx': 2 if len(users) > 2 else 1,
                'due_date_offset_days': 20,
            },
            {
                'plan_idx': 1, 'finding_number': 'ZT-2025-002',
                'title': 'عدم تطبيق نسبة الضريبة الصحيحة على بعض الخدمات',
                'description': 'تم تطبيق نسبة 5% بدلاً من 15% على خدمات خاضعة للنسبة المعدلة',
                'severity': 'high', 'category': 'financial',
                'condition': 'بعض الخدمات تم احتساب ضريبتها بنسبة خاطئة',
                'criteria': 'يجب تطبيق نسبة 15% على جميع الخدمات المحددة في اللائحة',
                'cause': 'عدم تحديث جدول الضريبة في النظام المحاسبي',
                'effect': 'نقص في تحصيل الضريبة المستحقة وغرامات محتملة',
                'recommendation': 'تحديث النظام المحاسبي بالنسب الجديدة وتدريب الموظفين',
                'status': 'in_progress',
                'responsible_user_idx': 1,
                'due_date_offset_days': 25,
            },
            {
                'plan_idx': 1, 'finding_number': 'ZT-2025-003',
                'title': 'غياب سجل ضريبي إلكتروني متكامل',
                'description': 'السجل الضريبي لا يتوافق مع المتطلبات الإلكترونية لهيئة الزكاة',
                'severity': 'medium', 'category': 'compliance',
                'condition': 'السجل الضريبي يدار يدوياً وغير مرتبط بالنظام',
                'criteria': 'يجب الاحتفاظ بسجل ضريبي إلكتروني متوافق مع متطلبات الهيئة',
                'cause': 'عدم الانتقال للنظام الإلكتروني المطلوب',
                'effect': 'صعوبة في تقديم البيانات للهيئة عند الطلب',
                'recommendation': 'تنفيذ سجل ضريبي إلكتروني متكامل مع النظام المحاسبي',
                'status': 'open',
                'responsible_user_idx': 0,
                'due_date_offset_days': 60,
            },
            {
                'plan_idx': 0, 'finding_number': 'FA-2025-005',
                'title': 'عدم تطبيق سياسة الإجازات بشكل سليم',
                'description': 'بعض الموظفين تجاوزوا رصيد إجازاتهم دون موافقة رسمية',
                'severity': 'medium', 'category': 'operational',
                'condition': 'توجد حالات تجاوز رصيد الإجازات دون تسوية',
                'criteria': 'لا يجوز تجاوز رصيد الإجازات إلا بموافقة خطية من الإدارة',
                'cause': 'عدم ربط نظام الإجازات بنظام الرواتب بشكل كامل',
                'effect': 'التزامات مالية غير محسوبة على الشركة ومخالفة لنظام العمل',
                'recommendation': 'ربط نظام الإجازات بنظام الرواتب وإصدار تقارير شهرية',
                'status': 'resolved',
                'responsible_user_idx': 1,
                'due_date_offset_days': -5,
            },
            {
                'plan_idx': 0, 'finding_number': 'FA-2025-006',
                'title': 'ضعف في سياسة صرف السلف',
                'description': 'صرف سلف تتجاوز الحد المسموح به في اللائحة المالية',
                'severity': 'low', 'category': 'control',
                'condition': 'تم صرف سلف تتجاوز 3 أشهر من الراتب الأساسي',
                'criteria': 'لا يجوز أن تتجاوز السلفة 3 أشهر من الراتب الأساسي',
                'cause': 'عدم التحقق من الرصيد في النظام قبل الموافقة',
                'effect': 'تراكم ديون على الموظفين وصعوبة التحصيل',
                'recommendation': 'تفعيل تحقق تلقائي من سقف السلف في النظام',
                'status': 'closed',
                'responsible_user_idx': 0,
                'due_date_offset_days': -20,
            },
            {
                'plan_idx': 1, 'finding_number': 'ZT-2025-004',
                'title': 'عدم الاحتفاظ بفواتير إلكترونية صالحة',
                'description': 'بعض الفواتير الإلكترونية لا تتوافق مع متطلبات فاتورة هيئة الزكاة',
                'severity': 'medium', 'category': 'compliance',
                'condition': 'فواتير صادرة لا تحمل الرمز الضريبي أو بيانات البائع الكاملة',
                'criteria': 'يجب أن تتضمن جميع الفواتير البيانات المطلوبة من هيئة الزكاة',
                'cause': 'عدم تحديث قالب الفاتورة الإلكترونية',
                'effect': 'رفض الفواتير من قبل العملاء ومشاكل في تقديم الإقرارات',
                'recommendation': 'تحديث قالب الفاتورة الإلكترونية وإلزام جميع الأقسام',
                'status': 'open',
                'responsible_user_idx': 2 if len(users) > 2 else 1,
                'due_date_offset_days': 35,
            },
        ]

        findings = []
        finding_count = 0
        for data in findings_data:
            plan_idx = data['plan_idx']
            if plan_idx >= len(plans):
                continue
            plan = plans[plan_idx]

            resp_idx = data.get('responsible_user_idx', 0)
            responsible = users[resp_idx] if resp_idx < len(users) else admin_user
            due_date = now.date() + __import__('datetime').timedelta(days=data['due_date_offset_days'])

            resolved_at = None
            resolved_by = None
            if data['status'] in ('resolved', 'closed'):
                resolved_at = now - __import__('datetime').timedelta(days=5)
                resolved_by = admin_user

            finding, created = AuditFinding.objects.get_or_create(
                audit_plan=plan,
                finding_number=data['finding_number'],
                defaults={
                    'title': data['title'],
                    'description': data['description'],
                    'severity': data['severity'],
                    'category': data['category'],
                    'condition': data['condition'],
                    'criteria': data['criteria'],
                    'cause': data['cause'],
                    'effect': data['effect'],
                    'recommendation': data['recommendation'],
                    'status': data['status'],
                    'responsible_person': responsible,
                    'due_date': due_date,
                    'resolved_at': resolved_at,
                    'resolved_by': resolved_by,
                },
            )
            findings.append(finding)
            if created:
                finding_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created finding: {finding.finding_number} - {finding.title}'))
            else:
                self.stdout.write(f'  Skipped (exists): {finding.finding_number}')

        # =============================================
        # 3. Create Audit Evidence (12)
        # =============================================
        evidence_data = [
            {'finding_idx': 0, 'evidence_type': 'document', 'description': 'نسخ من المصروفات غير الموافق عليها ثنائياً'},
            {'finding_idx': 0, 'evidence_type': 'data_analysis', 'description': 'تحليل إحصائي للمصروفات المعتمدة بوزن واحد'},
            {'finding_idx': 1, 'evidence_type': 'data_analysis', 'description': 'تقرير يوضح الفجوة الزمنية بين تاريخ العملية وتاريخ التسجيل'},
            {'finding_idx': 1, 'evidence_type': 'document', 'description': 'قائمة بالقيود المتأخرة ومدة التأخير لكل قيد'},
            {'finding_idx': 2, 'evidence_type': 'document', 'description': 'كشوف حسابات بنكية لآخر 6 أشهر'},
            {'finding_idx': 2, 'evidence_type': 'interview_observation', 'description': 'مقابلة مع المحاسب الرئيسي بخصوص المطابقة البنكية'},
            {'finding_idx': 3, 'evidence_type': 'document', 'description': 'نماذج معاملات بدون مستندات مؤيدة'},
            {'finding_idx': 4, 'evidence_type': 'document', 'description': 'إشعار تأخير من هيئة الزكاة بخصوص إقرار ضريبة القيمة المضافة'},
            {'finding_idx': 4, 'evidence_type': 'document', 'description': 'خطاب غرامة تأخير من الهيئة'},
            {'finding_idx': 5, 'evidence_type': 'data_analysis', 'description': 'تحليل الفروقات في نسب الضريبة المطبقة'},
            {'finding_idx': 7, 'evidence_type': 'data_analysis', 'description': 'تقرير رصيد الإجازات للموظفين المتجاوزين'},
            {'finding_idx': 9, 'evidence_type': 'document', 'description': 'عينة من الفواتير الإلكترونية غير المتوافقة'},
        ]

        evidence_count = 0
        for data in evidence_data:
            f_idx = data['finding_idx']
            if f_idx >= len(findings):
                continue
            finding = findings[f_idx]

            evidence, created = AuditEvidence.objects.get_or_create(
                finding=finding,
                description=data['description'],
                defaults={
                    'evidence_type': data['evidence_type'],
                    'collected_by': admin_user,
                },
            )
            if created:
                evidence_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created evidence: {evidence.get_evidence_type_display()} - {evidence.description[:50]}'))
            else:
                self.stdout.write(f'  Skipped (exists): {evidence.description[:50]}')

        # =============================================
        # 4. Create Audit Actions (8)
        # =============================================
        actions_data = [
            {
                'finding_idx': 0, 'action_number': 'ACT-FA-001-01',
                'description': 'تفعيل نظام الموافقات الإلكترونية في برنامج المحاسبة',
                'assigned_user_idx': 0, 'priority': 'high', 'status': 'in_progress',
                'due_date_offset_days': 20,
            },
            {
                'finding_idx': 0, 'action_number': 'ACT-FA-001-02',
                'description': 'إصدار تعميم بإلزام جميع الأقسام بنظام الموافقات الثنائية',
                'assigned_user_idx': 1, 'priority': 'high', 'status': 'pending',
                'due_date_offset_days': 10,
            },
            {
                'finding_idx': 1, 'action_number': 'ACT-FA-002-01',
                'description': 'توظيف محاسب إضافي لقسم القيود المحاسبية',
                'assigned_user_idx': 1, 'priority': 'medium', 'status': 'in_progress',
                'due_date_offset_days': 30,
            },
            {
                'finding_idx': 2, 'action_number': 'ACT-FA-003-01',
                'description': 'إعداد نموذج مطابقة بنكية معتمد وتعيين مسؤول',
                'assigned_user_idx': 0, 'priority': 'high', 'status': 'pending',
                'due_date_offset_days': 15,
            },
            {
                'finding_idx': 4, 'action_number': 'ACT-ZT-001-01',
                'description': 'إعداد تقويم سنوي لمواعيد تقديم الإقرارات الضريبية',
                'assigned_user_idx': 2 if len(users) > 2 else 1, 'priority': 'critical', 'status': 'in_progress',
                'due_date_offset_days': 10,
            },
            {
                'finding_idx': 5, 'action_number': 'ACT-ZT-002-01',
                'description': 'تحديث جدول نسب الضريبة في النظام المحاسبي',
                'assigned_user_idx': 1, 'priority': 'high', 'status': 'pending',
                'due_date_offset_days': 15,
            },
            {
                'finding_idx': 3, 'action_number': 'ACT-FA-004-01',
                'description': 'إصدار سياسة المستندات المؤيدة الإلزامية',
                'assigned_user_idx': 0, 'priority': 'medium', 'status': 'completed',
                'due_date_offset_days': -5,
            },
            {
                'finding_idx': 7, 'action_number': 'ACT-FA-005-01',
                'description': 'ربط نظام الإجازات بنظام الرواتب إلكترونياً',
                'assigned_user_idx': 1, 'priority': 'medium', 'status': 'completed',
                'due_date_offset_days': -3,
            },
        ]

        action_count = 0
        for data in actions_data:
            f_idx = data['finding_idx']
            if f_idx >= len(findings):
                continue
            finding = findings[f_idx]

            assign_idx = data.get('assigned_user_idx', 0)
            assigned_to = users[assign_idx] if assign_idx < len(users) else admin_user
            due_date = now.date() + __import__('datetime').timedelta(days=data['due_date_offset_days'])

            completion_date = None
            verified_by = None
            verified_at = None
            if data['status'] == 'completed':
                completion_date = now.date() - __import__('datetime').timedelta(days=2)
                verified_by = admin_user
                verified_at = now - __import__('datetime').timedelta(days=1)

            action, created = AuditAction.objects.get_or_create(
                finding=finding,
                action_number=data['action_number'],
                defaults={
                    'description': data['description'],
                    'assigned_to': assigned_to,
                    'priority': data['priority'],
                    'due_date': due_date,
                    'status': data['status'],
                    'completion_date': completion_date,
                    'verified_by': verified_by,
                    'verified_at': verified_at,
                },
            )
            if created:
                action_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created action: {action.action_number} - {action.description[:50]}'))
            else:
                self.stdout.write(f'  Skipped (exists): {action.action_number}')

        # =============================================
        # 5. Create Compliance Checks (5)
        # =============================================
        compliance_data = [
            {
                'name': 'فحص ضريبة القيمة المضافة',
                'regulation': 'نظام ضريبة القيمة المضافة',
                'description': 'فحص دوري للتوافق مع متطلبات ضريبة القيمة المضافة',
                'department': departments[1] if len(departments) > 1 else None,
                'frequency': 'quarterly',
                'last_check': now.date() - __import__('datetime').timedelta(days=30),
                'next_check': now.date() + __import__('datetime').timedelta(days=60),
                'responsible': users[1] if len(users) > 1 else admin_user,
                'status': 'partially_compliant',
                'findings': 'بعض الفواتير لا تتوافق مع المتطلبات. تم تسجيل ملاحظات في خطة تدقيق هيئة الزكاة.',
            },
            {
                'name': 'فحص نظام العمل والعمال',
                'regulation': 'نظام العمل السعودي',
                'description': 'فحص التوافق مع متطلبات نظام العمل والعمال',
                'department': departments[0] if len(departments) > 0 else None,
                'frequency': 'semi_annual',
                'last_check': now.date() - __import__('datetime').timedelta(days=60),
                'next_check': now.date() + __import__('datetime').timedelta(days=120),
                'responsible': admin_user,
                'status': 'compliant',
                'findings': 'لا توجد ملاحظات جوهرية. جميع السجلات متوافقة.',
            },
            {
                'name': 'فحص أنظمة مكافحة غسل الأموال',
                'regulation': 'نظام مكافحة غسل الأموال',
                'description': 'فحص التوافق مع متطلبات أنظمة مكافحة غسل الأموال وتمويل الإرهاب',
                'department': departments[1] if len(departments) > 1 else None,
                'frequency': 'annual',
                'last_check': now.date() - __import__('datetime').timedelta(days=180),
                'next_check': now.date() + __import__('datetime').timedelta(days=185),
                'responsible': users[0] if len(users) > 0 else admin_user,
                'status': 'compliant',
                'findings': 'جميع الإجراءات المطلوبة مطبقة بشكل سليم.',
            },
            {
                'name': 'فحص سياسات أمن المعلومات',
                'regulation': 'السياسة الوطنية لأمن المعلومات',
                'description': 'فحص التوافق مع سياسات وأطر أمن المعلومات المعتمدة',
                'department': departments[2] if len(departments) > 2 else None,
                'frequency': 'quarterly',
                'last_check': None,
                'next_check': now.date() + __import__('datetime').timedelta(days=30),
                'responsible': users[0] if len(users) > 0 else admin_user,
                'status': 'not_checked',
                'findings': '',
            },
            {
                'name': 'فحص اللوائح المالية الداخلية',
                'regulation': 'اللائحة المالية والprocurement الداخلية',
                'description': 'فحص دوري للتوافق مع اللوائح المالية والشراء الداخلية',
                'department': departments[0] if len(departments) > 0 else None,
                'frequency': 'monthly',
                'last_check': now.date() - __import__('datetime').timedelta(days=15),
                'next_check': now.date() + __import__('datetime').timedelta(days=15),
                'responsible': users[1] if len(users) > 1 else admin_user,
                'status': 'non_compliant',
                'findings': 'تم رصد مخالفات في إجراءات الشراء المباشر. يتطلب مراجعة فورية.',
            },
        ]

        compliance_count = 0
        for data in compliance_data:
            check, created = ComplianceCheck.objects.get_or_create(
                name=data['name'],
                regulation=data['regulation'],
                defaults=data,
            )
            if created:
                compliance_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created compliance check: {check.name}'))
            else:
                self.stdout.write(f'  Skipped (exists): {check.name}')

        # =============================================
        # Summary
        # =============================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Seed Summary ==='))
        self.stdout.write(f'  Audit Plans created: {sum(1 for p in plans if p.created_at) or len(plans)} (checked via get_or_create)')
        self.stdout.write(f'  Audit Findings created: {finding_count}')
        self.stdout.write(f'  Audit Evidence created: {evidence_count}')
        self.stdout.write(f'  Audit Actions created: {action_count}')
        self.stdout.write(f'  Compliance Checks created: {compliance_count}')
        self.stdout.write(self.style.SUCCESS('Done! Internal Audit data seeded successfully.'))
