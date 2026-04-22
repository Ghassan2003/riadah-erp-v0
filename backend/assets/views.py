"""
API views for the Assets module.
Handles asset categories, fixed assets, transfers, maintenance, disposals, and depreciation.
"""

from rest_framework import (
    generics, status, permissions, filters, views
)
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

from .models import (
    AssetCategory, FixedAsset, AssetTransfer, AssetMaintenance, AssetDisposal,
)
from .serializers import (
    AssetCategoryListSerializer, AssetCategoryCreateSerializer, AssetCategoryUpdateSerializer,
    FixedAssetListSerializer, FixedAssetCreateSerializer, FixedAssetUpdateSerializer, FixedAssetDetailSerializer,
    AssetTransferListSerializer, AssetTransferCreateSerializer,
    AssetMaintenanceListSerializer, AssetMaintenanceCreateSerializer, AssetMaintenanceUpdateSerializer,
    AssetDisposalListSerializer, AssetDisposalCreateSerializer,
    AssetDepreciationSerializer, AssetStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# AssetCategory Views
# =============================================

class AssetCategoryListView(generics.ListCreateAPIView):
    """GET: List asset categories. POST: Create category (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_en']
    ordering_fields = ['name', 'useful_life_years', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssetCategoryCreateSerializer
        return AssetCategoryListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return AssetCategory.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cat = serializer.save()
        return Response({
            'message': 'تم إنشاء تصنيف الأصل بنجاح',
            'category': AssetCategoryListSerializer(cat).data,
        }, status=status.HTTP_201_CREATED)


class AssetCategoryDetailView(generics.RetrieveUpdateAPIView):
    """GET: Category details. PATCH: Update category (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return AssetCategoryUpdateSerializer
        return AssetCategoryListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return AssetCategory.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        cat = serializer.save()
        return Response({
            'message': 'تم تحديث تصنيف الأصل بنجاح',
            'category': AssetCategoryListSerializer(cat).data,
        })


class AssetCategoryDeleteView(views.APIView):
    """DELETE: Soft-delete an asset category (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            cat = AssetCategory.objects.get(pk=pk)
        except AssetCategory.DoesNotExist:
            return Response({'error': 'تصنيف الأصل غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        cat.is_active = False
        cat.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم حذف تصنيف الأصل بنجاح'})


# =============================================
# FixedAsset Views
# =============================================

class FixedAssetListView(generics.ListCreateAPIView):
    """GET: List fixed assets. POST: Create asset (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_en', 'asset_number', 'serial_number', 'barcode']
    ordering_fields = ['name', 'asset_number', 'purchase_date', 'purchase_price', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FixedAssetCreateSerializer
        return FixedAssetListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = FixedAsset.objects.select_related('category', 'department', 'assigned_to')
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        asset_status = self.request.query_params.get('status')
        if asset_status:
            queryset = queryset.filter(status=asset_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إضافة الأصل الثابت بنجاح',
            'asset': FixedAssetDetailSerializer(asset).data,
        }, status=status.HTTP_201_CREATED)


class FixedAssetDetailView(generics.RetrieveUpdateAPIView):
    """GET: Asset details. PATCH: Update asset (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return FixedAssetUpdateSerializer
        return FixedAssetDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return FixedAsset.objects.select_related('category', 'department', 'assigned_to', 'supplier')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        asset = serializer.save()
        return Response({
            'message': 'تم تحديث بيانات الأصل بنجاح',
            'asset': FixedAssetDetailSerializer(asset).data,
        })


class FixedAssetDeleteView(views.APIView):
    """DELETE: Soft-delete a fixed asset (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            asset = FixedAsset.objects.get(pk=pk)
        except FixedAsset.DoesNotExist:
            return Response({'error': 'الأصل غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        asset.is_active = False
        asset.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم حذف الأصل بنجاح'})


class FixedAssetRestoreView(views.APIView):
    """POST: Restore a soft-deleted fixed asset (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            asset = FixedAsset.objects.get(pk=pk)
        except FixedAsset.DoesNotExist:
            return Response({'error': 'الأصل غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        asset.is_active = True
        asset.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم إعادة تفعيل الأصل بنجاح'})


# =============================================
# AssetTransfer Views
# =============================================

class AssetTransferListView(generics.ListAPIView):
    """GET: List asset transfers with filtering."""

    serializer_class = AssetTransferListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['transfer_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = AssetTransfer.objects.select_related(
            'asset', 'from_department', 'to_department',
            'from_employee', 'to_employee', 'approved_by'
        )
        asset = self.request.query_params.get('asset')
        if asset:
            queryset = queryset.filter(asset_id=asset)
        return queryset


class AssetTransferCreateView(generics.CreateAPIView):
    """POST: Create an asset transfer (admin only)."""

    serializer_class = AssetTransferCreateSerializer
    permission_classes = [IsAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transfer = serializer.save()

        # Update the asset's current location, department, and assignment
        asset = transfer.asset
        if transfer.to_department:
            asset.department = transfer.to_department
        if transfer.to_employee:
            asset.assigned_to = transfer.to_employee
        if transfer.to_location:
            asset.location = transfer.to_location
        asset.save(update_fields=['department', 'assigned_to', 'location', 'updated_at'])

        return Response({
            'message': 'تم نقل الأصل بنجاح',
            'transfer': AssetTransferListSerializer(transfer).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# AssetMaintenance Views
# =============================================

class AssetMaintenanceListView(generics.ListAPIView):
    """GET: List maintenance records with filtering."""

    serializer_class = AssetMaintenanceListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'vendor', 'asset__name']
    ordering_fields = ['maintenance_date', 'status', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = AssetMaintenance.objects.select_related('asset')
        asset = self.request.query_params.get('asset')
        if asset:
            queryset = queryset.filter(asset_id=asset)
        maint_status = self.request.query_params.get('status')
        if maint_status:
            queryset = queryset.filter(status=maint_status)
        return queryset


class AssetMaintenanceCreateView(generics.CreateAPIView):
    """POST: Create a maintenance record (admin only)."""

    serializer_class = AssetMaintenanceCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        maint = serializer.save()
        return Response({
            'message': 'تم إنشاء سجل الصيانة بنجاح',
            'maintenance': AssetMaintenanceListSerializer(maint).data,
        }, status=status.HTTP_201_CREATED)


class AssetMaintenanceUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a maintenance record (admin only)."""

    serializer_class = AssetMaintenanceUpdateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return AssetMaintenance.objects.select_related('asset')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        maint = serializer.save()
        return Response({
            'message': 'تم تحديث سجل الصيانة بنجاح',
            'maintenance': AssetMaintenanceListSerializer(maint).data,
        })


# =============================================
# AssetDisposal Views
# =============================================

class AssetDisposalListView(generics.ListAPIView):
    """GET: List asset disposals."""

    serializer_class = AssetDisposalListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['notes', 'buyer_name', 'asset__name']
    ordering_fields = ['disposal_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = AssetDisposal.objects.select_related('asset', 'approved_by')
        disposal_type = self.request.query_params.get('disposal_type')
        if disposal_type:
            queryset = queryset.filter(disposal_type=disposal_type)
        return queryset


class AssetDisposalCreateView(generics.CreateAPIView):
    """POST: Create an asset disposal (admin only). Updates asset status."""

    serializer_class = AssetDisposalCreateSerializer
    permission_classes = [IsAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        disposal = serializer.save(approved_by=request.user)

        # Update asset status
        asset = disposal.asset
        if disposal.disposal_type == 'sold':
            asset.status = 'sold'
        else:
            asset.status = 'disposed'
        asset.is_active = False
        asset.save(update_fields=['status', 'is_active', 'updated_at'])

        return Response({
            'message': 'تم تخريد الأصل بنجاح',
            'disposal': AssetDisposalListSerializer(disposal).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# AssetTransfer Detail, Update, Delete
# =============================================

class AssetTransferDetailView(generics.RetrieveAPIView):
    """GET: Asset transfer detail."""

    serializer_class = AssetTransferListSerializer

    def get_queryset(self):
        return AssetTransfer.objects.select_related(
            'asset', 'from_department', 'to_department',
            'from_employee', 'to_employee', 'approved_by'
        )


class AssetTransferUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update an asset transfer (admin only)."""

    serializer_class = AssetTransferCreateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return AssetTransfer.objects.select_related(
            'asset', 'from_department', 'to_department',
            'from_employee', 'to_employee', 'approved_by'
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        transfer = serializer.save()
        return Response({
            'message': 'تم تحديث بيانات النقل بنجاح',
            'transfer': AssetTransferListSerializer(transfer).data,
        })


class AssetTransferDeleteView(views.APIView):
    """DELETE: Delete an asset transfer (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            transfer = AssetTransfer.objects.get(pk=pk)
        except AssetTransfer.DoesNotExist:
            return Response({'error': 'سجل النقل غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        transfer.delete()
        return Response({'message': 'تم حذف سجل النقل بنجاح'})


# =============================================
# AssetMaintenance Detail and Delete
# =============================================

class AssetMaintenanceDetailView(generics.RetrieveAPIView):
    """GET: Maintenance record detail."""

    serializer_class = AssetMaintenanceListSerializer

    def get_queryset(self):
        return AssetMaintenance.objects.select_related('asset')


class AssetMaintenanceDeleteView(views.APIView):
    """DELETE: Delete a maintenance record (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            maint = AssetMaintenance.objects.get(pk=pk)
        except AssetMaintenance.DoesNotExist:
            return Response({'error': 'سجل الصيانة غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        maint.delete()
        return Response({'message': 'تم حذف سجل الصيانة بنجاح'})


# =============================================
# AssetDisposal Detail, Update, Delete
# =============================================

class AssetDisposalDetailView(generics.RetrieveAPIView):
    """GET: Asset disposal detail."""

    serializer_class = AssetDisposalListSerializer

    def get_queryset(self):
        return AssetDisposal.objects.select_related('asset', 'approved_by')


class AssetDisposalUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update an asset disposal (admin only)."""

    serializer_class = AssetDisposalCreateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return AssetDisposal.objects.select_related('asset', 'approved_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        disposal = serializer.save()
        return Response({
            'message': 'تم تحديث بيانات التخريد بنجاح',
            'disposal': AssetDisposalListSerializer(disposal).data,
        })


class AssetDisposalDeleteView(views.APIView):
    """DELETE: Delete an asset disposal (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            disposal = AssetDisposal.objects.get(pk=pk)
        except AssetDisposal.DoesNotExist:
            return Response({'error': 'سجل التخريد غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        disposal.delete()
        return Response({'message': 'تم حذف سجل التخريد بنجاح'})


# =============================================
# Asset Depreciation View
# =============================================

class AssetDepreciationView(views.APIView):
    """POST: Calculate and record monthly depreciation for assets."""

    permission_classes = [IsAdmin]

    @transaction.atomic
    def post(self, request):
        serializer = AssetDepreciationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        asset_ids = serializer.validated_data.get('asset_ids', [])
        today = timezone.now().date()

        if asset_ids:
            queryset = FixedAsset.objects.filter(id__in=asset_ids)
        else:
            queryset = FixedAsset.objects.filter(
                is_active=True, status='active'
            )

        depreciated = []
        skipped = []

        for asset in queryset:
            if asset.current_value <= asset.salvage_value:
                skipped.append({'asset': asset.asset_number, 'reason': 'وصلت إلى القيمة التخريدية'})
                continue

            monthly_dep = asset.calculate_depreciation()
            if monthly_dep <= 0:
                skipped.append({'asset': asset.asset_number, 'reason': 'قيمة الإهلاك صفر'})
                continue

            # Ensure accumulated depreciation doesn't exceed depreciable amount
            max_dep = asset.purchase_price - asset.salvage_value
            new_accumulated = asset.accumulated_depreciation + monthly_dep
            if new_accumulated > max_dep:
                monthly_dep = max_dep - asset.accumulated_depreciation
                if monthly_dep <= 0:
                    skipped.append({'asset': asset.asset_number, 'reason': 'مجمع الإهلاك وصل للحد الأقصى'})
                    continue
                new_accumulated = max_dep

            asset.accumulated_depreciation = new_accumulated
            asset.save(update_fields=['accumulated_depreciation', 'updated_at'])

            depreciated.append({
                'asset': asset.asset_number,
                'name': asset.name,
                'monthly_depreciation': str(monthly_dep),
                'new_accumulated': str(new_accumulated),
                'current_value': str(asset.current_value),
            })

        return Response({
            'message': f'تم احتساب الإهلاك لـ {len(depreciated)} أصل',
            'depreciated': depreciated,
            'skipped': skipped,
        })


# =============================================
# Asset Stats View
# =============================================

class AssetStatsView(views.APIView):
    """GET: Asset statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from decimal import Decimal
        today = timezone.now().date()
        thirty_days = today + timedelta(days=30)

        stats = {
            'total_assets': FixedAsset.objects.count(),
            'active_assets': FixedAsset.objects.filter(is_active=True, status='active').count(),
            'total_purchase_value': FixedAsset.objects.aggregate(
                total=Coalesce(Sum('purchase_price'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'total_accumulated_depreciation': FixedAsset.objects.aggregate(
                total=Coalesce(Sum('accumulated_depreciation'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'assets_in_maintenance': FixedAsset.objects.filter(status='in_maintenance').count(),
            'disposed_assets': FixedAsset.objects.filter(status__in=('disposed', 'sold')).count(),
            'expiring_warranties': FixedAsset.objects.filter(
                warranty_end_date__lte=thirty_days,
                warranty_end_date__gte=today,
            ).count(),
            'total_maintenance_cost': AssetMaintenance.objects.aggregate(
                total=Coalesce(Sum('cost'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
        }

        # Calculate total current value
        total_purchase = stats['total_purchase_value']
        total_dep = stats['total_accumulated_depreciation']
        stats['total_current_value'] = max(total_purchase - total_dep, Decimal('0.00'))

        serializer = AssetStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Excel Export View
# =============================================

class AssetExportView(views.APIView):
    """GET: Export fixed assets to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = FixedAsset.objects.select_related('category', 'department', 'assigned_to')
        columns = [
            ('asset_number', 'رقم الأصل', 22),
            ('name', 'اسم الأصل', 25),
            ('category', 'التصنيف', 20),
            ('serial_number', 'الرقم التسلسلي', 20),
            ('department', 'القسم', 20),
            ('assigned_to', 'مسند إلى', 25),
            ('purchase_date', 'تاريخ الشراء', 15),
            ('purchase_price', 'سعر الشراء', 15),
            ('accumulated_dep', 'مجمع الإهلاك', 15),
            ('current_value', 'القيمة الدفترية', 15),
            ('status', 'الحالة', 15),
            ('location', 'الموقع', 20),
        ]
        data = []
        for a in queryset:
            data.append({
                'asset_number': a.asset_number,
                'name': a.name,
                'category': a.category.name if a.category else '',
                'serial_number': a.serial_number or '',
                'department': a.department.name if a.department else '',
                'assigned_to': a.assigned_to.full_name if a.assigned_to else '',
                'purchase_date': str(a.purchase_date) if a.purchase_date else '',
                'purchase_price': str(a.purchase_price),
                'accumulated_dep': str(a.accumulated_depreciation),
                'current_value': str(a.current_value),
                'status': a.get_status_display(),
                'location': a.location or '',
            })
        return export_to_excel(data, columns, 'الأصول الثابتة', 'fixed_assets.xlsx')
