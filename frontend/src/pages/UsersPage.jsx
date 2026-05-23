/**
 * User management page - admin only.
 * Full CRUD with 2FA reset, force password change, edit user, security info,
 * invite employee modal, and pending invitations table.
 */

import { useState, useEffect } from 'react';
import { usersAPI, exportAPI, invitationsAPI } from '../api';
import {
  Users, Search, Shield, Loader2, UserCircle, Download,
  Plus, X, Eye, EyeOff, Lock, ShieldOff, ShieldCheck,
  Key, AlertTriangle, Save, Edit3, UserPlus, Mail, Copy, Clock,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';

const ROLE_LABELS = {
  admin: 'admin',
  warehouse: 'warehouse',
  sales: 'sales',
  accountant: 'accountant',
  hr: 'hr',
  purchasing: 'purchasing',
  project_manager: 'project_manager',
};

export default function UsersPage() {
  const { t, locale } = useI18n();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [exporting, setExporting] = useState(false);

  // Create user modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    username: '', email: '', password: '', password_confirm: '',
    first_name: '', last_name: '', phone: '', role: 'sales',
    must_change_password: true,
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [showCreatePassword, setShowCreatePassword] = useState(false);

  // Edit user modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [editForm, setEditForm] = useState({
    email: '', first_name: '', last_name: '', phone: '', role: '',
    is_active: true,
  });
  const [editLoading, setEditLoading] = useState(false);

  // User detail modal
  const [selectedUser, setSelectedUser] = useState(null);

  // Invite employee modal
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    email: '', role: 'sales', first_name: '', last_name: '', phone: '',
  });
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteLink, setInviteLink] = useState('');

  // Pending invitations
  const [invitations, setInvitations] = useState([]);
  const [loadingInvitations, setLoadingInvitations] = useState(true);
  const [activeTab, setActiveTab] = useState('users');

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await exportAPI.users();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'users.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(t('success'));
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchInvitations();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await usersAPI.list();
      setUsers(response.data.results || response.data);
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setLoading(false);
    }
  };

  const fetchInvitations = async () => {
    try {
      const response = await invitationsAPI.list();
      setInvitations(response.data.results || response.data || []);
    } catch (error) {
      // Silently fail - invitations feature may not be available
    } finally {
      setLoadingInvitations(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (createForm.password !== createForm.password_confirm) {
      toast.error(locale === 'ar' ? 'كلمات المرور غير متطابقة' : 'Passwords do not match');
      return;
    }
    if (createForm.password.length < 8) {
      toast.error(locale === 'ar' ? 'كلمة المرور يجب أن تكون 8 أحرف على الأقل' : 'Password must be at least 8 characters');
      return;
    }

    setCreateLoading(true);
    try {
      await usersAPI.create(createForm);
      toast.success(t('userCreated'));
      setShowCreateModal(false);
      setCreateForm({
        username: '', email: '', password: '', password_confirm: '',
        first_name: '', last_name: '', phone: '', role: 'sales',
        must_change_password: true,
      });
      fetchUsers();
    } catch (error) {
      const msg = error.response?.data?.username?.[0] || error.response?.data?.password?.[0] ||
        error.response?.data?.email?.[0] || error.response?.data?.detail || t('error');
      toast.error(msg);
    } finally {
      setCreateLoading(false);
    }
  };

  // Invite employee
  const handleInviteEmployee = async (e) => {
    e.preventDefault();
    if (!inviteForm.email.trim()) {
      toast.error(t('required'));
      return;
    }

    setInviteLoading(true);
    setInviteLink('');
    try {
      const response = await invitationsAPI.create(inviteForm);
      toast.success(t('inviteSuccess'));
      if (response.data?.invite_link) {
        setInviteLink(response.data.invite_link);
      }
      setInviteForm({ email: '', role: 'sales', first_name: '', last_name: '', phone: '' });
      fetchInvitations();
    } catch (error) {
      const msg = error.response?.data?.email?.[0] || error.response?.data?.detail ||
        error.response?.data?.non_field_errors?.[0] || t('error');
      toast.error(msg);
    } finally {
      setInviteLoading(false);
    }
  };

  const handleCancelInvitation = async (id) => {
    if (!window.confirm(t('cancelInvitationConfirm'))) return;
    try {
      await invitationsAPI.cancel(id);
      toast.success(t('invitationCancelled'));
      fetchInvitations();
    } catch (error) {
      toast.error(t('error'));
    }
  };

  const copyInviteLink = () => {
    if (inviteLink) {
      navigator.clipboard.writeText(inviteLink);
      toast.success(t('inviteLinkCopied'));
    }
  };

  const openEditModal = (user) => {
    setEditUser(user);
    setEditForm({
      email: user.email || '',
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      phone: user.phone || '',
      role: user.role || '',
      is_active: user.is_active !== undefined ? user.is_active : true,
    });
    setShowEditModal(true);
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    if (!editUser) return;

    setEditLoading(true);
    try {
      await usersAPI.update(editUser.id, editForm);
      toast.success(locale === 'ar' ? 'تم تحديث المستخدم بنجاح' : 'User updated successfully');
      setShowEditModal(false);
      setEditUser(null);
      fetchUsers();
    } catch (error) {
      const msg = error.response?.data?.email?.[0] || error.response?.data?.role?.[0] || t('error');
      toast.error(msg);
    } finally {
      setEditLoading(false);
    }
  };

  const handleToggleActive = async (userId) => {
    try {
      await usersAPI.toggleActive(userId);
      toast.success(t('success'));
      fetchUsers();
    } catch (error) {
      toast.error(t('error'));
    }
  };

  const handleReset2FA = async (userId, username) => {
    if (!confirm(`${t('confirm')} ${t('reset2FA')} ${username}?`)) return;
    try {
      await usersAPI.reset2FA(userId);
      toast.success(t('success'));
      fetchUsers();
    } catch (error) {
      toast.error(t('error'));
    }
  };

  const handleForcePasswordChange = async (userId, username) => {
    if (!confirm(`${t('confirm')} ${t('forceChangePass')} ${username}?`)) return;
    try {
      await usersAPI.forceChangePassword(userId);
      toast.success(t('success'));
      fetchUsers();
    } catch (error) {
      toast.error(t('error'));
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.first_name?.includes(searchTerm) ||
      u.last_name?.includes(searchTerm)
  );

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      case 'warehouse': return 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400';
      case 'sales': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      case 'accountant': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'hr': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400';
      case 'purchasing': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
      case 'project_manager': return 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'accepted': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      case 'expired': return 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400';
      case 'cancelled': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('manageUsers')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {locale === 'ar' ? 'إنشاء وتعديل وإدارة حسابات المستخدمين والأدوار' : 'Create, edit and manage user accounts and roles'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowInviteModal(true)}
            className="bg-accent-500 hover:bg-accent-600 dark:bg-accent-600 dark:hover:bg-accent-700 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 font-medium transition-colors"
          >
            <UserPlus className="h-4 w-4" /> {t('inviteEmployee')}
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-riadah-500 hover:bg-riadah-600 dark:bg-riadah-700 dark:hover:bg-riadah-800 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 font-medium transition-colors"
          >
            <Plus className="h-4 w-4" /> {t('addNewUser')}
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800 text-white px-4 py-2.5 rounded-lg flex items-center gap-2 disabled:opacity-50 font-medium transition-colors"
          >
            {exporting ? (
              <><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg> {t('loading')}...</>
            ) : (
              <><Download className="h-4 w-4" /> Excel</>
            )}
          </button>
          <div className="flex items-center gap-2 bg-riadah-50 dark:bg-riadah-900/30 px-4 py-2 rounded-lg">
            <Users className="w-5 h-5 text-accent-500 dark:text-accent-400" />
            <span className="text-riadah-700 dark:text-accent-300 font-medium">
              {filteredUsers.length} {locale === 'ar' ? 'مستخدم' : 'Users'}
            </span>
          </div>
        </div>
      </div>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={locale === 'ar' ? 'بحث عن مستخدم...' : 'Search users...'}
          className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white dark:bg-gray-800"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-fit">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'users'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          {t('manageUsers')}
        </button>
        <button
          onClick={() => setActiveTab('invitations')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'invitations'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          {t('pendingInvitations')}
          {invitations.length > 0 && (
            <span className="mr-1.5 inline-flex items-center justify-center w-5 h-5 rounded-full bg-accent-500 text-white text-[10px]">
              {invitations.length}
            </span>
          )}
        </button>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {locale === 'ar' ? 'المستخدم' : 'User'}
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('userRole')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('status')}</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">2FA</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('date')}</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-riadah-100 dark:bg-riadah-900/40 flex items-center justify-center text-accent-500 dark:text-accent-400 font-bold text-sm">
                          {u.first_name?.[0] || u.username?.[0] || '?'}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">
                            {u.first_name || u.last_name
                              ? `${u.first_name || ''} ${u.last_name || ''}`.trim()
                              : u.username}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400" dir="ltr">{u.email || '-'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${getRoleBadgeColor(u.role)}`}>
                        <Shield className="w-3 h-3" />
                        {t(u.role) || u.role_display || u.role}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${u.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                        {u.is_active ? t('active') : t('inactive')}
                      </span>
                      {u.must_change_password && u.is_active && (
                        <span className="block mt-1 text-[10px] text-amber-600 dark:text-amber-400 flex items-center gap-0.5">
                          <Key className="w-2.5 h-2.5" /> {t('forceChangePass')}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-col gap-1">
                        <span className={`text-xs ${u.two_factor_enabled ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'} flex items-center gap-1`}>
                          {u.two_factor_enabled ? <ShieldCheck className="w-3 h-3" /> : <ShieldOff className="w-3 h-3" />}
                          2FA: {u.two_factor_enabled ? t('active') : t('inactive')}
                        </span>
                        {u.days_until_password_expiry !== undefined && u.days_until_password_expiry <= 14 && (
                          <span className="text-[10px] text-amber-600 dark:text-amber-400 flex items-center gap-0.5">
                            <AlertTriangle className="w-2.5 h-2.5" />
                            {u.days_until_password_expiry === 0 ? t('inactive') : `${u.days_until_password_expiry} ${t('days')}`}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString(locale === 'ar' ? 'ar-SA' : 'en-US') : '-'}
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => setSelectedUser(u)}
                          className="p-1.5 text-gray-400 dark:text-gray-500 hover:bg-riadah-50 dark:hover:bg-riadah-900/30 hover:text-accent-500 dark:hover:text-accent-400 rounded-lg transition-colors"
                          title={locale === 'ar' ? 'عرض التفاصيل' : 'View details'}
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => openEditModal(u)}
                          className="p-1.5 text-gray-400 dark:text-gray-500 hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg transition-colors"
                          title={locale === 'ar' ? 'تعديل المستخدم' : 'Edit user'}
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleToggleActive(u.id)}
                          className={`p-1.5 rounded-lg transition-colors ${
                            u.is_active
                              ? 'text-gray-400 dark:text-gray-500 hover:bg-red-50 dark:hover:bg-red-900/30 hover:text-red-600 dark:hover:text-red-400'
                              : 'text-gray-400 dark:text-gray-500 hover:bg-green-50 dark:hover:bg-green-900/30 hover:text-green-600 dark:hover:text-green-400'
                          }`}
                          title={u.is_active ? (locale === 'ar' ? 'تعطيل' : 'Deactivate') : (locale === 'ar' ? 'تفعيل' : 'Activate')}
                        >
                          {u.is_active ? <X className="w-4 h-4" /> : <Users className="w-4 h-4" />}
                        </button>
                        {u.two_factor_enabled && (
                          <button
                            onClick={() => handleReset2FA(u.id, u.username)}
                            className="p-1.5 text-gray-400 dark:text-gray-500 hover:bg-amber-50 dark:hover:bg-amber-900/30 hover:text-amber-600 dark:hover:text-amber-400 rounded-lg transition-colors"
                            title={t('reset2FA')}
                          >
                            <ShieldOff className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleForcePasswordChange(u.id, u.username)}
                          className="p-1.5 text-gray-400 dark:text-gray-500 hover:bg-purple-50 dark:hover:bg-purple-900/30 hover:text-purple-600 dark:hover:text-purple-400 rounded-lg transition-colors"
                          title={t('forceChangePass')}
                        >
                          <Lock className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-gray-400 dark:text-gray-500">
                      <UserCircle className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                      <p>{locale === 'ar' ? 'لا يوجد مستخدمين' : 'No users found'}</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Invitations Tab */}
      {activeTab === 'invitations' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loadingInvitations ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-accent-500" />
            </div>
          ) : invitations.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-400 dark:text-gray-500">
              <Mail className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
              <p>{t('noInvitations')}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700">
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('email')}</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('userRole')}</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('status')}</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('date')}</th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{locale === 'ar' ? 'تاريخ الانتهاء' : 'Expires'}</th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t('actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {invitations.map((inv) => (
                    <tr key={inv.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-accent-100 dark:bg-accent-900/30 flex items-center justify-center text-accent-500 dark:text-accent-400">
                            <Mail className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-800 dark:text-gray-200" dir="ltr">{inv.email}</p>
                            {(inv.first_name || inv.last_name) && (
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {`${inv.first_name || ''} ${inv.last_name || ''}`.trim()}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${getRoleBadgeColor(inv.role)}`}>
                          {t(inv.role) || inv.role_display || inv.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${getStatusBadge(inv.status)}`}>
                          {inv.status === 'pending' && <Clock className="w-3 h-3" />}
                          {inv.status_display || inv.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                        {inv.created_at ? new Date(inv.created_at).toLocaleDateString(locale === 'ar' ? 'ar-SA' : 'en-US') : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                        {inv.expires_at ? new Date(inv.expires_at).toLocaleDateString(locale === 'ar' ? 'ar-SA' : 'en-US') : '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {inv.status === 'pending' && (
                          <button
                            onClick={() => handleCancelInvitation(inv.id)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                          >
                            <X className="w-3 h-3" />
                            {t('cancelInvitation')}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowCreateModal(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {locale === 'ar' ? 'إنشاء حساب مستخدم جديد' : 'Create New User Account'}
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {locale === 'ar' ? 'اسم المستخدم' : 'Username'} *
                  </label>
                  <input type="text" value={createForm.username} onChange={(e) => setCreateForm({...createForm, username: e.target.value})} required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('email')}</label>
                  <input type="email" value={createForm.email} onChange={(e) => setCreateForm({...createForm, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" dir="ltr" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {locale === 'ar' ? 'الاسم الأول' : 'First Name'}
                  </label>
                  <input type="text" value={createForm.first_name} onChange={(e) => setCreateForm({...createForm, first_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {locale === 'ar' ? 'الاسم الأخير' : 'Last Name'}
                  </label>
                  <input type="text" value={createForm.last_name} onChange={(e) => setCreateForm({...createForm, last_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('userRole')} *</label>
                <select value={createForm.role} onChange={(e) => setCreateForm({...createForm, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm">
                  {Object.entries(ROLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{t(label)}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {locale === 'ar' ? 'رقم الهاتف' : 'Phone'}
                </label>
                <input type="tel" value={createForm.phone} onChange={(e) => setCreateForm({...createForm, phone: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" dir="ltr" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('newPassword')} *</label>
                <div className="relative">
                  <input type={showCreatePassword ? 'text' : 'password'} value={createForm.password}
                    onChange={(e) => setCreateForm({...createForm, password: e.target.value})} required minLength={8}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm pl-10" />
                  <button type="button" onClick={() => setShowCreatePassword(!showCreatePassword)}
                    className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500">
                    {showCreatePassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('confirmPassword')} *</label>
                <input type="password" value={createForm.password_confirm}
                  onChange={(e) => setCreateForm({...createForm, password_confirm: e.target.value})} required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" />
              </div>

              <div className="flex items-center gap-2">
                <input type="checkbox" id="mustChange" checked={createForm.must_change_password}
                  onChange={(e) => setCreateForm({...createForm, must_change_password: e.target.checked})}
                  className="rounded border-gray-300 dark:border-gray-600 text-accent-500 dark:bg-gray-700" />
                <label htmlFor="mustChange" className="text-sm text-gray-600 dark:text-gray-400">{t('forceChangePass')}</label>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={createLoading}
                  className="flex-1 bg-riadah-500 hover:bg-riadah-600 dark:bg-riadah-700 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2">
                  {createLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}...</> : <><Save className="w-4 h-4" /> {t('add')}</>}
                </button>
                <button type="button" onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Invite Employee Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => { setShowInviteModal(false); setInviteLink(''); }} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-accent-500" />
                {t('inviteEmployeeTitle')}
              </h3>
              <button onClick={() => { setShowInviteModal(false); setInviteLink(''); }} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-sm text-gray-500 dark:text-gray-400 mb-5">
              {t('inviteEmployeeDesc')}
            </p>

            <form onSubmit={handleInviteEmployee} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('email')} *
                </label>
                <input
                  type="email"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({...inviteForm, email: e.target.value})}
                  required
                  dir="ltr"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('firstName')}
                  </label>
                  <input
                    type="text"
                    value={inviteForm.first_name}
                    onChange={(e) => setInviteForm({...inviteForm, first_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('lastName')}
                  </label>
                  <input
                    type="text"
                    value={inviteForm.last_name}
                    onChange={(e) => setInviteForm({...inviteForm, last_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('userRole')} *</label>
                <select
                  value={inviteForm.role}
                  onChange={(e) => setInviteForm({...inviteForm, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm"
                >
                  {Object.entries(ROLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{t(label)}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('phone')}
                </label>
                <input
                  type="tel"
                  value={inviteForm.phone}
                  onChange={(e) => setInviteForm({...inviteForm, phone: e.target.value})}
                  dir="ltr"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm"
                />
              </div>

              {/* Invite link display */}
              {inviteLink && (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-green-700 dark:text-green-400">
                      {t('inviteLink')}
                    </p>
                    <button
                      type="button"
                      onClick={copyInviteLink}
                      className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300 font-medium"
                    >
                      <Copy className="w-3 h-3" />
                      {t('copy')}
                    </button>
                  </div>
                  <textarea
                    readOnly
                    value={inviteLink}
                    dir="ltr"
                    className="w-full text-xs px-2 py-1.5 bg-white dark:bg-gray-700 border border-green-200 dark:border-green-700 rounded text-gray-600 dark:text-gray-300 resize-none"
                    rows={2}
                    onClick={(e) => e.target.select()}
                  />
                  <p className="text-[10px] text-green-600 dark:text-green-400">
                    {t('inviteLinkHint')}
                  </p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={inviteLoading}
                  className="flex-1 bg-accent-500 hover:bg-accent-600 dark:bg-accent-600 dark:hover:bg-accent-700 disabled:bg-accent-300 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {inviteLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}...</>
                  ) : (
                    <><UserPlus className="w-4 h-4" /> {t('inviteButton')}</>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowInviteModal(false); setInviteLink(''); }}
                  className="px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && editUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => { setShowEditModal(false); setEditUser(null); }} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Edit3 className="w-5 h-5 text-accent-500" />
                {locale === 'ar' ? 'تعديل حساب المستخدم' : 'Edit User Account'}
              </h3>
              <button onClick={() => { setShowEditModal(false); setEditUser(null); }} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* User info header */}
            <div className="flex items-center gap-3 mb-5 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
              <div className="w-12 h-12 rounded-full bg-riadah-100 dark:bg-riadah-900/40 flex items-center justify-center text-accent-500 dark:text-accent-400 font-bold">
                {editUser.first_name?.[0] || editUser.username?.[0] || '?'}
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">@{editUser.username}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{t('userRole')}: {t(editUser.role) || editUser.role}</p>
              </div>
            </div>

            <form onSubmit={handleUpdateUser} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {locale === 'ar' ? 'الاسم الأول' : 'First Name'}
                  </label>
                  <input type="text" value={editForm.first_name} onChange={(e) => setEditForm({...editForm, first_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {locale === 'ar' ? 'الاسم الأخير' : 'Last Name'}
                  </label>
                  <input type="text" value={editForm.last_name} onChange={(e) => setEditForm({...editForm, last_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('email')}</label>
                <input type="email" value={editForm.email} onChange={(e) => setEditForm({...editForm, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" dir="ltr" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {locale === 'ar' ? 'رقم الهاتف' : 'Phone'}
                </label>
                <input type="tel" value={editForm.phone} onChange={(e) => setEditForm({...editForm, phone: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm" dir="ltr" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('userRole')} *</label>
                <select value={editForm.role} onChange={(e) => setEditForm({...editForm, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-sm">
                  {Object.entries(ROLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{t(label)}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-600">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('status')}:</span>
                <button
                  type="button"
                  onClick={() => setEditForm({...editForm, is_active: !editForm.is_active})}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${editForm.is_active ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${editForm.is_active ? 'translate-x-6' : 'translate-x-1'}`} />
                </button>
                <span className={`text-sm font-medium ${editForm.is_active ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {editForm.is_active ? t('active') : t('inactive')}
                </span>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={editLoading}
                  className="flex-1 bg-riadah-500 hover:bg-riadah-600 dark:bg-riadah-700 dark:hover:bg-riadah-800 disabled:bg-accent-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2">
                  {editLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> {t('loading')}...</> : <><Save className="w-4 h-4" /> {t('savePermissions')}</>}
                </button>
                <button type="button" onClick={() => { setShowEditModal(false); setEditUser(null); }}
                  className="px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* User Detail Modal */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => setSelectedUser(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {locale === 'ar' ? 'تفاصيل المستخدم' : 'User Details'}
              </h3>
              <button onClick={() => setSelectedUser(null)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-center mb-6">
              <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-riadah-100 dark:bg-riadah-900/40 flex items-center justify-center text-2xl font-bold text-accent-500 dark:text-accent-400">
                {selectedUser.first_name?.[0] || selectedUser.username?.[0] || '?'}
              </div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{selectedUser.first_name} {selectedUser.last_name}</h4>
              <p className="text-gray-500 dark:text-gray-400">@{selectedUser.username}</p>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm text-gray-500 dark:text-gray-400">{t('email')}</span>
                <span className="text-sm text-gray-800 dark:text-gray-200" dir="ltr">{selectedUser.email || '-'}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm text-gray-500 dark:text-gray-400">{locale === 'ar' ? 'الهاتف' : 'Phone'}</span>
                <span className="text-sm text-gray-800 dark:text-gray-200" dir="ltr">{selectedUser.phone || '-'}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm text-gray-500 dark:text-gray-400">{t('userRole')}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getRoleBadgeColor(selectedUser.role)}`}>
                  {t(selectedUser.role) || selectedUser.role_display || selectedUser.role}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm text-gray-500 dark:text-gray-400">{t('status')}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${selectedUser.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                  {selectedUser.is_active ? t('active') : t('inactive')}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm text-gray-500 dark:text-gray-400">2FA</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${selectedUser.two_factor_enabled ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}`}>
                  {selectedUser.two_factor_enabled ? t('active') : t('inactive')}
                </span>
              </div>
              {selectedUser.days_until_password_expiry !== undefined && (
                <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                  <span className="text-sm text-gray-500 dark:text-gray-400">{locale === 'ar' ? 'انتهاء كلمة المرور' : 'Password Expiry'}</span>
                  <span className={`text-xs font-medium ${selectedUser.days_until_password_expiry <= 14 ? 'text-amber-600 dark:text-amber-400' : 'text-gray-600 dark:text-gray-400'}`}>
                    {selectedUser.days_until_password_expiry === 0 ? t('inactive') : `${selectedUser.days_until_password_expiry} ${t('days')}`}
                  </span>
                </div>
              )}
              <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
                <span className="text-sm text-gray-500 dark:text-gray-400">IP</span>
                <span className="text-xs text-gray-600 dark:text-gray-400 font-mono" dir="ltr">{selectedUser.last_login_ip || '-'}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-sm text-gray-500 dark:text-gray-400">{t('date')}</span>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedUser.created_at ? new Date(selectedUser.created_at).toLocaleDateString(locale === 'ar' ? 'ar-SA' : 'en-US') : '-'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
