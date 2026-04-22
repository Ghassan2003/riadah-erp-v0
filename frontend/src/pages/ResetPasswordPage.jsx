/**
 * Reset Password page - Step 2: Enter verification code + new password.
 * Verifies the 6-digit OTP and sets the new password.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { forgotPasswordAPI } from '../api';
import { Lock, Eye, EyeOff, Loader2, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';

export default function ResetPasswordPage() {
  const { t, locale, isRTL } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resetDone, setResetDone] = useState(false);

  // Get email from navigation state
  useEffect(() => {
    const stateEmail = location.state?.email;
    if (stateEmail) {
      setEmail(stateEmail);
    } else {
      // No email provided, redirect to forgot password
      navigate('/forgot-password');
    }
  }, [location.state, navigate]);

  const handleCodeInput = (index, value) => {
    if (value.length > 1) value = value.slice(-1);
    if (!/^\d*$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    if (value && index < 5) {
      document.getElementById(`reset-code-${index + 1}`)?.focus();
    }
  };

  const handleCodeKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      document.getElementById(`reset-code-${index - 1}`)?.focus();
    }
  };

  const handlePasteCode = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newCode = [...code];
    for (let i = 0; i < pasted.length; i++) {
      newCode[i] = pasted[i];
    }
    setCode(newCode);
    if (pasted.length >= 6) {
      document.getElementById('reset-code-5')?.focus();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const fullCode = code.join('');
    if (fullCode.length !== 6) {
      toast.error(locale === 'ar' ? 'أدخل رمز التحقق المكون من 6 أرقام' : 'Enter the 6-digit verification code');
      return;
    }
    if (newPassword.length < 8) {
      toast.error(locale === 'ar' ? 'كلمة المرور يجب أن تكون 8 أحرف على الأقل' : 'Password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error(t('confirmPassword'));
      return;
    }

    setLoading(true);
    try {
      await forgotPasswordAPI.reset({
        email,
        code: fullCode,
        new_password: newPassword,
        new_password_confirm: confirmPassword,
      });

      setResetDone(true);
      toast.success(t('resetPasswordSuccess'));
    } catch (error) {
      const msg = error.response?.data?.error || error.response?.data?.code?.[0] ||
        error.response?.data?.new_password?.[0] || error.response?.data?.new_password_confirm?.[0] || t('error');
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  // Success screen
  if (resetDone) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl shadow-riadah-100/50 dark:shadow-gray-900/50 p-8 text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 mb-6">
              <CheckCircle className="w-10 h-10" />
            </div>
            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-3">
              {t('resetPasswordSuccess')}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {locale === 'ar'
                ? 'تم إعادة تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول بكلمة المرور الجديدة.'
                : 'Your password has been reset successfully. You can now log in with your new password.'}
            </p>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-accent-500 hover:bg-accent-600 dark:hover:bg-accent-700 text-white font-medium py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {t('backToLogin')}
              <ArrowRight className={`w-4 h-4 ${isRTL ? '' : 'rotate-180'}`} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <img src="/logo.png" alt="RIADAH ERP" className="w-20 h-20 object-contain mb-4 mx-auto" />
          <h1 className="text-3xl font-bold text-white mb-1">RIADAH</h1>
          <p className="text-sm text-riadah-100">{t('loginSubtitle')}</p>
        </div>

        {/* Form */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl shadow-riadah-100/50 dark:shadow-gray-900/50 p-8">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent-100 dark:bg-accent-900/30 text-accent-500 dark:text-accent-400 mb-4">
              <Lock className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
              {t('resetPasswordTitle')}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              {locale === 'ar'
                ? `أدخل الرمز المُرسل إلى ${email}`
                : `Enter the code sent to ${email}`}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Verification Code */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-center">
                {locale === 'ar' ? 'رمز التحقق' : 'Verification Code'}
              </label>
              <div className="flex justify-center gap-2" dir="ltr">
                {code.map((digit, index) => (
                  <input
                    key={index}
                    id={`reset-code-${index}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleCodeInput(index, e.target.value)}
                    onKeyDown={(e) => handleCodeKeyDown(index, e)}
                    onPaste={handlePasteCode}
                    className="w-11 h-13 text-center text-xl font-bold border-2 border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-xl focus:border-accent-500 focus:ring-2 focus:ring-accent-200 dark:focus:ring-accent-800 outline-none transition-all"
                    autoFocus={index === 0}
                  />
                ))}
              </div>
            </div>

            {/* New Password */}
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('newPassword')}
              </label>
              <div className="relative">
                <input
                  id="newPassword"
                  type={showNewPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder={locale === 'ar' ? 'أدخل كلمة المرور الجديدة' : 'Enter new password'}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors pl-10"
                  minLength={8}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('confirmPassword')}
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder={locale === 'ar' ? 'أعد إدخال كلمة المرور الجديدة' : 'Confirm new password'}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors pl-10"
                  minLength={8}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-accent-500 hover:bg-accent-600 dark:hover:bg-accent-700 disabled:bg-accent-300 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {t('loading')}
                </>
              ) : (
                <>
                  {t('resetPasswordBtn')}
                  <Lock className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 flex items-center justify-center gap-4">
            <button
              onClick={() => navigate('/forgot-password')}
              className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 font-medium flex items-center gap-1"
            >
              {isRTL ? <ArrowRight className="w-3 h-3" /> : <ArrowLeft className="w-3 h-3" />}
              {locale === 'ar' ? 'إعادة إرسال الرمز' : 'Resend code'}
            </button>
            <span className="text-gray-300 dark:text-gray-600">|</span>
            <Link
              to="/login"
              className="text-sm text-accent-500 hover:text-accent-600 dark:text-accent-400 font-medium"
            >
              {t('backToLogin')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
