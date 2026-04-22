"""
Admin configuration for the Videos module.
"""

from django.contrib import admin
from .models import VideoCategory, VideoInstruction, VideoProgress, VideoComment


@admin.register(VideoCategory)
class VideoCategoryAdmin(admin.ModelAdmin):
    """Admin interface for VideoCategory model."""

    list_display = (
        'name_ar', 'name_en', 'icon', 'color',
        'order', 'is_active', 'video_count', 'created_at',
    )
    list_filter = ('is_active',)
    search_fields = ('name_ar', 'name_en', 'description_ar', 'description_en')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'id')

    fieldsets = (
        ('معلومات التصنيف', {
            'fields': ('name_ar', 'name_en', 'description_ar', 'description_en')
        }),
        ('المظهر', {
            'fields': ('icon', 'color', 'order', 'is_active')
        }),
    )


@admin.register(VideoInstruction)
class VideoInstructionAdmin(admin.ModelAdmin):
    """Admin interface for VideoInstruction model."""

    list_display = (
        'title_ar', 'category', 'difficulty_level',
        'duration_display', 'views_count', 'likes_count',
        'is_active', 'is_featured', 'created_at',
    )
    list_filter = ('category', 'difficulty_level', 'is_active', 'is_featured')
    search_fields = ('title_ar', 'title_en', 'description_ar', 'tags')
    date_hierarchy = 'created_at'
    list_editable = ('is_active', 'is_featured', 'order')
    ordering = ('order', '-created_at')

    fieldsets = (
        ('معلومات الفيديو', {
            'fields': (
                'title_ar', 'title_en', 'description_ar', 'description_en',
                'video_file', 'video_url', 'duration_seconds', 'thumbnail',
            )
        }),
        ('التصنيف', {
            'fields': ('category', 'category_model', 'tags', 'difficulty_level')
        }),
        ('التنظيم', {
            'fields': ('order', 'is_active', 'is_featured')
        }),
        ('الإحصائيات', {
            'fields': ('views_count', 'likes_count')
        }),
        ('معلومات الإنشاء', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    readonly_fields = ('views_count', 'likes_count', 'created_at', 'updated_at')


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    """Admin interface for VideoProgress model."""

    list_display = (
        'user', 'video', 'progress_percent',
        'watched_seconds', 'is_completed', 'last_watched_at',
    )
    list_filter = ('is_completed',)
    search_fields = ('user__username', 'video__title_ar')
    date_hierarchy = 'last_watched_at'
    raw_id_fields = ('user', 'video')

    fieldsets = (
        ('تقدم المشاهدة', {
            'fields': ('user', 'video', 'watched_seconds', 'is_completed', 'progress_percent')
        }),
        ('تاريخ المشاهدة', {
            'fields': ('last_watched_at', 'created_at')
        }),
    )

    readonly_fields = ('progress_percent', 'last_watched_at', 'created_at')


@admin.register(VideoComment)
class VideoCommentAdmin(admin.ModelAdmin):
    """Admin interface for VideoComment model."""

    list_display = (
        'video', 'user', 'comment_short', 'is_pinned', 'created_at',
    )
    list_filter = ('is_pinned',)
    search_fields = ('user__username', 'comment', 'video__title_ar')
    date_hierarchy = 'created_at'
    list_editable = ('is_pinned',)
    raw_id_fields = ('video', 'user')

    fieldsets = (
        ('التعليق', {
            'fields': ('video', 'user', 'comment', 'timestamp_seconds', 'is_pinned')
        }),
        ('تاريخ الإنشاء', {
            'fields': ('created_at',)
        }),
    )

    def comment_short(self, obj):
        return obj.comment[:60] + '...' if len(obj.comment) > 60 else obj.comment
    comment_short.short_description = 'التعليق'
