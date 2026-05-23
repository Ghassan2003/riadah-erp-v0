"""
API views for Cost Allocation module.
Handles Cost Centers, Allocation Rules, Targets, Execution, and Logs.
"""

from rest_framework import (
    generics, status, permissions, filters, views
)
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.db.models import Count, Q
from decimal import Decimal

from .cost_allocation import (
    CostCenter,
    AllocationRule,
    AllocationTarget,
    AllocationLog,
    AllocationLogStatus,
    execute_allocation_rule,
    execute_all_recurring_allocations,
)
from users.permissions import IsAccountantOrAdmin, IsAdmin


# =============================================
# Cost Center Serializers
# =============================================

class CostCenterListSerializer(generics.ListAPIView):
    """Serializer for listing cost centers."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CostCenter.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = []
        for cc in queryset:
            budget = cc.budget_amount
            actual = cc.actual_amount
            utilization = (
                round((actual / budget) * 100, 2)
                if budget > 0 else Decimal('0')
            )
            data.append({
                'id': cc.id,
                'code': cc.code,
                'name': cc.name,
                'name_en': cc.name_en,
                'is_active': cc.is_active,
                'budget_amount': str(budget),
                'actual_amount': str(actual),
                'utilization_percentage': utilization,
            })
        return Response(data)


class CostCenterCreateSerializer(generics.CreateAPIView):
    """Serializer for creating a cost center."""

    permission_classes = [IsAccountantOrAdmin]

    class Meta:
        from rest_framework import serializers

        fields = ['code', 'name', 'name_en', 'department', 'manager', 'parent', 'budget_amount']

    def get_serializer_class(self):
        from rest_framework import serializers

        class _Serializer(serializers.ModelSerializer):
            class Meta:
                model = CostCenter
                fields = ['code', 'name', 'name_en', 'department', 'manager', 'parent', 'budget_amount']

        return _Serializer


class CostCenterDetailSerializer:
    """Serializer for cost center detail view."""

    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def serialize(cost_center):
        budget = cost_center.budget_amount
        actual = cost_center.actual_amount
        variance = budget - actual

        data = {
            'id': cost_center.id,
            'code': cost_center.code,
            'name': cost_center.name,
            'name_en': cost_center.name_en,
            'department': cost_center.department.name if cost_center.department else None,
            'department_id': cost_center.department_id,
            'manager': cost_center.manager.get_full_name() if cost_center.manager else None,
            'manager_id': cost_center.manager_id,
            'parent': cost_center.parent.name if cost_center.parent else None,
            'parent_id': cost_center.parent_id,
            'is_active': cost_center.is_active,
            'budget_amount': str(budget),
            'actual_amount': str(actual),
            'variance': str(variance),
            'full_path': cost_center.get_full_path(),
            'children_actual_total': str(cost_center.get_children_actual_total()),
            'created_at': cost_center.created_at.isoformat() if cost_center.created_at else None,
            'updated_at': cost_center.updated_at.isoformat() if cost_center.updated_at else None,
            'children': [],
        }

        if cost_center.children.exists():
            for child in cost_center.children.all():
                child_budget = child.budget_amount
                child_actual = child.actual_amount
                child_variance = child_budget - child_actual
                data['children'].append({
                    'id': child.id,
                    'code': child.code,
                    'name': child.name,
                    'name_en': child.name_en,
                    'is_active': child.is_active,
                    'budget_amount': str(child_budget),
                    'actual_amount': str(child_actual),
                    'variance': str(child_variance),
                })

        return data


# =============================================
# Allocation Rule Serializers
# =============================================

class AllocationRuleListSerializer:
    """Serializer for listing allocation rules."""

    @staticmethod
    def serialize(rule):
        return {
            'id': rule.id,
            'name': rule.name,
            'allocation_type': rule.allocation_type,
            'allocation_type_display': rule.get_allocation_type_display(),
            'source_account_name': f'{rule.source_account.code} - {rule.source_account.name}' if rule.source_account else None,
            'source_account_id': rule.source_account_id,
            'is_active': rule.is_active,
            'is_recurring': rule.is_recurring,
            'effective_from': rule.effective_from.isoformat() if rule.effective_from else None,
            'effective_to': rule.effective_to.isoformat() if rule.effective_to else None,
            'last_executed': rule.last_executed.isoformat() if rule.last_executed else None,
            'targets_count': rule.targets.count(),
        }


class AllocationTargetSerializer:
    """Serializer for allocation targets."""

    @staticmethod
    def serialize(target):
        return {
            'id': target.id,
            'target_cost_center_name': target.target_cost_center.name if target.target_cost_center else None,
            'target_cost_center_code': target.target_cost_center.code if target.target_cost_center else None,
            'target_cost_center_id': target.target_cost_center_id,
            'target_account_name': target.target_account.name if target.target_account else None,
            'target_account_code': target.target_account.code if target.target_account else None,
            'target_account_id': target.target_account_id,
            'percentage': str(target.percentage) if target.percentage is not None else None,
            'ratio': str(target.ratio) if target.ratio is not None else None,
        }


class AllocationLogSerializer:
    """Serializer for allocation logs."""

    @staticmethod
    def serialize(log):
        return {
            'id': log.id,
            'rule_name': log.rule.name if log.rule else None,
            'rule_id': log.rule_id,
            'period_start': log.period_start.isoformat() if log.period_start else None,
            'period_end': log.period_end.isoformat() if log.period_end else None,
            'total_allocated': str(log.total_allocated),
            'source_balance_before': str(log.source_balance_before),
            'status': log.status,
            'status_display': log.get_status_display(),
            'executed_by_name': log.executed_by.get_full_name() if log.executed_by else None,
            'executed_by_id': log.executed_by_id,
            'executed_at': log.executed_at.isoformat() if log.executed_at else None,
            'error_message': log.error_message,
            'journal_entry_id': log.journal_entry_id,
        }


class AllocationRuleDetailSerializer:
    """Serializer for detailed allocation rule view."""

    @staticmethod
    def serialize(rule):
        data = {
            'id': rule.id,
            'name': rule.name,
            'description': rule.description,
            'source_account': {
                'id': rule.source_account.id,
                'code': rule.source_account.code,
                'name': rule.source_account.name,
            } if rule.source_account else None,
            'source_account_id': rule.source_account_id,
            'allocation_type': rule.allocation_type,
            'allocation_type_display': rule.get_allocation_type_display(),
            'is_active': rule.is_active,
            'is_recurring': rule.is_recurring,
            'recurrence_day': rule.recurrence_day,
            'effective_from': rule.effective_from.isoformat() if rule.effective_from else None,
            'effective_to': rule.effective_to.isoformat() if rule.effective_to else None,
            'last_executed': rule.last_executed.isoformat() if rule.last_executed else None,
            'is_effective': rule.is_effective(),
            'is_due_for_execution': rule.is_due_for_execution(),
            'created_by': rule.created_by.get_full_name() if rule.created_by else None,
            'created_by_id': rule.created_by_id,
            'created_at': rule.created_at.isoformat() if rule.created_at else None,
            'updated_at': rule.updated_at.isoformat() if rule.updated_at else None,
            'targets': [],
            'recent_logs': [],
        }

        for target in rule.targets.select_related(
            'target_cost_center', 'target_account'
        ).all():
            data['targets'].append(AllocationTargetSerializer.serialize(target))

        for log in rule.logs.all()[:5]:
            data['recent_logs'].append(AllocationLogSerializer.serialize(log))

        return data


class AllocationExecutionSerializer:
    """Serializer for allocation execution responses."""

    @staticmethod
    def serialize_success(result):
        return {
            'success': result.get('status') in (
                AllocationLogStatus.SUCCESS,
                AllocationLogStatus.PARTIAL,
            ),
            'message': (
                'تم تنفيذ التوزيع بنجاح'
                if result.get('status') == AllocationLogStatus.SUCCESS
                else 'تم تنفيذ التوزيع بشكل جزئي'
                if result.get('status') == AllocationLogStatus.PARTIAL
                else f'فشل تنفيذ التوزيع: {result.get("error", "")}'
            ),
            'status': result.get('status', ''),
            'rule_id': result.get('rule_id'),
            'rule_name': result.get('rule_name', ''),
            'total_allocated': str(result.get('total_allocated', Decimal('0'))),
            'journal_entry_id': result.get('journal_entry_id'),
            'allocations': result.get('allocations', []),
            'error': result.get('error', ''),
        }


# =============================================
# Cost Center Views
# =============================================

class CostCenterListView(generics.ListAPIView):
    """GET: قائمة مراكز التكلفة."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = CostCenter.objects.select_related(
            'department', 'manager', 'parent'
        ).order_by('code')

        # Filter by is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_val = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_val)

        # Filter by department
        department_id = self.request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        # Filter by parent (top-level only)
        top_level = self.request.query_params.get('top_level')
        if top_level and top_level.lower() == 'true':
            queryset = queryset.filter(parent__isnull=True)

        data = []
        for cc in queryset:
            budget = cc.budget_amount
            actual = cc.actual_amount
            utilization = (
                round((actual / budget) * 100, 2)
                if budget > 0 else Decimal('0')
            )
            data.append({
                'id': cc.id,
                'code': cc.code,
                'name': cc.name,
                'name_en': cc.name_en,
                'is_active': cc.is_active,
                'budget_amount': str(budget),
                'actual_amount': str(actual),
                'utilization_percentage': utilization,
            })

        return Response(data)


class CostCenterCreateView(views.APIView):
    """POST: إنشاء مركز تكلفة جديد."""

    permission_classes = [IsAccountantOrAdmin]

    def post(self, request):
        from rest_framework import serializers

        class _CreateSerializer(serializers.ModelSerializer):
            class Meta:
                model = CostCenter
                fields = ['code', 'name', 'name_en', 'department', 'manager', 'parent', 'budget_amount']

        serializer = _CreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cost_center = serializer.save()

        return Response({
            'message': 'تم إنشاء مركز التكلفة بنجاح',
            'cost_center': {
                'id': cost_center.id,
                'code': cost_center.code,
                'name': cost_center.name,
                'name_en': cost_center.name_en,
                'department': cost_center.department.name if cost_center.department else None,
                'manager': cost_center.manager.get_full_name() if cost_center.manager else None,
                'parent': cost_center.parent.name if cost_center.parent else None,
                'budget_amount': str(cost_center.budget_amount),
                'is_active': cost_center.is_active,
            },
        }, status=status.HTTP_201_CREATED)


class CostCenterDetailView(views.APIView):
    """GET: تفاصيل مركز تكلفة."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            cost_center = CostCenter.objects.select_related(
                'department', 'manager', 'parent'
            ).prefetch_related('children').get(pk=pk)
        except CostCenter.DoesNotExist:
            return Response(
                {'error': 'مركز التكلفة غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            CostCenterDetailSerializer.serialize(cost_center)
        )


class CostCenterUpdateView(views.APIView):
    """PATCH: تحديث مركز تكلفة."""

    permission_classes = [IsAccountantOrAdmin]

    def patch(self, request, pk):
        from rest_framework import serializers

        class _UpdateSerializer(serializers.ModelSerializer):
            class Meta:
                model = CostCenter
                fields = ['code', 'name', 'name_en', 'department', 'manager', 'parent', 'budget_amount', 'is_active']

        try:
            cost_center = CostCenter.objects.get(pk=pk)
        except CostCenter.DoesNotExist:
            return Response(
                {'error': 'مركز التكلفة غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = _UpdateSerializer(cost_center, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        cost_center = serializer.save()

        return Response({
            'message': 'تم تحديث مركز التكلفة بنجاح',
            'cost_center': {
                'id': cost_center.id,
                'code': cost_center.code,
                'name': cost_center.name,
                'name_en': cost_center.name_en,
                'department': cost_center.department.name if cost_center.department else None,
                'manager': cost_center.manager.get_full_name() if cost_center.manager else None,
                'parent': cost_center.parent.name if cost_center.parent else None,
                'budget_amount': str(cost_center.budget_amount),
                'actual_amount': str(cost_center.actual_amount),
                'is_active': cost_center.is_active,
            },
        })


# =============================================
# Allocation Rule Views
# =============================================

class AllocationRuleListView(generics.ListAPIView):
    """GET: قائمة قواعد التوزيع."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = AllocationRule.objects.select_related(
            'source_account'
        ).annotate(
            targets_count=Count('targets')
        ).order_by('-created_at')

        # Filter by is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_val = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_val)

        # Filter by allocation_type
        allocation_type = self.request.query_params.get('allocation_type')
        if allocation_type:
            queryset = queryset.filter(allocation_type=allocation_type)

        # Filter by is_recurring
        is_recurring = self.request.query_params.get('is_recurring')
        if is_recurring is not None:
            is_recurring_val = is_recurring.lower() == 'true'
            queryset = queryset.filter(is_recurring=is_recurring_val)

        data = []
        for rule in queryset:
            data.append(AllocationRuleListSerializer.serialize(rule))

        return Response(data)


