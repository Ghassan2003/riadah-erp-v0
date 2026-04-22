"""
API views for the Sales module.
Handles Customer CRUD, SalesOrder lifecycle, and inventory integration.
"""

from rest_framework import (
    generics, status, permissions, filters, views, viewsets
)
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Customer, SalesOrder, SalesOrderItem
from .serializers import (
    CustomerListSerializer,
    CustomerCreateSerializer,
    CustomerUpdateSerializer,
    CustomerDetailSerializer,
    SalesOrderListSerializer,
    SalesOrderDetailSerializer,
    CreateSalesOrderSerializer,
    ChangeOrderStatusSerializer,
    SalesStatsSerializer,
)
from users.permissions import IsSalesOrAdmin, IsWarehouseOrAdmin
from core.decorators import PermissionRequiredMixin


# =============================================
# Customer Views
# =============================================

class CustomerListView(PermissionRequiredMixin, generics.ListCreateAPIView):
    """GET: List customers. POST: Create customer (admin/sales)."""

    permission_module = 'sales'
    permission_action = {'get': 'view', 'post': 'create'}

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at', 'email']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerCreateSerializer
        return CustomerListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsSalesOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Customer.objects.all()
        show_deleted = self.request.query_params.get('show_deleted')
        if show_deleted and show_deleted.lower() == 'true':
            return Customer.all_objects.all() if hasattr(Customer, 'all_objects') else queryset
        return queryset.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return Response({
            'message': 'تم إضافة العميل بنجاح',
            'customer': CustomerDetailSerializer(customer).data,
        }, status=status.HTTP_201_CREATED)


class CustomerDetailView(PermissionRequiredMixin, generics.RetrieveUpdateAPIView):
    """GET: Customer details. PATCH: Update customer (admin/sales)."""

    permission_module = 'sales'
    permission_action = {'get': 'view', 'put': 'edit', 'patch': 'edit'}

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CustomerUpdateSerializer
        return CustomerDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsSalesOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Customer.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return Response({
            'message': 'تم تحديث بيانات العميل بنجاح',
            'customer': CustomerDetailSerializer(customer).data,
        })


