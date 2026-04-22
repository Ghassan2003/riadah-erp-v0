import React, { useState, useEffect } from 'react';
import {
  FileText, CheckCircle, DollarSign, AlertTriangle, Plus, Search, Download,
  X, RefreshCw, XCircle, Play
} from 'lucide-react';
import toast from 'react-hot-toast';

// ─── Mock Data ─────────────────────────────────────────────────────
const mockStats = { total_contracts: 24, active_contracts: 16, total_value: 3200000, expiring_soon_count: 3 };
const mockContracts = [
  { id: 1, contract_number: 'CTR-001', title: 'عقد تطوير النظام', type: 'خدمات', customer_supplier: 'شركة التقنية', start_date: '2024-01-01', end_date: '2025-06-30', value: 500000, status: 'active', remaining_days: 165 },
  { id: 2, contract_number: 'CTR-002', title: 'عقد توريد معدات', type: 'توريد', customer_supplier: 'مؤسسة البناء', start_date: '2024-06-01', end_date: '2025-02-28', value: 250000, status: 'expiring_soon', remaining_days: 45 },
  { id: 3, contract_number: 'CTR-003', title: 'عقد صيانة سنوي', type: 'صيانة', customer_supplier: 'شركة المرافق', start_date: '2023-07-01', end_date: '2024-12-31', value: 120000, status: 'expired', remaining_days: 0 },
  { id: 4, contract_number: 'CTR-004', title: 'عقد استشارات', type: 'خدمات', customer_supplier: 'شركة الاستشارات', start_date: '2025-01-01', end_date: '2025-12-31', value: 350000, status: 'draft', remaining_days: 365 },
  { id: 5, contract_number: 'CTR-005', title: 'عقد تشييد مبنى', type: 'إنشاءات', customer_supplier: 'شركة العمران', start_date: '2024-03-15', end_date: '2025-09-15', value: 1500000, status: 'active', remaining_days: 245 },
];
const mockMilestones = [
  { id: 1, contract: 'عقد تطوير النظام', title: 'المرحلة الأولى - التحليل', due_date: '2024-03-31', amount: 100000, status: 'completed' },
  { id: 2, contract: 'عقد تطوير النظام', title: 'المرحلة الثانية - التطوير', due_date: '2024-09-30', amount: 200000, status: 'in_progress' },
  { id: 3, contract: 'عقد توريد معدات', title: 'التوريد الأولي', due_date: '2024-08-15', amount: 125000, status: 'completed' },
  { id: 4, contract: 'عقد تشييد مبنى', title: 'الأساسات', due_date: '2025-01-30', amount: 500000, status: 'pending' },
];
const mockPayments = [
  { id: 1, contract: 'عقد تطوير النظام', amount: 100000, due_date: '2024-03-31', paid_date: '2024-03-28', status: 'paid', paid_amount: 100000 },
  { id: 2, contract: 'عقد تطوير النظام', amount: 200000, due_date: '2024-09-30', paid_date: null, status: 'unpaid', paid_amount: 0 },
  { id: 3, contract: 'عقد توريد معدات', amount: 125000, due_date: '2024-08-15', paid_date: '2024-08-10', status: 'paid', paid_amount: 125000 },
  { id: 4, contract: 'عقد تشييد مبنى', amount: 500000, due_date: '2025-01-30', paid_date: null, status: 'overdue', paid_amount: 0 },
  { id: 5, contract: 'عقد صيانة سنوي', amount: 60000, due_date: '2024-12-31', paid_date: '2024-12-30', status: 'paid', paid_amount: 60000 },
];

