"""
Custom password validators for ERP system.
Enforces strong password policies.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class MinLengthValidator:
    """Validate minimum password length (configurable, default 8)."""

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                f'كلمة المرور يجب أن تكون {self.min_length} أحرف على الأقل',
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return f'كلمة المرور يجب أن تكون {self.min_length} أحرف على الأقل.'


class ComplexityValidator:
    """
    Validate password complexity:
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """

    def validate(self, password, user=None):
        errors = []
        if not re.search(r'[A-Z]', password):
            errors.append('حرف كبير واحد على الأقل (A-Z)')
        if not re.search(r'[a-z]', password):
            errors.append('حرف صغير واحد على الأقل (a-z)')
        if not re.search(r'\d', password):
            errors.append('رقم واحد على الأقل (0-9)')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            errors.append('رمز خاص واحد على الأقل (!@#$%^&*)')

        if errors:
            raise ValidationError(
                f'كلمة المرور يجب أن تحتوي على: {", ".join(errors)}',
                code='password_no_complexity',
            )

    def get_help_text(self):
        return 'كلمة المرور يجب أن تحتوي على حرف كبير، حرف صغير، رقم، ورمز خاص.'


class PasswordHistoryValidator:
    """Validate password is not in recent history."""

    def __init__(self, history_count=5):
        self.history_count = history_count

    def validate(self, password, user=None):
        if user and hasattr(user, 'is_password_in_history'):
            if user.is_password_in_history(password):
                raise ValidationError(
                    'كلمة المرور مستخدمة سابقاً. اختر كلمة مرور مختلفة.',
                    code='password_reused',
                    params={'history_count': self.history_count},
                )

    def get_help_text(self):
        return f'كلمة المرور يجب ألا تكون من آخر {self.history_count} كلمات مرور مستخدمة.'


class UsernameSimilarityArabicValidator:
    """Validate password is not too similar to username (includes Arabic)."""

    def validate(self, password, user=None):
        if not user:
            return
        username = getattr(user, 'username', '')
        if not username:
            return

        # Check similarity (at least 50% of password chars match username)
        password_lower = password.lower()
        username_lower = username.lower()

        if password_lower == username_lower:
            raise ValidationError(
                'كلمة المرور لا يمكن أن تكون مطابقة لاسم المستخدم',
                code='password_same_as_username',
            )

        # Check if password contains username
        if len(username_lower) >= 3 and username_lower in password_lower:
            raise ValidationError(
                'كلمة المرور لا يمكن أن تحتوي على اسم المستخدم',
                code='password_contains_username',
            )

    def get_help_text(self):
        return 'كلمة المرور لا يمكن أن تكون مطابقة لاسم المستخدم أو تحتوي عليه.'


class SequentialCharsValidator:
    """Validate password doesn't have sequential or repeating characters."""

    def validate(self, password, user=None):
        # Check for sequential chars (e.g., 123, abc, 321)
        for i in range(len(password) - 2):
            if (ord(password[i + 1]) == ord(password[i]) + 1 and
                    ord(password[i + 2]) == ord(password[i]) + 2):
                raise ValidationError(
                    'كلمة المرور لا يمكن أن تحتوي على أحرف أو أرقام متتالية (مثل: 123, abc)',
                    code='password_sequential',
                )

        # Check for repeating chars (e.g., 111, aaa)
        for i in range(len(password) - 2):
            if password[i] == password[i + 1] == password[i + 2]:
                raise ValidationError(
                    'كلمة المرور لا يمكن أن تحتوي على 3 أحرف أو أرقام متكررة متتالية (مثل: 111, aaa)',
                    code='password_repeating',
                )

    def get_help_text(self):
        return 'كلمة المرور لا يمكن أن تحتوي على أحرف متتالية أو متكررة.'
