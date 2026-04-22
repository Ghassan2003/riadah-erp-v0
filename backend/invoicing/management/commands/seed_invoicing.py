"""Management command to seed sample invoicing data."""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from invoicing.models import Invoice, InvoiceItem, Payment, PaymentReminder

class Command(BaseCommand):
    help = 'Seed sample invoices for the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample invoicing data...')
        try:
            from sales.models import Customer, SalesOrder, SalesOrderItem
            from inventory.models import Product
            from users.models import User
        except ImportError as e:
            self.stdout.write(f'Skipping - missing dependency: {e}')
            return

        admin = User.objects.filter(username='admin').first()
        if not admin:
            self.stdout.write('No admin user found. Skipping.')
            return

        customers = list(Customer.objects.filter(is_active=True)[:3])
        products = list(Product.objects.filter(is_active=True)[:5])

        if not customers or not products:
            self.stdout.write('No customers or products found. Run seed_sales and seed_products first.')
            return

        count = 0
        for i, customer in enumerate(customers):
            inv_num = f'INV-{date.today().strftime("%Y%m%d")}-{(i+1):04d}'
            subtotal = 0
            inv, created = Invoice.objects.get_or_create(
                invoice_number=inv_num,
                defaults={
                    'invoice_type': 'sales',
                    'customer': customer,
                    'issue_date': date.today() - timedelta(days=i*5),
                    'due_date': date.today() + timedelta(days=30 - i*5),
                    'discount_type': 'percentage',
                    'discount_value': 5 if i == 0 else 0,
                    'vat_rate': 15,
                    'status': ['sent', 'paid', 'accepted'][i] if i < 3 else 'draft',
                    'payment_status': ['unpaid', 'paid', 'partially_paid'][i] if i < 3 else 'unpaid',
                    'created_by': admin,
                    'company_tax_number': '300000000000003',
                    'currency': 'SAR',
                }
            )
            if not created:
                continue
            count += 1

            for j, product in enumerate(products[:3]):
                qty = (j + 1) * 2
                price = float(product.unit_price)
                item_sub = qty * price
                vat = item_sub * 0.15
                InvoiceItem.objects.create(
                    invoice=inv,
                    product=product,
                    description=product.name,
                    quantity=qty,
                    unit_price=price,
                    subtotal=item_sub,
                    vat_rate=15,
                    vat_amount=round(vat, 2),
                    total=round(item_sub + vat, 2),
                )
                subtotal += item_sub

            inv.subtotal = subtotal
            inv.recalculate_totals()
            inv.save()

        # Create payments
        invoices = Invoice.objects.filter(payment_status='paid')
        for inv in invoices[:2]:
            pay_num = f'PAY-{date.today().strftime("%Y%m%d")}-{Invoice.objects.filter(invoice_type__startswith="sales").count():04d}'
            Payment.objects.get_or_create(
                payment_number=pay_num,
                defaults={
                    'invoice': inv,
                    'amount': inv.total_amount,
                    'payment_method': 'bank_transfer',
                    'payment_date': date.today() - timedelta(days=3),
                    'reference_number': f'TRF-{date.today().strftime("%Y%m%d")}',
                    'created_by': admin,
                }
            )

        self.stdout.write(f'Done! Created {count} invoices with items and payments.')
