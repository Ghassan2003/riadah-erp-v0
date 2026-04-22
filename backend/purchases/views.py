"""
API views for the Purchases module.
Handles Supplier CRUD, PurchaseOrder lifecycle, and inventory integration.
"""

from rest_framework import (
    generics, status, permissions, filters, views
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from .serializers import (
    SupplierListSerializer,
    SupplierCreateSerializer,
    SupplierUpdateSerializer,
    SupplierDetailSerializer,
    PurchaseOrderListSerializer,
    PurchaseOrderDetailSerializer,
    CreatePurchaseOrderSerializer,
    ChangePurchaseOrderStatusSerializer,
    PurchaseStatsSerializer,
)
from users.permissions import IsAdmin, IsSalesOrAdmin, IsWarehouseOrAdmin


# =============================================
# Supplier Views
# =============================================

class SupplierListView(generics.ListCreateAPIView):
    """GET: List suppliers. POST: Create supplier (admin/sales)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_en', 'email', 'phone']
    ordering_fields = ['name', 'created_at', 'email']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SupplierCreateSerializer
        return SupplierListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsSalesOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Supplier.objects.all()
        show_deleted = self.request.query_params.get('show_deleted')
        if show_deleted and show_deleted.lower() == 'true':
            return Supplier.all_objects.all() if hasattr(Supplier, 'all_objects') else queryset
        return queryset.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = serializer.save()
        return Response({
            'message': 'تم إضافة المورد بنجاح',
            'supplier': SupplierDetailSerializer(supplier).data,
        }, status=status.HTTP_201_CREATED)


class SupplierDetailView(generics.RetrieveUpdateAPIView):
    """GET: Supplier details. PATCH: Update supplier (admin/sales)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return SupplierUpdateSerializer
        return SupplierDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsSalesOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Supplier.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        supplier = serializer.save()
        return Response({
            'message': 'تم تحديث بيانات المورد بنجاح',
            'supplier': SupplierDetailSerializer(supplier).data,
        })


class SupplierSoftDeleteView(views.APIView):
    """DELETE: Soft-delete a supplier (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            supplier = Supplier.objects.get(pk=pk)
        except Supplier.DoesNotExist:
            return Response(
                {'error': 'المورد غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        supplier.soft_delete()
        return Response({'message': 'تم حذف المورد بنجاح'})


class SupplierRestoreView(views.APIView):
    """POST: Restore a soft-deleted supplier (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            supplier = Supplier.objects.get(pk=pk)
        except Supplier.DoesNotExist:
            return Response(
                {'error': 'المورد غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        supplier.restore()
        return Response({
            'message': 'تم استعادة المورد بنجاح',
            'supplier': SupplierDetailSerializer(supplier).data,
        })


# =============================================
# PurchaseOrder Views
# =============================================

class PurchaseOrderListView(generics.ListAPIView):
    """GET: List all purchase orders with filtering."""

    serializer_class = PurchaseOrderListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'supplier__name', 'notes']
    ordering_fields = ['order_number', 'order_date', 'total_amount', 'status', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = PurchaseOrder.objects.select_related('supplier', 'created_by')
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        # Filter by supplier
        supplier_param = self.request.query_params.get('supplier')
        if supplier_param:
            queryset = queryset.filter(supplier_id=supplier_param)
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(order_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(order_date__lte=date_to)
        return queryset


class PurchaseOrderDetailView(generics.RetrieveAPIView):
    """GET: Detailed view of a single order with items."""

    serializer_class = PurchaseOrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PurchaseOrder.objects.select_related('supplier', 'created_by').prefetch_related('items__product')


class PurchaseOrderCreateView(generics.CreateAPIView):
    """POST: Create a new purchase order with items."""

    serializer_class = CreatePurchaseOrderSerializer
    permission_classes = [IsSalesOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response({
            'message': 'تم إنشاء أمر الشراء بنجاح',
            'order': PurchaseOrderDetailSerializer(order).data,
        }, status=status.HTTP_201_CREATED)


class PurchaseOrderUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a draft purchase order."""

    serializer_class = CreatePurchaseOrderSerializer
    permission_classes = [IsSalesOrAdmin]

    def get_queryset(self):
        return PurchaseOrder.objects.filter(status='draft')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Delete old items and recreate
        instance.items.all().delete()
        items_data = serializer.validated_data.pop('items', [])

        for attr, value in serializer.validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for item_data in items_data:
            product = item_data['product']
            PurchaseOrderItem.objects.create(
                order=instance,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.unit_price,
            )

        instance.calculate_total()
        return Response({
            'message': 'تم تحديث أمر الشراء بنجاح',
            'order': PurchaseOrderDetailSerializer(instance).data,
        })


class PurchaseOrderDeleteView(views.APIView):
    """DELETE: Delete a draft purchase order (admin/sales only)."""

    permission_classes = [IsSalesOrAdmin]

    def delete(self, request, pk):
        try:
            order = PurchaseOrder.objects.get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response(
                {'error': 'أمر الشراء غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if order.status != 'draft':
            return Response(
                {'error': 'يمكن حذف الأوامر في حالة "مسودة" فقط'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.delete()
        return Response({'message': 'تم حذف أمر الشراء بنجاح'})


class PurchaseOrderStatusView(views.APIView):
    """POST: Change order status (confirm/receive/partial/cancel)."""

    permission_classes = [IsSalesOrAdmin]

    def post(self, request, pk):
        """Change the status of a purchase order."""
        try:
            order = PurchaseOrder.objects.select_related().get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response(
                {'error': 'أمر الشراء غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ChangePurchaseOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']

        try:
            order.change_status(new_status)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Auto-create journal entry for confirmed orders (Phase 4 integration)
        if new_status == 'confirmed':
            try:
                from accounting.views import create_purchase_journal_entry
                create_purchase_journal_entry(order)
            except Exception:
                pass  # Don't fail the order if accounting fails
        # Reverse journal entry for cancelled orders
        elif new_status == 'cancelled':
            try:
                from accounting.views import cancel_purchase_journal_entry
                cancel_purchase_journal_entry(order)
            except Exception:
                pass  # Don't fail the order if accounting fails

        return Response({
            'message': f'تم تغيير حالة الأمر إلى "{order.get_status_display()}"',
            'order': PurchaseOrderDetailSerializer(order).data,
        })


class PurchaseStatsView(generics.GenericAPIView):
    """GET: Purchase statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PurchaseStatsSerializer

    def get(self, request):
        today = timezone.now().date()
        this_month = today.replace(day=1)

        active_orders = PurchaseOrder.objects.filter(status__in=('draft', 'confirmed', 'partial', 'received'))
        completed_orders = active_orders.filter(status__in=('confirmed', 'partial', 'received'))

        stats = {
            'total_orders': active_orders.count(),
            'pending_orders': active_orders.filter(status='draft').count(),
            'confirmed_orders': completed_orders.count(),
            'total_purchases': completed_orders.aggregate(
                total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'today_purchases': completed_orders.filter(order_date=today).aggregate(
                total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'this_month_purchases': completed_orders.filter(order_date__gte=this_month).aggregate(
                total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'total_suppliers': Supplier.objects.filter(is_active=True).count(),
        }

        serializer = self.get_serializer(stats)
        return Response(serializer.data)


# =============================================
# Excel Export Views
# =============================================

class SupplierExportView(views.APIView):
    """GET: Export suppliers to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = Supplier.objects.filter(is_active=True)
        columns = [
            ('name', 'اسم المورد', 30),
            ('contact_person', 'جهة الاتصال', 25),
            ('email', 'البريد الإلكتروني', 30),
            ('phone', 'الهاتف', 15),
            ('address', 'العنوان', 35),
            ('tax_number', 'الرقم الضريبي', 20),
            ('balance', 'الرصيد', 15),
            ('is_active', 'نشط', 10),
        ]
        data = []
        for s in queryset:
            data.append({
                'name': s.name,
                'contact_person': s.contact_person or '',
                'email': s.email or '',
                'phone': s.phone or '',
                'address': s.address or '',
                'tax_number': s.tax_number or '',
                'balance': str(s.balance),
                'is_active': s.is_active,
            })
        return export_to_excel(data, columns, 'الموردون', 'suppliers.xlsx')


class PurchaseOrderExportView(views.APIView):
    """GET: Export purchase orders to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = PurchaseOrder.objects.select_related('supplier', 'created_by')
        columns = [
            ('order_number', 'رقم الأمر', 20),
            ('supplier', 'المورد', 25),
            ('status', 'الحالة', 15),
            ('order_date', 'تاريخ الأمر', 15),
            ('expected_date', 'تاريخ الاستلام المتوقع', 20),
            ('total_amount', 'الإجمالي', 15),
            ('notes', 'ملاحظات', 30),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for o in queryset:
            data.append({
                'order_number': o.order_number,
                'supplier': o.supplier.name if o.supplier else '',
                'status': o.get_status_display(),
                'order_date': str(o.order_date) if o.order_date else '',
                'expected_date': str(o.expected_date) if o.expected_date else '',
                'total_amount': str(o.total_amount),
                'notes': o.notes or '',
                'created_at': str(o.created_at.strftime('%Y-%m-%d %H:%M')) if o.created_at else '',
            })
        return export_to_excel(data, columns, 'أوامر الشراء', 'purchase_orders.xlsx')
