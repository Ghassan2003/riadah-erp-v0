"""
Views لنظام تعليمات الفيديو - Video Instructions System
يتضمن: CRUD للفيديوهات والتصنيفات، تتبع التقدم، التعليقات، الإحصائيات
"""

from rest_framework import (
    views, viewsets, generics, status, permissions,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, Avg
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import (
    VideoCategory,
    VideoInstruction,
    VideoProgress,
    VideoComment,
)
from .serializers import (
    VideoCategorySerializer,
    VideoCategoryListSerializer,
    VideoInstructionListSerializer,
    VideoInstructionDetailSerializer,
    VideoInstructionCreateSerializer,
    VideoProgressSerializer,
    VideoCommentSerializer,
)


# ═══════════════════════════════════════════════════
# Permissions
# ═══════════════════════════════════════════════════

class IsAdminOrReadOnly(permissions.BasePermission):
    """المشرفون يمكنهم الكتابة، الباقي قراءة فقط"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and (request.user.is_admin or request.user.role == 'admin')


# ═══════════════════════════════════════════════════
# Video Categories Views
# ═══════════════════════════════════════════════════

class VideoCategoryViewSet(viewsets.ModelViewSet):
    """إدارة تصنيفات الفيديوهات"""
    queryset = VideoCategory.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return VideoCategoryListSerializer
        return VideoCategorySerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def all(self, request):
        """عرض جميع التصنيفات بما فيها غير المفعّلة (للمشرفين)"""
        if request.user.role != 'admin':
            return Response(
                {'detail': 'غير مصرح بهذا الإجراء'},
                status=status.HTTP_403_FORBIDDEN
            )
        categories = VideoCategory.objects.all()
        serializer = VideoCategorySerializer(categories, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════
# Video Instructions Views
# ═══════════════════════════════════════════════════

class VideoInstructionViewSet(viewsets.ModelViewSet):
    """إدارة الفيديوهات التعليمية - CRUD كامل"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """تصفية الفيديوهات حسب التصنيف والبحث"""
        queryset = VideoInstruction.objects.filter(is_active=True)

        # فلترة حسب التصنيف
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # فلترة حسب المستوى
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)

        # فلترة المميزة فقط
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)

        # بحث في العنوان والوصف
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title_ar__icontains=search) |
                Q(title_en__icontains=search) |
                Q(description_ar__icontains=search) |
                Q(description_en__icontains=search) |
                Q(tags__icontains=search)
            )

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return VideoInstructionListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return VideoInstructionCreateSerializer
        return VideoInstructionDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        """عرض تفاصيل الفيديو مع زيادة عداد المشاهدات"""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """إعجاب بالفيديو"""
        video = self.get_object()
        video.likes_count += 1
        video.save(update_fields=['likes_count'])
        return Response({'likes_count': video.likes_count})

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """عرض الفيديوهات المميزة"""
        queryset = VideoInstruction.objects.filter(
            is_active=True, is_featured=True
        ).order_by('-created_at')[:10]
        serializer = VideoInstructionListSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """إحصائيات الفيديوهات"""
        total_videos = VideoInstruction.objects.filter(is_active=True).count()
        total_categories = VideoCategory.objects.filter(is_active=True).count()
        total_views = VideoInstruction.objects.aggregate(
            total=Sum('views_count')
        )['total'] or 0
        total_likes = VideoInstruction.objects.aggregate(
            total=Sum('likes_count')
        )['total'] or 0

        # إحصائيات المستخدم الحالي
        user_stats = {}
        if request.user.is_authenticated:
            user_progress = VideoProgress.objects.filter(user=request.user)
            user_stats = {
                'watched_count': user_progress.count(),
                'completed_count': user_progress.filter(is_completed=True).count(),
                'total_watch_time': user_progress.aggregate(
                    total=Sum('watched_seconds')
                )['total'] or 0,
            }

        # إحصائيات حسب التصنيف
        category_stats = list(
            VideoInstruction.objects.filter(is_active=True)
            .values('category')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response({
            'total_videos': total_videos,
            'total_categories': total_categories,
            'total_views': total_views,
            'total_likes': total_likes,
            'user_stats': user_stats,
            'category_stats': category_stats,
        })


# ═══════════════════════════════════════════════════
# Video Progress Views
# ═══════════════════════════════════════════════════

class VideoProgressView(views.APIView):
    """تحديث واستعلام تقدم مشاهدة الفيديو"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """الحصول على تقدم المستخدم في جميع الفيديوهات"""
        progress = VideoProgress.objects.filter(
            user=request.user
        ).select_related('video')

        serializer = VideoProgressSerializer(progress, many=True)
        return Response(serializer.data)

    def post(self, request):
        """تحديث أو إنشاء تقدم المشاهدة"""
        video_id = request.data.get('video')
        watched_seconds = request.data.get('watched_seconds', 0)
        is_completed = request.data.get('is_completed', False)

        if not video_id:
            return Response(
                {'detail': 'معرّف الفيديو مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            video = VideoInstruction.objects.get(id=video_id, is_active=True)
        except VideoInstruction.DoesNotExist:
            return Response(
                {'detail': 'الفيديو غير موجود'},
                status=status.HTTP_404_NOT_FOUND
            )

        # إنشاء أو تحديث التقدم
        progress, created = VideoProgress.objects.update_or_create(
            user=request.user,
            video=video,
            defaults={
                'watched_seconds': watched_seconds,
                'is_completed': is_completed,
            }
        )

        # تحديث تلقائي إذا شاهد أكثر من 90%
        if not is_completed and video.duration_seconds > 0:
            if watched_seconds >= video.duration_seconds * 0.9:
                progress.is_completed = True
                progress.save(update_fields=['is_completed'])

        serializer = VideoProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class VideoProgressDetailView(generics.RetrieveAPIView):
    """الحصول على تقدم مشاهدة فيديو محدد"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VideoProgressSerializer

    def get_object(self):
        progress = VideoProgress.objects.filter(
            user=self.request.user,
            video_id=self.kwargs['video_id']
        ).first()
        if not progress:
            return VideoProgress(
                user=self.request.user,
                video_id=self.kwargs['video_id'],
                watched_seconds=0,
                is_completed=False,
            )
        return progress


# ═══════════════════════════════════════════════════
# Video Comments Views
# ═══════════════════════════════════════════════════

class VideoCommentListCreateView(generics.ListCreateAPIView):
    """عرض وإنشاء التعليقات على فيديو"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VideoCommentSerializer

    def get_queryset(self):
        return VideoComment.objects.filter(
            video_id=self.kwargs['video_id']
        ).select_related('user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, video_id=self.kwargs['video_id'])


class VideoCommentDetailView(generics.RetrieveAPIView):
    """عرض تفاصيل تعليق محدد"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VideoCommentSerializer

    def get_queryset(self):
        return VideoComment.objects.select_related('user')


class VideoCommentUpdateView(generics.UpdateAPIView):
    """تحديث تعليق (المالك أو المشرف)"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VideoCommentSerializer

    def get_queryset(self):
        return VideoComment.objects.select_related('user')

    def get_object(self):
        comment = VideoComment.objects.get(pk=self.kwargs['pk'])
        if comment.user != self.request.user and self.request.user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('غير مصرح بتعديل هذا التعليق')
        return comment


class VideoCommentDeleteView(generics.DestroyAPIView):
    """حذف تعليق (المالك أو المشرف)"""
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        comment = VideoComment.objects.get(pk=self.kwargs['pk'])
        if comment.user != self.request.user and self.request.user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('غير مصرح بحذف هذا التعليق')
        return comment


# ═══════════════════════════════════════════════════
# Video Search View
# ═══════════════════════════════════════════════════

class VideoSearchView(views.APIView):
    """بحث شامل في الفيديوهات"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response({'results': [], 'count': 0})

        videos = VideoInstruction.objects.filter(
            is_active=True
        ).filter(
            Q(title_ar__icontains=query) |
            Q(title_en__icontains=query) |
            Q(description_ar__icontains=query) |
            Q(description_en__icontains=query) |
            Q(tags__icontains=query)
        ).order_by('-is_featured', 'order')[:20]

        serializer = VideoInstructionListSerializer(
            videos, many=True, context={'request': request}
        )
        return Response({
            'results': serializer.data,
            'count': len(serializer.data),
            'query': query,
        })