// ─── Shared Components ─────────────────────────────────────────────
const Badge = ({ children, color = 'blue' }) => {
  const c = {
    green: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    red: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    yellow: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    blue: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/40 dark:text-accent-300',
    gray: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300',
    violet: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
  };
  return <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${c[color]}`}>{children}</span>;
};

const StatCard = ({ icon: Icon, label, value, color }) => (
  <div className={`relative overflow-hidden rounded-2xl p-4 md:p-5 bg-gradient-to-br ${color} text-white shadow-lg`}>
    <div className="absolute top-0 left-0 w-24 h-24 bg-white/10 rounded-full -translate-x-8 -translate-y-8" />
    <div className="flex items-center gap-3">
      <div className="p-2 rounded-xl bg-white/20"><Icon className="w-5 h-5" /></div>
      <div><p className="text-xs opacity-80">{label}</p><p className="text-xl font-bold mt-0.5">{value}</p></div>
    </div>
  </div>
);

const Modal = ({ isOpen, onClose, title, children, wide }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" onClick={onClose}>
      <div className={`bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full ${wide ? 'max-w-2xl' : 'max-w-lg'} max-h-[90vh] overflow-y-auto`} onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-800 dark:text-white">{title}</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
};

const F = ({ label, children }) => (
  <div className="space-y-1.5"><label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>{children}</div>
);

const inp = "w-full px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-800 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-500 transition";
const bB = "inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 shadow-sm";
const bP = `${bB} bg-gradient-to-l from-riadah-500 to-riadah-400 text-white hover:from-riadah-500 hover:to-riadah-500`;
const bS = `${bB} bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700`;
const bSuc = `${bB} bg-emerald-500 text-white hover:bg-emerald-600`;
const bWar = `${bB} bg-amber-500 text-white hover:bg-amber-600`;
const bDan = `${bB} bg-red-500 text-white hover:bg-red-600`;
const fmt = (n) => n.toLocaleString('ar-SA');

const contractStatus = {
  active: { l: 'نشط', c: 'green' },
  draft: { l: 'مسودة', c: 'gray' },
  expired: { l: 'منتهي', c: 'red' },
  expiring_soon: { l: 'ينتهي قريباً', c: 'yellow' },
  terminated: { l: 'ملغي', c: 'gray' },
};

// ─── Main ──────────────────────────────────────────────────────────
export default function ContractsPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modals, setModals] = useState({ contract: false, payment: false });

  useEffect(() => { setTimeout(() => setLoading(false), 600); }, []);
  const toggle = (k) => setModals(p => ({ ...p, [k]: !p[k] }));
  const act = (msg) => toast.success(msg);

  const tabs = [
    { label: 'العقود', icon: FileText },
    { label: 'المراحل', icon: CheckCircle },
    { label: 'الدفعات', icon: DollarSign },
  ];

  return (
    <div dir="rtl" className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <div className="bg-gradient-to-l from-riadah-500 via-blue-600 to-riadah-700 text-white px-4 md:px-8 py-6 shadow-xl">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3"><FileText className="w-7 h-7" /> إدارة العقود</h1>
            <p className="text-blue-200 mt-1 text-sm">إدارة العقود والمراحل والدفاعات</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => act('تم التصدير')} className="bS !bg-white/15 !text-white hover:!bg-white/25"><Download className="w-4 h-4" /> تصدير</button>
            <button onClick={() => toggle('contract')} className={bP}><Plus className="w-4 h-4" /> عقد جديد</button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 space-y-6">
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="h-28 rounded-2xl bg-gray-200 dark:bg-gray-800 animate-pulse" />)}</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={FileText} label="إجمالي العقود" value={mockStats.total_contracts} color="from-riadah-400 to-riadah-500" />
            <StatCard icon={CheckCircle} label="العقود النشطة" value={mockStats.active_contracts} color="from-emerald-500 to-emerald-600" />
            <StatCard icon={DollarSign} label="القيمة الإجمالية" value={`${(mockStats.total_value / 1000000).toFixed(1)}M`} color="from-violet-500 to-violet-600" />
            <StatCard icon={AlertTriangle} label="تنتهي قريباً" value={mockStats.expiring_soon_count} color="from-amber-500 to-amber-600" />
          </div>
        )}

        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div className="flex border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
            {tabs.map((t, i) => (
              <button key={i} onClick={() => setActiveTab(i)}
                className={`flex items-center gap-2 px-5 py-3.5 text-sm font-medium whitespace-nowrap transition-all border-b-2 ${
                  activeTab === i ? 'border-accent-500 text-accent-500 dark:text-accent-400 bg-riadah-50/50 dark:bg-riadah-900/20' : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}>
                <t.icon className="w-4 h-4" /> {t.label}
              </button>
            ))}
          </div>
          <div className="p-4 md:p-6">
            {activeTab === 0 && <ContractsTab search={search} setSearch={setSearch} toggle={toggle} act={act} />}
            {activeTab === 1 && <MilestonesTab search={search} setSearch={setSearch} act={act} />}
            {activeTab === 2 && <PaymentsTab search={search} setSearch={setSearch} toggle={toggle} act={act} />}
          </div>
        </div>
      </div>

      {/* Create Contract Modal */}
      <Modal isOpen={modals.contract} onClose={() => toggle('contract')} title="إنشاء عقد جديد" wide>
        <form className="space-y-4" onSubmit={e => { e.preventDefault(); toggle('contract'); act('تم إنشاء العقد بنجاح'); }}>
          <F label="عنوان العقد"><input className={inp} placeholder="عنوان العقد" /></F>
          <div className="grid grid-cols-2 gap-4">
            <F label="النوع"><select className={inp}><option>خدمات</option><option>توريد</option><option>صيانة</option><option>إنشاءات</option><option>استشارات</option></select></F>
            <F label="العميل / المورد"><input className={inp} placeholder="اسم الجهة" /></F>
          </div>
          <F label="المشروع"><input className={inp} placeholder="اسم المشروع (اختياري)" /></F>
          <div className="grid grid-cols-3 gap-4">
            <F label="تاريخ البدء"><input type="date" className={inp} /></F>
            <F label="تاريخ الانتهاء"><input type="date" className={inp} /></F>
            <F label="القيمة"><input type="number" className={inp} placeholder="0.00" /></F>
          </div>
          <F label="الشروط والأحكام"><textarea className={`${inp} h-24 resize-none`} placeholder="الشروط والأحكام..." /></F>
          <div className="flex gap-3 pt-2"><button type="submit" className={bP}>إنشاء</button><button type="button" onClick={() => toggle('contract')} className={bS}>إلغاء</button></div>
        </form>
      </Modal>

      {/* Create Payment Modal */}
      <Modal isOpen={modals.payment} onClose={() => toggle('payment')} title="تسجيل دفعة">
        <form className="space-y-4" onSubmit={e => { e.preventDefault(); toggle('payment'); act('تم تسجيل الدفعة بنجاح'); }}>
          <F label="العقد"><select className={inp}>{mockContracts.filter(c => c.status === 'active').map(c => <option key={c.id}>{c.title}</option>)}</select></F>
          <div className="grid grid-cols-2 gap-4">
            <F label="المبلغ"><input type="number" className={inp} placeholder="0.00" /></F>
            <F label="تاريخ الاستحقاق"><input type="date" className={inp} /></F>
          </div>
          <F label="ملاحظات"><textarea className={`${inp} h-20 resize-none`} /></F>
          <div className="flex gap-3 pt-2"><button type="submit" className={bP}>تسجيل</button><button type="button" onClick={() => toggle('payment')} className={bS}>إلغاء</button></div>
        </form>
      </Modal>
    </div>
  );
}

