"""
API views for Multi-Branch and Multi-Currency support.
Handles Currency management, Exchange Rate history, Currency conversion,
and Branch CRUD operations.
"""

from rest_framework import (
    generics, serializers, status, permissions, filters, views
)
from rest_framework.response import Response
from decimal import Decimal

from .multicurrency import (
    Branch, Currency, ExchangeRate,
    convert_currency, get_exchange_rate,
    update_exchange_rate, get_branch_accounts,
)
from users.permissions import IsAccountantOrAdmin, IsAdmin


# =============================================
# Currency Serializers
# =============================================

class CurrencyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing currencies."""

    class Meta:
        model = Currency
        fields = (
            'id', 'code', 'name', 'name_en', 'symbol',
            'is_default', 'exchange_rate', 'rate_date', 'is_active',
        )
        read_only_fields = ('id', 'rate_date')


class CurrencyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new currency."""

    class Meta:
        model = Currency
        fields = ('code', 'name', 'name_en', 'symbol', 'exchange_rate')

    def validate_code(self, value):
        if Currency.objects.filter(code=value).exists():
            raise serializers.ValidationError('رمز العملة موجود مسبقاً')
        return value


class CurrencyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating currency info."""

    class Meta:
        model = Currency
        fields = ('name', 'name_en', 'symbol', 'exchange_rate', 'is_active')


class CurrencyDetailSerializer(serializers.ModelSerializer):
    """Detailed currency serializer with recent exchange rates."""

    recent_rates = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        fields = (
            'id', 'code', 'name', 'name_en', 'symbol', 'is_default',
            'exchange_rate', 'rate_date', 'is_active', 'created_at', 'updated_at',
            'recent_rates',
        )
        read_only_fields = ('id', 'code', 'created_at', 'updated_at')

    def get_recent_rates(self, obj):
        """Get the most recent 20 exchange rate records."""
        rates = obj.exchange_rates.all()[:20]
        return ExchangeRateSerializer(rates, many=True).data


class ExchangeRateSerializer(serializers.ModelSerializer):
    """Serializer for exchange rate history records."""

    currency = serializers.CharField(source='currency.code', read_only=True)

    class Meta:
        model = ExchangeRate
        fields = ('id', 'currency', 'rate', 'date', 'source', 'notes', 'created_at')
        read_only_fields = ('id', 'created_at')


# =============================================
# Branch Serializers
# =============================================

class BranchListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing branches."""

    manager_name = serializers.CharField(
        source='manager.full_name', read_only=True, default=None,
    )
    default_currency_name = serializers.CharField(
        source='default_currency.name', read_only=True, default=None,
    )

    class Meta:
        model = Branch
        fields = (
            'id', 'code', 'name', 'name_en', 'city',
            'is_active', 'is_headquarters', 'manager_name',
            'default_currency_name',
        )
        read_only_fields = ('id',)


class BranchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new branch."""

    class Meta:
        model = Branch
        fields = (
            'code', 'name', 'name_en', 'address', 'city',
            'phone', 'is_headquarters', 'manager', 'default_currency',
        )

    def validate_code(self, value):
        if Branch.objects.filter(code=value).exists():
            raise serializers.ValidationError('رمز الفرع موجود مسبقاً')
        return value


class BranchUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating branch info."""

    class Meta:
        model = Branch
        fields = (
            'name', 'name_en', 'address', 'city',
            'phone', 'is_active', 'manager', 'default_currency',
        )


class BranchDetailSerializer(serializers.ModelSerializer):
    """Detailed branch serializer with associated accounts."""

    manager_name = serializers.CharField(
        source='manager.full_name', read_only=True, default=None,
    )
    default_currency_name = serializers.CharField(
        source='default_currency.name', read_only=True, default=None,
    )
    accounts = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = (
            'id', 'code', 'name', 'name_en', 'address', 'city', 'country',
            'phone', 'is_active', 'is_headquarters', 'manager', 'default_currency',
            'created_at', 'updated_at', 'manager_name', 'default_currency_name',
            'accounts',
        )
        read_only_fields = ('id', 'code', 'created_at', 'updated_at')

    def get_accounts(self, obj):
        """Get all accounts used by this branch."""
        accounts = get_branch_accounts(obj.id)
        from .serializers import AccountListSerializer
        return AccountListSerializer(accounts, many=True).data


# =============================================
# Currency Conversion Serializer
# =============================================

class CurrencyConversionSerializer(serializers.Serializer):
    """
    Serializer for currency conversion.
    Input fields: amount, from_currency, to_currency, date (optional).
    Output fields: original_amount, converted_amount, exchange_rate,
                   from_currency, to_currency.
    """

    # Input fields
    amount = serializers.DecimalField(
        max_digits=16, decimal_places=2,
        help_text='المبلغ المراد تحويله',
    )
    from_currency = serializers.CharField(
        max_length=3,
        help_text='رمز العملة المصدر (مثال: USD)',
    )
    to_currency = serializers.CharField(
        max_length=3,
        help_text='رمز العملة الهدف (مثال: SAR)',
    )
    date = serializers.DateField(
        required=False, allow_null=True,
        help_text='تاريخ سعر الصرف (افتراضي: اليوم)',
    )

    # Output fields (populated by the view)
    original_amount = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True,
    )
    converted_amount = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True,
    )
    exchange_rate = serializers.DecimalField(
        max_digits=12, decimal_places=6, read_only=True,
    )


