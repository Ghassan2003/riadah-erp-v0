import React, { useState, useEffect } from 'react';
import {
  Wallet, ArrowDownCircle, ArrowUpCircle, ArrowLeftRight, CreditCard,
  Plus, Search, Download, X, Building, FileCheck, CheckSquare
} from 'lucide-react';
import toast from 'react-hot-toast';

// ─── Mock Data ─────────────────────────────────────────────────────
const mockStats = { total_receipts: 1250000, total_payments: 890000, total_transfers: 150000, account_balances: 560000 };
const mockTransactions = [
  { id: 1, transaction_number: 'TXN-001', type: 'receipt', account: 'البنك الأهلي', amount: 50000, date: '2025-01-15', payment_method: 'تحويل بنكي', reference: 'REF-1001', description: 'دفعة عقد تطوير', status: 'completed' },
  { id: 2, transaction_number: 'TXN-002', type: 'payment', account: 'الصندوق', amount: 15000, date: '2025-01-14', payment_method: 'نقدي', reference: 'REF-1002', description: 'مصروفات تشغيلية', status: 'completed' },
  { id: 3, transaction_number: 'TXN-003', type: 'transfer', account: 'البنك الأهلي', amount: 30000, date: '2025-01-13', payment_method: 'تحويل بنكي', reference: 'REF-1003', description: 'تحويل للصندوق', status: 'pending' },
  { id: 4, transaction_number: 'TXN-004', type: 'receipt', account: 'بنك الراجحي', amount: 75000, date: '2025-01-12', payment_method: 'شيك', reference: 'REF-1004', description: 'دفعة مشروع البناء', status: 'completed' },
  { id: 5, transaction_number: 'TXN-005', type: 'payment', account: 'البنك الأهلي', amount: 25000, date: '2025-01-11', payment_method: 'تحويل بنكي', reference: 'REF-1005', description: 'سداد مورد', status: 'cancelled' },
  { id: 6, transaction_number: 'TXN-006', type: 'adjustment', account: 'الصندوق', amount: 5000, date: '2025-01-10', payment_method: 'نقدي', reference: '', description: 'تسوية فرق', status: 'completed' },
];
const mockAccounts = [
  { id: 1, name: 'البنك الأهلي', type: 'بنكي', bank: 'البنك الأهلي السعودي', balance: 320000, currency: 'ريال' },
  { id: 2, name: 'بنك الراجحي', type: 'بنكي', bank: 'مصرف الراجحي', balance: 180000, currency: 'ريال' },
  { id: 3, name: 'الصندوق', type: 'نقدي', bank: '—', balance: 60000, currency: 'ريال' },
];
const mockCheques = [
  { id: 1, cheque_number: 'CHQ-001', bank: 'البنك الأهلي', amount: 75000, due_date: '2025-02-15', payer: 'شركة العمران', type: 'received', status: 'received' },
  { id: 2, cheque_number: 'CHQ-002', bank: 'بنك الراجحي', amount: 25000, due_date: '2025-01-20', payer: 'مؤسسة البناء', type: 'received', status: 'deposited' },
  { id: 3, cheque_number: 'CHQ-003', bank: 'البنك الأهلي', amount: 40000, due_date: '2025-01-10', payer: 'الشركة', type: 'issued', status: 'cleared' },
  { id: 4, cheque_number: 'CHQ-004', bank: 'بنك الراجحي', amount: 15000, due_date: '2025-01-25', payer: 'شركة التقنية', type: 'received', status: 'bounced' },
  { id: 5, cheque_number: 'CHQ-005', bank: 'البنك الأهلي', amount: 30000, due_date: '2025-03-01', payer: 'الشركة', type: 'issued', status: 'cancelled' },
];
const mockReconciliations = [
  { id: 1, account: 'البنك الأهلي', period: '2025-01', system_balance: 320000, actual_balance: 319500, difference: -500, status: 'completed' },
  { id: 2, account: 'بنك الراجحي', period: '2025-01', system_balance: 180000, actual_balance: 180000, difference: 0, status: 'completed' },
  { id: 3, account: 'الصندوق', period: '2025-01', system_balance: 60000, actual_balance: null, difference: null, status: 'pending' },
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

const Fld = ({ label, children }) => (
  <div className="space-y-1.5"><label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>{children}</div>
);

const inp = "w-full px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-800 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-500 transition";
const bB = "inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 shadow-sm";
const bP = `${bB} bg-gradient-to-l from-riadah-500 to-riadah-400 text-white hover:from-riadah-500 hover:to-riadah-500`;
const bS = `${bB} bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700`;
const bSuc = `${bB} bg-emerald-500 text-white hover:bg-emerald-600`;
const fmt = (n) => n.toLocaleString('ar-SA');

const typeMap = { receipt: { l: 'قبض', c: 'green', icon: ArrowDownCircle }, payment: { l: 'دفع', c: 'red', icon: ArrowUpCircle }, transfer: { l: 'تحويل', c: 'blue', icon: ArrowLeftRight }, adjustment: { l: 'تسوية', c: 'yellow', icon: CreditCard } };
const txnStatus = { completed: { l: 'مكتمل', c: 'green' }, pending: { l: 'معلق', c: 'yellow' }, cancelled: { l: 'ملغي', c: 'gray' } };
const chequeStatus = { received: { l: 'مستلم', c: 'green' }, deposited: { l: 'مودع', c: 'yellow' }, cleared: { l: 'مصروف', c: 'blue' }, bounced: { l: 'مرتجع', c: 'red' }, cancelled: { l: 'ملغي', c: 'gray' } };

// ─── Main ──────────────────────────────────────────────────────────
export default function PaymentsPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modals, setModals] = useState({ transaction: false, account: false, cheque: false, reconciliation: false });

  useEffect(() => { setTimeout(() => setLoading(false), 600); }, []);
  const toggle = (k) => setModals(p => ({ ...p, [k]: !p[k] }));
  const act = (msg) => toast.success(msg);

  const tabs = [
    { label: 'العمليات المالية', icon: Wallet },
    { label: 'الحسابات المالية', icon: CreditCard },
    { label: 'الشيكات', icon: FileCheck },
    { label: 'التسويات', icon: CheckSquare },
  ];

  return (
    <div dir="rtl" className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <div className="bg-gradient-to-l from-riadah-500 via-blue-600 to-riadah-700 text-white px-4 md:px-8 py-6 shadow-xl">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3"><Wallet className="w-7 h-7" /> إدارة المدفوعات</h1>
            <p className="text-blue-200 mt-1 text-sm">إدارة العمليات المالية والحسابات والشيكات والتسويات</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => act('تم التصدير')} className="bS !bg-white/15 !text-white hover:!bg-white/25"><Download className="w-4 h-4" /> تصدير</button>
            <button onClick={() => toggle('transaction')} className={bP}><Plus className="w-4 h-4" /> عملية جديدة</button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 space-y-6">
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="h-28 rounded-2xl bg-gray-200 dark:bg-gray-800 animate-pulse" />)}</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={ArrowDownCircle} label="إجمالي القبض" value={`${fmt(mockStats.total_receipts)} ر.س`} color="from-emerald-500 to-emerald-600" />
            <StatCard icon={ArrowUpCircle} label="إجمالي الدفع" value={`${fmt(mockStats.total_payments)} ر.س`} color="from-red-500 to-red-600" />
            <StatCard icon={ArrowLeftRight} label="التحويلات" value={`${fmt(mockStats.total_transfers)} ر.س`} color="from-riadah-400 to-riadah-500" />
            <StatCard icon={CreditCard} label="أرصدة الحسابات" value={`${fmt(mockStats.account_balances)} ر.س`} color="from-violet-500 to-violet-600" />
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
            {activeTab === 0 && <TransactionsTab search={search} setSearch={setSearch} toggle={toggle} act={act} />}
            {activeTab === 1 && <AccountsTab toggle={toggle} act={act} />}
            {activeTab === 2 && <ChequesTab search={search} setSearch={setSearch} toggle={toggle} act={act} />}
            {activeTab === 3 && <ReconciliationTab search={search} setSearch={setSearch} toggle={toggle} act={act} />}
          </div>
        </div>
      </div>

      {/* Transaction Modal */}
      <Modal isOpen={modals.transaction} onClose={() => toggle('transaction')} title="عملية مالية جديدة" wide>
        <form className="space-y-4" onSubmit={e => { e.preventDefault(); toggle('transaction'); act('تم إنشاء العملية بنجاح'); }}>
          <Fld label="نوع العملية">
            <select className={inp} id="txn-type">
              {Object.entries(typeMap).map(([k, v]) => <option key={k} value={k}>{v.l}</option>)}
            </select>
          </Fld>
          <div className="grid grid-cols-2 gap-4">
            <Fld label="الحساب"><select className={inp}>{mockAccounts.map(a => <option key={a.id}>{a.name}</option>)}</select></Fld>
            <Fld label="المبلغ"><input type="number" className={inp} placeholder="0.00" /></Fld>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Fld label="التاريخ"><input type="date" className={inp} /></Fld>
            <Fld label="طريقة الدفع"><select className={inp}><option>تحويل بنكي</option><option>نقدي</option><option>شيك</option><option>بطاقة ائتمان</option></select></Fld>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Fld label="المرجع"><input className={inp} placeholder="رقم المرجع" /></Fld>
            <Fld label="العميل / المورد"><input className={inp} placeholder="اسم الجهة" /></Fld>
          </div>
          <Fld label="الوصف"><textarea className={`${inp} h-20 resize-none`} placeholder="وصف العملية..." /></Fld>
          <div className="flex gap-3 pt-2"><button type="submit" className={bP}>إنشاء</button><button type="button" onClick={() => toggle('transaction')} className={bS}>إلغاء</button></div>
        </form>
      </Modal>

      {/* Account Modal */}
      <Modal isOpen={modals.account} onClose={() => toggle('account')} title="إنشاء حساب جديد">
        <form className="space-y-4" onSubmit={e => { e.preventDefault(); toggle('account'); act('تم إنشاء الحساب بنجاح'); }}>
          <Fld label="اسم الحساب"><input className={inp} placeholder="اسم الحساب" /></Fld>
          <div className="grid grid-cols-2 gap-4">
            <Fld label="النوع"><select className={inp}><option>بنكي</option><option>نقدي</option><option>محفظة إلكترونية</option></select></Fld>
            <Fld label="البنك"><input className={inp} placeholder="اسم البنك" /></Fld>
          </div>
          <Fld label="الرصيد الافتتاحي"><input type="number" className={inp} placeholder="0.00" /></Fld>
          <div className="flex gap-3 pt-2"><button type="submit" className={bP}>إنشاء</button><button type="button" onClick={() => toggle('account')} className={bS}>إلغاء</button></div>
        </form>
      </Modal>

      {/* Cheque Modal */}
      <Modal isOpen={modals.cheque} onClose={() => toggle('cheque')} title="تسجيل شيك">
        <form className="space-y-4" onSubmit={e => { e.preventDefault(); toggle('cheque'); act('تم تسجيل الشيك'); }}>
          <Fld label="رقم الشيك"><input className={inp} placeholder="CHQ-XXX" /></Fld>
          <div className="grid grid-cols-2 gap-4">
            <Fld label="البنك"><select className={inp}><option>البنك الأهلي</option><option>بنك الراجحي</option></select></Fld>
            <Fld label="المبلغ"><input type="number" className={inp} placeholder="0.00" /></Fld>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Fld label="تاريخ الاستحقاق"><input type="date" className={inp} /></Fld>
            <Fld label="النوع"><select className={inp}><option>مستلم</option><option>مصدر</option></select></Fld>
          </div>
          <Fld label="الجهة"><input className={inp} placeholder="اسم الجهة" /></Fld>
          <div className="flex gap-3 pt-2"><button type="submit" className={bP}>تسجيل</button><button type="button" onClick={() => toggle('cheque')} className={bS}>إلغاء</button></div>
        </form>
      </Modal>

      {/* Reconciliation Modal */}
      <Modal isOpen={modals.reconciliation} onClose={() => toggle('reconciliation')} title="تسوية حساب">
        <form className="space-y-4" onSubmit={e => { e.preventDefault(); toggle('reconciliation'); act('تمت التسوية بنجاح'); }}>
          <Fld label="الحساب"><select className={inp}>{mockAccounts.map(a => <option key={a.id}>{a.name}</option>)}</select></Fld>
          <div className="grid grid-cols-2 gap-4">
            <Fld label="الفترة"><input type="month" className={inp} /></Fld>
            <Fld label="الرصيد الفعلي"><input type="number" className={inp} placeholder="0.00" /></Fld>
          </div>
          <Fld label="ملاحظات"><textarea className={`${inp} h-20 resize-none`} placeholder="ملاحظات التسوية..." /></Fld>
          <div className="flex gap-3 pt-2"><button type="submit" className={bP}>تسوية</button><button type="button" onClick={() => toggle('reconciliation')} className={bS}>إلغاء</button></div>
        </form>
      </Modal>
    </div>
  );
}

