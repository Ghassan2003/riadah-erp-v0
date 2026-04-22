"""
نظام تعليمات الفيديو - Video Instructions System
يتيح رفع وإدارة وتنظيم مقاطع الفيديو التعليمية لنظام ERP
يدعم التصنيفات والترتيب والمشاهدة وتتبع التقدم
"""

from django.db import models
from django.conf import settings


class VideoCategory(models.Model):
    """تصنيفات الفيديوهات التعليمية"""

    name_ar = models.CharField(
        max_length=100,
        verbose_name='الاسم بالعربية',
    )
    name_en = models.CharField(
        max_length=100,
        verbose_name='الاسم بالإنجليزية',
    )
    description_ar = models.TextField(
        blank=True,
        verbose_name='الوصف بالعربية',
    )
    description_en = models.TextField(
        blank=True,
        verbose_name='الوصف بالإنجليزية',
    )
    icon = models.CharField(
        max_length=50,
        default='Video',
        verbose_name='أيقونة اللوسيد',
        help_text='اسم أيقونة من lucide-react مثل: Video, BookOpen, Settings',
    )
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name='اللون',
        help_text='كود اللون HEX مثل: #3B82F6',
    )
    order = models.IntegerField(
        default=0,
        verbose_name='الترتيب',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='مفعّل',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'تصنيف فيديو'
        verbose_name_plural = 'تصنيفات الفيديوهات'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name_ar

    @property
    def name(self):
        return self.name_ar

    @property
    def video_count(self):
        return self.videos.filter(is_active=True).count()


class VideoInstruction(models.Model):
    """مقاطع الفيديو التعليمية"""

    CATEGORY_CHOICES = (
        ('getting_started', 'البدء مع النظام'),
        ('inventory', 'إدارة المخزون'),
        ('sales', 'المبيعات'),
        ('purchases', 'المشتريات'),
        ('accounting', 'المحاسبة'),
        ('hr', 'الموارد البشرية'),
        ('documents', 'المستندات'),
        ('projects', 'المشاريع'),
        ('reports', 'التقارير'),
        ('settings', 'الإعدادات'),
        ('advanced', 'متقدم'),
        ('troubleshooting', 'حل المشكلات'),
    )

    title_ar = models.CharField(
        max_length=200,
        verbose_name='العنوان بالعربية',
    )
    title_en = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='العنوان بالإنجليزية',
    )
    description_ar = models.TextField(
        blank=True,
        verbose_name='الوصف بالعربية',
    )
    description_en = models.TextField(
        blank=True,
        verbose_name='الوصف بالإنجليزية',
    )

    # Video file or URL
    video_file = models.FileField(
        upload_to='videos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='ملف الفيديو',
        help_text='ارفع ملف فيديو بتنسيق MP4, WebM, أو OGG',
    )
    video_url = models.URLField(
        blank=True,
        verbose_name='رابط الفيديو الخارجي',
        help_text='رابط فيديو من YouTube, Vimeo, أو أي مصدر خارجي',
    )
    duration_seconds = models.IntegerField(
        default=0,
        verbose_name='المدة بالثواني',
        help_text='مدة الفيديو بالثواني',
    )

    # Thumbnail
    thumbnail = models.ImageField(
        upload_to='videos/thumbnails/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='صورة مصغرة',
        help_text='صورة مصغرة للفيديو (يوصى بأبعاد 16:9)',
    )

    # Categorization
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='getting_started',
        verbose_name='التصنيف',
        db_index=True,
    )
    category_model = models.ForeignKey(
        VideoCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='videos',
        verbose_name='التصنيف المخصص',
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name='الكلمات المفتاحية',
        help_text='قائمة بالكلمات المفتاحية للبحث',
    )

    # Organization
    order = models.IntegerField(
        default=0,
        verbose_name='الترتيب',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='مفعّل',
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name='مميز',
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=(
            ('beginner', 'مبتدئ'),
            ('intermediate', 'متوسط'),
            ('advanced', 'متقدم'),
        ),
        default='beginner',
        verbose_name='مستوى الصعوبة',
    )

    # Tracking
    views_count = models.IntegerField(
        default=0,
        verbose_name='عدد المشاهدات',
    )
    likes_count = models.IntegerField(
        default=0,
        verbose_name='عدد الإعجابات',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_videos',
        verbose_name='رفع بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'فيديو تعليمي'
        verbose_name_plural = 'الفيديوهات التعليمية'
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def __str__(self):
        return self.title_ar

    @property
    def title(self):
        return self.title_ar

    @property
    def description(self):
        return self.description_ar

    @property
    def duration_display(self):
        """تنسيق المدة كـ MM:SS أو HH:MM:SS"""
        total = self.duration_seconds
        if total == 0:
            return '--:--'
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        if hours > 0:
            return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
        return f'{minutes:02d}:{seconds:02d}'

    @property
    def video_source(self):
        """مصدر الفيديو: ملف محلي أو رابط خارجي"""
        if self.video_file:
            return self.video_file.url
        if self.video_url:
            return self.video_url
        return None

    @property
    def is_external(self):
        """هل الفيديو من مصدر خارجي؟"""
        if not self.video_url:
            return False
        external_domains = ['youtube.com', 'youtu.be', 'vimeo.com', 'vimeo']
        return any(domain in self.video_url for domain in external_domains)


class VideoProgress(models.Model):
    """تتبع تقدم المشاهدة لكل مستخدم"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='video_progress',
        verbose_name='المستخدم',
    )
    video = models.ForeignKey(
        VideoInstruction,
        on_delete=models.CASCADE,
        related_name='user_progress',
        verbose_name='الفيديو',
    )
    watched_seconds = models.IntegerField(
        default=0,
        verbose_name='الثواني المشاهدة',
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='مكتمل',
    )
    last_watched_at = models.DateTimeField(
        auto_now=True,
        verbose_name='آخر مشاهدة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'تقدم مشاهدة'
        verbose_name_plural = 'تقدم المشاهدة'
        unique_together = ('user', 'video')
        ordering = ['-last_watched_at']

    def __str__(self):
        status = 'مكتمل' if self.is_completed else 'قيد المشاهدة'
        return f'{self.user.username} - {self.video.title_ar} ({status})'

    @property
    def progress_percent(self):
        """نسبة الإنجاز"""
        if not self.video.duration_seconds:
            return 0
        return min(100, int((self.watched_seconds / self.video.duration_seconds) * 100))


class VideoComment(models.Model):
    """تعليقات المستخدمين على الفيديوهات"""

    video = models.ForeignKey(
        VideoInstruction,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='الفيديو',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='video_comments',
        verbose_name='المستخدم',
    )
    comment = models.TextField(
        verbose_name='التعليق',
    )
    timestamp_seconds = models.IntegerField(
        default=0,
        verbose_name='التوقيت بالثواني',
        help_text='التوقيت في الفيديو الذي يشير إليه التعليق',
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name='مثبّت',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'تعليق فيديو'
        verbose_name_plural = 'تعليقات الفيديوهات'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.comment[:50]}'
