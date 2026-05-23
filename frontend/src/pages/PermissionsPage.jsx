/**
 * Permissions Management page - admin only.
 * Allows viewing and managing granular permissions for each role.
 */

import { useState, useEffect, useCallback } from 'react';
import { permissionsAPI } from '../api';
import {
  Shield, Loader2, Save, RefreshCw, Check, X, Search,
  Lock, Unlock, Eye, Plus, Minus, Settings, Users,
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

const MODULE_LABELS = {
  dashboard: 'dashboard',
  inventory: 'inventory',
  sales: 'sales',
  purchases: 'purchases',
  accounting: 'accounting',
  hr: 'hr',
  documents: 'documents',
  projects: 'projects',
  notifications: 'notifications',
  auditlog: 'auditLogTitle',
  users: 'manageUsers',
  reports: 'reportsCenterTitle',
  backup: 'backup',
  permissions: 'permissionsTitle',
};

const ACTION_LABELS = {
  view: 'search',
  create: 'createAction',
  edit: 'edit',
  delete: 'delete',
  export: 'download',
  approve: 'confirm',
  manage: 'manageUsers',
};

const ACTION_COLORS = {
  view: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-400',
  create: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  edit: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  delete: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  export: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  approve: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
  manage: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
};

export default function PermissionsPage() {
  const { t } = useI18n();

  const [permissions, setPermissions] = useState([]);
  const [roles, setRoles] = useState({});
  const [selectedRole, setSelectedRole] = useState('admin');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [localRolePerms, setLocalRolePerms] = useState({});
  const [moduleFilter, setModuleFilter] = useState('');
  const [seedLoading, setSeedLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await permissionsAPI.allRoles();
      setPermissions(response.data.permissions || []);
      setRoles(response.data.roles || {});

      // Initialize local state
      const localPerms = {};
      Object.entries(response.data.roles || {}).forEach(([role, data]) => {
        localPerms[role] = new Set(data.permissions || []);
      });
      setLocalRolePerms(localPerms);
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const togglePermission = (permissionId) => {
    setHasChanges(true);
    setLocalRolePerms(prev => {
      const newPerms = { ...prev };
      const current = new Set(newPerms[selectedRole] || []);
      if (current.has(permissionId)) {
        current.delete(permissionId);
      } else {
        current.add(permissionId);
      }
      newPerms[selectedRole] = current;
      return newPerms;
    });
  };

  const toggleAllModule = (module) => {
    setHasChanges(true);
    const modulePerms = permissions.filter(p => p.module === module).map(p => p.id);
    setLocalRolePerms(prev => {
      const newPerms = { ...prev };
      const current = new Set(newPerms[selectedRole] || []);
      const allSelected = modulePerms.every(id => current.has(id));
      if (allSelected) {
        modulePerms.forEach(id => current.delete(id));
      } else {
        modulePerms.forEach(id => current.add(id));
      }
      newPerms[selectedRole] = current;
      return newPerms;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const permIds = Array.from(localRolePerms[selectedRole] || []);
      await permissionsAPI.updateRole(selectedRole, permIds);
      setHasChanges(false);
      toast.success(t('permissionsUpdated'));
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setSaving(false);
    }
  };

  const handleSeed = async () => {
    setSeedLoading(true);
    try {
      await permissionsAPI.seed();
      toast.success(t('seedPermissions'));
      fetchData();
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setSeedLoading(false);
    }
  };

  const handleRoleChange = (role) => {
    setSelectedRole(role);
    setHasChanges(false);
    setModuleFilter('');
  };

  // Group permissions by module
  const groupedPerms = {};
  permissions.forEach(p => {
    if (!groupedPerms[p.module]) {
      groupedPerms[p.module] = [];
    }
    groupedPerms[p.module].push(p);
  });

  const currentPermSet = localRolePerms[selectedRole] || new Set();
  const filteredModules = moduleFilter
    ? { [moduleFilter]: groupedPerms[moduleFilter] || [] }
    : groupedPerms;

  const getModuleStats = (module) => {
    const modulePermIds = (groupedPerms[module] || []).map(p => p.id);
    const assigned = modulePermIds.filter(id => currentPermSet.has(id)).length;
    return { assigned, total: modulePermIds.length };
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('permissionsTitle')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('permissionsDesc')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSeed}
            disabled={seedLoading}
            className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium px-4 py-2.5 rounded-lg transition-colors"
          >
            {seedLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            {t('seedPermissions')}
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !hasChanges}
            className={`flex items-center gap-2 font-medium px-4 py-2.5 rounded-lg transition-colors ${
              hasChanges
                ? 'bg-riadah-500 hover:bg-riadah-600 dark:bg-riadah-700 dark:hover:bg-riadah-800 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
            }`}
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {hasChanges ? t('savePermissions') : t('noData')}
          </button>
        </div>
      </div>

      {hasChanges && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
          <Settings className="w-4 h-4" />
          {t('savePermissions')}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Role selection sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
              <Users className="w-4 h-4" /> {t('roles')}
            </h3>
            <div className="space-y-1">
              {Object.entries(ROLE_LABELS).map(([role, label]) => (
                <button
                  key={role}
                  onClick={() => handleRoleChange(role)}
                  className={`w-full text-right px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedRole === role
                      ? 'bg-riadah-50 dark:bg-riadah-900/30 text-riadah-700 dark:text-accent-400 border border-riadah-200 dark:border-riadah-800'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 border border-transparent'
                  }`}
                >
                  {t(label)}
                </button>
              ))}
            </div>

            {/* Role stats */}
            <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('assignPermission')}</div>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-accent-500 dark:text-accent-400">
                  {currentPermSet.size}
                </span>
                <span className="text-sm text-gray-400 dark:text-gray-500">
                  / {permissions.length}
                </span>
              </div>
              <div className="mt-2 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-riadah-500 dark:bg-riadah-500 rounded-full transition-all duration-300"
                  style={{ width: `${permissions.length ? (currentPermSet.size / permissions.length) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>

          {/* Module filter */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 mt-4">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
              <Search className="w-4 h-4" /> {t('module')}
            </h3>
            <div className="space-y-1">
              <button
                onClick={() => setModuleFilter('')}
                className={`w-full text-right px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                  !moduleFilter ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                {t('module')}
              </button>
              {Object.entries(MODULE_LABELS).map(([module, label]) => {
                const stats = getModuleStats(module);
                return (
                  <button
                    key={module}
                    onClick={() => setModuleFilter(module === moduleFilter ? '' : module)}
                    className={`w-full text-right px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                      moduleFilter === module ? 'bg-riadah-50 dark:bg-riadah-900/30 text-riadah-700 dark:text-accent-400' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <span>{t(label)}</span>
                    <span className="text-[10px] bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                      {stats.assigned}/{stats.total}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Permissions grid */}
        <div className="lg:col-span-3">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/70">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                {t('permissionsList')}: {t(ROLE_LABELS[selectedRole])}
              </h3>
            </div>

            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {Object.entries(filteredModules).map(([module, perms]) => {
                const stats = getModuleStats(module);
                const allSelected = stats.assigned === stats.total && stats.total > 0;

                return (
                  <div key={module} className="px-4 py-4">
                    {/* Module header */}
                    <div className="flex items-center justify-between mb-3">
                      <button
                        onClick={() => toggleAllModule(module)}
                        className="flex items-center gap-2 text-sm font-semibold text-gray-800 dark:text-gray-200 hover:text-accent-500 dark:hover:text-accent-400 transition-colors"
                      >
                        {allSelected ? (
                          <Unlock className="w-4 h-4 text-green-500 dark:text-green-400" />
                        ) : (
                          <Lock className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                        )}
                        {t(MODULE_LABELS[module]) || module}
                      </button>
                      <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-1 rounded-full">
                        {stats.assigned}/{stats.total}
                      </span>
                    </div>

                    {/* Permission checkboxes */}
                    <div className="flex flex-wrap gap-2">
                      {perms.map(perm => {
                        const isChecked = currentPermSet.has(perm.id);
                        return (
                          <button
                            key={perm.id}
                            onClick={() => togglePermission(perm.id)}
                            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                              isChecked
                                ? `${ACTION_COLORS[perm.action] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'} border-transparent shadow-sm`
                                : 'bg-gray-50 dark:bg-gray-700 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                            }`}
                            title={`${t(MODULE_LABELS[perm.module])} - ${t(ACTION_LABELS[perm.action])}`}
                          >
                            {isChecked ? (
                              <Check className="w-3 h-3" />
                            ) : (
                              <Plus className="w-3 h-3" />
                            )}
                            {t(ACTION_LABELS[perm.action]) || perm.action}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {Object.keys(filteredModules).length === 0 && (
              <div className="text-center py-12 text-gray-400 dark:text-gray-500">
                <Eye className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                <p>{t('noData')}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
