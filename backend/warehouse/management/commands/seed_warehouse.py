"""
Management command to seed sample warehouse data.
Creates warehouses and sample stock records for development.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from warehouse.models import Warehouse, WarehouseStock


class Command(BaseCommand):
    help = 'Seed sample warehouses and stock data for the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample warehouse data...')

        # Create warehouses
        warehouses_data = [
            {'name': 'المستودع الرئيسي', 'city': 'الرياض', 'address': 'حي الصناعية، شارع الملك فهد', 'capacity': 50000},
            {'name': 'مستودع فرع جدة', 'city': 'جدة', 'address': 'منطقة الحمراء، طريق المدينة', 'capacity': 30000},
            {'name': 'مستودع فرع الدمام', 'city': 'الدمام', 'address': 'حي الفيصلية، شارع الأمير محمد', 'capacity': 25000},
            {'name': 'مستودع المواد الخطرة', 'city': 'الرياض', 'address': 'خارج المنطقة الصناعية', 'capacity': 10000},
        ]

        wh_objects = {}
        for data in warehouses_data:
            wh, created = Warehouse.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            wh_objects[data['name']] = wh
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created warehouse: {wh.name} ({wh.code})'))
            else:
                self.stdout.write(f'  Skipped (exists): {wh.name}')

        # Set warehouse managers if employees exist
        try:
            from hr.models import Employee
            manager = Employee.objects.filter(first_name='عبدالله', last_name='الشمري').first()
            if manager:
                main_wh = wh_objects.get('المستودع الرئيسي')
                if main_wh and not main_wh.manager:
                    main_wh.manager = manager
                    main_wh.save()
                    self.stdout.write('  Set warehouse manager')
        except Exception:
            pass

        # Create sample stock records if products exist
        try:
            from inventory.models import Product
            products = Product.objects.all()[:10]
            if products.exists():
                stock_count = 0
                for wh in wh_objects.values():
                    for product in products:
                        stock, created = WarehouseStock.objects.get_or_create(
                            warehouse=wh,
                            product=product,
                            defaults={
                                'quantity': 100,
                                'reserved_quantity': 10,
                                'min_stock_level': 20,
                                'max_stock_level': 500,
                                'last_restock_date': timezone.now().date(),
                            },
                        )
                        if created:
                            stock_count += 1
                if stock_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'  Created {stock_count} stock records'))
        except Exception as e:
            self.stdout.write(f'  Skipped stock creation: {e}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Done! Warehouse data seeded successfully.'))
