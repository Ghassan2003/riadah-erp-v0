/**
 * Login page with username/password + 2FA authentication.
 * Features: form validation, error handling, 2FA verification step,
 * dark mode support, and i18n (Arabic/English).
 */

import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, Loader2, Smartphone, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const { login, verify2FA, cancel2FA, isAuthenticated, pending2FA, pending2FAData } = useAuth();
  const { t, isRTL } = useI18n();
  const navigate = useNavigate();

  // Login form state
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  // 2FA state
  const [twoFACode, setTwoFACode] = useState(['', '', '', '', '', '']);
  const [twoFALoading, setTwoFALoading] = useState(false);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const validate = () => {
    const newErrors = {};
    if (!formData.username.trim()) {
      newErrors.username = t('usernameRequired');
    }
    if (!formData.password) {
      newErrors.password = t('passwordRequired');
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const result = await login(formData.username, formData.password);
      if (result.requires_2fa) {
        toast.success(t('enter2FACode'));
      } else {
        toast.success(t('loginSuccess'));
        navigate('/dashboard');
      }
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail ||
        t('loginFailed');
      toast.error(errorMessage);
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handle2FASubmit = async (e) => {
    e.preventDefault();
    const code = twoFACode.join('');
    if (code.length !== 6) {
      toast.error(t('invalid2FALength'));
      return;
    }

    setTwoFALoading(true);
    try {
      const user = await verify2FA(code);
      toast.success(t('loginSuccess'));
      if (user.must_change_password) {
        navigate('/profile');
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error(error.response?.data?.error || t('invalid2FACode'));
      setTwoFACode(['', '', '', '', '', '']);
      // Focus first input
      setTimeout(() => {
        document.getElementById('2fa-0')?.focus();
      }, 100);
    } finally {
      setTwoFALoading(false);
    }
  };

  const handle2FAInput = (index, value) => {
    if (value.length > 1) value = value.slice(-1);
    if (!/^\d*$/.test(value)) return;

    const newCode = [...twoFACode];
    newCode[index] = value;
    setTwoFACode(newCode);

    // Auto-focus next input
    if (value && index < 5) {
      document.getElementById(`2fa-${index + 1}`)?.focus();
    }
  };

  const handle2FAKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !twoFACode[index] && index > 0) {
      document.getElementById(`2fa-${index - 1}`)?.focus();
    }
    if (e.key === 'Enter' && twoFACode.join('').length === 6) {
      handle2FASubmit(e);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handlePaste2FA = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newCode = [...twoFACode];
    for (let i = 0; i < pasted.length; i++) {
      newCode[i] = pasted[i];
    }
    setTwoFACode(newCode);
    if (pasted.length >= 6) {
      document.getElementById('2fa-5')?.focus();
    }
  };

  // ===== 2FA Verification Screen =====
  if (pending2FA) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-riadah-600 text-white mb-4 shadow-lg shadow-riadah-200 dark:shadow-riadah-900/40">
              <Smartphone className="w-10 h-10" />
            </div>
            <h1 className="text-3xl font-bold text-white">{t('twoFactorAuth')}</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-2">{t('twoFactorDesc')}</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl shadow-riadah-100/50 dark:shadow-gray-900/50 p-8">
            <div className="text-center mb-6">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-riadah-50 dark:bg-riadah-900/30 flex items-center justify-center">
                <span className="text-2xl font-bold text-riadah-700 dark:text-riadah-400">
                  {pending2FAData?.username?.[0]?.toUpperCase() || '?'}
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {t('twoFactorWelcome')} <span className="font-semibold">{pending2FAData?.username}</span>
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                {t('twoFactorOpenApp')}
              </p>
            </div>

            <form onSubmit={handle2FASubmit} className="space-y-6">
              {/* 2FA Code Input */}
              <div className="flex justify-center gap-3" dir="ltr">
                {twoFACode.map((digit, index) => (
                  <input
                    key={index}
                    id={`2fa-${index}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handle2FAInput(index, e.target.value)}
                    onKeyDown={(e) => handle2FAKeyDown(index, e)}
                    onPaste={handlePaste2FA}
                    className="w-12 h-14 text-center text-xl font-bold border-2 border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-xl focus:border-accent-500 focus:ring-2 focus:ring-accent-200 dark:focus:ring-accent-800 outline-none transition-all"
                    autoFocus={index === 0}
                  />
                ))}
              </div>

              <button
                type="submit"
                disabled={twoFALoading || twoFACode.join('').length !== 6}
                className="w-full bg-accent-500 hover:bg-accent-600 dark:hover:bg-accent-700 disabled:bg-accent-300 text-white font-medium py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {twoFALoading ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> {t('verifying')}</>
                ) : (
                  <><ArrowRight className="w-5 h-5" /> {t('verify')}</>
                )}
              </button>

              <button
                type="button"
                onClick={cancel2FA}
                className="w-full text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 font-medium py-2 text-sm"
              >
                {t('backToLogin')}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // ===== Normal Login Screen =====
  return (
    <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and title */}
        <div className="text-center mb-8">
          <img src="/logo.png" alt="RIADAH ERP" className="w-20 h-20 object-contain mb-4 mx-auto" />
          <h1 className="text-3xl font-bold text-white mb-1">
            RIADAH
          </h1>
          <p className="text-sm text-center text-riadah-100 mb-6">
            {t('loginSubtitle')}
          </p>
        </div>

        {/* Login form */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl shadow-riadah-100/50 dark:shadow-gray-900/50 p-8">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-6">{t('loginHeading')}</h2>

          {errors.general && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4 text-sm">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('username')}
              </label>
              <input
                id="username"
                name="username"
                type="text"
                value={formData.username}
                onChange={handleChange}
                placeholder={t('enterUsername')}
                className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors ${
                  errors.username
                    ? 'border-red-400 bg-red-50 dark:bg-red-900/20'
                    : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400'
                }`}
                autoComplete="username"
              />
              {errors.username && (
                <p className="text-red-500 dark:text-red-400 text-xs mt-1">{errors.username}</p>
              )}
            </div>

            {/* Password field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('password')}
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleChange}
                  placeholder={t('enterPassword')}
                  className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors pl-10 ${
                    errors.password
                      ? 'border-red-400 bg-red-50 dark:bg-red-900/20'
                      : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400'
                  }`}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-red-500 dark:text-red-400 text-xs mt-1">{errors.password}</p>
              )}
            </div>

            {/* Forgot Password Link */}
            <div className="text-right">
              <Link
                to="/forgot-password"
                className="text-sm text-accent-500 hover:text-accent-600 dark:text-accent-400 font-medium"
              >
                {t('forgotPasswordLink')}
              </Link>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-accent-500 hover:bg-accent-600 dark:hover:bg-accent-700 disabled:bg-accent-300 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {t('loggingIn')}
                </>
              ) : (
                t('loginButton')
              )}
            </button>
          </form>

          {/* Demo credentials hint */}
          <div className="mt-6 p-4 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg border border-riadah-200 dark:border-riadah-800">
            <p className="text-sm font-medium text-riadah-800 dark:text-riadah-300 mb-2">{t('demoCredentials')}</p>
            <p className="text-xs text-riadah-600 dark:text-riadah-400">
              {t('demoUser')} <span className="font-mono bg-riadah-100 dark:bg-riadah-800/50 px-1 rounded">admin</span>
            </p>
            <p className="text-xs text-riadah-600 dark:text-riadah-400">
              {t('demoPass')} <span className="font-mono bg-riadah-100 dark:bg-riadah-800/50 px-1 rounded">admin123</span>
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-400 dark:text-gray-500 mt-6">
          {t('loginFooter')}
        </p>
      </div>
    </div>
  );
}
