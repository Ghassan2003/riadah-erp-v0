"""
Management command to create sample customers and sales orders for testing.
Usage: python manage.py seed_sales
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from sales.models import Customer, SalesOrder, SalesOrderItem


class Command(BaseCommand):
    help = 'Creates sample customers and sales orders for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing customers and orders before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            SalesOrderItem.objects.all().delete()
            SalesOrder.objects.all().delete()
            Customer.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all customers and orders.'))

        customers_data = [
            {'name': 'شركة الفا التقنية', 'email': 'info@alfatech.com', 'phone': '0501234567', 'address': 'الرياض، حي العليا، شارع التحلية'},
            {'name': 'مؤسسة النور للتجارة', 'email': 'sales@alnoor.com', 'phone': '0559876543', 'address': 'جدة، حي الروضة، طريق الملك فهد'},
            {'name': 'شركة البناء المتقدم', 'email': 'contact@advanced-bldg.com', 'phone': '0531112233', 'address': 'الدمام، حي الشاطئ، طريق الخليج'},
            {'name': 'مكتبة المعرفة', 'email': 'info@knowledge-books.com', 'phone': '0544455666', 'address': 'المدينة المنورة، حي العزيزية'},
            {'name': 'مستشفى السلام التخصصي', 'email': 'procurement@alsalam-hospital.com', 'phone': '0567788990', 'address': 'الرياض، حي النزهة، شارع الحسن'},
        ]

        created_customers = 0
        for data in customers_data:
            _, created = Customer.objects.get_or_create(
                email=data['email'], defaults=data
            )
            if created:
                created_customers += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created_customers} customer(s). Total: {Customer.objects.count()}'))

        # Try to create sample orders if products exist
        try:
            from inventory.models import Product
            products = list(Product.objects.all()[:5])

            if not products:
                self.stdout.write(self.style.WARNING('No products found. Run seed_products first.'))
                return

            from users.models import User
            admin_user = User.objects.filter(role='admin').first()

            # Create 3 sample orders
            orders_data = [
                {
                    'customer': Customer.objects.first(),
                    'status': 'confirmed',
                    'items': [
                        {'product': products[0], 'quantity': 2},
                        {'product': products[1], 'quantity': 3},
                    ],
                },
                {
                    'customer': Customer.objects.all()[1] if Customer.objects.count() > 1 else Customer.objects.first(),
                    'status': 'draft',
                    'items': [
                        {'product': products[2], 'quantity': 1},
                    ],
                },
                {
                    'customer': Customer.objects.all()[2] if Customer.objects.count() > 2 else Customer.objects.first(),
                    'status': 'delivered',
                    'items': [
                        {'product': products[0], 'quantity': 1},
                        {'product': products[3], 'quantity': 5} if len(products) > 3 else {'product': products[0], 'quantity': 1},
                    ],
                },
            ]

            created_orders = 0
            for order_data in orders_data:
                order_items = order_data.pop('items')
                order, created = SalesOrder.objects.get_or_create(
                    customer=order_data['customer'],
                    status=order_data['status'],
                    defaults={**order_data, 'created_by': admin_user},
                )
                if created:
                    for item_data in order_items:
                        SalesOrderItem.objects.create(
                            order=order,
                            product=item_data['product'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['product'].unit_price,
                        )
                    order.calculate_total()
                    created_orders += 1

            self.stdout.write(self.style.SUCCESS(f'Created {created_orders} order(s). Total: {SalesOrder.objects.count()}'))

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not create orders: {e}'))
