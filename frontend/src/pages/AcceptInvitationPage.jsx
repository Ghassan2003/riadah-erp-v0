/**
 * Employee invitation acceptance page.
 * Two-step process: fetch invitation details, then accept with username/password.
 * Features: token validation, error handling for expired/invalid tokens, auto-login on success.
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useI18n } from '../i18n/I18nContext';
import { invitationsAPI } from '../api';
import { Eye, EyeOff, Loader2, Mail, ShieldCheck, UserCheck, ArrowLeft, AlertTriangle, Clock } from 'lucide-react';
import toast from 'react-hot-toast';

export default function AcceptInvitationPage() {
  const { t, isRTL } = useI18n();
  const { token } = useParams();
  const navigate = useNavigate();

  const [invitation, setInvitation] = useState(null);
  const [loadingInvitation, setLoadingInvitation] = useState(true);
  const [invitationError, setInvitationError] = useState(null);

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    password_confirm: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  // Step 1: Fetch invitation details on mount
  useEffect(() => {
    fetchInvitationDetails();
  }, [token]);

  const fetchInvitationDetails = async () => {
    setLoadingInvitation(true);
    setInvitationError(null);
    try {
      const response = await invitationsAPI.getDetails(token);
      setInvitation(response.data);
    } catch (error) {
      const status = error.response?.status;
      const data = error.response?.data;
      if (status === 404 || status === 400) {
        setInvitationError(data?.detail || data?.error || t('invalidInvitation'));
      } else if (status === 410) {
        setInvitationError(data?.detail || data?.error || t('expiredInvitation'));
      } else {
        setInvitationError(t('invalidInvitation'));
      }
    } finally {
      setLoadingInvitation(false);
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
    if (!formData.username.trim()) {
      newErrors.username = t('usernameRequired');
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

  // Step 2: Accept invitation
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      const response = await invitationsAPI.accept(token, {
        username: formData.username,
        password: formData.password,
        password_confirm: formData.password_confirm,
      });

      const { access, refresh } = response.data;
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      toast.success(t('acceptInvitationSuccess'));
      navigate('/dashboard');
    } catch (error) {
      const errorData = error.response?.data;
      let errorMsg = t('error');
      if (errorData) {
        if (errorData.detail) {
          errorMsg = errorData.detail;
        } else if (errorData.username) {
          errorMsg = errorData.username[0];
        } else if (errorData.password) {
          errorMsg = errorData.password[0];
        } else if (errorData.non_field_errors) {
          errorMsg = Array.isArray(errorData.non_field_errors) ? errorData.non_field_errors[0] : errorData.non_field_errors;
        }
      }
      toast.error(errorMsg);
      setErrors({ general: errorMsg });
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass = (field) =>
    `w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors ${
      errors[field]
        ? 'border-red-400 bg-red-50 dark:bg-red-900/20'
        : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-white dark:placeholder-gray-400'
    }`;

  // Loading state
  if (loadingInvitation) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center">
          <Loader2 className="w-10 h-10 animate-spin text-white mx-auto mb-4" />
          <p className="text-white text-lg">{t('loading')}</p>
        </div>
      </div>
    );
  }

  // Error state
  if (invitationError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-riadah-900 via-riadah-700 to-riadah-500 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl shadow-riadah-100/50 dark:shadow-gray-900/50 p-8 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 text-red-500 dark:text-red-400 mb-4">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-2">
              {t('invalidInvitation')}
            </h2>
            <p className="text-gray-500 dark:text-gray-400 mb-6 text-sm">
              {invitationError}
            </p>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-accent-500 hover:text-accent-600 dark:text-accent-400 font-medium transition-colors"
            >
              <ArrowLeft className={`w-4 h-4 ${isRTL ? 'rotate-180' : ''}`} />
              {t('loginButton')}
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
            {t('acceptInvitationSubtitle')}
          </p>
        </div>

        {/* Accept invitation form */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl shadow-riadah-100/50 dark:shadow-gray-900/50 p-8">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent-500 text-white mb-4 shadow-lg shadow-accent-200 dark:shadow-accent-900/40">
              <UserCheck className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">{t('acceptInvitationTitle')}</h2>
          </div>

          {/* Invitation details card */}
          <div className="bg-riadah-50 dark:bg-riadah-900/20 rounded-xl p-4 mb-6 space-y-3 border border-riadah-200 dark:border-riadah-800">
            {/* Email */}
            <div className="flex items-center gap-3">
              <Mail className="w-5 h-5 text-accent-500 dark:text-accent-400 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('email')}</p>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate" dir="ltr">
                  {invitation?.email}
                </p>
              </div>
            </div>

            {/* Role */}
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-accent-500 dark:text-accent-400 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('yourRole')}</p>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  {invitation?.role_display || invitation?.role}
                </p>
              </div>
            </div>

            {/* Invited by */}
            {invitation?.invited_by_name && (
              <div className="flex items-center gap-3">
                <UserCheck className="w-5 h-5 text-accent-500 dark:text-accent-400 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs text-gray-500 dark:text-gray-400">{t('invitedBy')}</p>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {invitation.invited_by_name}
                  </p>
                </div>
              </div>
            )}

            {/* Company */}
            {invitation?.company_name && (
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-accent-500 dark:text-accent-400 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs text-gray-500 dark:text-gray-400">{t('companyName')}</p>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {invitation.company_name}
                  </p>
                </div>
              </div>
            )}
          </div>

          {errors.general && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4 text-sm">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
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

            {/* Submit button */}
            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-accent-500 hover:bg-accent-600 dark:hover:bg-accent-700 disabled:bg-accent-300 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {t('loading')}
                </>
              ) : (
                <>
                  <UserCheck className="w-4 h-4" />
                  {t('acceptInvitationButton')}
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
