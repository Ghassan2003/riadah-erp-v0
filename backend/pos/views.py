from django.utils import timezone
from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import TruncHour
from django.http import HttpResponse
from rest_framework import status, generics, pagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from collections import Counter

from .models import (
    POSShift,
    POSSale,
    POSRefund,
    POSHoldOrder,
    CashDrawerTransaction,
)
from .serializers import (
    POSShiftListSerializer,
    POSShiftCreateSerializer,
    POSShiftCloseSerializer,
    POSShiftDetailSerializer,
    POSSaleListSerializer,
    POSSaleCreateSerializer,
    POSSaleVoidSerializer,
    POSRefundSerializer,
    POSRefundCreateSerializer,
    POSHoldOrderSerializer,
    POSHoldOrderRecoverSerializer,
    CashDrawerTransactionSerializer,
    CashDrawerTransactionCreateSerializer,
)


# ─────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────
class StandardPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─────────────────────────────────────────────
# Shift Views
# ─────────────────────────────────────────────
class POSShiftListView(generics.ListAPIView):
    """قائمة الورديات"""
    queryset = POSShift.objects.all()
    serializer_class = POSShiftListSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'cashier']
    search_fields = ['shift_number']
    ordering_fields = ['created_at', 'start_time', 'total_sales']
    ordering = ['-created_at']


