"""
API views for the Equipment Maintenance module.
Handles Equipment, MaintenanceSchedule, MaintenanceWorkOrder, MaintenancePart,
EquipmentInspection, stats, and export.
"""

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import HttpResponse

from .models import (
    Equipment,
    MaintenanceSchedule,
    MaintenanceWorkOrder,
    MaintenancePart,
    EquipmentInspection,
)
from .serializers import (
    EquipmentListSerializer,
    EquipmentCreateSerializer,
    EquipmentDetailSerializer,
    MaintenanceScheduleListSerializer,
    MaintenanceScheduleDetailSerializer,
    MaintenanceWorkOrderListSerializer,
    MaintenanceWorkOrderCreateSerializer,
    MaintenanceWorkOrderApproveSerializer,
    MaintenanceWorkOrderCompleteSerializer,
    MaintenancePartListSerializer,
    MaintenancePartCreateSerializer,
    MaintenancePartDetailSerializer,
    EquipmentInspectionListSerializer,
    EquipmentInspectionCreateSerializer,
    EquipmentMaintStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Equipment Maintenance Stats View
# =============================================

class EquipmentMaintStatsView(views.APIView):
    """GET: Equipment maintenance statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.now()

        stats = {
            'total_equipment': Equipment.objects.count(),
            'operational_equipment': Equipment.objects.filter(status='operational').count(),
            'maintenance_equipment': Equipment.objects.filter(status='maintenance').count(),
            'broken_equipment': Equipment.objects.filter(status='broken').count(),
            'retired_equipment': Equipment.objects.filter(status='retired').count(),
            'total_work_orders': MaintenanceWorkOrder.objects.count(),
            'pending_work_orders': MaintenanceWorkOrder.objects.filter(status='requested').count(),
            'in_progress_work_orders': MaintenanceWorkOrder.objects.filter(status='in_progress').count(),
            'completed_work_orders': MaintenanceWorkOrder.objects.filter(status='completed').count(),
            'active_schedules': MaintenanceSchedule.objects.filter(is_active=True).count(),
            'overdue_schedules': MaintenanceSchedule.objects.filter(
                is_active=True, next_due__lt=now.date()
            ).count(),
            'total_inspections': EquipmentInspection.objects.count(),
            'passed_inspections': EquipmentInspection.objects.filter(status='pass').count(),
            'failed_inspections': EquipmentInspection.objects.filter(status='fail').count(),
            'total_maintenance_cost': MaintenanceWorkOrder.objects.filter(
                status='completed'
            ).aggregate(
                total=Coalesce(
                    Sum('actual_cost'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'pending_work_orders_cost': MaintenanceWorkOrder.objects.filter(
                status__in=('requested', 'approved', 'in_progress')
            ).aggregate(
                total=Coalesce(
                    Sum('estimated_cost'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
        }

        serializer = EquipmentMaintStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Equipment Views
# =============================================

class EquipmentListView(generics.ListCreateAPIView):
    """GET: List equipment. POST: Create equipment (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'equipment_number', 'brand', 'model_number', 'serial_number']
    ordering_fields = ['name', 'equipment_number', 'category', 'status', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EquipmentCreateSerializer
        return EquipmentListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Equipment.objects.select_related('assigned_department', 'assigned_to')
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        # Filter by status
        equip_status = self.request.query_params.get('status')
        if equip_status:
            queryset = queryset.filter(status=equip_status)
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(assigned_department_id=department)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        equipment = serializer.save()
        return Response({
            'message': 'تم إنشاء المعدة بنجاح',
            'equipment': EquipmentDetailSerializer(equipment).data,
        }, status=status.HTTP_201_CREATED)


class EquipmentDetailView(generics.RetrieveAPIView):
    """GET: Equipment details."""

    serializer_class = EquipmentDetailSerializer

    def get_queryset(self):
        return Equipment.objects.select_related('assigned_department', 'assigned_to')


class EquipmentCreateView(generics.CreateAPIView):
    """POST: Create equipment (admin only)."""

    serializer_class = EquipmentCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        equipment = serializer.save()
        return Response({
            'message': 'تم إنشاء المعدة بنجاح',
            'equipment': EquipmentDetailSerializer(equipment).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# Maintenance Schedule Views
# =============================================

class MaintenanceScheduleListView(generics.ListAPIView):
    """GET: List maintenance schedules with filtering."""

    serializer_class = MaintenanceScheduleListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['equipment__name', 'equipment__equipment_number']
    ordering_fields = ['next_due', 'priority', 'maintenance_type', 'created_at']
    ordering = ['next_due']

    def get_queryset(self):
        queryset = MaintenanceSchedule.objects.select_related(
            'equipment', 'assigned_to'
        )
        # Filter by equipment
        equipment = self.request.query_params.get('equipment')
        if equipment:
            queryset = queryset.filter(equipment_id=equipment)
        # Filter by maintenance type
        maint_type = self.request.query_params.get('maintenance_type')
        if maint_type:
            queryset = queryset.filter(maintenance_type=maint_type)
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        # Filter by is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        # Filter overdue
        overdue = self.request.query_params.get('overdue')
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(is_active=True, next_due__lt=timezone.now().date())
        return queryset


class MaintenanceScheduleDetailView(generics.RetrieveAPIView):
    """GET: Maintenance schedule details."""

    serializer_class = MaintenanceScheduleDetailSerializer

    def get_queryset(self):
        return MaintenanceSchedule.objects.select_related('equipment', 'assigned_to')


# =============================================
# Maintenance Work Order Views
# =============================================

class WorkOrderListView(generics.ListCreateAPIView):
    """GET: List work orders with filtering. POST: Create work order (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'work_order_number', 'equipment__name', 'equipment__equipment_number',
        'description',
    ]
    ordering_fields = [
        'work_order_number', 'status', 'priority', 'work_type', 'created_at',
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MaintenanceWorkOrderCreateSerializer
        return MaintenanceWorkOrderListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = MaintenanceWorkOrder.objects.select_related(
            'equipment', 'schedule', 'requested_by', 'assigned_to', 'approved_by'
        )
        # Filter by status
        wo_status = self.request.query_params.get('status')
        if wo_status:
            queryset = queryset.filter(status=wo_status)
        # Filter by equipment
        equipment = self.request.query_params.get('equipment')
        if equipment:
            queryset = queryset.filter(equipment_id=equipment)
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        # Filter by work_type
        work_type = self.request.query_params.get('work_type')
        if work_type:
            queryset = queryset.filter(work_type=work_type)
        return queryset

    def create(self, request, *args, **kwargs):
        from datetime import date
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Auto-generate work order number
        last_wo = MaintenanceWorkOrder.objects.order_by('-id').first()
        next_num = (last_wo.id + 1) if last_wo else 1
        wo_number = f'WO-{date.today().strftime("%Y%m%d")}-{next_num:04d}'
        work_order = serializer.save(
            work_order_number=wo_number,
            requested_by=request.user,
        )
        return Response({
            'message': 'تم إنشاء أمر عمل الصيانة بنجاح',
            'work_order': MaintenanceWorkOrderListSerializer(work_order).data,
        }, status=status.HTTP_201_CREATED)


class WorkOrderDetailView(generics.RetrieveAPIView):
    """GET: Work order details."""

    serializer_class = MaintenanceWorkOrderListSerializer

    def get_queryset(self):
        return MaintenanceWorkOrder.objects.select_related(
            'equipment', 'schedule', 'requested_by', 'assigned_to', 'approved_by'
        )


class WorkOrderCreateView(generics.CreateAPIView):
    """POST: Create work order (admin only)."""

    serializer_class = MaintenanceWorkOrderCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        from datetime import date
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        last_wo = MaintenanceWorkOrder.objects.order_by('-id').first()
        next_num = (last_wo.id + 1) if last_wo else 1
        wo_number = f'WO-{date.today().strftime("%Y%m%d")}-{next_num:04d}'
        work_order = serializer.save(
            work_order_number=wo_number,
            requested_by=request.user,
        )
        return Response({
            'message': 'تم إنشاء أمر عمل الصيانة بنجاح',
            'work_order': MaintenanceWorkOrderListSerializer(work_order).data,
        }, status=status.HTTP_201_CREATED)


class WorkOrderApproveView(views.APIView):
    """POST: Approve a work order (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            work_order = MaintenanceWorkOrder.objects.select_related(
                'equipment', 'requested_by'
            ).get(pk=pk)
        except MaintenanceWorkOrder.DoesNotExist:
            return Response(
                {'error': 'أمر العمل غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if work_order.status != 'requested':
            return Response(
                {'error': 'يمكن الموافقة فقط على أوامر العمل المطلوبة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MaintenanceWorkOrderApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        work_order.status = 'approved'
        work_order.approved_by = request.user
        assigned_to_id = serializer.validated_data.get('assigned_to')
        if assigned_to_id:
            from users.models import User
            try:
                work_order.assigned_to = User.objects.get(pk=assigned_to_id)
            except User.DoesNotExist:
                pass
        work_order.save()

        return Response({
            'message': 'تمت الموافقة على أمر عمل الصيانة',
            'work_order': MaintenanceWorkOrderListSerializer(work_order).data,
        })


class WorkOrderStartView(views.APIView):
    """POST: Start a work order (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            work_order = MaintenanceWorkOrder.objects.select_related(
                'equipment'
            ).get(pk=pk)
        except MaintenanceWorkOrder.DoesNotExist:
            return Response(
                {'error': 'أمر العمل غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if work_order.status != 'approved':
            return Response(
                {'error': 'يمكن بدء أوامر العمل الموافق عليها فقط'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        work_order.status = 'in_progress'
        work_order.started_at = timezone.now()
        work_order.save()

        return Response({
            'message': 'تم بدء أمر عمل الصيانة',
            'work_order': MaintenanceWorkOrderListSerializer(work_order).data,
        })


class WorkOrderCompleteView(views.APIView):
    """POST: Complete a work order (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            work_order = MaintenanceWorkOrder.objects.select_related(
                'equipment'
            ).get(pk=pk)
        except MaintenanceWorkOrder.DoesNotExist:
            return Response(
                {'error': 'أمر العمل غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if work_order.status != 'in_progress':
            return Response(
                {'error': 'يمكن إكمال أوامر العمل قيد التنفيذ فقط'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MaintenanceWorkOrderCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        work_order.status = 'completed'
        work_order.completed_at = timezone.now()
        work_order.actual_cost = serializer.validated_data.get('actual_cost', work_order.actual_cost)
        work_order.actual_hours = serializer.validated_data.get('actual_hours', work_order.actual_hours)
        work_order.completion_notes = serializer.validated_data.get('completion_notes', '')

        # Sum parts cost
        parts_total = work_order.parts.aggregate(
            total=Coalesce(
                Sum(F('quantity') * F('unit_cost')),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total']
        work_order.actual_cost = work_order.actual_cost + parts_total
        work_order.save()

        return Response({
            'message': 'تم إكمال أمر عمل الصيانة بنجاح',
            'work_order': MaintenanceWorkOrderListSerializer(work_order).data,
        })


# =============================================
# Maintenance Part Views
# =============================================

class MaintenancePartListView(generics.ListCreateAPIView):
    """GET: List maintenance parts. POST: Create maintenance part (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['part_name', 'part_number']
    ordering_fields = ['part_name', 'quantity', 'unit_cost', 'created_at']
    ordering = ['part_name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MaintenancePartCreateSerializer
        return MaintenancePartListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = MaintenancePart.objects.select_related('work_order', 'supplier')
        # Filter by work_order
        work_order = self.request.query_params.get('work_order')
        if work_order:
            queryset = queryset.filter(work_order_id=work_order)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        part = serializer.save()
        return Response({
            'message': 'تم إنشاء قطعة الغيار بنجاح',
            'part': MaintenancePartDetailSerializer(part).data,
        }, status=status.HTTP_201_CREATED)


class MaintenancePartDetailView(generics.RetrieveAPIView):
    """GET: Maintenance part details."""

    serializer_class = MaintenancePartDetailSerializer

    def get_queryset(self):
        return MaintenancePart.objects.select_related('work_order', 'supplier')


# =============================================
# Equipment Inspection Views
# =============================================

class EquipmentInspectionListView(generics.ListAPIView):
    """GET: List equipment inspections with filtering."""

    serializer_class = EquipmentInspectionListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['equipment__name', 'equipment__equipment_number', 'findings']
    ordering_fields = ['inspection_date', 'condition_rating', 'status', 'inspection_type']
    ordering = ['-inspection_date']

    def get_queryset(self):
        queryset = EquipmentInspection.objects.select_related('equipment', 'inspector')
        # Filter by equipment
        equipment = self.request.query_params.get('equipment')
        if equipment:
            queryset = queryset.filter(equipment_id=equipment)
        # Filter by inspection type
        inspection_type = self.request.query_params.get('inspection_type')
        if inspection_type:
            queryset = queryset.filter(inspection_type=inspection_type)
        # Filter by status
        insp_status = self.request.query_params.get('status')
        if insp_status:
            queryset = queryset.filter(status=insp_status)
        # Filter by condition rating
        condition_rating = self.request.query_params.get('condition_rating')
        if condition_rating:
            queryset = queryset.filter(condition_rating=condition_rating)
        return queryset


class EquipmentInspectionCreateView(generics.CreateAPIView):
    """POST: Create equipment inspection (admin only)."""

    serializer_class = EquipmentInspectionCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inspection = serializer.save(inspector=request.user)
        return Response({
            'message': 'تم إنشاء فحص المعدة بنجاح',
            'inspection': EquipmentInspectionListSerializer(inspection).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# Equipment Maintenance Export View
# =============================================

class EquipmentMaintExportView(views.APIView):
    """GET: Export equipment maintenance data to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        export_type = request.query_params.get('type', 'equipment')

        if export_type == 'work_orders':
            return self._export_work_orders(request)
        elif export_type == 'inspections':
            return self._export_inspections(request)
        else:
            return self._export_equipment(request)

    def _export_equipment(self, request):
        from core.utils import export_to_excel

        queryset = Equipment.objects.select_related('assigned_department').order_by('name')

        columns = [
            ('equipment_number', 'رقم المعدة', 15),
            ('name', 'اسم المعدة', 30),
            ('category', 'التصنيف', 15),
            ('brand', 'العلامة التجارية', 20),
            ('model_number', 'رقم الموديل', 20),
            ('serial_number', 'الرقم التسلسلي', 20),
            ('location', 'الموقع', 25),
            ('department', 'القسم', 20),
            ('purchase_date', 'تاريخ الشراء', 15),
            ('purchase_cost', 'تكلفة الشراء', 15),
            ('warranty_end', 'انتهاء الضمان', 15),
            ('status', 'الحالة', 12),
            ('meter_reading', 'قراءة العداد', 15),
            ('notes', 'ملاحظات', 30),
        ]

        data = []
        for eq in queryset:
            data.append({
                'equipment_number': eq.equipment_number,
                'name': eq.name,
                'category': eq.get_category_display(),
                'brand': eq.brand,
                'model_number': eq.model_number,
                'serial_number': eq.serial_number,
                'location': eq.location,
                'department': eq.assigned_department.name if eq.assigned_department else '',
                'purchase_date': str(eq.purchase_date) if eq.purchase_date else '',
                'purchase_cost': str(eq.purchase_cost),
                'warranty_end': str(eq.warranty_end) if eq.warranty_end else '',
                'status': eq.get_status_display(),
                'meter_reading': str(eq.current_meter_reading),
                'notes': eq.notes,
            })

        return export_to_excel(data, columns, 'المعدات', 'equipment.xlsx')

    def _export_work_orders(self, request):
        from core.utils import export_to_excel

        queryset = MaintenanceWorkOrder.objects.select_related(
            'equipment'
        ).order_by('-created_at')

        # Filter by status
        wo_status = request.query_params.get('status')
        if wo_status:
            queryset = queryset.filter(status=wo_status)
        # Filter by equipment
        equipment = request.query_params.get('equipment')
        if equipment:
            queryset = queryset.filter(equipment_id=equipment)

        columns = [
            ('work_order_number', 'رقم أمر العمل', 20),
            ('equipment_name', 'المعدة', 25),
            ('work_type', 'نوع العمل', 12),
            ('priority', 'الأولوية', 12),
            ('status', 'الحالة', 12),
            ('description', 'الوصف', 40),
            ('requested_by', 'مقدم الطلب', 20),
            ('assigned_to', 'المسؤول', 20),
            ('started_at', 'تاريخ البدء', 18),
            ('completed_at', 'تاريخ الإنجاز', 18),
            ('actual_cost', 'التكلفة الفعلية', 15),
            ('actual_hours', 'الساعات الفعلية', 15),
            ('completion_notes', 'ملاحظات الإنجاز', 30),
        ]

        data = []
        for wo in queryset:
            data.append({
                'work_order_number': wo.work_order_number,
                'equipment_name': wo.equipment.name,
                'work_type': wo.get_work_type_display(),
                'priority': wo.get_priority_display(),
                'status': wo.get_status_display(),
                'description': wo.description,
                'requested_by': wo.requested_by.get_full_name() if wo.requested_by else '',
                'assigned_to': wo.assigned_to.get_full_name() if wo.assigned_to else '',
                'started_at': str(wo.started_at) if wo.started_at else '',
                'completed_at': str(wo.completed_at) if wo.completed_at else '',
                'actual_cost': str(wo.actual_cost),
                'actual_hours': str(wo.actual_hours),
                'completion_notes': wo.completion_notes,
            })

        return export_to_excel(data, columns, 'أوامر عمل الصيانة', 'work_orders.xlsx')

    def _export_inspections(self, request):
        from core.utils import export_to_excel

        queryset = EquipmentInspection.objects.select_related(
            'equipment', 'inspector'
        ).order_by('-inspection_date')

        # Filter by equipment
        equipment = request.query_params.get('equipment')
        if equipment:
            queryset = queryset.filter(equipment_id=equipment)

        columns = [
            ('equipment_name', 'المعدة', 25),
            ('inspection_type', 'نوع الفحص', 12),
            ('inspector', 'المفتش', 20),
            ('inspection_date', 'تاريخ الفحص', 18),
            ('condition_rating', 'تقييم الحالة', 12),
            ('status', 'النتيجة', 15),
            ('findings', 'الملاحظات', 40),
            ('recommendations', 'التوصيات', 40),
            ('next_inspection', 'الفحص التالي', 15),
        ]

        data = []
        for insp in queryset:
            data.append({
                'equipment_name': insp.equipment.name,
                'inspection_type': insp.get_inspection_type_display(),
                'inspector': insp.inspector.get_full_name() if insp.inspector else '',
                'inspection_date': str(insp.inspection_date),
                'condition_rating': insp.get_condition_rating_display(),
                'status': insp.get_status_display(),
                'findings': insp.findings,
                'recommendations': insp.recommendations,
                'next_inspection': str(insp.next_inspection) if insp.next_inspection else '',
            })

        return export_to_excel(data, columns, 'فحوصات المعدات', 'inspections.xlsx')
