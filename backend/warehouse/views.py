"""
API views for the Warehouse module.
Handles warehouses, stocks, transfers, adjustments, and counts.
"""

from rest_framework import (
    generics, status, permissions, filters, views
)
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .models import (
    Warehouse, WarehouseStock, StockTransfer, StockTransferItem,
    StockAdjustment, StockCount, StockCountItem,
)
from .serializers import (
    WarehouseListSerializer, WarehouseCreateSerializer, WarehouseUpdateSerializer,
    WarehouseDetailSerializer,
    WarehouseStockListSerializer, WarehouseStockCreateSerializer, WarehouseStockUpdateSerializer,
    StockTransferListSerializer, StockTransferCreateSerializer,
    StockTransferItemListSerializer, StockTransferApproveSerializer, StockTransferReceiveSerializer,
    StockAdjustmentListSerializer, StockAdjustmentCreateSerializer,
    StockCountListSerializer, StockCountCreateSerializer, StockCountItemListSerializer,
    WarehouseStatsSerializer,
)
from users.permissions import IsAdmin, IsWarehouseOrAdmin


# =============================================
# Warehouse Views
# =============================================

class WarehouseListView(generics.ListCreateAPIView):
    """GET: List warehouses. POST: Create warehouse (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'city']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WarehouseCreateSerializer
        return WarehouseListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Warehouse.objects.prefetch_related('manager')
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wh = serializer.save()
        return Response({
            'message': 'تم إنشاء المستودع بنجاح',
            'warehouse': WarehouseDetailSerializer(wh).data,
        }, status=status.HTTP_201_CREATED)


class WarehouseDetailView(generics.RetrieveUpdateAPIView):
    """GET: Warehouse details. PATCH: Update warehouse (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return WarehouseUpdateSerializer
        return WarehouseDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Warehouse.objects.prefetch_related('manager')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        wh = serializer.save()
        return Response({
            'message': 'تم تحديث المستودع بنجاح',
            'warehouse': WarehouseDetailSerializer(wh).data,
        })


class WarehouseDeleteView(views.APIView):
    """DELETE: Soft-delete a warehouse (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            wh = Warehouse.objects.get(pk=pk)
        except Warehouse.DoesNotExist:
            return Response({'error': 'المستودع غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        wh.is_active = False
        wh.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم حذف المستودع بنجاح'})


class WarehouseRestoreView(views.APIView):
    """POST: Restore a soft-deleted warehouse (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            wh = Warehouse.objects.get(pk=pk)
        except Warehouse.DoesNotExist:
            return Response({'error': 'المستودع غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        wh.is_active = True
        wh.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم إعادة تفعيل المستودع بنجاح'})


# =============================================
# WarehouseStock Views
# =============================================

class WarehouseStockListView(generics.ListAPIView):
    """GET: List warehouse stock levels with filtering."""

    serializer_class = WarehouseStockListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['quantity', 'product__name', 'warehouse__name']
    ordering = ['warehouse__name', 'product__name']

    def get_queryset(self):
        queryset = WarehouseStock.objects.select_related('warehouse', 'product')
        warehouse = self.request.query_params.get('warehouse')
        if warehouse:
            queryset = queryset.filter(warehouse_id=warehouse)
        product = self.request.query_params.get('product')
        if product:
            queryset = queryset.filter(product_id=product)
        low_stock = self.request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            queryset = queryset.filter(quantity__lte=F('min_stock_level'))
        return queryset


class WarehouseStockCreateView(generics.CreateAPIView):
    """POST: Create a warehouse stock record (admin/warehouse only)."""

    serializer_class = WarehouseStockCreateSerializer
    permission_classes = [IsWarehouseOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stock = serializer.save()
        return Response({
            'message': 'تم إنشاء رصيد المخزون بنجاح',
            'stock': WarehouseStockListSerializer(stock).data,
        }, status=status.HTTP_201_CREATED)


class WarehouseStockUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update warehouse stock (admin/warehouse only)."""

    serializer_class = WarehouseStockUpdateSerializer
    permission_classes = [IsWarehouseOrAdmin]

    def get_queryset(self):
        return WarehouseStock.objects.select_related('warehouse', 'product')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        stock = serializer.save()
        return Response({
            'message': 'تم تحديث رصيد المخزون بنجاح',
            'stock': WarehouseStockListSerializer(stock).data,
        })


# =============================================
# StockTransfer Views
# =============================================

class StockTransferListView(generics.ListAPIView):
    """GET: List stock transfers with filtering."""

    serializer_class = StockTransferListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['transfer_number', 'notes']
    ordering_fields = ['transfer_number', 'status', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = StockTransfer.objects.select_related(
            'from_warehouse', 'to_warehouse', 'requested_by', 'approved_by'
        ).prefetch_related('items__product')
        from_warehouse = self.request.query_params.get('from_warehouse')
        if from_warehouse:
            queryset = queryset.filter(from_warehouse_id=from_warehouse)
        to_warehouse = self.request.query_params.get('to_warehouse')
        if to_warehouse:
            queryset = queryset.filter(to_warehouse_id=to_warehouse)
        transfer_status = self.request.query_params.get('status')
        if transfer_status:
            queryset = queryset.filter(status=transfer_status)
        return queryset


class StockTransferCreateView(generics.CreateAPIView):
    """POST: Create a stock transfer (admin/warehouse only)."""

    serializer_class = StockTransferCreateSerializer
    permission_classes = [IsWarehouseOrAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items_data = serializer.validated_data.pop('items')
        transfer = StockTransfer.objects.create(**serializer.validated_data)
        for item_data in items_data:
            StockTransferItem.objects.create(transfer=transfer, **item_data)
        transfer.status = 'pending'
        transfer.save(update_fields=['status', 'updated_at'])
        return Response({
            'message': 'تم إنشاء طلب التحويل بنجاح',
            'transfer': StockTransferListSerializer(transfer).data,
        }, status=status.HTTP_201_CREATED)


class StockTransferApproveView(views.APIView):
    """POST: Approve or reject a stock transfer (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            transfer = StockTransfer.objects.select_related('from_warehouse', 'to_warehouse').get(pk=pk)
        except StockTransfer.DoesNotExist:
            return Response({'error': 'التحويل غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StockTransferApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data['action']

        if transfer.status != 'pending':
            return Response({'error': 'يمكن الموافقة أو الرفض فقط على التحويلات المعلقة'}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'approve':
            # Reserve stock from source warehouse
            for item in transfer.items.all():
                try:
                    stock = WarehouseStock.objects.get(
                        warehouse=transfer.from_warehouse, product=item.product
                    )
                    if stock.available_quantity < item.quantity:
                        return Response(
                            {'error': f'الكمية المتاحة من "{item.product.name}" غير كافية في المستودع المصدر'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    stock.reserved_quantity += item.quantity
                    stock.save(update_fields=['reserved_quantity', 'updated_at'])
                except WarehouseStock.DoesNotExist:
                    return Response(
                        {'error': f'المنتج "{item.product.name}" غير موجود في المستودع المصدر'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            transfer.status = 'in_transit'
            transfer.approved_by = request.user
            transfer.approved_at = timezone.now()
            transfer.save()
            return Response({
                'message': 'تمت الموافقة على التحويل وبدء النقل',
                'transfer': StockTransferListSerializer(transfer).data,
            })
        else:
            transfer.status = 'cancelled'
            transfer.approved_by = request.user
            transfer.approved_at = timezone.now()
            transfer.save()
            return Response({
                'message': 'تم رفض التحويل',
                'transfer': StockTransferListSerializer(transfer).data,
            })


class StockTransferReceiveView(views.APIView):
    """POST: Receive items for a stock transfer (admin/warehouse only)."""

    permission_classes = [IsWarehouseOrAdmin]

    @transaction.atomic
    def post(self, request, pk):
        try:
            transfer = StockTransfer.objects.select_related('from_warehouse', 'to_warehouse').get(pk=pk)
        except StockTransfer.DoesNotExist:
            return Response({'error': 'التحويل غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        if transfer.status != 'in_transit':
            return Response({'error': 'يمكن الاستلام فقط للتحويلات قيد النقل'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = StockTransferReceiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items_data = {str(item['item_id']): item['received_quantity'] for item in serializer.validated_data['items']}

        for item in transfer.items.all():
            received_qty = float(items_data.get(str(item.id), item.received_quantity))
            item.received_quantity = received_qty
            item.save(update_fields=['received_quantity'])

            # Deduct from source warehouse
            try:
                from_stock = WarehouseStock.objects.get(
                    warehouse=transfer.from_warehouse, product=item.product
                )
                from_stock.quantity -= item.received_quantity
                from_stock.reserved_quantity -= min(item.quantity, item.received_quantity)
                from_stock.save(update_fields=['quantity', 'reserved_quantity', 'updated_at'])
            except WarehouseStock.DoesNotExist:
                pass

            # Add to destination warehouse
            to_stock, _ = WarehouseStock.objects.get_or_create(
                warehouse=transfer.to_warehouse, product=item.product,
                defaults={'quantity': 0, 'reserved_quantity': 0}
            )
            to_stock.quantity += item.received_quantity
            to_stock.last_restock_date = timezone.now().date()
            to_stock.save(update_fields=['quantity', 'last_restock_date', 'updated_at'])

        transfer.status = 'completed'
        transfer.save(update_fields=['status', 'updated_at'])
        return Response({
            'message': 'تم استلام التحويل بنجاح',
            'transfer': StockTransferListSerializer(transfer).data,
        })


# =============================================
# StockAdjustment Views
# =============================================

class StockAdjustmentListView(generics.ListAPIView):
    """GET: List stock adjustments with filtering."""

    serializer_class = StockAdjustmentListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['adjustment_number', 'notes', 'product__name']
    ordering_fields = ['adjustment_number', 'reason', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = StockAdjustment.objects.select_related('warehouse', 'product', 'created_by')
        warehouse = self.request.query_params.get('warehouse')
        if warehouse:
            queryset = queryset.filter(warehouse_id=warehouse)
        reason = self.request.query_params.get('reason')
        if reason:
            queryset = queryset.filter(reason=reason)
        return queryset


class StockAdjustmentCreateView(generics.CreateAPIView):
    """POST: Create a stock adjustment (admin/warehouse only). Updates stock."""

    serializer_class = StockAdjustmentCreateSerializer
    permission_classes = [IsWarehouseOrAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        adj = serializer.save(created_by=request.user)

        # Update warehouse stock
        stock, _ = WarehouseStock.objects.get_or_create(
            warehouse=adj.warehouse, product=adj.product,
            defaults={'quantity': 0, 'reserved_quantity': 0}
        )
        stock.quantity = adj.new_quantity
        stock.last_restock_date = timezone.now().date()
        stock.save(update_fields=['quantity', 'last_restock_date', 'updated_at'])

        return Response({
            'message': 'تم إنشاء التسوية وتحديث المخزون بنجاح',
            'adjustment': StockAdjustmentListSerializer(adj).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# StockCount Views
# =============================================

class StockCountListView(generics.ListAPIView):
    """GET: List stock counts with filtering."""

    serializer_class = StockCountListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['count_number', 'notes']
    ordering_fields = ['count_number', 'status', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = StockCount.objects.select_related('warehouse', 'counted_by').prefetch_related('items__product')
        warehouse = self.request.query_params.get('warehouse')
        if warehouse:
            queryset = queryset.filter(warehouse_id=warehouse)
        count_status = self.request.query_params.get('status')
        if count_status:
            queryset = queryset.filter(status=count_status)
        return queryset


class StockCountDetailView(generics.RetrieveAPIView):
    """GET: Stock count detail with items."""

    serializer_class = StockCountListSerializer

    def get_queryset(self):
        return StockCount.objects.select_related('warehouse', 'counted_by').prefetch_related('items__product')


class StockCountCreateView(generics.CreateAPIView):
    """POST: Create a stock count (admin/warehouse only)."""

    serializer_class = StockCountCreateSerializer
    permission_classes = [IsWarehouseOrAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items_data = serializer.validated_data.pop('items')
        count = StockCount.objects.create(**serializer.validated_data, status='in_progress', started_at=timezone.now())
        for item_data in items_data:
            StockCountItem.objects.create(count=count, **item_data)
        return Response({
            'message': 'تم إنشاء الجرد بنجاح',
            'count': StockCountListSerializer(count).data,
        }, status=status.HTTP_201_CREATED)


class StockCountCompleteView(views.APIView):
    """POST: Complete a stock count and create adjustments (admin/warehouse only)."""

    permission_classes = [IsWarehouseOrAdmin]

    @transaction.atomic
    def post(self, request, pk):
        try:
            count = StockCount.objects.select_related('warehouse').prefetch_related('items__product').get(pk=pk)
        except StockCount.DoesNotExist:
            return Response({'error': 'الجرد غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        if count.status not in ('draft', 'in_progress'):
            return Response({'error': 'يمكن إكمال الجرد فقط في حالة مسودة أو قيد التنفيذ'}, status=status.HTTP_400_BAD_REQUEST)

        adjustments_created = 0
        for item in count.items.all():
            if item.counted_quantity != item.system_quantity:
                StockAdjustment.objects.create(
                    warehouse=count.warehouse,
                    reason='count',
                    product=item.product,
                    previous_quantity=item.system_quantity,
                    new_quantity=item.counted_quantity,
                    notes=f'تسوية ناتجة عن الجرد {count.count_number}',
                    created_by=request.user,
                )
                # Update warehouse stock
                stock, _ = WarehouseStock.objects.get_or_create(
                    warehouse=count.warehouse, product=item.product,
                    defaults={'quantity': 0, 'reserved_quantity': 0}
                )
                stock.quantity = item.counted_quantity
                stock.last_restock_date = timezone.now().date()
                stock.save(update_fields=['quantity', 'last_restock_date', 'updated_at'])
                adjustments_created += 1

        has_adjustments = adjustments_created > 0
        count.status = 'adjusted' if has_adjustments else 'completed'
        count.completed_at = timezone.now()
        count.save()

        return Response({
            'message': f'تم إكمال الجرد بنجاح. تم إنشاء {adjustments_created} تسوية.',
            'count': StockCountListSerializer(count).data,
        })


# =============================================
# Warehouse Stock Detail and Delete
# =============================================

class WarehouseStockDetailView(generics.RetrieveAPIView):
    """GET: Warehouse stock detail."""

    serializer_class = WarehouseStockListSerializer

    def get_queryset(self):
        return WarehouseStock.objects.select_related('warehouse', 'product')


class WarehouseStockDeleteView(views.APIView):
    """DELETE: Delete a warehouse stock record (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            stock = WarehouseStock.objects.get(pk=pk)
        except WarehouseStock.DoesNotExist:
            return Response({'error': 'رصيد المخزون غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        stock.delete()
        return Response({'message': 'تم حذف رصيد المخزون بنجاح'})


# =============================================
# Stock Transfer Detail, Update, and Cancel
# =============================================

class StockTransferDetailView(generics.RetrieveAPIView):
    """GET: Stock transfer detail with items."""

    serializer_class = StockTransferListSerializer

    def get_queryset(self):
        return StockTransfer.objects.select_related(
            'from_warehouse', 'to_warehouse', 'requested_by', 'approved_by'
        ).prefetch_related('items__product')


class StockTransferUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a pending stock transfer (admin/warehouse only)."""

    serializer_class = StockTransferCreateSerializer
    permission_classes = [IsWarehouseOrAdmin]

    def get_queryset(self):
        return StockTransfer.objects.select_related(
            'from_warehouse', 'to_warehouse', 'requested_by', 'approved_by'
        ).prefetch_related('items__product')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.status != 'pending':
            return Response({'error': 'يمكن تعديل التحويلات المعلقة فقط'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        transfer = serializer.save()
        return Response({
            'message': 'تم تحديث طلب التحويل بنجاح',
            'transfer': StockTransferListSerializer(transfer).data,
        })


class StockTransferCancelView(views.APIView):
    """POST: Cancel a stock transfer (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            transfer = StockTransfer.objects.get(pk=pk)
        except StockTransfer.DoesNotExist:
            return Response({'error': 'التحويل غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        if transfer.status in ('completed', 'cancelled'):
            return Response({'error': 'لا يمكن إلغاء تحويل مكتمل أو ملغي'}, status=status.HTTP_400_BAD_REQUEST)
        if transfer.status == 'in_transit':
            # Release reserved stock
            for item in transfer.items.all():
                try:
                    stock = WarehouseStock.objects.get(
                        warehouse=transfer.from_warehouse, product=item.product
                    )
                    stock.reserved_quantity = max(stock.reserved_quantity - item.quantity, 0)
                    stock.save(update_fields=['reserved_quantity', 'updated_at'])
                except WarehouseStock.DoesNotExist:
                    pass
        transfer.status = 'cancelled'
        transfer.approved_by = request.user
        transfer.approved_at = timezone.now()
        transfer.save()
        return Response({
            'message': 'تم إلغاء التحويل بنجاح',
            'transfer': StockTransferListSerializer(transfer).data,
        })


# =============================================
# Stock Adjustment Detail, Update, and Delete
# =============================================

class StockAdjustmentDetailView(generics.RetrieveAPIView):
    """GET: Stock adjustment detail."""

    serializer_class = StockAdjustmentListSerializer

    def get_queryset(self):
        return StockAdjustment.objects.select_related('warehouse', 'product', 'created_by')


class StockAdjustmentUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update notes of a stock adjustment (admin only)."""

    serializer_class = StockAdjustmentCreateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return StockAdjustment.objects.select_related('warehouse', 'product', 'created_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        adj = serializer.save()
        return Response({
            'message': 'تم تحديث التسوية بنجاح',
            'adjustment': StockAdjustmentListSerializer(adj).data,
        })


class StockAdjustmentDeleteView(views.APIView):
    """DELETE: Delete a stock adjustment (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            adj = StockAdjustment.objects.get(pk=pk)
        except StockAdjustment.DoesNotExist:
            return Response({'error': 'التسوية غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
        adj.delete()
        return Response({'message': 'تم حذف التسوية بنجاح'})


# =============================================
# Stock Count Update and Delete
# =============================================

class StockCountUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update stock count notes/status (admin/warehouse only)."""

    serializer_class = StockCountCreateSerializer
    permission_classes = [IsWarehouseOrAdmin]

    def get_queryset(self):
        return StockCount.objects.select_related('warehouse', 'counted_by').prefetch_related('items__product')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.status in ('completed', 'adjusted'):
            return Response({'error': 'لا يمكن تعديل جرد مكتمل'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        count = serializer.save()
        return Response({
            'message': 'تم تحديث الجرد بنجاح',
            'count': StockCountListSerializer(count).data,
        })


class StockCountDeleteView(views.APIView):
    """DELETE: Delete a stock count (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            count = StockCount.objects.get(pk=pk)
        except StockCount.DoesNotExist:
            return Response({'error': 'الجرد غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        if count.status in ('completed', 'adjusted'):
            return Response({'error': 'لا يمكن حذف جرد مكتمل'}, status=status.HTTP_400_BAD_REQUEST)
        count.delete()
        return Response({'message': 'تم حذف الجرد بنجاح'})


# =============================================
# Warehouse Stats View
# =============================================

class WarehouseStatsView(views.APIView):
    """GET: Warehouse statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from decimal import Decimal
        total_stock = WarehouseStock.objects.aggregate(
            total=Coalesce(Sum('quantity'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total']

        stats = {
            'total_warehouses': Warehouse.objects.count(),
            'active_warehouses': Warehouse.objects.filter(is_active=True).count(),
            'total_stock_value': total_stock,
            'total_products_in_stock': WarehouseStock.objects.filter(quantity__gt=0).count(),
            'pending_transfers': StockTransfer.objects.filter(status='pending').count(),
            'in_transit_transfers': StockTransfer.objects.filter(status='in_transit').count(),
            'low_stock_items': WarehouseStock.objects.filter(
                quantity__lte=F('min_stock_level'), min_stock_level__gt=0
            ).count(),
            'completed_counts': StockCount.objects.filter(status__in=('completed', 'adjusted')).count(),
            'pending_adjustments': StockAdjustment.objects.count(),
        }
        serializer = WarehouseStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Excel Export Views
# =============================================

class WarehouseExportView(views.APIView):
    """GET: Export warehouse data to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = Warehouse.objects.prefetch_related('manager')
        columns = [
            ('code', 'رمز المستودع', 15),
            ('name', 'اسم المستودع', 25),
            ('city', 'المدينة', 20),
            ('manager', 'المدير', 25),
            ('capacity', 'السعة', 15),
            ('stock_level', 'المخزون الحالي', 15),
            ('utilized', 'نسبة الاستخدام %', 15),
            ('is_active', 'نشط', 10),
        ]
        data = []
        for wh in queryset:
            data.append({
                'code': wh.code,
                'name': wh.name,
                'city': wh.city or '',
                'manager': wh.manager.full_name if wh.manager else '',
                'capacity': str(wh.capacity),
                'stock_level': str(wh.current_stock_level),
                'utilized': wh.utilized_capacity,
                'is_active': wh.is_active,
            })
        return export_to_excel(data, columns, 'المستودعات', 'warehouses.xlsx')


class StockTransferExportView(views.APIView):
    """GET: Export stock transfers to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = StockTransfer.objects.select_related('from_warehouse', 'to_warehouse', 'requested_by')
        columns = [
            ('transfer_number', 'رقم التحويل', 25),
            ('from_warehouse', 'من مستودع', 20),
            ('to_warehouse', 'إلى مستودع', 20),
            ('status', 'الحالة', 15),
            ('requested_by', 'طلب بواسطة', 20),
            ('approved_at', 'تاريخ الموافقة', 20),
            ('notes', 'ملاحظات', 30),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for trf in queryset:
            data.append({
                'transfer_number': trf.transfer_number,
                'from_warehouse': trf.from_warehouse.name,
                'to_warehouse': trf.to_warehouse.name,
                'status': trf.get_status_display(),
                'requested_by': trf.requested_by.username if trf.requested_by else '',
                'approved_at': str(trf.approved_at) if trf.approved_at else '',
                'notes': trf.notes or '',
                'created_at': str(trf.created_at.strftime('%Y-%m-%d %H:%M')) if trf.created_at else '',
            })
        return export_to_excel(data, columns, 'تحويلات المخزون', 'stock_transfers.xlsx')


class StockAdjustmentExportView(views.APIView):
    """GET: Export stock adjustments to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = StockAdjustment.objects.select_related('warehouse', 'product', 'created_by')
        columns = [
            ('adjustment_number', 'رقم التسوية', 25),
            ('warehouse', 'المستودع', 20),
            ('product', 'المنتج', 25),
            ('reason', 'السبب', 15),
            ('previous_qty', 'الكمية السابقة', 15),
            ('new_qty', 'الكمية الجديدة', 15),
            ('difference', 'الفرق', 15),
            ('created_by', 'بواسطة', 20),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for adj in queryset:
            data.append({
                'adjustment_number': adj.adjustment_number,
                'warehouse': adj.warehouse.name,
                'product': adj.product.name,
                'reason': adj.get_reason_display(),
                'previous_qty': str(adj.previous_quantity),
                'new_qty': str(adj.new_quantity),
                'difference': str(adj.difference),
                'created_by': adj.created_by.username if adj.created_by else '',
                'created_at': str(adj.created_at.strftime('%Y-%m-%d %H:%M')) if adj.created_at else '',
            })
        return export_to_excel(data, columns, 'تسويات المخزون', 'stock_adjustments.xlsx')