// ─── Transactions Tab ──────────────────────────────────────────────
function TransactionsTab({ search, setSearch, toggle, act }) {
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const filtered = mockTransactions.filter(t =>
    (typeFilter === 'all' || t.type === typeFilter) &&
    (statusFilter === 'all' || t.status === statusFilter) &&
    (t.transaction_number.includes(search) || t.description.includes(search) || t.reference.includes(search))
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)} className={`${inp} !pr-10`} placeholder="بحث..." />
        </div>
        <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className={inp}>
          <option value="all">جميع الأنواع</option>
          {Object.entries(typeMap).map(([k, v]) => <option key={k} value={k}>{v.l}</option>)}
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className={inp}>
          <option value="all">جميع الحالات</option>
          {Object.entries(txnStatus).map(([k, v]) => <option key={k} value={k}>{v.l}</option>)}
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
            {['الرقم', 'النوع', 'الحساب', 'المبلغ', 'التاريخ', 'طريقة الدفع', 'المرجع', 'الوصف', 'الحالة'].map(h => <th key={h} className="px-3 py-3 text-right font-medium whitespace-nowrap">{h}</th>)}
          </tr></thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {filtered.map(t => {
              const T = typeMap[t.type];
              return (
                <tr key={t.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                  <td className="px-3 py-3 text-accent-500 font-medium">{t.transaction_number}</td>
                  <td className="px-3 py-3"><Badge color={T?.c}>{T?.l}</Badge></td>
                  <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{t.account}</td>
                  <td className={`px-3 py-3 font-bold ${t.type === 'receipt' ? 'text-emerald-600' : t.type === 'payment' ? 'text-red-600' : 'text-gray-800 dark:text-gray-200'}`}>
                    {t.type === 'receipt' ? '+' : t.type === 'payment' ? '-' : ''}{fmt(t.amount)}
                  </td>
                  <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{t.date}</td>
                  <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{t.payment_method}</td>
                  <td className="px-3 py-3 text-gray-500">{t.reference || '—'}</td>
                  <td className="px-3 py-3 text-gray-600 dark:text-gray-400 max-w-[150px] truncate">{t.description}</td>
                  <td className="px-3 py-3"><Badge color={txnStatus[t.status]?.c}>{txnStatus[t.status]?.l}</Badge></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Accounts Tab ──────────────────────────────────────────────────
function AccountsTab({ toggle, act }) {
  const typeColors = { بنكي: 'from-riadah-400 to-riadah-500', نقدي: 'from-emerald-500 to-emerald-600', 'محفظة إلكترونية': 'from-violet-500 to-violet-600' };
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => toggle('account')} className={bP}><Plus className="w-4 h-4" /> حساب جديد</button>
      </div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockAccounts.map(a => (
          <div key={a.id} className={`relative overflow-hidden rounded-2xl p-5 bg-gradient-to-br ${typeColors[a.type] || 'from-gray-500 to-gray-600'} text-white shadow-lg`}>
            <div className="absolute top-0 left-0 w-32 h-32 bg-white/10 rounded-full -translate-x-12 -translate-y-12" />
            <div className="absolute bottom-0 right-0 w-20 h-20 bg-white/5 rounded-full translate-x-8 translate-y-8" />
            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-lg">{a.name}</h3>
                <Badge color="white">{a.type}</Badge>
              </div>
              {a.bank !== '—' && <p className="text-sm opacity-80 mb-3">{a.bank}</p>}
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-xs opacity-70">الرصيد الحالي</p>
                  <p className="text-2xl font-bold mt-0.5">{fmt(a.balance)}</p>
                  <p className="text-xs opacity-60">{a.currency}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Cheques Tab ───────────────────────────────────────────────────
function ChequesTab({ search, setSearch, toggle, act }) {
  const [statusFilter, setStatusFilter] = useState('all');
  const filtered = mockCheques.filter(c =>
    (statusFilter === 'all' || c.status === statusFilter) &&
    (c.cheque_number.includes(search) || c.payer.includes(search) || c.bank.includes(search))
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)} className={`${inp} !pr-10`} placeholder="بحث..." />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className={inp}>
          <option value="all">جميع الحالات</option>
          {Object.entries(chequeStatus).map(([k, v]) => <option key={k} value={k}>{v.l}</option>)}
        </select>
        <button onClick={() => toggle('cheque')} className={bP}><Plus className="w-4 h-4" /> شيك جديد</button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
            {['رقم الشيك', 'البنك', 'المبلغ', 'تاريخ الاستحقاق', 'الجهة', 'النوع', 'الحالة', 'إجراءات'].map(h => <th key={h} className="px-3 py-3 text-right font-medium whitespace-nowrap">{h}</th>)}
          </tr></thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {filtered.map(c => (
              <tr key={c.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <td className="px-3 py-3 text-accent-500 font-medium">{c.cheque_number}</td>
                <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{c.bank}</td>
                <td className="px-3 py-3 font-bold text-gray-800 dark:text-gray-200">{fmt(c.amount)}</td>
                <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{c.due_date}</td>
                <td className="px-3 py-3 text-gray-600 dark:text-gray-400">{c.payer}</td>
                <td className="px-3 py-3"><Badge color={c.type === 'received' ? 'green' : 'violet'}>{c.type === 'received' ? 'مستلم' : 'مصدر'}</Badge></td>
                <td className="px-3 py-3"><Badge color={chequeStatus[c.status]?.c}>{chequeStatus[c.status]?.l}</Badge></td>
                <td className="px-3 py-3">
                  {c.status === 'received' && (
                    <button onClick={() => act('تم إيداع الشيك')} className="text-xs px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 text-amber-600 rounded-lg hover:bg-amber-100">إيداع</button>
                  )}
                  {c.status === 'deposited' && (
                    <button onClick={() => act('تم صرف الشيك')} className="text-xs px-3 py-1.5 bg-riadah-50 dark:bg-riadah-900/20 text-accent-500 rounded-lg hover:bg-riadah-100">صرف</button>
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

// ─── Reconciliation Tab ────────────────────────────────────────────
function ReconciliationTab({ search, setSearch, toggle, act }) {
  const filtered = mockReconciliations.filter(r => r.account.includes(search));
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)} className={`${inp} !pr-10`} placeholder="بحث..." />
        </div>
        <button onClick={() => toggle('reconciliation')} className={bP}><Plus className="w-4 h-4" /> تسوية جديدة</button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
            {['الحساب', 'الفترة', 'رصيد النظام', 'الرصيد الفعلي', 'الفرق', 'الحالة'].map(h => <th key={h} className="px-4 py-3 text-right font-medium">{h}</th>)}
          </tr></thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {filtered.map(r => (
              <tr key={r.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-800 dark:text-white">{r.account}</td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{r.period}</td>
                <td className="px-4 py-3 text-gray-800 dark:text-gray-200">{fmt(r.system_balance)}</td>
                <td className="px-4 py-3 text-gray-800 dark:text-gray-200">{r.actual_balance !== null ? fmt(r.actual_balance) : '—'}</td>
                <td className="px-4 py-3">
                  {r.difference !== null ? (
                    <span className={r.difference < 0 ? 'text-red-500 font-bold' : r.difference === 0 ? 'text-emerald-500 font-bold' : 'text-amber-500 font-bold'}>
                      {r.difference === 0 ? '✓ متطابق' : fmt(r.difference)}
                    </span>
                  ) : '—'}
                </td>
                <td className="px-4 py-3">
                  <Badge color={r.status === 'completed' ? 'green' : 'yellow'}>{r.status === 'completed' ? 'مكتمل' : 'معلق'}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
