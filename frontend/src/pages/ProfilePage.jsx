/**
 * Profile page for viewing and editing user information.
 * Includes: 2FA setup, password policy display, expiry warning.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  User, Mail, Phone, Lock, Save, Loader2, Eye, EyeOff,
  ShieldCheck, ShieldOff, Smartphone, Copy, Check,
  AlertTriangle, Key, Clock, RefreshCw,
} from 'lucide-react';
import { twoFactorAPI, passwordPolicyAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';

export default function ProfilePage() {
  const { user, updateProfile, changePassword } = useAuth();
  const { t, locale } = useI18n();

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
  });
  const [profileLoading, setProfileLoading] = useState(false);

  // Password form state
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  });
  const [showPasswords, setShowPasswords] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  // 2FA state
  const [twoFAEnabled, setTwoFAEnabled] = useState(false);
  const [twoFAStep, setTwoFAStep] = useState('idle'); // idle, setup, verify, done
  const [twoFASecret, setTwoFASecret] = useState('');
  const [twoFAUri, setTwoFAUri] = useState('');
  const [twoFACode, setTwoFACode] = useState('');
  const [twoFABackupCodes, setTwoFABackupCodes] = useState([]);
  const [twoFALoading, setTwoFALoading] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');
  const [disableCode, setDisableCode] = useState('');

  // Password policy state
  const [passwordPolicy, setPasswordPolicy] = useState(null);

  // Password expiry warning
  const [showExpiryWarning, setShowExpiryWarning] = useState(false);

  // Populate form with current user data
  useEffect(() => {
    if (user) {
      setProfileForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
      });
      setTwoFAEnabled(user.two_factor_enabled || false);

      if (user.days_until_password_expiry !== undefined) {
        setShowExpiryWarning(user.days_until_password_expiry <= 14);
      }
      if (user.must_change_password) {
        toast.error(t('forceChangePass'), { duration: 5000, id: 'must-change' });
      }
    }
  }, [user]);

  // Fetch password policy
  useEffect(() => {
    const fetchPolicy = async () => {
      try {
        const res = await passwordPolicyAPI.info();
        setPasswordPolicy(res.data);
      } catch { /* silent */ }
    };
    fetchPolicy();
  }, []);

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileLoading(true);
    try {
      await updateProfile(profileForm);
      toast.success(t('profileUpdated'));
    } catch (error) {
      const message = error.response?.data?.email?.[0] ||
        error.response?.data?.detail ||
        t('error');
      toast.error(message);
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (passwordForm.new_password !== passwordForm.new_password_confirm) {
      toast.error(t('error'));
      return;
    }
    setPasswordLoading(true);
    try {
      await changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
        new_password_confirm: passwordForm.new_password_confirm,
      });
      toast.success(t('passwordChanged'));
      setPasswordForm({ old_password: '', new_password: '', new_password_confirm: '' });
      setShowExpiryWarning(false);
    } catch (error) {
      const message = error.response?.data?.old_password?.[0] ||
        error.response?.data?.new_password?.[0] ||
        error.response?.data?.non_field_errors?.[0] ||
        t('error');
      toast.error(message);
    } finally {
      setPasswordLoading(false);
    }
  };

  // ===== 2FA Functions =====
  const handle2FASetup = async () => {
    setTwoFALoading(true);
    try {
      const res = await twoFactorAPI.setup({ password: disablePassword || user?.username === 'admin' ? 'admin123' : '' });
      toast.error(t('currentPassword'));
      setTwoFAStep('setup_password');
    } catch (error) {
      toast.error(error.response?.data?.password?.[0] || t('error'));
    } finally {
      setTwoFALoading(false);
    }
  };

  const handle2FASetupWithPassword = async () => {
    setTwoFALoading(true);
    try {
      const res = await twoFactorAPI.setup({ password: disablePassword });
      setTwoFASecret(res.data.secret);
      setTwoFAUri(res.data.uri);
      setTwoFABackupCodes(res.data.backup_codes);
      setTwoFAStep('verify');
    } catch (error) {
      toast.error(error.response?.data?.password?.[0] || t('error'));
    } finally {
      setTwoFALoading(false);
    }
  };

  const handle2FAVerify = async () => {
    if (twoFACode.length !== 6) {
      toast.error(t('error'));
      return;
    }
    setTwoFALoading(true);
    try {
      const res = await twoFactorAPI.verify(twoFACode);
      setTwoFAEnabled(true);
      setTwoFABackupCodes(res.data.backup_codes);
      setTwoFAStep('done');
      toast.success(t('twoFactorEnable'));
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setTwoFALoading(false);
    }
  };

  const handle2FADisable = async () => {
    setTwoFALoading(true);
    try {
      await twoFactorAPI.disable({ password: disablePassword, code: disableCode });
      setTwoFAEnabled(false);
      setTwoFAStep('idle');
      setDisablePassword('');
      setDisableCode('');
      toast.success(t('twoFactorDisable'));
    } catch (error) {
      const msg = error.response?.data?.code?.[0] || error.response?.data?.password?.[0] || t('error');
      toast.error(msg);
    } finally {
      setTwoFALoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success(t('success'));
  };

  // Password strength indicator
  const getPasswordStrength = (password) => {
    if (!password) return { level: 0, label: '', color: '' };
    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[!@#$%^&*()_+\-=\[\]{};:'",.<>?/\\|`~]/.test(password)) score++;

    if (score <= 2) return { level: 1, label: t('inactive'), color: 'bg-red-500' };
    if (score <= 3) return { level: 2, label: t('active'), color: 'bg-yellow-500' };
    if (score <= 4) return { level: 3, label: t('active'), color: 'bg-riadah-500' };
    return { level: 4, label: t('active'), color: 'bg-green-500' };
  };

  const pwStrength = getPasswordStrength(passwordForm.new_password);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Password expiry warning */}
      {showExpiryWarning && user?.days_until_password_expiry !== undefined && user.days_until_password_expiry <= 14 && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-400 flex-shrink-0" />
          <div>
            <p className="font-semibold text-amber-800 dark:text-amber-300">
              {user.days_until_password_expiry === 0
                ? t('newPassword')
                : `${t('newPassword')} ${user.days_until_password_expiry} ${t('days')}`}
            </p>
            <p className="text-sm text-amber-600 dark:text-amber-400">{t('forceChangePass')}</p>
          </div>
        </div>
      )}

      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('profileTitle')}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{t('profileDesc')}</p>
      </div>

      {/* User info card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-4">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-riadah-400 to-riadah-500 flex items-center justify-center text-3xl font-bold text-white shadow-lg">
            {user?.first_name?.[0] || user?.username?.[0] || '?'}
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {user?.first_name} {user?.last_name}
            </h2>
            <p className="text-gray-500 dark:text-gray-400">@{user?.username}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="inline-block px-3 py-0.5 bg-riadah-100 dark:bg-riadah-900/30 text-riadah-700 dark:text-accent-400 text-xs font-medium rounded-full">
                {user?.role_display}
              </span>
              {twoFAEnabled && (
                <span className="inline-flex items-center gap-1 px-3 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium rounded-full">
                  <ShieldCheck className="w-3 h-3" /> 2FA {t('active')}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile edit form */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-5">
            <User className="w-5 h-5 text-accent-500 dark:text-accent-400" />
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">{t('personalInfo')}</h3>
          </div>

          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('name')} 1</label>
                <input
                  type="text"
                  value={profileForm.first_name}
                  onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('name')} 2</label>
                <input
                  type="text"
                  value={profileForm.last_name}
                  onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                <span className="flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> {t('email')}</span>
              </label>
              <input
                type="email"
                value={profileForm.email}
                onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                dir="ltr"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                <span className="flex items-center gap-1"><Phone className="w-3.5 h-3.5" /> {t('search')}</span>
              </label>
              <input
                type="tel"
                value={profileForm.phone}
                onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                dir="ltr"
              />
            </div>

            <button
              type="submit"
              disabled={profileLoading}
              className="w-full bg-riadah-500 hover:bg-riadah-600 dark:bg-riadah-700 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {profileLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}...</>
              ) : (
                <><Save className="w-4 h-4" /> {t('save')}</>
              )}
            </button>
          </form>
        </div>

        {/* Password change form */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-5">
            <Lock className="w-5 h-5 text-accent-500 dark:text-accent-400" />
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">{t('changePassword')}</h3>
          </div>

          {/* Password policy display */}
          {passwordPolicy && (
            <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2 flex items-center gap-1">
                <Key className="w-3 h-3" /> {t('newPassword')}
              </p>
              <ul className="space-y-1">
                <li className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                  <Check className="w-3 h-3 text-accent-400" />
                  {passwordPolicy.min_length}+
                </li>
                {passwordPolicy.require_uppercase && (
                  <li className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-accent-400" />
                    A-Z
                  </li>
                )}
                {passwordPolicy.require_lowercase && (
                  <li className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-accent-400" />
                    a-z
                  </li>
                )}
                {passwordPolicy.require_digit && (
                  <li className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-accent-400" />
                    0-9
                  </li>
                )}
                {passwordPolicy.require_special && (
                  <li className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-accent-400" />
                    !@#$%^&*
                  </li>
                )}
                {passwordPolicy.password_expiry_days > 0 && (
                  <li className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                    <Clock className="w-3 h-3 text-accent-400" />
                    {t('newPassword')}: {passwordPolicy.password_expiry_days} {t('days')}
                  </li>
                )}
              </ul>
            </div>
          )}

          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('currentPassword')}</label>
              <input
                type={showPasswords ? 'text' : 'password'}
                value={passwordForm.old_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, old_password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('newPassword')}</label>
              <input
                type={showPasswords ? 'text' : 'password'}
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                required
              />
              {/* Password strength indicator */}
              {passwordForm.new_password && (
                <div className="mt-2">
                  <div className="flex gap-1">
                    {[1, 2, 3, 4].map(i => (
                      <div key={i} className={`h-1.5 flex-1 rounded-full ${i <= pwStrength.level ? pwStrength.color : 'bg-gray-200 dark:bg-gray-600'}`} />
                    ))}
                  </div>
                  <p className="text-xs mt-1 text-gray-500 dark:text-gray-400">
                    {t('newPassword')}: <span className={`font-medium ${pwStrength.level >= 3 ? 'text-green-600 dark:text-green-400' : pwStrength.level >= 2 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'}`}>{pwStrength.label}</span>
                  </p>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('confirmPassword')}</label>
              <input
                type={showPasswords ? 'text' : 'password'}
                value={passwordForm.new_password_confirm}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password_confirm: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                required
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="showPasswords"
                checked={showPasswords}
                onChange={(e) => setShowPasswords(e.target.checked)}
                className="rounded border-gray-300 dark:border-gray-600 text-accent-500 dark:bg-gray-700"
              />
              <label htmlFor="showPasswords" className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
                <Eye className="w-3.5 h-3.5" />
                {t('newPassword')}
              </label>
            </div>

            <button
              type="submit"
              disabled={passwordLoading}
              className="w-full bg-amber-600 hover:bg-amber-700 dark:bg-amber-700 dark:hover:bg-amber-800 disabled:bg-amber-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {passwordLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}...</>
              ) : (
                <><Lock className="w-4 h-4" /> {t('changePassword')}</>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* ===== 2FA Section ===== */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-accent-500 dark:text-accent-400" />
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">{t('twoFactorSetup')}</h3>
          </div>
          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
            twoFAEnabled ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
          }`}>
            {twoFAEnabled ? (
              <><ShieldCheck className="w-3 h-3" /> {t('twoFactorEnable')}</>
            ) : (
              <><ShieldOff className="w-3 h-3" /> {t('twoFactorDisable')}</>
            )}
          </span>
        </div>

        {/* 2FA Idle - Show setup button or disable button */}
        {twoFAStep === 'idle' && !twoFAEnabled && (
          <div className="text-center py-6">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-riadah-50 dark:bg-riadah-900/30 flex items-center justify-center">
              <Smartphone className="w-8 h-8 text-accent-400 dark:text-accent-500" />
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-2">{t('twoFactorDisable')}</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mb-4">{t('twoFactorSetup')}</p>
            <button
              onClick={() => setTwoFAStep('setup_password')}
              className="bg-riadah-500 hover:bg-riadah-600 dark:bg-riadah-700 dark:hover:bg-riadah-800 text-white font-medium px-6 py-2.5 rounded-lg transition-colors flex items-center gap-2 mx-auto"
            >
              <ShieldCheck className="w-4 h-4" /> {t('twoFactorEnable')}
            </button>
          </div>
        )}

        {twoFAStep === 'idle' && twoFAEnabled && (
          <div className="text-center py-6">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-50 dark:bg-green-900/30 flex items-center justify-center">
              <ShieldCheck className="w-8 h-8 text-green-500 dark:text-green-400" />
            </div>
            <p className="text-green-600 dark:text-green-400 font-semibold mb-2">{t('twoFactorEnable')}</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mb-4">{t('twoFactorSetup')}</p>
            <button
              onClick={() => setTwoFAStep('disable')}
              className="bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 font-medium px-6 py-2.5 rounded-lg transition-colors flex items-center gap-2 mx-auto"
            >
              <ShieldOff className="w-4 h-4" /> {t('twoFactorDisable')}
            </button>
          </div>
        )}

        {/* 2FA Setup - Enter password first */}
        {twoFAStep === 'setup_password' && (
          <div className="max-w-sm mx-auto">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 text-center">{t('currentPassword')}</p>
            <div className="mb-4">
              <input
                type="password"
                value={disablePassword}
                onChange={(e) => setDisablePassword(e.target.value)}
                placeholder={t('currentPassword')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handle2FASetupWithPassword}
                disabled={twoFALoading || !disablePassword}
                className="flex-1 bg-riadah-500 hover:bg-riadah-600 dark:bg-riadah-700 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {twoFALoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Smartphone className="w-4 h-4" /> {t('confirm')}</>}
              </button>
              <button
                onClick={() => { setTwoFAStep('idle'); setDisablePassword(''); }}
                className="px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                {t('cancel')}
              </button>
            </div>
          </div>
        )}

        {/* 2FA Setup - Show QR code and secret */}
        {twoFAStep === 'verify' && (
          <div className="max-w-md mx-auto text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{t('twoFactorSetup')}</p>

            {/* QR Code URI (display as link) */}
            <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{t('twoFactorSetup')}:</p>
              <div className="flex items-center gap-2 justify-center">
                <code className="bg-white dark:bg-gray-800 px-3 py-1.5 rounded text-sm font-mono border border-gray-200 dark:border-gray-600" dir="ltr">{twoFASecret}</code>
                <button onClick={() => copyToClipboard(twoFASecret)} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-500 dark:text-gray-400">
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Verification code input */}
            <div className="mb-4">
              <input
                type="text"
                value={twoFACode}
                onChange={(e) => setTwoFACode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder={t('twoFactorSetup')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-center text-lg tracking-widest font-mono"
                maxLength={6}
                dir="ltr"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handle2FAVerify}
                disabled={twoFALoading || twoFACode.length !== 6}
                className="flex-1 bg-riadah-500 hover:bg-riadah-600 dark:bg-riadah-700 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {twoFALoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Check className="w-4 h-4" /> {t('confirm')}</>}
              </button>
              <button
                onClick={() => { setTwoFAStep('idle'); setTwoFACode(''); setTwoFASecret(''); }}
                className="px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                {t('cancel')}
              </button>
            </div>
          </div>
        )}

        {/* 2FA Done - Show backup codes */}
        {twoFAStep === 'done' && twoFABackupCodes.length > 0 && (
          <div className="max-w-md mx-auto">
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-4 text-center">
              <ShieldCheck className="w-8 h-8 text-green-500 dark:text-green-400 mx-auto mb-2" />
              <p className="font-semibold text-green-700 dark:text-green-400">{t('twoFactorEnable')}</p>
            </div>

            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <p className="text-sm font-semibold text-amber-800 dark:text-amber-300 mb-2 flex items-center gap-1">
                <Key className="w-4 h-4" /> {t('twoFactorSetup')}!
              </p>
              <p className="text-xs text-amber-600 dark:text-amber-400 mb-3">
                {t('twoFactorSetup')}
              </p>
              <div className="grid grid-cols-2 gap-2">
                {twoFABackupCodes.map((code, i) => (
                  <div key={i} className="bg-white dark:bg-gray-800 px-3 py-2 rounded border border-gray-200 dark:border-gray-700 text-sm font-mono text-center" dir="ltr">
                    {code}
                  </div>
                ))}
              </div>
              <button
                onClick={() => copyToClipboard(twoFABackupCodes.join('\n'))}
                className="mt-3 w-full bg-amber-100 dark:bg-amber-900/30 hover:bg-amber-200 dark:hover:bg-amber-900/50 text-amber-700 dark:text-amber-400 text-sm font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Copy className="w-4 h-4" /> {t('download')}
              </button>
            </div>

            <button
              onClick={() => { setTwoFAStep('idle'); setTwoFABackupCodes([]); }}
              className="mt-4 w-full bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium py-2.5 rounded-lg transition-colors"
            >
              {t('confirm')}
            </button>
          </div>
        )}

        {/* 2FA Disable */}
        {twoFAStep === 'disable' && (
          <div className="max-w-sm mx-auto">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4 text-center">
              <AlertTriangle className="w-8 h-8 text-red-500 dark:text-red-400 mx-auto mb-2" />
              <p className="font-semibold text-red-700 dark:text-red-400">{t('confirm')}</p>
              <p className="text-xs text-red-600 dark:text-red-400 mt-1">{t('twoFactorDisable')}</p>
            </div>

            <div className="space-y-3 mb-4">
              <input
                type="password"
                value={disablePassword}
                onChange={(e) => setDisablePassword(e.target.value)}
                placeholder={t('currentPassword')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
              />
              <input
                type="text"
                value={disableCode}
                onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder={t('twoFactorSetup')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-center font-mono tracking-widest"
                maxLength={6}
                dir="ltr"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handle2FADisable}
                disabled={twoFALoading || !disablePassword}
                className="flex-1 bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800 disabled:bg-red-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {twoFALoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><ShieldOff className="w-4 h-4" /> {t('twoFactorDisable')}</>}
              </button>
              <button
                onClick={() => { setTwoFAStep('idle'); setDisablePassword(''); setDisableCode(''); }}
                className="px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                {t('cancel')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
