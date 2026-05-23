"""
Central RAG (Retrieval-Augmented Generation) chat service for RIADAH ERP.
Orchestrates message processing, intent classification, and response generation.
Updated to support the full 23-app module structure.
"""

import logging

from .models import Conversation, Message
from .intent_classifier import intent_classifier
from .smart_query_engine import SmartQueryEngine
from .ai_service import generate_response

logger = logging.getLogger(__name__)

# Intents that should be routed to the smart query engine for data lookups
DATA_QUERY_INTENTS = {
    'sales_query',
    'hr_query',
    'financial_query',
    'purchases_query',
    'crm_query',
    'projects_query',
    'pos_query',
    'payroll_query',
}

# Intents that should be handled directly without AI
DIRECT_RESPONSE_INTENTS = {
    'greeting',
    'farewell',
}


def process_chat_message(user, message, conversation_id=None):
    """
    Process a user's chat message through the full pipeline.

    Pipeline:
    1. Get or create a conversation for the user.
    2. Save the user's message.
    3. Classify the intent of the message.
    4. Route to the appropriate handler:
       - Direct intents (greeting, farewell) → canned responses.
       - Data query intents → SmartQueryEngine for SQL-based lookups.
       - General questions → AI service (HuggingFace LLM).
    5. Save the assistant's response.
    6. Return a result dict.

    Args:
        user: The authenticated User instance.
        message: The user's message text (str).
        conversation_id: Optional conversation ID to continue an existing conversation.

    Returns:
        dict: {
            'response': str,
            'conversation_id': int,
            'message_id': int,
        }
    """
    # ── Step 1: Get or create conversation ────────────────────────────
    conversation = _get_or_create_conversation(user, conversation_id, message)

    # ── Step 2: Save user message ─────────────────────────────────────
    user_message = Message.objects.create(
        conversation=conversation,
        role='user',
        content=message,
    )

    # ── Step 3: Classify intent ───────────────────────────────────────
    intent, confidence = intent_classifier.predict(message)
    logger.info(
        'Intent classified for user %s: "%s" (confidence: %.2f)',
        user.username,
        intent,
        confidence,
    )

    # ── Step 4: Route to appropriate handler ───────────────────────────
    if intent in DIRECT_RESPONSE_INTENTS:
        response_text = _get_direct_response(intent, user)

    elif intent in DATA_QUERY_INTENTS:
        query_engine = SmartQueryEngine()
        response_text = query_engine.process_query(
            user=user,
            query_text=message,
            intent=intent,
        )

    else:
        # General question → AI service
        context = _build_context(user, conversation)
        response_text = generate_response(
            prompt=message,
            context=context,
        )

    # ── Step 5: Save assistant response ───────────────────────────────
    assistant_message = Message.objects.create(
        conversation=conversation,
        role='assistant',
        content=response_text,
    )

    # ── Step 6: Return result ─────────────────────────────────────────
    return {
        'response': response_text,
        'conversation_id': conversation.id,
        'message_id': assistant_message.id,
    }


def _get_or_create_conversation(user, conversation_id, first_message):
    """
    Retrieve an existing conversation or create a new one.
    """
    if conversation_id:
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                user=user,
                is_active=True,
            )
            return conversation
        except Conversation.DoesNotExist:
            logger.warning(
                'Conversation %s not found or inactive for user %s. Creating new one.',
                conversation_id,
                user.username,
            )

    # Generate a title from the first message (first 50 chars)
    title = first_message[:50] if first_message else 'محادثة جديدة'
    if len(first_message) > 50:
        title += '...'

    conversation = Conversation.objects.create(
        user=user,
        title=title,
    )
    return conversation


def _get_direct_response(intent, user):
    """Return a canned Arabic response for direct intents."""

    responses = {
        'greeting': (
            f'مرحباً {user.first_name or user.username}! 👋 أنا المساعد الذكي لنظام ريادة ERP. '
            'يمكنني مساعدتك في الاستعلامات عن:\n\n'
            '📊 **المبيعات** — مبيعات اليوم، الشهر، أفضل المنتجات\n'
            '👥 **الموارد البشرية** — الموظفين، الحضور، الإجازات\n'
            '💰 **المحاسبة** — الأرباح، المصروفات، الميزانية\n'
            '🛒 **المشتريات** — أوامر الشراء، الموردين\n'
            '🤝 **CRM** — العملاء، الفرص، التذاكر\n'
            '📁 **المشاريع** — الحالة، المخاطر، الميزانيات\n'
            '🏪 **نقاط البيع** — مبيعات اليوم، المنتجات الأكثر طلباً\n'
            '💳 **الرواتب** — كشوف المرتبات\n\n'
            'أو يمكنك سؤالي أي سؤال عام عن النظام. كيف يمكنني مساعدتك؟'
        ),
        'farewell': (
            f'مع السلامة {user.first_name or user.username}! 😊 أتمنى أن أكون قد ساعدتك. '
            'لا تتردد في العودة عند الحاجة. يوم سعيد!'
        ),
    }
    return responses.get(intent, 'شكراً لتواصلك معنا.')


def _build_context(user, conversation):
    """
    Build a context string for the AI service containing
    user info and recent conversation history.
    """
    context_parts = []

    # User role info
    role_display = getattr(user, 'role_display', user.role or 'مستخدم')
    context_parts.append(f'دور المستخدم: {role_display}')
    context_parts.append(f'اسم المستخدم: {user.username}')

    # ERP modules available
    context_parts.append(
        'وحدات النظام المتاحة: المبيعات، المشتريات، المحاسبة، الموارد البشرية، '
        'إدارة العلاقات (CRM)، المشاريع، نقاط البيع (POS)، الفوترة، المدفوعات، '
        'الرواتب، الوثائق، المناقصات، الاستيراد والتصدير، صيانة المعدات، '
        'التحليلات الذكية، لوحة المؤسس، الإشعارات، إدارة المستخدمين، المراجعة.'
    )

    # Recent conversation history (last 6 messages for context window)
    recent_messages = conversation.messages.order_by('-created_at')[:6]
    if recent_messages.exists():
        context_parts.append('\n--- سابقة المحادثة ---')
        for msg in reversed(recent_messages):
            role = msg.get_role_display()
            context_parts.append(f'{role}: {msg.content[:200]}')
        context_parts.append('--- نهاية السابقة ---')

    return '\n'.join(context_parts)
