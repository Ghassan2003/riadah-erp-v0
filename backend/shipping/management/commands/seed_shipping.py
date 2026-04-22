"""
Management command to seed sample Shipping data.
Creates ShippingMethods, Shipments, ShipmentItems, ShipmentEvents, and DeliveryAttempts
for development and testing.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from shipping.models import (
    ShippingMethod,
    Shipment,
    ShipmentItem,
    ShipmentEvent,
    DeliveryAttempt,
)


class Command(BaseCommand):
    help = 'Seed sample shipping data for the ERP system'

    def handle(self, *args, **options):
        from sales.models import Customer
        from inventory.models import Product
        from users.models import User

        self.stdout.write('Creating sample Shipping data...')

        # Ensure prerequisites exist
        customers = list(Customer.objects.all()[:6])
        if not customers:
            self.stdout.write(self.style.ERROR('  No customers found. Run seed_sales first.'))
            return

        products = list(Product.objects.all()[:10])
        if not products:
            self.stdout.write(self.style.ERROR('  No products found. Run seed_inventory first.'))
            return

        admin_user = User.objects.filter(role='admin').first()

        # =============================================
        # 1. Create Shipping Methods (4)
        # =============================================
        methods_data = [
            {
                'name': 'شحن سريع',
                'description': 'خدمة الشحن السريع خلال يوم إلى يومين عمل',
                'carrier': 'أرامكس',
                'tracking_url': 'https://www.aramex.com/track/{tracking}',
                'cost_type': 'flat_rate',
                'base_cost': Decimal('50.00'),
                'cost_per_unit': Decimal('0'),
                'estimated_days': 2,
                'is_active': True,
            },
            {
                'name': 'شحن عادي',
                'description': 'الشحن البريدي العادي خلال 3 إلى 5 أيام عمل',
                'carrier': 'البريد السعودي',
                'tracking_url': 'https://www.spl.com.sa/track/{tracking}',
                'cost_type': 'weight_based',
                'base_cost': Decimal('15.00'),
                'cost_per_unit': Decimal('5.00'),
                'estimated_days': 5,
                'is_active': True,
            },
            {
                'name': 'شحن مجاني',
                'description': 'شحن مجاني للطلبات فوق 500 ريال',
                'carrier': 'شركة التوصيل الداخلي',
                'tracking_url': '',
                'cost_type': 'free',
                'base_cost': Decimal('0'),
                'cost_per_unit': Decimal('0'),
                'estimated_days': 7,
                'is_active': True,
            },
            {
                'name': 'شحن دولي',
                'description': 'شحن دولي للمنتجات المصدرة مع تأمين شامل',
                'carrier': 'DHL',
                'tracking_url': 'https://www.dhl.com/track/{tracking}',
                'cost_type': 'volume_based',
                'base_cost': Decimal('120.00'),
                'cost_per_unit': Decimal('8.50'),
                'estimated_days': 14,
                'is_active': True,
            },
        ]

        methods = []
        for data in methods_data:
            method, created = ShippingMethod.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            methods.append(method)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created shipping method: {method.name}'))
            else:
                self.stdout.write(f'  Skipped (exists): {method.name}')

        # =============================================
        # 2. Create Shipments (6)
        # =============================================
        now = timezone.now()
        shipments_data = [
            {
                'shipment_number': 'SHP-2025-0001',
                'customer': customers[0] if len(customers) > 0 else None,
                'shipping_method': methods[0] if len(methods) > 0 else None,
                'status': 'delivered',
                'weight': Decimal('2.50'),
                'dimensions': '30x20x15 سم',
                'origin_address': 'مستودع الرياض الرئيسي، طريق الملك فهد، الرياض',
                'destination_address': 'شارع الأمير سلطان، جدة',
                'tracking_number': 'ARMX-789456123',
                'estimated_delivery': now - timedelta(days=5),
                'actual_delivery': now - timedelta(days=4),
                'shipping_cost': Decimal('50.00'),
                'insurance_amount': Decimal('200.00'),
                'notes': 'تم التوصيل بنجاح',
            },
            {
                'shipment_number': 'SHP-2025-0002',
                'customer': customers[1] if len(customers) > 1 else None,
                'shipping_method': methods[1] if len(methods) > 1 else None,
                'status': 'in_transit',
                'weight': Decimal('5.75'),
                'dimensions': '50x40x30 سم',
                'origin_address': 'مستودع الرياض الرئيسي، طريق الملك فهد، الرياض',
                'destination_address': 'حي النزهة، الدمام',
                'tracking_number': 'SPL-456789123',
                'estimated_delivery': now + timedelta(days=2),
                'actual_delivery': None,
                'shipping_cost': Decimal('43.75'),
                'insurance_amount': Decimal('0'),
                'notes': 'في الطريق إلى الدمام',
            },
            {
                'shipment_number': 'SHP-2025-0003',
                'customer': customers[2] if len(customers) > 2 else None,
                'shipping_method': methods[2] if len(methods) > 2 else None,
                'status': 'pending',
                'weight': Decimal('1.00'),
                'dimensions': '20x15x10 سم',
                'origin_address': 'مستودع جدة، حي الصفا',
                'destination_address': 'شارع التحلية، مكة المكرمة',
                'tracking_number': '',
                'estimated_delivery': now + timedelta(days=7),
                'actual_delivery': None,
                'shipping_cost': Decimal('0'),
                'insurance_amount': Decimal('0'),
                'notes': 'شحن مجاني',
            },
            {
                'shipment_number': 'SHP-2025-0004',
                'customer': customers[3] if len(customers) > 3 else None,
                'shipping_method': methods[3] if len(methods) > 3 else None,
                'status': 'packed',
                'weight': Decimal('12.00'),
                'dimensions': '80x60x50 سم',
                'origin_address': 'مستودع الرياض الرئيسي، طريق الملك فهد، الرياض',
                'destination_address': 'Dubai, UAE',
                'tracking_number': 'DHL-123456789',
                'estimated_delivery': now + timedelta(days=10),
                'actual_delivery': None,
                'shipping_cost': Decimal('650.00'),
                'insurance_amount': Decimal('5000.00'),
                'notes': 'شحنة تصدير مع تأمين شامل',
            },
            {
                'shipment_number': 'SHP-2025-0005',
                'customer': customers[4] if len(customers) > 4 else None,
                'shipping_method': methods[0] if len(methods) > 0 else None,
                'status': 'out_for_delivery',
                'weight': Decimal('0.80'),
                'dimensions': '25x15x10 سم',
                'origin_address': 'مستودع الرياض الرئيسي، طريق الملك فهد، الرياض',
                'destination_address': 'حي الياسمين، الرياض',
                'tracking_number': 'ARMX-321654987',
                'estimated_delivery': now,
                'actual_delivery': None,
                'shipping_cost': Decimal('50.00'),
                'insurance_amount': Decimal('150.00'),
                'notes': 'خارج للتوصيل',
            },
            {
                'shipment_number': 'SHP-2025-0006',
                'customer': customers[5] if len(customers) > 5 else None,
                'shipping_method': methods[1] if len(methods) > 1 else None,
                'status': 'returned',
                'weight': Decimal('3.25'),
                'dimensions': '35x25x20 سم',
                'origin_address': 'مستودع الرياض الرئيسي، طريق الملك فهد، الرياض',
                'destination_address': 'حي الروضة، الخبر',
                'tracking_number': 'SPL-987654321',
                'estimated_delivery': now - timedelta(days=10),
                'actual_delivery': None,
                'shipping_cost': Decimal('31.25'),
                'insurance_amount': Decimal('0'),
                'notes': 'مرتجع - العميل رفض الاستلام',
            },
        ]

        shipments = []
        for data in shipments_data:
            if not data['customer'] or not data['shipping_method']:
                continue
            shipment, created = Shipment.objects.get_or_create(
                shipment_number=data['shipment_number'],
                defaults={**data, 'created_by': admin_user},
            )
            shipments.append(shipment)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created shipment: {shipment.shipment_number} ({shipment.get_status_display()})'))
            else:
                self.stdout.write(f'  Skipped (exists): {shipment.shipment_number}')

        # =============================================
        # 3. Create Shipment Items (12)
        # =============================================
        items_data = [
            # Items for SHP-2025-0001 (2 items)
            {'shipment_idx': 0, 'product_idx': 0, 'quantity': 2, 'unit_price': Decimal('150.00'), 'weight': Decimal('1.20')},
            {'shipment_idx': 0, 'product_idx': 1, 'quantity': 1, 'unit_price': Decimal('280.00'), 'weight': Decimal('1.30')},
            # Items for SHP-2025-0002 (3 items)
            {'shipment_idx': 1, 'product_idx': 2, 'quantity': 5, 'unit_price': Decimal('45.00'), 'weight': Decimal('2.50')},
            {'shipment_idx': 1, 'product_idx': 3, 'quantity': 2, 'unit_price': Decimal('120.00'), 'weight': Decimal('1.75')},
            {'shipment_idx': 1, 'product_idx': 4, 'quantity': 1, 'unit_price': Decimal('350.00'), 'weight': Decimal('1.50')},
            # Items for SHP-2025-0003 (1 item)
            {'shipment_idx': 2, 'product_idx': 5, 'quantity': 1, 'unit_price': Decimal('85.00'), 'weight': Decimal('1.00')},
            # Items for SHP-2025-0004 (2 items)
            {'shipment_idx': 3, 'product_idx': 6, 'quantity': 3, 'unit_price': Decimal('500.00'), 'weight': Decimal('7.50')},
            {'shipment_idx': 3, 'product_idx': 7, 'quantity': 1, 'unit_price': Decimal('1200.00'), 'weight': Decimal('4.50')},
            # Items for SHP-2025-0005 (1 item)
            {'shipment_idx': 4, 'product_idx': 8, 'quantity': 1, 'unit_price': Decimal('320.00'), 'weight': Decimal('0.80')},
            # Items for SHP-2025-0006 (3 items)
            {'shipment_idx': 5, 'product_idx': 0, 'quantity': 1, 'unit_price': Decimal('150.00'), 'weight': Decimal('0.60')},
            {'shipment_idx': 5, 'product_idx': 9, 'quantity': 2, 'unit_price': Decimal('95.00'), 'weight': Decimal('1.65')},
        ]

        items_count = 0
        for data in items_data:
            s_idx = data['shipment_idx']
            p_idx = data['product_idx']
            if s_idx >= len(shipments) or p_idx >= len(products):
                continue

            item, created = ShipmentItem.objects.get_or_create(
                shipment=shipments[s_idx],
                product=products[p_idx],
                defaults={
                    'quantity': data['quantity'],
                    'unit_price': data['unit_price'],
                    'weight': data['weight'],
                },
            )
            if created:
                items_count += 1

        self.stdout.write(self.style.SUCCESS(f'  Created {items_count} shipment items'))

        # =============================================
        # 4. Create Shipment Events (15)
        # =============================================
        events_data = [
            # Events for SHP-2025-0001 (delivered)
            {'shipment_idx': 0, 'event_type': 'created', 'location': 'الرياض', 'description': 'تم إنشاء الشحنة في المستودع الرئيسي', 'days_offset': -7},
            {'shipment_idx': 0, 'event_type': 'picked', 'location': 'الرياض', 'description': 'تم تجهيز الشحنة من المستودع', 'days_offset': -6},
            {'shipment_idx': 0, 'event_type': 'packed', 'location': 'الرياض', 'description': 'تم تغليف الشحنة', 'days_offset': -6},
            {'shipment_idx': 0, 'event_type': 'shipped', 'location': 'الرياض', 'description': 'تم تسليم الشحنة لناقل الشحن', 'days_offset': -5},
            {'shipment_idx': 0, 'event_type': 'delivered', 'location': 'جدة', 'description': 'تم تسليم الشحنة للعميل بنجاح', 'days_offset': -4},
            # Events for SHP-2025-0002 (in_transit)
            {'shipment_idx': 1, 'event_type': 'created', 'location': 'الرياض', 'description': 'تم إنشاء الشحنة', 'days_offset': -3},
            {'shipment_idx': 1, 'event_type': 'picked', 'location': 'الرياض', 'description': 'تم تجهيز الشحنة', 'days_offset': -2},
            {'shipment_idx': 1, 'event_type': 'packed', 'location': 'الرياض', 'description': 'تم تغليف الشحنة', 'days_offset': -2},
            {'shipment_idx': 1, 'event_type': 'in_transit', 'location': 'الرياض - الدمام', 'description': 'الشحنة في الطريق إلى الدمام', 'days_offset': -1},
            # Events for SHP-2025-0004 (packed)
            {'shipment_idx': 3, 'event_type': 'created', 'location': 'الرياض', 'description': 'تم إنشاء الشحنة الدولية', 'days_offset': -2},
            {'shipment_idx': 3, 'event_type': 'packed', 'location': 'الرياض', 'description': 'تم تغليف الشحنة وتجهيزها للتصدير', 'days_offset': -1},
            # Events for SHP-2025-0005 (out_for_delivery)
            {'shipment_idx': 4, 'event_type': 'created', 'location': 'الرياض', 'description': 'تم إنشاء الشحنة', 'days_offset': -2},
            {'shipment_idx': 4, 'event_type': 'shipped', 'location': 'الرياض', 'description': 'تم شحن الشحنة', 'days_offset': -1},
            {'shipment_idx': 4, 'event_type': 'out_for_delivery', 'location': 'الرياض', 'description': 'الشحنة خارج للتوصيل', 'days_offset': 0},
        ]

        events_count = 0
        for data in events_data:
            s_idx = data['shipment_idx']
            if s_idx >= len(shipments):
                continue

            event, created = ShipmentEvent.objects.get_or_create(
                shipment=shipments[s_idx],
                event_type=data['event_type'],
                description=data['description'],
                defaults={
                    'location': data['location'],
                    'created_at': now + timedelta(days=data['days_offset']),
                },
            )
            if created:
                events_count += 1

        self.stdout.write(self.style.SUCCESS(f'  Created {events_count} shipment events'))

        # =============================================
        # 5. Create Delivery Attempts (3)
        # =============================================
        attempts_data = [
            # Delivery attempt for SHP-2025-0001 (success)
            {'shipment_idx': 0, 'attempt_number': 1, 'attempt_date': now - timedelta(days=4), 'status': 'success', 'recipient_name': 'أحمد محمد', 'notes': 'تم التسليم بنجاح'},
            # Delivery attempts for SHP-2025-0006 (returned)
            {'shipment_idx': 5, 'attempt_number': 1, 'attempt_date': now - timedelta(days=3), 'status': 'fail', 'recipient_name': '', 'notes': 'العميل غير متواجد في العنوان'},
            {'shipment_idx': 5, 'attempt_number': 2, 'attempt_date': now - timedelta(days=1), 'status': 'fail', 'recipient_name': 'جار العميل', 'notes': 'العميل رفض الاستلام'},
        ]

        attempts_count = 0
        for data in attempts_data:
            s_idx = data['shipment_idx']
            if s_idx >= len(shipments):
                continue

            attempt, created = DeliveryAttempt.objects.get_or_create(
                shipment=shipments[s_idx],
                attempt_number=data['attempt_number'],
                defaults={
                    'attempt_date': data['attempt_date'],
                    'status': data['status'],
                    'recipient_name': data['recipient_name'],
                    'notes': data['notes'],
                },
            )
            if created:
                attempts_count += 1

        self.stdout.write(self.style.SUCCESS(f'  Created {attempts_count} delivery attempts'))

        # =============================================
        # Summary
        # =============================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Seed Summary ==='))
        self.stdout.write(f'  Shipping Methods: {len(methods)} (or existed)')
        self.stdout.write(f'  Shipments: {len(shipments)} (or existed)')
        self.stdout.write(f'  Shipment Items created: {items_count}')
        self.stdout.write(f'  Shipment Events created: {events_count}')
        self.stdout.write(f'  Delivery Attempts created: {attempts_count}')
        self.stdout.write(self.style.SUCCESS('Done! Shipping data seeded successfully.'))
