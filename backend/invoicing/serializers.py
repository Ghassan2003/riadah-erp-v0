from decimal import Decimal

from rest_framework import serializers

from .models import Invoice, InvoiceItem, Payment, PaymentReminder


# ─── Invoice Item Serializers ────────────────────────────────────────────────

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = '__all__'
        read_only_fields = ('subtotal', 'vat_amount', 'total')


class InvoiceItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ('id', 'product', 'description', 'quantity', 'unit_price',
                  'unit', 'discount_type', 'discount_value', 'vat_rate')
        read_only_fields = ('id',)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value


# ─── Invoice Serializers ────────────────────────────────────────────────────

class InvoiceListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', default=None, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', default=None, read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = (
            'id', 'invoice_number', 'invoice_type', 'customer', 'customer_name',
            'supplier', 'supplier_name', 'issue_date', 'due_date', 'subtotal',
            'discount_amount', 'vat_amount', 'total_amount', 'currency',
            'payment_status', 'paid_amount', 'remaining_amount', 'status',
            'is_active', 'created_at'
        )

    def get_item_count(self, obj):
        return obj.items.count()


class InvoiceCreateSerializer(serializers.ModelSerializer):
    items = InvoiceItemCreateSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = (
            'id', 'invoice_number', 'invoice_type', 'sales_order', 'customer',
            'supplier', 'issue_date', 'due_date', 'discount_type', 'discount_value',
            'vat_rate', 'currency', 'notes', 'terms_conditions', 'tax_number',
            'company_tax_number', 'created_by', 'items'
        )
        read_only_fields = ('id', 'invoice_number', 'subtotal', 'discount_amount',
                            'vat_amount', 'total_after_discount', 'total_amount')

    def validate(self, attrs):
        # Sales invoices must have a customer
        if attrs.get('invoice_type') == 'sales' and not attrs.get('customer'):
            if not attrs.get('sales_order'):
                raise serializers.ValidationError({
                    'customer': 'فاتورة المبيعات يجب أن تحتوي على عميل'
                })

        # Purchase invoices must have a supplier
        if attrs.get('invoice_type') == 'purchase' and not attrs.get('supplier'):
            raise serializers.ValidationError({
                'supplier': 'فاتورة المشتريات يجب أن تحتوي على مورد'
            })

        # Due date must be after issue date
        issue_date = attrs.get('issue_date')
        due_date = attrs.get('due_date')
        if issue_date and due_date and due_date < issue_date:
            raise serializers.ValidationError({
                'due_date': 'تاريخ الاستحقاق يجب أن يكون بعد تاريخ الإصدار'
            })

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])

        # If sales_order is provided, auto-populate from sales order
        sales_order = validated_data.get('sales_order')
        if sales_order:
            validated_data['customer'] = validated_data.get('customer') or sales_order.customer
            if not items_data:
                # Copy items from sales order
                for so_item in sales_order.items.all():
                    items_data.append({
                        'product': so_item.product,
                        'description': so_item.description or (so_item.product.name if so_item.product else ''),
                        'quantity': so_item.quantity,
                        'unit_price': so_item.unit_price,
                        'unit': so_item.unit or 'piece',
                        'discount_type': 'percentage',
                        'discount_value': Decimal('0'),
                        'vat_rate': Decimal('15.00'),
                    })

        invoice = Invoice.objects.create(**validated_data)

        # Create invoice items
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        # Recalculate totals from items
        invoice.recalculate_totals()

        return invoice


class InvoiceUpdateSerializer(serializers.ModelSerializer):
    items = InvoiceItemCreateSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = (
            'id', 'invoice_type', 'sales_order', 'customer', 'supplier',
            'issue_date', 'due_date', 'discount_type', 'discount_value',
            'vat_rate', 'currency', 'notes', 'terms_conditions', 'tax_number',
            'company_tax_number', 'status', 'items'
        )
        read_only_fields = ('id', 'invoice_number', 'subtotal', 'discount_amount',
                            'vat_amount', 'total_after_discount', 'total_amount')

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()
            # Create new items
            for item_data in items_data:
                InvoiceItem.objects.create(invoice=instance, **item_data)

            # Recalculate totals
            instance.recalculate_totals()

        return instance


class InvoiceDetailSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', default=None, read_only=True)
    customer_email = serializers.CharField(source='customer.email', default=None, read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', default=None, read_only=True)
    customer_address = serializers.CharField(source='customer.address', default=None, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', default=None, read_only=True)
    supplier_phone = serializers.CharField(source='supplier.phone', default=None, read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    created_by_name = serializers.CharField(source='created_by.full_name', default=None, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'


class InvoiceChangeStatusSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['send', 'accept', 'cancel'],
        write_only=True
    )

    def validate_action(self, value):
        return value


# ─── Payment Serializers ─────────────────────────────────────────────────────

class PaymentListSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'payment_number', 'invoice', 'invoice_number', 'amount',
            'payment_method', 'payment_date', 'reference_number', 'bank_name',
            'notes', 'created_at'
        )


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            'id', 'payment_number', 'invoice', 'amount', 'payment_method',
            'payment_date', 'reference_number', 'bank_name', 'notes', 'created_by'
        )
        read_only_fields = ('id', 'payment_number')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ يجب أن يكون أكبر من صفر')
        return value

    def validate(self, attrs):
        invoice = attrs.get('invoice')
        amount = attrs.get('amount')

        if invoice and amount:
            remaining = invoice.remaining_amount
            if amount > remaining:
                raise serializers.ValidationError({
                    'amount': f'المبلغ ({amount}) يتجاوز المبلغ المتبقي ({remaining})'
                })

        return attrs


# ─── Reminder Serializers ────────────────────────────────────────────────────

class PaymentReminderListSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)

    class Meta:
        model = PaymentReminder
        fields = (
            'id', 'invoice', 'invoice_number', 'reminder_type', 'message',
            'sent_date', 'sent_via', 'status', 'created_at'
        )


class PaymentReminderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReminder
        fields = ('id', 'invoice', 'reminder_type', 'message', 'sent_via', 'status')
        read_only_fields = ('id',)

    def validate_message(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('رسالة التذكير مطلوبة')
        return value


# ─── Stats Serializer ────────────────────────────────────────────────────────

class InvoiceStatsSerializer(serializers.Serializer):
    total_invoices = serializers.IntegerField(read_only=True)
    total_sales = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_purchases = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_paid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_unpaid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_overdue = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    paid_count = serializers.IntegerField(read_only=True)
    unpaid_count = serializers.IntegerField(read_only=True)
    partially_paid_count = serializers.IntegerField(read_only=True)
    overdue_count = serializers.IntegerField(read_only=True)
