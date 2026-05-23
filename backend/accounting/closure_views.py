"""
واجهات API لنظام الإغلاق المحاسبي الدوري.
يتضمن إدارة السنوات المالية والفترات المحاسبية وإجراءات الإقفال وإعادة الفتح.
"""

from rest_framework import serializers, status, permissions, views
from rest_framework.response import Response

from .closure import (
    FiscalYear,
    FiscalPeriod,
    ClosureEntry,
    FiscalYearStatus,
    PeriodStatus,
    open_fiscal_year,
    validate_period_closable,
    get_period_balances,
    close_period,
    reopen_period,
    close_fiscal_year,
)
from users.permissions import IsAccountantOrAdmin, IsAdmin


# =============================================
# Serializers
# =============================================

class FiscalYearListSerializer(serializers.ModelSerializer):
    """مُسلسِّل قائمة السنوات المالية."""

    periods_count = serializers.IntegerField(
        source='periods.count',
        read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
    )

    class Meta:
        model = FiscalYear
        fields = [
            'id', 'year', 'company_name', 'status', 'status_display',
            'start_date', 'end_date', 'periods_count', 'created_at',
        ]


class FiscalPeriodSerializer(serializers.ModelSerializer):
    """مُسلسِّل الفترة المحاسبية."""

    fiscal_year_year = serializers.IntegerField(
        source='fiscal_year.year',
        read_only=True,
    )
    period_type_display = serializers.CharField(
        source='get_period_type_display',
        read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
    )
    period_label = serializers.CharField(
        source='get_period_label',
        read_only=True,
    )
    closed_by_name = serializers.CharField(
        source='closed_by.get_full_name',
        read_only=True,
        default=None,
    )

    class Meta:
        model = FiscalPeriod
        fields = [
            'id', 'fiscal_year', 'fiscal_year_year',
            'period_number', 'period_type', 'period_type_display',
            'period_start', 'period_end',
            'status', 'status_display', 'period_label',
            'opening_balances', 'closing_balances',
            'closed_by', 'closed_by_name', 'closed_at',
            'notes', 'created_at', 'updated_at',
        ]


