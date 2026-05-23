/**
 * Performance Review Management page - HR module.
 * Full CRUD for employee performance reviews with star rating system.
 * Supports dark mode, i18n (Arabic-first RTL), and role-based access.
 */

import { useState, useEffect } from 'react';
import { performanceReviewsAPI, employeesAPI } from '../api';
import toast from 'react-hot-toast';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import { Search, Plus, X, Edit2, Eye, Star, Award, ClipboardList, TrendingUp } from 'lucide-react';

// ──────────────────────────────────────────────
// Constants
// ──────────────────────────────────────────────

const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  self_review: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  manager_review: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

const REVIEW_PERIOD_MAP = {
  quarterly: 'quarterly',
  semi_annual: 'semiAnnual',
  annual: 'annual',
};

const STATUS_MAP = {
  draft: 'draft',
  self_review: 'selfReview',
  manager_review: 'managerReview',
  completed: 'completed',
  cancelled: 'cancelled',
};

const RATING_CRITERIA = [
  { key: 'goals_rating', labelKey: 'goalsRating' },
  { key: 'competencies_rating', labelKey: 'competenciesRating' },
  { key: 'teamwork_rating', labelKey: 'teamworkRating' },
  { key: 'communication_rating', labelKey: 'communicationRating' },
  { key: 'initiative_rating', labelKey: 'initiativeRating' },
];

const EMPTY_FORM = {
  employee: '',
  reviewer: '',
  review_period: 'quarterly',
  year: new Date().getFullYear(),
  quarter: 1,
  goals_rating: 0,
  competencies_rating: 0,
  teamwork_rating: 0,
  communication_rating: 0,
  initiative_rating: 0,
  strengths: '',
  areas_for_improvement: '',
  goals_for_next_period: '',
  status: 'draft',
};

// ──────────────────────────────────────────────
// Helper: rating color class
// ──────────────────────────────────────────────

function ratingColorClass(value) {
  if (value >= 4) return 'text-green-500';
  if (value === 3) return 'text-yellow-500';
  return 'text-red-500';
}

function ratingBgClass(value) {
  if (value >= 4) return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
  if (value === 3) return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
  return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
}

function ratingLabel(t, value) {
  if (value >= 5) return t('excellent');
  if (value >= 4) return t('good');
  if (value === 3) return t('satisfactory');
  if (value >= 2) return t('needsImprovement');
  return t('poor');
}

// ──────────────────────────────────────────────
// Star Rating Components
// ──────────────────────────────────────────────

/** Static star display (read-only) */
function StarDisplay({ value, size = 'md', showLabel = true, t }) {
  const iconSize = size === 'lg' ? 'w-6 h-6' : size === 'sm' ? 'w-3.5 h-3.5' : 'w-4.5 h-4.5';
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          className={`${iconSize} ${
            star <= value
              ? 'fill-yellow-400 text-yellow-400'
              : 'fill-transparent text-gray-300 dark:text-gray-600'
          }`}
        />
      ))}
      {showLabel && value > 0 && (
        <span className={`ms-1.5 text-sm font-semibold ${ratingColorClass(value)}`}>
          {value}/5
        </span>
      )}
    </div>
  );
}

