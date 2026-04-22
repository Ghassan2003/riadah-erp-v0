"""
Management command to seed sample Equipment Maintenance data.
Creates Equipment, MaintenanceSchedules, MaintenanceWorkOrders, MaintenanceParts,
and EquipmentInspections for development and testing.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta

from equipmaint.models import (
    Equipment,
    MaintenanceSchedule,
    MaintenanceWorkOrder,
    MaintenancePart,
    EquipmentInspection,
)


class Command(BaseCommand):
    help = 'Seed sample equipment maintenance data for the ERP system'

    def handle(self, *args, **options):
        from users.models import User
        from hr.models import Department

        self.stdout.write('Creating sample Equipment Maintenance data...')

        # Get an admin user
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('  No admin user found. Run seed_users first.'))
            return

        # Get a department (optional)
        department = Department.objects.first()

        now = timezone.now()

        # =============================================
        # 1. Create Equipment (5 records)
        # =============================================
        equipment_data = [
            {
                'name': 'رافعة برجية',
                'equipment_number': 'EQ-001',
                'category': 'machinery',
                'brand': 'Liebherr',
                'model_number': '280 EC-H',
                'serial_number': 'LH-2021-45892',
                'location': 'ورشة رئيسية - المبنى أ',
                'purchase_date': date(2021, 3, 15),
                'purchase_cost': Decimal('450000.00'),
                'warranty_end': date(2024, 3, 15),
                'status': 'operational',
            },
            {
                'name': 'شاحنة نقل ثقيل',
                'equipment_number': 'EQ-002',
                'category': 'vehicle',
                'brand': 'Volvo',
                'model_number': 'FH16 750',
                'serial_number': 'VL-2022-78123',
                'location': 'مواقف المركبات - الخارج',
                'purchase_date': date(2022, 6, 20),
                'purchase_cost': Decimal('320000.00'),
                'warranty_end': date(2025, 6, 20),
                'status': 'operational',
            },
            {
                'name': 'مولد كهربائي ديزل',
                'equipment_number': 'EQ-003',
                'category': 'electrical',
                'brand': 'Caterpillar',
                'model_number': 'C32 ACERT',
                'serial_number': 'CAT-2020-33567',
                'location': 'غرفة المولدات - الطابق السفلي',
                'purchase_date': date(2020, 1, 10),
                'purchase_cost': Decimal('185000.00'),
                'warranty_end': date(2023, 1, 10),
                'status': 'maintenance',
            },
            {
                'name': 'وحدة تكييف مركزي',
                'equipment_number': 'EQ-004',
                'category': 'hvac',
                'brand': 'Carrier',
                'model_number': '30XA-252',
                'serial_number': 'CR-2019-66234',
                'location': 'سطح المبنى الرئيسي',
                'purchase_date': date(2019, 8, 5),
                'purchase_cost': Decimal('95000.00'),
                'warranty_end': date(2022, 8, 5),
                'status': 'operational',
            },
            {
                'name': 'نظام إطفاء حريق',
                'equipment_number': 'EQ-005',
                'category': 'safety',
                'brand': 'Tyco',
                'model_number': 'LFII-750',
                'serial_number': 'TY-2023-11890',
                'location': 'ممرات المبنى الرئيسي',
                'purchase_date': date(2023, 2, 14),
                'purchase_cost': Decimal('42000.00'),
                'warranty_end': date(2026, 2, 14),
                'status': 'operational',
            },
        ]

        equipment_objs = []
        eq_count = 0
        for data in equipment_data:
            eq, created = Equipment.objects.get_or_create(
                equipment_number=data['equipment_number'],
                defaults={
                    'name': data['name'],
                    'category': data['category'],
                    'brand': data['brand'],
                    'model_number': data['model_number'],
                    'serial_number': data['serial_number'],
                    'location': data['location'],
                    'purchase_date': data['purchase_date'],
                    'purchase_cost': data['purchase_cost'],
                    'warranty_end': data['warranty_end'],
                    'status': data['status'],
                    'assigned_department': department,
                    'assigned_to': admin_user,
                    'current_meter_reading': Decimal('1500.00'),
                },
            )
            equipment_objs.append(eq)
            if created:
                eq_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created equipment: {eq.name} ({eq.equipment_number})'))
            else:
                self.stdout.write(f'  Skipped (exists): {eq.name}')

        if len(equipment_objs) < 5:
            self.stdout.write(self.style.WARNING('  Not enough equipment objects, skipping related seeds.'))
            return

        # =============================================
        # 2. Create Maintenance Schedules (4 records)
        # =============================================
        schedules_data = [
            {
                'equipment_idx': 0,
                'maintenance_type': 'preventive',
                'frequency_type': 'monthly',
                'frequency_value': 1,
                'last_performed': now.date() - timedelta(days=25),
                'next_due': now.date() + timedelta(days=5),
                'estimated_cost': Decimal('5000.00'),
                'estimated_hours': Decimal('8.00'),
                'priority': 'high',
            },
            {
                'equipment_idx': 1,
                'maintenance_type': 'preventive',
                'frequency_type': 'quarterly',
                'frequency_value': 1,
                'last_performed': now.date() - timedelta(days=80),
                'next_due': now.date() + timedelta(days=10),
                'estimated_cost': Decimal('3500.00'),
                'estimated_hours': Decimal('4.00'),
                'priority': 'medium',
            },
            {
                'equipment_idx': 2,
                'maintenance_type': 'corrective',
                'frequency_type': 'monthly',
                'frequency_value': 1,
                'last_performed': now.date() - timedelta(days=15),
                'next_due': now.date() - timedelta(days=5),  # overdue
                'estimated_cost': Decimal('12000.00'),
                'estimated_hours': Decimal('16.00'),
                'priority': 'critical',
            },
            {
                'equipment_idx': 3,
                'maintenance_type': 'inspection',
                'frequency_type': 'semi_annual',
                'frequency_value': 1,
                'last_performed': now.date() - timedelta(days=170),
                'next_due': now.date() + timedelta(days=15),
                'estimated_cost': Decimal('2000.00'),
                'estimated_hours': Decimal('3.00'),
                'priority': 'low',
            },
        ]

        schedule_objs = []
        sched_count = 0
        for data in schedules_data:
            idx = data['equipment_idx']
            if idx >= len(equipment_objs):
                continue
            eq = equipment_objs[idx]

            sched, created = MaintenanceSchedule.objects.get_or_create(
                equipment=eq,
                maintenance_type=data['maintenance_type'],
                frequency_type=data['frequency_type'],
                defaults={
                    'frequency_value': data['frequency_value'],
                    'last_performed': data['last_performed'],
                    'next_due': data['next_due'],
                    'assigned_to': admin_user,
                    'estimated_cost': data['estimated_cost'],
                    'estimated_hours': data['estimated_hours'],
                    'priority': data['priority'],
                    'is_active': True,
                    'notes': 'جدول صيانة منتظم',
                },
            )
            schedule_objs.append(sched)
            if created:
                sched_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created schedule: {sched.equipment.name} - {sched.get_maintenance_type_display()}'))
            else:
                self.stdout.write(f'  Skipped (exists): {sched.equipment.name} schedule')

        # =============================================
        # 3. Create Maintenance Work Orders (6 records)
        # =============================================
        work_orders_data = [
            {
                'equipment_idx': 2,
                'schedule_idx': 2,
                'work_type': 'corrective',
                'priority': 'critical',
                'status': 'in_progress',
                'description': 'إصلاح عطل في نظام التبريد للمولد - ارتفاع حرارة غير طبيعي',
                'started_at': now - timedelta(days=2),
            },
            {
                'equipment_idx': 0,
                'schedule_idx': 0,
                'work_type': 'preventive',
                'priority': 'high',
                'status': 'requested',
                'description': 'صيانة دورية شهرية للرافعة البرجية - فحص الكابلات والمرابط',
            },
            {
                'equipment_idx': 1,
                'schedule_idx': 1,
                'work_type': 'preventive',
                'priority': 'medium',
                'status': 'approved',
                'description': 'صيانة ربع سنوية للشاحنة - تغيير زيت المحرك والفلتر',
                'started_at': None,
            },
            {
                'equipment_idx': 3,
                'schedule_idx': 3,
                'work_type': 'inspection',
                'priority': 'low',
                'status': 'completed',
                'description': 'فحص دوري لنظام التكييف المركزي - تنظيف الفلاتر واختبار الضغط',
                'started_at': now - timedelta(days=10),
                'completed_at': now - timedelta(days=9),
                'actual_cost': Decimal('1800.00'),
                'actual_hours': Decimal('2.50'),
                'completion_notes': 'تم تنظيف الفلاتر وضبط ضغط الفريون - الحالة جيدة',
            },
            {
                'equipment_idx': 4,
                'schedule_idx': None,
                'work_type': 'emergency',
                'priority': 'critical',
                'status': 'completed',
                'description': 'طوارئ - استبدال طفاية حريق تالفة في الطابق الثاني',
                'started_at': now - timedelta(days=5),
                'completed_at': now - timedelta(days=5),
                'actual_cost': Decimal('850.00'),
                'actual_hours': Decimal('1.00'),
                'completion_notes': 'تم استبدال الطفاية وتعبئة النظام',
            },
            {
                'equipment_idx': 0,
                'schedule_idx': None,
                'work_type': 'corrective',
                'priority': 'high',
                'status': 'cancelled',
                'description': 'إصلاح تسريب زيت في الرافعة - تم إلغاؤه بسبب عدم تأكيد العطل',
            },
        ]

        work_order_objs = []
        wo_count = 0
        for i, data in enumerate(work_orders_data):
            idx = data['equipment_idx']
            if idx >= len(equipment_objs):
                continue
            eq = equipment_objs[idx]

            wo_number = f'WO-{(now.date() - timedelta(days=i*5)).strftime("%Y%m%d")}-{i+1:04d}'

            sched = None
            if data.get('schedule_idx') is not None:
                sched_idx = data['schedule_idx']
                if sched_idx < len(schedule_objs):
                    sched = schedule_objs[sched_idx]

            wo, created = MaintenanceWorkOrder.objects.get_or_create(
                work_order_number=wo_number,
                defaults={
                    'equipment': eq,
                    'schedule': sched,
                    'work_type': data['work_type'],
                    'priority': data['priority'],
                    'status': data['status'],
                    'description': data['description'],
                    'requested_by': admin_user,
                    'assigned_to': admin_user,
                    'started_at': data.get('started_at'),
                    'completed_at': data.get('completed_at'),
                    'actual_cost': data.get('actual_cost', Decimal('0')),
                    'actual_hours': data.get('actual_hours', Decimal('0')),
                    'completion_notes': data.get('completion_notes', ''),
                    'approved_by': admin_user if data['status'] in ('approved', 'in_progress', 'completed', 'cancelled') else None,
                },
            )
            work_order_objs.append(wo)
            if created:
                wo_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created work order: {wo.work_order_number} - {wo.get_status_display()}'))
            else:
                self.stdout.write(f'  Skipped (exists): {wo.work_order_number}')

        # =============================================
        # 4. Create Maintenance Parts (8 records)
        # =============================================
        parts_data = [
            {'wo_idx': 0, 'part_name': 'فلتر زيت المولد', 'part_number': 'CAT-OIL-F500', 'quantity': 2, 'unit_cost': Decimal('450.00')},
            {'wo_idx': 0, 'part_name': 'حشية غطاء الصمامات', 'part_number': 'CAT-GSK-V720', 'quantity': 1, 'unit_cost': Decimal('320.00')},
            {'wo_idx': 0, 'part_name': 'ثرموستات المولد', 'part_number': 'CAT-THR-882', 'quantity': 1, 'unit_cost': Decimal('780.00')},
            {'wo_idx': 1, 'part_name': 'كابل رفع رئيسي', 'part_number': 'LB-CBL-M200', 'quantity': 1, 'unit_cost': Decimal('2500.00')},
            {'wo_idx': 1, 'part_name': 'مرابط شد', 'part_number': 'LB-BLT-50M', 'quantity': 20, 'unit_cost': Decimal('35.00')},
            {'wo_idx': 2, 'part_name': 'فلتر زيت محرك', 'part_number': 'VL-OIL-FH16', 'quantity': 1, 'unit_cost': Decimal('280.00')},
            {'wo_idx': 3, 'part_name': 'فلتر تكييف', 'part_number': 'CR-AIR-F30X', 'quantity': 4, 'unit_cost': Decimal('120.00')},
            {'wo_idx': 4, 'part_name': 'طفاية حريق 6 كجم', 'part_number': 'TY-EXT-6KG', 'quantity': 1, 'unit_cost': Decimal('350.00')},
        ]

        part_count = 0
        for data in parts_data:
            idx = data['wo_idx']
            if idx >= len(work_order_objs):
                continue
            wo = work_order_objs[idx]

            part, created = MaintenancePart.objects.get_or_create(
                work_order=wo,
                part_name=data['part_name'],
                part_number=data['part_number'],
                defaults={
                    'quantity': data['quantity'],
                    'unit_cost': data['unit_cost'],
                    'notes': 'قطعة غيار للصيانة',
                },
            )
            if created:
                part_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created part: {part.part_name} x{part.quantity}'))
            else:
                self.stdout.write(f'  Skipped (exists): {part.part_name}')

        # =============================================
        # 5. Create Equipment Inspections (4 records)
        # =============================================
        inspections_data = [
            {
                'equipment_idx': 0,
                'inspection_type': 'monthly',
                'condition_rating': 'good',
                'findings': 'حالة الرافعة جيدة - الكابلات في حالة جيدة مع بعض التآكل الطبيعي',
                'recommendations': 'يُنصح بتغيير كابل الرفع الرئيسي خلال 3 أشهر',
                'next_inspection': now.date() + timedelta(days=30),
                'status': 'conditional_pass',
                'days_ago': 5,
            },
            {
                'equipment_idx': 2,
                'inspection_type': 'special',
                'condition_rating': 'poor',
                'findings': 'ارتفاع حرارة المولد بشكل مستمر - مشكلة في نظام التبريد',
                'recommendations': 'يجب إصلاح نظام التبريد فوراً وتغيير الفلاتر',
                'next_inspection': now.date() + timedelta(days=7),
                'status': 'fail',
                'days_ago': 3,
            },
            {
                'equipment_idx': 1,
                'inspection_type': 'weekly',
                'condition_rating': 'excellent',
                'findings': 'الشاحنة في حالة ممتازة - جميع الأنظمة تعمل بشكل طبيعي',
                'recommendations': 'الاستمرار في الصيانة الدورية المعتادة',
                'next_inspection': now.date() + timedelta(days=7),
                'status': 'pass',
                'days_ago': 1,
            },
            {
                'equipment_idx': 4,
                'inspection_type': 'monthly',
                'condition_rating': 'good',
                'findings': 'نظام الإطفاء يعمل بشكل جيد - جميع الطفايات في مكانها الصحيح',
                'recommendations': 'جدولة فحص ضغط الطفايات الأسبوع القادم',
                'next_inspection': now.date() + timedelta(days=30),
                'status': 'pass',
                'days_ago': 10,
            },
        ]

        insp_count = 0
        for data in inspections_data:
            idx = data['equipment_idx']
            if idx >= len(equipment_objs):
                continue
            eq = equipment_objs[idx]

            insp, created = EquipmentInspection.objects.get_or_create(
                equipment=eq,
                inspection_type=data['inspection_type'],
                inspection_date=now - timedelta(days=data['days_ago']),
                defaults={
                    'inspector': admin_user,
                    'condition_rating': data['condition_rating'],
                    'findings': data['findings'],
                    'recommendations': data['recommendations'],
                    'next_inspection': data['next_inspection'],
                    'status': data['status'],
                },
            )
            if created:
                insp_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created inspection: {insp.equipment.name} - {insp.get_condition_rating_display()}'))
            else:
                self.stdout.write(f'  Skipped (exists): {insp.equipment.name} inspection')

        # =============================================
        # Summary
        # =============================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Seed Summary ==='))
        self.stdout.write(f'  Equipment created: {eq_count}')
        self.stdout.write(f'  Maintenance Schedules created: {sched_count}')
        self.stdout.write(f'  Work Orders created: {wo_count}')
        self.stdout.write(f'  Maintenance Parts created: {part_count}')
        self.stdout.write(f'  Equipment Inspections created: {insp_count}')
        self.stdout.write(self.style.SUCCESS('Done! Equipment Maintenance data seeded successfully.'))
