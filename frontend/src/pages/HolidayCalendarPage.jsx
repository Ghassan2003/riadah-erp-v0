/**
 * HolidayCalendarPage - صفحة إدارة التقويم والعطلات الرسمية.
 * يعرض تقويم سنوي مع تمييز العطلات وإدارتها (إضافة/حذف).
 * يدعم الوضع الداكن و RTL.
 */

import { useState, useEffect } from 'react';
import { useI18n } from '../i18n/I18nContext';
import toast from 'react-hot-toast';
import {
  Calendar, Plus, X, Trash2, ChevronLeft, ChevronRight,
  CalendarDays, PartyPopper, Building, Star, BarChart3,
  RefreshCw, CheckCircle, AlertTriangle, Loader2,
} from 'lucide-react';

/* ─── بيانات العطلات السعودية (أمثلة) ─── */
const DEFAULT_HOLIDAYS = [
  { id: 1, name: 'رأس السنة الميلادية', date: '2025-01-01', type: 'public', recurring: true, notes: '' },
  { id: 2, name: 'اليوم الوطني السعودي', date: '2025-09-23', type: 'public', recurring: true, notes: 'عيد التأسيس' },
  { id: 3, name: 'عيد الفطر المبارك', date: '2025-03-30', type: 'public', recurring: false, notes: 'يبدأ اعتباراً من رؤية الهلال' },
  { id: 4, name: 'عيد الأضحى المبارك', date: '2025-06-06', type: 'public', recurring: false, notes: 'يبدأ اعتباراً من يوم عرفة' },
  { id: 5, name: 'يوم التأسيس', date: '2025-02-22', type: 'public', recurring: true, notes: '' },
  { id: 6, name: 'عيد الميلاد المجيد', date: '2025-12-25', type: 'optional', recurring: true, notes: '' },
  { id: 7, name: 'إجازة نصف العام', date: '2025-06-20', type: 'company', recurring: false, notes: 'حسب تقويم الشركة' },
  { id: 8, name: 'إجازة نهاية العام', date: '2025-12-31', type: 'company', recurring: true, notes: '' },
];

/* ─── أسماء الأشهر العربية ─── */
const MONTH_NAMES_AR = [
  'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
  'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر',
];

const MONTH_NAMES_SHORT = [
  'ينا', 'فبر', 'مار', 'أبر', 'ماي', 'يون',
  'يول', 'أغس', 'سبت', 'أكت', 'نوف', 'ديس',
];

const DAY_NAMES_AR = ['أحد', 'إثن', 'ثلا', 'أرب', 'خمي', 'جمع', 'سبت'];

/* ─── أنواع العطلات ─── */
const HOLIDAY_TYPES = {
  public: { label: 'عطلة رسمية', color: 'bg-blue-500', bgLight: 'bg-blue-100 dark:bg-blue-900/30', textColor: 'text-blue-700 dark:text-blue-400', dotColor: 'bg-blue-500' },
  company: { label: 'عطلة الشركة', color: 'bg-green-500', bgLight: 'bg-green-100 dark:bg-green-900/30', textColor: 'text-green-700 dark:text-green-400', dotColor: 'bg-green-500' },
  optional: { label: 'عطلة اختيارية', color: 'bg-yellow-500', bgLight: 'bg-yellow-100 dark:bg-yellow-900/30', textColor: 'text-yellow-700 dark:text-yellow-400', dotColor: 'bg-yellow-500' },
};

/* ─── Spinner ─── */
const Spinner = () => (
  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
);

