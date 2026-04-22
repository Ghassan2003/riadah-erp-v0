"""
Management command to seed sample Import/Export data.
Creates ImportOrders, ImportItems, ExportOrders, ExportItems, and CustomsDeclarations
for development and testing.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum

from importexport.models import (
    ImportOrder,
    ImportItem,
    ExportOrder,
    ExportItem,
    CustomsDeclaration,
)


class Command(BaseCommand):
    help = 'Seed sample import/export data for the ERP system'

    def handle(self, *args, **options):
        from purchases.models import Supplier
        from sales.models import Customer
        from inventory.models import Product
        from users.models import User

        self.stdout.write('Creating sample Import/Export data...')

        # Ensure suppliers and customers exist
        suppliers = list(Supplier.objects.filter(is_active=True)[:5])
        if not suppliers:
            self.stdout.write(self.style.ERROR('  No active suppliers found. Run seed_purchases first.'))
            return

        customers = list(Customer.objects.filter(is_active=True)[:5])
        if not customers:
            self.stdout.write(self.style.ERROR('  No active customers found. Run seed_sales first.'))
            return

        products = list(Product.objects.all()[:10])
        if not products:
            self.stdout.write(self.style.ERROR('  No products found. Run seed_inventory first.'))
            return

        # Get an admin user for created_by fields
        admin_user = User.objects.filter(role='admin').first()

        # =============================================
        # 1. Create Import Orders (3)
        # =============================================
        import_orders_data = [
            {
                'order_number': 'IMP-2025-001',
                'supplier_idx': 0,
                'order_date': '2025-01-15',
                'expected_arrival': '2025-03-10',
                'actual_arrival': None,
                'port_of_entry': 'ميناء جدة الإسلامي',
                'country_of_origin': 'الصين',
                'currency': 'USD',
                'exchange_rate': Decimal('3.7500'),
                'status': 'transit',
                'total_amount': Decimal('45000.00'),
                'customs_duties': Decimal('6750.00'),
                'shipping_cost': Decimal('3200.00'),
                'insurance_cost': Decimal('800.00'),
                'other_costs': Decimal('500.00'),
                'payment_terms': '30% مقدم، 70% قبل الشحن',
                'notes': 'شحنة قطع غيار للمصنع',
            },
            {
                'order_number': 'IMP-2025-002',
                'supplier_idx': 1,
                'order_date': '2025-02-01',
                'expected_arrival': '2025-04-15',
                'actual_arrival': None,
                'port_of_entry': 'ميناء الملك عبدالعزيز بالدمام',
                'country_of_origin': 'ألمانيا',
                'currency': 'EUR',
                'exchange_rate': Decimal('4.0800'),
                'status': 'customs',
                'total_amount': Decimal('28000.00'),
                'customs_duties': Decimal('4200.00'),
                'shipping_cost': Decimal('2100.00'),
                'insurance_cost': Decimal('600.00'),
                'other_costs': Decimal('300.00'),
                'payment_terms': 'دفعة واحدة عند التسليم',
                'notes': 'أجهزة قياس ومعدات فنية',
            },
            {
                'order_number': 'IMP-2025-003',
                'supplier_idx': 2,
                'order_date': '2025-03-01',
                'expected_arrival': '2025-05-20',
                'actual_arrival': '2025-05-18',
                'port_of_entry': 'ميناء جدة الإسلامي',
                'country_of_origin': 'اليابان',
                'currency': 'JPY',
                'exchange_rate': Decimal('0.0250'),
                'status': 'received',
                'total_amount': Decimal('18500.00'),
                'customs_duties': Decimal('2775.00'),
                'shipping_cost': Decimal('1800.00'),
                'insurance_cost': Decimal('450.00'),
                'other_costs': Decimal('200.00'),
                'payment_terms': 'خطاب اعتماد',
                'notes': 'قطع إلكترونية دقيقة',
            },
        ]

        import_orders = []
        for data in import_orders_data:
            idx = data['supplier_idx']
            if idx >= len(suppliers):
                continue

            order, created = ImportOrder.objects.get_or_create(
                order_number=data['order_number'],
                defaults={
                    'supplier': suppliers[idx],
                    'order_date': data['order_date'],
                    'expected_arrival': data['expected_arrival'],
                    'actual_arrival': data['actual_arrival'],
                    'port_of_entry': data['port_of_entry'],
                    'country_of_origin': data['country_of_origin'],
                    'currency': data['currency'],
                    'exchange_rate': data['exchange_rate'],
                    'status': data['status'],
                    'total_amount': data['total_amount'],
                    'customs_duties': data['customs_duties'],
                    'shipping_cost': data['shipping_cost'],
                    'insurance_cost': data['insurance_cost'],
                    'other_costs': data['other_costs'],
                    'payment_terms': data['payment_terms'],
                    'notes': data['notes'],
                    'created_by': admin_user,
                },
            )
            if created:
                order.recalculate()
                import_orders.append(order)
                self.stdout.write(self.style.SUCCESS(f'  Created import order: {order.order_number}'))
            else:
                import_orders.append(order)
                self.stdout.write(f'  Skipped (exists): {order.order_number}')

        # =============================================
        # 2. Create Import Items (8)
        # =============================================
        import_items_data = [
            # Items for IMP-2025-001 (3 items)
            {'order_idx': 0, 'product_idx': 0, 'description': 'محرك كهربائي صناعي 75 حصان', 'hs_code': '8501.52', 'quantity': Decimal('5'), 'unit_price': Decimal('3000.00'), 'customs_duty_rate': Decimal('15.00'), 'unit': 'piece', 'country_of_origin': 'الصين'},
            {'order_idx': 0, 'product_idx': 1, 'description': 'صمام تحكم هيدروليكي', 'hs_code': '8481.20', 'quantity': Decimal('50'), 'unit_price': Decimal('180.00'), 'customs_duty_rate': Decimal('10.00'), 'unit': 'piece', 'country_of_origin': 'الصين'},
            {'order_idx': 0, 'product_idx': 2, 'description': 'حامل محمل كروي SKF', 'hs_code': '8482.10', 'quantity': Decimal('200'), 'unit_price': Decimal('75.00'), 'customs_duty_rate': Decimal('5.00'), 'unit': 'piece', 'country_of_origin': 'الصين'},
            # Items for IMP-2025-002 (3 items)
            {'order_idx': 1, 'product_idx': 3, 'description': 'جهاز قياس ضغط رقمي', 'hs_code': '9026.20', 'quantity': Decimal('10'), 'unit_price': Decimal('1200.00'), 'customs_duty_rate': Decimal('5.00'), 'unit': 'piece', 'country_of_origin': 'ألمانيا'},
            {'order_idx': 1, 'product_idx': 4, 'description': 'محلل غازات محمول', 'hs_code': '9027.80', 'quantity': Decimal('3'), 'unit_price': Decimal('4500.00'), 'customs_duty_rate': Decimal('15.00'), 'unit': 'piece', 'country_of_origin': 'ألمانيا'},
            {'order_idx': 1, 'product_idx': 5, 'description': 'مولد كهربائي احتياطي 500 كيلو فولت أمبير', 'hs_code': '8501.61', 'quantity': Decimal('1'), 'unit_price': Decimal('4000.00'), 'customs_duty_rate': Decimal('15.00'), 'unit': 'piece', 'country_of_origin': 'ألمانيا'},
            # Items for IMP-2025-003 (2 items)
            {'order_idx': 2, 'product_idx': 6, 'description': 'شريحة إلكترونية متحكم دقيق ARM', 'hs_code': '8542.31', 'quantity': Decimal('500'), 'unit_price': Decimal('12.00'), 'customs_duty_rate': Decimal('0.00'), 'unit': 'piece', 'country_of_origin': 'اليابان'},
            {'order_idx': 2, 'product_idx': 7, 'description': 'حساس درجة حرارة صناعي PT100', 'hs_code': '9025.19', 'quantity': Decimal('100'), 'unit_price': Decimal('35.00'), 'customs_duty_rate': Decimal('5.00'), 'unit': 'piece', 'country_of_origin': 'اليابان'},
        ]

        item_count = 0
        for data in import_items_data:
            order_idx = data['order_idx']
            product_idx = data['product_idx']
            if order_idx >= len(import_orders):
                continue

            product = products[product_idx] if product_idx < len(products) else None

            item, created = ImportItem.objects.get_or_create(
                import_order=import_orders[order_idx],
                description=data['description'],
                defaults={
                    'product': product,
                    'hs_code': data['hs_code'],
                    'quantity': data['quantity'],
                    'unit_price': data['unit_price'],
                    'customs_duty_rate': data['customs_duty_rate'],
                    'unit': data['unit'],
                    'country_of_origin': data['country_of_origin'],
                },
            )
            if created:
                item_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created import item: {item.description[:40]}'))
            else:
                self.stdout.write(f'  Skipped (exists): {item.description[:40]}')

        # =============================================
        # 3. Create Export Orders (2)
        # =============================================
        export_orders_data = [
            {
                'order_number': 'EXP-2025-001',
                'customer_idx': 0,
                'order_date': '2025-02-10',
                'ship_date': '2025-03-01',
                'port_of_loading': 'ميناء جدة الإسلامي',
                'destination_country': 'الإمارات العربية المتحدة',
                'destination_port': 'ميناء جبل علي',
                'currency': 'USD',
                'exchange_rate': Decimal('3.7500'),
                'status': 'shipped',
                'total_amount': Decimal('32000.00'),
                'shipping_terms': 'FOB',
                'payment_terms': '60 يوم من تاريخ الشحن',
                'notes': 'شحنة معدات للعميل في دبي',
            },
            {
                'order_number': 'EXP-2025-002',
                'customer_idx': 1,
                'order_date': '2025-03-15',
                'ship_date': None,
                'port_of_loading': 'ميناء الملك عبدالعزيز بالدمام',
                'destination_country': 'الكويت',
                'destination_port': 'ميناء الشويخ',
                'currency': 'USD',
                'exchange_rate': Decimal('3.7500'),
                'status': 'confirmed',
                'total_amount': Decimal('18500.00'),
                'shipping_terms': 'CIF',
                'payment_terms': 'دفعة مقدمة 50% والباقي عند التسليم',
                'notes': 'مواد كيميائية صناعية',
            },
        ]

        export_orders = []
        for data in export_orders_data:
            idx = data['customer_idx']
            if idx >= len(customers):
                continue

            order, created = ExportOrder.objects.get_or_create(
                order_number=data['order_number'],
                defaults={
                    'customer': customers[idx],
                    'order_date': data['order_date'],
                    'ship_date': data['ship_date'],
                    'port_of_loading': data['port_of_loading'],
                    'destination_country': data['destination_country'],
                    'destination_port': data['destination_port'],
                    'currency': data['currency'],
                    'exchange_rate': data['exchange_rate'],
                    'status': data['status'],
                    'total_amount': data['total_amount'],
                    'shipping_terms': data['shipping_terms'],
                    'payment_terms': data['payment_terms'],
                    'notes': data['notes'],
                    'created_by': admin_user,
                },
            )
            if created:
                export_orders.append(order)
                self.stdout.write(self.style.SUCCESS(f'  Created export order: {order.order_number}'))
            else:
                export_orders.append(order)
                self.stdout.write(f'  Skipped (exists): {order.order_number}')

        # =============================================
        # 4. Create Export Items (6)
        # =============================================
        export_items_data = [
            # Items for EXP-2025-001 (3 items)
            {'order_idx': 0, 'product_idx': 3, 'description': 'وحدة تبريد صناعية 10 طن', 'hs_code': '8418.69', 'quantity': Decimal('2'), 'unit_price': Decimal('8500.00'), 'unit': 'piece'},
            {'order_idx': 0, 'product_idx': 4, 'description': 'مضخة مياه غاطسة 5 حصان', 'hs_code': '8413.70', 'quantity': Decimal('5'), 'unit_price': Decimal('2200.00'), 'unit': 'piece'},
            {'order_idx': 0, 'product_idx': 5, 'description': 'لوحة تحكم كهربائية PLC', 'hs_code': '8537.10', 'quantity': Decimal('2'), 'unit_price': Decimal('2750.00'), 'unit': 'piece'},
            # Items for EXP-2025-002 (3 items)
            {'order_idx': 1, 'product_idx': 6, 'description': 'مذيب صناعي Xylene', 'hs_code': '2902.44', 'quantity': Decimal('500'), 'unit_price': Decimal('18.00'), 'unit': 'liter'},
            {'order_idx': 1, 'product_idx': 7, 'description': 'مواد تشحيم صناعية كالسيوم', 'hs_code': '2710.19', 'quantity': Decimal('200'), 'unit_price': Decimal('25.00'), 'unit': 'liter'},
            {'order_idx': 1, 'product_idx': 8, 'description': 'مواد مانعة للتآكل', 'hs_code': '3811.11', 'quantity': Decimal('100'), 'unit_price': Decimal('42.00'), 'unit': 'kilogram'},
        ]

        export_item_count = 0
        for data in export_items_data:
            order_idx = data['order_idx']
            product_idx = data['product_idx']
            if order_idx >= len(export_orders):
                continue

            product = products[product_idx] if product_idx < len(products) else None

            item, created = ExportItem.objects.get_or_create(
                export_order=export_orders[order_idx],
                description=data['description'],
                defaults={
                    'product': product,
                    'hs_code': data['hs_code'],
                    'quantity': data['quantity'],
                    'unit_price': data['unit_price'],
                    'unit': data['unit'],
                },
            )
            if created:
                export_item_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created export item: {item.description[:40]}'))
            else:
                self.stdout.write(f'  Skipped (exists): {item.description[:40]}')

        # =============================================
        # 5. Create Customs Declarations (3)
        # =============================================
        customs_data = [
            {
                'declaration_number': 'CD-2025-001',
                'import_order_idx': 0,
                'export_order_idx': None,
                'declaration_type': 'import',
                'status': 'cleared',
                'declared_value': Decimal('45000.00'),
                'duties_amount': Decimal('6750.00'),
                'taxes_amount': Decimal('9000.00'),
                'notes': 'تم التخليص بنجاح بعد استكمال المستندات',
            },
            {
                'declaration_number': 'CD-2025-002',
                'import_order_idx': 1,
                'export_order_idx': None,
                'declaration_type': 'import',
                'status': 'submitted',
                'declared_value': Decimal('28000.00'),
                'duties_amount': Decimal('4200.00'),
                'taxes_amount': Decimal('5600.00'),
                'notes': 'بانتظار الفحص المخبري',
            },
            {
                'declaration_number': 'CD-2025-003',
                'import_order_idx': None,
                'export_order_idx': 0,
                'declaration_type': 'export',
                'status': 'cleared',
                'declared_value': Decimal('32000.00'),
                'duties_amount': Decimal('0.00'),
                'taxes_amount': Decimal('0.00'),
                'notes': 'تصدير - تم التخليص',
            },
        ]

        customs_count = 0
        for data in customs_data:
            import_idx = data['import_order_idx']
            export_idx = data['export_order_idx']

            import_order = import_orders[import_idx] if import_idx is not None and import_idx < len(import_orders) else None
            export_order = export_orders[export_idx] if export_idx is not None and export_idx < len(export_orders) else None

            defaults = {
                'declaration_type': data['declaration_type'],
                'declared_value': data['declared_value'],
                'duties_amount': data['duties_amount'],
                'taxes_amount': data['taxes_amount'],
                'notes': data['notes'],
                'created_by': admin_user,
            }

            if data['status'] == 'submitted':
                defaults['submitted_date'] = timezone.now().date()
            elif data['status'] == 'cleared':
                defaults['submitted_date'] = timezone.now().date()
                defaults['cleared_date'] = timezone.now().date()

            declaration, created = CustomsDeclaration.objects.get_or_create(
                declaration_number=data['declaration_number'],
                import_order=import_order,
                export_order=export_order,
                defaults=defaults,
            )
            if created:
                declaration.status = data['status']
                declaration.save()
                customs_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created customs declaration: {declaration.declaration_number}'))
            else:
                self.stdout.write(f'  Skipped (exists): {declaration.declaration_number}')

        # =============================================
        # Summary
        # =============================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Seed Summary ==='))
        self.stdout.write(f'  Import Orders created: {len(import_orders)} (total in DB: {ImportOrder.objects.count()})')
        self.stdout.write(f'  Import Items created: {item_count} (total in DB: {ImportItem.objects.count()})')
        self.stdout.write(f'  Export Orders created: {len(export_orders)} (total in DB: {ExportOrder.objects.count()})')
        self.stdout.write(f'  Export Items created: {export_item_count} (total in DB: {ExportItem.objects.count()})')
        self.stdout.write(f'  Customs Declarations created: {customs_count} (total in DB: {CustomsDeclaration.objects.count()})')
        self.stdout.write(self.style.SUCCESS('Done! Import/Export data seeded successfully.'))
