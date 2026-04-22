"""
واجهات برمجة التطبيقات لوحدة التصنيع.
تتعامل مع قوائم المواد، أوامر الإنتاج، سجلات الإنتاج، مراكز العمل، خطوات المسارات، الإحصائيات، والتصدير.
"""

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.utils import timezone

from .models import (
    BillOfMaterials,
    BOMItem,
    ProductionOrder,
    ProductionLog,
    WorkCenter,
    RoutingStep,
)
from .serializers import (
    BOMListSerializer,
    BOMCreateSerializer,
    BOMUpdateSerializer,
    BOMDetailSerializer,
    BOMItemSerializer,
    BOMItemCreateSerializer,
    BOMItemUpdateSerializer,
    ProductionOrderListSerializer,
    ProductionOrderCreateSerializer,
    ProductionOrderUpdateSerializer,
    ProductionLogSerializer,
    ProductionLogCreateSerializer,
    WorkCenterSerializer,
    WorkCenterCreateSerializer,
    WorkCenterUpdateSerializer,
    RoutingStepSerializer,
    RoutingStepCreateSerializer,
    RoutingStepUpdateSerializer,
    ManufacturingStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Manufacturing Stats View
# =============================================

class ManufacturingStatsView(views.APIView):
    """GET: إحصائيات لوحة معلومات التصنيع."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stats = {
            'total_boms': BillOfMaterials.objects.count(),
            'active_boms': BillOfMaterials.objects.filter(status='active').count(),
            'total_production_orders': ProductionOrder.objects.count(),
            'orders_in_progress': ProductionOrder.objects.filter(status='in_progress').count(),
            'orders_completed': ProductionOrder.objects.filter(status='completed').count(),
            'orders_draft': ProductionOrder.objects.filter(status='draft').count(),
            'total_work_centers': WorkCenter.objects.count(),
            'active_work_centers': WorkCenter.objects.filter(status='active').count(),
            'work_centers_maintenance': WorkCenter.objects.filter(status='maintenance').count(),
            'total_routing_steps': RoutingStep.objects.count(),
            'total_production_logs': ProductionLog.objects.count(),
        }

        serializer = ManufacturingStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# BillOfMaterials Views
# =============================================

class BOMListView(generics.ListCreateAPIView):
    """GET: عرض قوائم المواد. POST: إنشاء قائمة مواد (المشرفون فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'product__name', 'product__sku']
    ordering_fields = ['name', 'version', 'status', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BOMCreateSerializer
        return BOMListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = BillOfMaterials.objects.select_related('product', 'created_by')
        # تصفية حسب الحالة
        bom_status = self.request.query_params.get('status')
        if bom_status:
            queryset = queryset.filter(status=bom_status)
        # تصفية حسب المنتج
        product = self.request.query_params.get('product')
        if product:
            queryset = queryset.filter(product_id=product)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bom = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء قائمة المواد بنجاح',
            'bom': BOMDetailSerializer(bom).data,
        }, status=status.HTTP_201_CREATED)


class BOMDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: تفاصيل قائمة المواد. PATCH: تحديث قائمة المواد. DELETE: حذف قائمة المواد (المشرفون فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return BOMUpdateSerializer
        if self.request.method == 'DELETE':
            return BOMListSerializer
        return BOMDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return BillOfMaterials.objects.select_related('product', 'created_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        bom = serializer.save()
        return Response({
            'message': 'تم تحديث قائمة المواد بنجاح',
            'bom': BOMDetailSerializer(bom).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'تم حذف قائمة المواد بنجاح'})


# =============================================
# BOMItem Views
# =============================================

class BOMItemListView(generics.ListCreateAPIView):
    """GET: عرض بنود قوائم المواد. POST: إنشاء بند (المشرفون فقط)."""

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['material__name', 'quantity', 'created_at']
    ordering = ['bom', 'id']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BOMItemCreateSerializer
        return BOMItemSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = BOMItem.objects.select_related('bom', 'material')
        # تصفية حسب قائمة المواد
        bom = self.request.query_params.get('bom')
        if bom:
            queryset = queryset.filter(bom_id=bom)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response({
            'message': 'تم إنشاء بند قائمة المواد بنجاح',
            'item': BOMItemSerializer(item).data,
        }, status=status.HTTP_201_CREATED)


class BOMItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: تفاصيل بند قائمة المواد. PATCH: تحديث. DELETE: حذف (المشرفون فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return BOMItemUpdateSerializer
        return BOMItemSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return BOMItem.objects.select_related('bom', 'material')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response({
            'message': 'تم تحديث بند قائمة المواد بنجاح',
            'item': BOMItemSerializer(item).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'تم حذف بند قائمة المواد بنجاح'})


# =============================================
# ProductionOrder Views
# =============================================

class ProductionOrderListView(generics.ListCreateAPIView):
    """GET: عرض أوامر الإنتاج. POST: إنشاء أمر إنتاج (المشرفون فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'product__name', 'product__sku']
    ordering_fields = ['order_number', 'status', 'priority', 'planned_start_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductionOrderCreateSerializer
        return ProductionOrderListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ProductionOrder.objects.select_related('product', 'bom', 'created_by')
        # تصفية حسب الحالة
        order_status = self.request.query_params.get('status')
        if order_status:
            queryset = queryset.filter(status=order_status)
        # تصفية حسب المنتج
        product = self.request.query_params.get('product')
        if product:
            queryset = queryset.filter(product_id=product)
        # تصفية حسب الأولوية
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء أمر الإنتاج بنجاح',
            'order': ProductionOrderListSerializer(order).data,
        }, status=status.HTTP_201_CREATED)


class ProductionOrderDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل أمر الإنتاج. PATCH: تحديث أمر الإنتاج (المشرفون فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProductionOrderUpdateSerializer
        return ProductionOrderListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return ProductionOrder.objects.select_related('product', 'bom', 'created_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response({
            'message': 'تم تحديث أمر الإنتاج بنجاح',
            'order': ProductionOrderListSerializer(order).data,
        })


class ProductionOrderStartView(views.APIView):
    """POST: بدء أمر إنتاج (المشرفون فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            order = ProductionOrder.objects.select_related('product', 'bom').get(pk=pk)
        except ProductionOrder.DoesNotExist:
            return Response(
                {'error': 'أمر الإنتاج غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status not in ('draft', 'planned'):
            return Response(
                {'error': 'لا يمكن بدء أمر إنتاج ليس في حالة مسودة أو مخطط'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = 'in_progress'
        order.actual_start_date = timezone.now().date()
        order.save()

        # إنشاء سجل إنتاج تلقائي
        ProductionLog.objects.create(
            production_order=order,
            operation_type='setup',
            quantity=0,
            notes='تم بدء أمر الإنتاج',
            operator=request.user,
        )

        return Response({
            'message': 'تم بدء أمر الإنتاج بنجاح',
            'order': ProductionOrderListSerializer(order).data,
        })


class ProductionOrderCancelView(views.APIView):
    """POST: إلغاء أمر إنتاج (المشرفون فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            order = ProductionOrder.objects.select_related('product', 'bom').get(pk=pk)
        except ProductionOrder.DoesNotExist:
            return Response(
                {'error': 'أمر الإنتاج غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status not in ('draft', 'planned', 'in_progress'):
            return Response(
                {'error': 'لا يمكن إلغاء أمر إنتاج في هذه الحالة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get('reason', '')
        order.status = 'cancelled'
        order.save()

        # إنشاء سجل إنتاج تلقائي
        ProductionLog.objects.create(
            production_order=order,
            operation_type='setup',
            quantity=0,
            notes=f'تم إلغاء أمر الإنتاج. السبب: {reason}' if reason else 'تم إلغاء أمر الإنتاج',
            operator=request.user,
        )

        return Response({
            'message': 'تم إلغاء أمر الإنتاج بنجاح',
            'order': ProductionOrderListSerializer(order).data,
        })


class ProductionOrderCompleteView(views.APIView):
    """POST: إكمال أمر إنتاج (المشرفون فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            order = ProductionOrder.objects.select_related('product', 'bom').get(pk=pk)
        except ProductionOrder.DoesNotExist:
            return Response(
                {'error': 'أمر الإنتاج غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status != 'in_progress':
            return Response(
                {'error': 'لا يمكن إكمال أمر إنتاج ليس في حالة قيد التنفيذ'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = 'completed'
        order.actual_end_date = timezone.now().date()
        order.save()

        # إنشاء سجل إنتاج تلقائي
        ProductionLog.objects.create(
            production_order=order,
            operation_type='quality_check',
            quantity=order.quantity_produced,
            defect_quantity=order.quantity_defective,
            notes='تم إكمال أمر الإنتاج',
            operator=request.user,
        )

        return Response({
            'message': 'تم إكمال أمر الإنتاج بنجاح',
            'order': ProductionOrderListSerializer(order).data,
        })


# =============================================
# ProductionLog Views
# =============================================

class ProductionLogListView(generics.ListCreateAPIView):
    """GET: عرض سجلات الإنتاج. POST: إنشاء سجل إنتاج (المشرفون فقط)."""

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['log_date', 'operation_type', 'created_at']
    ordering = ['-log_date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductionLogCreateSerializer
        return ProductionLogSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = ProductionLog.objects.select_related('production_order', 'operator')
        # تصفية حسب أمر الإنتاج
        order = self.request.query_params.get('order')
        if order:
            queryset = queryset.filter(production_order_id=order)
        # تصفية حسب نوع العملية
        operation_type = self.request.query_params.get('operation_type')
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        log = serializer.save()
        return Response({
            'message': 'تم إنشاء سجل الإنتاج بنجاح',
            'log': ProductionLogSerializer(log).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# WorkCenter Views
# =============================================

class WorkCenterListView(generics.ListCreateAPIView):
    """GET: عرض مراكز العمل. POST: إنشاء مركز عمل (المشرفون فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location']
    ordering_fields = ['name', 'status', 'capacity', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkCenterCreateSerializer
        return WorkCenterSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = WorkCenter.objects.all()
        # تصفية حسب الحالة
        wc_status = self.request.query_params.get('status')
        if wc_status:
            queryset = queryset.filter(status=wc_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        work_center = serializer.save()
        return Response({
            'message': 'تم إنشاء مركز العمل بنجاح',
            'work_center': WorkCenterSerializer(work_center).data,
        }, status=status.HTTP_201_CREATED)


class WorkCenterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: تفاصيل مركز العمل. PATCH: تحديث. DELETE: حذف (المشرفون فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return WorkCenterUpdateSerializer
        return WorkCenterSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return WorkCenter.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        work_center = serializer.save()
        return Response({
            'message': 'تم تحديث مركز العمل بنجاح',
            'work_center': WorkCenterSerializer(work_center).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'تم حذف مركز العمل بنجاح'})


# =============================================
# RoutingStep Views
# =============================================

class RoutingStepListView(generics.ListCreateAPIView):
    """GET: عرض خطوات مسارات الإنتاج. POST: إنشاء خطوة (المشرفون فقط)."""

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['step_number', 'operation_name', 'estimated_minutes', 'created_at']
    ordering = ['bom', 'step_number']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RoutingStepCreateSerializer
        return RoutingStepSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = RoutingStep.objects.select_related('bom', 'work_center')
        # تصفية حسب قائمة المواد
        bom = self.request.query_params.get('bom')
        if bom:
            queryset = queryset.filter(bom_id=bom)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        step = serializer.save()
        return Response({
            'message': 'تم إنشاء خطوة مسار الإنتاج بنجاح',
            'step': RoutingStepSerializer(step).data,
        }, status=status.HTTP_201_CREATED)


class RoutingStepDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: تفاصيل خطوة مسار. PATCH: تحديث. DELETE: حذف (المشرفون فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return RoutingStepUpdateSerializer
        return RoutingStepSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return RoutingStep.objects.select_related('bom', 'work_center')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        step = serializer.save()
        return Response({
            'message': 'تم تحديث خطوة مسار الإنتاج بنجاح',
            'step': RoutingStepSerializer(step).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'تم حذف خطوة مسار الإنتاج بنجاح'})


# =============================================
# Manufacturing Export View
# =============================================

class ManufacturingExportView(views.APIView):
    """GET: تصدير بيانات التصنيع إلى ملف Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        export_type = request.query_params.get('type', 'orders')

        if export_type == 'orders':
            queryset = ProductionOrder.objects.select_related(
                'product', 'bom', 'created_by'
            ).order_by('-created_at')

            columns = [
                ('order_number', 'رقم الأمر', 20),
                ('product_name', 'المنتج', 30),
                ('bom_name', 'قائمة المواد', 25),
                ('quantity', 'الكمية المطلوبة', 15),
                ('quantity_produced', 'الكمية المنتجة', 15),
                ('quantity_defective', 'الكمية المعيبة', 15),
                ('status', 'الحالة', 15),
                ('priority', 'الأولوية', 12),
                ('planned_start_date', 'تاريخ البدء المخطط', 18),
                ('planned_end_date', 'تاريخ الانتهاء المخطط', 18),
                ('actual_start_date', 'تاريخ البدء الفعلي', 18),
                ('actual_end_date', 'تاريخ الانتهاء الفعلي', 18),
            ]
            data = []
            for o in queryset:
                data.append({
                    'order_number': o.order_number,
                    'product_name': o.product.name if o.product else '',
                    'bom_name': o.bom.name if o.bom else '',
                    'quantity': str(o.quantity),
                    'quantity_produced': str(o.quantity_produced),
                    'quantity_defective': str(o.quantity_defective),
                    'status': o.get_status_display(),
                    'priority': o.get_priority_display(),
                    'planned_start_date': str(o.planned_start_date),
                    'planned_end_date': str(o.planned_end_date),
                    'actual_start_date': str(o.actual_start_date) if o.actual_start_date else '',
                    'actual_end_date': str(o.actual_end_date) if o.actual_end_date else '',
                })
            return export_to_excel(data, columns, 'أوامر الإنتاج', 'production_orders.xlsx')

        elif export_type == 'boms':
            queryset = BillOfMaterials.objects.select_related('product').order_by('-created_at')

            columns = [
                ('name', 'الاسم', 30),
                ('product_name', 'المنتج', 30),
                ('version', 'الإصدار', 10),
                ('status', 'الحالة', 15),
                ('effective_date', 'تاريخ السريان', 15),
                ('items_count', 'عدد البنود', 12),
            ]
            data = []
            for b in queryset:
                data.append({
                    'name': b.name,
                    'product_name': b.product.name if b.product else '',
                    'version': str(b.version),
                    'status': b.get_status_display(),
                    'effective_date': str(b.effective_date) if b.effective_date else '',
                    'items_count': str(b.items.count()),
                })
            return export_to_excel(data, columns, 'قوائم المواد', 'bills_of_materials.xlsx')

        elif export_type == 'logs':
            queryset = ProductionLog.objects.select_related(
                'production_order', 'operator'
            ).order_by('-log_date')

            columns = [
                ('order_number', 'رقم الأمر', 20),
                ('operation_type', 'نوع العملية', 15),
                ('quantity', 'الكمية', 12),
                ('defect_quantity', 'كمية المعيوبات', 15),
                ('operator_name', 'المشغل', 20),
                ('log_date', 'التاريخ', 20),
                ('notes', 'ملاحظات', 30),
            ]
            data = []
            for l in queryset:
                data.append({
                    'order_number': l.production_order.order_number if l.production_order else '',
                    'operation_type': l.get_operation_type_display(),
                    'quantity': str(l.quantity),
                    'defect_quantity': str(l.defect_quantity),
                    'operator_name': l.operator.username if l.operator else '',
                    'log_date': str(l.log_date),
                    'notes': l.notes,
                })
            return export_to_excel(data, columns, 'سجلات الإنتاج', 'production_logs.xlsx')

        else:
            return Response(
                {'error': 'نوع التصدير غير صالح. الاختيارات: orders, boms, logs'},
                status=status.HTTP_400_BAD_REQUEST,
            )
