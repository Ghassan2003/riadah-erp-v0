"""
أمر إدارة (Management command) لبذر بيانات إدارة علاقات العملاء (CRM).
ينشئ جهات اتصال، فرص بيع، أنشطة، شرائح عملاء، وحملات تسويقية لأغراض التطوير والاختبار.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import (
    Contact,
    Lead,
    LeadActivity,
    CustomerSegment,
    Campaign,
    CampaignActivity,
)


class Command(BaseCommand):
    help = 'بذر بيانات عينة لإدارة علاقات العملاء (CRM) في نظام ERP'

    def handle(self, *args, **options):
        from users.models import User

        self.stdout.write('جارٍ إنشاء بيانات عينة لإدارة علاقات العملاء...')

        # الحصول على مستخدم مسؤول
        admin_user = User.objects.filter(role='admin').first()

        # =============================================
        # 1. إنشاء جهات الاتصال (8 جهات)
        # =============================================
        contacts_data = [
            {'first_name': 'أحمد', 'last_name': 'العمري', 'email': 'ahmed@company.com', 'phone': '0111234567', 'mobile': '0551234567', 'company': 'شركة التقنية المتقدمة', 'position': 'مدير تقنية المعلومات', 'source': 'website', 'status': 'active'},
            {'first_name': 'سارة', 'last_name': 'القحطاني', 'email': 'sara@business.com', 'phone': '0112345678', 'mobile': '0552345678', 'company': 'مؤسسة الابتكار', 'position': 'مديرة التسويق', 'source': 'referral', 'status': 'active'},
            {'first_name': 'محمد', 'last_name': 'الزهراني', 'email': 'mohammed@enterprise.com', 'phone': '0113456789', 'mobile': '0553456789', 'company': 'شركة المشاريع الكبرى', 'position': 'المدير التنفيذي', 'source': 'event', 'status': 'active'},
            {'first_name': 'فاطمة', 'last_name': 'الشمري', 'email': 'fatima@startup.com', 'phone': '0114567890', 'mobile': '0554567890', 'company': 'شركة الناشئة', 'position': 'مديرة المالية', 'source': 'social_media', 'status': 'active'},
            {'first_name': 'خالد', 'last_name': 'الدوسري', 'email': 'khaled@corp.com', 'phone': '0115678901', 'mobile': '0555678901', 'company': 'مجموعة الدوسري التجارية', 'position': 'مدير المشاريع', 'source': 'phone', 'status': 'active'},
            {'first_name': 'نورة', 'last_name': 'العتيبي', 'email': 'noura@digital.com', 'phone': '0116789012', 'mobile': '0556789012', 'company': 'وكالة الرقمية', 'position': 'مديرة العمليات', 'source': 'email', 'status': 'active'},
            {'first_name': 'عبدالله', 'last_name': 'المطيري', 'email': 'abdullah@trade.com', 'phone': '0117890123', 'mobile': '0557890123', 'company': 'شركة التجارة الدولية', 'position': 'مدير المبيعات', 'source': 'website', 'status': 'active'},
            {'first_name': 'ريم', 'last_name': 'الحربي', 'email': 'reem@services.com', 'phone': '0118901234', 'mobile': '0558901234', 'company': 'شركة الخدمات المتكاملة', 'position': 'مديرة الموارد البشرية', 'source': 'referral', 'status': 'inactive'},
        ]

        contacts = []
        contact_count = 0
        for data in contacts_data:
            contact, created = Contact.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                    'mobile': data['mobile'],
                    'company': data['company'],
                    'position': data['position'],
                    'source': data['source'],
                    'status': data['status'],
                    'assigned_to': admin_user,
                },
            )
            contacts.append(contact)
            if created:
                contact_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء جهة اتصال: {contact.first_name} {contact.last_name} - {contact.company}'))
            else:
                self.stdout.write(f'  تم التخطي (موجود): {contact.first_name} {contact.last_name}')

        # =============================================
        # 2. إنشاء فرص البيع (6 فرص في مراحل مختلفة)
        # =============================================
        leads_data = [
            {'contact_idx': 0, 'title': 'نظام إدارة الموارد - شركة التقنية المتقدمة', 'value': 150000, 'probability': 75, 'status': 'proposal', 'pipeline_stage': 'proposal', 'source': 'website', 'expected_close_days': 30},
            {'contact_idx': 1, 'title': 'حملة تسويقية رقمية - مؤسسة الابتكار', 'value': 45000, 'probability': 90, 'status': 'negotiation', 'pipeline_stage': 'negotiation', 'source': 'referral', 'expected_close_days': 15},
            {'contact_idx': 2, 'title': 'تحول رقمي شامل - شركة المشاريع الكبرى', 'value': 500000, 'probability': 30, 'status': 'qualified', 'pipeline_stage': 'qualified', 'source': 'event', 'expected_close_days': 90},
            {'contact_idx': 3, 'title': 'تطبيق جوال - شركة الناشئة', 'value': 80000, 'probability': 60, 'status': 'contacted', 'pipeline_stage': 'lead', 'source': 'social_media', 'expected_close_days': 45},
            {'contact_idx': 4, 'title': 'نظام إدارة المخزون - مجموعة الدوسري', 'value': 120000, 'probability': 100, 'status': 'won', 'pipeline_stage': 'closed_won', 'source': 'phone', 'expected_close_days': -10},
            {'contact_idx': 5, 'title': 'تصميم بوابة إلكترونية - وكالة الرقمية', 'value': 35000, 'probability': 0, 'status': 'lost', 'pipeline_stage': 'closed_lost', 'source': 'email', 'expected_close_days': -5, 'lost_reason': 'تم اختيار منافس بسعر أقل'},
        ]

        leads = []
        lead_count = 0
        for data in leads_data:
            idx = data['contact_idx']
            if idx >= len(contacts):
                continue
            contact = contacts[idx]

            from datetime import timedelta
            expected_close = timezone.now().date() + timedelta(days=data['expected_close_days'])

            lead, created = Lead.objects.get_or_create(
                title=data['title'],
                defaults={
                    'contact': contact,
                    'value': Decimal(str(data['value'])),
                    'probability': data['probability'],
                    'status': data['status'],
                    'pipeline_stage': data['pipeline_stage'],
                    'source': data['source'],
                    'expected_close_date': expected_close,
                    'assigned_to': admin_user,
                    'lost_reason': data.get('lost_reason', ''),
                    'notes': f'فرصة بيع لـ {contact.company}',
                },
            )
            leads.append(lead)
            if created:
                lead_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء فرصة بيع: {lead.title} ({lead.get_status_display()}) - {lead.value} ريال'))
            else:
                self.stdout.write(f'  تم التخطي (موجود): {lead.title}')

        # =============================================
        # 3. إنشاء أنشطة الفرص (10 أنشطة)
        # =============================================
        activities_data = [
            {'lead_idx': 0, 'activity_type': 'call', 'subject': 'مكالمة أولية لمناقشة المتطلبات', 'scheduled_days': -5, 'completed': True},
            {'lead_idx': 0, 'activity_type': 'meeting', 'subject': 'اجتماع عرض العرض الفني', 'scheduled_days': -2, 'completed': True},
            {'lead_idx': 0, 'activity_type': 'email', 'subject': 'إرسال عرض السعر', 'scheduled_days': -1, 'completed': True},
            {'lead_idx': 1, 'activity_type': 'call', 'subject': 'متابعة مفاوضات الحملة التسويقية', 'scheduled_days': -3, 'completed': True},
            {'lead_idx': 1, 'activity_type': 'meeting', 'subject': 'اجتماع تفاوض نهائي', 'scheduled_days': 2, 'completed': False},
            {'lead_idx': 2, 'activity_type': 'meeting', 'subject': 'اجتماع تقديم حلول التحول الرقمي', 'scheduled_days': -10, 'completed': True},
            {'lead_idx': 2, 'activity_type': 'task', 'subject': 'إعداد دراسة جدوى شاملة', 'scheduled_days': 5, 'completed': False},
            {'lead_idx': 3, 'activity_type': 'call', 'subject': 'مكالمة استكشافية أولية', 'scheduled_days': -7, 'completed': True},
            {'lead_idx': 3, 'activity_type': 'email', 'subject': 'إرسال معلومات تعريفية بالشركة', 'scheduled_days': -5, 'completed': True},
            {'lead_idx': 3, 'activity_type': 'meeting', 'subject': 'اجتماع مناقشة متطلبات التطبيق', 'scheduled_days': 7, 'completed': False},
        ]

        activity_count = 0
        for data in activities_data:
            idx = data['lead_idx']
            if idx >= len(leads):
                continue
            lead = leads[idx]

            from datetime import timedelta
            scheduled_at = timezone.now() + timedelta(days=data['scheduled_days'])

            activity, created = LeadActivity.objects.get_or_create(
                lead=lead,
                subject=data['subject'],
                defaults={
                    'activity_type': data['activity_type'],
                    'description': data['subject'],
                    'scheduled_at': scheduled_at,
                    'completed': data['completed'],
                    'completed_by': admin_user if data['completed'] else None,
                },
            )
            if created:
                activity_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء نشاط: {activity.subject} ({activity.get_activity_type_display()})'))
            else:
                self.stdout.write(f'  تم التخطي (موجود): {activity.subject}')

        # =============================================
        # 4. إنشاء شرائح العملاء (3 شرائح)
        # =============================================
        segments_data = [
            {
                'name': 'عملاء VIP',
                'description': 'العملاء ذوو القيمة العالية والصفقات الكبرى',
                'criteria': {'min_value': 100000, 'status': 'won'},
                'customer_count': 15,
                'discount_percentage': Decimal('10.00'),
                'is_active': True,
            },
            {
                'name': 'عملاء محتملون',
                'description': 'العملاء الجدد في مراحل مبكرة من خط المبيعات',
                'criteria': {'status': ['new', 'contacted']},
                'customer_count': 42,
                'discount_percentage': Decimal('5.00'),
                'is_active': True,
            },
            {
                'name': 'شركاء استراتيجيون',
                'description': 'الشركات التي نتعامل معها في مشاريع طويلة الأمد',
                'criteria': {'min_projects': 3, 'min_value': 500000},
                'customer_count': 8,
                'discount_percentage': Decimal('15.00'),
                'is_active': True,
            },
        ]

        segment_count = 0
        for data in segments_data:
            segment, created = CustomerSegment.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'criteria': data['criteria'],
                    'customer_count': data['customer_count'],
                    'discount_percentage': data['discount_percentage'],
                    'is_active': data['is_active'],
                },
            )
            if created:
                segment_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء شريحة عملاء: {segment.name}'))
            else:
                self.stdout.write(f'  تم التخطي (موجود): {segment.name}')

        # =============================================
        # 5. إنشاء الحملات التسويقية (2 حملات مع أنشطة)
        # =============================================
        from datetime import timedelta

        campaigns_data = [
            {
                'name': 'حملة إطلاق منتج 2025',
                'description': 'حملة تسويقية شاملة لإطلاق المنتج الجديد في السوق المحلي',
                'campaign_type': 'social_media',
                'status': 'active',
                'start_date': timezone.now().date() - timedelta(days=15),
                'end_date': timezone.now().date() + timedelta(days=30),
                'budget': Decimal('50000'),
                'actual_cost': Decimal('18500'),
                'target_audience': 'شركات تقنية متوسطة إلى كبيرة',
            },
            {
                'name': 'حملة البريد الإلكتروني - الربع الأول',
                'description': 'حملة بريد إلكتروني موجهة للعملاء المحتملين',
                'campaign_type': 'email',
                'status': 'active',
                'start_date': timezone.now().date() - timedelta(days=7),
                'end_date': timezone.now().date() + timedelta(days=60),
                'budget': Decimal('15000'),
                'actual_cost': Decimal('3200'),
                'target_audience': 'مدراء المعلومات والتقنية في القطاع الخاص',
            },
        ]

        campaigns = []
        campaign_count = 0
        for data in campaigns_data:
            campaign, created = Campaign.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'campaign_type': data['campaign_type'],
                    'status': data['status'],
                    'start_date': data['start_date'],
                    'end_date': data['end_date'],
                    'budget': data['budget'],
                    'actual_cost': data['actual_cost'],
                    'target_audience': data['target_audience'],
                    'assigned_to': admin_user,
                },
            )
            campaigns.append(campaign)
            if created:
                campaign_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء حملة تسويقية: {campaign.name} ({campaign.get_campaign_type_display()})'))
            else:
                self.stdout.write(f'  تم التخطي (موجود): {campaign.name}')

        # إنشاء أنشطة الحملات
        campaign_activities_data = [
            # أنشطة حملة إطلاق منتج 2025
            {'campaign_idx': 0, 'activity_type': 'email_sent', 'contact_idx': 0, 'description': 'إرسال دعوة لفعالية الإطلاق', 'days_ago': 12},
            {'campaign_idx': 0, 'activity_type': 'email_sent', 'contact_idx': 1, 'description': 'إرسال نشرة تعريفية بالمنتج', 'days_ago': 10},
            {'campaign_idx': 0, 'activity_type': 'call_made', 'contact_idx': 2, 'description': 'مكالمة متابعة بعد إرسال الدعوة', 'days_ago': 8},
            {'campaign_idx': 0, 'activity_type': 'form_submitted', 'contact_idx': 3, 'description': 'تسجيل في فعالية الإطلاق', 'days_ago': 5},
            # أنشطة حملة البريد الإلكتروني
            {'campaign_idx': 1, 'activity_type': 'email_sent', 'contact_idx': 4, 'description': 'إرسال بريد تسويقي عن الخدمات', 'days_ago': 5},
            {'campaign_idx': 1, 'activity_type': 'email_sent', 'contact_idx': 5, 'description': 'إرسال عرض خاص للعملاء الجدد', 'days_ago': 4},
            {'campaign_idx': 1, 'activity_type': 'call_made', 'contact_idx': 6, 'description': 'مكالمة استكشافية بعد فتح البريد', 'days_ago': 3},
            {'campaign_idx': 1, 'activity_type': 'meeting_scheduled', 'contact_idx': 0, 'description': 'حجز اجتماع لعرض الحلول', 'days_ago': 2},
            {'campaign_idx': 1, 'activity_type': 'purchase_made', 'contact_idx': 1, 'description': 'تقديم طلب عرض سعر', 'days_ago': 1},
        ]

        campaign_activity_count = 0
        for data in campaign_activities_data:
            c_idx = data['campaign_idx']
            ct_idx = data['contact_idx']
            if c_idx >= len(campaigns) or ct_idx >= len(contacts):
                continue
            campaign = campaigns[c_idx]
            contact = contacts[ct_idx]

            activity_date = timezone.now() - timedelta(days=data['days_ago'])

            activity, created = CampaignActivity.objects.get_or_create(
                campaign=campaign,
                contact=contact,
                activity_type=data['activity_type'],
                activity_date=activity_date,
                defaults={
                    'description': data['description'],
                },
            )
            if created:
                campaign_activity_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء نشاط حملة: {campaign.name} - {activity.get_activity_type_display()}'))
            else:
                self.stdout.write(f'  تم التخطي (موجود): {activity.get_activity_type_display()}')

        # =============================================
        # ملخص
        # =============================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== ملخص البذر ==='))
        self.stdout.write(f'  جهات الاتصال المنشأة: {contact_count}')
        self.stdout.write(f'  فرص البيع المنشأة: {lead_count}')
        self.stdout.write(f'  أنشطة الفرص المنشأة: {activity_count}')
        self.stdout.write(f'  شرائح العملاء المنشأة: {segment_count}')
        self.stdout.write(f'  الحملات التسويقية المنشأة: {campaign_count}')
        self.stdout.write(f'  أنشطة الحملات المنشأة: {campaign_activity_count}')
        self.stdout.write(self.style.SUCCESS('تم إنشاء بيانات إدارة علاقات العملاء بنجاح!'))
