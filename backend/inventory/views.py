"""
API views for product management (CRUD operations).
Implements soft delete and role-based permissions.
"""

from rest_framework import generics, status, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import models
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import Coalesce

from .models import Product
from .serializers import (
    ProductListSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
    ProductDetailSerializer,
    InventoryStatsSerializer,
)
from users.permissions import IsWarehouseOrAdmin
from core.decorators import PermissionRequiredMixin


class ProductListView(PermissionRequiredMixin, generics.ListCreateAPIView):
    """
    GET: List all active products with search and ordering.
    POST: Create a new product (admin/warehouse only).
    """

    permission_module = 'inventory'
    permission_action = {'get': 'view', 'post': 'create'}

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'sku', 'quantity', 'unit_price', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateSerializer
        return ProductListSerializer

    def get_permissions(self):
        """Read access for all authenticated users, write for admin/warehouse."""
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsWarehouseOrAdmin()]

    def get_queryset(self):
        """Return active products, with optional filtering."""
        queryset = Product.objects.select_related()
        # Allow viewing deleted products with query param
        show_deleted = self.request.query_params.get('show_deleted')
        if show_deleted and show_deleted.lower() == 'true':
            queryset = Product.all_objects.all()
        return queryset

    def list(self, request, *args, **kwargs):
        """List products with optional inventory stats."""
        response = super().list(request, *args, **kwargs)

        # Add inventory summary stats
        stats = Product.objects.aggregate(
            total=Count('id'),
            low_stock=Count('id', filter=models.Q(quantity__lte=models.F('reorder_level'))),
            total_value=Coalesce(
                Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
                0,
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )
        response.data['stats'] = {
            'total_products': stats['total'],
            'low_stock_products': stats['low_stock'],
            'total_inventory_value': stats['total_value'],
        }
        return response

    def create(self, request, *args, **kwargs):
        """Create a new product."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(
            {
                'message': 'تم إضافة المنتج بنجاح',
                'product': ProductDetailSerializer(product).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProductDetailView(PermissionRequiredMixin, generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve a single product's details.
    PUT/PATCH: Update product (admin/warehouse only).
    """

    permission_module = 'inventory'
    permission_action = {'get': 'view', 'put': 'edit', 'patch': 'edit'}

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProductUpdateSerializer
        return ProductDetailSerializer

    def get_permissions(self):
        """Read access for all, write for admin/warehouse."""
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsWarehouseOrAdmin()]

    def get_queryset(self):
        """Allow retrieving inactive products by ID."""
        return Product.all_objects.all()

    def update(self, request, *args, **kwargs):
        """Update product data."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response({
            'message': 'تم تحديث المنتج بنجاح',
            'product': ProductDetailSerializer(product).data,
        })


class ProductSoftDeleteView(APIView):
    """
    DELETE: Soft-delete a product (admin/warehouse only).
    The product is marked as inactive, not physically removed.
    """

    permission_classes = [IsWarehouseOrAdmin]

    def delete(self, request, pk):
        """Soft-delete a product by setting is_active=False."""
        try:
            product = Product.all_objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {'error': 'المنتج غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not product.is_active:
            return Response(
                {'error': 'المنتج محذوف بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product.soft_delete()
        return Response({
            'message': 'تم حذف المنتج بنجاح (حذف ناعم)',
        })


class ProductRestoreView(APIView):
    """
    POST: Restore a soft-deleted product (admin only).
    """

    permission_classes = [IsWarehouseOrAdmin]

    def post(self, request, pk):
        """Restore a soft-deleted product."""
        try:
            product = Product.all_objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {'error': 'المنتج غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if product.is_active:
            return Response(
                {'error': 'المنتج نشط بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product.restore()
        return Response({
            'message': 'تم استعادة المنتج بنجاح',
            'product': ProductDetailSerializer(product).data,
        })


class ProductExportView(APIView):
    """GET: Export products to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = Product.objects.filter(is_active=True)
        columns = [
            ('sku', 'الكود', 15),
            ('name', 'اسم المنتج', 30),
            ('description', 'الوصف', 35),
            ('unit_price', 'سعر الوحدة', 15),
            ('quantity', 'الكمية', 12),
            ('reorder_level', 'حد إعادة الطلب', 15),
            ('is_active', 'نشط', 10),
        ]
        data = []
        for p in queryset:
            data.append({
                'sku': p.sku,
                'name': p.name,
                'description': p.description or '',
                'unit_price': str(p.unit_price),
                'quantity': p.quantity,
                'reorder_level': p.reorder_level,
                'is_active': p.is_active,
            })
        return export_to_excel(data, columns, 'المنتجات', 'products.xlsx')


class InventoryStatsView(generics.GenericAPIView):
    """
    GET: Retrieve inventory statistics for the dashboard.
    Available to all authenticated users.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventoryStatsSerializer

    def get(self, request):
        """Return aggregated inventory statistics."""
        stats = Product.objects.aggregate(
            total_products=Count('id'),
            active_products=Count('id', filter=models.Q(is_active=True)),
            low_stock_products=Count(
                'id',
                filter=models.Q(quantity__lte=models.F('reorder_level')),
            ),
            total_inventory_value=Coalesce(
                Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
                0,
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )
        serializer = self.get_serializer(stats)
        return Response(serializer.data)
