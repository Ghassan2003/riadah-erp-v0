"""
المسلسلات (Serializers) لوحدة إدارة علاقات العملاء (CRM).
تتعامل مع تحويل بيانات الشركات، جهات الاتصال، فرص البيع، أنشطة الفرص، شرائح العملاء، الحملات التسويقية، وأنشطة الحملات.
"""

from rest_framework import serializers
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


# =============================================
# مسلسلات الشركات / الحسابات
# =============================================

class CompanyListSerializer(serializers.ModelSerializer):
    """مسلسل خفيف لعرض قائمة الشركات."""

    company_type_display = serializers.CharField(source='get_company_type_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    contacts_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Company
        fields = (
            'id', 'name', 'name_en', 'industry', 'website', 'phone', 'email',
            'city', 'country', 'company_type', 'company_type_display',
            'annual_revenue', 'employee_count', 'assigned_to', 'assigned_to_name',
            'is_active', 'contacts_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class CompanyCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء شركة."""

    class Meta:
        model = Company
        fields = (
            'name', 'name_en', 'industry', 'website', 'phone', 'email',
            'address', 'city', 'country', 'company_type', 'annual_revenue',
            'employee_count', 'assigned_to', 'is_active', 'notes',
        )


class CompanyUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث شركة."""

    class Meta:
        model = Company
        fields = (
            'name', 'name_en', 'industry', 'website', 'phone', 'email',
            'address', 'city', 'country', 'company_type', 'annual_revenue',
            'employee_count', 'assigned_to', 'is_active', 'notes',
        )


class CompanyDetailSerializer(serializers.ModelSerializer):
    """مسلسل تفصيلي لعرض بيانات الشركة الكاملة."""

    company_type_display = serializers.CharField(source='get_company_type_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    contacts_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Company
        fields = (
            'id', 'name', 'name_en', 'industry', 'website', 'phone', 'email',
            'address', 'city', 'country', 'company_type', 'company_type_display',
            'annual_revenue', 'employee_count', 'assigned_to', 'assigned_to_name',
            'is_active', 'notes', 'contacts_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


# =============================================
# مسلسلات جهات الاتصال
# =============================================

class ContactListSerializer(serializers.ModelSerializer):
    """مسلسل خفيف لعرض قائمة جهات الاتصال."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    full_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = (
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'mobile', 'company', 'company_account', 'company_name', 'position',
            'source', 'source_display', 'status', 'status_display',
            'assigned_to', 'assigned_to_name', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    def get_company_name(self, obj):
        if obj.company_account:
            return obj.company_account.name
        return obj.company or ''


class ContactCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء جهة اتصال."""

    class Meta:
        model = Contact
        fields = (
            'first_name', 'last_name', 'email', 'phone', 'mobile',
            'company', 'company_account', 'position', 'source', 'status',
            'assigned_to', 'notes',
        )


class ContactUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث جهة اتصال."""

    class Meta:
        model = Contact
        fields = (
            'first_name', 'last_name', 'email', 'phone', 'mobile',
            'company', 'company_account', 'position', 'source', 'status',
            'assigned_to', 'notes',
        )


class ContactDetailSerializer(serializers.ModelSerializer):
    """مسلسل تفصيلي لعرض بيانات جهة الاتصال الكاملة مع معلومات الشركة."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    full_name = serializers.SerializerMethodField()
    company_info = CompanyDetailSerializer(source='company_account', read_only=True, default=None)
    leads_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Contact
        fields = (
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'mobile', 'company', 'company_account', 'company_info', 'position',
            'source', 'source_display', 'status', 'status_display',
            'assigned_to', 'assigned_to_name', 'notes', 'leads_count',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'


# =============================================
# مسلسلات فرص البيع
# =============================================

class LeadListSerializer(serializers.ModelSerializer):
    """مسلسل خفيف لعرض قائمة فرص البيع."""

    contact_name = serializers.SerializerMethodField()
    contact_email = serializers.CharField(source='contact.email', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    pipeline_stage_display = serializers.CharField(source='get_pipeline_stage_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    weighted_value = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = (
            'id', 'title', 'contact', 'contact_name', 'contact_email',
            'value', 'probability', 'weighted_value', 'expected_close_date',
            'status', 'status_display', 'pipeline_stage', 'pipeline_stage_display',
            'assigned_to', 'assigned_to_name', 'source', 'source_display',
            'lost_reason', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_contact_name(self, obj):
        return f'{obj.contact.first_name} {obj.contact.last_name}' if obj.contact else ''

    def get_weighted_value(self, obj):
        if obj.value and obj.probability:
            return str(obj.value * obj.probability / 100)
        return '0.00'


class LeadCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء فرصة بيع."""

    class Meta:
        model = Lead
        fields = (
            'title', 'contact', 'value', 'probability', 'expected_close_date',
            'status', 'pipeline_stage', 'assigned_to', 'source', 'notes',
        )

    def validate_probability(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('نسبة الاحتمالية يجب أن تكون بين 0 و 100')
        return value


class LeadUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث فرصة بيع."""

    class Meta:
        model = Lead
        fields = (
            'title', 'contact', 'value', 'probability', 'expected_close_date',
            'status', 'pipeline_stage', 'assigned_to', 'source', 'lost_reason', 'notes',
        )

    def validate_probability(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('نسبة الاحتمالية يجب أن تكون بين 0 و 100')
        return value


class LeadChangeStatusSerializer(serializers.Serializer):
    """مسلسل لتغيير حالة فرصة البيع."""

    status = serializers.ChoiceField(
        choices=Lead.STATUS_CHOICES,
        error_messages={'invalid_choice': 'حالة غير صالحة'},
    )
    pipeline_stage = serializers.ChoiceField(
        choices=Lead.PIPELINE_STAGE_CHOICES,
        required=False,
        allow_null=True,
        default=None,
    )
    lost_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# مسلسل تفصيلي لفرصة البيع مع الأنشطة
# =============================================

class LeadActivityForDetailSerializer(serializers.ModelSerializer):
    """مسلسل لأنشطة الفرصة داخل عرض التفاصيل."""

    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    completed_by_name = serializers.CharField(source='completed_by.username', read_only=True, default=None)

    class Meta:
        model = LeadActivity
        fields = (
            'id', 'activity_type', 'activity_type_display', 'subject',
            'description', 'scheduled_at', 'completed', 'completed_by',
            'completed_by_name', 'created_at',
        )


class LeadDetailWithActivitiesSerializer(serializers.ModelSerializer):
    """مسلسل تفصيلي لعرض فرصة البيع مع جميع الأنشطة والجدول الزمني."""

    contact_name = serializers.SerializerMethodField()
    contact_email = serializers.CharField(source='contact.email', read_only=True, default=None)
    contact_phone = serializers.CharField(source='contact.phone', read_only=True, default=None)
    contact_company = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    pipeline_stage_display = serializers.CharField(source='get_pipeline_stage_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    weighted_value = serializers.SerializerMethodField()
    activities = LeadActivityForDetailSerializer(many=True, read_only=True)
    timeline = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = (
            'id', 'title', 'contact', 'contact_name', 'contact_email',
            'contact_phone', 'contact_company', 'value', 'probability',
            'weighted_value', 'expected_close_date', 'status', 'status_display',
            'pipeline_stage', 'pipeline_stage_display', 'assigned_to',
            'assigned_to_name', 'source', 'source_display', 'lost_reason',
            'notes', 'activities', 'timeline', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_contact_name(self, obj):
        return f'{obj.contact.first_name} {obj.contact.last_name}' if obj.contact else ''

    def get_contact_company(self, obj):
        if obj.contact:
            if obj.contact.company_account:
                return obj.contact.company_account.name
            return obj.contact.company or ''
        return ''

    def get_weighted_value(self, obj):
        if obj.value and obj.probability:
            return str(obj.value * obj.probability / 100)
        return '0.00'

    def get_timeline(self, obj):
        """بناء جدول زمني للأحداث من تاريخ الإنشاء والأنشطة."""
        timeline = []
        # حدث الإنشاء
        timeline.append({
            'type': 'created',
            'description': f'تم إنشاء فرصة البيع "{obj.title}"',
            'date': obj.created_at.isoformat() if obj.created_at else None,
        })
        # الأنشطة كأحداث في الجدول الزمني
        for activity in obj.activities.all().order_by('created_at'):
            timeline.append({
                'type': 'activity',
                'activity_type': activity.activity_type,
                'activity_type_display': activity.get_activity_type_display(),
                'description': activity.subject,
                'date': activity.created_at.isoformat() if activity.created_at else None,
                'completed': activity.completed,
            })
        # آخر تحديث
        if obj.updated_at and obj.updated_at != obj.created_at:
            status_label = obj.get_status_display()
            stage_label = obj.get_pipeline_stage_display()
            timeline.append({
                'type': 'status_change',
                'description': f'الحالة: {status_label} | المرحلة: {stage_label}',
                'date': obj.updated_at.isoformat() if obj.updated_at else None,
            })
        # ترتيب حسب التاريخ الأحدث
        timeline.sort(key=lambda x: x['date'] or '', reverse=False)
        return timeline


# =============================================
# مسلسل تحليلات مراحل المبيعات
# =============================================

class StageAnalyticsSerializer(serializers.Serializer):
    """مسلسل لتحليلات كل مرحلة من مراحل خط المبيعات."""

    stage = serializers.CharField()
    stage_display = serializers.CharField()
    count = serializers.IntegerField()
    avg_days_in_stage = serializers.FloatField(allow_null=True, required=False)
    win_rate = serializers.FloatField(allow_null=True, required=False)
    avg_deal_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, allow_null=True, required=False
    )


class LostReasonsSerializer(serializers.Serializer):
    """مسلسل لأسباب فقدان الفرص."""

    reason = serializers.CharField()
    count = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=14, decimal_places=2)


class MonthlySalesTrendSerializer(serializers.Serializer):
    """مسلسل للاتجاه الشهري للمبيعات."""

    month = serializers.CharField()
    won_deals = serializers.IntegerField()
    won_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    lost_deals = serializers.IntegerField()
    lost_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_value = serializers.DecimalField(max_digits=14, decimal_places=2)


class SalesStageAnalyticsSerializer(serializers.Serializer):
    """مسلسل شامل لتحليلات مراحل المبيعات."""

    stage_analytics = StageAnalyticsSerializer(many=True)
    total_lost_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    lost_reasons_breakdown = LostReasonsSerializer(many=True)
    monthly_sales_trend = MonthlySalesTrendSerializer(many=True)


# =============================================
# مسلسلات أنشطة الفرص
# =============================================

class LeadActivityListSerializer(serializers.ModelSerializer):
    """مسلسل لعرض قائمة أنشطة الفرص."""

    lead_title = serializers.CharField(source='lead.title', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    completed_by_name = serializers.CharField(source='completed_by.username', read_only=True, default=None)

    class Meta:
        model = LeadActivity
        fields = (
            'id', 'lead', 'lead_title', 'activity_type', 'activity_type_display',
            'subject', 'description', 'scheduled_at', 'completed',
            'completed_by', 'completed_by_name', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class LeadActivityCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء نشاط فرصة."""

    class Meta:
        model = LeadActivity
        fields = (
            'lead', 'activity_type', 'subject', 'description', 'scheduled_at',
        )


# =============================================
# مسلسلات شرائح العملاء
# =============================================

class CustomerSegmentListSerializer(serializers.ModelSerializer):
    """مسلسل لعرض قائمة شرائح العملاء."""

    class Meta:
        model = CustomerSegment
        fields = (
            'id', 'name', 'description', 'criteria', 'customer_count',
            'discount_percentage', 'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class CustomerSegmentCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء شريحة عملاء."""

    class Meta:
        model = CustomerSegment
        fields = (
            'name', 'description', 'criteria', 'customer_count',
            'discount_percentage', 'is_active',
        )

    def validate_discount_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('نسبة الخصم يجب أن تكون بين 0 و 100')
        return value


class CustomerSegmentUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث شريحة عملاء."""

    class Meta:
        model = CustomerSegment
        fields = (
            'name', 'description', 'criteria', 'customer_count',
            'discount_percentage', 'is_active',
        )

    def validate_discount_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('نسبة الخصم يجب أن تكون بين 0 و 100')
        return value


# =============================================
# مسلسلات الحملات التسويقية
# =============================================

class CampaignListSerializer(serializers.ModelSerializer):
    """مسلسل لعرض قائمة الحملات التسويقية."""

    campaign_type_display = serializers.CharField(source='get_campaign_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    activities_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Campaign
        fields = (
            'id', 'name', 'description', 'campaign_type', 'campaign_type_display',
            'status', 'status_display', 'start_date', 'end_date', 'budget',
            'actual_cost', 'target_audience', 'assigned_to', 'assigned_to_name',
            'activities_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class CampaignCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء حملة تسويقية."""

    class Meta:
        model = Campaign
        fields = (
            'name', 'description', 'campaign_type', 'status',
            'start_date', 'end_date', 'budget', 'target_audience', 'assigned_to',
        )


class CampaignUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث حملة تسويقية."""

    class Meta:
        model = Campaign
        fields = (
            'name', 'description', 'campaign_type', 'status',
            'start_date', 'end_date', 'budget', 'actual_cost',
            'target_audience', 'assigned_to',
        )


class CampaignChangeStatusSerializer(serializers.Serializer):
    """مسلسل لتغيير حالة الحملة التسويقية."""

    status = serializers.ChoiceField(
        choices=Campaign.STATUS_CHOICES,
        error_messages={'invalid_choice': 'حالة غير صالحة'},
    )


# =============================================
# مسلسلات أنشطة الحملات
# =============================================

class CampaignActivityListSerializer(serializers.ModelSerializer):
    """مسلسل لعرض قائمة أنشطة الحملات."""

    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    contact_name = serializers.SerializerMethodField()

    class Meta:
        model = CampaignActivity
        fields = (
            'id', 'campaign', 'campaign_name', 'activity_type',
            'activity_type_display', 'contact', 'contact_name',
            'description', 'activity_date', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def get_contact_name(self, obj):
        return f'{obj.contact.first_name} {obj.contact.last_name}' if obj.contact else None


class CampaignActivityCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء نشاط حملة."""

    class Meta:
        model = CampaignActivity
        fields = (
            'campaign', 'activity_type', 'contact', 'description', 'activity_date',
        )


# =============================================
# مسلسل تحويل فرصة بيع إلى عميل
# =============================================

class LeadConvertSerializer(serializers.Serializer):
    """مسلسل للتحقق من إمكانية تحويل فرصة البيع إلى عميل."""

    def validate(self, attrs):
        lead = self.context.get('lead')
        if not lead:
            raise serializers.ValidationError('فرصة البيع غير موجودة')
        if lead.status not in ('won', 'negotiation'):
            raise serializers.ValidationError(
                'يمكن تحويل فرص البيع فقط إذا كانت حالتها "مكتسب" أو "تفاوض"'
            )
        return attrs


# =============================================
# مسلسل بيانات قمع خط المبيعات
# =============================================

class PipelineFunnelSerializer(serializers.Serializer):
    """مسلسل لبيانات قمع خط المبيعات."""

    stage = serializers.CharField()
    stage_display = serializers.CharField()
    count = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    weighted_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    conversion_rate = serializers.FloatField(allow_null=True, required=False)


# =============================================
# مسلسل التنبؤ بالمبيعات
# =============================================

class SalesForecastSerializer(serializers.Serializer):
    """مسلسل للتنبؤ بالمبيعات الشهرية."""

    month = serializers.CharField()
    expected_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    leads_count = serializers.IntegerField()
    avg_probability = serializers.FloatField(allow_null=True, required=False)


# =============================================
# مسلسل إحصائيات إدارة علاقات العملاء
# =============================================

class CRMStatsSerializer(serializers.Serializer):
    """مسلسل لإحصائيات لوحة تحكم إدارة علاقات العملاء."""

    total_contacts = serializers.IntegerField()
    active_contacts = serializers.IntegerField()
    total_leads = serializers.IntegerField()
    active_leads = serializers.IntegerField()
    won_leads = serializers.IntegerField()
    lost_leads = serializers.IntegerField()
    total_pipeline_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    weighted_pipeline_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_segments = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    total_campaigns = serializers.IntegerField()
    total_budget = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_actual_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending_activities = serializers.IntegerField()
    completed_activities = serializers.IntegerField()


# =============================================
# مسلسل إحصائيات الشركة
# =============================================

class CompanyStatsSerializer(serializers.Serializer):
    """مسلسل لإحصائيات الشركة."""

    company_id = serializers.IntegerField()
    company_name = serializers.CharField()
    total_contacts = serializers.IntegerField()
    total_leads = serializers.IntegerField()
    won_deals = serializers.IntegerField()
    lost_deals = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    active_pipeline_value = serializers.DecimalField(max_digits=14, decimal_places=2)


# =============================================
# مسلسلات سياسات اتفاقية مستوى الخدمة (SLA)
# =============================================

class SLAPolicyListSerializer(serializers.ModelSerializer):
    """مسلسل خفيف لعرض قائمة سياسات SLA."""

    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    tickets_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = SLAPolicy
        fields = (
            'id', 'name', 'description', 'priority', 'priority_display',
            'first_response_time', 'resolution_time', 'is_active',
            'tickets_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class SLAPolicyCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء سياسة SLA."""

    class Meta:
        model = SLAPolicy
        fields = (
            'name', 'description', 'priority',
            'first_response_time', 'resolution_time', 'is_active',
        )

    def validate_first_response_time(self, value):
        if value <= 0:
            raise serializers.ValidationError('وقت الاستجابة الأولية يجب أن يكون أكبر من صفر')
        return value

    def validate_resolution_time(self, value):
        if value <= 0:
            raise serializers.ValidationError('وقت الحل يجب أن يكون أكبر من صفر')
        return value


class SLAPolicyUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث سياسة SLA."""

    class Meta:
        model = SLAPolicy
        fields = (
            'name', 'description', 'priority',
            'first_response_time', 'resolution_time', 'is_active',
        )

    def validate_first_response_time(self, value):
        if value <= 0:
            raise serializers.ValidationError('وقت الاستجابة الأولية يجب أن يكون أكبر من صفر')
        return value

    def validate_resolution_time(self, value):
        if value <= 0:
            raise serializers.ValidationError('وقت الحل يجب أن يكون أكبر من صفر')
        return value


# =============================================
# مسلسلات تذاكر الدعم
# =============================================

class TicketListSerializer(serializers.ModelSerializer):
    """مسلسل خفيف لعرض قائمة تذاكر الدعم."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    contact_name = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True, default=None)
    sla_policy_name = serializers.CharField(source='sla_policy.name', read_only=True, default=None)
    comments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Ticket
        fields = (
            'id', 'ticket_number', 'subject', 'status', 'status_display',
            'priority', 'priority_display', 'category', 'category_display',
            'contact', 'contact_name', 'company', 'company_name',
            'assigned_to', 'assigned_to_name', 'sla_policy', 'sla_policy_name',
            'comments_count', 'resolved_at', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'ticket_number', 'created_at', 'updated_at')

    def get_contact_name(self, obj):
        return f'{obj.contact.first_name} {obj.contact.last_name}' if obj.contact else ''


class TicketCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء تذكرة دعم."""

    class Meta:
        model = Ticket
        fields = (
            'subject', 'description', 'status', 'priority', 'category',
            'contact', 'company', 'assigned_to', 'sla_policy',
        )

    def validate_subject(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('موضوع التذكرة لا يمكن أن يكون فارغاً')
        return value.strip()


class TicketUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث تذكرة دعم."""

    class Meta:
        model = Ticket
        fields = (
            'subject', 'description', 'status', 'priority', 'category',
            'contact', 'company', 'assigned_to', 'sla_policy', 'resolution',
        )

    def validate_subject(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError('موضوع التذكرة لا يمكن أن يكون فارغاً')
        return value


class TicketCommentForDetailSerializer(serializers.ModelSerializer):
    """مسلسل للتعليقات داخل عرض تفاصيل التذكرة."""

    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = TicketComment
        fields = (
            'id', 'content', 'is_internal', 'created_by', 'created_by_name',
            'created_at',
        )


class TicketDetailSerializer(serializers.ModelSerializer):
    """مسلسل تفصيلي لعرض بيانات التذكرة الكاملة مع التعليقات."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    contact_name = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True, default=None)
    sla_policy_name = serializers.CharField(source='sla_policy.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)
    comments = TicketCommentForDetailSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Ticket
        fields = (
            'id', 'ticket_number', 'subject', 'description', 'status',
            'status_display', 'priority', 'priority_display', 'category',
            'category_display', 'contact', 'contact_name', 'company',
            'company_name', 'assigned_to', 'assigned_to_name', 'sla_policy',
            'sla_policy_name', 'resolution', 'resolved_at', 'first_response_at',
            'created_by', 'created_by_name', 'comments', 'comments_count',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'ticket_number', 'created_at', 'updated_at')

    def get_contact_name(self, obj):
        return f'{obj.contact.first_name} {obj.contact.last_name}' if obj.contact else ''


class TicketAssignSerializer(serializers.Serializer):
    """مسلسل لتسند التذكرة إلى مستخدم."""

    assigned_to = serializers.IntegerField(
        help_text='معرف المستخدم الذي سيتم تسند التذكرة إليه',
        error_messages={'required': 'معرف المستخدم المسند إليه مطلوب'},
    )


class TicketResolveSerializer(serializers.Serializer):
    """مسلسل لحل التذكرة."""

    resolution = serializers.CharField(
        required=True,
        help_text='وصف الحل',
        error_messages={'required': 'وصف الحل مطلوب'},
    )


class TicketStatsSerializer(serializers.Serializer):
    """مسلسل لإحصائيات التذاكر."""

    total_tickets = serializers.IntegerField()
    new_tickets = serializers.IntegerField()
    in_progress_tickets = serializers.IntegerField()
    pending_customer_tickets = serializers.IntegerField()
    resolved_tickets = serializers.IntegerField()
    closed_tickets = serializers.IntegerField()
    reopened_tickets = serializers.IntegerField()
    avg_resolution_time_minutes = serializers.FloatField(allow_null=True, required=False)
    tickets_by_priority = serializers.DictField(child=serializers.IntegerField(), required=False)
    tickets_by_category = serializers.DictField(child=serializers.IntegerField(), required=False)


# =============================================
# مسلسلات تعليقات التذاكر
# =============================================

class TicketCommentListSerializer(serializers.ModelSerializer):
    """مسلسل لعرض قائمة تعليقات التذكرة."""

    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = TicketComment
        fields = (
            'id', 'ticket', 'content', 'is_internal', 'created_by',
            'created_by_name', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class TicketCommentCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء تعليق على تذكرة."""

    class Meta:
        model = TicketComment
        fields = (
            'ticket', 'content', 'is_internal',
        )

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('محتوى التعليق لا يمكن أن يكون فارغاً')
        return value.strip()


# =============================================
# مسلسلات عروض الأسعار
# =============================================

class QuotationItemForDetailSerializer(serializers.ModelSerializer):
    """مسلسل لبنود عرض السعر داخل عرض التفاصيل."""

    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)

    class Meta:
        model = QuotationItem
        fields = (
            'id', 'item_type', 'item_type_display', 'item_name', 'description',
            'quantity', 'unit_price', 'discount_percent', 'subtotal', 'order',
        )


class QuotationListSerializer(serializers.ModelSerializer):
    """مسلسل خفيف لعرض قائمة عروض الأسعار."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True, default=None)
    contact_name = serializers.SerializerMethodField()
    lead_title = serializers.CharField(source='lead.title', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)
    items_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Quotation
        fields = (
            'id', 'quote_number', 'company', 'company_name', 'contact',
            'contact_name', 'lead', 'lead_title', 'status', 'status_display',
            'valid_until', 'subtotal', 'discount_percent', 'discount_amount',
            'vat_percent', 'vat_amount', 'total_amount', 'converted_to_order',
            'created_by', 'created_by_name', 'items_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'quote_number', 'created_at', 'updated_at')

    def get_contact_name(self, obj):
        return f'{obj.contact.first_name} {obj.contact.last_name}' if obj.contact else ''


class QuotationCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء عرض سعر."""

    class Meta:
        model = Quotation
        fields = (
            'company', 'contact', 'lead', 'status', 'valid_until',
            'subtotal', 'discount_percent', 'discount_amount',
            'vat_percent', 'vat_amount', 'total_amount',
            'notes', 'terms_conditions', 'created_by',
        )


class QuotationUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث عرض سعر."""

    class Meta:
        model = Quotation
        fields = (
            'company', 'contact', 'lead', 'status', 'valid_until',
            'subtotal', 'discount_percent', 'discount_amount',
            'vat_percent', 'vat_amount', 'total_amount',
            'notes', 'terms_conditions',
        )


class QuotationDetailSerializer(serializers.ModelSerializer):
    """مسلسل تفصيلي لعرض بيانات عرض السعر الكاملة مع البنود."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True, default=None)
    contact_name = serializers.SerializerMethodField()
    lead_title = serializers.CharField(source='lead.title', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)
    items = QuotationItemForDetailSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Quotation
        fields = (
            'id', 'quote_number', 'company', 'company_name', 'contact',
            'contact_name', 'lead', 'lead_title', 'status', 'status_display',
            'valid_until', 'subtotal', 'discount_percent', 'discount_amount',
            'vat_percent', 'vat_amount', 'total_amount', 'notes',
            'terms_conditions', 'created_by', 'created_by_name',
            'converted_to_order', 'items', 'items_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'quote_number', 'created_at', 'updated_at')

    def get_contact_name(self, obj):
        return f'{obj.contact.first_name} {obj.contact.last_name}' if obj.contact else ''


class QuotationItemCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء بند عرض سعر."""

    class Meta:
        model = QuotationItem
        fields = (
            'quotation', 'item_type', 'item_name', 'description',
            'quantity', 'unit_price', 'discount_percent', 'subtotal', 'order',
        )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('سعر الوحدة يجب أن يكون أكبر من صفر')
        return value


class QuotationItemUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث بند عرض سعر."""

    class Meta:
        model = QuotationItem
        fields = (
            'item_type', 'item_name', 'description',
            'quantity', 'unit_price', 'discount_percent', 'subtotal', 'order',
        )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('سعر الوحدة يجب أن يكون أكبر من صفر')
        return value


# =============================================
# مسلسلات العمولات
# =============================================

class CommissionListSerializer(serializers.ModelSerializer):
    """مسلسل خفيف لعرض قائمة العمولات."""

    sale_type_display = serializers.CharField(source='get_sale_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    salesperson_name = serializers.CharField(source='salesperson.username', read_only=True)

    class Meta:
        model = Commission
        fields = (
            'id', 'salesperson', 'salesperson_name', 'sale_type',
            'sale_type_display', 'reference_id', 'reference_number',
            'amount', 'commission_percent', 'commission_amount',
            'status', 'status_display', 'paid_at',
            'period_month', 'period_year', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class CommissionCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء عمولة."""

    class Meta:
        model = Commission
        fields = (
            'salesperson', 'sale_type', 'reference_id', 'reference_number',
            'amount', 'commission_percent', 'commission_amount',
            'status', 'paid_at', 'notes', 'period_month', 'period_year',
        )

    def validate(self, attrs):
        amount = attrs.get('amount')
        percent = attrs.get('commission_percent')
        commission_amount = attrs.get('commission_amount')

        if amount and percent and commission_amount:
            expected = amount * percent / Decimal('100')
            # السماح بفارق بسيط بسبب التقريب
            if abs(expected - commission_amount) > Decimal('0.01'):
                raise serializers.ValidationError(
                    'مبلغ العمولة غير صحيح - يجب أن يساوي قيمة المبيعات × نسبة العمولة / 100'
                )
        return attrs


class CommissionUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث عمولة."""

    class Meta:
        model = Commission
        fields = (
            'salesperson', 'sale_type', 'reference_id', 'reference_number',
            'amount', 'commission_percent', 'commission_amount',
            'status', 'paid_at', 'notes', 'period_month', 'period_year',
        )

    def validate(self, attrs):
        amount = attrs.get('amount')
        percent = attrs.get('commission_percent')
        commission_amount = attrs.get('commission_amount')

        if amount is not None and percent is not None and commission_amount is not None:
            expected = amount * percent / Decimal('100')
            if abs(expected - commission_amount) > Decimal('0.01'):
                raise serializers.ValidationError(
                    'مبلغ العمولة غير صحيح - يجب أن يساوي قيمة المبيعات × نسبة العمولة / 100'
                )
        return attrs


class CommissionStatsSerializer(serializers.Serializer):
    """مسلسل لإحصائيات العمولات."""

    total_pending = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_approved = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_cancelled = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_all = serializers.DecimalField(max_digits=14, decimal_places=2)
    by_period = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )
