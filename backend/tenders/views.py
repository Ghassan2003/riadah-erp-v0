"""
API views for the Tender Management module.
Handles Tenders, TenderDocuments, TenderBids, TenderEvaluations,
TenderAwards, stats, and export.
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
    Tender,
    TenderDocument,
    TenderBid,
    TenderEvaluation,
    TenderAward,
)
from .serializers import (
    TenderListSerializer,
    TenderCreateSerializer,
    TenderUpdateSerializer,
    TenderDetailSerializer,
    TenderDocumentListSerializer,
    TenderDocumentCreateSerializer,
    TenderBidListSerializer,
    TenderBidCreateSerializer,
    TenderBidUpdateSerializer,
    TenderEvaluationListSerializer,
    TenderEvaluationCreateSerializer,
    TenderEvaluationUpdateSerializer,
    TenderAwardListSerializer,
    TenderAwardCreateSerializer,
    TenderAwardApproveSerializer,
    TenderStatsSerializer,
)
from users.permissions import IsAdmin


# =============================================
# Tender Views
# =============================================

class TenderStatsView(views.APIView):
    """GET: Tender statistics for dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stats = {
            'total_tenders': Tender.objects.count(),
            'draft_tenders': Tender.objects.filter(status='draft').count(),
            'published_tenders': Tender.objects.filter(status='published').count(),
            'evaluation_tenders': Tender.objects.filter(status='evaluation').count(),
            'awarded_tenders': Tender.objects.filter(status='awarded').count(),
            'cancelled_tenders': Tender.objects.filter(status='cancelled').count(),
            'total_bids': TenderBid.objects.count(),
            'total_awards': TenderAward.objects.count(),
            'total_estimated_value': Tender.objects.aggregate(
                total=Coalesce(
                    Sum('estimated_value'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
            'total_contract_value': TenderAward.objects.filter(
                status='approved'
            ).aggregate(
                total=Coalesce(
                    Sum('contract_value'),
                    Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )['total'],
        }

        serializer = TenderStatsSerializer(stats)
        return Response(serializer.data)


class TenderListView(generics.ListCreateAPIView):
    """GET: List tenders. POST: Create tender (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'tender_number', 'description']
    ordering_fields = ['title', 'tender_number', 'status', 'estimated_value', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TenderCreateSerializer
        return TenderListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Tender.objects.select_related('department', 'project', 'created_by')
        # Filter by status
        tender_status = self.request.query_params.get('status')
        if tender_status:
            queryset = queryset.filter(status=tender_status)
        # Filter by tender_type
        tender_type = self.request.query_params.get('tender_type')
        if tender_type:
            queryset = queryset.filter(tender_type=tender_type)
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        # Filter by project
        project = self.request.query_params.get('project')
        if project:
            queryset = queryset.filter(project_id=project)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tender = serializer.save(created_by=request.user)
        return Response({
            'message': 'تم إنشاء المناقصة بنجاح',
            'tender': TenderDetailSerializer(tender).data,
        }, status=status.HTTP_201_CREATED)


class TenderDetailView(generics.RetrieveUpdateAPIView):
    """GET: Tender details. PATCH: Update tender (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TenderUpdateSerializer
        return TenderDetailSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Tender.objects.select_related('department', 'project', 'created_by')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        tender = serializer.save()
        return Response({
            'message': 'تم تحديث المناقصة بنجاح',
            'tender': TenderDetailSerializer(tender).data,
        })


class TenderDeleteView(views.APIView):
    """DELETE: Delete a tender (admin only)."""

    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            tender = Tender.objects.get(pk=pk)
        except Tender.DoesNotExist:
            return Response(
                {'error': 'المناقصة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if tender.status not in ('draft',):
            return Response(
                {'error': 'لا يمكن حذف مناقصة ليست في حالة مسودة'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tender.delete()
        return Response({'message': 'تم حذف المناقصة بنجاح'})


class TenderPublishView(views.APIView):
    """POST: Publish a tender (admin only). Changes status to published."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            tender = Tender.objects.get(pk=pk)
        except Tender.DoesNotExist:
            return Response(
                {'error': 'المناقصة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if tender.status != 'draft':
            return Response(
                {'error': 'لا يمكن نشر مناقصة ليست في حالة مسودة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not tender.closing_date:
            return Response(
                {'error': 'يجب تحديد تاريخ الإغلاق قبل النشر'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tender.status = 'published'
        tender.publish_date = timezone.now().date()
        tender.save()

        return Response({
            'message': 'تم نشر المناقصة بنجاح',
            'tender': TenderDetailSerializer(tender).data,
        })


# =============================================
# Tender Document Views
# =============================================

class TenderDocumentListView(generics.ListCreateAPIView):
    """GET: List tender documents. POST: Upload tender document (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title', 'uploaded_at']
    ordering = ['-uploaded_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TenderDocumentCreateSerializer
        return TenderDocumentListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = TenderDocument.objects.select_related('tender')
        # Filter by tender
        tender = self.request.query_params.get('tender')
        if tender:
            queryset = queryset.filter(tender_id=tender)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        return Response({
            'message': 'تم رفع المستند بنجاح',
            'document': TenderDocumentListSerializer(document).data,
        }, status=status.HTTP_201_CREATED)


class TenderDocumentDetailView(generics.RetrieveDestroyAPIView):
    """GET: Tender document details. DELETE: Delete tender document (admin only)."""

    serializer_class = TenderDocumentListSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return TenderDocument.objects.select_related('tender')


# =============================================
# Tender Bid Views
# =============================================

class TenderBidListView(generics.ListCreateAPIView):
    """GET: List tender bids. POST: Create tender bid (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['bid_number', 'supplier__name']
    ordering_fields = ['bid_number', 'total_amount', 'status', 'submission_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TenderBidCreateSerializer
        return TenderBidListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = TenderBid.objects.select_related('tender', 'supplier')
        # Filter by tender
        tender = self.request.query_params.get('tender')
        if tender:
            queryset = queryset.filter(tender_id=tender)
        # Filter by supplier
        supplier = self.request.query_params.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        # Filter by status
        bid_status = self.request.query_params.get('status')
        if bid_status:
            queryset = queryset.filter(status=bid_status)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bid = serializer.save()
        return Response({
            'message': 'تم إنشاء العرض بنجاح',
            'bid': TenderBidListSerializer(bid).data,
        }, status=status.HTTP_201_CREATED)


class TenderBidDetailView(generics.RetrieveUpdateAPIView):
    """GET: Tender bid details. PATCH: Update tender bid (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TenderBidUpdateSerializer
        return TenderBidListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return TenderBid.objects.select_related('tender', 'supplier')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        bid = serializer.save()
        return Response({
            'message': 'تم تحديث العرض بنجاح',
            'bid': TenderBidListSerializer(bid).data,
        })


class TenderBidDisqualifyView(views.APIView):
    """POST: Disqualify a tender bid (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            bid = TenderBid.objects.select_related('tender', 'supplier').get(pk=pk)
        except TenderBid.DoesNotExist:
            return Response(
                {'error': 'العرض غير موجود'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if bid.status == 'disqualified':
            return Response(
                {'error': 'هذا العرض غير مؤهل مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if bid.status not in ('submitted', 'qualified'):
            return Response(
                {'error': 'لا يمكن استبعاد عرض في هذه الحالة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get('reason', '')
        bid.status = 'disqualified'
        bid.notes = reason if reason else bid.notes
        bid.save()

        return Response({
            'message': 'تم استبعاد العرض بنجاح',
            'bid': TenderBidListSerializer(bid).data,
        })


# =============================================
# Tender Evaluation Views
# =============================================

class TenderEvaluationListView(generics.ListCreateAPIView):
    """GET: List tender evaluations. POST: Create tender evaluation (admin only)."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['criterion']
    ordering_fields = ['criterion', 'weight', 'score', 'weighted_score', 'created_at']
    ordering = ['criterion']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TenderEvaluationCreateSerializer
        return TenderEvaluationListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = TenderEvaluation.objects.select_related('bid__supplier', 'bid__tender', 'evaluator')
        # Filter by bid
        bid = self.request.query_params.get('bid')
        if bid:
            queryset = queryset.filter(bid_id=bid)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evaluation = serializer.save(evaluator=request.user)
        return Response({
            'message': 'تم إنشاء التقييم بنجاح',
            'evaluation': TenderEvaluationListSerializer(evaluation).data,
        }, status=status.HTTP_201_CREATED)


class TenderEvaluationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: Tender evaluation details. PATCH: Update. DELETE: Delete (admin only)."""

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return TenderEvaluationUpdateSerializer
        return TenderEvaluationListSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return TenderEvaluation.objects.select_related('bid__supplier', 'bid__tender', 'evaluator')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        evaluation = serializer.save()
        return Response({
            'message': 'تم تحديث التقييم بنجاح',
            'evaluation': TenderEvaluationListSerializer(evaluation).data,
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'message': 'تم حذف التقييم بنجاح'})


# =============================================
# Tender Award Views
# =============================================

class TenderAwardListView(generics.ListAPIView):
    """GET: List tender awards."""

    serializer_class = TenderAwardListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['contract_value', 'status', 'created_at']
    ordering = ['-created_at']

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TenderAward.objects.select_related(
            'tender', 'bid__supplier', 'approved_by'
        )
        # تصفية حسب المناقصة
        tender = self.request.query_params.get('tender')
        if tender:
            queryset = queryset.filter(tender_id=tender)
        # تصفية حسب الحالة
        award_status = self.request.query_params.get('status')
        if award_status:
            queryset = queryset.filter(status=award_status)
        return queryset


class TenderAwardDetailView(generics.RetrieveAPIView):
    """GET: Tender award details."""

    serializer_class = TenderAwardListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TenderAward.objects.select_related(
            'tender', 'bid__supplier', 'approved_by'
        )


class TenderAwardCreateView(views.APIView):
    """POST: Create a tender award (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = TenderAwardCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        award = serializer.save()

        # Update tender status to awarded
        tender = award.tender
        tender.status = 'awarded'
        tender.save()

        # Update bid status to selected
        bid = award.bid
        bid.status = 'selected'
        bid.save()

        return Response({
            'message': 'تم إنشاء الترسية بنجاح',
            'award': TenderAwardListSerializer(award).data,
        }, status=status.HTTP_201_CREATED)


class TenderAwardApproveView(views.APIView):
    """POST: Approve or reject a tender award (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            award = TenderAward.objects.select_related(
                'tender', 'bid__supplier', 'approved_by'
            ).get(pk=pk)
        except TenderAward.DoesNotExist:
            return Response(
                {'error': 'الترسية غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TenderAwardApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']

        if award.status != 'pending':
            return Response(
                {'error': 'يمكن الموافقة أو الرفض فقط على الترسيات المعلقة'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == 'approve':
            award.status = 'approved'
            award.approved_by = request.user
            award.save()

            return Response({
                'message': 'تمت الموافقة على الترسية',
                'award': TenderAwardListSerializer(award).data,
            })
        else:
            award.status = 'rejected'
            award.approved_by = request.user
            award.save()

            # Revert tender and bid statuses
            tender = award.tender
            tender.status = 'evaluation'
            tender.save()

            bid = award.bid
            bid.status = 'submitted'
            bid.save()

            return Response({
                'message': 'تم رفض الترسية',
                'award': TenderAwardListSerializer(award).data,
            })


# =============================================
# Tender Export View
# =============================================

class TenderExportView(views.APIView):
    """GET: Export tenders to Excel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.utils import export_to_excel

        queryset = Tender.objects.select_related(
            'department', 'project', 'created_by'
        ).order_by('-created_at')

        # Filter by status
        tender_status = self.request.query_params.get('status')
        if tender_status:
            queryset = queryset.filter(status=tender_status)

        columns = [
            ('tender_number', 'رقم المناقصة', 15),
            ('title', 'العنوان', 40),
            ('tender_type', 'نوع المناقصة', 15),
            ('status', 'الحالة', 15),
            ('publish_date', 'تاريخ النشر', 15),
            ('closing_date', 'تاريخ الإغلاق', 15),
            ('estimated_value', 'القيمة التقديرية', 18),
            ('department', 'القسم', 20),
            ('project', 'المشروع', 25),
            ('bids_count', 'عدد العروض', 12),
            ('created_by', 'أنشئ بواسطة', 15),
            ('created_at', 'تاريخ الإنشاء', 20),
        ]
        data = []
        for t in queryset:
            data.append({
                'tender_number': t.tender_number,
                'title': t.title,
                'tender_type': t.get_tender_type_display(),
                'status': t.get_status_display(),
                'publish_date': str(t.publish_date) if t.publish_date else '',
                'closing_date': str(t.closing_date) if t.closing_date else '',
                'estimated_value': str(t.estimated_value),
                'department': t.department.name if t.department else '',
                'project': t.project.name if t.project else '',
                'bids_count': t.bids.count(),
                'created_by': t.created_by.username if t.created_by else '',
                'created_at': str(t.created_at.strftime('%Y-%m-%d %H:%M')) if t.created_at else '',
            })
        return export_to_excel(data, columns, 'المناقصات', 'tenders.xlsx')
