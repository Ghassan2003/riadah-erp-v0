"""
Serializers للنظام التعليمي - تحويل النماذج إلى JSON والعكس.
"""

from rest_framework import serializers
from .models import (
    VideoCategory,
    VideoInstruction,
    VideoProgress,
    VideoComment,
)


class VideoCategorySerializer(serializers.ModelSerializer):
    """Serializer لتصنيفات الفيديو"""
    video_count = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='name_ar', read_only=True)

    class Meta:
        model = VideoCategory
        fields = [
            'id', 'name_ar', 'name_en', 'description_ar', 'description_en',
            'icon', 'color', 'order', 'is_active', 'created_at',
            'name', 'video_count',
        ]
        read_only_fields = ['created_at']


class VideoCategoryListSerializer(serializers.ModelSerializer):
    """Serializer مختصر لعرض التصنيفات في القوائم"""
    video_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VideoCategory
        fields = ['id', 'name_ar', 'name_en', 'icon', 'color', 'video_count']


class VideoInstructionListSerializer(serializers.ModelSerializer):
    """Serializer مختصر لعرض الفيديوهات في القوائم"""
    category_display = serializers.CharField(
        source='get_category_display', read_only=True
    )
    difficulty_display = serializers.CharField(
        source='get_difficulty_level_display', read_only=True
    )
    duration_display = serializers.CharField(read_only=True)
    has_progress = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = VideoInstruction
        fields = [
            'id', 'title_ar', 'title_en', 'description_ar',
            'video_url', 'duration_seconds', 'duration_display',
            'thumbnail', 'category', 'category_display',
            'difficulty_level', 'difficulty_display',
            'is_featured', 'views_count', 'likes_count',
            'order', 'created_at',
            'has_progress', 'progress_percent',
        ]

    def get_has_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return VideoProgress.objects.filter(
                user=request.user, video=obj
            ).exists()
        return False

    def get_progress_percent(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = VideoProgress.objects.filter(
                user=request.user, video=obj
            ).first()
            if progress:
                return progress.progress_percent
        return 0


class VideoInstructionDetailSerializer(serializers.ModelSerializer):
    """Serializer مفصّل لعرض تفاصيل الفيديو"""
    category_display = serializers.CharField(
        source='get_category_display', read_only=True
    )
    difficulty_display = serializers.CharField(
        source='get_difficulty_level_display', read_only=True
    )
    duration_display = serializers.CharField(read_only=True)
    video_source = serializers.CharField(read_only=True)
    is_external = serializers.BooleanField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    related_videos = serializers.SerializerMethodField()

    class Meta:
        model = VideoInstruction
        fields = [
            'id', 'title_ar', 'title_en', 'description_ar', 'description_en',
            'video_file', 'video_url', 'duration_seconds', 'duration_display',
            'thumbnail', 'category', 'category_display', 'category_model',
            'tags', 'difficulty_level', 'difficulty_display',
            'is_featured', 'views_count', 'likes_count',
            'order', 'is_active',
            'video_source', 'is_external',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
            'user_progress', 'related_videos',
        ]
        read_only_fields = ['created_at', 'updated_at', 'views_count', 'likes_count']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.first_name or obj.created_by.username
        return None

    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = VideoProgress.objects.filter(
                user=request.user, video=obj
            ).first()
            if progress:
                return {
                    'watched_seconds': progress.watched_seconds,
                    'is_completed': progress.is_completed,
                    'progress_percent': progress.progress_percent,
                    'last_watched_at': progress.last_watched_at,
                }
        return None

    def get_related_videos(self, obj):
        """الحصول على فيديوهات ذات صلة من نفس التصنيف"""
        related = VideoInstruction.objects.filter(
            category=obj.category,
            is_active=True,
        ).exclude(id=obj.id).order_by('order', '-created_at')[:5]
        return VideoInstructionListSerializer(
            related, many=True, context=self.context
        ).data


class VideoInstructionCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء/تحديث فيديو تعليمي"""

    class Meta:
        model = VideoInstruction
        fields = [
            'title_ar', 'title_en', 'description_ar', 'description_en',
            'video_file', 'video_url', 'duration_seconds', 'thumbnail',
            'category', 'category_model', 'tags',
            'order', 'is_active', 'is_featured', 'difficulty_level',
        ]

    def validate(self, attrs):
        """التأكد من وجود إما ملف فيديو أو رابط"""
        video_file = attrs.get('video_file')
        video_url = attrs.get('video_url')
        if not video_file and not video_url:
            raise serializers.ValidationError(
                {'detail': 'يجب توفير ملف فيديو أو رابط فيديو خارجي'}
            )
        return attrs


class VideoProgressSerializer(serializers.ModelSerializer):
    """Serializer لتحديث تقدم المشاهدة"""

    class Meta:
        model = VideoProgress
        fields = ['id', 'video', 'watched_seconds', 'is_completed', 'progress_percent']
        read_only_fields = ['id', 'progress_percent']

    def validate(self, attrs):
        video = attrs.get('video')
        watched = attrs.get('watched_seconds', 0)
        if video and watched > video.duration_seconds:
            attrs['watched_seconds'] = video.duration_seconds
        if video and watched >= video.duration_seconds * 0.9:
            attrs['is_completed'] = True
        return attrs


class VideoCommentSerializer(serializers.ModelSerializer):
    """Serializer للتعليقات على الفيديوهات"""
    user_name = serializers.CharField(
        source='user.first_name', read_only=True
    )
    user_username = serializers.CharField(
        source='user.username', read_only=True
    )
    user_role = serializers.CharField(
        source='user.role', read_only=True
    )

    class Meta:
        model = VideoComment
        fields = [
            'id', 'video', 'user', 'user_name', 'user_username',
            'user_role', 'comment', 'timestamp_seconds',
            'is_pinned', 'created_at',
        ]
        read_only_fields = ['user', 'created_at', 'is_pinned']
