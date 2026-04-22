from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'إنشاء بيانات تجريبية لنقطة البيع - Create sample POS data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('بدء إنشاء البيانات التجريبية...'))

        # Get or create cashier user
        cashier, created = User.objects.get_or_create(
            username='cashier1',
            defaults={
                'first_name': 'أحمد',
                'last_name': 'محمد',
                'email': 'cashier1@example.com',
            }
        )
        if created:
            cashier.set_password('password123')
            cashier.save()
            self.stdout.write(f'تم إنشاء مستخدم: {cashier.username}')

        # Get or create manager user for processed_by fields
        manager, created = User.objects.get_or_create(
            username='manager1',
            defaults={
                'first_name': 'خالد',
                'last_name': 'علي',
                'email': 'manager1@example.com',
            }
        )
        if created:
            manager.set_password('password123')
            manager.save()
            self.stdout.write(f'تم إنشاء مستخدم: {manager.username}')

        from pos.models import (
            POSShift,
            POSSale,
            POSRefund,
            POSHoldOrder,
            CashDrawerTransaction,
        )

        # ─── Shift 1: Closed shift (yesterday) ───
        yesterday = timezone.now() - datetime.timedelta(days=1)
        shift1_number = f'SH-{yesterday.strftime("%Y%m%d")}-0001'
        shift1, created = POSShift.objects.get_or_create(
            shift_number=shift1_number,
            defaults={
                'cashier': cashier,
                'start_time': yesterday.replace(hour=8, minute=0, second=0, microsecond=0),
                'end_time': yesterday.replace(hour=16, minute=0, second=0, microsecond=0),
                'status': 'closed',
                'opening_cash': Decimal('5000.00'),
                'closing_cash': Decimal('18450.00'),
                'expected_cash': Decimal('18500.00'),
                'difference': Decimal('-50.00'),
                'total_sales': Decimal('13500.00'),
                'total_transactions': 12,
                'total_refunds': Decimal('0.00'),
                'notes': 'وردية عادية',
            }
        )
        if created:
            self.stdout.write(f'تم إنشاء الوردية: {shift1.shift_number} (مغلقة)')

        # ─── Shift 2: Open shift (today) ───
        today = timezone.now()
        shift2_number = f'SH-{today.strftime("%Y%m%d")}-0001'
        shift2, created = POSShift.objects.get_or_create(
            shift_number=shift2_number,
            defaults={
                'cashier': cashier,
                'start_time': today.replace(hour=9, minute=0, second=0, microsecond=0),
                'status': 'open',
                'opening_cash': Decimal('3000.00'),
                'total_sales': Decimal('0.00'),
                'total_transactions': 0,
                'total_refunds': Decimal('0.00'),
            }
        )
        if created:
            self.stdout.write(f'تم إنشاء الوردية: {shift2.shift_number} (مفتوحة)')

        # Create opening drawer transaction for shift2
        CashDrawerTransaction.objects.get_or_create(
            shift=shift2,
            transaction_type='opening',
            defaults={
                'amount': Decimal('3000.00'),
                'description': f'فتح الوردية {shift2.shift_number}',
                'created_by': cashier,
            }
        )

        # ─── Sample Products (try to get from inventory) ───
        sample_products = [
            {'id': 1, 'name': 'لاب توب HP ProBook', 'price': Decimal('4500.00')},
            {'id': 2, 'name': 'شاشة Dell 24 بوصة', 'price': Decimal('1200.00')},
            {'id': 3, 'name': 'ماوس لاسلكي Logitech', 'price': Decimal('150.00')},
            {'id': 4, 'name': 'لوحة مفاتيح ميكانيكية', 'price': Decimal('350.00')},
            {'id': 5, 'name': 'سماعات بلوتوث Sony', 'price': Decimal('280.00')},
        ]

        # ─── Sale 1: Cash sale ───
        sale1_items = [
            {
                'product_id': '1',
                'name': 'لاب توب HP ProBook',
                'quantity': 1,
                'unit_price': '4500.00',
                'discount': 0,
                'vat': round((4500 * 0.15), 2),
                'total': round(4500 + (4500 * 0.15), 2),
            },
            {
                'product_id': '3',
                'name': 'ماوس لاسلكي Logitech',
                'quantity': 2,
                'unit_price': '150.00',
                'discount': 0,
                'vat': round((300 * 0.15), 2),
                'total': round(300 + (300 * 0.15), 2),
            },
        ]
        sale1_subtotal = 4500 + 300
        sale1_vat = round(sale1_subtotal * 0.15, 2)
        sale1_total = sale1_subtotal + sale1_vat

        sale1_number = f'RCP-{today.strftime("%Y%m%d")}-0000001'
        sale1, created = POSSale.objects.get_or_create(
            receipt_number=sale1_number,
            defaults={
                'shift': shift2,
                'customer': None,
                'items': sale1_items,
                'subtotal': Decimal(str(sale1_subtotal)),
                'discount_amount': Decimal('0.00'),
                'vat_amount': Decimal(str(sale1_vat)),
                'total_amount': Decimal(str(sale1_total)),
                'payment_method': 'cash',
                'cash_received': Decimal('6000.00'),
                'change_amount': Decimal(str(round(6000 - sale1_total, 2))),
                'status': 'completed',
                'notes': 'بيع نقدية',
            }
        )
        if created:
            self.stdout.write(f'تم إنشاء عملية البيع: {sale1.receipt_number}')

        # ─── Sale 2: Card sale ───
        sale2_items = [
            {
                'product_id': '2',
                'name': 'شاشة Dell 24 بوصة',
                'quantity': 1,
                'unit_price': '1200.00',
                'discount': 0,
                'vat': round((1200 * 0.15), 2),
                'total': round(1200 + (1200 * 0.15), 2),
            },
        ]
        sale2_subtotal = 1200
        sale2_vat = round(sale2_subtotal * 0.15, 2)
        sale2_total = sale2_subtotal + sale2_vat

        sale2_number = f'RCP-{today.strftime("%Y%m%d")}-0000002'
        sale2, created = POSSale.objects.get_or_create(
            receipt_number=sale2_number,
            defaults={
                'shift': shift2,
                'customer': None,
                'items': sale2_items,
                'subtotal': Decimal(str(sale2_subtotal)),
                'discount_amount': Decimal('0.00'),
                'vat_amount': Decimal(str(sale2_vat)),
                'total_amount': Decimal(str(sale2_total)),
                'payment_method': 'card',
                'card_last_four': '4532',
                'status': 'completed',
                'notes': 'بيع ببطاقة',
            }
        )
        if created:
            self.stdout.write(f'تم إنشاء عملية البيع: {sale2.receipt_number}')

        # ─── Sale 3: Multiple items with discount ───
        sale3_items = [
            {
                'product_id': '4',
                'name': 'لوحة مفاتيح ميكانيكية',
                'quantity': 1,
                'unit_price': '350.00',
                'discount': 50,
                'vat': round((300 * 0.15), 2),
                'total': round(300 + (300 * 0.15), 2),
            },
            {
                'product_id': '5',
                'name': 'سماعات بلوتوث Sony',
                'quantity': 1,
                'unit_price': '280.00',
                'discount': 0,
                'vat': round((280 * 0.15), 2),
                'total': round(280 + (280 * 0.15), 2),
            },
        ]
        sale3_subtotal = 350 + 280
        sale3_discount = 50
        sale3_vat = round((sale3_subtotal - sale3_discount) * 0.15, 2)
        sale3_total = sale3_subtotal - sale3_discount + sale3_vat

        sale3_number = f'RCP-{today.strftime("%Y%m%d")}-0000003'
        sale3, created = POSSale.objects.get_or_create(
            receipt_number=sale3_number,
            defaults={
                'shift': shift2,
                'customer': None,
                'items': sale3_items,
                'subtotal': Decimal(str(sale3_subtotal)),
                'discount_amount': Decimal(str(sale3_discount)),
                'vat_amount': Decimal(str(sale3_vat)),
                'total_amount': Decimal(str(round(sale3_total, 2))),
                'payment_method': 'cash',
                'cash_received': Decimal('700.00'),
                'change_amount': Decimal(str(round(700 - sale3_total, 2))),
                'status': 'completed',
                'notes': 'بيع مع خصم',
            }
        )
        if created:
            self.stdout.write(f'تم إنشاء عملية البيع: {sale3.receipt_number}')

        # ─── Sale 4: Online payment ───
        sale4_items = [
            {
                'product_id': '1',
                'name': 'لاب توب HP ProBook',
                'quantity': 1,
                'unit_price': '4500.00',
                'discount': 200,
                'vat': round((4300 * 0.15), 2),
                'total': round(4300 + (4300 * 0.15), 2),
            },
        ]
        sale4_subtotal = 4500
        sale4_discount = 200
        sale4_vat = round((sale4_subtotal - sale4_discount) * 0.15, 2)
        sale4_total = sale4_subtotal - sale4_discount + sale4_vat

        sale4_number = f'RCP-{today.strftime("%Y%m%d")}-0000004'
        sale4, created = POSSale.objects.get_or_create(
            receipt_number=sale4_number,
            defaults={
                'shift': shift2,
                'customer': None,
                'items': sale4_items,
                'subtotal': Decimal(str(sale4_subtotal)),
                'discount_amount': Decimal(str(sale4_discount)),
                'vat_amount': Decimal(str(sale4_vat)),
                'total_amount': Decimal(str(round(sale4_total, 2))),
                'payment_method': 'online',
                'status': 'completed',
                'notes': 'بيع إلكتروني',
            }
        )
        if created:
            self.stdout.write(f'تم إنشاء عملية البيع: {sale4.receipt_number}')

        # ─── Sale 5: This one will be refunded ───
        sale5_items = [
            {
                'product_id': '5',
                'name': 'سماعات بلوتوث Sony',
                'quantity': 2,
                'unit_price': '280.00',
                'discount': 0,
                'vat': round((560 * 0.15), 2),
                'total': round(560 + (560 * 0.15), 2),
            },
        ]
        sale5_subtotal = 560
        sale5_vat = round(sale5_subtotal * 0.15, 2)
        sale5_total = sale5_subtotal + sale5_vat

        sale5_number = f'RCP-{today.strftime("%Y%m%d")}-0000005'
        sale5, created = POSSale.objects.get_or_create(
            receipt_number=sale5_number,
            defaults={
                'shift': shift2,
                'customer': None,
                'items': sale5_items,
                'subtotal': Decimal(str(sale5_subtotal)),
                'discount_amount': Decimal('0.00'),
                'vat_amount': Decimal(str(sale5_vat)),
                'total_amount': Decimal(str(sale5_total)),
                'payment_method': 'cash',
                'cash_received': Decimal('700.00'),
                'change_amount': Decimal(str(round(700 - sale5_total, 2))),
                'status': 'refunded',
                'notes': 'تم استرداد هذه العملية',
            }
        )
        if created:
            self.stdout.write(f'تم إنشاء عملية البيع: {sale5.receipt_number}')

        # ─── Refund for Sale 5 ───
        refund_number = f'REF-{today.strftime("%Y%m%d")}-0001'
        refund, created = POSRefund.objects.get_or_create(
            refund_number=refund_number,
            defaults={
                'sale': sale5,
                'shift': shift2,
                'items': [
                    {
                        'product_id': '5',
                        'name': 'سماعات بلوتوث Sony',
                        'quantity': 2,
                        'unit_price': '280.00',
                    }
                ],
                'refund_amount': Decimal(str(sale5_total)),
                'refund_method': 'cash',
                'reason': 'المنتج معيب - طلب العميل الإرجاع',
                'processed_by': manager,
            }
        )
        if created:
            self.stdout.write(f'تم إنشاء إرجاع: {refund.refund_number}')

        # Update shift2 totals
        total_sales = sum(
            s.total_amount for s in [sale1, sale2, sale3, sale4]
        )
        total_transactions = 4
        total_refunds = refund.refund_amount

        shift2.total_sales = total_sales
        shift2.total_transactions = total_transactions
        shift2.total_refunds = total_refunds
        shift2.save()
        self.stdout.write(f'تم تحديث إجماليات الوردية {shift2.shift_number}')

        self.stdout.write(self.style.SUCCESS('✅ تم إنشاء جميع البيانات التجريبية بنجاح!'))
        self.stdout.write(f'   - 2 ورديات (واحدة مغلقة، واحدة مفتوحة)')
        self.stdout.write(f'   - 5 عمليات بيع')
        self.stdout.write(f'   - 1 إرجاع')