/** Interactive star rating input */
function StarRatingInput({ value, onChange, size = 'md' }) {
  const iconSize = size === 'lg' ? 'w-7 h-7' : 'w-5 h-5';
  const [hovered, setHovered] = useState(0);

  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => onChange(star === value ? 0 : star)}
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(0)}
          className="transition-transform hover:scale-110 focus:outline-none"
        >
          <Star
            className={`${iconSize} ${
              star <= (hovered || value)
                ? 'fill-yellow-400 text-yellow-400'
                : 'fill-transparent text-gray-300 dark:text-gray-600'
            } transition-colors`}
          />
        </button>
      ))}
      {value > 0 && (
        <span className={`ms-2 text-sm font-semibold ${ratingColorClass(value)}`}>
          {value}/5
        </span>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────
// Main Component
// ──────────────────────────────────────────────

export default function PerformancePage() {
  const { t } = useI18n();
  const { isHR } = useAuth();
  const canManage = isHR;

  // ── Data State ──
  const [reviews, setReviews] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);

  // ── Filter State ──
  const [searchQuery, setSearchQuery] = useState('');
  const [filterEmployee, setFilterEmployee] = useState('');
  const [filterYear, setFilterYear] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  // ── Modal State ──
  const [modalMode, setModalMode] = useState(null); // null | 'create' | 'view' | 'edit'
  const [selectedReview, setSelectedReview] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  // ── Computed ──
  const periodLabels = {
    quarterly: t('quarterly'),
    semi_annual: t('semiAnnual'),
    annual: t('annual'),
  };

  const statusLabels = {
    draft: t('draft'),
    self_review: t('selfReview'),
    manager_review: t('managerReview'),
    completed: t('completed'),
    cancelled: t('cancelled'),
  };

  // ── Computed overall rating ──
  const computeOverall = (data) => {
    const ratings = [
      data.goals_rating,
      data.competencies_rating,
      data.teamwork_rating,
      data.communication_rating,
      data.initiative_rating,
    ].filter((r) => r > 0);
    if (ratings.length === 0) return 0;
    const raw = ratings.reduce((a, b) => a + b, 0) / ratings.length;
    return Math.round(raw * 10) / 10;
  };

  const overallRating = computeOverall(form);

  // ── Year options ──
  const currentYear = new Date().getFullYear();
  const yearOptions = [];
  for (let y = currentYear + 1; y >= currentYear - 5; y--) {
    yearOptions.push(y);
  }

  // ──────────────────────────────────────────────
  // Data Fetching
  // ──────────────────────────────────────────────

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterEmployee) params.employee = filterEmployee;
      if (filterYear) params.year = filterYear;
      if (filterStatus) params.status = filterStatus;
      if (searchQuery) params.search = searchQuery;
      const res = await performanceReviewsAPI.list(params);
      setReviews(res.data.results || res.data);
    } catch {
      toast.error(t('errorSavingData'));
    } finally {
      setLoading(false);
    }
  };

  const fetchEmployees = async () => {
    try {
      const res = await employeesAPI.list({ page_size: 300 });
      setEmployees(res.data.results || res.data);
    } catch {
      /* silent */
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    fetchReviews();
  }, [filterEmployee, filterYear, filterStatus, searchQuery]);

  // ──────────────────────────────────────────────
  // Modal Handlers
  // ──────────────────────────────────────────────

  const openCreateModal = () => {
    setForm({ ...EMPTY_FORM });
    setModalMode('create');
  };

  const openViewModal = async (review) => {
    setModalMode('view');
    setSelectedReview(null);
    setDetailLoading(true);
    try {
      const res = await performanceReviewsAPI.get(review.id);
      setSelectedReview(res.data);
    } catch {
      toast.error(t('errorSavingData'));
      setModalMode(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const openEditModal = async (review) => {
    setModalMode('edit');
    setSelectedReview(null);
    setDetailLoading(true);
    try {
      const res = await performanceReviewsAPI.get(review.id);
      const data = res.data;
      setSelectedReview(data);
      setForm({
        employee: data.employee || '',
        reviewer: data.reviewer || '',
        review_period: data.review_period || 'quarterly',
        year: data.year || currentYear,
        quarter: data.quarter || 1,
        goals_rating: data.goals_rating || 0,
        competencies_rating: data.competencies_rating || 0,
        teamwork_rating: data.teamwork_rating || 0,
        communication_rating: data.communication_rating || 0,
        initiative_rating: data.initiative_rating || 0,
        strengths: data.strengths || '',
        areas_for_improvement: data.areas_for_improvement || '',
        goals_for_next_period: data.goals_for_next_period || '',
        status: data.status || 'draft',
      });
    } catch {
      toast.error(t('errorSavingData'));
      setModalMode(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeModal = () => {
    setModalMode(null);
    setSelectedReview(null);
    setForm({ ...EMPTY_FORM });
  };

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  // ──────────────────────────────────────────────
  // Save Handler
  // ──────────────────────────────────────────────

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.employee) {
      toast.error(t('selectEmployee'));
      return;
    }

    setSaving(true);
    try {
      const payload = {
        ...form,
        employee: parseInt(form.employee),
        year: parseInt(form.year),
        quarter: form.review_period === 'quarterly' ? parseInt(form.quarter) : null,
      };

      // Remove quarter for non-quarterly periods
      if (form.review_period !== 'quarterly') {
        delete payload.quarter;
      }

      if (modalMode === 'create') {
        await performanceReviewsAPI.create(payload);
        toast.success(t('reviewCreated'));
      } else if (modalMode === 'edit') {
        await performanceReviewsAPI.update(selectedReview.id, payload);
        toast.success(t('reviewUpdated'));
      }

      closeModal();
      fetchReviews();
    } catch (err) {
      const errorMsg =
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.detail ||
        t('errorSavingData');
      toast.error(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  // ──────────────────────────────────────────────
  // Get employee name by id
  // ──────────────────────────────────────────────

  const getEmployeeName = (id) => {
    const emp = employees.find((e) => e.id === (typeof id === 'number' ? id : parseInt(id)));
    if (emp) return emp.full_name || emp.first_name;
    // Fallback for nested employee objects
    if (typeof id === 'object' && id !== null) {
      return id.full_name || id.first_name || `${id.first_name || ''} ${id.last_name || ''}`.trim();
    }
    return '-';
  };

  const getReviewerName = (id) => {
    if (!id) return '-';
    const emp = employees.find((e) => e.id === (typeof id === 'number' ? id : parseInt(id)));
    if (emp) return emp.full_name || emp.first_name;
    if (typeof id === 'object' && id !== null) {
      return id.full_name || id.first_name || `${id.first_name || ''} ${id.last_name || ''}`.trim();
    }
    return '-';
  };

  // ──────────────────────────────────────────────
  // Render: Detail Modal
  // ──────────────────────────────────────────────

  const renderDetailModal = () => {
    if (!selectedReview) return null;
    const review = selectedReview;
    const overall = computeOverall(review);

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                <Award className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {t('performanceReviews')} - {getEmployeeName(review.employee)}
              </h3>
            </div>
            <button
              onClick={closeModal}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="p-5 space-y-5">
            {/* Info Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('reviewPeriod')}</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{periodLabels[review.review_period]}</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('year')}</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{review.year}</p>
              </div>
              {review.review_period === 'quarterly' && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('quarter')}</p>
                  <p className="font-semibold text-gray-900 dark:text-gray-100">Q{review.quarter}</p>
                </div>
              )}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('status')}</p>
                <span
                  className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    STATUS_COLORS[review.status] || ''
                  }`}
                >
                  {statusLabels[review.status] || review.status}
                </span>
              </div>
            </div>

            {/* Reviewer */}
            {review.reviewer && (
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('reviewer') || 'Reviewer'}</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">{getReviewerName(review.reviewer)}</p>
              </div>
            )}

            {/* Overall Rating - Prominent Display */}
            <div
              className={`rounded-xl border p-5 text-center ${ratingBgClass(
                overall || 0
              )} transition-colors`}
            >
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">
                {t('overallRating')}
              </p>
              <StarDisplay value={Math.round(overall)} size="lg" showLabel={false} t={t} />
              <p className={`text-3xl font-bold mt-2 ${ratingColorClass(overall)}`}>
                {overall > 0 ? overall.toFixed(1) : '-'}
              </p>
              {overall > 0 && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {ratingLabel(t, overall)}
                </p>
              )}
            </div>

            {/* Rating Criteria Cards */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                {t('performanceReviews')}
              </h4>
              <div className="grid gap-3">
                {RATING_CRITERIA.map(({ key, labelKey }) => {
                  const val = review[key] || 0;
                  return (
                    <div
                      key={key}
                      className={`flex items-center justify-between p-3 rounded-lg border ${
                        val > 0
                          ? ratingBgClass(val)
                          : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600'
                      }`}
                    >
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t(labelKey)}
                      </span>
                      <div className="flex items-center gap-2">
                        <StarDisplay value={val} size="sm" showLabel={false} t={t} />
                        {val > 0 && (
                          <span
                            className={`text-sm font-bold ${ratingColorClass(val)}`}
                          >
                            {val}/5
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Text Sections */}
            <div className="space-y-4">
              {review.strengths && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                    {t('strengths')}
                  </h4>
                  <div className="bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-lg p-3">
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {review.strengths}
                    </p>
                  </div>
                </div>
              )}

              {review.areas_for_improvement && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                    {t('areasForImprovement')}
                  </h4>
                  <div className="bg-orange-50 dark:bg-orange-900/10 border border-orange-200 dark:border-orange-800 rounded-lg p-3">
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {review.areas_for_improvement}
                    </p>
                  </div>
                </div>
              )}

              {review.goals_for_next_period && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                    {t('goalsForNextPeriod')}
                  </h4>
                  <div className="bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {review.goals_for_next_period}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex gap-3 p-5 border-t dark:border-gray-700">
            {canManage && review.status !== 'cancelled' && review.status !== 'completed' && (
              <button
                onClick={() => {
                  const formData = {
                    employee: review.employee || '',
                    reviewer: review.reviewer || '',
                    review_period: review.review_period || 'quarterly',
                    year: review.year || currentYear,
                    quarter: review.quarter || 1,
                    goals_rating: review.goals_rating || 0,
                    competencies_rating: review.competencies_rating || 0,
                    teamwork_rating: review.teamwork_rating || 0,
                    communication_rating: review.communication_rating || 0,
                    initiative_rating: review.initiative_rating || 0,
                    strengths: review.strengths || '',
                    areas_for_improvement: review.areas_for_improvement || '',
                    goals_for_next_period: review.goals_for_next_period || '',
                    status: review.status || 'draft',
                  };
                  setForm(formData);
                  setModalMode('edit');
                }}
                className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors text-sm font-medium"
              >
                <Edit2 className="w-4 h-4" /> {t('editReview')}
              </button>
            )}
            <button
              onClick={closeModal}
              className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
            >
              {t('cancel')}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // ──────────────────────────────────────────────
  // Render: Create / Edit Modal
  // ──────────────────────────────────────────────

  const renderFormModal = () => {
    const isEdit = modalMode === 'edit';
    const title = isEdit ? t('editReview') : t('addReview');

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 rounded-t-2xl z-10">
            <div className="flex items-center gap-3">
              <div
                className={`p-2 rounded-lg ${
                  isEdit
                    ? 'bg-blue-100 dark:bg-blue-900/30'
                    : 'bg-green-100 dark:bg-green-900/30'
                }`}
              >
                {isEdit ? (
                  <Edit2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                ) : (
                  <Plus className="w-5 h-5 text-green-600 dark:text-green-400" />
                )}
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{title}</h3>
            </div>
            <button
              onClick={closeModal}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSave} className="p-5 space-y-5">
            {/* Employee & Reviewer */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('employee')} *
                </label>
                <select
                  value={form.employee}
                  onChange={(e) => updateField('employee', e.target.value)}
                  required
                  disabled={isEdit}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none bg-white disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  <option value="">{t('selectEmployee')}</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name || emp.first_name}
                      {emp.employee_number ? ` (${emp.employee_number})` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('reviewer') || 'Reviewer'}
                </label>
                <select
                  value={form.reviewer}
                  onChange={(e) => updateField('reviewer', e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none bg-white"
                >
                  <option value="">--</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name || emp.first_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Review Period, Year, Quarter */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('reviewPeriod')} *
                </label>
                <select
                  value={form.review_period}
                  onChange={(e) => updateField('review_period', e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none bg-white"
                >
                  {Object.entries(REVIEW_PERIOD_MAP).map(([k, v]) => (
                    <option key={k} value={k}>
                      {t(v)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('year')} *
                </label>
                <select
                  value={form.year}
                  onChange={(e) => updateField('year', e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none bg-white"
                >
                  {yearOptions.map((y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  ))}
                </select>
              </div>
              {form.review_period === 'quarterly' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {t('quarter')} *
                  </label>
                  <select
                    value={form.quarter}
                    onChange={(e) => updateField('quarter', e.target.value)}
                    className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none bg-white"
                  >
                    {[1, 2, 3, 4].map((q) => (
                      <option key={q} value={q}>
                        Q{q}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('status')}
              </label>
              <select
                value={form.status}
                onChange={(e) => updateField('status', e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none bg-white"
              >
                {Object.entries(STATUS_MAP).map(([k, v]) => (
                  <option key={k} value={k}>
                    {t(v)}
                  </option>
                ))}
              </select>
            </div>

            {/* Divider */}
            <div className="border-t dark:border-gray-700" />

            {/* Ratings Section */}
            <div>
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                {t('performanceReviews')}
              </h4>
              <div className="space-y-4">
                {RATING_CRITERIA.map(({ key, labelKey }) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                  >
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[120px]">
                      {t(labelKey)}
                    </span>
                    <StarRatingInput
                      value={form[key]}
                      onChange={(val) => updateField(key, val)}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Overall Rating Preview */}
            <div
              className={`rounded-xl border p-4 text-center transition-colors ${
                overall > 0
                  ? ratingBgClass(overall)
                  : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600'
              }`}
            >
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-1">
                {t('overallRating')}
              </p>
              <StarDisplay
                value={Math.round(overall)}
                size="lg"
                showLabel={false}
                t={t}
              />
              <p className={`text-2xl font-bold mt-1 ${ratingColorClass(overall)}`}>
                {overall > 0 ? overall.toFixed(1) : '-'}
              </p>
              {overall > 0 && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {ratingLabel(t, overall)}
                </p>
              )}
            </div>

            {/* Divider */}
            <div className="border-t dark:border-gray-700" />

            {/* Text Areas */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('strengths')}
                </label>
                <textarea
                  value={form.strengths}
                  onChange={(e) => updateField('strengths', e.target.value)}
                  rows={3}
                  placeholder="..."
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('areasForImprovement')}
                </label>
                <textarea
                  value={form.areas_for_improvement}
                  onChange={(e) => updateField('areas_for_improvement', e.target.value)}
                  rows={3}
                  placeholder="..."
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('goalsForNextPeriod')}
                </label>
                <textarea
                  value={form.goals_for_next_period}
                  onChange={(e) => updateField('goals_for_next_period', e.target.value)}
                  rows={3}
                  placeholder="..."
                  className="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none resize-none"
                />
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 disabled:opacity-50 transition-colors font-medium text-sm"
              >
                {saving ? t('saving') : isEdit ? t('save') : t('create')}
              </button>
              <button
                type="button"
                onClick={closeModal}
                className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium text-sm"
              >
                {t('cancel')}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // ──────────────────────────────────────────────
  // Render: Main Page
  // ──────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-riadah-100 dark:bg-riadah-900/30 rounded-xl">
            <ClipboardList className="w-6 h-6 text-riadah-600 dark:text-riadah-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {t('performanceReviews')}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-0.5 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4" />
              {t('performanceReviews')}
            </p>
          </div>
        </div>
        {canManage && (
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-4 py-2.5 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 transition-colors shadow-sm text-sm font-medium"
          >
            <Plus className="w-4 h-4" /> {t('addReview')}
          </button>
        )}
      </div>

      {/* Stats Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <ClipboardList className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{reviews.length}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('performanceReviews')}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <Award className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {reviews.filter((r) => r.status === 'completed').length}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('completed')}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
              <Star className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {reviews.filter((r) => r.status === 'draft').length}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('draft')}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              {(() => {
                const completed = reviews.filter(
                  (r) => r.status === 'completed' && r.overall_rating
                );
                const avg =
                  completed.length > 0
                    ? (
                        completed.reduce((sum, r) => sum + (r.overall_rating || 0), 0) /
                        completed.length
                      ).toFixed(1)
                    : '-';
                return (
                  <>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{avg}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{t('overallRating')}</p>
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute top-1/2 -translate-y-1/2 start-3 w-4 h-4 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('search') + '...'}
              className="w-full ps-9 pe-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none text-sm"
            />
          </div>
          {/* Employee Filter */}
          <select
            value={filterEmployee}
            onChange={(e) => setFilterEmployee(e.target.value)}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none text-sm bg-white"
          >
            <option value="">{t('allStatuses').replace('Statuses', '') + ' ' + t('employee')}</option>
            {employees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.full_name || emp.first_name}
              </option>
            ))}
          </select>
          {/* Year Filter */}
          <select
            value={filterYear}
            onChange={(e) => setFilterYear(e.target.value)}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none text-sm bg-white"
          >
            <option value="">{t('allYears')}</option>
            {yearOptions.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-riadah-500 focus:border-transparent outline-none text-sm bg-white"
          >
            <option value="">{t('allStatuses')}</option>
            {Object.entries(STATUS_MAP).map(([k, v]) => (
              <option key={k} value={k}>
                {t(v)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Reviews Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-flex items-center gap-2 text-gray-400 dark:text-gray-500">
              <div className="w-5 h-5 border-2 border-gray-300 dark:border-gray-600 border-t-riadah-500 rounded-full animate-spin" />
              {t('loading')}
            </div>
          </div>
        ) : reviews.length === 0 ? (
          <div className="p-12 text-center">
            <ClipboardList className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">{t('noReviews')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="px-4 py-3 text-right font-medium">{t('employee')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('reviewPeriod')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('year')}/{t('quarter')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('overallRating')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('status')}</th>
                  <th className="px-4 py-3 text-right font-medium">{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {reviews.map((review) => {
                  const empName = getEmployeeName(review.employee);
                  const overallVal = review.overall_rating || computeOverall(review);
                  return (
                    <tr
                      key={review.id}
                      className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900 dark:text-gray-100">{empName}</p>
                        {review.reviewer && (
                          <p className="text-xs text-gray-400 dark:text-gray-500">
                            {getReviewerName(review.reviewer)}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                        {periodLabels[review.review_period]}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                        {review.year}
                        {review.review_period === 'quarterly' && review.quarter
                          ? ` / Q${review.quarter}`
                          : ''}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <StarDisplay
                            value={Math.round(overallVal)}
                            size="sm"
                            showLabel={false}
                            t={t}
                          />
                          {overallVal > 0 && (
                            <span
                              className={`text-xs font-bold ${ratingColorClass(overallVal)}`}
                            >
                              {overallVal.toFixed(1)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                            STATUS_COLORS[review.status] || ''
                          }`}
                        >
                          {statusLabels[review.status] || review.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => openViewModal(review)}
                            className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-riadah-600 dark:hover:text-riadah-400 hover:bg-riadah-50 dark:hover:bg-riadah-900/20 rounded-lg transition-colors"
                            title={t('view')}
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {canManage &&
                            review.status !== 'cancelled' &&
                            review.status !== 'completed' && (
                              <button
                                onClick={() => openEditModal(review)}
                                className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                                title={t('edit')}
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                            )}
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

      {/* ── Modals ── */}
      {modalMode === 'view' && renderDetailModal()}
      {(modalMode === 'create' || modalMode === 'edit') && renderFormModal()}
    </div>
  );
}