# =============================================
# Currency Views
# =============================================

class CurrencyListView(generics.ListAPIView):
    """GET: List all currencies."""

    serializer_class = CurrencyListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'name_en']
    ordering_fields = ['code', 'name', 'exchange_rate', 'is_default', 'is_active']
    ordering = ['code']

    def get_queryset(self):
        queryset = Currency.objects.all()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class CurrencyCreateView(generics.CreateAPIView):
    """POST: Create a new currency (admin only)."""

    serializer_class = CurrencyCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        currency = serializer.save()
        return Response({
            'message': 'تم إنشاء العملة بنجاح',
            'currency': CurrencyDetailSerializer(currency).data,
        }, status=status.HTTP_201_CREATED)


class CurrencyDetailView(generics.RetrieveAPIView):
    """GET: Detailed view of a single currency with recent exchange rates."""

    serializer_class = CurrencyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Currency.objects.all()


class CurrencyUpdateView(generics.UpdateAPIView):
    """PATCH: Update currency info (admin only)."""

    serializer_class = CurrencyUpdateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return Currency.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        currency = serializer.save()
        return Response({
            'message': 'تم تحديث العملة بنجاح',
            'currency': CurrencyDetailSerializer(currency).data,
        })


class CurrencyRateUpdateView(views.APIView):
    """POST: Update exchange rate for a currency (accountant/admin only)."""

    permission_classes = [IsAccountantOrAdmin]

    def post(self, request, pk):
        try:
            currency = Currency.objects.get(pk=pk)
        except Currency.DoesNotExist:
            return Response(
                {'error': 'العملة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        rate = request.data.get('rate')
        source = request.data.get('source', 'manual')
        notes = request.data.get('notes', '')

        if rate is None:
            return Response(
                {'error': 'حقل سعر الصرف مطلوب'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            updated_currency, history = update_exchange_rate(
                currency.code, rate, source,
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update notes if provided
        if notes:
            history.notes = notes
            history.save(update_fields=['notes'])

        return Response({
            'message': 'تم تحديث سعر الصرف بنجاح',
            'currency': CurrencyDetailSerializer(updated_currency).data,
            'rate_history': ExchangeRateSerializer(history).data,
        })


class ExchangeRateListView(generics.ListAPIView):
    """GET: List exchange rate history for a currency."""

    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date', 'rate', 'created_at']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        currency_id = self.kwargs.get('pk')
        queryset = ExchangeRate.objects.filter(currency_id=currency_id)

        # Filter by optional date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset


class CurrencyConvertView(views.APIView):
    """POST: Convert amount between two currencies."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CurrencyConversionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        from_currency = serializer.validated_data['from_currency']
        to_currency = serializer.validated_data['to_currency']
        date = serializer.validated_data.get('date')

        try:
            converted_amount = convert_currency(
                amount, from_currency, to_currency, date,
            )
            from_rate = get_exchange_rate(from_currency, date)
            to_rate = get_exchange_rate(to_currency, date)
            effective_rate = from_rate / to_rate if to_rate != 0 else Decimal('1')
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result_data = {
            'original_amount': str(amount),
            'converted_amount': str(converted_amount),
            'exchange_rate': str(effective_rate.quantize(Decimal('0.000001'))),
            'from_currency': from_currency,
            'to_currency': to_currency,
        }

        return Response(result_data)


# =============================================
# Branch Views
# =============================================

class BranchListView(generics.ListAPIView):
    """GET: List all branches."""

    serializer_class = BranchListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'name_en', 'city']
    ordering_fields = ['code', 'name', 'city', 'is_active']
    ordering = ['code']

    def get_queryset(self):
        queryset = Branch.objects.select_related('manager', 'default_currency')
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class BranchCreateView(generics.CreateAPIView):
    """POST: Create a new branch (admin only)."""

    serializer_class = BranchCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        return Response({
            'message': 'تم إنشاء الفرع بنجاح',
            'branch': BranchDetailSerializer(branch).data,
        }, status=status.HTTP_201_CREATED)


class BranchDetailView(generics.RetrieveAPIView):
    """GET: Detailed view of a single branch with associated accounts."""

    serializer_class = BranchDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Branch.objects.select_related(
            'manager', 'default_currency',
        )


class BranchUpdateView(generics.UpdateAPIView):
    """PATCH: Update branch info (admin only)."""

    serializer_class = BranchUpdateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return Branch.objects.select_related('manager', 'default_currency')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        return Response({
            'message': 'تم تحديث الفرع بنجاح',
            'branch': BranchDetailSerializer(branch).data,
        })



