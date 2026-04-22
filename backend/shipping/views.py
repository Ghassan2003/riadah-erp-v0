"""
API views for the Shipping module.
Handles ShippingMethods, Shipments, ShipmentItems, ShipmentEvents,
DeliveryAttempts, stats, and export.
"""

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    ShippingMethod,
    Shipment,
    ShipmentItem,
    ShipmentEvent,
    DeliveryAttempt,
)
from .serializers import (
    ShippingMethodListSerializer,
    ShippingMethodCreateSerializer,
    ShippingMethodUpdateSerializer,
    ShippingMethodDetailSerializer,
    ShipmentListSerializer,
    ShipmentCreateSerializer,
    ShipmentUpdateSerializer,
    ShipmentChangeStatusSerializer,
    ShipmentDetailSerializer,
    ShipmentItemSerializer,
    ShipmentItemCreateSerializer,
    ShipmentEventSerializer,
    ShipmentEventCreateSerializer,
    DeliveryAttemptSerializer,
    ShippingStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Shipping Method Views
# =============================================

class ShippingMethodListView(generics.ListCreateAPIView):
    """GET: List shipping methods. POST: Create shipping method (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'carrier']
    ordering_fields = ['name', 'carrier', 'cost_type', 'base_cost', 'estimated_days', 'is_active']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ShippingMethodCreateSerializer
        return ShippingMethodListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ShippingMethod.objects.all()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.save()
        return Response({
            'message': 'تم إنشاء طريقة الشحن بنجاح',
            'method': ShippingMethodDetailSerializer(method).data,
        }, status=status.HTTP_201_CREATED)


class ShippingMethodDetailView(generics.RetrieveUpdateAPIView):
    """GET: Shipping method details. PATCH: Update shipping method (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ShippingMethodUpdateSerializer
        return ShippingMethodDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return ShippingMethod.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        method = serializer.save()
        return Response({
            'message': 'تم تحديث طريقة الشحن بنجاح',
            'method': ShippingMethodDetailSerializer(method).data,
        })


# =============================================
# Shipment Views
# =============================================

class ShipmentListView(generics.ListCreateAPIView):
    """GET: List shipments with filtering. POST: Create shipment (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['shipment_number', 'tracking_number', 'customer__name']
    ordering_fields = ['shipment_number', 'status', 'estimated_delivery', 'shipping_cost', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ShipmentCreateSerializer
        return ShipmentListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Shipment.objects.select_related(
            'customer', 'shipping_method', 'created_by'
        )
        # Filter by status
        shipment_status = self.request.query_params.get('status')
        if shipment_status:
            queryset = queryset.filter(status=shipment_status)
        # Filter by customer
        customer = self.request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(customer_id=customer)
        # Filter by tracking number
        tracking = self.request.query_params.get('tracking')
        if tracking:
            queryset = queryset.filter(tracking_number=tracking)
        # Filter by shipping method
        shipping_method = self.request.query_params.get('shipping_method')
        if shipping_method:
            queryset = queryset.filter(shipping_method_id=shipping_method)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء الشحنة بنجاح',
            'shipment': ShipmentDetailSerializer(shipment).data,
        }, status=status.HTTP_201_CREATED)


class ShipmentDetailView(generics.RetrieveAPIView):
    """GET: Shipment details."""

    def get_serializer_class(self):
        return ShipmentDetailSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Shipment.objects.select_related(
            'customer', 'shipping_method', 'created_by', 'sales_order'
        )


class ShipmentChangeStatusView(views.APIView):
    """POST: Change shipment status (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            shipment = Shipment.objects.select_related('customer', 'shipping_method').get(pk=pk)
        except Shipment.DoesNotExist:
            return Response(
                {'error': 'الشحنة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ShipmentChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')

        # Validate status transition
        valid_transitions = {
            'pending': ['picking', 'cancelled'],
            'picking': ['packed', 'cancelled'],
            'packed': ['in_transit', 'cancelled'],
            'in_transit': ['out_for_delivery', 'returned'],
            'out_for_delivery': ['delivered', 'returned'],
            'delivered': ['returned'],
            'returned': [],
            'cancelled': [],
        }

        allowed = valid_transitions.get(shipment.status, [])
        if new_status not in allowed:
            return Response(
                {'error': f'لا يمكن تغيير الحالة من "{shipment.get_status_display()}" إلى "{dict(Shipment.STATUS_CHOICES).get(new_status, new_status)}"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = shipment.status
        shipment.status = new_status

        # Auto-set actual delivery date
        if new_status == 'delivered':
            shipment.actual_delivery = timezone.now()

        shipment.save()

        # Create event for status change
        ShipmentEvent.objects.create(
            shipment=shipment,
            event_type=new_status,
            description=f'تم تغيير حالة الشحنة من "{shipment.get_status_display()}" إلى "{dict(Shipment.STATUS_CHOICES).get(new_status, new_status)}". {notes}'.strip(),
        )

        return Response({
            'message': 'تم تغيير حالة الشحنة بنجاح',
            'shipment': ShipmentDetailSerializer(shipment).data,
        })


# =============================================
# Shipment Item Views
# =============================================

class ShipmentItemListView(generics.ListCreateAPIView):
    """GET: List shipment items. POST: Create shipment item (admin only)."""

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['product__name', 'quantity', 'unit_price', 'created_at']
    ordering = ['id']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ShipmentItemCreateSerializer
        return ShipmentItemSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ShipmentItem.objects.select_related('shipment', 'product')
        shipment = self.request.query_params.get('shipment')
        if shipment:
            queryset = queryset.filter(shipment_id=shipment)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response({
            'message': 'تم إضافة بند الشحنة بنجاح',
            'item': ShipmentItemSerializer(item).data,
        }, status=status.HTTP_201_CREATED)


class ShipmentItemDetailView(generics.RetrieveAPIView):
    """GET: Shipment item details."""

    serializer_class = ShipmentItemSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return ShipmentItem.objects.select_related('shipment', 'product')


# =============================================
# Shipment Event Views
# =============================================

class ShipmentEventListView(generics.ListAPIView):
    """GET: List shipment events."""

    serializer_class = ShipmentEventSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'event_type']
    ordering = ['-created_at']

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ShipmentEvent.objects.select_related('shipment')
        shipment = self.request.query_params.get('shipment')
        if shipment:
            queryset = queryset.filter(shipment_id=shipment)
        return queryset


class ShipmentEventCreateView(generics.CreateAPIView):
    """POST: Create shipment event (admin only)."""

    serializer_class = ShipmentEventCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response({
            'message': 'تم إضافة حدث الشحنة بنجاح',
            'event': ShipmentEventSerializer(event).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# Delivery Attempt Views
# =============================================

class DeliveryAttemptListView(generics.ListAPIView):
    """GET: List delivery attempts."""

    serializer_class = DeliveryAttemptSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['attempt_date', 'attempt_number', 'status']
    ordering = ['-attempt_date']

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = DeliveryAttempt.objects.select_related('shipment')
        shipment = self.request.query_params.get('shipment')
        if shipment:
            queryset = queryset.filter(shipment_id=shipment)
        return queryset


# =============================================
# Shipping Stats View
# =============================================

class ShippingStatsView(views.APIView):
    """GET: Shipping statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stats = {
            'total_shipments': Shipment.objects.count(),
            'pending_shipments': Shipment.objects.filter(status='pending').count(),
            'in_transit_shipments': Shipment.objects.filter(status='in_transit').count(),
            'delivered_shipments': Shipment.objects.filter(status='delivered').count(),
            'returned_shipments': Shipment.objects.filter(status='returned').count(),
            'total_shipping_methods': ShippingMethod.objects.count(),
            'active_shipping_methods': ShippingMethod.objects.filter(is_active=True).count(),
            'total_shipping_cost': Shipment.objects.aggregate(
                total=Coalesce(
                    Sum('shipping_cost'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_events': ShipmentEvent.objects.count(),
            'total_delivery_attempts': DeliveryAttempt.objects.count(),
            'failed_delivery_attempts': DeliveryAttempt.objects.filter(status='fail').count(),
        }

        serializer = ShippingStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Shipping Export View
# =============================================

class ShippingExportView(views.APIView):
    """GET: Export shipments to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        queryset = Shipment.objects.select_related(
            'customer', 'shipping_method', 'created_by'
        ).order_by('-created_at')

        # Filter by status
        shipment_status = self.request.query_params.get('status')
        if shipment_status:
            queryset = queryset.filter(status=shipment_status)

        columns = [
            ('shipment_number', 'رقم الشحنة', 20),
            ('customer_name', 'العميل', 25),
            ('shipping_method', 'طريقة الشحن', 20),
            ('status', 'الحالة', 15),
            ('tracking_number', 'رقم التتبع', 20),
            ('weight', 'الوزن (كجم)', 12),
            ('shipping_cost', 'تكلفة الشحن', 14),
            ('insurance_amount', 'مبلغ التأمين', 14),
            ('estimated_delivery', 'التوصيل المقدر', 18),
            ('actual_delivery', 'التوصيل الفعلي', 18),
            ('origin_address', 'عنوان المصدر', 30),
            ('destination_address', 'عنوان الوجهة', 30),
            ('notes', 'ملاحظات', 30),
            ('created_at', 'تاريخ الإنشاء', 18),
        ]

        data = []
        for s in queryset:
            data.append({
                'shipment_number': s.shipment_number,
                'customer_name': s.customer.name if s.customer else '',
                'shipping_method': s.shipping_method.name if s.shipping_method else '',
                'status': s.get_status_display(),
                'tracking_number': s.tracking_number,
                'weight': str(s.weight) if s.weight else '',
                'shipping_cost': str(s.shipping_cost),
                'insurance_amount': str(s.insurance_amount),
                'estimated_delivery': str(s.estimated_delivery) if s.estimated_delivery else '',
                'actual_delivery': str(s.actual_delivery) if s.actual_delivery else '',
                'origin_address': s.origin_address,
                'destination_address': s.destination_address,
                'notes': s.notes,
                'created_at': str(s.created_at),
            })

        return export_to_excel(data, columns, 'الشحنات', 'shipping.xlsx')
