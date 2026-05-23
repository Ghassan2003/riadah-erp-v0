"""
AI Service module for RIADAH ERP chatbot.
Connects to HuggingFace Inference API using the Llama 3.1 8B Instruct model.
"""

import logging
import requests

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
import os

HUGGINGFACE_API_URL = (
    'https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct'
)
# Read API token from environment variable (never hardcode secrets)
HUGGINGFACE_TOKEN = os.environ.get('HUGGINGFACE_API_TOKEN', '')

# Maximum tokens for the generated response
MAX_NEW_TOKENS = 512

# System prompt for the ERP assistant (in Arabic)
SYSTEM_PROMPT = """أنت المساعد الذكي لنظام ريادة ERP — نظام تخطيط موارد المؤسسات المتكامل.

مهامك:
- الإجابة على أسئلة المستخدمين حول النظام وميزاته.
- تقديم إرشادات حول استخدام وحدات النظام المختلفة (المبيعات، المخزون، المحاسبة، الموارد البشرية، إلخ).
- مساعدة المستخدمين في فهم البيانات والتقارير.
- تقديم اقتراحات وتوصيات لتحسين العمليات.

قواعد:
1. أجب باللغة العربية دائماً.
2. كن مختصراً ومفيداً في إجاباتك.
3. إذا لم تكن متأكداً من إجابة، اطلب المزيد من التفاصيل.
4. لا تذكر أنك نموذج ذكاء اصطناعي — أنت مساعد النظام.
5. استخدم لغة مهنية وودية.
6. لا تُفصح عن معلومات حساسة أو خاصة.
"""


def generate_response(prompt, context=None):
    """
    Generate an AI response using the HuggingFace Inference API.

    Args:
        prompt (str): The user's message / query.
        context (str, optional): Additional context such as user role,
            company info, or conversation history.

    Returns:
        str: The generated response text.

    Raises:
        requests.RequestException: If the API request fails.
        ValueError: If the response cannot be parsed.
    """
    # Build the full prompt with system message and optional context
    full_prompt = _build_full_prompt(prompt, context)

    headers = {
        'Authorization': f'Bearer {HUGGINGFACE_TOKEN}',
        'Content-Type': 'application/json',
    }

    payload = {
        'inputs': full_prompt,
        'parameters': {
            'max_new_tokens': MAX_NEW_TOKENS,
            'temperature': 0.7,
            'top_p': 0.9,
            'do_sample': True,
            'return_full_text': False,
        },
    }

    try:
        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        # Parse the response
        result = response.json()

        if isinstance(result, list) and len(result) > 0:
            generated_text = result[0].get('generated_text', '').strip()
        elif isinstance(result, dict):
            generated_text = result.get('generated_text', '').strip()
        else:
            generated_text = str(result).strip()

        # Clean up the response
        generated_text = _clean_response(generated_text)

        if not generated_text:
            return 'عذراً، لم أتمكن من توليد إجابة مناسبة. يرجى إعادة صياغة سؤالك.'

        return generated_text

    except requests.exceptions.Timeout:
        logger.error('HuggingFace API request timed out.')
        return 'عذراً، استغرقت معالجة طلبك وقتاً طويلاً. يرجى المحاولة مرة أخرى.'

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else 'N/A'
        logger.error('HuggingFace API HTTP error (status=%s): %s', status_code, e)
        return 'عذراً، حدث خطأ في خدمة الذكاء الاصطناعي. يرجى المحاولة لاحقاً.'

    except requests.exceptions.RequestException as e:
        logger.error('HuggingFace API request error: %s', e)
        return 'عذراً، حدث خطأ في الاتصال بخدمة الذكاء الاصطناعي. يرجى المحاولة لاحقاً.'

    except (KeyError, IndexError, ValueError) as e:
        logger.error('Error parsing HuggingFace API response: %s', e)
        return 'عذراً، حدث خطأ في معالجة الرد. يرجى المحاولة لاحقاً.'


def _build_full_prompt(prompt, context=None):
    """
    Construct the full prompt for the Llama 3.1 Instruct model.

    Uses the chat template format:
        <|system|>
        ...
        <|user|>
        ...
        <|assistant| >
    """
    parts = []

    # System message
    parts.append(f'<|system|>\n{SYSTEM_PROMPT}')

    # Optional context (treated as previous assistant knowledge)
    if context and context.strip():
        parts.append(f'<|user|>\nمعلومات إضافية:\n{context}')

    # User prompt
    parts.append(f'<|user|>\n{prompt}')
    parts.append('<|assistant| >')

    return '\n'.join(parts)


def _clean_response(text):
    """
    Clean and normalize the generated response text.
    Removes any artifact tags and extra whitespace.
    """
    # Remove potential leftover tags from the model output
    import re
    text = re.sub(r'<\|[^>]+\|>', '', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Remove excessive newlines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