class POSShiftOpenView(APIView):
    """فتح وردية جديدة"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = POSShiftCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        shift = serializer.save()

        # Create opening drawer transaction
        CashDrawerTransaction.objects.create(
            shift=shift,
            transaction_type='opening',
            amount=shift.opening_cash,
            description=f'فتح الوردية {shift.shift_number}',
            created_by=request.user,
        )

        detail_serializer = POSShiftDetailSerializer(shift)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class POSShiftCloseView(APIView):
    """إغلاق الوردية"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            shift = POSShift.objects.get(pk=pk)
        except POSShift.DoesNotExist:
            return Response(
                {'error': 'الوردية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND
            )

        if shift.status == 'closed':
            return Response(
                {'error': 'الوردية مغلقة بالفعل'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = POSShiftCloseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        closing_cash = serializer.validated_data['closing_cash']
        notes = serializer.validated_data['notes']

        shift.close_shift(closing_cash, notes)

        # Create closing drawer transaction
        CashDrawerTransaction.objects.create(
            shift=shift,
            transaction_type='closing',
            amount=shift.closing_cash,
            description=f'إغلاق الوردية {shift.shift_number}',
            created_by=request.user,
        )

        detail_serializer = POSShiftDetailSerializer(shift)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)


class POSShiftDetailView(generics.RetrieveAPIView):
    """تفاصيل الوردية"""
    queryset = POSShift.objects.all()
    serializer_class = POSShiftDetailSerializer
    permission_classes = [IsAuthenticated]


# ─────────────────────────────────────────────
# Sale Views
# ─────────────────────────────────────────────
class POSSaleListView(generics.ListAPIView):
    """قائمة عمليات البيع"""
    queryset = POSSale.objects.all()
    serializer_class = POSSaleListSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ['shift', 'status', 'payment_method', 'customer']
    search_fields = ['receipt_number', 'notes']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by date
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset


class POSSaleCreateView(APIView):
    """إنشاء عملية بيع جديدة"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from inventory.models import Product

        serializer = POSSaleCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        shift = validated_data['shift']
        items = validated_data['items']

        # Validate products exist and have enough quantity
        item_details = []
        for item in items:
            try:
                product = Product.objects.get(pk=item['product_id'])
            except Product.DoesNotExist:
                return Response(
                    {'error': f'المنتج غير موجود: {item["name"]} (ID: {item["product_id"]})'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check quantity
            current_qty = getattr(product, 'quantity', None)
            if current_qty is not None and current_qty < item['quantity']:
                return Response(
                    {'error': f'الكمية غير كافية للمنتج: {item["name"]}. '
                              f'المتاح: {current_qty}, المطلوب: {item["quantity"]}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Compute item totals
            line_total = item['quantity'] * item['unit_price']
            item_discount = item.get('discount', 0)
            item_vat = round((line_total - item_discount) * 0.15, 2)
            item_total = line_total - item_discount + item_vat

            item_details.append({
                'product_id': str(product.pk),
                'name': item['name'],
                'quantity': item['quantity'],
                'unit_price': item['unit_price'],
                'discount': item_discount,
                'vat': item_vat,
                'total': item_total,
                'product_instance': product,
            })

        # Create the sale
        sale = POSSale.objects.create(
            shift=shift,
            customer=validated_data.get('customer'),
            items=[
                {
                    'product_id': d['product_id'],
                    'name': d['name'],
                    'quantity': d['quantity'],
                    'unit_price': d['unit_price'],
                    'discount': d['discount'],
                    'vat': d['vat'],
                    'total': d['total'],
                }
                for d in item_details
            ],
            subtotal=validated_data['subtotal'],
            discount_amount=validated_data['discount_amount'],
            vat_amount=validated_data['vat_amount'],
            total_amount=validated_data['total_amount'],
            payment_method=validated_data.get('payment_method', 'cash'),
            cash_received=validated_data.get('cash_received', 0),
            change_amount=validated_data.get('change_amount', 0),
            card_last_four=validated_data.get('card_last_four', ''),
            notes=validated_data.get('notes', ''),
        )

        # Reduce product quantities in inventory
        for detail in item_details:
            product = detail['product_instance']
            current_qty = getattr(product, 'quantity', None)
            if current_qty is not None:
                product.quantity = current_qty - detail['quantity']
                product.save(update_fields=['quantity'])

        # Update shift totals
        shift.total_sales = (shift.total_sales or 0) + sale.total_amount
        shift.total_transactions = (shift.total_transactions or 0) + 1
        shift.save(update_fields=['total_sales', 'total_transactions'])

        return Response({
            'id': sale.id,
            'receipt_number': sale.receipt_number,
            'total_amount': str(sale.total_amount),
            'change_amount': str(sale.change_amount),
            'payment_method': sale.payment_method,
            'status': sale.status,
            'created_at': sale.created_at,
        }, status=status.HTTP_201_CREATED)


class POSSaleDetailView(generics.RetrieveAPIView):
    """تفاصيل عملية البيع"""
    queryset = POSSale.objects.all()
    serializer_class = POSSaleListSerializer
    permission_classes = [IsAuthenticated]


class POSSaleVoidView(APIView):
    """إلغاء عملية البيع"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            sale = POSSale.objects.get(pk=pk)
        except POSSale.DoesNotExist:
            return Response(
                {'error': 'عملية البيع غير موجودة'},
                status=status.HTTP_404_NOT_FOUND
            )

        if sale.status == 'voided':
            return Response(
                {'error': 'عملية البيع ملغاة بالفعل'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if sale.status == 'refunded':
            return Response(
                {'error': 'تم إرجاع عملية البيع بالفعل، لا يمكن إلغاؤها'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = POSSaleVoidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        void_reason = serializer.validated_data['void_reason']

        # Restore product quantities
        from inventory.models import Product
        for item in sale.items:
            try:
                product = Product.objects.get(pk=item['product_id'])
                current_qty = getattr(product, 'quantity', None)
                if current_qty is not None:
                    product.quantity = current_qty + item['quantity']
                    product.save(update_fields=['quantity'])
            except Product.DoesNotExist:
                pass  # Log warning in production

        # Void the sale
        sale.void_sale(request.user, void_reason)

        # Update shift totals
        shift = sale.shift
        shift.total_sales = max((shift.total_sales or 0) - sale.total_amount, 0)
        shift.total_transactions = max((shift.total_transactions or 0) - 1, 0)
        shift.save(update_fields=['total_sales', 'total_transactions'])

        return Response({
            'id': sale.id,
            'receipt_number': sale.receipt_number,
            'status': sale.status,
            'void_reason': sale.void_reason,
            'voided_by': request.user.get_full_name() or request.user.username,
            'voided_at': sale.voided_at,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Refund Views
# ─────────────────────────────────────────────
class POSRefundListView(generics.ListAPIView):
    """قائمة الإرجاعات"""
    queryset = POSRefund.objects.all()
    serializer_class = POSRefundSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ['sale', 'shift', 'refund_method', 'processed_by']
    search_fields = ['refund_number', 'reason']
    ordering_fields = ['created_at', 'refund_amount']
    ordering = ['-created_at']


class POSRefundCreateView(APIView):
    """إنشاء إرجاع جديد"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from inventory.models import Product

        serializer = POSRefundCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        sale = validated_data['sale']
        shift = validated_data['shift']
        items = validated_data['items']
        refund_method = validated_data.get('refund_method', 'original')

        # If original, use the sale's payment method
        if refund_method == 'original':
            refund_method = sale.payment_method

        # Restore product quantities
        for item in items:
            try:
                product = Product.objects.get(pk=item.get('product_id'))
                current_qty = getattr(product, 'quantity', None)
                if current_qty is not None:
                    product.quantity = current_qty + item.get('quantity', 0)
                    product.save(update_fields=['quantity'])
            except Product.DoesNotExist:
                pass

        # Create refund
        refund = POSRefund.objects.create(
            sale=sale,
            shift=shift,
            items=items,
            refund_amount=validated_data['refund_amount'],
            refund_method=refund_method,
            reason=validated_data['reason'],
            processed_by=validated_data.get('processed_by') or request.user,
        )

        # Mark sale as refunded
        sale.status = 'refunded'
        sale.save(update_fields=['status'])

        # Update shift totals
        shift.total_refunds = (shift.total_refunds or 0) + refund.refund_amount
        shift.save(update_fields=['total_refunds'])

        refund_serializer = POSRefundSerializer(refund)
        return Response(refund_serializer.data, status=status.HTTP_201_CREATED)


class POSRefundDetailView(generics.RetrieveAPIView):
    """تفاصيل الإرجاع"""
    queryset = POSRefund.objects.all()
    serializer_class = POSRefundSerializer
    permission_classes = [IsAuthenticated]


# ─────────────────────────────────────────────
# Hold Order Views
# ─────────────────────────────────────────────
class POSHoldListView(generics.ListAPIView):
    """قائمة الطلبات المعلقة"""
    queryset = POSHoldOrder.objects.filter(is_recovered=False)
    serializer_class = POSHoldOrderSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ['shift']
    ordering = ['-created_at']


class POSHoldCreateView(generics.CreateAPIView):
    """إنشاء طلب معلق"""
    queryset = POSHoldOrder.objects.all()
    serializer_class = POSHoldOrderSerializer
    permission_classes = [IsAuthenticated]


class POSHoldDeleteView(generics.DestroyAPIView):
    """حذف طلب معلق"""
    queryset = POSHoldOrder.objects.all()
    permission_classes = [IsAuthenticated]


class POSHoldDetailView(generics.RetrieveAPIView):
    """تفاصيل الطلب المعلق"""
    queryset = POSHoldOrder.objects.all()
    serializer_class = POSHoldOrderSerializer
    permission_classes = [IsAuthenticated]


# ─────────────────────────────────────────────
# Cash Drawer Views
# ─────────────────────────────────────────────
class CashDrawerTransactionListView(generics.ListAPIView):
    """قائمة حركات الصندوق"""
    queryset = CashDrawerTransaction.objects.all()
    serializer_class = CashDrawerTransactionSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filterset_fields = ['shift', 'transaction_type', 'created_by']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class CashDrawerTransactionCreateView(generics.CreateAPIView):
    """إنشاء حركة صندوق (إيداع/سحب)"""
    queryset = CashDrawerTransaction.objects.all()
    serializer_class = CashDrawerTransactionCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CashDrawerTransactionDetailView(generics.RetrieveAPIView):
    """تفاصيل حركة الصندوق"""
    queryset = CashDrawerTransaction.objects.all()
    serializer_class = CashDrawerTransactionSerializer
    permission_classes = [IsAuthenticated]


# ─────────────────────────────────────────────
# Stats & Export Views
# ─────────────────────────────────────────────
class POSStatsView(APIView):
    """إحصائيات نقطة البيع"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Today's sales
        today_sales = POSSale.objects.filter(
            created_at__date=today,
            status='completed',
        )
        today_sales_total = today_sales.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        today_sales_count = today_sales.count()

        # Today's refunds
        today_refunds = POSRefund.objects.filter(created_at__date=today)
        today_refunds_total = today_refunds.aggregate(
            total=Sum('refund_amount')
        )['total'] or 0

        today_net_sales = today_sales_total - today_refunds_total

        # Payment method breakdown
        payment_breakdown = today_sales.values('payment_method').annotate(
            total=Sum('total_amount'),
            count=Count('id'),
        ).order_by('-total')

        payment_method_breakdown = {}
        for item in payment_breakdown:
            payment_method_breakdown[item['payment_method']] = {
                'total': str(item['total']),
                'count': item['count'],
            }

        # Top products today
        all_items = []
        for sale in today_sales:
            if sale.items:
                for item in sale.items:
                    all_items.append({
                        'product_id': item.get('product_id'),
                        'name': item.get('name', ''),
                        'quantity': item.get('quantity', 0),
                        'total': item.get('total', 0),
                    })

        # Aggregate by product
        product_totals = {}
        for item in all_items:
            pid = item['product_id']
            if pid not in product_totals:
                product_totals[pid] = {
                    'product_id': pid,
                    'name': item['name'],
                    'quantity': 0,
                    'total': 0,
                }
            product_totals[pid]['quantity'] += item['quantity']
            product_totals[pid]['total'] += item['total']

        top_products = sorted(
            product_totals.values(),
            key=lambda x: x['total'],
            reverse=True,
        )[:10]

        # Hourly sales
        hourly_data = today_sales.annotate(
            hour=TruncHour('created_at')
        ).values('hour').annotate(
            total=Sum('total_amount'),
            count=Count('id'),
        ).order_by('hour')

        hourly_sales = []
        for h in hourly_data:
            hourly_sales.append({
                'hour': h['hour'].strftime('%H:00') if h['hour'] else '',
                'total': str(h['total']),
                'count': h['count'],
            })

        # Current open shift for current user
        current_shift = POSShift.objects.filter(
            cashier=request.user,
            status='open',
        ).first()

        current_shift_data = None
        if current_shift:
            current_shift_data = POSShiftDetailSerializer(current_shift).data

        return Response({
            'date': today.isoformat(),
            'today_sales_total': str(today_sales_total),
            'today_sales_count': today_sales_count,
            'today_refunds_total': str(today_refunds_total),
            'today_net_sales': str(today_net_sales),
            'current_shift': current_shift_data,
            'payment_method_breakdown': payment_method_breakdown,
            'top_products': top_products,
            'hourly_sales': hourly_sales,
        })


class POSExportView(APIView):
    """تصدير بيانات نقطة البيع"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
        except ImportError:
            return Response(
                {'error': 'يجب تثبيت مكتبة openpyxl: pip install openpyxl'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Get filter parameters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        export_type = request.query_params.get('type', 'sales')

        wb = openpyxl.Workbook()

        # Styles
        header_font = Font(bold=True, size=12, color='FFFFFF')
        header_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center')
        cell_alignment = Alignment(horizontal='center', vertical='center')
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin'),
        )

        if export_type == 'sales' or export_type == 'all':
            # Sales sheet
            ws = wb.active
            ws.title = 'عمليات البيع'
            ws.sheet_view.rightToLeft = True

            headers = [
                'رقم الإيصال', 'الكاشير', 'العميل', 'المجموع الفرعي',
                'الخصم', 'ضريبة القيمة المضافة', 'الإجمالي',
                'طريقة الدفع', 'الحالة', 'التاريخ',
            ]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = thin_border

            sales = POSSale.objects.all()
            if date_from:
                sales = sales.filter(created_at__date__gte=date_from)
            if date_to:
                sales = sales.filter(created_at__date__lte=date_to)

            for row, sale in enumerate(sales, 2):
                cashier_name = (
                    sale.shift.cashier.get_full_name() or sale.shift.cashier.username
                )
                customer_name = ''
                if sale.customer:
                    customer_name = getattr(sale.customer, 'name', str(sale.customer))

                data = [
                    sale.receipt_number,
                    cashier_name,
                    customer_name,
                    str(sale.subtotal),
                    str(sale.discount_amount),
                    str(sale.vat_amount),
                    str(sale.total_amount),
                    sale.get_payment_method_display(),
                    sale.get_status_display(),
                    sale.created_at.strftime('%Y-%m-%d %H:%M'),
                ]
                for col, value in enumerate(data, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    cell.alignment = cell_alignment
                    cell.border = thin_border

            # Auto-width
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                ws.column_dimensions[column].width = max(max_length + 4, 15)

        if export_type == 'shifts' or export_type == 'all':
            # Shifts sheet
            if export_type != 'all':
                ws = wb.active
            else:
                ws = wb.create_sheet('الورديات')

            ws.title = 'الورديات'
            ws.sheet_view.rightToLeft = True

            headers = [
                'رقم الوردية', 'الكاشير', 'وقت البدء', 'وقت الانتهاء',
                'الحالة', 'المبلغ الافتتاحي', 'المبلغ النهائي',
                'المبلغ المتوقع', 'الفرق', 'إجمالي المبيعات',
                'عدد العمليات', 'إجمالي المردودات',
            ]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = thin_border

            shifts = POSShift.objects.all()
            if date_from:
                shifts = shifts.filter(created_at__date__gte=date_from)
            if date_to:
                shifts = shifts.filter(created_at__date__lte=date_to)

            for row, shift_obj in enumerate(shifts, 2):
                cashier_name = shift_obj.cashier.get_full_name() or shift_obj.cashier.username
                data = [
                    shift_obj.shift_number,
                    cashier_name,
                    shift_obj.start_time.strftime('%Y-%m-%d %H:%M') if shift_obj.start_time else '',
                    shift_obj.end_time.strftime('%Y-%m-%d %H:%M') if shift_obj.end_time else '',
                    shift_obj.get_status_display(),
                    str(shift_obj.opening_cash),
                    str(shift_obj.closing_cash),
                    str(shift_obj.expected_cash),
                    str(shift_obj.difference),
                    str(shift_obj.total_sales),
                    str(shift_obj.total_transactions),
                    str(shift_obj.total_refunds),
                ]
                for col, value in enumerate(data, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    cell.alignment = cell_alignment
                    cell.border = thin_border

            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                ws.column_dimensions[column].width = max(max_length + 4, 15)

        # Prepare response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = (
            f'attachment; filename=pos_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        wb.save(response)
        return response