// ─── Contracts Tab ─────────────────────────────────────────────────
function ContractsTab({ search, setSearch, toggle, act }) {
  const [statusFilter, setStatusFilter] = useState('all');
  const filtered = mockContracts.filter(c =>
    (statusFilter === 'all' || c.status === statusFilter) &&
    (c.title.includes(search) || c.contract_number.includes(search) || c.customer_supplier.includes(search))
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)} className={`${inp} !pr-10`} placeholder="بحث في العقود..." />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className={inp}>
          <option value="all">جميع الحالات</option>
          {Object.entries(contractStatus).map(([k, v]) => <option key={k} value={k}>{v.l}</option>)}
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
            {['الرقم', 'العنوان', 'النوع', 'العميل / المورد', 'تاريخ البدء', 'تاريخ الانتهاء', 'القيمة', 'الحالة', 'الأيام المتبقية', 'إجراءات'].map(h => <th key={h} className="px-3 py-3 text-right font-medium whitespace-nowrap">{h}</th>)}
          </tr></thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {filtered.map(c => (
              <tr key={c.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <td className="px-3 py-3 text-accent-500 font-medium">{c.contract_number}</td>
                <td className="px-3 py-3 font-medium text-gray-800 dark:text-white">{c.title}</td>
                <td className="px-3 py-3"><Badge color="violet">{c.type}</Badge></td>
                <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{c.customer_supplier}</td>
                <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{c.start_date}</td>
                <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{c.end_date}</td>
                <td className="px-3 py-3 font-medium text-gray-800 dark:text-gray-200">{fmt(c.value)}</td>
                <td className="px-3 py-3"><Badge color={contractStatus[c.status]?.c}>{contractStatus[c.status]?.l}</Badge></td>
                <td className="px-3 py-3">
                  <span className={c.remaining_days <= 60 && c.remaining_days > 0 ? 'text-amber-600 font-bold' : c.remaining_days === 0 ? 'text-red-500 font-bold' : 'text-gray-600 dark:text-gray-400'}>
                    {c.remaining_days === 0 ? 'منتهي' : `${c.remaining_days} يوم`}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-1 flex-nowrap">
                    {c.status === 'draft' && (
                      <button onClick={() => act('تم تفعيل العقد')} className="p-1.5 rounded-lg hover:bg-emerald-50 dark:hover:bg-emerald-900/20 text-emerald-500" title="تفعيل"><Play className="w-4 h-4" /></button>
                    )}
                    {c.status === 'expired' && (
                      <button onClick={() => act('تم تجديد العقد')} className="p-1.5 rounded-lg hover:bg-riadah-50 dark:hover:bg-riadah-900/20 text-accent-500" title="تجديد"><RefreshCw className="w-4 h-4" /></button>
                    )}
                    {(c.status === 'active' || c.status === 'draft') && (
                      <button onClick={() => act('تم إلغاء العقد')} className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500" title="إلغاء"><XCircle className="w-4 h-4" /></button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Milestones Tab ────────────────────────────────────────────────
function MilestonesTab({ search, setSearch, act }) {
  const mStatus = { pending: { l: 'معلق', c: 'gray' }, in_progress: { l: 'قيد التنفيذ', c: 'yellow' }, completed: { l: 'مكتمل', c: 'green' } };
  const [sFilter, setSFilter] = useState('all');
  const filtered = mockMilestones.filter(m =>
    (sFilter === 'all' || m.status === sFilter) &&
    (m.contract.includes(search) || m.title.includes(search))
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)} className={`${inp} !pr-10`} placeholder="بحث..." />
        </div>
        <select value={sFilter} onChange={e => setSFilter(e.target.value)} className={inp}>
          <option value="all">جميع الحالات</option>
          {Object.entries(mStatus).map(([k, v]) => <option key={k} value={k}>{v.l}</option>)}
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
            {['العقد', 'المرحلة', 'تاريخ الاستحقاق', 'المبلغ', 'الحالة', 'إجراءات'].map(h => <th key={h} className="px-4 py-3 text-right font-medium">{h}</th>)}
          </tr></thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {filtered.map(m => (
              <tr key={m.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{m.contract}</td>
                <td className="px-4 py-3 font-medium text-gray-800 dark:text-white">{m.title}</td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{m.due_date}</td>
                <td className="px-4 py-3 font-medium text-gray-800 dark:text-gray-200">{fmt(m.amount)}</td>
                <td className="px-4 py-3"><Badge color={mStatus[m.status]?.c}>{mStatus[m.status]?.l}</Badge></td>
                <td className="px-4 py-3">
                  {m.status === 'pending' && (
                    <button onClick={() => act('تم بدء المرحلة')} className="text-xs px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 text-amber-600 rounded-lg hover:bg-amber-100">بدء</button>
                  )}
                  {m.status === 'in_progress' && (
                    <button onClick={() => act('تم إكمال المرحلة')} className="text-xs px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 rounded-lg hover:bg-emerald-100">إكمال</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Payments Tab ──────────────────────────────────────────────────
function PaymentsTab({ search, setSearch, toggle, act }) {
  const pStatus = { paid: { l: 'مدفوع', c: 'green' }, unpaid: { l: 'غير مدفوع', c: 'yellow' }, overdue: { l: 'متأخر', c: 'red' }, partial: { l: 'جزئي', c: 'blue' } };
  const [sFilter, setSFilter] = useState('all');
  const filtered = mockPayments.filter(p =>
    (sFilter === 'all' || p.status === sFilter) &&
    (p.contract.includes(search))
  );
  const progress = (paid, total) => total > 0 ? Math.min(100, (paid / total) * 100) : 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)} className={`${inp} !pr-10`} placeholder="بحث..." />
        </div>
        <select value={sFilter} onChange={e => setSFilter(e.target.value)} className={inp}>
          <option value="all">جميع الحالات</option>
          {Object.entries(pStatus).map(([k, v]) => <option key={k} value={k}>{v.l}</option>)}
        </select>
        <button onClick={() => toggle('payment')} className={bP}><Plus className="w-4 h-4" /> دفعة جديدة</button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
            {['العقد', 'المبلغ', 'تاريخ الاستحقاق', 'تاريخ الدفع', 'المبلغ المدفوع', 'النسبة', 'الحالة', 'إجراءات'].map(h => <th key={h} className="px-3 py-3 text-right font-medium whitespace-nowrap">{h}</th>)}
          </tr></thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {filtered.map(p => (
              <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <td className="px-3 py-3 font-medium text-gray-800 dark:text-white">{p.contract}</td>
                <td className="px-3 py-3 font-medium text-gray-800 dark:text-gray-200">{fmt(p.amount)}</td>
                <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{p.due_date}</td>
                <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{p.paid_date || '—'}</td>
                <td className="px-3 py-3 text-gray-800 dark:text-gray-200">{fmt(p.paid_amount)}</td>
                <td className="px-3 py-3 w-28">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full bg-riadah-500 rounded-full transition-all" style={{ width: `${progress(p.paid_amount, p.amount)}%` }} />
                    </div>
                    <span className="text-xs text-gray-500">{progress(p.paid_amount, p.amount)}%</span>
                  </div>
                </td>
                <td className="px-3 py-3"><Badge color={pStatus[p.status]?.c}>{pStatus[p.status]?.l}</Badge></td>
                <td className="px-3 py-3">
                  {p.status !== 'paid' && (
                    <button onClick={() => act('تم تسجيل الدفع')} className="text-xs px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 rounded-lg hover:bg-emerald-100">تسجيل دفع</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
