from rest_framework import serializers
from django.utils import timezone
from django.db.models import Sum
from django.db.models import DecimalField
from .models import (
    POSShift,
    POSSale,
    POSRefund,
    POSHoldOrder,
    CashDrawerTransaction,
    PriceList,
    DiscountRule,
    PromoCode,
    LoyaltyProgram,
    LoyaltyTransaction,
    RestaurantTable,
    InstallmentPlan,
    InstallmentPayment,
)


class POSShiftListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة الورديات"""
    cashier_name = serializers.SerializerMethodField()

    class Meta:
        model = POSShift
        fields = [
            'id', 'shift_number', 'cashier', 'cashier_name',
            'start_time', 'end_time', 'status',
            'opening_cash', 'closing_cash', 'expected_cash', 'difference',
            'total_sales', 'total_transactions', 'total_refunds',
            'created_at',
        ]
        read_only_fields = fields

    def get_cashier_name(self, obj):
        return obj.cashier.get_full_name() or obj.cashier.username


class POSShiftCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء وردية جديدة"""

    class Meta:
        model = POSShift
        fields = ['id', 'shift_number', 'cashier', 'opening_cash', 'notes']
        read_only_fields = ['id', 'shift_number']

    def validate_cashier(self, value):
        # Check if cashier already has an open shift
        existing_shift = POSShift.objects.filter(
            cashier=value, status='open'
        ).first()
        if existing_shift:
            raise serializers.ValidationError(
                f'الكاشير لديه وردية مفتوحة بالفعل: {existing_shift.shift_number}'
            )
        return value

    def create(self, validated_data):
        # Generate shift number: SH-YYYYMMDD-XXXX
        today = timezone.now().strftime('%Y%m%d')
        prefix = 'SH'
        last_shift = POSShift.objects.filter(
            shift_number__startswith=f'{prefix}-{today}'
        ).order_by('-shift_number').first()

        if last_shift:
            try:
                last_seq = int(last_shift.shift_number.split('-')[-1])
                new_seq = last_seq + 1
            except (IndexError, ValueError):
                new_seq = 1
        else:
            new_seq = 1

        validated_data['shift_number'] = f'{prefix}-{today}-{str(new_seq).zfill(4)}'
        validated_data['status'] = 'open'
        return super().create(validated_data)


class POSShiftCloseSerializer(serializers.Serializer):
    """مسلسل إغلاق الوردية"""
    closing_cash = serializers.DecimalField(
        max_digits=14, decimal_places=2
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default=''
    )


