"""
Management command to create sample products for testing.
Usage: python manage.py seed_products
"""

from django.core.management.base import BaseCommand
from inventory.models import Product


class Command(BaseCommand):
    help = 'Creates sample products for testing the inventory module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear all existing products before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Product.all_objects.count()
            Product.all_objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Cleared {count} existing product(s).'))

        sample_products = [
            {
                'name': 'لابتوب Dell Latitude 5540',
                'description': 'لابتوب أعمال بمعالج Intel Core i7 ورام 16GB وتخزين 512GB SSD',
                'sku': 'LAP-DELL-5540',
                'quantity': 25,
                'unit_price': 4500.00,
                'reorder_level': 5,
            },
            {
                'name': 'شاشة Samsung 27 بوصة',
                'description': 'شاشة IPS بدقة 4K مع دعم HDR',
                'sku': 'MON-SAM-274K',
                'quantity': 40,
                'unit_price': 1200.00,
                'reorder_level': 10,
            },
            {
                'name': 'ماوس لاسلكي Logitech MX Master 3',
                'description': 'ماوس لاسلكي متعدد الأجهزة مع شحن USB-C',
                'sku': 'MOU-LOG-MX3',
                'quantity': 100,
                'unit_price': 350.00,
                'reorder_level': 20,
            },
            {
                'name': 'لوحة مفاتيح ميكانيكية Keychron K2',
                'description': 'لوحة مفاتيح بلوتوث مع إضاءة RGB مفاتيح أزرار ميكانيكية',
                'sku': 'KEY-KCH-K2',
                'quantity': 3,
                'unit_price': 450.00,
                'reorder_level': 10,
            },
            {
                'name': 'طابعة HP LaserJet Pro M404dn',
                'description': 'طابعة ليزر مزدوجة الوجه سرعة 40 صفحة بالدقيقة',
                'sku': 'PRT-HP-M404',
                'quantity': 15,
                'unit_price': 1800.00,
                'reorder_level': 5,
            },
            {
                'name': 'سماعة Jabra Evolve2 85',
                'description': 'سماعة رأس لاسلكية مع إلغاء الضوضاء النشط',
                'sku': 'HSD-JBR-E285',
                'quantity': 2,
                'unit_price': 950.00,
                'reorder_level': 8,
            },
            {
                'name': 'كابل HDMI 2.1 - 2 متر',
                'description': 'كابل HDMI عالي السرعة يدعم 8K و4K@120Hz',
                'sku': 'CAB-HDMI-2M',
                'quantity': 200,
                'unit_price': 45.00,
                'reorder_level': 50,
            },
            {
                'name': 'حبر طابعة HP 26A أسود',
                'description': 'خرطوشة حبر أصلي لطابعات HP LaserJet',
                'sku': 'INK-HP-26A',
                'quantity': 8,
                'unit_price': 250.00,
                'reorder_level': 15,
            },
            {
                'name': 'هارد خارجي WD Elements 2TB',
                'description': 'قرص صلب خارجي USB 3.0 سعة 2 تيرابايت',
                'sku': 'HDD-WD-2TB',
                'quantity': 30,
                'unit_price': 280.00,
                'reorder_level': 10,
            },
            {
                'name': 'ويب كام Logitech C920 HD Pro',
                'description': 'كاميرا ويب بدقة 1080p مع مايكروفون مدمج',
                'sku': 'CAM-LOG-C920',
                'quantity': 0,
                'unit_price': 550.00,
                'reorder_level': 5,
            },
        ]

        created_count = 0
        skipped_count = 0

        for product_data in sample_products:
            _, created = Product.all_objects.update_or_create(
                sku=product_data['sku'],
                defaults=product_data,
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete!\n'
                f'  Created: {created_count} product(s)\n'
                f'  Updated: {skipped_count} product(s)\n'
                f'  Total: {created_count + skipped_count} product(s)'
            )
        )
