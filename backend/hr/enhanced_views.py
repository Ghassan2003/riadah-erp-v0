"""
Enhanced HR Views & Serializers.
Provides CRUD views and serializers for all NEW HR models:
  - Recruitment (JobRequisition, JobPosting, JobApplication, Interview, JobOffer)
  - Qualifications (Education, Experience, Skill, Language, Certification)
  - Documents (EmployeeDocument, DocumentTemplate)
  - Training (TrainingNeed, Course, TrainingSession, TrainingEnrollment, TrainingBudget)
  - Employee Finances (Loan, LoanPayment, SalaryAdvance, OvertimeRequest)
  - Benefits & Discipline (HealthInsurance, EmployeeInsurance, DisciplinaryAction, Grievance, Offboarding)
"""

from rest_framework import generics, status, permissions, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers as drf_serializers
from django.db.models import Q
from django.utils import timezone

# Import models
from .recruitment import (
    JobRequisition, JobPosting, JobApplication, Interview, JobOffer,
    hire_candidate,
)
from .qualifications import Education, Experience, Skill, Language, Certification
from .documents import EmployeeDocument, DocumentTemplate
from .training import (
    TrainingNeed, Course, TrainingSession, TrainingEnrollment, TrainingBudget,
)
from .employee_finances import Loan, LoanPayment, SalaryAdvance, OvertimeRequest
from .benefits_discipline import (
    HealthInsurance, EmployeeInsurance, DisciplinaryAction, Grievance, Offboarding,
)

# Import existing HR models for FK filters
from .models import Employee, Department

from users.permissions import IsAdmin, IsHROrAdmin


# ═══════════════════════════════════════════════════
# SERIALIZERS
# ═══════════════════════════════════════════════════

# ─── Recruitment Serializers ─────────────────────

class JobRequisitionSerializer(drf_serializers.ModelSerializer):
    """طلب توظيف"""
    department_name = drf_serializers.CharField(source='department.name', read_only=True, default=None)
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    priority_display = drf_serializers.CharField(source='get_priority_display', read_only=True)
    employment_type_display = drf_serializers.CharField(source='get_employment_type_display', read_only=True)
    requested_by_name = drf_serializers.CharField(source='requested_by.username', read_only=True, default=None)
    approved_by_name = drf_serializers.CharField(source='approved_by.username', read_only=True, default=None)
    remaining_count = drf_serializers.IntegerField(read_only=True)

    class Meta:
        model = JobRequisition
        fields = (
            'id', 'requisition_number', 'department', 'position', 'job_description',
            'required_count', 'filled_count', 'priority', 'employment_type',
            'min_salary', 'max_salary', 'required_qualifications',
            'required_experience', 'skills_required', 'status', 'requested_by',
            'approved_by', 'approved_at', 'deadline', 'notes', 'created_at',
            'updated_at', 'department_name', 'status_display', 'priority_display',
            'employment_type_display', 'requested_by_name', 'approved_by_name',
            'remaining_count',
        )
        read_only_fields = ('requisition_number', 'created_at', 'updated_at')


class JobPostingSerializer(drf_serializers.ModelSerializer):
    """إعلان وظيفي"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    employment_type_display = drf_serializers.CharField(source='get_employment_type_display', read_only=True)
    requisition_title = drf_serializers.CharField(source='requisition.position', read_only=True, default=None)
    created_by_name = drf_serializers.CharField(source='created_by.username', read_only=True, default=None)
    is_active = drf_serializers.BooleanField(read_only=True)

    class Meta:
        model = JobPosting
        fields = (
            'id', 'posting_number', 'requisition', 'title', 'description',
            'requirements', 'benefits', 'location', 'employment_type',
            'salary_range', 'is_internal', 'is_external', 'posted_on', 'status',
            'published_at', 'closes_at', 'applications_count', 'created_by',
            'created_at', 'updated_at', 'status_display', 'employment_type_display',
            'requisition_title', 'created_by_name', 'is_active',
        )
        read_only_fields = ('posting_number', 'applications_count', 'created_at', 'updated_at')


class JobApplicationSerializer(drf_serializers.ModelSerializer):
    """طلب توظيف (سيرة ذاتية)"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    source_display = drf_serializers.CharField(source='get_source_display', read_only=True)
    full_name = drf_serializers.CharField(read_only=True)
    posting_title = drf_serializers.CharField(source='posting.title', read_only=True, default=None)
    assigned_to_name = drf_serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    interviews_count = drf_serializers.IntegerField(read_only=True)

    class Meta:
        model = JobApplication
        fields = (
            'id', 'application_number', 'posting', 'requisition', 'first_name',
            'last_name', 'email', 'phone', 'national_id', 'date_of_birth',
            'gender', 'education', 'experience_years', 'current_company',
            'current_position', 'expected_salary', 'cv_file', 'cover_letter',
            'linkedin_profile', 'source', 'status', 'rating', 'assigned_to',
            'notes', 'rejection_reason', 'created_at', 'updated_at',
            'status_display', 'source_display', 'full_name', 'posting_title',
            'assigned_to_name', 'interviews_count',
        )
        read_only_fields = ('application_number', 'created_at', 'updated_at')


class InterviewSerializer(drf_serializers.ModelSerializer):
    """مقابلة"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    interview_type_display = drf_serializers.CharField(source='get_interview_type_display', read_only=True)
    recommendation_display = drf_serializers.CharField(source='get_recommendation_display', read_only=True, default=None)
    candidate_name = drf_serializers.CharField(read_only=True)
    interviewer_name = drf_serializers.CharField(source='interviewer.username', read_only=True, default=None)

    class Meta:
        model = Interview
        fields = (
            'id', 'application', 'interview_type', 'interviewer',
            'scheduled_date', 'duration_minutes', 'location', 'status',
            'technical_score', 'behavioral_score', 'communication_score',
            'overall_score', 'strengths', 'weaknesses', 'recommendation',
            'notes', 'created_at', 'updated_at', 'status_display',
            'interview_type_display', 'recommendation_display',
            'candidate_name', 'interviewer_name',
        )
        read_only_fields = ('overall_score', 'created_at', 'updated_at')


class JobOfferSerializer(drf_serializers.ModelSerializer):
    """عرض وظيفي"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    candidate_name = drf_serializers.CharField(read_only=True)
    department_name = drf_serializers.CharField(source='department.name', read_only=True, default=None)
    total_compensation = drf_serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    created_by_name = drf_serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = JobOffer
        fields = (
            'id', 'offer_number', 'application', 'requisition', 'position',
            'department', 'proposed_salary', 'housing_allowance',
            'transport_allowance', 'other_allowances', 'employment_type',
            'start_date', 'contract_duration', 'probation_months', 'status',
            'sent_at', 'responded_at', 'notes', 'created_by', 'created_at',
            'updated_at', 'status_display', 'candidate_name', 'department_name',
            'total_compensation', 'created_by_name',
        )
        read_only_fields = ('offer_number', 'created_at', 'updated_at')


