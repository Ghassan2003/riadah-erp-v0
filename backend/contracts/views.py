"""
API views for the Contracts module.
Handles contracts, milestones, payments, and renewals.
"""

from rest_framework import (
    generics, status, permissions, filters, views
)
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum, Count, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

from .models import Contract, ContractMilestone, ContractPayment
from .serializers import (
    ContractListSerializer, ContractCreateSerializer, ContractUpdateSerializer, ContractDetailSerializer,
    ContractMilestoneListSerializer, ContractMilestoneCreateSerializer, ContractMilestoneUpdateSerializer,
    ContractPaymentListSerializer, ContractPaymentCreateSerializer, ContractPaymentUpdateSerializer,
    ContractChangeStatusSerializer, ContractRenewSerializer, ContractStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Contract Views
# =============================================

class ContractListView(generics.ListCreateAPIView):
    """GET: List contracts. POST: Create contract (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'title_en', 'contract_number', 'notes']
    ordering_fields = ['title', 'contract_number', 'start_date', 'end_date', 'value', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ContractCreateSerializer
        return ContractListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Contract.objects.select_related('customer', 'supplier', 'project', 'responsible_person').prefetch_related('milestones', 'contract_payments')
        contract_type = self.request.query_params.get('contract_type')
        if contract_type:
            queryset = queryset.filter(contract_type=contract_type)
        contract_status = self.request.query_params.get('status')
        if contract_status:
            queryset = queryset.filter(status=contract_status)
        customer = self.request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(customer_id=customer)
        is_expiring = self.request.query_params.get('expiring_soon')
        if is_expiring and is_expiring.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                end_date__isnull=False,
                end_date__lte=today + timedelta(days=30),
                end_date__gte=today,
            )
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء العقد بنجاح',
            'contract': ContractDetailSerializer(contract).data,
        }, status=status.HTTP_201_CREATED)


class ContractDetailView(generics.RetrieveUpdateAPIView):
    """GET: Contract details. PATCH: Update contract (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ContractUpdateSerializer
        return ContractDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Contract.objects.select_related(
            'customer', 'supplier', 'project', 'signed_by',
            'responsible_person', 'created_by'
        ).prefetch_related('milestones', 'contract_payments')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        contract = serializer.save()
        return Response({
            'message': 'تم تحديث العقد بنجاح',
            'contract': ContractDetailSerializer(contract).data,
        })


class ContractDeleteView(views.APIView):
    """DELETE: Soft-delete a contract (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            contract = Contract.objects.get(pk=pk)
        except Contract.DoesNotExist:
            return Response({'error': 'العقد غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        contract.is_active = False
        contract.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم حذف العقد بنجاح'})


class ContractRestoreView(views.APIView):
    """POST: Restore a soft-deleted contract (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            contract = Contract.objects.get(pk=pk)
        except Contract.DoesNotExist:
            return Response({'error': 'العقد غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        contract.is_active = True
        contract.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'تم إعادة تفعيل العقد بنجاح'})


class ContractChangeStatusView(views.APIView):
    """POST: Change contract status (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            contract = Contract.objects.get(pk=pk)
        except Contract.DoesNotExist:
            return Response({'error': 'العقد غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ContractChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contract.status = serializer.validated_data['new_status']
        contract.save(update_fields=['status', 'updated_at'])

        return Response({
            'message': 'تم تغيير حالة العقد بنجاح',
            'contract': ContractDetailSerializer(contract).data,
        })


class ContractRenewView(views.APIView):
    """POST: Renew a contract (admin only)."""

    permission_classes = [IsAdmin]

    @transaction.atomic
    def post(self, request, pk):
        try:
            contract = Contract.objects.get(pk=pk)
        except Contract.DoesNotExist:
            return Response({'error': 'العقد غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ContractRenewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_end_date = serializer.validated_data['new_end_date']
        new_value = serializer.validated_data.get('new_value')

        # Mark current contract as renewed
        old_end_date = contract.end_date
        contract.status = 'renewed'
        contract.end_date = old_end_date
        contract.save(update_fields=['status', 'updated_at'])

        # Create new contract
        new_contract = Contract.objects.create(
            title=contract.title,
            title_en=contract.title_en,
            contract_type=contract.contract_type,
            customer=contract.customer,
            supplier=contract.supplier,
            project=contract.project,
            start_date=old_end_date or contract.start_date,
            end_date=new_end_date,
            value=new_value if new_value is not None else contract.value,
            currency=contract.currency,
            vat_inclusive=contract.vat_inclusive,
            payment_terms=contract.payment_terms,
            description=contract.description,
            terms_conditions=contract.terms_conditions,
            status='active',
            renewal_reminder_days=contract.renewal_reminder_days,
            signed_by=contract.signed_by,
            responsible_person=contract.responsible_person,
            notes=serializer.validated_data.get('notes', ''),
            created_by=request.user,
        )

        return Response({
            'message': 'تم تجديد العقد بنجاح',
            'old_contract': ContractListSerializer(contract).data,
            'new_contract': ContractDetailSerializer(new_contract).data,
        })


# =============================================
# ContractMilestone Views
# =============================================

class ContractMilestoneListView(generics.ListAPIView):
    """GET: List contract milestones with filtering."""

    serializer_class = ContractMilestoneListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'status', 'amount']
    ordering = ['due_date']

    def get_queryset(self):
        queryset = ContractMilestone.objects.select_related('contract')
        contract = self.request.query_params.get('contract')
        if contract:
            queryset = queryset.filter(contract_id=contract)
        milestone_status = self.request.query_params.get('status')
        if milestone_status:
            queryset = queryset.filter(status=milestone_status)
        return queryset


class ContractMilestoneCreateView(generics.CreateAPIView):
    """POST: Create a contract milestone (admin only)."""

    serializer_class = ContractMilestoneCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        milestone = serializer.save()
        return Response({
            'message': 'تم إنشاء المرحلة بنجاح',
            'milestone': ContractMilestoneListSerializer(milestone).data,
        }, status=status.HTTP_201_CREATED)


class ContractMilestoneUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a contract milestone (admin only)."""

    serializer_class = ContractMilestoneUpdateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return ContractMilestone.objects.select_related('contract')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        milestone = serializer.save()

        # Auto-check overdue milestones
        if milestone.status != 'completed' and milestone.due_date < timezone.now().date():
            milestone.status = 'overdue'
            milestone.save(update_fields=['status'])

        return Response({
            'message': 'تم تحديث المرحلة بنجاح',
            'milestone': ContractMilestoneListSerializer(milestone).data,
        })


class ContractMilestoneDetailView(generics.RetrieveAPIView):
    """GET: Contract milestone detail."""

    serializer_class = ContractMilestoneListSerializer

    def get_queryset(self):
        return ContractMilestone.objects.select_related('contract')


class ContractMilestoneDeleteView(views.APIView):
    """DELETE: Delete a contract milestone (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            milestone = ContractMilestone.objects.get(pk=pk)
        except ContractMilestone.DoesNotExist:
            return Response({'error': 'المرحلة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
        milestone.delete()
        return Response({'message': 'تم حذف المرحلة بنجاح'})


# =============================================
# ContractPayment Views
# =============================================

class ContractPaymentListView(generics.ListAPIView):
    """GET: List contract payments with filtering."""

    serializer_class = ContractPaymentListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['reference', 'notes']
    ordering_fields = ['due_date', 'amount', 'payment_status']
    ordering = ['due_date']

    def get_queryset(self):
        queryset = ContractPayment.objects.select_related('contract', 'milestone')
        contract = self.request.query_params.get('contract')
        if contract:
            queryset = queryset.filter(contract_id=contract)
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        return queryset


class ContractPaymentCreateView(generics.CreateAPIView):
    """POST: Create a contract payment (admin only)."""

    serializer_class = ContractPaymentCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response({
            'message': 'تم إنشاء الدفعة بنجاح',
            'payment': ContractPaymentListSerializer(payment).data,
        }, status=status.HTTP_201_CREATED)


class ContractPaymentUpdateView(generics.UpdateAPIView):
    """PUT/PATCH: Update a contract payment (admin only)."""

    serializer_class = ContractPaymentUpdateSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return ContractPayment.objects.select_related('contract', 'milestone')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response({
            'message': 'تم تحديث الدفعة بنجاح',
            'payment': ContractPaymentListSerializer(payment).data,
        })


class ContractPaymentDetailView(generics.RetrieveAPIView):
    """GET: Contract payment detail."""

    serializer_class = ContractPaymentListSerializer

    def get_queryset(self):
        return ContractPayment.objects.select_related('contract', 'milestone')


class ContractPaymentDeleteView(views.APIView):
    """DELETE: Delete a contract payment (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            payment = ContractPayment.objects.get(pk=pk)
        except ContractPayment.DoesNotExist:
            return Response({'error': 'الدفعة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
        payment.delete()
        return Response({'message': 'تم حذف الدفعة بنجاح'})


# =============================================
# Contract Stats View
# =============================================

class ContractStatsView(views.APIView):
    """GET: Contract statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from decimal import Decimal
        today = timezone.now().date()
        thirty_days = today + timedelta(days=30)

        stats = {
            'total_contracts': Contract.objects.count(),
            'active_contracts': Contract.objects.filter(status='active').count(),
            'expired_contracts': Contract.objects.filter(status='expired').count(),
            'expiring_soon': Contract.objects.filter(
                status='active',
                end_date__isnull=False,
                end_date__lte=thirty_days,
                end_date__gte=today,
            ).count(),
            'total_value': Contract.objects.aggregate(
                total=Coalesce(Sum('value'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'total_paid': ContractPayment.objects.aggregate(
                total=Coalesce(Sum('paid_amount'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
            )['total'],
            'pending_payments': ContractPayment.objects.filter(payment_status='pending').count(),
            'completed_milestones': ContractMilestone.objects.filter(status='completed').count(),
            'pending_milestones': ContractMilestone.objects.filter(status__in=('pending', 'in_progress')).count(),
        }
        serializer = ContractStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# Excel Export View
# =============================================

class ContractExportView(views.APIView):
    """GET: Export contracts to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel
        queryset = Contract.objects.select_related('customer', 'supplier', 'project', 'responsible_person')
        columns = [
            ('contract_number', 'رقم العقد', 25),
            ('title', 'عنوان العقد', 30),
            ('contract_type', 'نوع العقد', 15),
            ('customer', 'العميل', 25),
            ('supplier', 'المورد', 25),
            ('project', 'المشروع', 25),
            ('start_date', 'تاريخ البداية', 15),
            ('end_date', 'تاريخ النهاية', 15),
            ('value', 'القيمة', 15),
            ('currency', 'العملة', 10),
            ('status', 'الحالة', 15),
            ('responsible', 'المسؤول', 20),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for c in queryset:
            data.append({
                'contract_number': c.contract_number,
                'title': c.title,
                'contract_type': c.get_contract_type_display(),
                'customer': c.customer.name if c.customer else '',
                'supplier': c.supplier.name if c.supplier else '',
                'project': c.project.name if c.project else '',
                'start_date': str(c.start_date) if c.start_date else '',
                'end_date': str(c.end_date) if c.end_date else '',
                'value': str(c.value),
                'currency': c.currency,
                'status': c.get_status_display(),
                'responsible': c.responsible_person.username if c.responsible_person else '',
                'created_at': str(c.created_at.strftime('%Y-%m-%d %H:%M')) if c.created_at else '',
            })
        return export_to_excel(data, columns, 'العقود', 'contracts.xlsx')
