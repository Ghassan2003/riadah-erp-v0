/**
 * Cost Allocation page - manages cost centers and allocation rules.
 * Two tabs: Cost Centers and Allocation Rules.
 * Supports dark mode and i18n (RTL Arabic/English).
 */

import { useState, useEffect, useCallback } from 'react';
import { costAllocationAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import {
  Plus, X, Target, Settings2, Play, AlertTriangle,
  Trash2, Edit2, History,
} from 'lucide-react';

export default function CostAllocationPage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const isAccountant = user?.role === 'admin' || user?.role === 'accountant';

  const RULE_TYPE_LABELS = {
    percentage: 'نسبة مئوية',
    equal: 'تساوي',
    manual: 'يدوي',
    ratio: 'نسبة',
  };

  const RULE_STATUS_COLORS = {
    active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    inactive: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
    draft: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  };

  const RULE_STATUS_LABELS = {
    active: 'نشط',
    inactive: 'غير نشط',
    draft: 'مسودة',
  };

  /* ── state ── */
  const [activeTab, setActiveTab] = useState('centers');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  /* cost centers */
  const [costCenters, setCostCenters] = useState([]);
  const [showCenterModal, setShowCenterModal] = useState(false);
  const [editingCenter, setEditingCenter] = useState(null);
  const [centerForm, setCenterForm] = useState({ code: '', name: '', budget: '', description: '' });

  /* allocation rules */
  const [rules, setRules] = useState([]);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [ruleForm, setRuleForm] = useState({
    name: '', allocation_type: 'percentage', source_account: '',
    description: '',
  });

  /* allocation logs */
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  /* confirm dialog */
  const [confirmAction, setConfirmAction] = useState(null);

  // ──────────────────────── Data Fetching ────────────────────────

  const fetchCostCenters = useCallback(async () => {
    setLoading(true);
    try {
      const res = await costAllocationAPI.getCostCenters();
      setCostCenters(res.data.results || res.data);
    } catch {
      toast.error('خطأ في تحميل مراكز التكلفة');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRules = useCallback(async () => {
    setLoading(true);
    try {
      const res = await costAllocationAPI.getRules();
      setRules(res.data.results || res.data);
    } catch {
      toast.error('خطأ في تحميل قواعد التوزيع');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    setLoadingLogs(true);
    try {
      const res = await costAllocationAPI.getLogs();
      setLogs(res.data.results || res.data);
    } catch {
      toast.error('خطأ في تحميل سجل التوزيع');
    } finally {
      setLoadingLogs(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'centers') fetchCostCenters();
    else fetchRules();
  }, [activeTab, fetchCostCenters, fetchRules]);

  // ──────────────────────── Cost Center CRUD ────────────────────────

  const openCreateCenter = () => {
    setEditingCenter(null);
    setCenterForm({ code: '', name: '', budget: '', description: '' });
    setShowCenterModal(true);
  };

  const openEditCenter = (center) => {
    setEditingCenter(center);
    setCenterForm({
      code: center.code || '',
      name: center.name || '',
      budget: String(center.budget || ''),
      description: center.description || '',
    });
    setShowCenterModal(true);
  };

  const handleSaveCenter = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = { ...centerForm, budget: parseFloat(centerForm.budget) || 0 };
      if (editingCenter) {
        await costAllocationAPI.updateCostCenter(editingCenter.id, data);
        toast.success('تم تحديث مركز التكلفة بنجاح');
      } else {
        await costAllocationAPI.createCostCenter(data);
        toast.success('تم إنشاء مركز التكلفة بنجاح');
      }
      setShowCenterModal(false);
      fetchCostCenters();
    } catch (err) {
      const msg = err.response?.data?.code?.[0] || err.response?.data?.error || 'خطأ في حفظ مركز التكلفة';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCenter = async () => {
    if (!confirmAction?.id) return;
    try {
      await costAllocationAPI.deleteCostCenter(confirmAction.id);
      toast.success('تم حذف مركز التكلفة بنجاح');
      fetchCostCenters();
    } catch {
      toast.error('خطأ في حذف مركز التكلفة');
    } finally {
      setConfirmAction(null);
    }
  };

  // ──────────────────────── Allocation Rule CRUD ────────────────────────

  const openCreateRule = () => {
    setEditingRule(null);
    setRuleForm({ name: '', allocation_type: 'percentage', source_account: '', description: '' });
    setShowRuleModal(true);
  };

  const openEditRule = (rule) => {
    setEditingRule(rule);
    setRuleForm({
      name: rule.name || '',
      allocation_type: rule.allocation_type || 'percentage',
      source_account: rule.source_account || '',
      description: rule.description || '',
    });
    setShowRuleModal(true);
  };

  const handleSaveRule = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingRule) {
        await costAllocationAPI.updateRule(editingRule.id, ruleForm);
        toast.success('تم تحديث قاعدة التوزيع بنجاح');
      } else {
        await costAllocationAPI.createRule(ruleForm);
        toast.success('تم إنشاء قاعدة التوزيع بنجاح');
      }
      setShowRuleModal(false);
      fetchRules();
    } catch (err) {
      const msg = err.response?.data?.error || 'خطأ في حفظ قاعدة التوزيع';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteRule = async () => {
    if (!confirmAction?.id) return;
    try {
      await costAllocationAPI.deleteRule(confirmAction.id);
      toast.success('تم حذف قاعدة التوزيع بنجاح');
      fetchRules();
    } catch {
      toast.error('خطأ في حذف قاعدة التوزيع');
    } finally {
      setConfirmAction(null);
    }
  };

  const handleExecuteRule = async (rule) => {
    try {
      await costAllocationAPI.executeRule(rule.id);
      toast.success(`تم تنفيذ قاعدة "${rule.name}" بنجاح`);
      fetchRules();
    } catch {
      toast.error('خطأ في تنفيذ قاعدة التوزيع');
    }
  };

  // ──────────────────────── Helpers ────────────────────────

  const formatAmount = (val) =>
    Number(val || 0).toLocaleString('ar-SA', { minimumFractionDigits: 2 });

  const getUtilizationColor = (ratio) => {
    if (ratio >= 100) return 'bg-red-500';
    if (ratio >= 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  // ──────────────────────── Render ────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            توزيع التكاليف
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            إدارة مراكز التكلفة وقواعد التوزيع
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setShowLogs(true);
              fetchLogs();
            }}
            className="flex items-center gap-2 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            <History className="w-4 h-4" />
            سجل التوزيع
          </button>
          <button
            onClick={activeTab === 'centers' ? openCreateCenter : openCreateRule}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors shadow-sm"
          >
            <Plus className="w-5 h-5" />
            {activeTab === 'centers' ? 'إضافة مركز تكلفة' : 'إضافة قاعدة توزيع'}
          </button>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
        <button
          onClick={() => setActiveTab('centers')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'centers'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Target className="w-4 h-4" />
          مراكز التكلفة
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'rules'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Settings2 className="w-4 h-4" />
          قواعد التوزيع
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Cost Centers Tab
         ═══════════════════════════════════════════════════════════ */}
      {activeTab === 'centers' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-400 dark:text-gray-500">جاري التحميل...</div>
          ) : costCenters.length === 0 ? (
            <div className="p-12 text-center">
              <Target className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">لا توجد مراكز تكلفة</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">أضف مركز تكلفة جديد للبدء</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                    <th className="px-4 py-3 text-right font-medium">الرمز</th>
                    <th className="px-4 py-3 text-right font-medium">الاسم</th>
                    <th className="px-4 py-3 text-right font-medium">الميزانية</th>
                    <th className="px-4 py-3 text-right font-medium">الفعلي</th>
                    <th className="px-4 py-3 text-right font-medium">الاستخدام</th>
                    <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {costCenters.map((center) => {
                    const budget = center.budget || 0;
                    const actual = center.actual_amount || 0;
                    const utilization = budget > 0 ? Math.round((actual / budget) * 100) : 0;
                    const clampedUtilization = Math.min(utilization, 100);

                    return (
                      <tr
                        key={center.id}
                        className="border-b border-gray-50 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                      >
                        <td className="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">
                          {center.code}
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                          {center.name}
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100" dir="ltr">
                          {formatAmount(budget)}
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100" dir="ltr">
                          {formatAmount(actual)}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full transition-all duration-300 ${getUtilizationColor(utilization)}`}
                                style={{ width: `${clampedUtilization}%` }}
                              />
                            </div>
                            <span
                              className={`text-xs font-medium min-w-[36px] ${
                                utilization >= 100
                                  ? 'text-red-600 dark:text-red-400'
                                  : utilization >= 80
                                  ? 'text-yellow-600 dark:text-yellow-400'
                                  : 'text-green-600 dark:text-green-400'
                              }`}
                            >
                              {utilization}%
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => openEditCenter(center)}
                              className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/30 transition-colors"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() =>
                                setConfirmAction({ type: 'center', id: center.id, name: center.name })
                              }
                              className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Allocation Rules Tab
         ═══════════════════════════════════════════════════════════ */}
      {activeTab === 'rules' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-400 dark:text-gray-500">جاري التحميل...</div>
          ) : rules.length === 0 ? (
            <div className="p-12 text-center">
              <Settings2 className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">لا توجد قواعد توزيع</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">أضف قاعدة توزيع جديدة للبدء</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                    <th className="px-4 py-3 text-right font-medium">الاسم</th>
                    <th className="px-4 py-3 text-right font-medium">النوع</th>
                    <th className="px-4 py-3 text-right font-medium">الحساب المصدر</th>
                    <th className="px-4 py-3 text-right font-medium">الحالة</th>
                    <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((rule) => (
                    <tr
                      key={rule.id}
                      className="border-b border-gray-50 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                        {rule.name}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2.5 py-1 bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-riadah-400 rounded-full text-xs font-medium">
                          {RULE_TYPE_LABELS[rule.allocation_type] || rule.allocation_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-600 dark:text-gray-400">
                        {rule.source_account || '—'}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                            RULE_STATUS_COLORS[rule.status] || RULE_STATUS_COLORS.draft
                          }`}
                        >
                          {RULE_STATUS_LABELS[rule.status] || rule.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {rule.status === 'active' && (
                            <button
                              onClick={() => handleExecuteRule(rule)}
                              className="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 p-1.5 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                              title="تنفيذ القاعدة"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => openEditRule(rule)}
                            className="text-accent-500 dark:text-accent-400 hover:text-riadah-800 dark:hover:text-accent-300 p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/30 transition-colors"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() =>
                              setConfirmAction({ type: 'rule', id: rule.id, name: rule.name })
                            }
                            className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Create / Edit Cost Center Modal
         ═══════════════════════════════════════════════════════════ */}
      {showCenterModal && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setShowCenterModal(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingCenter ? 'تعديل مركز التكلفة' : 'إضافة مركز تكلفة جديد'}
              </h3>
              <button
                onClick={() => setShowCenterModal(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSaveCenter} className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    الرمز *
                  </label>
                  <input
                    type="text"
                    value={centerForm.code}
                    onChange={(e) => setCenterForm({ ...centerForm, code: e.target.value })}
                    placeholder="مثال: CC-001"
                    disabled={!!editingCenter}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none disabled:bg-gray-50 dark:disabled:bg-gray-700 disabled:text-gray-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    الميزانية *
                  </label>
                  <input
                    type="number"
                    value={centerForm.budget}
                    onChange={(e) => setCenterForm({ ...centerForm, budget: e.target.value })}
                    placeholder="0.00"
                    dir="ltr"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  اسم مركز التكلفة *
                </label>
                <input
                  type="text"
                  value={centerForm.name}
                  onChange={(e) => setCenterForm({ ...centerForm, name: e.target.value })}
                  placeholder="اسم مركز التكلفة"
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  الوصف
                </label>
                <textarea
                  value={centerForm.description}
                  onChange={(e) => setCenterForm({ ...centerForm, description: e.target.value })}
                  placeholder="وصف مركز التكلفة"
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none resize-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50 font-medium"
                >
                  {saving ? 'جاري الحفظ...' : editingCenter ? 'حفظ التعديلات' : 'إنشاء'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCenterModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Create / Edit Allocation Rule Modal
         ═══════════════════════════════════════════════════════════ */}
      {showRuleModal && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setShowRuleModal(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editingRule ? 'تعديل قاعدة التوزيع' : 'إضافة قاعدة توزيع جديدة'}
              </h3>
              <button
                onClick={() => setShowRuleModal(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSaveRule} className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  اسم القاعدة *
                </label>
                <input
                  type="text"
                  value={ruleForm.name}
                  onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
                  placeholder="اسم قاعدة التوزيع"
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    نوع التوزيع *
                  </label>
                  <select
                    value={ruleForm.allocation_type}
                    onChange={(e) => setRuleForm({ ...ruleForm, allocation_type: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none bg-white dark:bg-gray-700"
                  >
                    {Object.entries(RULE_TYPE_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    الحساب المصدر
                  </label>
                  <input
                    type="text"
                    value={ruleForm.source_account}
                    onChange={(e) => setRuleForm({ ...ruleForm, source_account: e.target.value })}
                    placeholder="رمز الحساب"
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none"
                    dir="ltr"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  الوصف
                </label>
                <textarea
                  value={ruleForm.description}
                  onChange={(e) => setRuleForm({ ...ruleForm, description: e.target.value })}
                  placeholder="وصف قاعدة التوزيع"
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none resize-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-riadah-500 dark:bg-riadah-700 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 transition-colors disabled:opacity-50 font-medium"
                >
                  {saving ? 'جاري الحفظ...' : editingRule ? 'حفظ التعديلات' : 'إنشاء'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowRuleModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Allocation Logs Modal
         ═══════════════════════════════════════════════════════════ */}
      {showLogs && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setShowLogs(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <History className="w-5 h-5 text-riadah-500" />
                سجل التوزيع
              </h3>
              <button
                onClick={() => setShowLogs(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="overflow-y-auto max-h-[60vh]">
              {loadingLogs ? (
                <div className="p-12 text-center text-gray-400 dark:text-gray-500">
                  جاري التحميل...
                </div>
              ) : logs.length === 0 ? (
                <div className="p-12 text-center">
                  <History className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-500 dark:text-gray-400">لا يوجد سجل توزيع</p>
                </div>
              ) : (
                <div className="divide-y dark:divide-gray-700">
                  {logs.map((log, idx) => (
                    <div key={idx} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                            {log.rule_name || log.name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {log.executed_by || log.user} — {log.created_at || log.date}
                          </p>
                        </div>
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                            log.status === 'success'
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          }`}
                        >
                          {log.status === 'success' ? 'نجح' : 'فشل'}
                        </span>
                      </div>
                      {log.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                          {log.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          Delete Confirmation Dialog
         ═══════════════════════════════════════════════════════════ */}
      {confirmAction && (
        <div
          className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-[60] p-4"
          onClick={() => setConfirmAction(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 text-center">
              <div className="mx-auto w-14 h-14 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-4">
                <AlertTriangle className="w-7 h-7 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                تأكيد الحذف
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                هل أنت متأكد من حذف{' '}
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  {confirmAction.name}
                </span>؟
              </p>
              <p className="text-xs text-red-500 dark:text-red-400 mt-2">
                هذا الإجراء لا يمكن التراجع عنه
              </p>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setConfirmAction(null)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  إلغاء
                </button>
                <button
                  onClick={() => {
                    if (confirmAction.type === 'center') handleDeleteCenter();
                    else handleDeleteRule();
                  }}
                  className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
                >
                  حذف
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
