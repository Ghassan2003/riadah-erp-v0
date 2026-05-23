"""
Chatbot models for RIADAH ERP System.
Manages conversations and messages between users and the AI assistant.
"""

from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    Model representing a chat conversation session.
    Each conversation belongs to a specific user and optionally to a company.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chatbot_conversations',
        verbose_name='المستخدم',
        db_index=True,
    )
    # Company FK — nullable since no Company model exists yet.
    # When a Company model is introduced, update this field accordingly.
    company = models.ForeignKey(
        'self',  # Placeholder; replace with actual Company model when available
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='الشركة',
        db_index=True,
        editable=False,
    )
    title = models.CharField(
        max_length=255,
        verbose_name='العنوان',
        default='محادثة جديدة',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشطة',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
        db_index=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'محادثة'
        verbose_name_plural = 'المحادثات'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.title} — {self.user.username}'

    @property
    def message_count(self):
        """Return the number of messages in this conversation."""
        return self.messages.count()


class Message(models.Model):
    """
    Model representing a single message within a conversation.
    Messages can be from the user, the assistant, or the system.
    """

    ROLE_CHOICES = (
        ('user', 'المستخدم'),
        ('assistant', 'المساعد'),
        ('system', 'النظام'),
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='المحادثة',
        db_index=True,
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='المرسل',
        db_index=True,
    )
    content = models.TextField(
        verbose_name='المحتوى',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'رسالة'
        verbose_name_plural = 'الرسائل'
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.get_role_display()}] {self.content[:50]}'

    @property
    def content_preview(self):
        """Return the first 50 characters of the message content."""
        return self.content[:50] + ('...' if len(self.content) > 50 else '')
