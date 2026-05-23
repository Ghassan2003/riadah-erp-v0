"""
Management command to seed sample assets data.
Creates asset categories and sample fixed assets for development.
"""

from django.core.management.base import BaseCommand
from datetime import date, timedelta
from assets.models import AssetCategory, FixedAsset


class Command(BaseCommand):
    help = 'Seed sample asset categories and fixed assets for the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample assets data...')

        # Create asset categories
        categories_data = [
            {'name': 'أجهزة الحاسب', 'name_en': 'Computers', 'useful_life_years': 3, 'depreciation_method': 'straight_line', 'salvage_value_rate': 10},
            {'name': 'المركبات', 'name_en': 'Vehicles', 'useful_life_years': 5, 'depreciation_method': 'straight_line', 'salvage_value_rate': 15},
            {'name': 'الأثاث المكتبي', 'name_en': 'Office Furniture', 'useful_life_years': 10, 'depreciation_method': 'straight_line', 'salvage_value_rate': 5},
            {'name': 'الأجهزة والمعدات', 'name_en': 'Equipment & Machinery', 'useful_life_years': 7, 'depreciation_method': 'declining_balance', 'salvage_value_rate': 10},
            {'name': 'الأجهزة الطرفية', 'name_en': 'Peripheral Devices', 'useful_life_years': 3, 'depreciation_method': 'straight_line', 'salvage_value_rate': 10},
        ]

        cat_objects = {}
        for data in categories_data:
            cat, created = AssetCategory.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            cat_objects[data['name']] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created category: {cat.name}'))
            else:
                self.stdout.write(f'  Skipped (exists): {cat.name}')

        # Get department and supplier references
        try:
            from hr.models import Department, Employee
            dept = Department.objects.filter(name='تقنية المعلومات').first()
            emp = Employee.objects.filter(first_name='نورة', last_name='العنزي').first()
        except Exception:
            dept = None
            emp = None

        try:
            from purchases.models import Supplier
            supplier = Supplier.objects.first()
        except Exception:
            supplier = None

        # Create sample fixed assets
        assets_data = [
            {'name': 'حاسوب محمول Dell Latitude', 'name_en': 'Dell Latitude Laptop', 'category': 'أجهزة الحاسب', 'serial_number': 'DL-LT-2024-001', 'purchase_price': 5500, 'useful_life_months': 36},
            {'name': 'طابعة HP LaserJet', 'name_en': 'HP LaserJet Printer', 'category': 'الأجهزة الطرفية', 'serial_number': 'HP-LJ-2024-001', 'purchase_price': 3200, 'useful_life_months': 36},
            {'name': 'مكتب خشبي VIP', 'name_en': 'Wooden VIP Desk', 'category': 'الأثاث المكتبي', 'serial_number': 'DSK-001', 'purchase_price': 4500, 'useful_life_months': 120},
            {'name': 'شاشة عرض Samsung 55"', 'name_en': 'Samsung 55" Display', 'category': 'الأجهزة والمعدات', 'serial_number': 'SAM-55-001', 'purchase_price': 2800, 'useful_life_months': 84},
            {'name': 'سيارة تويوتا كامري 2024', 'name_en': 'Toyota Camry 2024', 'category': 'المركبات', 'serial_number': 'TOY-CAM-2024-001', 'purchase_price': 120000, 'useful_life_months': 60},
        ]

        asset_count = 0
        for data in assets_data:
            cat_name = data.pop('category')
            cat = cat_objects.get(cat_name)
            if not cat:
                continue

            salvage = round(data['purchase_price'] * (cat.salvage_value_rate / 100), 2)

            asset, created = FixedAsset.objects.get_or_create(
                serial_number=data['serial_number'],
                defaults={
                    'name': data['name'],
                    'name_en': data.get('name_en', ''),
                    'category': cat,
                    'purchase_date': date(2024, 1, 15),
                    'purchase_price': data['purchase_price'],
                    'salvage_value': salvage,
                    'useful_life_months': data['useful_life_months'],
                    'location': 'المكتب الرئيسي',
                    'department': dept,
                    'assigned_to': emp if asset_count == 0 else None,
                    'supplier': supplier,
                    'warranty_end_date': date.today() + timedelta(days=365),
                    'status': 'active',
                },
            )
            if created:
                asset_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created asset: {asset.name} ({asset.asset_number})'))
            else:
                self.stdout.write(f'  Skipped (exists): {asset.name}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done! Created {asset_count} fixed assets.'))
