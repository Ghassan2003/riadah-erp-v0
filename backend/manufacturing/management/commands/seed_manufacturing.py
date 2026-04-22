"""
أمر إدارة لبذر بيانات التصنيع التجريبية.
ينشئ قوائم مواد، بنود قوائم، أوامر إنتاج، سجلات إنتاج، مراكز عمل، وخطوط مسارات إنتاج.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from manufacturing.models import (
    BillOfMaterials,
    BOMItem,
    ProductionOrder,
    ProductionLog,
    WorkCenter,
    RoutingStep,
)


class Command(BaseCommand):
    help = 'بذر بيانات التصنيع التجريبية لمنظومة ERP'

    def handle(self, *args, **options):
        from inventory.models import Product
        from users.models import User

        self.stdout.write('إنشاء بيانات التصنيع التجريبية...')

        # التأكد من وجود منتجات
        products = list(Product.objects.all()[:10])
        if len(products) < 4:
            self.stdout.write(self.style.ERROR('  لا يوجد منتجات كافية. قم بتشغيل seed_inventory أولاً.'))
            return

        # الحصول على مستخدم مشرف
        admin_user = User.objects.filter(role='admin').first()

        # =============================================
        # 1. إنشاء مراكز العمل (3)
        # =============================================
        work_centers_data = [
            {
                'name': 'مركز القص واللحام',
                'description': 'مركز متخصص في عمليات القص واللحام للمعادن',
                'location': 'المبنى أ - الطابق الأول',
                'capacity': 3,
                'status': 'active',
                'cost_per_hour': Decimal('150.00'),
            },
            {
                'name': 'مركز التجميع',
                'description': 'مركز تجميع المنتجات النهائية',
                'location': 'المبنى ب - الطابق الأرضي',
                'capacity': 5,
                'status': 'active',
                'cost_per_hour': Decimal('120.00'),
            },
            {
                'name': 'مركز الطلاء والتشطيب',
                'description': 'مركز الطلاء والتشطيب النهائي',
                'location': 'المبنى أ - الطابق الثاني',
                'capacity': 2,
                'status': 'maintenance',
                'cost_per_hour': Decimal('200.00'),
            },
        ]

        work_centers = []
        wc_count = 0
        for data in work_centers_data:
            wc, created = WorkCenter.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'location': data['location'],
                    'capacity': data['capacity'],
                    'status': data['status'],
                    'cost_per_hour': data['cost_per_hour'],
                },
            )
            work_centers.append(wc)
            if created:
                wc_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء مركز عمل: {wc.name}'))
            else:
                self.stdout.write(f'  تم التخطي (موجود): {wc.name}')

        # =============================================
        # 2. إنشاء قوائم المواد (3)
        # =============================================
        now = timezone.now()
        boms_data = [
            {
                'product_idx': 0,
                'name': f'قائمة مواد {products[0].name}',
                'description': 'قائمة المواد الأساسية للمنتج',
                'version': 1,
                'status': 'active',
                'effective_date': now.date(),
            },
            {
                'product_idx': 1,
                'name': f'قائمة مواد {products[1].name}',
                'description': 'قائمة مواد المنتج الثاني',
                'version': 2,
                'status': 'active',
                'effective_date': now.date(),
            },
            {
                'product_idx': 2,
                'name': f'قائمة مواد {products[2].name}',
                'description': 'قائمة مواد تجريبية',
                'version': 1,
                'status': 'draft',
                'effective_date': None,
            },
        ]

        boms = []
        bom_count = 0
        for data in boms_data:
            idx = data['product_idx']
            if idx >= len(products):
                continue
            product = products[idx]

            bom, created = BillOfMaterials.objects.get_or_create(
                name=data['name'],
                defaults={
                    'product': product,
                    'description': data['description'],
                    'version': data['version'],
                    'status': data['status'],
                    'effective_date': data['effective_date'],
                    'created_by': admin_user,
                },
            )
            boms.append(bom)
            if created:
                bom_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء قائمة مواد: {bom.name}'))
            else:
                self.stdout.write(f'  تم التخطي (موجودة): {bom.name}')

        # =============================================
        # 3. إنشاء بنود قوائم المواد (10)
        # =============================================
        bom_items_data = [
            {'bom_idx': 0, 'material_idx': 3, 'quantity': 5.00, 'unit_cost': 25.00, 'notes': 'مادة خام أساسية'},
            {'bom_idx': 0, 'material_idx': 4, 'quantity': 2.50, 'unit_cost': 45.00, 'notes': 'قطعة غيار'},
            {'bom_idx': 0, 'material_idx': 5, 'quantity': 1.00, 'unit_cost': 120.00, 'notes': 'محرك رئيسي'},
            {'bom_idx': 0, 'material_idx': 6, 'quantity': 10.00, 'unit_cost': 5.50, 'notes': 'براغي ومسامير'},
        ]

        # بنود لقائمة المواد الثانية
        if len(boms) >= 2 and len(products) >= 4:
            bom_items_data.extend([
                {'bom_idx': 1, 'material_idx': 3, 'quantity': 3.00, 'unit_cost': 25.00, 'notes': 'مادة خام'},
                {'bom_idx': 1, 'material_idx': 4, 'quantity': 4.00, 'unit_cost': 45.00, 'notes': 'قطع غيار إضافية'},
                {'bom_idx': 1, 'material_idx': 7, 'quantity': 2.00, 'unit_cost': 80.00, 'notes': 'لوحة تحكم'},
            ])

        # بنود لقائمة المواد الثالثة
        if len(boms) >= 3 and len(products) >= 5:
            bom_items_data.extend([
                {'bom_idx': 2, 'material_idx': 5, 'quantity': 2.00, 'unit_cost': 120.00, 'notes': 'محرك احتياطي'},
                {'bom_idx': 2, 'material_idx': 6, 'quantity': 20.00, 'unit_cost': 5.50, 'notes': 'مواد تثبيت'},
                {'bom_idx': 2, 'material_idx': 7, 'quantity': 1.00, 'unit_cost': 80.00, 'notes': 'لوحة إلكترونية'},
            ])

        item_count = 0
        for data in bom_items_data:
            bom_idx = data['bom_idx']
            material_idx = data['material_idx']
            if bom_idx >= len(boms) or material_idx >= len(products):
                continue

            bom = boms[bom_idx]
            material = products[material_idx]

            item, created = BOMItem.objects.get_or_create(
                bom=bom,
                material=material,
                defaults={
                    'quantity': Decimal(str(data['quantity'])),
                    'unit_cost': Decimal(str(data['unit_cost'])),
                    'notes': data['notes'],
                },
            )
            if created:
                item_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء بند: {item.material.name} ({item.quantity})'))
            else:
                self.stdout.write(f'  تم التخطي (موجود): {item.material.name}')

        # =============================================
        # 4. إنشاء أوامر الإنتاج (4)
        # =============================================
        orders_data = [
            {
                'order_number': 'PO-2025-001',
                'product_idx': 0,
                'bom_idx': 0,
                'quantity': 100,
                'quantity_produced': 100,
                'quantity_defective': 2,
                'status': 'completed',
                'priority': 'high',
                'planned_start': now.date() - timezone.timedelta(days=20),
                'planned_end': now.date() - timezone.timedelta(days=10),
                'actual_start': now.date() - timezone.timedelta(days=19),
                'actual_end': now.date() - timezone.timedelta(days=9),
                'notes': 'تم الانتهاء بنجاح مع 2 وحدة معيبة',
            },
            {
                'order_number': 'PO-2025-002',
                'product_idx': 1,
                'bom_idx': 1,
                'quantity': 50,
                'quantity_produced': 30,
                'quantity_defective': 1,
                'status': 'in_progress',
                'priority': 'medium',
                'planned_start': now.date() - timezone.timedelta(days=5),
                'planned_end': now.date() + timezone.timedelta(days=10),
                'actual_start': now.date() - timezone.timedelta(days=4),
                'actual_end': None,
                'notes': 'قيد التنفيذ حالياً',
            },
            {
                'order_number': 'PO-2025-003',
                'product_idx': 2,
                'bom_idx': 2,
                'quantity': 200,
                'quantity_produced': 0,
                'quantity_defective': 0,
                'status': 'planned',
                'priority': 'urgent',
                'planned_start': now.date() + timezone.timedelta(days=1),
                'planned_end': now.date() + timezone.timedelta(days=20),
                'actual_start': None,
                'actual_end': None,
                'notes': 'أمر عاجل - عميل VIP',
            },
            {
                'order_number': 'PO-2025-004',
                'product_idx': 0,
                'bom_idx': 0,
                'quantity': 75,
                'quantity_produced': 0,
                'quantity_defective': 0,
                'status': 'draft',
                'priority': 'low',
                'planned_start': now.date() + timezone.timedelta(days=15),
                'planned_end': now.date() + timezone.timedelta(days=30),
                'actual_start': None,
                'actual_end': None,
                'notes': 'أمر مسودة - بانتظار الموافقة',
            },
        ]

        orders = []
        order_count = 0
        for data in orders_data:
            product_idx = data['product_idx']
            if product_idx >= len(products):
                continue
            product = products[product_idx]

            bom = None
            bom_idx = data['bom_idx']
            if bom_idx < len(boms):
                bom = boms[bom_idx]

            order, created = ProductionOrder.objects.get_or_create(
                order_number=data['order_number'],
                defaults={
                    'product': product,
                    'bom': bom,
                    'quantity': Decimal(str(data['quantity'])),
                    'quantity_produced': Decimal(str(data['quantity_produced'])),
                    'quantity_defective': Decimal(str(data['quantity_defective'])),
                    'status': data['status'],
                    'priority': data['priority'],
                    'planned_start_date': data['planned_start'],
                    'planned_end_date': data['planned_end'],
                    'actual_start_date': data['actual_start'],
                    'actual_end_date': data['actual_end'],
                    'notes': data['notes'],
                    'created_by': admin_user,
                },
            )
            orders.append(order)
            if created:
                order_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء أمر إنتاج: {order.order_number} ({order.get_status_display()})'))
            else:
                self.stdout.write(f'  تم التخطي (موجود): {order.order_number}')

        # =============================================
        # 5. إنشاء سجلات الإنتاج (6)
        # =============================================
        logs_data = [
            {'order_idx': 0, 'operation_type': 'setup', 'quantity': 0, 'defect_quantity': 0, 'notes': 'إعداد خط الإنتاج'},
            {'order_idx': 0, 'operation_type': 'production', 'quantity': 100, 'defect_quantity': 2, 'notes': 'إنتاج كامل للدفعة'},
            {'order_idx': 0, 'operation_type': 'quality_check', 'quantity': 98, 'defect_quantity': 2, 'notes': 'فحص الجودة - 2 وحدات مرفوضة'},
            {'order_idx': 1, 'operation_type': 'setup', 'quantity': 0, 'defect_quantity': 0, 'notes': 'إعداد خط الإنتاج للأمر الثاني'},
            {'order_idx': 1, 'operation_type': 'production', 'quantity': 30, 'defect_quantity': 1, 'notes': 'إنتاج مرحلة أولى'},
            {'order_idx': 1, 'operation_type': 'maintenance', 'quantity': 0, 'defect_quantity': 0, 'notes': 'صيانة دورية للآلة'},
        ]

        log_count = 0
        for data in logs_data:
            order_idx = data['order_idx']
            if order_idx >= len(orders):
                continue
            order = orders[order_idx]

            log = ProductionLog.objects.create(
                production_order=order,
                operation_type=data['operation_type'],
                quantity=Decimal(str(data['quantity'])),
                defect_quantity=Decimal(str(data['defect_quantity'])),
                notes=data['notes'],
                operator=admin_user,
            )
            log_count += 1
            self.stdout.write(self.style.SUCCESS(f'  تم إنشاء سجل إنتاج: {log.get_operation_type_display()} - {log.notes[:30]}'))

        # =============================================
        # 6. إنشاء خطوات مسارات الإنتاج (5)
        # =============================================
        routing_steps_data = [
            {'bom_idx': 0, 'step_number': 1, 'wc_idx': 0, 'operation_name': 'قص المادة الخام', 'estimated_minutes': 30, 'cost_per_unit': 75.00},
            {'bom_idx': 0, 'step_number': 2, 'wc_idx': 0, 'operation_name': 'لحام الأجزاء', 'estimated_minutes': 45, 'cost_per_unit': 112.50},
            {'bom_idx': 0, 'step_number': 3, 'wc_idx': 1, 'operation_name': 'التجميع النهائي', 'estimated_minutes': 60, 'cost_per_unit': 120.00},
            {'bom_idx': 1, 'step_number': 1, 'wc_idx': 2, 'operation_name': 'الطلاء والتشطيب', 'estimated_minutes': 40, 'cost_per_unit': 133.33},
            {'bom_idx': 1, 'step_number': 2, 'wc_idx': 1, 'operation_name': 'التجميع والتغليف', 'estimated_minutes': 25, 'cost_per_unit': 50.00},
        ]

        step_count = 0
        for data in routing_steps_data:
            bom_idx = data['bom_idx']
            wc_idx = data['wc_idx']
            if bom_idx >= len(boms) or wc_idx >= len(work_centers):
                continue

            bom = boms[bom_idx]
            work_center = work_centers[wc_idx]

            step, created = RoutingStep.objects.get_or_create(
                bom=bom,
                step_number=data['step_number'],
                defaults={
                    'work_center': work_center,
                    'operation_name': data['operation_name'],
                    'estimated_minutes': Decimal(str(data['estimated_minutes'])),
                    'cost_per_unit': Decimal(str(data['cost_per_unit'])),
                },
            )
            if created:
                step_count += 1
                self.stdout.write(self.style.SUCCESS(f'  تم إنشاء خطوة مسار: {step.operation_name} ({step.step_number})'))
            else:
                self.stdout.write(f'  تم التخطي (موجودة): {step.operation_name}')

        # =============================================
        # ملخص
        # =============================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== ملخص البذر ==='))
        self.stdout.write(f'  مراكز العمل: {wc_count} تم إنشاؤها')
        self.stdout.write(f'  قوائم المواد: {bom_count} تم إنشاؤها')
        self.stdout.write(f'  بنود قوائم المواد: {item_count} تم إنشاؤها')
        self.stdout.write(f'  أوامر الإنتاج: {order_count} تم إنشاؤها')
        self.stdout.write(f'  سجلات الإنتاج: {log_count} تم إنشاؤها')
        self.stdout.write(f'  خطوات مسارات الإنتاج: {step_count} تم إنشاؤها')
        self.stdout.write(self.style.SUCCESS('تم بنجاح! تم بذر بيانات التصنيع التجريبية.'))