class FiscalYearDetailSerializer(serializers.ModelSerializer):
    """مُسلسِّل تفاصيل السنة المالية مع الفترات المرتبطة."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
    )
    periods = FiscalPeriodSerializer(
        many=True,
        read_only=True,
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        default=None,
    )

    class Meta:
        model = FiscalYear
        fields = [
            'id', 'year', 'company_name', 'status', 'status_display',
            'start_date', 'end_date', 'periods',
            'created_by', 'created_by_name',
            'notes', 'created_at', 'updated_at',
        ]


class FiscalYearCreateSerializer(serializers.Serializer):
    """مُسلسِّل إنشاء سنة مالية جديدة."""

    year = serializers.IntegerField(
        required=True,
        min_value=2000,
        max_value=2100,
    )
    company_name = serializers.CharField(
        required=True,
        max_length=255,
    )
    start_date = serializers.DateField(
        required=False,
        allow_null=True,
    )
    end_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    def validate_year(self, value):
        if FiscalYear.objects.filter(year=value).exists():
            raise serializers.ValidationError(f'السنة المالية {value} موجودة مسبقاً')
        return value


class ClosureEntrySerializer(serializers.ModelSerializer):
    """مُسلسِّل قيد الإقفال."""

    entry_type_display = serializers.CharField(
        source='get_entry_type_display',
        read_only=True,
    )
    fiscal_period_label = serializers.CharField(
        source='fiscal_period.get_period_label',
        read_only=True,
    )

    class Meta:
        model = ClosureEntry
        fields = [
            'id', 'fiscal_period', 'fiscal_period_label',
            'journal_entry', 'entry_type', 'entry_type_display',
            'description', 'total_amount', 'created_at',
        ]


class PeriodBalanceSerializer(serializers.Serializer):
    """مُسلسِّل رصيد حساب في فترة محاسبية."""

    account_code = serializers.CharField()
    account_name = serializers.CharField()
    account_type = serializers.CharField()
    balance = serializers.CharField()


# =============================================
# Fiscal Year Views
# =============================================

class FiscalYearListView(views.APIView):
    """GET: قائمة جميع السنوات المالية."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            fiscal_years = FiscalYear.objects.all().order_by('-year')
            serializer = FiscalYearListSerializer(fiscal_years, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'حدث خطأ أثناء جلب السنوات المالية: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FiscalYearCreateView(views.APIView):
    """POST: إنشاء سنة مالية جديدة مع 12 فترة شهرية تلقائياً."""

    permission_classes = [IsAccountantOrAdmin]

    def post(self, request):
        serializer = FiscalYearCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            year = serializer.validated_data['year']
            company_name = serializer.validated_data['company_name']

            fiscal_year = open_fiscal_year(year, company_name, request.user)

            return Response({
                'message': f'تم إنشاء السنة المالية {year} و12 فترة شهرية بنجاح',
                'fiscal_year': FiscalYearDetailSerializer(fiscal_year).data,
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {'error': f'حدث خطأ أثناء إنشاء السنة المالية: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FiscalYearDetailView(views.APIView):
    """GET: تفاصيل سنة مالية مع جميع فتراتها."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            fiscal_year = FiscalYear.objects.select_related('created_by').get(pk=pk)
            serializer = FiscalYearDetailSerializer(fiscal_year)
            return Response(serializer.data)
        except FiscalYear.DoesNotExist:
            return Response(
                {'error': 'السنة المالية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {'error': f'حدث خطأ أثناء جلب تفاصيل السنة المالية: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FiscalYearCloseView(views.APIView):
    """POST: إقفال السنة المالية بالكامل (مدير فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            fiscal_year = FiscalYear.objects.get(pk=pk)
        except FiscalYear.DoesNotExist:
            return Response(
                {'error': 'السنة المالية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            closed_year = close_fiscal_year(pk, request.user)
            return Response({
                'message': f'تم إقفال السنة المالية {closed_year.year} بنجاح',
                'fiscal_year': FiscalYearDetailSerializer(closed_year).data,
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {'error': f'حدث خطأ أثناء إقفال السنة المالية: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# =============================================
# Fiscal Period Views
# =============================================

class FiscalPeriodDetailView(views.APIView):
    """GET: تفاصيل فترة محاسبية واحدة مع أرصدتها وقيود الإقفال."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            period = FiscalPeriod.objects.select_related(
                'fiscal_year', 'closed_by'
            ).prefetch_related('closure_entries__journal_entry').get(pk=pk)

            period_data = FiscalPeriodSerializer(period).data

            # إضافة قيود الإقفال المرتبطة
            closure_entries = period.closure_entries.all()
            period_data['closure_entries'] = ClosureEntrySerializer(
                closure_entries, many=True
            ).data

            return Response(period_data)

        except FiscalPeriod.DoesNotExist:
            return Response(
                {'error': 'الفترة المحاسبية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {'error': f'حدث خطأ أثناء جلب تفاصيل الفترة: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FiscalPeriodCloseView(views.APIView):
    """POST: إقفال فترة محاسبية (محاسب أو مدير)."""

    permission_classes = [IsAccountantOrAdmin]

    def post(self, request, pk):
        try:
            period = FiscalPeriod.objects.select_related('fiscal_year').get(pk=pk)
        except FiscalPeriod.DoesNotExist:
            return Response(
                {'error': 'الفترة المحاسبية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            closed_period, closure_entries = close_period(pk, request.user)

            return Response({
                'message': (
                    f'تم إقفال الفترة {closed_period.get_period_label()} '
                    f'للسنة {closed_period.year} بنجاح '
                    f'({len(closure_entries)} قيد إقفال)'
                ),
                'period': FiscalPeriodSerializer(closed_period).data,
                'closure_entries': ClosureEntrySerializer(closure_entries, many=True).data,
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {'error': f'حدث خطأ أثناء إقفال الفترة: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FiscalPeriodReopenView(views.APIView):
    """POST: إعادة فتح فترة محاسبية مقفلة (مدير فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            period = FiscalPeriod.objects.select_related('fiscal_year').get(pk=pk)
        except FiscalPeriod.DoesNotExist:
            return Response(
                {'error': 'الفترة المحاسبية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            reopened_period = reopen_period(pk, request.user)

            return Response({
                'message': (
                    f'تم إعادة فتح الفترة {reopened_period.get_period_label()} '
                    f'للسنة {reopened_period.year} بنجاح'
                ),
                'period': FiscalPeriodSerializer(reopened_period).data,
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {'error': f'حدث خطأ أثناء إعادة فتح الفترة: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FiscalPeriodBalancesView(views.APIView):
    """GET: أرصدة الحسابات في فترة محاسبية."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            period = FiscalPeriod.objects.select_related('fiscal_year').get(pk=pk)
        except FiscalPeriod.DoesNotExist:
            return Response(
                {'error': 'الفترة المحاسبية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            balances = get_period_balances(period)

            # تحويل الأرصدة باستخدام المُسلسِّل
            result = {}
            for category, accounts in balances.items():
                result[category] = PeriodBalanceSerializer(accounts, many=True).data

            return Response({
                'period': FiscalPeriodSerializer(period).data,
                'balances': result,
            })

        except Exception as e:
            return Response(
                {'error': f'حدث خطأ أثناء جلب أرصدة الفترة: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
