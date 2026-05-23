"""
Serializers for the Tender Management module.
Handles Tender, TenderDocument, TenderBid, TenderEvaluation, and TenderAward
data transformation.
"""

from rest_framework import serializers
from .models import (
    Tender,
    TenderDocument,
    TenderBid,
    TenderEvaluation,
    TenderAward,
)


# =============================================
# Tender Serializers
# =============================================

class TenderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing tenders."""

    tender_type_display = serializers.CharField(source='get_tender_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)
    bids_count = serializers.SerializerMethodField()

    class Meta:
        model = Tender
        fields = (
            'id', 'title', 'tender_number', 'tender_type', 'tender_type_display',
            'status', 'status_display', 'publish_date', 'closing_date',
            'estimated_value', 'department', 'department_name', 'project',
            'project_name', 'created_by', 'created_by_name', 'bids_count',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_bids_count(self, obj):
        return obj.bids.count()


class TenderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a tender."""

    class Meta:
        model = Tender
        fields = (
            'title', 'tender_number', 'description', 'tender_type',
            'publish_date', 'closing_date', 'opening_date', 'estimated_value',
            'department', 'project', 'terms_conditions',
        )

    def validate(self, attrs):
        if 'closing_date' in attrs and 'publish_date' in attrs:
            if attrs['closing_date'] <= attrs['publish_date']:
                raise serializers.ValidationError('تاريخ الإغلاق يجب أن يكون بعد تاريخ النشر')
        if 'opening_date' in attrs and 'closing_date' in attrs:
            if attrs['opening_date'] < attrs['closing_date']:
                raise serializers.ValidationError('تاريخ فتح العروض يجب أن يكون بعد تاريخ الإغلاق')
        return attrs


class TenderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a tender."""

    class Meta:
        model = Tender
        fields = (
            'title', 'description', 'tender_type', 'status',
            'publish_date', 'closing_date', 'opening_date',
            'estimated_value', 'department', 'project', 'terms_conditions',
        )

    def validate(self, attrs):
        if 'closing_date' in attrs and 'publish_date' in attrs:
            if attrs['closing_date'] <= attrs['publish_date']:
                raise serializers.ValidationError('تاريخ الإغلاق يجب أن يكون بعد تاريخ النشر')
        if 'opening_date' in attrs and 'closing_date' in attrs:
            if attrs['opening_date'] < attrs['closing_date']:
                raise serializers.ValidationError('تاريخ فتح العروض يجب أن يكون بعد تاريخ الإغلاق')
        return attrs


class TenderDetailSerializer(TenderListSerializer):
    """Detailed tender serializer with additional information."""

    documents_count = serializers.SerializerMethodField()
    award_info = serializers.SerializerMethodField()

    class Meta(TenderListSerializer.Meta):
        fields = TenderListSerializer.Meta.fields + (
            'description', 'terms_conditions', 'opening_date',
            'documents_count', 'award_info',
        )

    def get_documents_count(self, obj):
        return obj.documents.count()

    def get_award_info(self, obj):
        award = obj.awards.filter(status='approved').first()
        if award:
            return {
                'id': award.id,
                'supplier': award.bid.supplier.name if award.bid and award.bid.supplier else None,
                'contract_value': str(award.contract_value),
                'contract_duration_days': award.contract_duration_days,
                'status': award.status,
                'status_display': award.get_status_display(),
            }
        return None


# =============================================
# Tender Document Serializers
# =============================================

class TenderDocumentListSerializer(serializers.ModelSerializer):
    """Serializer for listing tender documents."""

    tender_title = serializers.CharField(source='tender.title', read_only=True)
    tender_number = serializers.CharField(source='tender.tender_number', read_only=True)

    class Meta:
        model = TenderDocument
        fields = (
            'id', 'tender', 'tender_title', 'tender_number',
            'title', 'file', 'description', 'uploaded_at',
        )
        read_only_fields = ('id', 'uploaded_at')


class TenderDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a tender document."""

    class Meta:
        model = TenderDocument
        fields = ('tender', 'title', 'file', 'description')


# =============================================
# Tender Bid Serializers
# =============================================

