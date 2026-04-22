"""
المسلسلات (Serializers) لوحدة إدارة علاقات العملاء (CRM).
تتعامل مع تحويل بيانات جهات الاتصال، فرص البيع، أنشطة الفرص، شرائح العملاء، الحملات التسويقية، وأنشطة الحملات.
"""

from rest_framework import serializers
from .models import (
    Contact,
    Lead,
    LeadActivity,
    CustomerSegment,
    Campaign,
    CampaignActivity,
)


# =============================================
# مسلسلات جهات الاتصال
# =============================================

class ContactListSerializer(serializers.ModelSerializer):
    """مسلسل خفيف لعرض قائمة جهات الاتصال."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = (
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'mobile', 'company', 'position', 'source', 'source_display',
            'status', 'status_display', 'assigned_to', 'assigned_to_name',
            'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'


class ContactCreateSerializer(serializers.ModelSerializer):
    """مسلسل لإنشاء جهة اتصال."""

    class Meta:
        model = Contact
        fields = (
            'first_name', 'last_name', 'email', 'phone', 'mobile',
            'company', 'position', 'source', 'status', 'assigned_to', 'notes',
        )


class ContactUpdateSerializer(serializers.ModelSerializer):
    """مسلسل لتحديث جهة اتصال."""

    class Meta:
        model = Contact
        fields = (
            'first_name', 'last_name', 'email', 'phone', 'mobile',
            'company', 'position', 'source', 'status', 'assigned_to', 'notes',
        )


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
    activities_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = (
            'id', 'name', 'description', 'campaign_type', 'campaign_type_display',
            'status', 'status_display', 'start_date', 'end_date', 'budget',
            'actual_cost', 'target_audience', 'assigned_to', 'assigned_to_name',
            'activities_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_activities_count(self, obj):
        return obj.activities.count()


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