class AllocationRuleCreateView(views.APIView):
    """POST: إنشاء قاعدة توزيع جديدة مع الأهداف."""

    permission_classes = [IsAccountantOrAdmin]

    @db_transaction.atomic
    def post(self, request):
        from rest_framework import serializers

        class _TargetSerializer(serializers.Serializer):
            target_cost_center = serializers.PrimaryKeyRelatedField(
                queryset=CostCenter.objects.filter(is_active=True),
                error_messages={'does_not_exist': 'مركز التكلفة الهدف غير موجود'}
            )
            target_account = serializers.PrimaryKeyRelatedField(
                queryset=CostCenter,  # Will be overridden below
                error_messages={'does_not_exist': 'الحساب الهدف غير موجود'}
            )
            percentage = serializers.DecimalField(
                max_digits=5, decimal_places=2, required=False, allow_null=True
            )
            ratio = serializers.DecimalField(
                max_digits=10, decimal_places=2, required=False, allow_null=True
            )

        class _CreateSerializer(serializers.Serializer):
            name = serializers.CharField(max_length=255)
            description = serializers.CharField(required=False, default='', allow_blank=True)
            source_account = serializers.PrimaryKeyRelatedField(
                queryset=AllocationRule._meta.get_field('source_account').related_model.objects.filter(is_active=True),
            )
            allocation_type = serializers.ChoiceField(choices=AllocationRule.allocation_type.field.choices)
            is_active = serializers.BooleanField(default=True)
            is_recurring = serializers.BooleanField(default=False)
            recurrence_day = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=28)
            effective_from = serializers.DateField()
            effective_to = serializers.DateField(required=False, allow_null=True, default=None)
            targets = _TargetSerializer(many=True, required=False, default=[])

        serializer = _CreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Override target_account queryset to use Account model
        from .models import Account
        targets_data = request.data.get('targets', [])
        validated_targets = []

        for target_data in targets_data:
            try:
                cost_center = CostCenter.objects.get(
                    pk=target_data['target_cost_center'], is_active=True
                )
            except (CostCenter.DoesNotExist, KeyError, ValueError):
                return Response(
                    {'error': 'مركز التكلفة الهدف غير موجود أو غير مفعّل'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                account = Account.objects.get(
                    pk=target_data['target_account'], is_active=True
                )
            except (Account.DoesNotExist, KeyError, ValueError):
                return Response(
                    {'error': 'الحساب الهدف غير موجود أو غير مفعّل'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            validated_targets.append({
                'target_cost_center': cost_center,
                'target_account': account,
                'percentage': target_data.get('percentage'),
                'ratio': target_data.get('ratio'),
            })

        # Create the rule
        rule = AllocationRule.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            source_account=data['source_account'],
            allocation_type=data['allocation_type'],
            is_active=data.get('is_active', True),
            is_recurring=data.get('is_recurring', False),
            recurrence_day=data.get('recurrence_day'),
            effective_from=data['effective_from'],
            effective_to=data.get('effective_to'),
            created_by=request.user,
        )

        # Create targets
        created_targets = []
        for target_data in validated_targets:
            target = AllocationTarget.objects.create(
                rule=rule,
                target_cost_center=target_data['target_cost_center'],
                target_account=target_data['target_account'],
                percentage=target_data.get('percentage'),
                ratio=target_data.get('ratio'),
            )
            created_targets.append(AllocationTargetSerializer.serialize(target))

        return Response({
            'message': 'تم إنشاء قاعدة التوزيع بنجاح',
            'rule': AllocationRuleDetailSerializer.serialize(rule),
        }, status=status.HTTP_201_CREATED)


class AllocationRuleDetailView(views.APIView):
    """GET: تفاصيل قاعدة التوزيع مع الأهداف والسجلات."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            rule = AllocationRule.objects.select_related(
                'source_account', 'created_by'
            ).prefetch_related(
                'targets__target_cost_center',
                'targets__target_account',
                'logs__rule',
                'logs__executed_by',
            ).get(pk=pk)
        except AllocationRule.DoesNotExist:
            return Response(
                {'error': 'قاعدة التوزيع غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            AllocationRuleDetailSerializer.serialize(rule)
        )


class AllocationRuleExecuteView(views.APIView):
    """POST: تنفيذ قاعدة توزيع واحدة."""

    permission_classes = [IsAccountantOrAdmin]

    def post(self, request, pk):
        try:
            rule = AllocationRule.objects.get(pk=pk)
        except AllocationRule.DoesNotExist:
            return Response(
                {'error': 'قاعدة التوزيع غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not rule.is_active:
            return Response(
                {'error': 'قاعدة التوزيع غير مفعّلة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = execute_allocation_rule(pk, request.user)

        response_data = AllocationExecutionSerializer.serialize_success(result)

        http_status = status.HTTP_200_OK
        if result.get('status') == AllocationLogStatus.FAILED:
            http_status = status.HTTP_400_BAD_REQUEST

        return Response(response_data, status=http_status)


class AllocationRuleBatchExecuteView(views.APIView):
    """POST: تنفيذ جميع قواعد التوزيع المتكررة المستحقة."""

    permission_classes = [IsAdmin]

    def post(self, request):
        result = execute_all_recurring_allocations(request.user)

        return Response({
            'success': result['failed_count'] == 0,
            'message': (
                f'تم تنفيذ {result["rules_executed"]} قاعدة توزيع من أصل '
                f'{result["total_rules_checked"]} قاعدة متكررة '
                f'({result["success_count"]} نجح، '
                f'{result["partial_count"]} جزئي، '
                f'{result["failed_count"]} فشل)'
            ),
            'total_rules_checked': result['total_rules_checked'],
            'rules_executed': result['rules_executed'],
            'success_count': result['success_count'],
            'partial_count': result['partial_count'],
            'failed_count': result['failed_count'],
            'results': [
                AllocationExecutionSerializer.serialize_success(r)
                for r in result['results']
            ],
        })


# =============================================
# Allocation Log Views
# =============================================

class AllocationLogListView(generics.ListAPIView):
    """GET: قائمة سجلات التوزيعات."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = AllocationLog.objects.select_related(
            'rule', 'executed_by'
        ).order_by('-executed_at')

        # Filter by rule_id
        rule_id = self.request.query_params.get('rule_id')
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)

        # Filter by status
        log_status = self.request.query_params.get('status')
        if log_status:
            queryset = queryset.filter(status=log_status)

        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(executed_at__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(executed_at__date__lte=date_to)

        data = []
        for log in queryset:
            data.append(AllocationLogSerializer.serialize(log))

        return Response(data)
