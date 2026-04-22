"""
API views for the Import/Export module.
Handles ImportOrders, ImportItems, ExportOrders, ExportItems,
CustomsDeclarations, stats, status changes, and export.
"""

from decimal import Decimal

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import HttpResponse

from .models import (
    ImportOrder,
    ImportItem,
    ExportOrder,
    ExportItem,
    CustomsDeclaration,
)
from .serializers import (
    ImportOrderListSerializer,
    ImportOrderCreateSerializer,
    ImportOrderDetailSerializer,
    ImportItemListSerializer,
    ImportItemCreateSerializer,
    ExportOrderListSerializer,
    ExportOrderCreateSerializer,
    ExportOrderDetailSerializer,
    ExportItemListSerializer,
    ExportItemCreateSerializer,
    CustomsDeclarationListSerializer,
    CustomsDeclarationCreateSerializer,
    CustomsDeclarationChangeStatusSerializer,
    ImportExportStatsSerializer,
    ChangeStatusSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Import/Export Stats View
# =============================================

class ImportExportStatsView(views.APIView):
    """GET: Import/Export statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stats = {
            'total_import_orders': ImportOrder.objects.count(),
            'active_import_orders': ImportOrder.objects.filter(
                status__in=('draft', 'submitted', 'customs', 'transit', 'warehouse')
            ).count(),
            'total_export_orders': ExportOrder.objects.count(),
            'active_export_orders': ExportOrder.objects.filter(
                status__in=('draft', 'confirmed', 'packed', 'customs', 'shipped')
            ).count(),
            'total_customs_declarations': CustomsDeclaration.objects.count(),
            'pending_customs': CustomsDeclaration.objects.filter(
                status__in=('draft', 'submitted', 'hold')
            ).count(),
            'total_import_value': ImportOrder.objects.aggregate(
                total=Coalesce(
                    Sum('total_amount'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_export_value': ExportOrder.objects.aggregate(
                total=Coalesce(
                    Sum('total_amount'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_landed_cost': ImportOrder.objects.aggregate(
                total=Coalesce(
                    Sum('total_landed_cost'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_customs_duties': ImportOrder.objects.aggregate(
                total=Coalesce(
                    Sum('customs_duties'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
        }

        serializer = ImportExportStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Import Order Views
# =============================================

class ImportOrderListView(generics.ListAPIView):
    """GET: List import orders with filtering."""

    serializer_class = ImportOrderListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'supplier__name', 'port_of_entry', 'country_of_origin']
    ordering_fields = ['order_number', 'order_date', 'status', 'total_amount', 'created_at']
    ordering = ['-order_date', '-created_at']

    def get_queryset(self):
        queryset = ImportOrder.objects.select_related('supplier', 'created_by')
        # Filter by status
        order_status = self.request.query_params.get('status')
        if order_status:
            queryset = queryset.filter(status=order_status)
        # Filter by supplier
        supplier = self.request.query_params.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        return queryset


class ImportOrderDetailView(generics.RetrieveAPIView):
    """GET: Import order details."""

    serializer_class = ImportOrderDetailSerializer

    def get_queryset(self):
        return ImportOrder.objects.select_related('supplier', 'created_by')


class ImportOrderCreateView(generics.CreateAPIView):
    """POST: Create import order (admin only)."""

    serializer_class = ImportOrderCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(created_by=request.user)

        # Recalculate landed cost
        order.recalculate()

        return Response({
            'message': 'تم إنشاء أمر الاستيراد بنجاح',
            'order': ImportOrderDetailSerializer(order).data,
        }, status=status.HTTP_201_CREATED)


class ImportOrderChangeStatusView(views.APIView):
    """POST: Change import order status (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            order = ImportOrder.objects.select_related('supplier').get(pk=pk)
        except ImportOrder.DoesNotExist:
            return Response(
                {'error': 'أمر الاستيراد غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        valid_statuses = [s[0] for s in ImportOrder.STATUS_CHOICES]

        if new_status not in valid_statuses:
            return Response(
                {'error': 'حالة غير صالحة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = order.status
        order.status = new_status
        order.save()

        return Response({
            'message': f'تم تغيير حالة أمر الاستيراد من {order.get_status_display()} بنجاح',
            'order': ImportOrderDetailSerializer(order).data,
        })


# =============================================
# Import Item Views
# =============================================

class ImportItemListView(generics.ListAPIView):
    """GET: List import items with filtering."""

    serializer_class = ImportItemListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'hs_code', 'product__name']
    ordering_fields = ['description', 'quantity', 'unit_price', 'total_price', 'created_at']
    ordering = ['id']

    def get_queryset(self):
        queryset = ImportItem.objects.select_related('import_order', 'product')
        # Filter by import_order
        import_order = self.request.query_params.get('import_order')
        if import_order:
            queryset = queryset.filter(import_order_id=import_order)
        return queryset


class ImportItemDetailView(generics.RetrieveAPIView):
    """GET: Import item details."""

    serializer_class = ImportItemListSerializer

    def get_queryset(self):
        return ImportItem.objects.select_related('import_order', 'product')


# =============================================
# Export Order Views
# =============================================

class ExportOrderListView(generics.ListAPIView):
    """GET: List export orders with filtering."""

    serializer_class = ExportOrderListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'customer__name', 'destination_country', 'destination_port']
    ordering_fields = ['order_number', 'order_date', 'status', 'total_amount', 'created_at']
    ordering = ['-order_date', '-created_at']

    def get_queryset(self):
        queryset = ExportOrder.objects.select_related('customer', 'created_by')
        # Filter by status
        order_status = self.request.query_params.get('status')
        if order_status:
            queryset = queryset.filter(status=order_status)
        # Filter by customer
        customer = self.request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(customer_id=customer)
        return queryset


class ExportOrderDetailView(generics.RetrieveAPIView):
    """GET: Export order details."""

    serializer_class = ExportOrderDetailSerializer

    def get_queryset(self):
        return ExportOrder.objects.select_related('customer', 'created_by')


class ExportOrderCreateView(generics.CreateAPIView):
    """POST: Create export order (admin only)."""

    serializer_class = ExportOrderCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(created_by=request.user)

        return Response({
            'message': 'تم إنشاء أمر التصدير بنجاح',
            'order': ExportOrderDetailSerializer(order).data,
        }, status=status.HTTP_201_CREATED)


class ExportOrderChangeStatusView(views.APIView):
    """POST: Change export order status (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            order = ExportOrder.objects.select_related('customer').get(pk=pk)
        except ExportOrder.DoesNotExist:
            return Response(
                {'error': 'أمر التصدير غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        valid_statuses = [s[0] for s in ExportOrder.STATUS_CHOICES]

        if new_status not in valid_statuses:
            return Response(
                {'error': 'حالة غير صالحة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        order.save()

        return Response({
            'message': f'تم تغيير حالة أمر التصدير بنجاح',
            'order': ExportOrderDetailSerializer(order).data,
        })


# =============================================
# Export Item Views
# =============================================

class ExportItemListView(generics.ListAPIView):
    """GET: List export items with filtering."""

    serializer_class = ExportItemListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'hs_code', 'product__name']
    ordering_fields = ['description', 'quantity', 'unit_price', 'total_price', 'created_at']
    ordering = ['id']

    def get_queryset(self):
        queryset = ExportItem.objects.select_related('export_order', 'product')
        # Filter by export_order
        export_order = self.request.query_params.get('export_order')
        if export_order:
            queryset = queryset.filter(export_order_id=export_order)
        return queryset


class ExportItemDetailView(generics.RetrieveAPIView):
    """GET: Export item details."""

    serializer_class = ExportItemListSerializer

    def get_queryset(self):
        return ExportItem.objects.select_related('export_order', 'product')


# =============================================
# Customs Declaration Views
# =============================================

class CustomsDeclarationListView(generics.ListAPIView):
    """GET: List customs declarations with filtering."""

    serializer_class = CustomsDeclarationListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['declaration_number', 'import_order__order_number', 'export_order__order_number']
    ordering_fields = ['declaration_number', 'declaration_type', 'status', 'declared_value', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = CustomsDeclaration.objects.select_related(
            'import_order', 'export_order', 'created_by'
        )
        # Filter by status
        decl_status = self.request.query_params.get('status')
        if decl_status:
            queryset = queryset.filter(status=decl_status)
        # Filter by declaration type
        decl_type = self.request.query_params.get('declaration_type')
        if decl_type:
            queryset = queryset.filter(declaration_type=decl_type)
        return queryset


class CustomsDeclarationDetailView(generics.RetrieveAPIView):
    """GET: Customs declaration details."""

    serializer_class = CustomsDeclarationListSerializer

    def get_queryset(self):
        return CustomsDeclaration.objects.select_related(
            'import_order', 'export_order', 'created_by'
        )


class CustomsDeclarationCreateView(generics.CreateAPIView):
    """POST: Create customs declaration (admin only)."""

    serializer_class = CustomsDeclarationCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        declaration = serializer.save(created_by=request.user)

        return Response({
            'message': 'تم إنشاء الإقرار الجمركي بنجاح',
            'declaration': CustomsDeclarationListSerializer(declaration).data,
        }, status=status.HTTP_201_CREATED)


class CustomsDeclarationChangeStatusView(views.APIView):
    """POST: Change customs declaration status (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            declaration = CustomsDeclaration.objects.select_related(
                'import_order', 'export_order'
            ).get(pk=pk)
        except CustomsDeclaration.DoesNotExist:
            return Response(
                {'error': 'الإقرار الجمركي غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomsDeclarationChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        old_status = declaration.status
        declaration.status = new_status

        # Set dates based on status change
        if new_status == 'submitted' and not declaration.submitted_date:
            declaration.submitted_date = timezone.now().date()
        if new_status == 'cleared' and not declaration.cleared_date:
            declaration.cleared_date = timezone.now().date()

        declaration.save()

        return Response({
            'message': f'تم تغيير حالة الإقرار الجمركي بنجاح',
            'declaration': CustomsDeclarationListSerializer(declaration).data,
        })


# =============================================
# Import/Export Export View
# =============================================

class ImportExportExportView(views.APIView):
    """GET: Export import/export data to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        export_type = request.query_params.get('type', 'import')

        if export_type == 'import':
            queryset = ImportOrder.objects.select_related('supplier').order_by('-order_date')
            columns = [
                ('order_number', 'رقم الأمر', 18),
                ('supplier_name', 'المورد', 25),
                ('order_date', 'تاريخ الأمر', 14),
                ('expected_arrival', 'تاريخ الوصول المتوقع', 16),
                ('actual_arrival', 'تاريخ الوصول الفعلي', 16),
                ('port_of_entry', 'ميناء الدخول', 20),
                ('country_of_origin', 'بلد المنشأ', 18),
                ('currency', 'العملة', 10),
                ('exchange_rate', 'سعر الصرف', 12),
                ('status_display', 'الحالة', 14),
                ('total_amount', 'إجمالي المبلغ', 16),
                ('customs_duties', 'الرسوم الجمركية', 16),
                ('shipping_cost', 'تكلفة الشحن', 14),
                ('insurance_cost', 'تكلفة التأمين', 14),
                ('other_costs', 'تكاليف أخرى', 14),
                ('total_landed_cost', 'التكلفة الواردة', 16),
            ]
            data = []
            for o in queryset:
                data.append({
                    'order_number': o.order_number,
                    'supplier_name': o.supplier.name if o.supplier else '',
                    'order_date': str(o.order_date),
                    'expected_arrival': str(o.expected_arrival) if o.expected_arrival else '',
                    'actual_arrival': str(o.actual_arrival) if o.actual_arrival else '',
                    'port_of_entry': o.port_of_entry,
                    'country_of_origin': o.country_of_origin,
                    'currency': o.currency,
                    'exchange_rate': str(o.exchange_rate),
                    'status_display': o.get_status_display(),
                    'total_amount': str(o.total_amount),
                    'customs_duties': str(o.customs_duties),
                    'shipping_cost': str(o.shipping_cost),
                    'insurance_cost': str(o.insurance_cost),
                    'other_costs': str(o.other_costs),
                    'total_landed_cost': str(o.total_landed_cost),
                })
            return export_to_excel(data, columns, 'أوامر الاستيراد', 'import_orders.xlsx')

        elif export_type == 'export':
            queryset = ExportOrder.objects.select_related('customer').order_by('-order_date')
            columns = [
                ('order_number', 'رقم الأمر', 18),
                ('customer_name', 'العميل', 25),
                ('order_date', 'تاريخ الأمر', 14),
                ('ship_date', 'تاريخ الشحن', 14),
                ('port_of_loading', 'ميناء التحميل', 20),
                ('destination_country', 'بلد الوجهة', 18),
                ('destination_port', 'ميناء الوجهة', 20),
                ('currency', 'العملة', 10),
                ('exchange_rate', 'سعر الصرف', 12),
                ('status_display', 'الحالة', 14),
                ('total_amount', 'إجمالي المبلغ', 16),
                ('shipping_terms', 'شروط الشحن', 16),
            ]
            data = []
            for o in queryset:
                data.append({
                    'order_number': o.order_number,
                    'customer_name': o.customer.name if o.customer else '',
                    'order_date': str(o.order_date),
                    'ship_date': str(o.ship_date) if o.ship_date else '',
                    'port_of_loading': o.port_of_loading,
                    'destination_country': o.destination_country,
                    'destination_port': o.destination_port,
                    'currency': o.currency,
                    'exchange_rate': str(o.exchange_rate),
                    'status_display': o.get_status_display(),
                    'total_amount': str(o.total_amount),
                    'shipping_terms': o.shipping_terms,
                })
            return export_to_excel(data, columns, 'أوامر التصدير', 'export_orders.xlsx')

        elif export_type == 'customs':
            queryset = CustomsDeclaration.objects.select_related(
                'import_order', 'export_order'
            ).order_by('-created_at')
            columns = [
                ('declaration_number', 'رقم الإقرار', 18),
                ('declaration_type_display', 'النوع', 12),
                ('related_order', 'الأمر المرتبط', 18),
                ('status_display', 'الحالة', 14),
                ('submitted_date', 'تاريخ التقديم', 14),
                ('cleared_date', 'تاريخ التخليص', 14),
                ('declared_value', 'القيمة المصرّح بها', 16),
                ('duties_amount', 'مبلغ الرسوم', 14),
                ('taxes_amount', 'مبلغ الضرائب', 14),
            ]
            data = []
            for d in queryset:
                data.append({
                    'declaration_number': d.declaration_number,
                    'declaration_type_display': d.get_declaration_type_display(),
                    'related_order': (
                        d.import_order.order_number if d.import_order
                        else d.export_order.order_number if d.export_order
                        else ''
                    ),
                    'status_display': d.get_status_display(),
                    'submitted_date': str(d.submitted_date) if d.submitted_date else '',
                    'cleared_date': str(d.cleared_date) if d.cleared_date else '',
                    'declared_value': str(d.declared_value),
                    'duties_amount': str(d.duties_amount),
                    'taxes_amount': str(d.taxes_amount),
                })
            return export_to_excel(data, columns, 'الإقرارات الجمركية', 'customs_declarations.xlsx')

        else:
            return Response(
                {'error': 'نوع التصدير غير صالح (import/export/customs)'},
                status=status.HTTP_400_BAD_REQUEST,
            )
