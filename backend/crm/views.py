"""
واجهات برمجة التطبيقات (API Views) لوحدة إدارة علاقات العملاء (CRM).
تتعامل مع جهات الاتصال، فرص البيع، أنشطة الفرص، شرائح العملاء، الحملات التسويقية، وأنشطة الحملات والإحصائيات والتصدير.
"""

from decimal import Decimal

from rest_framework import (
    generics, status, permissions, filters, views,
)
from rest_framework.response import Response
from django.db.models import Sum, Count, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    Contact,
    Lead,
    LeadActivity,
    CustomerSegment,
    Campaign,
    CampaignActivity,
)
from .serializers import (
    ContactListSerializer,
    ContactCreateSerializer,
    ContactUpdateSerializer,
    LeadListSerializer,
    LeadCreateSerializer,
    LeadUpdateSerializer,
    LeadChangeStatusSerializer,
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
        queryset = Contact.objects.select_related('assigned_to')
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
        return ContactListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Contact.objects.select_related('assigned_to')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        return Response({
            'message': 'تم تحديث جهة الاتصال بنجاح',
            'contact': ContactListSerializer(contact).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'message': 'تم حذف جهة الاتصال بنجاح'})


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
        # تصفية حسب فرصة البيع
        lead = self.request.query_params.get('lead')
        if lead:
            queryset = queryset.filter(lead_id=lead)
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
        return Response({'message': 'تم حذف شريحة العملاء بنجاح'})


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
        queryset = Campaign.objects.select_related('assigned_to')
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
        # تصفية حسب الحملة
        campaign = self.request.query_params.get('campaign')
        if campaign:
            queryset = queryset.filter(campaign_id=campaign)
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
# واجهة تصدير إدارة علاقات العملاء
# =============================================

class CRMExportView(views.APIView):
    """GET: تصدير بيانات إدارة علاقات العملاء إلى Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        export_type = self.request.query_params.get('type', 'leads')

        if export_type == 'contacts':
            queryset = Contact.objects.select_related('assigned_to').order_by('-created_at')
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
                data.append({
                    'full_name': f'{c.first_name} {c.last_name}',
                    'email': c.email,
                    'phone': c.phone,
                    'mobile': c.mobile,
                    'company': c.company,
                    'position': c.position,
                    'source': c.get_source_display() if c.source else '',
                    'status': c.get_status_display(),
                    'assigned_to': c.assigned_to.username if c.assigned_to else '',
                    'created_at': str(c.created_at.date()) if c.created_at else '',
                })
            return export_to_excel(data, columns, 'جهات الاتصال', 'contacts.xlsx')
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