class TenderBidListSerializer(serializers.ModelSerializer):
    """Serializer for listing tender bids."""

    tender_title = serializers.CharField(source='tender.title', read_only=True)
    tender_number = serializers.CharField(source='tender.tender_number', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    evaluations_count = serializers.SerializerMethodField()

    class Meta:
        model = TenderBid
        fields = (
            'id', 'tender', 'tender_title', 'tender_number',
            'supplier', 'supplier_name', 'bid_number', 'submission_date',
            'status', 'status_display', 'total_amount', 'validity_days',
            'technical_score', 'financial_score', 'total_score',
            'evaluations_count', 'notes', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_evaluations_count(self, obj):
        return obj.evaluations.count()


class TenderBidCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a tender bid."""

    class Meta:
        model = TenderBid
        fields = (
            'tender', 'supplier', 'bid_number', 'submission_date',
            'total_amount', 'validity_days', 'notes',
        )

    def validate(self, attrs):
        if attrs['total_amount'] < 0:
            raise serializers.ValidationError('إجمالي المبلغ يجب أن يكون صفر أو أكبر')
        if attrs['validity_days'] <= 0:
            raise serializers.ValidationError('أيام الصلاحية يجب أن تكون أكبر من صفر')
        return attrs


class TenderBidUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a tender bid."""

    class Meta:
        model = TenderBid
        fields = (
            'total_amount', 'validity_days',
            'technical_score', 'financial_score', 'total_score', 'notes',
        )


# =============================================
# Tender Evaluation Serializers
# =============================================

class TenderEvaluationListSerializer(serializers.ModelSerializer):
    """Serializer for listing tender evaluations."""

    bid_number = serializers.CharField(source='bid.bid_number', read_only=True)
    supplier_name = serializers.CharField(source='bid.supplier.name', read_only=True)
    evaluator_name = serializers.CharField(source='evaluator.username', read_only=True, default=None)

    class Meta:
        model = TenderEvaluation
        fields = (
            'id', 'bid', 'bid_number', 'supplier_name',
            'criterion', 'weight', 'score', 'weighted_score',
            'evaluator', 'evaluator_name', 'notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class TenderEvaluationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a tender evaluation."""

    class Meta:
        model = TenderEvaluation
        fields = ('bid', 'criterion', 'weight', 'score', 'weighted_score', 'notes')

    def validate(self, attrs):
        if attrs['weight'] < 0:
            raise serializers.ValidationError('الوزن يجب أن يكون صفر أو أكبر')
        if attrs['score'] < 0:
            raise serializers.ValidationError('الدرجة يجب أن تكون صفر أو أكبر')
        return attrs


class TenderEvaluationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a tender evaluation."""

    class Meta:
        model = TenderEvaluation
        fields = ('criterion', 'weight', 'score', 'weighted_score', 'notes')


# =============================================
# Tender Award Serializers
# =============================================

class TenderAwardListSerializer(serializers.ModelSerializer):
    """Serializer for listing tender awards."""

    tender_number = serializers.CharField(source='tender.tender_number', read_only=True)
    tender_title = serializers.CharField(source='tender.title', read_only=True)
    supplier_name = serializers.CharField(source='bid.supplier.name', read_only=True)
    bid_number = serializers.CharField(source='bid.bid_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = TenderAward
        fields = (
            'id', 'tender', 'tender_number', 'tender_title',
            'bid', 'bid_number', 'supplier_name', 'award_date',
            'contract_value', 'contract_duration_days', 'terms',
            'approved_by', 'approved_by_name', 'status', 'status_display',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')


class TenderAwardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a tender award."""

    class Meta:
        model = TenderAward
        fields = ('tender', 'bid', 'award_date', 'contract_value', 'contract_duration_days', 'terms')

    def validate(self, attrs):
        if attrs['tender'] != attrs['bid'].tender:
            raise serializers.ValidationError('العرض يجب أن يكون تابعاً لهذه المناقصة')
        if attrs['contract_value'] < 0:
            raise serializers.ValidationError('قيمة العقد يجب أن تكون صفر أو أكبر')
        if attrs['contract_duration_days'] <= 0:
            raise serializers.ValidationError('مدة العقد يجب أن تكون أكبر من صفر')
        return attrs


class TenderAwardApproveSerializer(serializers.Serializer):
    """Serializer for approving/rejecting tender awards."""

    action = serializers.ChoiceField(
        choices=('approve', 'reject'),
        error_messages={'invalid_choice': 'إجراء غير صالح (approve أو reject)'},
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


# =============================================
# Tender Stats Serializer
# =============================================

class TenderStatsSerializer(serializers.Serializer):
    """Serializer for Tender dashboard statistics."""

    total_tenders = serializers.IntegerField()
    draft_tenders = serializers.IntegerField()
    published_tenders = serializers.IntegerField()
    evaluation_tenders = serializers.IntegerField()
    awarded_tenders = serializers.IntegerField()
    cancelled_tenders = serializers.IntegerField()
    total_bids = serializers.IntegerField()
    total_awards = serializers.IntegerField()
    total_estimated_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_contract_value = serializers.DecimalField(max_digits=14, decimal_places=2)
