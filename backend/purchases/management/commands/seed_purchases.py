"""
Management command to create sample suppliers and purchase orders for testing.
Usage: python manage.py seed_purchases
"""

from django.core.management.base import BaseCommand
from purchases.models import Supplier, PurchaseOrder, PurchaseOrderItem
from inventory.models import Product
from users.models import User
from django.utils import timezone
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Creates sample suppliers and purchase orders for testing the purchases module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing purchase data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            PurchaseOrderItem.objects.all().delete()
            PurchaseOrder.objects.all().delete()
            Supplier.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all purchase data.'))

        # Seed suppliers
        suppliers_data = [
            {
                'name': 'شركة التقنية المتقدمة',
                'name_en': 'Advanced Technology Co.',
                'contact_person': 'أحمد محمد',
                'email': 'info@advtech.sa',
                'phone': '+966501234567',
                'address': 'الرياض، حي العليا، شارع التحلية',
                'tax_number': '300012345600003',
            },
            {
                'name': 'مؤسسة الأثاث الحديث',
                'name_en': 'Modern Furniture Est.',
                'contact_person': 'خالد العمري',
                'email': 'sales@modernfurn.sa',
                'phone': '+966509876543',
                'address': 'جدة، حي الروضة، شارع الملك فهد',
                'tax_number': '300098765400003',
            },
            {
                'name': 'شركة الموردين الموحدون',
                'name_en': 'United Suppliers Co.',
                'contact_person': 'سعد الدوسري',
                'email': 'contact@unitedsup.sa',
                'phone': '+966507654321',
                'address': 'الدمام، حي الشاطئ، شارع الأمير محمد',
                'tax_number': '300076543200003',
            },
            {
                'name': 'شركة الورق والأدوات المكتبية',
                'name_en': 'Paper & Office Supplies Co.',
                'contact_person': 'فهد القحطاني',
                'email': 'orders@papersupplies.sa',
                'phone': '+966503456789',
                'address': 'الرياض، حي النرجس، طريق أنس بن مالك',
                'tax_number': '300034567800003',
            },
            {
                'name': 'مؤسسة الأجهزة الكهربائية',
                'name_en': 'Electrical Devices Est.',
                'contact_person': 'عبدالله الشهري',
                'email': 'info@elecdevices.sa',
                'phone': '+966502345678',
                'address': 'مكة المكرمة، حي العزيزية',
                'tax_number': '300023456700003',
            },
        ]

        created_suppliers = 0
        for supplier_data in suppliers_data:
            _, created = Supplier.objects.update_or_create(
                email=supplier_data['email'],
                defaults=supplier_data,
            )
            if created:
                created_suppliers += 1

        self.stdout.write(f'Created {created_suppliers} supplier(s).')

        # Create purchase orders
        suppliers = list(Supplier.objects.all())
        products = list(Product.objects.all())
        admin_user = User.objects.filter(role='admin').first()

        if not suppliers:
            self.stdout.write(self.style.WARNING('No suppliers found, skipping purchase orders.'))
            return

        if not products:
            self.stdout.write(self.style.WARNING('No products found, skipping purchase orders.'))
            return

        orders_data = [
            {
                'supplier': suppliers[0],
                'status': 'confirmed',
                'expected_date': date.today() + timedelta(days=7),
                'notes': 'طلب أجهزة حاسوب للمكاتب',
                'items': [
                    {'product': products[0], 'quantity': 10, 'unit_price': 4200.00} if len(products) > 0 else None,
                    {'product': products[1], 'quantity': 5, 'unit_price': 1100.00} if len(products) > 1 else None,
                ],
            },
            {
                'supplier': suppliers[1],
                'status': 'received',
                'expected_date': date.today() - timedelta(days=5),
                'notes': 'طلب أثاث لمكتب الإدارة',
                'items': [
                    {'product': products[4], 'quantity': 3, 'unit_price': 1700.00} if len(products) > 4 else None,
                ],
            },
            {
                'supplier': suppliers[2],
                'status': 'draft',
                'expected_date': date.today() + timedelta(days=14),
                'notes': 'طلب مواد مكتبية متنوعة',
                'items': [
                    {'product': products[6], 'quantity': 50, 'unit_price': 40.00} if len(products) > 6 else None,
                    {'product': products[7], 'quantity': 20, 'unit_price': 230.00} if len(products) > 7 else None,
                ],
            },
            {
                'supplier': suppliers[3],
                'status': 'partial',
                'expected_date': date.today() + timedelta(days=3),
                'notes': 'طلب حبر ولوازم طباعة',
                'items': [
                    {'product': products[7], 'quantity': 30, 'unit_price': 240.00} if len(products) > 7 else None,
                ],
            },
        ]

        created_orders = 0
        for order_data in orders_data:
            items = [i for i in order_data.pop('items') if i is not None]
            if not items:
                continue

            order = PurchaseOrder.objects.create(
                supplier=order_data['supplier'],
                status=order_data['status'],
                expected_date=order_data['expected_date'],
                notes=order_data['notes'],
                created_by=admin_user,
            )
            order.save()  # Generate order number

            for item_data in items:
                PurchaseOrderItem.objects.create(
                    order=order,
                    product=item_data['product'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                )
            order.calculate_total()
            created_orders += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete!\n'
                f'  Suppliers: {created_suppliers} created\n'
                f'  Purchase Orders: {created_orders} created'
            )
        )