export default function HolidayCalendarPage() {
  const { locale } = useI18n();
  const nl = locale === 'ar' ? 'ar-SA' : 'en-US';

  /* ─── حالة البيانات ─── */
  const [holidays, setHolidays] = useState(DEFAULT_HOLIDAYS);
  const [loading, setLoading] = useState(false);
  const [selectedYear, setSelectedYear] = useState(2025);
  const [viewMode, setViewMode] = useState('year'); // 'year' | 'month'
  const [selectedMonth, setSelectedMonth] = useState(() => new Date().getMonth());

  /* ─── مودال ─── */
  const [showAddModal, setShowAddModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showConfirmDelete, setShowConfirmDelete] = useState(null);
  const [holidayForm, setHolidayForm] = useState({
    name: '',
    date: '',
    type: 'public',
    recurring: false,
    notes: '',
  });

  /* ─── حقول الإدخال ─── */
  const inputCls = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none';
  const selectCls = 'w-full px-3 py-2.5 border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white dark:bg-gray-700';

  /* ─── حساب الأيام العاملة ─── */
  const calculateWorkingDays = (year) => {
    const yearHolidays = holidays.filter((h) => {
      const hYear = new Date(h.date).getFullYear();
      return hYear === year;
    });
    const publicHolidays = yearHolidays.filter((h) => h.type === 'public').length;
    const companyHolidays = yearHolidays.filter((h) => h.type === 'company').length;
    const optionalHolidays = yearHolidays.filter((h) => h.type === 'optional').length;
    const totalHolidays = yearHolidays.length;

    // حساب أيام الجمعة والسبت في السنة
    let fridaysSaturdays = 0;
    for (let m = 0; m < 12; m++) {
      const daysInMonth = new Date(year, m + 1, 0).getDate();
      for (let d = 1; d <= daysInMonth; d++) {
        const dayOfWeek = new Date(year, m, d).getDay();
        if (dayOfWeek === 5 || dayOfWeek === 6) fridaysSaturdays++;
      }
    }

    const isLeapYear = (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
    const totalDays = isLeapYear ? 366 : 365;
    const workingDays = Math.max(0, totalDays - fridaysSaturdays - publicHolidays - companyHolidays);

    return { publicHolidays, companyHolidays, optionalHolidays, totalHolidays, workingDays, fridaysSaturdays };
  };

  const stats = calculateWorkingDays(selectedYear);

  /* ─── تصفية العطلات حسب السنة المحددة ─── */
  const yearHolidays = holidays.filter((h) => {
    const hYear = new Date(h.date).getFullYear();
    return hYear === selectedYear;
  });

  /* ─── الحصول على عطلات شهر معين ─── */
  const getMonthHolidays = (month) => {
    return yearHolidays.filter((h) => new Date(h.date).getMonth() === month);
  };

  /* ─── بناء خلايا التقويم الشهري ─── */
  const buildMonthGrid = (month) => {
    const firstDay = new Date(selectedYear, month, 1);
    const lastDay = new Date(selectedYear, month + 1, 0);
    const startPadding = firstDay.getDay();
    const daysInMonth = lastDay.getDate();
    const monthHols = getMonthHolidays(month);

    const cells = [];
    for (let i = 0; i < startPadding; i++) {
      cells.push({ day: null });
    }
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${selectedYear}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const holiday = monthHols.find((h) => h.date === dateStr);
      const isToday = new Date().toDateString() === new Date(selectedYear, month, d).toDateString();
      const dayOfWeek = new Date(selectedYear, month, d).getDay();
      const isWeekend = dayOfWeek === 5 || dayOfWeek === 6;
      cells.push({ day: d, holiday, isToday, isWeekend, dateStr });
    }
    return cells;
  };

  /* ─── إضافة عطلة ─── */
  const handleAddHoliday = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const newHoliday = {
        ...holidayForm,
        id: Date.now(),
      };
      setHolidays((prev) => [...prev, newHoliday]);
      toast.success(`تمت إضافة "${holidayForm.name}" بنجاح`);
      setShowAddModal(false);
      setHolidayForm({ name: '', date: '', type: 'public', recurring: false, notes: '' });
    } catch (err) {
      toast.error('حدث خطأ أثناء الإضافة');
    } finally {
      setSaving(false);
    }
  };

  /* ─── حذف عطلة ─── */
  const handleDeleteHoliday = async (id) => {
    try {
      await holidayCalendarAPI.deleteHoliday(id);
      setHolidays((prev) => prev.filter((h) => h.id !== id));
      toast.success('تم حذف العطلة بنجاح');
      setShowConfirmDelete(null);
    } catch (err) {
      toast.error('خطأ في حذف العطلة');
    }
  };

  /* ─── التنقل بين الأشهر ─── */
  const prevMonth = () => {
    if (selectedMonth === 0) { setSelectedMonth(11); }
    else { setSelectedMonth(selectedMonth - 1); }
  };
  const nextMonth = () => {
    if (selectedMonth === 11) { setSelectedMonth(0); }
    else { setSelectedMonth(selectedMonth + 1); }
  };

  return (
    <div dir="rtl" className="space-y-6">

      {/* ─── العنوان ─── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">التقويم والعطلات الرسمية</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">إدارة التقويم السنوي والعطلات الرسمية وشركات</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {/* محدد السنة */}
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className={selectCls}
          >
            {[2024, 2025, 2026, 2027].map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          {/* زر الإضافة */}
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium shadow-sm"
          >
            <Plus className="w-4 h-4" />
            إضافة عطلة
          </button>
        </div>
      </div>

      {/* ─── بطاقات الإحصائيات ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
              <CalendarDays className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">العطلات الرسمية</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.publicHolidays}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
              <Building className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">عطلات الشركة</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.companyHolidays}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400">
              <Star className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">عطلات اختيارية</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.optionalHolidays}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">أيام العمل</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats.workingDays}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ─── محول العرض ─── */}
      <div className="flex gap-2 bg-white dark:bg-gray-800 rounded-xl p-1.5 shadow-sm border border-gray-100 dark:border-gray-700 w-fit">
        <button
          onClick={() => setViewMode('year')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            viewMode === 'year'
              ? 'bg-[#003366] text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
          }`}
        >
          <Calendar className="w-4 h-4" />
          عرض سنوي
        </button>
        <button
          onClick={() => setViewMode('month')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            viewMode === 'month'
              ? 'bg-[#003366] text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
          }`}
        >
          <CalendarDays className="w-4 h-4" />
          عرض شهري
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════
          عرض سنوي - شبكة 12 شهر
      ═══════════════════════════════════════════════════════ */}
      {viewMode === 'year' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {MONTH_NAMES_AR.map((monthName, monthIdx) => {
            const monthHols = getMonthHolidays(monthIdx);
            return (
              <div key={monthIdx} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                {/* عنوان الشهر */}
                <div className="bg-gradient-to-l from-[#003366] to-[#004d99] px-4 py-2.5">
                  <h4 className="text-white font-semibold text-sm">{monthName}</h4>
                </div>
                {/* أيام الأسبوع */}
                <div className="grid grid-cols-7 gap-0.5 p-2">
                  {DAY_NAMES_AR.map((d) => (
                    <div key={d} className="text-center text-[10px] font-medium text-gray-400 dark:text-gray-500 py-1">
                      {d}
                    </div>
                  ))}
                  {/* خلايا الأيام */}
                  {buildMonthGrid(monthIdx).map((cell, idx) => (
                    <div
                      key={idx}
                      className={`aspect-square flex items-center justify-center rounded text-[10px] font-medium relative ${
                        cell.day === null
                          ? ''
                          : cell.holiday
                          ? `${HOLIDAY_TYPES[cell.holiday.type].bgLight} ${HOLIDAY_TYPES[cell.holiday.type].textColor} font-bold`
                          : cell.isWeekend
                          ? 'text-red-400 dark:text-red-500'
                          : cell.isToday
                          ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 font-bold ring-1 ring-blue-300 dark:ring-blue-600'
                          : 'text-gray-600 dark:text-gray-400'
                      }`}
                      title={cell.holiday ? `${cell.holiday.name} (${HOLIDAY_TYPES[cell.holiday.type].label})` : ''}
                    >
                      {cell.day || ''}
                      {cell.holiday && (
                        <div className={`absolute bottom-0.5 w-1 h-1 rounded-full ${HOLIDAY_TYPES[cell.holiday.type].dotColor}`} />
                      )}
                    </div>
                  ))}
                </div>
                {/* العطلات في الشهر */}
                {monthHols.length > 0 && (
                  <div className="px-3 pb-2 space-y-0.5">
                    {monthHols.map((h) => (
                      <div key={h.id} className="flex items-center gap-1 text-[10px]">
                        <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${HOLIDAY_TYPES[h.type].dotColor}`} />
                        <span className="text-gray-600 dark:text-gray-400 truncate">{h.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
          عرض شهري - شهر واحد مفصل
      ═══════════════════════════════════════════════════════ */}
      {viewMode === 'month' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {/* التنقل بين الأشهر */}
          <div className="flex items-center justify-between p-5 border-b border-gray-100 dark:border-gray-700">
            <button onClick={prevMonth} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300">
              <ChevronRight className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {MONTH_NAMES_AR[selectedMonth]} {selectedYear}
            </h3>
            <button onClick={nextMonth} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300">
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>

          {/* التقويم المفصل */}
          <div className="p-5">
            <div className="grid grid-cols-7 gap-2 mb-3">
              {DAY_NAMES_AR.map((d) => (
                <div key={d} className="text-center text-sm font-medium text-gray-500 dark:text-gray-400 py-2">
                  {d}
                </div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-2">
              {buildMonthGrid(selectedMonth).map((cell, idx) => (
                <div
                  key={idx}
                  className={`min-h-[70px] rounded-lg border p-1.5 transition-all ${
                    cell.day === null
                      ? 'bg-transparent border-transparent'
                      : cell.holiday
                      ? `${HOLIDAY_TYPES[cell.holiday.type].bgLight} border-${cell.holiday.type === 'public' ? 'blue' : cell.holiday.type === 'company' ? 'green' : 'yellow'}-200 dark:border-${cell.holiday.type === 'public' ? 'blue' : cell.holiday.type === 'company' ? 'green' : 'yellow'}-800`
                      : cell.isWeekend
                      ? 'bg-red-50 dark:bg-red-900/10 border-red-100 dark:border-red-900/30'
                      : cell.isToday
                      ? 'bg-blue-50 dark:bg-blue-900/10 border-blue-300 dark:border-blue-700 ring-1 ring-blue-400'
                      : 'bg-gray-50 dark:bg-gray-700/30 border-gray-100 dark:border-gray-700'
                  }`}
                >
                  {cell.day && (
                    <>
                      <span className={`text-xs font-medium ${cell.holiday ? HOLIDAY_TYPES[cell.holiday.type].textColor : cell.isWeekend ? 'text-red-500 dark:text-red-400' : cell.isToday ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'}`}>
                        {cell.day}
                      </span>
                      {cell.holiday && (
                        <p className={`text-[10px] mt-0.5 leading-tight font-medium ${HOLIDAY_TYPES[cell.holiday.type].textColor}`}>
                          {cell.holiday.name.length > 15 ? cell.holiday.name.substring(0, 15) + '...' : cell.holiday.name}
                        </p>
                      )}
                    </>
                  )}
                </div>
              ))}
            </div>

            {/* مفتاح الألوان */}
            <div className="flex flex-wrap items-center justify-center gap-5 mt-5 pt-4 border-t border-gray-100 dark:border-gray-700">
              {Object.entries(HOLIDAY_TYPES).map(([key, info]) => (
                <div key={key} className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                  <div className={`w-3 h-3 rounded-full ${info.dotColor}`} />
                  {info.label}
                </div>
              ))}
              <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                عطلة نهاية الأسبوع
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ─── جدول العطلات ─── */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="p-5 border-b border-gray-100 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <PartyPopper className="w-5 h-5 text-[#FF6600]" />
            قائمة العطلات - {selectedYear}
          </h3>
        </div>
        <div className="overflow-x-auto">
          {yearHolidays.length === 0 ? (
            <div className="p-12 text-center">
              <CalendarDays className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">لا توجد عطلات مسجلة لهذه السنة</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/70 text-gray-600 dark:text-gray-300 border-b dark:border-gray-700">
                  <th className="px-4 py-3 text-right font-medium">التاريخ</th>
                  <th className="px-4 py-3 text-right font-medium">اسم العطلة</th>
                  <th className="px-4 py-3 text-right font-medium">النوع</th>
                  <th className="px-4 py-3 text-right font-medium">متكررة</th>
                  <th className="px-4 py-3 text-right font-medium">ملاحظات</th>
                  <th className="px-4 py-3 text-right font-medium">الإجراءات</th>
                </tr>
              </thead>
              <tbody>
                {yearHolidays
                  .sort((a, b) => new Date(a.date) - new Date(b.date))
                  .map((h) => {
                    const typeInfo = HOLIDAY_TYPES[h.type] || HOLIDAY_TYPES.public;
                    return (
                      <tr key={h.id} className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                        <td className="px-4 py-3 font-mono text-gray-600 dark:text-gray-300">{h.date}</td>
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{h.name}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${typeInfo.bgLight} ${typeInfo.textColor}`}>
                            {typeInfo.label}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {h.recurring ? (
                            <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400 text-xs">
                              <RefreshCw className="w-3 h-3" />
                              نعم
                            </span>
                          ) : (
                            <span className="text-gray-400 dark:text-gray-500 text-xs">لا</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400 max-w-[200px] truncate">{h.notes || '-'}</td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => setShowConfirmDelete(h)}
                            className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                            title="حذف"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* ─── مودال إضافة عطلة ─── */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Plus className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                إضافة عطلة جديدة
              </h3>
              <button onClick={() => setShowAddModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddHoliday} className="p-5 space-y-4">
              {/* اسم العطلة */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">اسم العطلة *</label>
                <input
                  type="text"
                  value={holidayForm.name}
                  onChange={(e) => setHolidayForm({ ...holidayForm, name: e.target.value })}
                  required
                  placeholder="مثال: عيد الفطر المبارك"
                  className={inputCls}
                />
              </div>

              {/* التاريخ */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">التاريخ *</label>
                <input
                  type="date"
                  value={holidayForm.date}
                  onChange={(e) => setHolidayForm({ ...holidayForm, date: e.target.value })}
                  required
                  className={inputCls}
                />
              </div>

              {/* النوع */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">النوع *</label>
                <select
                  value={holidayForm.type}
                  onChange={(e) => setHolidayForm({ ...holidayForm, type: e.target.value })}
                  className={selectCls}
                >
                  {Object.entries(HOLIDAY_TYPES).map(([key, info]) => (
                    <option key={key} value={key}>{info.label}</option>
                  ))}
                </select>
              </div>

              {/* متكررة */}
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">عطلة متكررة سنوياً</label>
                <button
                  type="button"
                  onClick={() => setHolidayForm({ ...holidayForm, recurring: !holidayForm.recurring })}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    holidayForm.recurring ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      holidayForm.recurring ? '-translate-x-6' : '-translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* ملاحظات */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">ملاحظات</label>
                <textarea
                  value={holidayForm.notes}
                  onChange={(e) => setHolidayForm({ ...holidayForm, notes: e.target.value })}
                  rows={2}
                  placeholder="أي ملاحظات إضافية..."
                  className={`${inputCls} resize-none`}
                />
              </div>

              {/* الأزرار */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium text-sm transition-colors"
                >
                  {saving ? (
                    <span className="flex items-center justify-center gap-2">
                      <Spinner /> جاري الحفظ...
                    </span>
                  ) : (
                    'إضافة العطلة'
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 font-medium text-sm transition-colors"
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─── مودال تأكيد الحذف ─── */}
      {showConfirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm">
            <div className="p-6 text-center">
              <div className="w-14 h-14 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
                <AlertTriangle className="w-7 h-7 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">تأكيد الحذف</h3>
              <p className="text-gray-500 dark:text-gray-400 text-sm mb-1">
                هل أنت متأكد من حذف العطلة التالية؟
              </p>
              <p className="font-semibold text-gray-700 dark:text-gray-200 mb-5">
                "{showConfirmDelete.name}"
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => handleDeleteHoliday(showConfirmDelete.id)}
                  className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium text-sm transition-colors"
                >
                  حذف
                </button>
                <button
                  onClick={() => setShowConfirmDelete(null)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 font-medium text-sm transition-colors"
                >
                  إلغاء
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
