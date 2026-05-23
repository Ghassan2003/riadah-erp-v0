"""
Seed command for Startup Finance module — بيانات تجريبية.
Creates: StartupProfile, FundingRounds, BurnRateEntries, SubscriptionPlans,
SubscriptionCycles, CustomerMetrics, FinancialEntries, FinancialKPIs.

Usage: python manage.py seed_startup_finance
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'إنشاء بيانات تجريبية لوحدة تمويل الشركات الناشئة'

    def handle(self, *args, **options):
        from startup_finance.models import (
            StartupProfile, FundingRound, BurnRateEntry,
            SubscriptionPlan, SubscriptionCycle, CustomerMetric,
            FinancialKPI, FinancialEntry,
        )
        from sales.models import Customer

        self.stdout.write(self.style.SUCCESS('🌱 بدء إنشاء بيانات تجريبية...'))

        # 1. ملف الشركة الناشئة
        profile, created = StartupProfile.objects.get_or_create(
            company_name='ريادة تك',
            defaults={
                'industry': 'تقنية المعلومات',
                'stage': 'series_a',
                'founded_date': date(2022, 1, 15),
                'team_size': 28,
                'currency': 'SAR',
                'initial_funding': Decimal('4500000'),
                'monthly_recurring_revenue': Decimal('185000'),
                'monthly_operating_expenses': Decimal('320000'),
                'cash_balance': Decimal('2800000'),
            }
        )
        action = 'تم إنشاؤه' if created else 'موجود مسبقاً'
        self.stdout.write(f'  ✅ ملف الشركة: {profile.company_name} ({action})')

        # 2. جولات التمويل
        funding_rounds_data = [
            {'round_type': 'pre_seed', 'round_name': 'Pre-Seed', 'amount_raised': Decimal('200000'), 'valuation_pre_money': Decimal('2000000'), 'equity_diluted': Decimal('10'), 'round_date': date(2022, 3, 1), 'investor_names': 'مستثمر ملائكي'},
            {'round_type': 'seed', 'round_name': 'Seed Round', 'amount_raised': Decimal('800000'), 'valuation_pre_money': Decimal('5000000'), 'equity_diluted': Decimal('13.8'), 'round_date': date(2022, 11, 15), 'investor_names': 'صندوق رأس المال الجريء أ, مستثمر ملائكي'},
            {'round_type': 'angel', 'round_name': 'Angel Bridge', 'amount_raised': Decimal('500000'), 'valuation_pre_money': Decimal('8000000'), 'equity_diluted': Decimal('5.9'), 'round_date': date(2023, 6, 1), 'investor_names': 'مستثمر ملائكي ب'},
            {'round_type': 'series_a', 'round_name': 'Series A', 'amount_raised': Decimal('3000000'), 'valuation_pre_money': Decimal('25000000'), 'equity_diluted': Decimal('10.7'), 'round_date': date(2024, 2, 1), 'investor_names': 'صندوق النمو أ, صندوق التكنولوجيا ب'},
        ]
        for rd in funding_rounds_data:
            FundingRound.objects.get_or_create(
                startup=profile,
                round_type=rd['round_type'],
                round_date=rd['round_date'],
                defaults={**rd},
            )
        self.stdout.write(f'  ✅ جولات التمويل: {len(funding_rounds_data)} جولات')

        # 3. خطط الاشتراك
        plans_data = [
            {'name': 'الأساسية', 'price_monthly': Decimal('99'), 'price_yearly': Decimal('990'), 'trial_days': 14, 'max_users': 5, 'features': ['تقارير أساسية', 'دعم بريدي', '5 مستخدمين']},
            {'name': 'الاحترافية', 'price_monthly': Decimal('299'), 'price_yearly': Decimal('2990'), 'trial_days': 14, 'max_users': 25, 'features': ['تقارير متقدمة', 'دعم أولوي', '25 مستخدم', 'API متكامل']},
            {'name': 'المؤسسية', 'price_monthly': Decimal('799'), 'price_yearly': Decimal('7990'), 'trial_days': 30, 'max_users': 100, 'features': ['جميع الميزات', 'دعم مخصص', 'مستخدمين غير محدودين', 'SLA مخصص', 'تكامل مخصص']},
        ]
        plans = []
        for pd in plans_data:
            plan, _ = SubscriptionPlan.objects.get_or_create(
                name=pd['name'],
                defaults=pd,
            )
            plans.append(plan)
        self.stdout.write(f'  ✅ خطط الاشتراك: {len(plans)} خطط')

        # 4. سجلات معدل الحرق (آخر 12 شهر)
        now = timezone.now().date()
        categories_expense = [
            ('payroll', Decimal('180000'), True),
            ('rent', Decimal('25000'), True),
            ('marketing', Decimal('35000'), True),
            ('software', Decimal('12000'), True),
            ('infrastructure', Decimal('8000'), True),
            ('operations', Decimal('30000'), True),
            ('legal', Decimal('5000'), False),
            ('misc', Decimal('10000'), False),
        ]

        burn_entries_count = 0
        for months_ago in range(12):
            month_date = date(now.year, now.month - months_ago, 1) if now.month > months_ago else date(now.year - 1, now.month - months_ago + 12, 1)

            for cat, base_amount, is_recurring in categories_expense:
                # إضافة تباين عشوائي ±15%
                variation = 1 + random.uniform(-0.15, 0.15)
                amount = base_amount * Decimal(str(variation))

                entry, _ = BurnRateEntry.objects.get_or_create(
                    startup=profile,
                    month=month_date,
                    category=cat,
                    entry_type='expense',
                    defaults={
                        'amount': amount.quantize(Decimal('0.01')),
                        'is_recurring': is_recurring,
                        'description': f'مصروف {cat} لشهر {month_date.strftime("%Y-%m")}',
                    }
                )
                burn_entries_count += 1

            # إيرادات شهرية (بزيادة تدريجية)
            revenue_growth = 1 + (months_ago * 0.03)  # نمو 3% شهري
            revenue_amount = Decimal('185000') * Decimal(str(revenue_growth))
            variation = 1 + random.uniform(-0.05, 0.05)
            revenue_amount *= Decimal(str(variation))

            BurnRateEntry.objects.get_or_create(
                startup=profile,
                month=month_date,
                category='subscription_revenue',
                entry_type='revenue',
                defaults={
                    'amount': revenue_amount.quantize(Decimal('0.01')),
                    'is_recurring': True,
                    'description': f'إيرادات اشتراكات {month_date.strftime("%Y-%m")}',
                }
            )

        self.stdout.write(f'  ✅ سجلات معدل الحرق: {burn_entries_count + 12} سجل')

        # 5. دورات الاشتراك
        # إنشاء عملاء اختباريين إذا لم يوجدوا
        customer_names = [
            'شركة التقنية المتقدمة', 'مؤسسة الابتكار', 'شركة البيانات الذكية',
            'مجموعة الحلول الرقمية', 'شركة السحابة العربية', 'مؤسسة الأتمتة',
            'شركة الذكاء الاصطناعي', 'مجموعة البرمجيات الحديثة',
            'شركة التحليلات المتقدمة', 'مؤسسة التكنولوجيا المالية',
            'شركة التجارة الإلكترونية', 'مجموعة الأمن السيبراني',
            'شركة التعليم الرقمي', 'مؤسسة الرعاية الصحية',
            'شركة اللوجستيات الذكية',
        ]

        customers = []
        for name in customer_names:
            customer, _ = Customer.objects.get_or_create(
                name=name,
                defaults={'email': f'contact@{name.replace(" ", "").lower()}.com'},
            )
            customers.append(customer)

        subscription_count = 0
        statuses_dist = ['active'] * 10 + ['trialing'] * 2 + ['past_due'] * 1 + ['cancelled'] * 2
        billing_choices = ['monthly', 'quarterly', 'yearly']

        for i, customer in enumerate(customers):
            plan = random.choice(plans)
            sub_status = random.choice(statuses_dist)
            billing = random.choice(billing_choices)

            # حساب المبلغ حسب دورة الفوترة
            if billing == 'quarterly':
                amount = plan.price_monthly * 3
            elif billing == 'yearly':
                amount = plan.price_yearly or plan.price_monthly * 12
            else:
                amount = plan.price_monthly

            start_offset = random.randint(30, 365)
            start_date = now - timedelta(days=start_offset)

            end_date = None
            if sub_status == 'cancelled':
                end_date = start_date + timedelta(days=random.randint(30, 180))
            elif sub_status in ('active', 'trialing'):
                end_date = start_date + timedelta(days=365 if billing == 'yearly' else 90 if billing == 'quarterly' else 30)

            SubscriptionCycle.objects.get_or_create(
                startup=profile,
                customer=customer,
                defaults={
                    'plan': plan,
                    'status': sub_status,
                    'billing_cycle': billing,
                    'amount': amount,
                    'start_date': start_date,
                    'end_date': end_date,
                    'trial_end_date': start_date + timedelta(days=plan.trial_days) if plan.trial_days > 0 and sub_status == 'trialing' else None,
                }
            )
            subscription_count += 1

        self.stdout.write(f'  ✅ دورات الاشتراك: {subscription_count} دورة')

        # 6. مقاييس العملاء
        channels = ['Google Ads', 'SEO', 'Referral', 'Direct', 'LinkedIn', 'Conference']
        metrics_count = 0
        for i, customer in enumerate(customers[:12]):
            acquisition_cost = Decimal(random.randint(200, 3000))
            monthly_rev = Decimal(random.randint(99, 2000))
            months_active = random.randint(3, 24)
            total_rev = monthly_rev * months_active
            projected_ltv = monthly_rev * 36 * Decimal('0.7')  # 36 شهر متوسط بقاء × 70% هامش

            CustomerMetric.objects.get_or_create(
                startup=profile,
                customer=customer,
                defaults={
                    'customer_name': customer.name,
                    'acquisition_channel': random.choice(channels),
                    'acquisition_cost': acquisition_cost,
                    'monthly_revenue': monthly_rev,
                    'months_active': months_active,
                    'total_revenue': total_rev,
                    'projected_ltv': projected_ltv,
                    'cohort': date(now.year - random.randint(0, 2), random.randint(1, 12), 1),
                }
            )
            metrics_count += 1

        self.stdout.write(f'  ✅ مقاييس العملاء: {metrics_count} مقياس')

        # 7. KPIs للأشهر الـ 12 الماضية
        for months_ago in range(12):
            month_date = date(now.year, now.month - months_ago, 1) if now.month > months_ago else date(now.year - 1, now.month - months_ago + 12, 1)

            growth_factor = 1 + (months_ago * 0.03)
            mrr_val = Decimal('185000') * Decimal(str(growth_factor))
            expenses_val = Decimal('305000') * Decimal(str(1 + random.uniform(-0.05, 0.05)))
            revenue_val = mrr_val * Decimal('1.2')
            burn = max(expenses_val - revenue_val, Decimal('0'))

            FinancialKPI.objects.get_or_create(
                startup=profile,
                month=month_date,
                defaults={
                    'total_revenue': revenue_val.quantize(Decimal('0.01')),
                    'mrr': mrr_val.quantize(Decimal('0.01')),
                    'arr': (mrr_val * 12).quantize(Decimal('0.01')),
                    'arpu': (mrr_val / 15).quantize(Decimal('0.01')),
                    'total_expenses': expenses_val.quantize(Decimal('0.01')),
                    'burn_rate': burn.quantize(Decimal('0.01')),
                    'cac': Decimal(random.randint(800, 1500)),
                    'ltv': Decimal(random.randint(15000, 45000)),
                    'runway_months': Decimal('9.3'),
                    'gross_margin_pct': Decimal('42.5'),
                    'net_margin_pct': Decimal('-18.2'),
                    'ltv_cac_ratio': Decimal('18.5'),
                    'quick_ratio': Decimal('1.3'),
                    'total_subscribers': 15 + (12 - months_ago) * 2,
                    'new_subscribers': random.randint(2, 6),
                    'churned_subscribers': 1 if months_ago < 8 else 0,
                    'churn_rate_pct': Decimal('6.7'),
                    'cash_balance': Decimal('2800000') - (burn * months_ago),
                    'total_funding_raised': Decimal('4500000'),
                }
            )

        self.stdout.write(f'  ✅ مؤشرات KPIs: 12 شهر')

        self.stdout.write(self.style.SUCCESS('\n🎉 تم إنشاء جميع البيانات التجريبية بنجاح!'))
        self.stdout.write(f'  📊 الملف: {profile.company_name}')
        self.stdout.write(f'  💰 المعدل الحالي: {profile.burn_rate:,.2f} {profile.currency}/شهر')
        self.stdout.write(f'  ⏱️ أشهر المشاركة: {profile.runway_months:,.1f} شهر')
