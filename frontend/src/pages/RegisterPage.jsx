/**
 * Business owner registration page.
 * Allows creating the first admin account for a new company.
 * Features: availability check, form validation, password strength, auto-login on success.
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useI18n } from '../i18n/I18nContext';
import { authAPI } from '../api';
import { Eye, EyeOff, Loader2, Building2, UserPlus, ShieldAlert, ArrowLeft, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const { t, isRTL } = useI18n();
  const navigate = useNavigate();

  const [registrationAvailable, setRegistrationAvailable] = useState(true);
  const [checkingAvailability, setCheckingAvailability] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    phone: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  // Check if registration is available (no admin exists yet)
  useEffect(() => {
    checkRegistrationAvailability();
  }, []);

  const checkRegistrationAvailability = async () => {
    setCheckingAvailability(true);
    try {
      const response = await authAPI.checkRegistrationAvailability();
      setRegistrationAvailable(response.data.registration_available);
    } catch (error) {
      // If the endpoint doesn't exist, assume registration is available
      setRegistrationAvailable(true);
    } finally {
      setCheckingAvailability(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.first_name.trim()) {
      newErrors.first_name = t('required');
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = t('required');
    }
    if (!formData.username.trim()) {
      newErrors.username = t('usernameRequired');
    }
    if (!formData.email.trim()) {
      newErrors.email = t('required');
    }
    if (!formData.password) {
      newErrors.password = t('passwordRequired');
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    if (!formData.password_confirm) {
      newErrors.password_confirm = t('required');
    } else if (formData.password !== formData.password_confirm) {
      newErrors.password_confirm = t('passwordMismatch');
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const response = await authAPI.registerOwner({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        password_confirm: formData.password_confirm,
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone,
      });

      const { access, refresh, user: userData } = response.data;

      // Store tokens directly
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      toast.success(t('registerSuccess'));

      // Navigate to dashboard - the auth context will pick up the token on next render
      navigate('/dashboard');
    } catch (error) {
      const errorData = error.response?.data;
      let errorMsg = t('error');

      if (errorData) {
        if (errorData.error) {
          errorMsg = errorData.error;
        } else if (errorData.detail) {
          errorMsg = errorData.detail;
        } else if (errorData.username) {
          errorMsg = Array.isArray(errorData.username) ? errorData.username[0] : errorData.username;
        } else if (errorData.email) {
          errorMsg = Array.isArray(errorData.email) ? errorData.email[0] : errorData.email;
        } else if (errorData.non_field_errors) {
          errorMsg = Array.isArray(errorData.non_field_errors) ? errorData.non_field_errors[0] : errorData.non_field_errors;
        } else if (errorData.password) {
          errorMsg = Array.isArray(errorData.password) ? errorData.password[0] : errorData.password;
        } else if (errorData.password_confirm) {
          errorMsg = Array.isArray(errorData.password_confirm) ? errorData.password_confirm[0] : errorData.password_confirm;
        }
      }

      toast.error(errorMsg);
      setErrors({ general: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const inputClass = (field) =>
    `w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors ${
      errors[field]
        ? 'border-red-400 bg-red-50 dark:bg-red-900/20'
        : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400'
    }`;

  // Loading state - checking availability
  if (checkingAvailability) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center">
          <Loader2 className="w-10 h-10 animate-spin text-white mx-auto mb-4" />
          <p className="text-white text-lg">{t('loading')}</p>
        </div>
      </div>
    );
  }

  // Registration not available - admin already exists
  if (!registrationAvailable) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl shadow-riadah-100/50 dark:shadow-gray-900/50 p-8 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-500 dark:text-amber-400 mb-4">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-2">
              التسجيل غير متاح
            </h2>
            <p className="text-gray-500 dark:text-gray-400 mb-6 text-sm">
              يوجد مدير نظام بالفعل. يرجى التواصل مع المدير الحالي للحصول على دعوة إنشاء حساب.
            </p>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 bg-accent-500 hover:bg-accent-600 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
            >
              <ArrowLeft className={`w-4 h-4 ${isRTL ? 'rotate-180' : ''}`} />
              تسجيل الدخول
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and title */}
        <div className="text-center mb-8">
          <img src="/logo.png" alt="RIADAH ERP" className="w-20 h-20 object-contain mb-4 mx-auto" />
          <h1 className="text-3xl font-bold text-white mb-1">
            RIADAH
          </h1>
          <p className="text-sm text-center text-riadah-100 mb-2">
            {t('registerSubtitle')}
          </p>
        </div>

        {/* Registration form */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl shadow-riadah-100/50 dark:shadow-gray-900/50 p-8">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent-500 text-white mb-4 shadow-lg shadow-accent-200 dark:shadow-accent-900/40">
              <Building2 className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
              إنشاء حساب صاحب العمل
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              أنشئ حسابك كمسؤول النظام لإدارة المؤسسة وإضافة الموظفين
            </p>
          </div>

          {errors.general && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4 text-sm">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* First Name & Last Name */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('firstName')} *
                </label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  value={formData.first_name}
                  onChange={handleChange}
                  className={inputClass('first_name')}
                />
                {errors.first_name && (
                  <p className="text-red-500 dark:text-red-400 text-xs mt-1">{errors.first_name}</p>
                )}
              </div>
              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('lastName')} *
                </label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  value={formData.last_name}
                  onChange={handleChange}
                  className={inputClass('last_name')}
                />
                {errors.last_name && (
                  <p className="text-red-500 dark:text-red-400 text-xs mt-1">{errors.last_name}</p>
                )}
              </div>
            </div>

            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('username')} *
              </label>
              <input
                id="username"
                name="username"
                type="text"
                value={formData.username}
                onChange={handleChange}
                placeholder={t('enterUsername')}
                className={inputClass('username')}
                autoComplete="username"
              />
              {errors.username && (
                <p className="text-red-500 dark:text-red-400 text-xs mt-1">{errors.username}</p>
              )}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('email')} *
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                className={inputClass('email')}
                dir="ltr"
                autoComplete="email"
              />
              {errors.email && (
                <p className="text-red-500 dark:text-red-400 text-xs mt-1">{errors.email}</p>
              )}
            </div>

            {/* Phone */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('phone')}
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleChange}
                className={inputClass('phone')}
                dir="ltr"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('password')} *
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleChange}
                  placeholder={t('enterPassword')}
                  className={`${inputClass('password')} pl-10`}
                  autoComplete="new-password"
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

            {/* Password Confirm */}
            <div>
              <label htmlFor="password_confirm" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                {t('confirmPassword')} *
              </label>
              <div className="relative">
                <input
                  id="password_confirm"
                  name="password_confirm"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={formData.password_confirm}
                  onChange={handleChange}
                  className={`${inputClass('password_confirm')} pl-10`}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password_confirm && (
                <p className="text-red-500 dark:text-red-400 text-xs mt-1">{errors.password_confirm}</p>
              )}
            </div>

            {/* Permissions info */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 space-y-1.5 border border-blue-200 dark:border-blue-800">
              <p className="text-xs font-medium text-blue-800 dark:text-blue-300">ستحصل على الصلاحيات التالية:</p>
              <div className="flex flex-wrap gap-1.5">
                {['إدارة كاملة', 'إضافة موظفين', 'دعوة مستخدمين', 'إدارة الصلاحيات', 'جميع الوحدات'].map((perm) => (
                  <span key={perm} className="inline-flex items-center gap-1 text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full">
                    <CheckCircle className="w-3 h-3" />
                    {perm}
                  </span>
                ))}
              </div>
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
                  {t('loading')}
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  إنشاء حساب المسؤول
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer link to login */}
        <div className="text-center mt-6">
          <Link
            to="/login"
            className="text-sm text-riadah-100 hover:text-white dark:text-gray-400 dark:hover:text-gray-200 font-medium transition-colors"
          >
            {t('registerLoginLink')}
          </Link>
        </div>
      </div>
    </div>
  );
}
