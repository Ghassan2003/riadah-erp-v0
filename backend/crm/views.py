"""
واجهات برمجة التطبيقات (API Views) لوحدة إدارة علاقات العملاء (CRM).
تتعامل مع الشركات، جهات الاتصال، فرص البيع، أنشطة الفرص، شرائح العملاء، الحملات التسويقية، وأنشطة الحملات والإحصائيات والتصدير.
"""

from decimal import Decimal
from datetime import date, timedelta
from collections import defaultdict

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, DurationField, Q, Value, Avg, ExpressionWrapper, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    Company,
    Contact,
    Lead,
    LeadActivity,
    CustomerSegment,
    Campaign,
    CampaignActivity,
    SLAPolicy,
    Ticket,
    TicketComment,
    Quotation,
    QuotationItem,
    Commission,
)
from .serializers import (
    CompanyListSerializer,
    CompanyCreateSerializer,
    CompanyUpdateSerializer,
    CompanyDetailSerializer,
    ContactListSerializer,
    ContactCreateSerializer,
    ContactUpdateSerializer,
    ContactDetailSerializer,
    LeadListSerializer,
    LeadCreateSerializer,
    LeadUpdateSerializer,
    LeadChangeStatusSerializer,
    LeadDetailWithActivitiesSerializer,
    LeadActivityListSerializer,
    LeadActivityCreateSerializer,
    CustomerSegmentListSerializer,
    CustomerSegmentCreateSerializer,
    CustomerSegmentUpdateSerializer,
    CampaignListSerializer,
    CampaignCreateSerializer,
    CampaignUpdateSerializer,
    CampaignChangeStatusSerializer,
    CampaignActivityListSerializer,
    CampaignActivityCreateSerializer,
    CRMStatsSerializer,
    LeadConvertSerializer,
    PipelineFunnelSerializer,
    SalesForecastSerializer,
    SalesStageAnalyticsSerializer,
    CompanyStatsSerializer,
    SLAPolicyListSerializer,
    SLAPolicyCreateSerializer,
    SLAPolicyUpdateSerializer,
    TicketListSerializer,
    TicketCreateSerializer,
    TicketUpdateSerializer,
    TicketDetailSerializer,
    TicketAssignSerializer,
    TicketResolveSerializer,
    TicketStatsSerializer,
    TicketCommentListSerializer,
    TicketCommentCreateSerializer,
    QuotationListSerializer,
    QuotationCreateSerializer,
    QuotationUpdateSerializer,
    QuotationDetailSerializer,
    QuotationItemCreateSerializer,
    QuotationItemUpdateSerializer,
    CommissionListSerializer,
    CommissionCreateSerializer,
    CommissionUpdateSerializer,
    CommissionStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# واجهات إحصائيات إدارة علاقات العملاء
# =============================================

class CRMStatsView(views.APIView):
    """GET: إحصائيات لوحة تحكم إدارة علاقات العملاء."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stats = {
            'total_contacts': Contact.objects.count(),
            'active_contacts': Contact.objects.filter(status='active').count(),
            'total_leads': Lead.objects.count(),
            'active_leads': Lead.objects.filter(
                status__in=('new', 'contacted', 'qualified', 'proposal', 'negotiation')
            ).count(),
            'won_leads': Lead.objects.filter(status='won').count(),
            'lost_leads': Lead.objects.filter(status='lost').count(),
            'won_revenue': Lead.objects.filter(status='won').aggregate(
                total=Coalesce(
                    Sum('value'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_pipeline_value': Lead.objects.filter(
                status__in=('new', 'contacted', 'qualified', 'proposal', 'negotiation')
            ).aggregate(
                total=Coalesce(
                    Sum('value'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'weighted_pipeline_value': Lead.objects.filter(
                status__in=('new', 'contacted', 'qualified', 'proposal', 'negotiation')
            ).aggregate(
                total=Coalesce(
                    Sum(F('value') * F('probability') / 100),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_segments': CustomerSegment.objects.count(),
            'active_campaigns': Campaign.objects.filter(status='active').count(),
            'total_campaigns': Campaign.objects.count(),
            'total_budget': Campaign.objects.aggregate(
                total=Coalesce(
                    Sum('budget'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_actual_cost': Campaign.objects.aggregate(
                total=Coalesce(
                    Sum('actual_cost'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'pending_activities': LeadActivity.objects.filter(completed=False).count(),
            'completed_activities': LeadActivity.objects.filter(completed=True).count(),
        }

        serializer = CRMStatsSerializer(stats)
        return Response(serializer.data)


# =============================================
# واجهات الشركات / الحسابات
# =============================================

class CompanyListView(generics.ListCreateAPIView):
    """GET: عرض قائمة الشركات مع التصفية. POST: إنشاء شركة (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_en', 'industry', 'city', 'country', 'email', 'phone']
    ordering_fields = ['name', 'company_type', 'industry', 'city', 'country', 'annual_revenue', 'employee_count', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CompanyCreateSerializer
        return CompanyListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Company.objects.select_related('assigned_to').annotate(
            contacts_count=Count('contacts')
        )
        # تصفية حسب نوع الشركة
        company_type = self.request.query_params.get('company_type')
        if company_type:
            queryset = queryset.filter(company_type=company_type)
        # تصفية حسب القطاع الصناعي
        industry = self.request.query_params.get('industry')
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        # تصفية حسب المدينة
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        # تصفية حسب البلد
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__icontains=country)
        # تصفية حسب حالة التفعيل
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        # تصفية حسب المستخدم المسند إليه
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        return Response({
            'message': 'تم إنشاء الشركة بنجاح',
            'company': CompanyDetailSerializer(company).data,
        }, status=status.HTTP_201_CREATED)


class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: تفاصيل الشركة. PUT/PATCH: تحديث الشركة (للمسؤولين فقط). DELETE: حذف الشركة (للمسؤولين فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CompanyUpdateSerializer
        return CompanyDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Company.objects.select_related('assigned_to').annotate(
            contacts_count=Count('contacts')
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        return Response({
            'message': 'تم تحديث الشركة بنجاح',
            'company': CompanyDetailSerializer(company).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyContactsView(generics.ListAPIView):
    """GET: عرض قائمة جهات الاتصال التابعة لشركة معينة."""

    serializer_class = ContactListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        company_id = self.kwargs.get('pk')
        return Contact.objects.filter(
            company_account_id=company_id
        ).select_related('assigned_to', 'company_account').order_by('-created_at')


class CompanyStatsView(views.APIView):
    """GET: إحصائيات شركة معينة (إجمالي الفرص، الصفقات الرابحة، الإيرادات)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response(
                {'error': 'الشركة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # معرفات جهات الاتصال التابعة للشركة
        contact_ids = Contact.objects.filter(
            company_account=company
        ).values_list('id', flat=True)

        leads = Lead.objects.filter(contact_id__in=contact_ids)

        total_leads = leads.count()
        won_deals = leads.filter(status='won').count()
        lost_deals = leads.filter(status='lost').count()
        total_revenue = leads.filter(status='won').aggregate(
            total=Coalesce(
                Sum('value'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total']
        active_pipeline_value = leads.filter(
            status__in=('new', 'contacted', 'qualified', 'proposal', 'negotiation')
        ).aggregate(
            total=Coalesce(
                Sum('value'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total']

        stats_data = {
            'company_id': company.id,
            'company_name': company.name,
            'total_contacts': len(contact_ids),
            'total_leads': total_leads,
            'won_deals': won_deals,
            'lost_deals': lost_deals,
            'total_revenue': total_revenue,
            'active_pipeline_value': active_pipeline_value,
        }

        serializer = CompanyStatsSerializer(stats_data)
        return Response(serializer.data)


# =============================================
# واجهات جهات الاتصال
# =============================================

class ContactListView(generics.ListCreateAPIView):
    """GET: عرض قائمة جهات الاتصال. POST: إنشاء جهة اتصال (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'company', 'phone', 'mobile']
    ordering_fields = ['first_name', 'last_name', 'company', 'status', 'source', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ContactCreateSerializer
        return ContactListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Contact.objects.select_related('assigned_to', 'company_account')
        # تصفية حسب الحالة
        contact_status = self.request.query_params.get('status')
        if contact_status:
            queryset = queryset.filter(status=contact_status)
        # تصفية حسب المصدر
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        # تصفية حسب المستخدم المسند إليه
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        # تصفية حسب الشركة (الحساب)
        company_account = self.request.query_params.get('company_account')
        if company_account:
            queryset = queryset.filter(company_account_id=company_account)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        return Response({
            'message': 'تم إنشاء جهة الاتصال بنجاح',
            'contact': ContactListSerializer(contact).data,
        }, status=status.HTTP_201_CREATED)


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: تفاصيل جهة الاتصال. PUT/PATCH: تحديث جهة الاتصال (للمسؤولين فقط). DELETE: حذف جهة الاتصال (للمسؤولين فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ContactUpdateSerializer
        return ContactDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Contact.objects.select_related('assigned_to', 'company_account')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        return Response({
            'message': 'تم تحديث جهة الاتصال بنجاح',
            'contact': ContactDetailSerializer(contact).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# واجهات فرص البيع
# =============================================

class LeadListView(generics.ListCreateAPIView):
    """GET: عرض قائمة فرص البيع مع التصفية. POST: إنشاء فرصة بيع (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'contact__first_name', 'contact__last_name', 'contact__company']
    ordering_fields = ['title', 'value', 'probability', 'status', 'pipeline_stage', 'expected_close_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LeadCreateSerializer
        return LeadListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Lead.objects.select_related('contact', 'assigned_to')
        # تصفية حسب الحالة
        lead_status = self.request.query_params.get('status')
        if lead_status:
            queryset = queryset.filter(status=lead_status)
        # تصفية حسب مرحلة خط المبيعات
        pipeline_stage = self.request.query_params.get('pipeline_stage')
        if pipeline_stage:
            queryset = queryset.filter(pipeline_stage=pipeline_stage)
        # تصفية حسب المستخدم المسند إليه
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = serializer.save()
        return Response({
            'message': 'تم إنشاء فرصة البيع بنجاح',
            'lead': LeadListSerializer(lead).data,
        }, status=status.HTTP_201_CREATED)


class LeadDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل فرصة البيع. PUT/PATCH: تحديث فرصة البيع (للمسؤولين فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return LeadUpdateSerializer
        return LeadListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Lead.objects.select_related('contact', 'assigned_to')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        lead = serializer.save()
        return Response({
            'message': 'تم تحديث فرصة البيع بنجاح',
            'lead': LeadListSerializer(lead).data,
        })


class LeadDetailWithActivitiesView(views.APIView):
    """GET: تفاصيل فرصة البيع الكاملة مع جميع الأنشطة والجدول الزمني."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            lead = Lead.objects.select_related(
                'contact', 'contact__company_account', 'assigned_to'
            ).get(pk=pk)
        except Lead.DoesNotExist:
            return Response(
                {'error': 'فرصة البيع غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeadDetailWithActivitiesSerializer(lead)
        return Response(serializer.data)


class LeadChangeStatusView(views.APIView):
    """POST: تغيير حالة فرصة البيع (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            lead = Lead.objects.select_related('contact', 'assigned_to').get(pk=pk)
        except Lead.DoesNotExist:
            return Response(
                {'error': 'فرصة البيع غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LeadChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        pipeline_stage = serializer.validated_data.get('pipeline_stage')
        lost_reason = serializer.validated_data.get('lost_reason', '')

        lead.status = new_status
        if pipeline_stage:
            lead.pipeline_stage = pipeline_stage
        if new_status == 'lost':
            lead.lost_reason = lost_reason
            if not pipeline_stage:
                lead.pipeline_stage = 'closed_lost'
        if new_status == 'won' and not pipeline_stage:
            lead.pipeline_stage = 'closed_won'
        lead.save()

        return Response({
            'message': 'تم تغيير حالة فرصة البيع بنجاح',
            'lead': LeadListSerializer(lead).data,
        })


# =============================================
# واجهات أنشطة الفرص
# =============================================

class LeadActivityListView(generics.ListCreateAPIView):
    """GET: عرض قائمة أنشطة الفرص. POST: إنشاء نشاط فرصة (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject', 'description']
    ordering_fields = ['subject', 'activity_type', 'scheduled_at', 'completed', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LeadActivityCreateSerializer
        return LeadActivityListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = LeadActivity.objects.select_related('lead', 'completed_by')
        # تصفية حسب فرصة البيع (من معرف المسار أولاً)
        lead = self.kwargs.get('pk')
        if lead:
            queryset = queryset.filter(lead_id=lead)
        elif self.request.query_params.get('lead'):
            queryset = queryset.filter(lead_id=self.request.query_params.get('lead'))
        # تصفية حسب نوع النشاط
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        # تصفية حسب الحالة (مكتمل / غير مكتمل)
        completed = self.request.query_params.get('completed')
        if completed is not None:
            queryset = queryset.filter(completed=completed.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity = serializer.save()
        return Response({
            'message': 'تم إنشاء نشاط الفرصة بنجاح',
            'activity': LeadActivityListSerializer(activity).data,
        }, status=status.HTTP_201_CREATED)


class LeadActivityCompleteView(views.APIView):
    """POST: تحديد نشاط فرصة كمكتمل (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            activity = LeadActivity.objects.select_related('lead', 'completed_by').get(pk=pk)
        except LeadActivity.DoesNotExist:
            return Response(
                {'error': 'نشاط الفرصة غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if activity.completed:
            return Response(
                {'error': 'هذا النشاط مكتمل مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        activity.completed = True
        activity.completed_by = request.user
        activity.save()

        return Response({
            'message': 'تم تحديد النشاط كمكتمل بنجاح',
            'activity': LeadActivityListSerializer(activity).data,
        })


# =============================================
# واجهات شرائح العملاء
# =============================================

class CustomerSegmentListView(generics.ListCreateAPIView):
    """GET: عرض قائمة شرائح العملاء. POST: إنشاء شريحة عملاء (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'customer_count', 'discount_percentage', 'is_active', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomerSegmentCreateSerializer
        return CustomerSegmentListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = CustomerSegment.objects.all()
        # تصفية حسب الحالة (نشط / غير نشط)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        segment = serializer.save()
        return Response({
            'message': 'تم إنشاء شريحة العملاء بنجاح',
            'segment': CustomerSegmentListSerializer(segment).data,
        }, status=status.HTTP_201_CREATED)


class CustomerSegmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: تفاصيل شريحة العملاء. PUT/PATCH: تحديث شريحة العملاء (للمسؤولين فقط). DELETE: حذف شريحة العملاء (للمسؤولين فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CustomerSegmentUpdateSerializer
        return CustomerSegmentListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return CustomerSegment.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        segment = serializer.save()
        return Response({
            'message': 'تم تحديث شريحة العملاء بنجاح',
            'segment': CustomerSegmentListSerializer(segment).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================
# واجهات الحملات التسويقية
# =============================================

class CampaignListView(generics.ListCreateAPIView):
    """GET: عرض قائمة الحملات التسويقية. POST: إنشاء حملة تسويقية (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'target_audience']
    ordering_fields = ['name', 'campaign_type', 'status', 'start_date', 'budget', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CampaignCreateSerializer
        return CampaignListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Campaign.objects.select_related('assigned_to').annotate(
            activities_count=Count('activities')
        )
        # تصفية حسب الحالة
        campaign_status = self.request.query_params.get('status')
        if campaign_status:
            queryset = queryset.filter(status=campaign_status)
        # تصفية حسب نوع الحملة
        campaign_type = self.request.query_params.get('campaign_type')
        if campaign_type:
            queryset = queryset.filter(campaign_type=campaign_type)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        campaign = serializer.save()
        return Response({
            'message': 'تم إنشاء الحملة التسويقية بنجاح',
            'campaign': CampaignListSerializer(campaign).data,
        }, status=status.HTTP_201_CREATED)


class CampaignDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل الحملة التسويقية. PUT/PATCH: تحديث الحملة التسويقية (للمسؤولين فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CampaignUpdateSerializer
        return CampaignListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Campaign.objects.select_related('assigned_to')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        campaign = serializer.save()
        return Response({
            'message': 'تم تحديث الحملة التسويقية بنجاح',
            'campaign': CampaignListSerializer(campaign).data,
        })


class CampaignChangeStatusView(views.APIView):
    """POST: تغيير حالة الحملة التسويقية (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            campaign = Campaign.objects.select_related('assigned_to').get(pk=pk)
        except Campaign.DoesNotExist:
            return Response(
                {'error': 'الحملة التسويقية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CampaignChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        campaign.status = serializer.validated_data['status']
        campaign.save()

        return Response({
            'message': 'تم تغيير حالة الحملة التسويقية بنجاح',
            'campaign': CampaignListSerializer(campaign).data,
        })


# =============================================
# واجهات أنشطة الحملات
# =============================================

class CampaignActivityListView(generics.ListCreateAPIView):
    """GET: عرض قائمة أنشطة الحملات. POST: إنشاء نشاط حملة (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description']
    ordering_fields = ['activity_type', 'activity_date', 'created_at']
    ordering = ['-activity_date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CampaignActivityCreateSerializer
        return CampaignActivityListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = CampaignActivity.objects.select_related('campaign', 'contact')
        # تصفية حسب الحملة (من معرف المسار أولاً)
        campaign = self.kwargs.get('pk')
        if campaign:
            queryset = queryset.filter(campaign_id=campaign)
        elif self.request.query_params.get('campaign'):
            queryset = queryset.filter(campaign_id=self.request.query_params.get('campaign'))
        # تصفية حسب نوع النشاط
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity = serializer.save()
        return Response({
            'message': 'تم إنشاء نشاط الحملة بنجاح',
            'activity': CampaignActivityListSerializer(activity).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# واجهة تحويل فرصة بيع إلى عميل
# =============================================

class LeadConvertToCustomerView(views.APIView):
    """POST: تحويل فرصة بيع إلى عميل (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            lead = Lead.objects.select_related('contact', 'assigned_to').get(pk=pk)
        except Lead.DoesNotExist:
            return Response(
                {'error': 'فرصة البيع غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # التحقق من إمكانية التحويل
        serializer = LeadConvertSerializer(data={}, context={'lead': lead})
        serializer.is_valid(raise_exception=True)

        # إنشاء عميل جديد من بيانات جهة الاتصال
        from sales.models import Customer

        customer = Customer.objects.create(
            name=f'{lead.contact.first_name} {lead.contact.last_name}'.strip(),
            email=lead.contact.email or '',
            phone=lead.contact.phone or lead.contact.mobile or '',
            address='',
        )

        # تحديث حالة الفرصة إلى "مكتسب"
        if lead.status != 'won':
            lead.status = 'won'
            lead.pipeline_stage = 'closed_won'
            lead.save(update_fields=['status', 'pipeline_stage', 'updated_at'])

        return Response({
            'message': 'تم تحويل فرصة البيع إلى عميل بنجاح',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'is_active': customer.is_active,
                'created_at': customer.created_at,
            },
            'lead': LeadListSerializer(lead).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# واجهة بيانات قمع خط المبيعات
# =============================================

class PipelineFunnelView(views.APIView):
    """GET: بيانات قمع خط المبيعات مجمعة حسب المراحل."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # ترتيب مراحل القمع
        stage_order = ['lead', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
        stage_labels = dict(Lead.PIPELINE_STAGE_CHOICES)

        # تجميع البيانات حسب المرحلة - استعلام مجمّع واحد بدلاً من 18 استعلاماً
        pipeline_data = Lead.objects.values('pipeline_stage').annotate(
            count=Count('id'),
            total_value=Coalesce(Sum('value'), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
            weighted_value=Coalesce(Sum(F('value') * F('probability') / 100), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2))
        ).order_by('pipeline_stage')

        pipeline_map = {p['pipeline_stage']: p for p in pipeline_data}

        funnel_data = []
        prev_count = None

        for stage in stage_order:
            data = pipeline_map.get(stage, {'count': 0, 'total_value': 0, 'weighted_value': 0})
            count = data['count']
            total_value = data['total_value']
            weighted_value = data['weighted_value']

            # حساب معدل التحويل بين المراحل
            conversion_rate = None
            if prev_count is not None and prev_count > 0:
                conversion_rate = round((count / prev_count) * 100, 1)

            funnel_data.append({
                'stage': stage,
                'stage_display': stage_labels.get(stage, stage),
                'count': count,
                'total_value': total_value,
                'weighted_value': weighted_value,
                'conversion_rate': conversion_rate,
            })

            prev_count = count

        serializer = PipelineFunnelSerializer(funnel_data, many=True)
        return Response(serializer.data)


# =============================================
# واجهة التنبؤ بالمبيعات
# =============================================

class SalesForecastView(views.APIView):
    """GET: التنبؤ بالمبيعات للأشهر القادمة."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        months = int(request.query_params.get('months', 3))
        if months < 1 or months > 24:
            months = 3

        today = timezone.now().date()
        forecast_data = []

        for i in range(months):
            # حساب بداية الشهر المستهدف
            target_month = today.month + i
            target_year = today.year
            while target_month > 12:
                target_month -= 12
                target_year += 1
            target_date = date(target_year, target_month, 1)

            # بداية ونهاية الشهر المستهدف
            if target_date.month == 12:
                end_date = target_date.replace(year=target_date.year + 1, month=1, day=1)
            else:
                end_date = target_date.replace(month=target_date.month + 1, day=1)

            leads_in_month = Lead.objects.filter(
                expected_close_date__gte=target_date,
                expected_close_date__lt=end_date,
                status__in=('new', 'contacted', 'qualified', 'proposal', 'negotiation'),
            )

            expected_value = leads_in_month.aggregate(
                total=Coalesce(
                    Sum(F('value') * F('probability') / 100),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total']

            leads_count = leads_in_month.count()
            avg_probability = None
            if leads_count > 0:
                total_prob = leads_in_month.aggregate(
                    s=Coalesce(Sum('probability'), Value(0))
                )['s']
                avg_probability = round(total_prob / leads_count, 1)

            month_name = target_date.strftime('%Y-%m')

            forecast_data.append({
                'month': month_name,
                'expected_value': expected_value,
                'leads_count': leads_count,
                'avg_probability': avg_probability,
            })

        serializer = SalesForecastSerializer(forecast_data, many=True)
        return Response(serializer.data)


# =============================================
# واجهة تحليلات مراحل المبيعات
# =============================================

class SalesStageAnalyticsView(views.APIView):
    """GET: تحليلات شاملة لمراحل خط المبيعات - متوسط الأيام، معدل الفوز، متوسط قيمة الصفقة، أسباب الفقدان، الاتجاه الشهري."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stage_order = ['lead', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
        stage_labels = dict(Lead.PIPELINE_STAGE_CHOICES)

        # --- 1. تحليلات كل مرحلة ---
        stage_analytics = []
        stage_aggregates = Lead.objects.values('pipeline_stage').annotate(
            count=Count('id'),
            avg_value=Coalesce(
                Avg('value'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        )
        stage_map = {s['pipeline_stage']: s for s in stage_aggregates}

        for stage_key in stage_order:
            data = stage_map.get(stage_key, {'count': 0, 'avg_value': Decimal('0.00')})
            count = data['count']
            avg_deal_value = data['avg_value']

            # حساب متوسط الأيام في المرحلة (الفرق بين created_at و updated_at)
            avg_days = None
            if count > 0:
                leads_in_stage = Lead.objects.filter(pipeline_stage=stage_key)
                # حساب الفرق بالأيام بين الإنشاء وآخر تحديث
                day_diffs = leads_in_stage.annotate(
                    day_diff=ExpressionWrapper(
                        F('updated_at') - F('created_at'),
                        output_field=DurationField()
                    )
                ).values_list('day_diff', flat=True)

                valid_diffs = [d for d in day_diffs if d is not None]
                if valid_diffs:
                    total_days = sum(d.days for d in valid_diffs)
                    avg_days = round(total_days / len(valid_diffs), 1)

            # حساب معدل الفوز لكل مرحلة
            win_rate = None
            if count > 0 and stage_key not in ('closed_won', 'closed_lost'):
                # من الفرص في هذه المرحلة، كم انتقلت إلى closed_won
                won_count = Lead.objects.filter(
                    pipeline_stage=stage_key
                ).count()
                total_in_stage = count
                if total_in_stage > 0:
                    # حساب معدل الفوز الإجمالي كنسبة من إجمالي الفرص
                    total_won = Lead.objects.filter(status='won').count()
                    total_all = Lead.objects.count()
                    if total_all > 0:
                        win_rate = round((total_won / total_all) * 100, 1)
            elif stage_key == 'closed_won':
                total_won = Lead.objects.filter(status='won').count()
                total_all = Lead.objects.count()
                if total_all > 0:
                    win_rate = round((total_won / total_all) * 100, 1)

            stage_analytics.append({
                'stage': stage_key,
                'stage_display': stage_labels.get(stage_key, stage_key),
                'count': count,
                'avg_days_in_stage': avg_days,
                'win_rate': win_rate,
                'avg_deal_value': avg_deal_value,
            })

        # --- 2. إجمالي القيمة المفقودة مع تفصيل الأسباب ---
        lost_leads = Lead.objects.filter(status='lost')
        total_lost_value = lost_leads.aggregate(
            total=Coalesce(
                Sum('value'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total']

        lost_reasons = lost_leads.values('lost_reason').annotate(
            count=Count('id'),
            total_value=Coalesce(
                Sum('value'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        ).order_by('-total_value')

        lost_reasons_breakdown = []
        for lr in lost_reasons:
            reason = lr['lost_reason'] or 'غير محدد'
            lost_reasons_breakdown.append({
                'reason': reason,
                'count': lr['count'],
                'total_value': lr['total_value'],
            })

        # --- 3. الاتجاه الشهري للمبيعات (آخر 12 شهراً) ---
        today = timezone.now().date()
        monthly_trend = []

        for i in range(11, -1, -1):
            month_date = today.replace(day=1)
            for _ in range(i):
                if month_date.month == 1:
                    month_date = month_date.replace(year=month_date.year - 1, month=12)
                else:
                    month_date = month_date.replace(month=month_date.month - 1)

            # بداية ونهاية الشهر
            start_date = month_date
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1, day=1)

            # الصفقات الرابحة في هذا الشهر
            won_leads_month = Lead.objects.filter(
                status='won',
                updated_at__gte=start_date,
                updated_at__lt=end_date,
            )
            won_count = won_leads_month.count()
            won_value = won_leads_month.aggregate(
                total=Coalesce(
                    Sum('value'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total']

            # الصفقات المفقودة في هذا الشهر
            lost_leads_month = Lead.objects.filter(
                status='lost',
                updated_at__gte=start_date,
                updated_at__lt=end_date,
            )
            lost_count = lost_leads_month.count()
            lost_value_month = lost_leads_month.aggregate(
                total=Coalesce(
                    Sum('value'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total']

            month_label = start_date.strftime('%Y-%m')

            monthly_trend.append({
                'month': month_label,
                'won_deals': won_count,
                'won_value': won_value,
                'lost_deals': lost_count,
                'lost_value': lost_value_month,
                'net_value': won_value - lost_value_month,
            })

        # --- تجميع كل التحليلات ---
        analytics_data = {
            'stage_analytics': stage_analytics,
            'total_lost_value': total_lost_value,
            'lost_reasons_breakdown': lost_reasons_breakdown,
            'monthly_sales_trend': monthly_trend,
        }

        serializer = SalesStageAnalyticsSerializer(analytics_data)
        return Response(serializer.data)


# =============================================
# واجهة أفضل مندوبي المبيعات
# =============================================

class TopRepsView(views.APIView):
    """GET: أفضل مندوبي المبيعات حسب الإيرادات (عدد الصفقات الرابحة، الإيرادات، معدل الفوز)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # تجميع الفرص الرابحة حسب المندوب المسند إليه
        won_aggregates = Lead.objects.filter(
            status='won',
            assigned_to__isnull=False,
        ).values('assigned_to').annotate(
            deals=Count('id'),
            revenue=Coalesce(
                Sum('value'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        ).order_by('-revenue')[:10]

        # تجميع إجمالي الفرص (غير المكتسبة فقط) لكل مندوب لحساب معدل الفوز
        total_aggregates = Lead.objects.filter(
            assigned_to__isnull=False,
        ).values('assigned_to').annotate(
            total_leads=Count('id'),
            won_leads=Count(
                Case(
                    When(status='won', then=1),
                )
            ),
        )
        total_map = {t['assigned_to']: t for t in total_aggregates}

        # جمع معرفات المستخدمين المطلوبين للاستعلام عن أسمائهم
        user_ids = [w['assigned_to'] for w in won_aggregates]
        # أيضاً إضافة معرفات المستخدمين من total_map الذين قد لا يكونوا في won_aggregates
        for uid in total_map:
            if uid not in user_ids:
                user_ids.append(uid)

        from users.models import User
        users_map = {
            u.id: u
            for u in User.objects.filter(id__in=user_ids)
        }

        reps_data = []
        for w in won_aggregates:
            user = users_map.get(w['assigned_to'])
            if not user:
                continue

            total = total_map.get(w['assigned_to'], {})
            total_leads = total.get('total_leads', 0)
            won_leads = total.get('won_leads', 0)

            win_rate = 0.0
            if total_leads > 0:
                win_rate = round((won_leads / total_leads) * 100, 1)

            reps_data.append({
                'name': user.get_full_name() or user.username,
                'deals': w['deals'],
                'revenue': float(w['revenue']),
                'win_rate': win_rate,
            })

        return Response(reps_data)


# =============================================
# واجهة توزيع مصادر الفرص
# =============================================

class LeadSourceDistributionView(views.APIView):
    """GET: تحليلات مصادر الفرص - عدد الفرص، عدد المحولات، الإيرادات لكل مصدر."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        source_labels = dict(Lead.SOURCE_CHOICES)
        source_arabic_labels = dict(Lead.SOURCE_CHOICES)

        # تجميع البيانات حسب المصدر
        source_aggregates = Lead.objects.values('source').annotate(
            leads=Count('id'),
            converted=Count(
                Case(
                    When(status='won', then=1),
                )
            ),
            revenue=Coalesce(
                Sum(
                    Case(
                        When(status='won', then=F('value')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )
                ),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        ).order_by('-leads')

        distribution_data = []
        for s in source_aggregates:
            source_key = s['source']
            display_name = source_labels.get(source_key, source_key or 'غير محدد')

            distribution_data.append({
                'name': display_name,
                'leads': s['leads'],
                'converted': s['converted'],
                'revenue': float(s['revenue']),
            })

        return Response({
            'sources': distribution_data,
            'labels': source_arabic_labels,
        })


# =============================================
# واجهة تصدير إدارة علاقات العملاء
# =============================================

class CRMExportView(views.APIView):
    """GET: تصدير بيانات إدارة علاقات العملاء إلى Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        export_type = self.request.query_params.get('type', 'leads')

        if export_type == 'contacts':
            queryset = Contact.objects.select_related('assigned_to', 'company_account').order_by('-created_at')
            columns = [
                ('full_name', 'الاسم الكامل', 30),
                ('email', 'البريد الإلكتروني', 30),
                ('phone', 'الهاتف', 18),
                ('mobile', 'الهاتف المحمول', 18),
                ('company', 'الشركة', 25),
                ('position', 'المنصب', 25),
                ('source', 'المصدر', 20),
                ('status', 'الحالة', 15),
                ('assigned_to', 'مسند إلى', 20),
                ('created_at', 'تاريخ الإنشاء', 20),
            ]
            data = []
            for c in queryset:
                company_name = c.company_account.name if c.company_account else c.company
                data.append({
                    'full_name': f'{c.first_name} {c.last_name}',
                    'email': c.email,
                    'phone': c.phone,
                    'mobile': c.mobile,
                    'company': company_name,
                    'position': c.position,
                    'source': c.get_source_display() if c.source else '',
                    'status': c.get_status_display(),
                    'assigned_to': c.assigned_to.username if c.assigned_to else '',
                    'created_at': str(c.created_at.date()) if c.created_at else '',
                })
            return export_to_excel(data, columns, 'جهات الاتصال', 'contacts.xlsx')
        elif export_type == 'companies':
            queryset = Company.objects.select_related('assigned_to').order_by('-created_at')
            columns = [
                ('name', 'اسم الشركة', 30),
                ('name_en', 'الاسم بالإنجليزية', 30),
                ('industry', 'القطاع الصناعي', 25),
                ('city', 'المدينة', 20),
                ('country', 'البلد', 20),
                ('company_type', 'نوع الشركة', 15),
                ('annual_revenue', 'الإيرادات السنوية', 18),
                ('employee_count', 'عدد الموظفين', 12),
                ('phone', 'الهاتف', 18),
                ('email', 'البريد الإلكتروني', 30),
                ('is_active', 'نشط', 8),
                ('assigned_to', 'مسند إلى', 20),
                ('created_at', 'تاريخ الإنشاء', 20),
            ]
            data = []
            for c in queryset:
                data.append({
                    'name': c.name,
                    'name_en': c.name_en,
                    'industry': c.industry,
                    'city': c.city,
                    'country': c.country,
                    'company_type': c.get_company_type_display(),
                    'annual_revenue': str(c.annual_revenue),
                    'employee_count': c.employee_count,
                    'phone': c.phone,
                    'email': c.email,
                    'is_active': 'نعم' if c.is_active else 'لا',
                    'assigned_to': c.assigned_to.username if c.assigned_to else '',
                    'created_at': str(c.created_at.date()) if c.created_at else '',
                })
            return export_to_excel(data, columns, 'الشركات', 'companies.xlsx')
        else:
            queryset = Lead.objects.select_related('contact', 'assigned_to').order_by('-created_at')
            columns = [
                ('title', 'العنوان', 30),
                ('contact_name', 'جهة الاتصال', 25),
                ('contact_email', 'البريد الإلكتروني', 25),
                ('value', 'القيمة', 15),
                ('probability', 'نسبة الاحتمالية', 15),
                ('weighted_value', 'القيمة المرجحة', 15),
                ('expected_close_date', 'تاريخ الإغلاق المتوقع', 18),
                ('status', 'الحالة', 15),
                ('pipeline_stage', 'مرحلة خط المبيعات', 20),
                ('assigned_to', 'مسند إلى', 20),
                ('source', 'المصدر', 20),
                ('created_at', 'تاريخ الإنشاء', 20),
            ]
            data = []
            for l in queryset:
                data.append({
                    'title': l.title,
                    'contact_name': f'{l.contact.first_name} {l.contact.last_name}' if l.contact else '',
                    'contact_email': l.contact.email if l.contact else '',
                    'value': str(l.value),
                    'probability': f'{l.probability}%',
                    'weighted_value': str(l.value * l.probability / 100) if l.value and l.probability else '0.00',
                    'expected_close_date': str(l.expected_close_date) if l.expected_close_date else '',
                    'status': l.get_status_display(),
                    'pipeline_stage': l.get_pipeline_stage_display(),
                    'assigned_to': l.assigned_to.username if l.assigned_to else '',
                    'source': l.get_source_display() if l.source else '',
                    'created_at': str(l.created_at.date()) if l.created_at else '',
                })
            return export_to_excel(data, columns, 'فرص البيع', 'leads.xlsx')


# =============================================
# واجهات سياسات اتفاقية مستوى الخدمة (SLA)
# =============================================

class SLAPolicyListView(generics.ListCreateAPIView):
    """GET: عرض قائمة سياسات SLA. POST: إنشاء سياسة SLA (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority', 'first_response_time', 'resolution_time', 'is_active', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SLAPolicyCreateSerializer
        return SLAPolicyListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = SLAPolicy.objects.annotate(
            tickets_count=Count('tickets')
        )
        # تصفية حسب الأولوية
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        # تصفية حسب حالة التفعيل
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sla_policy = serializer.save()
        return Response({
            'message': 'تم إنشاء سياسة SLA بنجاح',
            'sla_policy': SLAPolicyListSerializer(sla_policy).data,
        }, status=status.HTTP_201_CREATED)


class SLAPolicyDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل سياسة SLA. PUT/PATCH: تحديث سياسة SLA (للمسؤولين فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return SLAPolicyUpdateSerializer
        return SLAPolicyListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return SLAPolicy.objects.annotate(
            tickets_count=Count('tickets')
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        sla_policy = serializer.save()
        return Response({
            'message': 'تم تحديث سياسة SLA بنجاح',
            'sla_policy': SLAPolicyListSerializer(sla_policy).data,
        })


class SLAPolicyDeleteView(views.APIView):
    """DELETE: حذف سياسة SLA (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            sla_policy = SLAPolicy.objects.get(pk=pk)
        except SLAPolicy.DoesNotExist:
            return Response(
                {'error': 'سياسة SLA غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        sla_policy.delete()
        return Response({'message': 'تم حذف سياسة SLA بنجاح'})


# =============================================
# واجهات تذاكر الدعم
# =============================================

class TicketListView(generics.ListCreateAPIView):
    """GET: عرض قائمة تذاكر الدعم مع التصفية. POST: إنشاء تذكرة دعم (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ticket_number', 'subject', 'description', 'contact__first_name', 'contact__last_name']
    ordering_fields = ['ticket_number', 'subject', 'status', 'priority', 'category', 'assigned_to', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TicketCreateSerializer
        return TicketListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Ticket.objects.select_related(
            'contact', 'company', 'assigned_to', 'sla_policy'
        ).annotate(
            comments_count=Count('comments')
        )
        # تصفية حسب الحالة
        ticket_status = self.request.query_params.get('status')
        if ticket_status:
            queryset = queryset.filter(status=ticket_status)
        # تصفية حسب الأولوية
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        # تصفية حسب التصنيف
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        # تصفية حسب المستخدم المسند إليه
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        # تصفية حسب الشركة
        company = self.request.query_params.get('company')
        if company:
            queryset = queryset.filter(company_id=company)
        # تصفية حسب سياسة SLA
        sla_policy = self.request.query_params.get('sla_policy')
        if sla_policy:
            queryset = queryset.filter(sla_policy_id=sla_policy)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response({
            'message': 'تم إنشاء تذكرة الدعم بنجاح',
            'ticket': TicketListSerializer(ticket).data,
        }, status=status.HTTP_201_CREATED)


class TicketDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل التذكرة الكاملة مع التعليقات. PUT/PATCH: تحديث التذكرة (للمسؤولين فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TicketUpdateSerializer
        return TicketDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Ticket.objects.select_related(
            'contact', 'company', 'assigned_to', 'sla_policy', 'created_by'
        ).annotate(
            comments_count=Count('comments')
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response({
            'message': 'تم تحديث تذكرة الدعم بنجاح',
            'ticket': TicketDetailSerializer(ticket).data,
        })


class TicketDeleteView(views.APIView):
    """DELETE: حذف تذكرة دعم (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response(
                {'error': 'تذكرة الدعم غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        ticket.delete()
        return Response({'message': 'تم حذف تذكرة الدعم بنجاح'})


class TicketAssignView(views.APIView):
    """POST: تسند تذكرة إلى مستخدم (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            ticket = Ticket.objects.select_related(
                'contact', 'company', 'assigned_to', 'sla_policy'
            ).get(pk=pk)
        except Ticket.DoesNotExist:
            return Response(
                {'error': 'تذكرة الدعم غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TicketAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from users.models import User
        try:
            user = User.objects.get(pk=serializer.validated_data['assigned_to'])
        except User.DoesNotExist:
            return Response(
                {'error': 'المستخدم غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        ticket.assigned_to = user
        if not ticket.first_response_at:
            ticket.first_response_at = timezone.now()
        ticket.save()

        return Response({
            'message': 'تم تسند التذكرة بنجاح',
            'ticket': TicketDetailSerializer(ticket).data,
        })


class TicketResolveView(views.APIView):
    """POST: حل تذكرة دعم (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            ticket = Ticket.objects.select_related(
                'contact', 'company', 'assigned_to', 'sla_policy'
            ).get(pk=pk)
        except Ticket.DoesNotExist:
            return Response(
                {'error': 'تذكرة الدعم غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ticket.status in ('resolved', 'closed'):
            return Response(
                {'error': 'هذه التذكرة تم حلها أو إغلاقها مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TicketResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket.status = 'resolved'
        ticket.resolution = serializer.validated_data['resolution']
        ticket.resolved_at = timezone.now()
        ticket.save()

        return Response({
            'message': 'تم حل التذكرة بنجاح',
            'ticket': TicketDetailSerializer(ticket).data,
        })


class TicketStatsView(views.APIView):
    """GET: إحصائيات التذاكر - عد حسب الحالة، متوسط وقت الحل."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # عد حسب الحالة
        status_counts = Ticket.objects.values('status').annotate(
            count=Count('id')
        )
        status_map = {s['status']: s['count'] for s in status_counts}

        # متوسط وقت الحل (بالدقائق)
        avg_resolution_time = None
        resolved_tickets = Ticket.objects.filter(
            status='resolved',
            resolved_at__isnull=False,
        )
        if resolved_tickets.count() > 0:
            total_minutes = 0
            count = 0
            for ticket in resolved_tickets:
                if ticket.created_at and ticket.resolved_at:
                    diff = ticket.resolved_at - ticket.created_at
                    total_minutes += diff.total_seconds() / 60
                    count += 1
            if count > 0:
                avg_resolution_time = round(total_minutes / count, 1)

        # عد حسب الأولوية
        priority_counts = Ticket.objects.values('priority').annotate(
            count=Count('id')
        )
        priority_labels = dict(Ticket.PRIORITY_CHOICES)
        tickets_by_priority = {
            priority_labels.get(p['priority'], p['priority']): p['count']
            for p in priority_counts
        }

        # عد حسب التصنيف
        category_counts = Ticket.objects.values('category').annotate(
            count=Count('id')
        )
        category_labels = dict(Ticket.CATEGORY_CHOICES)
        tickets_by_category = {
            category_labels.get(c['category'], c['category']): c['count']
            for c in category_counts
        }

        stats_data = {
            'total_tickets': Ticket.objects.count(),
            'new_tickets': status_map.get('new', 0),
            'in_progress_tickets': status_map.get('in_progress', 0),
            'pending_customer_tickets': status_map.get('pending_customer', 0),
            'resolved_tickets': status_map.get('resolved', 0),
            'closed_tickets': status_map.get('closed', 0),
            'reopened_tickets': status_map.get('reopened', 0),
            'avg_resolution_time_minutes': avg_resolution_time,
            'tickets_by_priority': tickets_by_priority,
            'tickets_by_category': tickets_by_category,
        }

        serializer = TicketStatsSerializer(stats_data)
        return Response(serializer.data)


# =============================================
# واجهات تعليقات التذاكر
# =============================================

class TicketCommentListView(generics.ListCreateAPIView):
    """GET: عرض قائمة تعليقات تذكرة. POST: إضافة تعليق (للمسؤولين فقط)."""

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TicketCommentCreateSerializer
        return TicketCommentListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        ticket_id = self.kwargs.get('ticket_id')
        queryset = TicketComment.objects.select_related('created_by').filter(
            ticket_id=ticket_id
        )
        # تصفية التعليقات الداخلية فقط
        is_internal = self.request.query_params.get('is_internal')
        if is_internal is not None:
            queryset = queryset.filter(is_internal=is_internal.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إضافة التعليق بنجاح',
            'comment': TicketCommentListSerializer(comment).data,
        }, status=status.HTTP_201_CREATED)


# =============================================
# واجهات عروض الأسعار
# =============================================

class QuotationListView(generics.ListCreateAPIView):
    """GET: عرض قائمة عروض الأسعار. POST: إنشاء عرض سعر (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['quote_number', 'company__name', 'contact__first_name', 'contact__last_name']
    ordering_fields = ['quote_number', 'status', 'valid_until', 'total_amount', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuotationCreateSerializer
        return QuotationListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Quotation.objects.select_related(
            'company', 'contact', 'lead', 'created_by'
        ).annotate(
            items_count=Count('items')
        )
        # تصفية حسب الحالة
        quote_status = self.request.query_params.get('status')
        if quote_status:
            queryset = queryset.filter(status=quote_status)
        # تصفية حسب الشركة
        company = self.request.query_params.get('company')
        if company:
            queryset = queryset.filter(company_id=company)
        # تصفية حسب التحويل لأمر بيع
        converted = self.request.query_params.get('converted_to_order')
        if converted is not None:
            queryset = queryset.filter(converted_to_order=converted.lower() == 'true')
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quotation = serializer.save()
        return Response({
            'message': 'تم إنشاء عرض السعر بنجاح',
            'quotation': QuotationListSerializer(quotation).data,
        }, status=status.HTTP_201_CREATED)


class QuotationDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل عرض السعر الكاملة مع البنود. PUT/PATCH: تحديث عرض السعر (للمسؤولين فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return QuotationUpdateSerializer
        return QuotationDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Quotation.objects.select_related(
            'company', 'contact', 'lead', 'created_by'
        ).annotate(
            items_count=Count('items')
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        quotation = serializer.save()
        return Response({
            'message': 'تم تحديث عرض السعر بنجاح',
            'quotation': QuotationDetailSerializer(quotation).data,
        })


class QuotationDeleteView(views.APIView):
    """DELETE: حذف عرض سعر (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            quotation = Quotation.objects.get(pk=pk)
        except Quotation.DoesNotExist:
            return Response(
                {'error': 'عرض السعر غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )
        quotation.delete()
        return Response({'message': 'تم حذف عرض السعر بنجاح'})


class QuotationConvertView(views.APIView):
    """POST: تحويل عرض سعر إلى أمر بيع (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.select_related(
                'company', 'contact', 'lead', 'created_by'
            ).get(pk=pk)
        except Quotation.DoesNotExist:
            return Response(
                {'error': 'عرض السعر غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if quotation.converted_to_order:
            return Response(
                {'error': 'تم تحويل هذا العرض إلى أمر بيع مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quotation.status not in ('accepted', 'sent'):
            return Response(
                {'error': 'يمكن تحويل العروض المقبولة أو المرسلة فقط'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quotation.converted_to_order = True
        quotation.status = 'accepted'
        quotation.save()

        return Response({
            'message': 'تم تحويل عرض السعر إلى أمر بيع بنجاح',
            'quotation': QuotationDetailSerializer(quotation).data,
        })


# =============================================
# واجهات العمولات
# =============================================

class CommissionListView(generics.ListCreateAPIView):
    """GET: عرض قائمة العمولات. POST: إنشاء عمولة (للمسؤولين فقط)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['reference_number', 'salesperson__username', 'salesperson__first_name', 'salesperson__last_name']
    ordering_fields = ['salesperson', 'sale_type', 'status', 'commission_amount', 'period_year', 'period_month', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommissionCreateSerializer
        return CommissionListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Commission.objects.select_related('salesperson')
        # تصفية حسب الحالة
        commission_status = self.request.query_params.get('status')
        if commission_status:
            queryset = queryset.filter(status=commission_status)
        # تصفية حسب المندوب
        salesperson = self.request.query_params.get('salesperson')
        if salesperson:
            queryset = queryset.filter(salesperson_id=salesperson)
        # تصفية حسب نوع البيع
        sale_type = self.request.query_params.get('sale_type')
        if sale_type:
            queryset = queryset.filter(sale_type=sale_type)
        # تصفية حسب الفترة
        period_month = self.request.query_params.get('period_month')
        if period_month:
            queryset = queryset.filter(period_month=period_month)
        period_year = self.request.query_params.get('period_year')
        if period_year:
            queryset = queryset.filter(period_year=period_year)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        commission = serializer.save()
        return Response({
            'message': 'تم إنشاء العمولة بنجاح',
            'commission': CommissionListSerializer(commission).data,
        }, status=status.HTTP_201_CREATED)


class CommissionDetailView(generics.RetrieveUpdateAPIView):
    """GET: تفاصيل العمولة. PUT/PATCH: تحديث العمولة (للمسؤولين فقط)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CommissionUpdateSerializer
        return CommissionListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Commission.objects.select_related('salesperson')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        commission = serializer.save()
        return Response({
            'message': 'تم تحديث العمولة بنجاح',
            'commission': CommissionListSerializer(commission).data,
        })


class CommissionDeleteView(views.APIView):
    """DELETE: حذف عمولة (للمسؤولين فقط)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            commission = Commission.objects.get(pk=pk)
        except Commission.DoesNotExist:
            return Response(
                {'error': 'العمولة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        commission.delete()
        return Response({'message': 'تم حذف العمولة بنجاح'})


class CommissionStatsView(views.APIView):
    """GET: إحصائيات العمولات - إجمالي المعلق، المعتمد، المدفوع حسب الفترة."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # إجمالي حسب الحالة
        total_pending = Commission.objects.filter(status='pending').aggregate(
            total=Coalesce(
                Sum('commission_amount'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total']

        total_approved = Commission.objects.filter(status='approved').aggregate(
            total=Coalesce(
                Sum('commission_amount'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total']

        total_paid = Commission.objects.filter(status='paid').aggregate(
            total=Coalesce(
                Sum('commission_amount'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total']

        total_cancelled = Commission.objects.filter(status='cancelled').aggregate(
            total=Coalesce(
                Sum('commission_amount'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total']

        total_all = Commission.objects.aggregate(
            total=Coalesce(
                Sum('commission_amount'),
                Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total']

        # تفصيل حسب الفترة
        period_year = self.request.query_params.get('period_year')
        period_month = self.request.query_params.get('period_month')

        by_period = []
        if period_year:
            queryset = Commission.objects.filter(period_year=int(period_year))
            if period_month:
                queryset = queryset.filter(period_month=int(period_month))

            period_aggregates = queryset.values('period_month').annotate(
                pending=Coalesce(
                    Sum('commission_amount', filter=Q(status='pending')),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                ),
                approved=Coalesce(
                    Sum('commission_amount', filter=Q(status='approved')),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                ),
                paid=Coalesce(
                    Sum('commission_amount', filter=Q(status='paid')),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                ),
            ).order_by('period_month')

            for p in period_aggregates:
                by_period.append({
                    'month': p['period_month'],
                    'pending': str(p['pending']),
                    'approved': str(p['approved']),
                    'paid': str(p['paid']),
                })

        stats_data = {
            'total_pending': total_pending,
            'total_approved': total_approved,
            'total_paid': total_paid,
            'total_cancelled': total_cancelled,
            'total_all': total_all,
            'by_period': by_period,
        }

        serializer = CommissionStatsSerializer(stats_data)
        return Response(serializer.data)
