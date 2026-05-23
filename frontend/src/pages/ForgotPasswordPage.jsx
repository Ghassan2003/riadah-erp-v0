/**
 * Forgot Password page - Step 1: Enter email to receive verification code.
 * Sends a 6-digit OTP to the user's email for password recovery.
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { forgotPasswordAPI } from '../api';
import { Mail, Loader2, ArrowRight, KeyRound, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';

export default function ForgotPasswordPage() {
  const { t, locale, isRTL } = useI18n();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [devCode, setDevCode] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) {
      toast.error(locale === 'ar' ? 'البريد الإلكتروني مطلوب' : 'Email is required');
      return;
    }

    setLoading(true);
    try {
      const response = await forgotPasswordAPI.request(email);
      setSent(true);

      // In development mode, backend returns the code
      if (response.data._dev_code) {
        setDevCode(response.data._dev_code);
      }

      toast.success(t('forgotPasswordSent'));
    } catch (error) {
      const msg = error.response?.data?.email?.[0] || error.response?.data?.error || t('error');
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl shadow-riadah-100/50 dark:shadow-gray-900/50 p-8 text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 mb-6">
              <CheckCircle className="w-10 h-10" />
            </div>

            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-3">
              {t('forgotPasswordCheckEmail')}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-2">
              {locale === 'ar'
                ? `تم إرسال رمز التحقق إلى:`
                : `Verification code sent to:`}
            </p>
            <p className="text-accent-500 dark:text-accent-400 font-semibold mb-4" dir="ltr">{email}</p>

            {devCode && (
              <div className="mb-6 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl">
                <p className="text-sm font-medium text-amber-700 dark:text-amber-400 mb-1">
                  {locale === 'ar' ? 'رمز التحقق (وضع التطوير):' : 'Verification Code (Dev Mode):'}
                </p>
                <p className="text-3xl font-bold text-amber-800 dark:text-amber-300 tracking-widest" dir="ltr">
                  {devCode}
                </p>
              </div>
            )}

            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              {locale === 'ar'
                ? 'هذا الرمز صالح لمدة 15 دقيقة فقط'
                : 'This code is valid for 15 minutes only'}
            </p>

            <div className="space-y-3">
              <button
                onClick={() => navigate('/reset-password', { state: { email, devCode } })}
                className="w-full bg-accent-500 hover:bg-accent-600 dark:hover:bg-accent-700 text-white font-medium py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {t('forgotPasswordEnterCode')}
                <ArrowRight className={`w-4 h-4 ${isRTL ? '' : 'rotate-180'}`} />
              </button>
              <Link
                to="/login"
                className="w-full block text-center text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 font-medium py-2 text-sm"
              >
                {t('backToLogin')}
              </Link>
            </div>
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
              <KeyRound className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
              {t('forgotPasswordTitle')}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              {t('forgotPasswordDesc')}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('email')}
              </label>
              <div className="relative">
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={locale === 'ar' ? 'أدخل بريدك الإلكتروني' : 'Enter your email address'}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors"
                  dir="ltr"
                  required
                />
                <Mail className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
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
                  {t('forgotPasswordSend')}
                  <ArrowRight className={`w-4 h-4 ${isRTL ? '' : 'rotate-180'}`} />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
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