class POSShiftDetailSerializer(serializers.ModelSerializer):
    """مسلسل تفاصيل الوردية مع ملخص المبيعات"""
    cashier_name = serializers.SerializerMethodField()
    sales_summary = serializers.SerializerMethodField()
    refunds_summary = serializers.SerializerMethodField()
    drawer_transactions = serializers.SerializerMethodField()

    class Meta:
        model = POSShift
        fields = [
            'id', 'shift_number', 'cashier', 'cashier_name',
            'start_time', 'end_time', 'status',
            'opening_cash', 'closing_cash', 'expected_cash', 'difference',
            'total_sales', 'total_transactions', 'total_refunds',
            'notes', 'sales_summary', 'refunds_summary',
            'drawer_transactions', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_cashier_name(self, obj):
        return obj.cashier.get_full_name() or obj.cashier.username

    def get_sales_summary(self, obj):
        sales = obj.sales.filter(status='completed')
        cash_sales = sales.filter(payment_method='cash').aggregate(
            total=Sum('total_amount', output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total'] or 0
        card_sales = sales.filter(payment_method='card').aggregate(
            total=Sum('total_amount', output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total'] or 0
        online_sales = sales.filter(payment_method='online').aggregate(
            total=Sum('total_amount', output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total'] or 0
        mixed_sales = sales.filter(payment_method='mixed').aggregate(
            total=Sum('total_amount', output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total'] or 0

        return {
            'cash_sales': cash_sales,
            'card_sales': card_sales,
            'online_sales': online_sales,
            'mixed_sales': mixed_sales,
            'total_completed_sales': cash_sales + card_sales + online_sales + mixed_sales,
            'completed_count': sales.count(),
            'voided_count': obj.sales.filter(status='voided').count(),
            'refunded_count': obj.sales.filter(status='refunded').count(),
        }

    def get_refunds_summary(self, obj):
        refunds = obj.refunds.all()
        cash_refunds = refunds.filter(refund_method='cash').aggregate(
            total=Sum('refund_amount', output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total'] or 0
        card_refunds = refunds.filter(refund_method='card').aggregate(
            total=Sum('refund_amount', output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total'] or 0
        original_refunds = refunds.filter(refund_method='original').aggregate(
            total=Sum('refund_amount', output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total'] or 0

        return {
            'cash_refunds': cash_refunds,
            'card_refunds': card_refunds,
            'original_refunds': original_refunds,
            'total_refund_amount': cash_refunds + card_refunds + original_refunds,
            'refunds_count': refunds.count(),
        }

    def get_drawer_transactions(self, obj):
        transactions = obj.drawer_transactions.all()
        return CashDrawerTransactionSerializer(transactions, many=True).data


class POSSaleListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة عمليات البيع"""
    cashier_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = POSSale
        fields = [
            'id', 'receipt_number', 'shift', 'cashier_name',
            'customer', 'customer_name',
            'subtotal', 'discount_amount', 'vat_amount', 'total_amount',
            'payment_method', 'status',
            'items_count', 'created_at',
        ]
        read_only_fields = fields

    def get_cashier_name(self, obj):
        return obj.shift.cashier.get_full_name() or obj.shift.cashier.username

    def get_customer_name(self, obj):
        if obj.customer:
            return obj.customer.name if hasattr(obj.customer, 'name') else str(obj.customer)
        return None


# Add items_count to the serializer fields
POSSaleListSerializer._declared_fields = {
    **getattr(POSSaleListSerializer, '_declared_fields', {}),
    'items_count': serializers.SerializerMethodField(),
}


def get_items_count(self, obj):
    return len(obj.items) if obj.items else 0


POSSaleListSerializer.get_items_count = get_items_count


class POSSaleCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء عملية بيع"""
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
    )

    class Meta:
        model = POSSale
        fields = [
            'id', 'receipt_number', 'shift', 'customer',
            'items', 'subtotal', 'discount_amount', 'vat_amount',
            'total_amount', 'payment_method',
            'cash_received', 'change_amount', 'card_last_four',
            'notes',
        ]
        read_only_fields = ['id', 'receipt_number', 'vat_amount']

    def validate_shift(self, value):
        if value.status != 'open':
            raise serializers.ValidationError('الوردية غير مفتوحة')
        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('يجب إضافة عنصر واحد على الأقل')

        for item in value:
            required_fields = ['product_id', 'name', 'quantity', 'unit_price']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(
                        f'حقل {field} مطلوب في كل عنصر'
                    )
            if item['quantity'] <= 0:
                raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
            if item['unit_price'] < 0:
                raise serializers.ValidationError('السعر يجب أن يكون صفر أو أكبر')

        return value

    def validate_cash_received(self, value):
        # Will be validated further in view after total is computed
        return value

    def validate(self, attrs):
        items = attrs.get('items', [])
        subtotal = sum(
            item.get('quantity', 0) * item.get('unit_price', 0)
            for item in items
        )
        discount = attrs.get('discount_amount', 0)
        vat = round((subtotal - discount) * 0.15, 2)
        total = subtotal - discount + vat

        attrs['subtotal'] = subtotal
        attrs['vat_amount'] = vat
        attrs['total_amount'] = total

        # Validate cash received for cash payments
        payment_method = attrs.get('payment_method', 'cash')
        if payment_method == 'cash':
            cash_received = attrs.get('cash_received', 0)
            if cash_received < total:
                raise serializers.ValidationError(
                    'المبلغ المستلم أقل من الإجمالي'
                )
            attrs['change_amount'] = cash_received - total

        return attrs


class POSSaleVoidSerializer(serializers.Serializer):
    """مسلسل إلغاء عملية البيع"""
    void_reason = serializers.CharField(
        required=True,
        max_length=500
    )


class POSRefundSerializer(serializers.ModelSerializer):
    """مسلسل الإرجاع"""
    refund_method_display = serializers.CharField(
        source='get_refund_method_display', read_only=True
    )
    processed_by_name = serializers.SerializerMethodField()
    sale_receipt = serializers.CharField(
        source='sale.receipt_number', read_only=True
    )

    class Meta:
        model = POSRefund
        fields = [
            'id', 'refund_number', 'sale', 'sale_receipt',
            'shift', 'items', 'refund_amount',
            'refund_method', 'refund_method_display',
            'reason', 'processed_by', 'processed_by_name',
            'created_at',
        ]
        read_only_fields = ['id', 'refund_number', 'created_at']

    def get_processed_by_name(self, obj):
        if obj.processed_by:
            return obj.processed_by.get_full_name() or obj.processed_by.username
        return None


class POSRefundCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء إرجاع"""

    class Meta:
        model = POSRefund
        fields = [
            'id', 'refund_number', 'sale', 'shift',
            'items', 'refund_amount', 'refund_method',
            'reason', 'processed_by',
        ]
        read_only_fields = ['id', 'refund_number']

    def validate_sale(self, value):
        if value.status == 'voided':
            raise serializers.ValidationError('لا يمكن إرجاع عملية بيع ملغاة')
        if value.status == 'refunded':
            raise serializers.ValidationError('تم إرجاع عملية البيع بالفعل')
        return value

    def validate_shift(self, value):
        if value.status != 'open':
            raise serializers.ValidationError('الوردية غير مفتوحة')
        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('يجب تحديد عنصر واحد على الأقل للإرجاع')
        return value


class POSHoldOrderSerializer(serializers.ModelSerializer):
    """مسلسل الطلبات المعلقة"""
    shift_number = serializers.CharField(
        source='shift.shift_number', read_only=True
    )
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = POSHoldOrder
        fields = [
            'id', 'hold_number', 'shift', 'shift_number',
            'customer_name', 'items', 'items_count',
            'subtotal', 'discount_amount', 'vat_amount', 'total_amount',
            'notes', 'is_recovered', 'created_at',
        ]
        read_only_fields = ['id', 'hold_number', 'created_at']

    def get_items_count(self, obj):
        return len(obj.items) if obj.items else 0


class POSHoldOrderRecoverSerializer(serializers.Serializer):
    """مسلسل استرجاع طلب معلق"""
    hold_number = serializers.CharField()


class CashDrawerTransactionSerializer(serializers.ModelSerializer):
    """مسلسل حركات الصندوق"""
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', read_only=True
    )
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CashDrawerTransaction
        fields = [
            'id', 'shift', 'transaction_type', 'transaction_type_display',
            'amount', 'description', 'created_by', 'created_by_name',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class CashDrawerTransactionCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء حركة صندوق"""

    class Meta:
        model = CashDrawerTransaction
        fields = [
            'id', 'shift', 'transaction_type', 'amount',
            'description', 'created_by',
        ]
        read_only_fields = ['id']

    def validate_shift(self, value):
        if value.status != 'open':
            raise serializers.ValidationError('الوردية غير مفتوحة')
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ يجب أن يكون أكبر من صفر')
        return value


class POSStatsSerializer(serializers.Serializer):
    """مسلسل إحصائيات نقطة البيع"""
    today_sales_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    today_sales_count = serializers.IntegerField()
    today_refunds_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    today_net_sales = serializers.DecimalField(max_digits=14, decimal_places=2)
    current_shift = POSShiftDetailSerializer(required=False)
    payment_method_breakdown = serializers.DictField()
    top_products = serializers.ListField()
    hourly_sales = serializers.ListField()


# ============================================================
# قوائم الأسعار - Price Lists
# ============================================================


class PriceListListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة قوائم الأسعار"""

    class Meta:
        model = PriceList
        fields = [
            'id', 'name', 'description', 'is_default', 'is_active',
            'valid_from', 'valid_until', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class PriceListCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء قائمة أسعار"""

    class Meta:
        model = PriceList
        fields = [
            'id', 'name', 'description', 'is_default', 'is_active',
            'valid_from', 'valid_until',
        ]
        read_only_fields = ['id']

    def validate_is_default(self, value):
        if value:
            existing_default = PriceList.objects.filter(is_default=True).first()
            if existing_default:
                raise serializers.ValidationError(
                    'يوجد بالفعل قائمة أسعار افتراضية. يُرجى إلغاء القائمة الافتراضية الحالية أولاً.'
                )
        return value


class PriceListUpdateSerializer(serializers.ModelSerializer):
    """مسلسل تحديث قائمة أسعار"""

    class Meta:
        model = PriceList
        fields = [
            'id', 'name', 'description', 'is_default', 'is_active',
            'valid_from', 'valid_until',
        ]
        read_only_fields = ['id']

    def validate_is_default(self, value):
        if value:
            existing_default = PriceList.objects.filter(
                is_default=True
            ).exclude(pk=self.instance.pk if self.instance else None).first()
            if existing_default:
                raise serializers.ValidationError(
                    'يوجد بالفعل قائمة أسعار افتراضية. يُرجى إلغاء القائمة الافتراضية الحالية أولاً.'
                )
        return value


# ============================================================
# قواعد الخصم - Discount Rules
# ============================================================


class DiscountRuleListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة قواعد الخصم"""
    discount_type_display = serializers.CharField(
        source='get_discount_type_display', read_only=True
    )
    applies_to_display = serializers.CharField(
        source='get_applies_to_display', read_only=True
    )

    class Meta:
        model = DiscountRule
        fields = [
            'id', 'name', 'discount_type', 'discount_type_display',
            'discount_value', 'min_quantity', 'max_discount_amount',
            'applies_to', 'applies_to_display', 'product_category',
            'is_active', 'priority', 'valid_from', 'valid_until',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class DiscountRuleCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء قاعدة خصم"""

    class Meta:
        model = DiscountRule
        fields = [
            'id', 'name', 'discount_type', 'discount_value',
            'min_quantity', 'max_discount_amount', 'applies_to',
            'product_category', 'is_active', 'priority',
            'valid_from', 'valid_until',
        ]
        read_only_fields = ['id']

    def validate_discount_value(self, value):
        if value <= 0:
            raise serializers.ValidationError('قيمة الخصم يجب أن تكون أكبر من صفر')
        if self.initial_data.get('discount_type') == 'percentage' and value > 100:
            raise serializers.ValidationError('نسبة الخصم يجب ألا تتجاوز 100%')
        return value

    def validate(self, attrs):
        discount_type = attrs.get('discount_type')
        applies_to = attrs.get('applies_to')

        if applies_to in ['specific_category', 'specific_product'] and not attrs.get('product_category'):
            raise serializers.ValidationError({
                'product_category': 'يجب تحديد فئة المنتجات عند اختيار فئة محددة أو منتج محدد'
            })

        if discount_type == 'percentage':
            discount_value = attrs.get('discount_value')
            if discount_value and discount_value > 100:
                raise serializers.ValidationError({
                    'discount_value': 'نسبة الخصم يجب ألا تتجاوز 100%'
                })

        return attrs


class DiscountRuleUpdateSerializer(serializers.ModelSerializer):
    """مسلسل تحديث قاعدة خصم"""

    class Meta:
        model = DiscountRule
        fields = [
            'id', 'name', 'discount_type', 'discount_value',
            'min_quantity', 'max_discount_amount', 'applies_to',
            'product_category', 'is_active', 'priority',
            'valid_from', 'valid_until',
        ]
        read_only_fields = ['id']

    def validate_discount_value(self, value):
        if value <= 0:
            raise serializers.ValidationError('قيمة الخصم يجب أن تكون أكبر من صفر')
        if self.initial_data.get('discount_type') == 'percentage' and value > 100:
            raise serializers.ValidationError('نسبة الخصم يجب ألا تتجاوز 100%')
        return value

    def validate(self, attrs):
        discount_type = attrs.get('discount_type')
        applies_to = attrs.get('applies_to')

        if applies_to in ['specific_category', 'specific_product'] and not attrs.get('product_category'):
            raise serializers.ValidationError({
                'product_category': 'يجب تحديد فئة المنتجات عند اختيار فئة محددة أو منتج محدد'
            })

        if discount_type == 'percentage':
            discount_value = attrs.get('discount_value')
            if discount_value and discount_value > 100:
                raise serializers.ValidationError({
                    'discount_value': 'نسبة الخصم يجب ألا تتجاوز 100%'
                })

        return attrs


class DiscountRuleApplySerializer(serializers.Serializer):
    """مسلسل البحث عن قواعد الخصم المطبقة"""
    product_category = serializers.CharField(required=False, allow_blank=True, default='')
    quantity = serializers.IntegerField(required=False, default=1)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)


# ============================================================
# الأكواد الترويجية - Promo Codes
# ============================================================


class PromoCodeListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة الأكواد الترويجية"""
    discount_type_display = serializers.CharField(
        source='get_discount_type_display', read_only=True
    )

    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'description', 'discount_type',
            'discount_type_display', 'discount_value',
            'min_order_amount', 'max_uses', 'used_count',
            'max_uses_per_customer', 'is_active',
            'valid_from', 'valid_until',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class PromoCodeCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء كود ترويجي"""

    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'description', 'discount_type',
            'discount_value', 'min_order_amount', 'max_uses',
            'max_uses_per_customer', 'is_active',
            'valid_from', 'valid_until',
        ]
        read_only_fields = ['id']

    def validate_code(self, value):
        code_upper = value.upper().strip()
        if PromoCode.objects.filter(code=code_upper).exists():
            raise serializers.ValidationError('هذا الكود الترويجي مستخدم بالفعل')
        return code_upper

    def validate_discount_value(self, value):
        if value <= 0:
            raise serializers.ValidationError('قيمة الخصم يجب أن تكون أكبر من صفر')
        return value


class PromoCodeUpdateSerializer(serializers.ModelSerializer):
    """مسلسل تحديث كود ترويجي"""

    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'description', 'discount_type',
            'discount_value', 'min_order_amount', 'max_uses',
            'max_uses_per_customer', 'is_active',
            'valid_from', 'valid_until',
        ]
        read_only_fields = ['id']

    def validate_code(self, value):
        code_upper = value.upper().strip()
        existing = PromoCode.objects.filter(code=code_upper).exclude(
            pk=self.instance.pk if self.instance else None
        ).first()
        if existing:
            raise serializers.ValidationError('هذا الكود الترويجي مستخدم بالفعل')
        return code_upper

    def validate_discount_value(self, value):
        if value <= 0:
            raise serializers.ValidationError('قيمة الخصم يجب أن تكون أكبر من صفر')
        return value


class PromoCodeValidateSerializer(serializers.Serializer):
    """مسلسل التحقق من صلاحية الكود الترويجي"""
    code = serializers.CharField(max_length=50)
    order_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    customer_id = serializers.IntegerField(required=False, default=None)


# ============================================================
# برامج الولاء - Loyalty Programs
# ============================================================


class LoyaltyProgramListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة برامج الولاء"""
    enrolled_customers = serializers.SerializerMethodField()

    class Meta:
        model = LoyaltyProgram
        fields = [
            'id', 'name', 'description', 'points_per_currency',
            'min_redemption_points', 'points_value', 'is_active',
            'enrolled_customers', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_enrolled_customers(self, obj):
        return LoyaltyTransaction.objects.filter(
            loyalty_program=obj
        ).values('customer').distinct().count()


class LoyaltyProgramCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء برنامج ولاء"""

    class Meta:
        model = LoyaltyProgram
        fields = [
            'id', 'name', 'description', 'points_per_currency',
            'min_redemption_points', 'points_value', 'is_active',
        ]
        read_only_fields = ['id']

    def validate_points_per_currency(self, value):
        if value <= 0:
            raise serializers.ValidationError('عدد النقاط لكل وحدة نقدية يجب أن يكون أكبر من صفر')
        return value


class LoyaltyProgramUpdateSerializer(serializers.ModelSerializer):
    """مسلسل تحديث برنامج ولاء"""

    class Meta:
        model = LoyaltyProgram
        fields = [
            'id', 'name', 'description', 'points_per_currency',
            'min_redemption_points', 'points_value', 'is_active',
        ]
        read_only_fields = ['id']

    def validate_points_per_currency(self, value):
        if value <= 0:
            raise serializers.ValidationError('عدد النقاط لكل وحدة نقدية يجب أن يكون أكبر من صفر')
        return value


class LoyaltyTransactionListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة معاملات الولاء"""
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', read_only=True
    )
    program_name = serializers.CharField(
        source='loyalty_program.name', read_only=True
    )
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = LoyaltyTransaction
        fields = [
            'id', 'loyalty_program', 'program_name', 'customer',
            'customer_name', 'pos_sale', 'points', 'balance_after',
            'transaction_type', 'transaction_type_display',
            'description', 'created_at',
        ]
        read_only_fields = fields

    def get_customer_name(self, obj):
        if obj.customer:
            return obj.customer.name if hasattr(obj.customer, 'name') else str(obj.customer)
        return None


class LoyaltyBalanceSerializer(serializers.Serializer):
    """مسلسل رصيد الولاء"""
    customer_id = serializers.IntegerField()


class LoyaltyRedeemSerializer(serializers.Serializer):
    """مسلسل استبدال نقاط الولاء"""
    customer_id = serializers.IntegerField()
    program_id = serializers.IntegerField()
    points = serializers.IntegerField()
    sale_id = serializers.IntegerField(required=False, default=None)

    def validate_points(self, value):
        if value <= 0:
            raise serializers.ValidationError('عدد النقاط يجب أن يكون أكبر من صفر')
        return value


# ============================================================
# الطاولات - Restaurant Tables
# ============================================================


class RestaurantTableListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة الطاولات"""
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = RestaurantTable
        fields = [
            'id', 'table_number', 'capacity', 'area',
            'status', 'status_display', 'current_shift',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class RestaurantTableCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء طاولة"""

    class Meta:
        model = RestaurantTable
        fields = [
            'id', 'table_number', 'capacity', 'area', 'status',
        ]
        read_only_fields = ['id']

    def validate_table_number(self, value):
        if RestaurantTable.objects.filter(table_number=value).exists():
            raise serializers.ValidationError('رقم الطاولة مستخدم بالفعل')
        return value

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError('السعة يجب أن تكون أكبر من صفر')
        return value


class RestaurantTableUpdateSerializer(serializers.ModelSerializer):
    """مسلسل تحديث طاولة"""

    class Meta:
        model = RestaurantTable
        fields = [
            'id', 'table_number', 'capacity', 'area', 'status',
        ]
        read_only_fields = ['id']

    def validate_table_number(self, value):
        existing = RestaurantTable.objects.filter(table_number=value).exclude(
            pk=self.instance.pk if self.instance else None
        ).first()
        if existing:
            raise serializers.ValidationError('رقم الطاولة مستخدم بالفعل')
        return value

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError('السعة يجب أن تكون أكبر من صفر')
        return value


class RestaurantTableStatusSerializer(serializers.Serializer):
    """مسلسل تحديث حالة الطاولة"""
    status = serializers.ChoiceField(
        choices=RestaurantTable.TABLE_STATUS_CHOICES
    )


# ============================================================
# خطط الأقساط - Installment Plans
# ============================================================


class InstallmentPlanListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة خطط الأقساط"""
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    customer_name = serializers.SerializerMethodField()
    sale_receipt = serializers.CharField(
        source='pos_sale.receipt_number', read_only=True
    )
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = InstallmentPlan
        fields = [
            'id', 'pos_sale', 'sale_receipt', 'customer', 'customer_name',
            'total_amount', 'paid_amount', 'remaining_amount',
            'number_of_installments', 'installment_amount',
            'paid_installments', 'next_due_date', 'status',
            'status_display', 'progress_percentage',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_customer_name(self, obj):
        if obj.customer:
            return obj.customer.name if hasattr(obj.customer, 'name') else str(obj.customer)
        return None

    def get_progress_percentage(self, obj):
        if obj.total_amount and obj.total_amount > 0:
            return round((float(obj.paid_amount) / float(obj.total_amount)) * 100, 1)
        return 0


class InstallmentPlanCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء خطة أقساط"""

    class Meta:
        model = InstallmentPlan
        fields = [
            'id', 'pos_sale', 'customer', 'total_amount',
            'number_of_installments', 'installment_amount',
            'next_due_date', 'notes',
        ]
        read_only_fields = ['id', 'paid_amount', 'remaining_amount', 'paid_installments']

    def validate_number_of_installments(self, value):
        if value <= 0:
            raise serializers.ValidationError('عدد الأقساط يجب أن يكون أكبر من صفر')
        return value

    def validate_installment_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('مبلغ القسط يجب أن يكون أكبر من صفر')
        return value

    def validate(self, attrs):
        num = attrs.get('number_of_installments')
        amount = attrs.get('installment_amount')
        total = attrs.get('total_amount')

        if num and amount and total:
            expected_total = num * amount
            if abs(float(expected_total) - float(total)) > 0.01:
                raise serializers.ValidationError(
                    f'إجمالي الأقساط ({expected_total}) لا يتطابق مع المبلغ الإجمالي ({total})'
                )

        return attrs


class InstallmentPlanUpdateSerializer(serializers.ModelSerializer):
    """مسلسل تحديث خطة أقساط"""

    class Meta:
        model = InstallmentPlan
        fields = [
            'id', 'customer', 'status', 'notes',
        ]
        read_only_fields = ['id']


class InstallmentPaymentListSerializer(serializers.ModelSerializer):
    """مسلسل قائمة دفعات الأقساط"""
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = InstallmentPayment
        fields = [
            'id', 'installment_plan', 'installment_number',
            'amount', 'due_date', 'paid_date', 'payment_method',
            'payment_method_display', 'status', 'status_display',
            'paid_amount', 'notes', 'created_at',
        ]
        read_only_fields = fields


class InstallmentPaymentCreateSerializer(serializers.ModelSerializer):
    """مسلسل إنشاء دفعة قسط"""

    class Meta:
        model = InstallmentPayment
        fields = [
            'id', 'installment_plan', 'installment_number',
            'amount', 'due_date', 'payment_method', 'notes',
        ]
        read_only_fields = ['id']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ يجب أن يكون أكبر من صفر')
        return value


class InstallmentPaymentUpdateSerializer(serializers.ModelSerializer):
    """مسلسل تحديث دفعة قسط"""

    class Meta:
        model = InstallmentPayment
        fields = [
            'id', 'status', 'paid_date', 'payment_method',
            'paid_amount', 'notes',
        ]
        read_only_fields = ['id']