class HireCandidateSerializer(drf_serializers.Serializer):
    """تسليم عقد لتعيين مرشح"""
    offer_id = drf_serializers.IntegerField(help_text='معرف العرض الوظيفي')


# ─── Qualification Serializers ──────────────────

class EducationSerializer(drf_serializers.ModelSerializer):
    """مؤهل تعليمي"""
    degree_display = drf_serializers.CharField(source='get_degree_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)

    class Meta:
        model = Education
        fields = (
            'id', 'employee', 'institution', 'degree', 'major', 'gpa',
            'graduation_date', 'country', 'certificate_file', 'verified',
            'notes', 'created_at', 'degree_display', 'employee_name',
            'employee_number',
        )
        read_only_fields = ('created_at',)


class ExperienceSerializer(drf_serializers.ModelSerializer):
    """خبرة عملية"""
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    duration_months = drf_serializers.IntegerField(read_only=True)

    class Meta:
        model = Experience
        fields = (
            'id', 'employee', 'company_name', 'position', 'department',
            'start_date', 'end_date', 'is_current', 'responsibilities',
            'achievements', 'country', 'created_at', 'employee_name',
            'employee_number', 'duration_months',
        )
        read_only_fields = ('is_current', 'created_at')


class SkillSerializer(drf_serializers.ModelSerializer):
    """مهارة"""
    skill_type_display = drf_serializers.CharField(source='get_skill_type_display', read_only=True)
    proficiency_level_display = drf_serializers.CharField(source='get_proficiency_level_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)

    class Meta:
        model = Skill
        fields = (
            'id', 'employee', 'skill_name', 'skill_type', 'proficiency_level',
            'years_of_experience', 'certificate_name', 'certificate_file',
            'verified', 'created_at', 'skill_type_display',
            'proficiency_level_display', 'employee_name', 'employee_number',
        )
        read_only_fields = ('created_at',)


class LanguageSerializer(drf_serializers.ModelSerializer):
    """لغة"""
    proficiency_display = drf_serializers.CharField(source='get_proficiency_display', read_only=True)
    reading_display = drf_serializers.CharField(source='get_reading_display', read_only=True)
    writing_display = drf_serializers.CharField(source='get_writing_display', read_only=True)
    speaking_display = drf_serializers.CharField(source='get_speaking_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)

    class Meta:
        model = Language
        fields = (
            'id', 'employee', 'language', 'proficiency', 'reading', 'writing',
            'speaking', 'certificate_name', 'certificate_file', 'created_at',
            'proficiency_display', 'reading_display', 'writing_display',
            'speaking_display', 'employee_name', 'employee_number',
        )
        read_only_fields = ('created_at',)


class CertificationSerializer(drf_serializers.ModelSerializer):
    """شهادة مهنية"""
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)

    class Meta:
        model = Certification
        fields = (
            'id', 'employee', 'name', 'issuing_organization',
            'certificate_number', 'issue_date', 'expiry_date', 'is_expired',
            'credential_url', 'certificate_file', 'notes', 'created_at',
            'employee_name', 'employee_number',
        )
        read_only_fields = ('is_expired', 'created_at')


# ─── Document Serializers ───────────────────────

class EmployeeDocumentSerializer(drf_serializers.ModelSerializer):
    """وثيقة موظف"""
    document_type_display = drf_serializers.CharField(source='get_document_type_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    uploaded_by_name = drf_serializers.CharField(source='uploaded_by.username', read_only=True, default=None)
    verified_by_name = drf_serializers.CharField(source='verified_by.username', read_only=True, default=None)

    class Meta:
        model = EmployeeDocument
        fields = (
            'id', 'employee', 'document_type', 'title', 'description', 'file',
            'file_size', 'uploaded_by', 'expires_at', 'is_verified',
            'verified_by', 'verified_at', 'created_at', 'document_type_display',
            'employee_name', 'employee_number', 'uploaded_by_name',
            'verified_by_name',
        )
        read_only_fields = ('file_size', 'created_at')


class DocumentTemplateSerializer(drf_serializers.ModelSerializer):
    """قالب مستند"""
    document_type_display = drf_serializers.CharField(source='get_document_type_display', read_only=True)

    class Meta:
        model = DocumentTemplate
        fields = (
            'id', 'name', 'name_en', 'document_type', 'template_file',
            'description', 'is_active', 'created_at', 'document_type_display',
        )
        read_only_fields = ('created_at',)


# ─── Training Serializers ───────────────────────

class TrainingNeedSerializer(drf_serializers.ModelSerializer):
    """احتياج تدريبي"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    priority_display = drf_serializers.CharField(source='get_priority_display', read_only=True)
    department_name = drf_serializers.CharField(source='department.name', read_only=True, default=None)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True, default=None)
    identified_by_name = drf_serializers.CharField(source='identified_by.username', read_only=True, default=None)

    class Meta:
        model = TrainingNeed
        fields = (
            'id', 'department', 'employee', 'skill_gap', 'priority',
            'suggested_training', 'target_date', 'status', 'identified_by',
            'created_at', 'updated_at', 'status_display', 'priority_display',
            'department_name', 'employee_name', 'identified_by_name',
        )
        read_only_fields = ('created_at', 'updated_at')


class CourseSerializer(drf_serializers.ModelSerializer):
    """دورة تدريبية"""
    training_type_display = drf_serializers.CharField(source='get_training_type_display', read_only=True)
    category_display = drf_serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Course
        fields = (
            'id', 'code', 'name', 'name_en', 'description', 'provider',
            'training_type', 'category', 'duration_hours', 'max_participants',
            'cost_per_participant', 'total_budget', 'certificate_offered',
            'is_active', 'created_at', 'updated_at', 'training_type_display',
            'category_display',
        )
        read_only_fields = ('created_at', 'updated_at')


class TrainingSessionSerializer(drf_serializers.ModelSerializer):
    """جلسة تدريبية"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    course_name = drf_serializers.CharField(source='course.name', read_only=True)
    course_code = drf_serializers.CharField(source='course.code', read_only=True)
    enrolled_count = drf_serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainingSession
        fields = (
            'id', 'course', 'session_number', 'start_date', 'end_date',
            'location', 'instructor', 'status', 'actual_cost', 'notes',
            'created_at', 'updated_at', 'status_display', 'course_name',
            'course_code', 'enrolled_count',
        )
        read_only_fields = ('created_at', 'updated_at')


class TrainingEnrollmentSerializer(drf_serializers.ModelSerializer):
    """تسجيل في تدريب"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    session_info = TrainingSessionSerializer(source='session', read_only=True)

    class Meta:
        model = TrainingEnrollment
        fields = (
            'id', 'session', 'employee', 'enrollment_date', 'status',
            'completion_date', 'score', 'passed', 'certificate_issued',
            'certificate_file', 'feedback', 'feedback_notes', 'cost',
            'created_at', 'updated_at', 'status_display', 'employee_name',
            'employee_number', 'session_info',
        )
        read_only_fields = ('passed', 'created_at', 'updated_at')


class TrainingBudgetSerializer(drf_serializers.ModelSerializer):
    """ميزانية التدريب"""
    department_name = drf_serializers.CharField(source='department.name', read_only=True, default=None)
    remaining_amount = drf_serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    utilization_percentage = drf_serializers.FloatField(read_only=True)
    approved_by_name = drf_serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = TrainingBudget
        fields = (
            'id', 'year', 'department', 'total_budget', 'utilized_amount',
            'approved_by', 'approved_at', 'notes', 'created_at', 'updated_at',
            'department_name', 'remaining_amount', 'utilization_percentage',
            'approved_by_name',
        )
        read_only_fields = ('created_at', 'updated_at')


# ─── Employee Finance Serializers ───────────────

class LoanSerializer(drf_serializers.ModelSerializer):
    """قرض"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    loan_type_display = drf_serializers.CharField(source='get_loan_type_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    approved_by_name = drf_serializers.CharField(source='approved_by.username', read_only=True, default=None)
    guarantor_employee_name = drf_serializers.CharField(
        source='guarantor_employee.full_name', read_only=True, default=None,
    )
    total_paid = drf_serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    progress_percentage = drf_serializers.FloatField(read_only=True)
    installments_paid_count = drf_serializers.IntegerField(read_only=True)
    installments_overdue_count = drf_serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = (
            'id', 'loan_number', 'employee', 'loan_type', 'amount',
            'interest_rate', 'repayment_period_months', 'monthly_installment',
            'total_remaining', 'start_date', 'end_date', 'status', 'purpose',
            'approved_by', 'approved_at', 'guarantor', 'guarantor_employee',
            'notes', 'created_at', 'updated_at', 'status_display',
            'loan_type_display', 'employee_name', 'employee_number',
            'approved_by_name', 'guarantor_employee_name', 'total_paid',
            'progress_percentage', 'installments_paid_count',
            'installments_overdue_count',
        )
        read_only_fields = (
            'loan_number', 'monthly_installment', 'total_remaining',
            'created_at', 'updated_at',
        )


class LoanCreateSerializer(drf_serializers.ModelSerializer):
    """إنشاء قرض"""
    class Meta:
        model = Loan
        fields = (
            'employee', 'loan_type', 'amount', 'interest_rate',
            'repayment_period_months', 'start_date', 'end_date',
            'purpose', 'guarantor', 'guarantor_employee', 'notes',
        )


class LoanPaymentSerializer(drf_serializers.ModelSerializer):
    """قسط قرض"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    remaining_amount = drf_serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    loan_number = drf_serializers.CharField(source='loan.loan_number', read_only=True)

    class Meta:
        model = LoanPayment
        fields = (
            'id', 'loan', 'payment_number', 'due_date', 'amount',
            'paid_amount', 'payment_date', 'status', 'payslip', 'notes',
            'created_at', 'status_display', 'remaining_amount', 'loan_number',
        )
        read_only_fields = ('status', 'created_at')


class SalaryAdvanceSerializer(drf_serializers.ModelSerializer):
    """سلفة"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    approved_by_name = drf_serializers.CharField(source='approved_by.username', read_only=True, default=None)
    progress_percentage = drf_serializers.FloatField(read_only=True)
    months_remaining = drf_serializers.IntegerField(read_only=True)

    class Meta:
        model = SalaryAdvance
        fields = (
            'id', 'advance_number', 'employee', 'amount', 'reason',
            'repayment_months', 'monthly_deduction', 'total_deducted',
            'total_remaining', 'request_date', 'status', 'approved_by',
            'approved_at', 'notes', 'created_at', 'updated_at',
            'status_display', 'employee_name', 'employee_number',
            'approved_by_name', 'progress_percentage', 'months_remaining',
        )
        read_only_fields = (
            'advance_number', 'monthly_deduction', 'total_deducted',
            'total_remaining', 'created_at', 'updated_at',
        )


class SalaryAdvanceCreateSerializer(drf_serializers.ModelSerializer):
    """إنشاء سلفة"""
    class Meta:
        model = SalaryAdvance
        fields = ('employee', 'amount', 'reason', 'repayment_months', 'request_date', 'notes')


class OvertimeRequestSerializer(drf_serializers.ModelSerializer):
    """طلب أجور إضافية"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    overtime_type_display = drf_serializers.CharField(source='get_overtime_type_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    approved_by_name = drf_serializers.CharField(source='approved_by.username', read_only=True, default=None)
    duration_display = drf_serializers.CharField(read_only=True)
    rate_display = drf_serializers.CharField(read_only=True)

    class Meta:
        model = OvertimeRequest
        fields = (
            'id', 'employee', 'date', 'start_time', 'end_time', 'hours',
            'overtime_type', 'rate_multiplier', 'hourly_rate', 'total_amount',
            'reason', 'status', 'approved_by', 'approved_at',
            'paid_in_payslip', 'payslip', 'notes', 'created_at', 'updated_at',
            'status_display', 'overtime_type_display', 'employee_name',
            'employee_number', 'approved_by_name', 'duration_display',
            'rate_display',
        )
        read_only_fields = (
            'hours', 'rate_multiplier', 'hourly_rate', 'total_amount',
            'created_at', 'updated_at',
        )


class OvertimeApproveSerializer(drf_serializers.Serializer):
    """موافقة / رفض طلب أجور إضافية"""
    action = drf_serializers.ChoiceField(
        choices=('approve', 'reject'),
        error_messages={'invalid_choice': 'إجراء غير صالح، يجب أن يكون approve أو reject'},
    )
    notes = drf_serializers.CharField(required=False, allow_blank=True, default='')


# ─── Benefits & Discipline Serializers ──────────

class HealthInsuranceSerializer(drf_serializers.ModelSerializer):
    """تأمين صحي"""
    plan_type_display = drf_serializers.CharField(source='get_plan_type_display', read_only=True)
    network_type_display = drf_serializers.CharField(source='get_network_type_display', read_only=True)
    total_monthly_premium = drf_serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_annual_premium = drf_serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    enrolled_count = drf_serializers.SerializerMethodField()

    class Meta:
        model = HealthInsurance
        fields = (
            'id', 'insurance_provider', 'plan_name', 'plan_type',
            'monthly_premium_employee', 'monthly_premium_company',
            'coverage_amount', 'network_type', 'is_active', 'created_at',
            'updated_at', 'plan_type_display', 'network_type_display',
            'total_monthly_premium', 'total_annual_premium', 'enrolled_count',
        )
        read_only_fields = ('created_at', 'updated_at')

    def get_enrolled_count(self, obj):
        return obj.enrollments.filter(status='active').count()


class EmployeeInsuranceSerializer(drf_serializers.ModelSerializer):
    """تسجيل تأمين موظف"""
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    plan_name = drf_serializers.CharField(source='insurance.plan_name', read_only=True)
    provider_name = drf_serializers.CharField(source='insurance.insurance_provider', read_only=True)

    class Meta:
        model = EmployeeInsurance
        fields = (
            'id', 'employee', 'insurance', 'policy_number', 'member_id',
            'start_date', 'end_date', 'status', 'dependents_count', 'notes',
            'created_at', 'status_display', 'employee_name', 'employee_number',
            'plan_name', 'provider_name',
        )
        read_only_fields = ('created_at',)


class DisciplinaryActionSerializer(drf_serializers.ModelSerializer):
    """إجراء تأديبي"""
    action_type_display = drf_serializers.CharField(source='get_action_type_display', read_only=True)
    severity_level_display = drf_serializers.CharField(source='get_severity_level_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    issued_by_name = drf_serializers.CharField(source='issued_by.username', read_only=True, default=None)

    class Meta:
        model = DisciplinaryAction
        fields = (
            'id', 'action_number', 'employee', 'action_type', 'severity_level',
            'reason', 'incident_date', 'incident_description', 'witnesses',
            'issued_by', 'acknowledged_by_employee', 'acknowledged_at',
            'effective_date', 'end_date', 'is_active', 'related_docs',
            'created_at', 'updated_at', 'action_type_display',
            'severity_level_display', 'employee_name', 'employee_number',
            'issued_by_name',
        )
        read_only_fields = ('action_number', 'created_at', 'updated_at')


class GrievanceSerializer(drf_serializers.ModelSerializer):
    """شكوى"""
    grievance_type_display = drf_serializers.CharField(source='get_grievance_type_display', read_only=True)
    priority_display = drf_serializers.CharField(source='get_priority_display', read_only=True)
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    assigned_to_name = drf_serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    resolved_by_name = drf_serializers.CharField(source='resolved_by.username', read_only=True, default=None)

    class Meta:
        model = Grievance
        fields = (
            'id', 'grievance_number', 'employee', 'grievance_type', 'priority',
            'description', 'resolution_requested', 'status', 'assigned_to',
            'resolution', 'resolution_date', 'resolved_by', 'attachments',
            'is_confidential', 'created_at', 'updated_at',
            'grievance_type_display', 'priority_display', 'status_display',
            'employee_name', 'employee_number', 'assigned_to_name',
            'resolved_by_name',
        )
        read_only_fields = ('grievance_number', 'created_at', 'updated_at')


class OffboardingSerializer(drf_serializers.ModelSerializer):
    """إنهاء خدمات"""
    offboarding_type_display = drf_serializers.CharField(source='get_offboarding_type_display', read_only=True)
    status_display = drf_serializers.CharField(source='get_status_display', read_only=True)
    clearance_status_display = drf_serializers.CharField(source='get_clearance_status_display', read_only=True)
    employee_name = drf_serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = drf_serializers.CharField(source='employee.employee_number', read_only=True)
    approved_by_name = drf_serializers.CharField(source='approved_by.username', read_only=True, default=None)
    net_settlement = drf_serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_deductions = drf_serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Offboarding
        fields = (
            'id', 'employee', 'offboarding_type', 'last_working_day', 'reason',
            'exit_interview_conducted', 'exit_interview_notes',
            'exit_interview_date', 'clearance_status',
            'final_settlement_amount', 'end_of_service_benefit',
            'outstanding_loans', 'outstanding_advances', 'checklist',
            'knowledge_transfer_done', 'approved_by', 'approved_at',
            'status', 'notes', 'created_at', 'updated_at',
            'offboarding_type_display', 'status_display',
            'clearance_status_display', 'employee_name', 'employee_number',
            'approved_by_name', 'net_settlement', 'total_deductions',
        )
        read_only_fields = ('created_at', 'updated_at')


# ═══════════════════════════════════════════════════
# RECRUITMENT VIEWS
# ═══════════════════════════════════════════════════

class JobRequisitionListView(generics.ListCreateAPIView):
    """قائمة طلبات التوظيف + إنشاء طلب جديد"""
    serializer_class = JobRequisitionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = JobRequisition.objects.select_related('department', 'requested_by', 'approved_by')
        status_val = self.request.query_params.get('status')
        department_id = self.request.query_params.get('department')
        priority = self.request.query_params.get('priority')
        employment_type = self.request.query_params.get('employment_type')
        search = self.request.query_params.get('search')

        if status_val:
            qs = qs.filter(status=status_val)
        if department_id:
            qs = qs.filter(department_id=department_id)
        if priority:
            qs = qs.filter(priority=priority)
        if employment_type:
            qs = qs.filter(employment_type=employment_type)
        if search:
            qs = qs.filter(
                Q(position__icontains=search)
                | Q(requisition_number__icontains=search)
            )
        return qs


class JobRequisitionDetailView(generics.RetrieveUpdateAPIView):
    """تفاصيل طلب توظيف + تحديث"""
    serializer_class = JobRequisitionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('PATCH', 'PUT'):
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return JobRequisition.objects.select_related(
            'department', 'requested_by', 'approved_by',
        )


class JobPostingListView(generics.ListCreateAPIView):
    """قائمة الإعلانات الوظيفية + إنشاء إعلان جديد"""
    serializer_class = JobPostingSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = JobPosting.objects.select_related('requisition', 'created_by')
        status_val = self.request.query_params.get('status')
        employment_type = self.request.query_params.get('employment_type')
        requisition_id = self.request.query_params.get('requisition')
        is_published = self.request.query_params.get('is_published')
        search = self.request.query_params.get('search')

        if status_val:
            qs = qs.filter(status=status_val)
        if employment_type:
            qs = qs.filter(employment_type=employment_type)
        if requisition_id:
            qs = qs.filter(requisition_id=requisition_id)
        if is_published == 'true':
            qs = qs.filter(status='published', closes_at__gte=timezone.now())
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(posting_number__icontains=search))
        return qs


class JobPostingDetailView(generics.RetrieveUpdateAPIView):
    """تفاصيل إعلان وظيفي + تحديث"""
    serializer_class = JobPostingSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('PATCH', 'PUT'):
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return JobPosting.objects.select_related('requisition', 'created_by')


class JobApplicationListView(generics.ListAPIView):
    """قائمة طلبات التوظيف (السير الذاتية) — قراءة فقط"""
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = JobApplication.objects.select_related('posting', 'requisition', 'assigned_to')
        status_val = self.request.query_params.get('status')
        posting_id = self.request.query_params.get('posting')
        requisition_id = self.request.query_params.get('requisition')
        source = self.request.query_params.get('source')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        search = self.request.query_params.get('search')
        rating = self.request.query_params.get('rating')

        if status_val:
            qs = qs.filter(status=status_val)
        if posting_id:
            qs = qs.filter(posting_id=posting_id)
        if requisition_id:
            qs = qs.filter(requisition_id=requisition_id)
        if source:
            qs = qs.filter(source=source)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if rating:
            qs = qs.filter(rating=rating)
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(application_number__icontains=search)
            )
        return qs


class JobApplicationDetailView(generics.RetrieveUpdateAPIView):
    """تفاصيل طلب توظيف + تحديث الحالة/التقييم"""
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('PATCH', 'PUT'):
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return JobApplication.objects.select_related('posting', 'requisition', 'assigned_to')


class InterviewListView(generics.ListAPIView):
    """قائمة المقابلات — قراءة فقط"""
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Interview.objects.select_related('application', 'interviewer')
        application_id = self.request.query_params.get('application')
        status_val = self.request.query_params.get('status')
        interview_type = self.request.query_params.get('interview_type')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if application_id:
            qs = qs.filter(application_id=application_id)
        if status_val:
            qs = qs.filter(status=status_val)
        if interview_type:
            qs = qs.filter(interview_type=interview_type)
        if date_from:
            qs = qs.filter(scheduled_date__date__gte=date_from)
        if date_to:
            qs = qs.filter(scheduled_date__date__lte=date_to)
        return qs


class InterviewCreateView(generics.CreateAPIView):
    """إنشاء مقابلة جديدة لطلب توظيف"""
    serializer_class = InterviewSerializer
    permission_classes = [IsHROrAdmin]
    queryset = Interview.objects.all()


class InterviewDetailView(generics.RetrieveUpdateAPIView):
    """تفاصيل مقابلة + تحديث الدرجات"""
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('PATCH', 'PUT'):
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Interview.objects.select_related('application', 'interviewer')


class JobOfferListView(generics.ListCreateAPIView):
    """قائمة العروض الوظيفية + إنشاء عرض جديد"""
    serializer_class = JobOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = JobOffer.objects.select_related('application', 'requisition', 'department', 'created_by')
        status_val = self.request.query_params.get('status')
        department_id = self.request.query_params.get('department')
        requisition_id = self.request.query_params.get('requisition')

        if status_val:
            qs = qs.filter(status=status_val)
        if department_id:
            qs = qs.filter(department_id=department_id)
        if requisition_id:
            qs = qs.filter(requisition_id=requisition_id)
        return qs


class JobOfferDetailView(generics.RetrieveUpdateAPIView):
    """تفاصيل عرض وظيفي + تحديث الحالة"""
    serializer_class = JobOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('PATCH', 'PUT'):
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return JobOffer.objects.select_related('application', 'requisition', 'department', 'created_by')


class HireCandidateView(views.APIView):
    """تعيين مرشح: إنشاء سجل موظف من عرض وظيفي مقبول"""
    permission_classes = [IsHROrAdmin]

    def post(self, request):
        serializer = HireCandidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            offer = JobOffer.objects.select_related('application', 'department').get(
                id=serializer.validated_data['offer_id'],
            )
        except JobOffer.DoesNotExist:
            return Response(
                {'detail': 'العرض الوظيفي غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if offer.status != 'accepted':
            return Response(
                {'detail': 'لا يمكن التعيين إلا لعروض وظيفية مقبولة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = hire_candidate(offer, request.user)

        return Response(
            {
                'detail': f'تم تعيين المرشح {employee.full_name} بنجاح',
                'employee_id': employee.id,
                'employee_number': employee.employee_number,
            },
            status=status.HTTP_201_CREATED,
        )


# ═══════════════════════════════════════════════════
# QUALIFICATION VIEWS
# ═══════════════════════════════════════════════════

class EducationListView(generics.ListAPIView):
    """قائمة المؤهلات التعليمية لموظف"""
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Education.objects.select_related('employee')
        employee_id = self.request.query_params.get('employee_id')
        degree = self.request.query_params.get('degree')
        verified = self.request.query_params.get('verified')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if degree:
            qs = qs.filter(degree=degree)
        if verified is not None:
            qs = qs.filter(verified=(verified.lower() == 'true'))
        return qs


class EducationCreateView(generics.CreateAPIView):
    """إضافة مؤهل تعليمي"""
    serializer_class = EducationSerializer
    permission_classes = [IsHROrAdmin]
    queryset = Education.objects.all()


class ExperienceListView(generics.ListAPIView):
    """قائمة الخبرات العملية لموظف"""
    serializer_class = ExperienceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Experience.objects.select_related('employee')
        employee_id = self.request.query_params.get('employee_id')
        is_current = self.request.query_params.get('is_current')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if is_current is not None:
            qs = qs.filter(is_current=(is_current.lower() == 'true'))
        return qs


class ExperienceCreateView(generics.CreateAPIView):
    """إضافة خبرة عملية"""
    serializer_class = ExperienceSerializer
    permission_classes = [IsHROrAdmin]
    queryset = Experience.objects.all()


class SkillListView(generics.ListAPIView):
    """قائمة المهارات لموظف"""
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Skill.objects.select_related('employee')
        employee_id = self.request.query_params.get('employee_id')
        skill_type = self.request.query_params.get('skill_type')
        proficiency_level = self.request.query_params.get('proficiency_level')
        verified = self.request.query_params.get('verified')
        search = self.request.query_params.get('search')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if skill_type:
            qs = qs.filter(skill_type=skill_type)
        if proficiency_level:
            qs = qs.filter(proficiency_level=proficiency_level)
        if verified is not None:
            qs = qs.filter(verified=(verified.lower() == 'true'))
        if search:
            qs = qs.filter(skill_name__icontains=search)
        return qs


class SkillCreateView(generics.CreateAPIView):
    """إضافة مهارة"""
    serializer_class = SkillSerializer
    permission_classes = [IsHROrAdmin]
    queryset = Skill.objects.all()


class LanguageListView(generics.ListAPIView):
    """قائمة اللغات لموظف"""
    serializer_class = LanguageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Language.objects.select_related('employee')
        employee_id = self.request.query_params.get('employee_id')
        proficiency = self.request.query_params.get('proficiency')
        language = self.request.query_params.get('language')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if proficiency:
            qs = qs.filter(proficiency=proficiency)
        if language:
            qs = qs.filter(language__icontains=language)
        return qs


class LanguageCreateView(generics.CreateAPIView):
    """إضافة لغة"""
    serializer_class = LanguageSerializer
    permission_classes = [IsHROrAdmin]
    queryset = Language.objects.all()


class CertificationListView(generics.ListAPIView):
    """قائمة الشهادات المهنية لموظف"""
    serializer_class = CertificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Certification.objects.select_related('employee')
        employee_id = self.request.query_params.get('employee_id')
        is_expired = self.request.query_params.get('is_expired')
        search = self.request.query_params.get('search')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if is_expired is not None:
            qs = qs.filter(is_expired=(is_expired.lower() == 'true'))
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(issuing_organization__icontains=search))
        return qs


class CertificationCreateView(generics.CreateAPIView):
    """إضافة شهادة مهنية"""
    serializer_class = CertificationSerializer
    permission_classes = [IsHROrAdmin]
    queryset = Certification.objects.all()


# ═══════════════════════════════════════════════════
# DOCUMENT VIEWS
# ═══════════════════════════════════════════════════

class EmployeeDocumentListView(generics.ListAPIView):
    """قائمة وثائق الموظف"""
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = EmployeeDocument.objects.select_related('employee', 'uploaded_by', 'verified_by')
        employee_id = self.request.query_params.get('employee_id')
        document_type = self.request.query_params.get('document_type')
        is_verified = self.request.query_params.get('is_verified')
        search = self.request.query_params.get('search')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if document_type:
            qs = qs.filter(document_type=document_type)
        if is_verified is not None:
            qs = qs.filter(is_verified=(is_verified.lower() == 'true'))
        if search:
            qs = qs.filter(title__icontains=search)
        return qs


class EmployeeDocumentCreateView(generics.CreateAPIView):
    """رفع وثيقة جديدة"""
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsHROrAdmin]
    queryset = EmployeeDocument.objects.all()


class DocumentTemplateListView(generics.ListAPIView):
    """قائمة قوالب المستندات"""
    serializer_class = DocumentTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = DocumentTemplate.objects.all()
        document_type = self.request.query_params.get('document_type')
        is_active = self.request.query_params.get('is_active')

        if document_type:
            qs = qs.filter(document_type=document_type)
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() == 'true'))
        return qs


class DocumentTemplateDetailView(generics.RetrieveAPIView):
    """تفاصيل قالب مستند"""
    serializer_class = DocumentTemplateSerializer
    permission_classes = [IsAuthenticated]
    queryset = DocumentTemplate.objects.all()


# ═══════════════════════════════════════════════════
# TRAINING VIEWS
# ═══════════════════════════════════════════════════

class TrainingNeedListView(generics.ListAPIView):
    """قائمة الاحتياجات التدريبية"""
    serializer_class = TrainingNeedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TrainingNeed.objects.select_related('department', 'employee', 'identified_by')
        department_id = self.request.query_params.get('department')
        employee_id = self.request.query_params.get('employee_id')
        status_val = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')

        if department_id:
            qs = qs.filter(department_id=department_id)
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if status_val:
            qs = qs.filter(status=status_val)
        if priority:
            qs = qs.filter(priority=priority)
        return qs


class TrainingNeedCreateView(generics.CreateAPIView):
    """إضافة احتياج تدريبي جديد"""
    serializer_class = TrainingNeedSerializer
    permission_classes = [IsHROrAdmin]
    queryset = TrainingNeed.objects.all()


class CourseListView(generics.ListAPIView):
    """قائمة الدورات التدريبية"""
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Course.objects.all()
        training_type = self.request.query_params.get('training_type')
        category = self.request.query_params.get('category')
        is_active = self.request.query_params.get('is_active')
        search = self.request.query_params.get('search')

        if training_type:
            qs = qs.filter(training_type=training_type)
        if category:
            qs = qs.filter(category=category)
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() == 'true'))
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
        return qs


class CourseDetailView(generics.RetrieveAPIView):
    """تفاصيل دورة تدريبية"""
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    queryset = Course.objects.all()


class TrainingSessionListView(generics.ListAPIView):
    """قائمة الجلسات التدريبية"""
    serializer_class = TrainingSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TrainingSession.objects.select_related('course')
        course_id = self.request.query_params.get('course')
        status_val = self.request.query_params.get('status')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if course_id:
            qs = qs.filter(course_id=course_id)
        if status_val:
            qs = qs.filter(status=status_val)
        if date_from:
            qs = qs.filter(start_date__gte=date_from)
        if date_to:
            qs = qs.filter(end_date__lte=date_to)
        return qs


class TrainingSessionCreateView(generics.CreateAPIView):
    """إنشاء جلسة تدريبية جديدة"""
    serializer_class = TrainingSessionSerializer
    permission_classes = [IsHROrAdmin]
    queryset = TrainingSession.objects.all()


class TrainingEnrollmentListView(generics.ListAPIView):
    """قائمة تسجيلات التدريب"""
    serializer_class = TrainingEnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TrainingEnrollment.objects.select_related('session', 'session__course', 'employee')
        session_id = self.request.query_params.get('session')
        employee_id = self.request.query_params.get('employee_id')
        status_val = self.request.query_params.get('status')

        if session_id:
            qs = qs.filter(session_id=session_id)
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if status_val:
            qs = qs.filter(status=status_val)
        return qs


class TrainingEnrollmentCreateView(generics.CreateAPIView):
    """تسجيل موظف في دورة تدريبية"""
    serializer_class = TrainingEnrollmentSerializer
    permission_classes = [IsHROrAdmin]
    queryset = TrainingEnrollment.objects.all()


class TrainingBudgetListView(generics.ListAPIView):
    """قائمة ميزانيات التدريب"""
    serializer_class = TrainingBudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TrainingBudget.objects.select_related('department', 'approved_by')
        year = self.request.query_params.get('year')
        department_id = self.request.query_params.get('department')

        if year:
            qs = qs.filter(year=year)
        if department_id:
            qs = qs.filter(department_id=department_id)
        return qs


class TrainingBudgetDetailView(generics.RetrieveAPIView):
    """تفاصيل ميزانية التدريب"""
    serializer_class = TrainingBudgetSerializer
    permission_classes = [IsAuthenticated]
    queryset = TrainingBudget.objects.all()


# ═══════════════════════════════════════════════════
# EMPLOYEE FINANCE VIEWS
# ═══════════════════════════════════════════════════

class LoanListView(generics.ListAPIView):
    """قائمة القروض"""
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Loan.objects.select_related(
            'employee', 'approved_by', 'guarantor_employee',
        )
        employee_id = self.request.query_params.get('employee_id')
        status_val = self.request.query_params.get('status')
        loan_type = self.request.query_params.get('loan_type')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if status_val:
            qs = qs.filter(status=status_val)
        if loan_type:
            qs = qs.filter(loan_type=loan_type)
        return qs


class LoanCreateView(generics.CreateAPIView):
    """إنشاء قرض جديد"""
    serializer_class = LoanCreateSerializer
    permission_classes = [IsHROrAdmin]
    queryset = Loan.objects.all()


class LoanDetailView(generics.RetrieveAPIView):
    """تفاصيل قرض"""
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    queryset = Loan.objects.select_related(
        'employee', 'approved_by', 'guarantor_employee',
    )


class LoanPaymentListView(generics.ListAPIView):
    """قائمة أقساط القرض — فلترة حسب القرض"""
    serializer_class = LoanPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = LoanPayment.objects.select_related('loan')
        loan_id = self.request.query_params.get('loan')
        status_val = self.request.query_params.get('status')

        if loan_id:
            qs = qs.filter(loan_id=loan_id)
        if status_val:
            qs = qs.filter(status=status_val)
        return qs


class SalaryAdvanceListView(generics.ListAPIView):
    """قائمة السلف"""
    serializer_class = SalaryAdvanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SalaryAdvance.objects.select_related('employee', 'approved_by')
        employee_id = self.request.query_params.get('employee_id')
        status_val = self.request.query_params.get('status')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if status_val:
            qs = qs.filter(status=status_val)
        if date_from:
            qs = qs.filter(request_date__gte=date_from)
        if date_to:
            qs = qs.filter(request_date__lte=date_to)
        return qs


class SalaryAdvanceCreateView(generics.CreateAPIView):
    """إنشاء سلفة جديدة"""
    serializer_class = SalaryAdvanceCreateSerializer
    permission_classes = [IsHROrAdmin]
    queryset = SalaryAdvance.objects.all()


class OvertimeRequestListView(generics.ListAPIView):
    """قائمة طلبات الأجور الإضافية"""
    serializer_class = OvertimeRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = OvertimeRequest.objects.select_related('employee', 'approved_by')
        employee_id = self.request.query_params.get('employee_id')
        status_val = self.request.query_params.get('status')
        overtime_type = self.request.query_params.get('overtime_type')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if status_val:
            qs = qs.filter(status=status_val)
        if overtime_type:
            qs = qs.filter(overtime_type=overtime_type)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs


class OvertimeRequestCreateView(generics.CreateAPIView):
    """إنشاء طلب أجور إضافية"""
    serializer_class = OvertimeRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # الموظف نفسه أو الموارد البشرية يمكنهم الإنشاء
        if self.request.method == 'POST':
            return [IsHROrAdmin()]
        return [IsAuthenticated()]

    queryset = OvertimeRequest.objects.all()


class OvertimeApproveView(views.APIView):
    """موافقة أو رفض طلب أجور إضافية"""
    permission_classes = [IsHROrAdmin]

    def post(self, request, pk):
        try:
            overtime = OvertimeRequest.objects.get(pk=pk)
        except OvertimeRequest.DoesNotExist:
            return Response(
                {'detail': 'طلب الأجور الإضافية غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OvertimeApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')

        if overtime.status != 'pending':
            return Response(
                {'detail': 'لا يمكن معالجة هذا الطلب لأنه ليس في حالة انتظار'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == 'approve':
            overtime.status = 'approved'
            overtime.approved_by = request.user
            overtime.approved_at = timezone.now()
            message = 'تمت الموافقة على طلب الأجور الإضافية بنجاح'
        else:
            overtime.status = 'rejected'
            overtime.approved_by = request.user
            overtime.approved_at = timezone.now()
            message = 'تم رفض طلب الأجور الإضافية'

        if notes:
            overtime.notes = (overtime.notes + '\n' + notes).strip() if overtime.notes else notes
        overtime.save()

        return Response(
            {'detail': message, 'status': overtime.status},
            status=status.HTTP_200_OK,
        )


# ═══════════════════════════════════════════════════
# BENEFITS & DISCIPLINE VIEWS
# ═══════════════════════════════════════════════════

class HealthInsuranceListView(generics.ListAPIView):
    """قائمة خطط التأمين الصحي"""
    serializer_class = HealthInsuranceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = HealthInsurance.objects.all()
        plan_type = self.request.query_params.get('plan_type')
        network_type = self.request.query_params.get('network_type')
        is_active = self.request.query_params.get('is_active')
        search = self.request.query_params.get('search')

        if plan_type:
            qs = qs.filter(plan_type=plan_type)
        if network_type:
            qs = qs.filter(network_type=network_type)
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() == 'true'))
        if search:
            qs = qs.filter(
                Q(insurance_provider__icontains=search) | Q(plan_name__icontains=search)
            )
        return qs


class HealthInsuranceDetailView(generics.RetrieveAPIView):
    """تفاصيل خطة التأمين الصحي"""
    serializer_class = HealthInsuranceSerializer
    permission_classes = [IsAuthenticated]
    queryset = HealthInsurance.objects.all()


class EmployeeInsuranceListView(generics.ListAPIView):
    """قائمة تسجيلات التأمين للموظفين"""
    serializer_class = EmployeeInsuranceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = EmployeeInsurance.objects.select_related('employee', 'insurance')
        employee_id = self.request.query_params.get('employee_id')
        insurance_id = self.request.query_params.get('insurance')
        status_val = self.request.query_params.get('status')
        policy_number = self.request.query_params.get('policy_number')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if insurance_id:
            qs = qs.filter(insurance_id=insurance_id)
        if status_val:
            qs = qs.filter(status=status_val)
        if policy_number:
            qs = qs.filter(policy_number__icontains=policy_number)
        return qs


class EmployeeInsuranceCreateView(generics.CreateAPIView):
    """تسجيل موظف في خطة تأمين"""
    serializer_class = EmployeeInsuranceSerializer
    permission_classes = [IsHROrAdmin]
    queryset = EmployeeInsurance.objects.all()


class DisciplinaryActionListView(generics.ListAPIView):
    """قائمة الإجراءات التأديبية"""
    serializer_class = DisciplinaryActionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = DisciplinaryAction.objects.select_related('employee', 'issued_by')
        employee_id = self.request.query_params.get('employee_id')
        action_type = self.request.query_params.get('action_type')
        severity = self.request.query_params.get('severity')
        is_active = self.request.query_params.get('is_active')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if action_type:
            qs = qs.filter(action_type=action_type)
        if severity:
            qs = qs.filter(severity_level=severity)
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() == 'true'))
        if date_from:
            qs = qs.filter(incident_date__gte=date_from)
        if date_to:
            qs = qs.filter(incident_date__lte=date_to)
        return qs


class DisciplinaryActionCreateView(generics.CreateAPIView):
    """إنشاء إجراء تأديبي جديد"""
    serializer_class = DisciplinaryActionSerializer
    permission_classes = [IsHROrAdmin]
    queryset = DisciplinaryAction.objects.all()


class GrievanceListView(generics.ListAPIView):
    """قائمة الشكاوى"""
    serializer_class = GrievanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Grievance.objects.select_related('employee', 'assigned_to', 'resolved_by')
        employee_id = self.request.query_params.get('employee_id')
        grievance_type = self.request.query_params.get('grievance_type')
        status_val = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if grievance_type:
            qs = qs.filter(grievance_type=grievance_type)
        if status_val:
            qs = qs.filter(status=status_val)
        if priority:
            qs = qs.filter(priority=priority)
        return qs


class GrievanceCreateView(generics.CreateAPIView):
    """إنشاء شكوى جديدة"""
    serializer_class = GrievanceSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # الموظف نفسه أو الموارد البشرية يمكنهم الإنشاء
        return [IsAuthenticated()]

    queryset = Grievance.objects.all()


class GrievanceDetailView(generics.RetrieveAPIView):
    """تفاصيل شكوى"""
    serializer_class = GrievanceSerializer
    permission_classes = [IsAuthenticated]
    queryset = Grievance.objects.select_related('employee', 'assigned_to', 'resolved_by')


class OffboardingListView(generics.ListAPIView):
    """قائمة عمليات إنهاء الخدمات"""
    serializer_class = OffboardingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Offboarding.objects.select_related('employee', 'approved_by')
        employee_id = self.request.query_params.get('employee_id')
        offboarding_type = self.request.query_params.get('offboarding_type')
        status_val = self.request.query_params.get('status')
        clearance_status = self.request.query_params.get('clearance_status')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if offboarding_type:
            qs = qs.filter(offboarding_type=offboarding_type)
        if status_val:
            qs = qs.filter(status=status_val)
        if clearance_status:
            qs = qs.filter(clearance_status=clearance_status)
        return qs


class OffboardingCreateView(generics.CreateAPIView):
    """إنشاء عملية إنهاء خدمات جديدة"""
    serializer_class = OffboardingSerializer
    permission_classes = [IsHROrAdmin]
    queryset = Offboarding.objects.all()