class CustomerSoftDeleteView(views.APIView):
    """DELETE: Soft-delete a customer (admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        try:
            customer = Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'العميل غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        customer.soft_delete()
        return Response({'message': 'تم حذف العميل بنجاح'})


# =============================================
# SalesOrder Views
# =============================================

class SalesOrderListView(PermissionRequiredMixin, generics.ListAPIView):
    """GET: List all sales orders with filtering."""

    permission_module = 'sales'
    permission_action = 'view'

    serializer_class = SalesOrderListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'customer__name', 'notes']
    ordering_fields = ['order_number', 'order_date', 'total_amount', 'status', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = SalesOrder.objects.select_related('customer', 'created_by')
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        # Filter by customer
        customer_param = self.request.query_params.get('customer')
        if customer_param:
            queryset = queryset.filter(customer_id=customer_param)
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(order_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(order_date__lte=date_to)
        return queryset


class SalesOrderDetailView(PermissionRequiredMixin, generics.RetrieveAPIView):
    """GET: Detailed view of a single order with items."""

    permission_module = 'sales'
    permission_action = 'view'

    serializer_class = SalesOrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SalesOrder.objects.select_related('customer', 'created_by').prefetch_related('items__product')


class SalesOrderCreateView(PermissionRequiredMixin, generics.CreateAPIView):
    """POST: Create a new sales order with items."""

    permission_module = 'sales'
    permission_action = 'create'

    serializer_class = CreateSalesOrderSerializer
    permission_classes = [IsSalesOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response({
            'message': 'تم إنشاء أمر البيع بنجاح',
            'order': SalesOrderDetailSerializer(order).data,
        }, status=status.HTTP_201_CREATED)


class SalesOrderStatusView(views.APIView):
    """POST: Change order status (confirm/ship/deliver/cancel)."""

    permission_classes = [IsSalesOrAdmin]

    def post(self, request, pk):
        """Change the status of a sales order."""
        try:
            order = SalesOrder.objects.select_related().get(pk=pk)
        except SalesOrder.DoesNotExist:
            return Response(
                {'error': 'أمر البيع غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ChangeOrderStatusSerializer(data=request.data)
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
                from accounting.views import create_sales_journal_entry
                create_sales_journal_entry(order)
            except Exception:
                pass  # Don't fail the order if accounting fails
        # Reverse journal entry for cancelled orders
        elif new_status == 'cancelled':
            try:
                from accounting.views import cancel_sales_journal_entry
                cancel_sales_journal_entry(order)
            except Exception:
                pass  # Don't fail the order if accounting fails

        return Response({
            'message': f'تم تغيير حالة الأمر إلى "{order.get_status_display()}"',
            'order': SalesOrderDetailSerializer(order).data,
        })


class SalesOrderUpdateView(PermissionRequiredMixin, generics.UpdateAPIView):
    """PUT/PATCH: Update a draft sales order (replace items and recalculate total)."""

    permission_module = 'sales'
    permission_action = 'edit'

    permission_classes = [IsSalesOrAdmin]
    serializer_class = CreateSalesOrderSerializer

    def get_queryset(self):
        return SalesOrder.objects.select_related('customer', 'created_by').prefetch_related('items__product')

    def update(self, request, *args, **kwargs):
        """Update a draft sales order by replacing all items."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.status != 'draft':
            return Response(
                {'error': 'يمكن تعديل الأوامر في حالة "مسودة" فقط'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # Delete old items
            instance.items.all().delete()
            # Create new items from serializer
            items_data = serializer.validated_data.get('items', [])
            for item_data in items_data:
                product = item_data['product']
                SalesOrderItem.objects.create(
                    order=instance,
                    product=product,
                    quantity=item_data['quantity'],
                    unit_price=product.unit_price,
                )
            # Update order fields
            instance.customer = serializer.validated_data.get('customer', instance.customer)
            instance.notes = serializer.validated_data.get('notes', instance.notes)
            instance.calculate_total()

        return Response({
            'message': 'تم تحديث أمر البيع بنجاح',
            'order': SalesOrderDetailSerializer(instance).data,
        })


class SalesOrderDeleteView(views.APIView):
    """DELETE: Delete a draft sales order (admin only)."""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        """Delete a sales order that is in draft status."""
        try:
            order = SalesOrder.objects.get(pk=pk)
        except SalesOrder.DoesNotExist:
            return Response(
                {'error': 'أمر البيع غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status != 'draft':
            return Response(
                {'error': 'يمكن حذف الأوامر في حالة "مسودة" فقط'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.delete()
        return Response({'message': 'تم حذف أمر البيع بنجاح'})


class CustomerExportView(views.APIView):
    """GET: Export customers to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = Customer.objects.filter(is_active=True)
        columns = [
            ('name', 'اسم العميل', 30),
            ('email', 'البريد الإلكتروني', 30),
            ('phone', 'الهاتف', 15),
            ('address', 'العنوان', 35),
            ('is_active', 'نشط', 10),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for c in queryset:
            data.append({
                'name': c.name,
                'email': c.email or '',
                'phone': c.phone or '',
                'address': c.address or '',
                'is_active': c.is_active,
                'created_at': str(c.created_at.strftime('%Y-%m-%d %H:%M')) if c.created_at else '',
            })
        return export_to_excel(data, columns, 'العملاء', 'customers.xlsx')


class SalesOrderExportView(views.APIView):
    """GET: Export sales orders to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = SalesOrder.objects.select_related('customer', 'created_by')
        columns = [
            ('order_number', 'رقم الأمر', 20),
            ('customer', 'العميل', 25),
            ('status', 'الحالة', 15),
            ('order_date', 'تاريخ الأمر', 15),
            ('total_amount', 'الإجمالي', 15),
            ('notes', 'ملاحظات', 30),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for o in queryset:
            data.append({
                'order_number': o.order_number,
                'customer': o.customer.name if o.customer else '',
                'status': o.get_status_display(),
                'order_date': str(o.order_date) if o.order_date else '',
                'total_amount': str(o.total_amount),
                'notes': o.notes or '',
                'created_at': str(o.created_at.strftime('%Y-%m-%d %H:%M')) if o.created_at else '',
            })
        return export_to_excel(data, columns, 'أوامر البيع', 'sales_orders.xlsx')


class SalesStatsView(generics.GenericAPIView):
    """GET: Sales statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SalesStatsSerializer

    def get(self, request):
        today = timezone.now().date()
        this_month = today.replace(day=1)

        active_orders = SalesOrder.objects.filter(status__in=('draft', 'confirmed', 'shipped', 'delivered'))
        completed_orders = active_orders.filter(status__in=('confirmed', 'shipped', 'delivered'))

        stats = {
            'total_orders': active_orders.count(),
            'pending_orders': active_orders.filter(status='draft').count(),
            'confirmed_orders': completed_orders.count(),
            'total_sales': completed_orders.aggregate(
                total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'today_sales': completed_orders.filter(order_date=today).aggregate(
                total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'this_month_sales': completed_orders.filter(order_date__gte=this_month).aggregate(
                total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
        }

        serializer = self.get_serializer(stats)
        return Response(serializer.data)
