/**
 * System Settings Page - Comprehensive company, currency, and auto-numbering settings.
 */

import { useState, useEffect } from 'react';
import {
  Settings, Building2, DollarSign, Hash, Mail, Globe,
  Save, RefreshCw, Eye, Copy, CheckCircle2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { settingsAPI } from '../api';
import { useI18n } from '../i18n/I18nContext';

export default function SystemSettingsPage() {
  const { t, locale } = useI18n();
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('company');
  const [preview, setPreview] = useState(null);
  const [changedFields, setChangedFields] = useState(new Set());
  const [copied, setCopied] = useState(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await settingsAPI.get();
      setSettings(res.data);
    } catch {
      toast.error(t('error') + ': ' + t('loadFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    try {
      const res = await settingsAPI.numberPreview();
      setPreview(res.data);
    } catch {
      toast.error(t('error') + ': ' + t('loadFailed'));
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const allSettings = {};
      Object.values(settings).forEach(group => {
        if (group.settings) {
          Object.entries(group.settings).forEach(([key, value]) => {
            allSettings[key] = value;
          });
        }
      });
      await settingsAPI.update({ settings: allSettings });
      toast.success(t('settingsSaved'));
      setChangedFields(new Set());
    } catch {
      toast.error(t('error') + ': ' + t('save'));
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (group, key, value) => {
    setSettings(prev => ({
      ...prev,
      [group]: {
        ...prev[group],
        settings: {
          ...prev[group].settings,
          [key]: value,
        },
      },
    }));
    setChangedFields(prev => new Set([...prev, key]));
  };

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  const tabs = [
    { key: 'company', label: t('companySettings'), icon: Building2 },
    { key: 'financial', label: t('currencySettings'), icon: DollarSign },
    { key: 'numbering', label: t('numberingSettings'), icon: Hash },
    { key: 'email', label: t('emailSettings'), icon: Mail },
    { key: 'general', label: t('generalSettings'), icon: Globe },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-accent-500" />
      </div>
    );
  }

  const companyFields = [
    { key: 'company_name', label: t('companyName'), type: 'text', placeholder: t('companyName') },
    { key: 'company_address', label: t('companyAddress'), type: 'text', placeholder: t('companyAddress') },
    { key: 'company_phone', label: t('companyPhone'), type: 'text', placeholder: '+966500000000' },
    { key: 'company_email', label: t('companyEmail'), type: 'email', placeholder: 'info@company.com' },
    { key: 'company_website', label: t('companyWebsite'), type: 'text', placeholder: 'https://company.com' },
    { key: 'company_cr_number', label: t('crNumber'), type: 'text', placeholder: '1234567890' },
    { key: 'company_vat_number', label: t('taxNumber'), type: 'text', placeholder: '300000000000003' },
    { key: 'company_fax', label: t('fax'), type: 'text', placeholder: '+966123456789' },
  ];

  const financialFields = [
    { key: 'default_currency', label: t('defaultCurrency'), type: 'select', options: [
      { value: 'SAR', label: t('sar') },
      { value: 'AED', label: t('aed') },
      { value: 'USD', label: t('usd') },
      { value: 'EUR', label: t('eur') },
      { value: 'KWD', label: t('kwd') },
      { value: 'QAR', label: t('qar') },
      { value: 'BHD', label: t('bhd') },
      { value: 'OMR', label: t('omr') },
      { value: 'EGP', label: t('egp') },
    ]},
    { key: 'currency_symbol', label: t('currencySymbol'), type: 'text', placeholder: t('currencySymbol') },
    { key: 'decimal_places', label: t('decimalPlaces'), type: 'select', options: [
      { value: '0', label: '0' }, { value: '2', label: '2' }, { value: '3', label: '3' },
    ]},
    { key: 'fiscal_year_start', label: t('fiscalYearStart'), type: 'select', options: [
      { value: '01', label: t('january') }, { value: '04', label: t('april') },
      { value: '07', label: t('july') }, { value: '10', label: t('october') },
    ]},
    { key: 'tax_rate', label: t('taxRate'), type: 'number', placeholder: '15' },
  ];

  const numberingFields = [
    { key: 'order_prefix', label: t('orderPrefix'), type: 'text', placeholder: 'SO' },
    { key: 'purchase_prefix', label: t('purchasePrefix'), type: 'text', placeholder: 'PO' },
    { key: 'invoice_prefix', label: t('invoicePrefix'), type: 'text', placeholder: 'INV' },
    { key: 'journal_prefix', label: t('journalPrefix'), type: 'text', placeholder: 'JE' },
    { key: 'employee_prefix', label: t('employeePrefix'), type: 'text', placeholder: 'EMP' },
    { key: 'product_prefix', label: t('productPrefix'), type: 'text', placeholder: 'PRD' },
    { key: 'next_order_number', label: t('nextOrderNumber'), type: 'number', placeholder: '1001' },
    { key: 'next_purchase_number', label: t('nextPurchaseNumber'), type: 'number', placeholder: '1001' },
    { key: 'next_invoice_number', label: t('nextInvoiceNumber'), type: 'number', placeholder: '1001' },
    { key: 'next_journal_number', label: t('nextJournalNumber'), type: 'number', placeholder: '1001' },
  ];

  const emailFields = [
    { key: 'smtp_host', label: t('smtpServer'), type: 'text', placeholder: 'smtp.gmail.com' },
    { key: 'smtp_port', label: t('port'), type: 'text', placeholder: '587' },
    { key: 'smtp_user', label: t('smtpUser'), type: 'text', placeholder: 'user@gmail.com' },
    { key: 'email_from', label: t('emailFrom'), type: 'email', placeholder: 'noreply@company.com' },
    { key: 'admin_email', label: t('adminEmail'), type: 'email', placeholder: 'admin@company.com' },
  ];

  const generalFields = [
    { key: 'system_language', label: t('systemLanguage'), type: 'select', options: [
      { value: 'ar', label: t('arabic') }, { value: 'en', label: t('english') },
    ]},
    { key: 'timezone', label: t('timezone'), type: 'select', options: [
      { value: 'Asia/Riyadh', label: t('riyadhTimezone') },
      { value: 'Asia/Dubai', label: t('dubaiTimezone') },
      { value: 'Africa/Cairo', label: t('cairoTimezone') },
    ]},
    { key: 'date_format', label: t('dateFormat'), type: 'select', options: [
      { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
      { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
      { value: 'DD-MM-YYYY', label: 'DD-MM-YYYY' },
    ]},
    { key: 'items_per_page', label: t('itemsPerPage'), type: 'select', options: [
      { value: '10', label: '10' }, { value: '20', label: '20' },
      { value: '50', label: '50' }, { value: '100', label: '100' },
    ]},
  ];

  const fieldsMap = {
    company: companyFields,
    financial: financialFields,
    numbering: numberingFields,
    email: emailFields,
    general: generalFields,
  };

  const renderField = (field, groupKey) => {
    const value = settings?.[groupKey]?.settings?.[field.key] || '';
    const isChanged = changedFields.has(field.key);

    return (
      <div key={field.key} className="space-y-1">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {field.label}
          {isChanged && <span className="text-accent-500 dark:text-accent-400 mr-1 text-xs">({t('modified')})</span>}
        </label>
        {field.type === 'select' ? (
          <select value={value}
            onChange={(e) => updateSetting(groupKey, field.key, e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500 focus:border-accent-500">
            {field.options?.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        ) : (
          <input
            type={field.type}
            value={value}
            onChange={(e) => updateSetting(groupKey, field.key, e.target.value)}
            placeholder={field.placeholder}
            className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
          />
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Settings className="w-7 h-7 text-accent-500" />
            {t('settingsTitle')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('settingsDesc')}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchSettings} className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm">
            <RefreshCw className="w-4 h-4" /> {t('refresh')}
          </button>
          <button onClick={handleSave} disabled={saving || changedFields.size === 0}
            className="flex items-center gap-2 px-4 py-2 bg-riadah-500 text-white rounded-lg hover:bg-riadah-600 dark:hover:bg-riadah-800 disabled:opacity-50 transition-colors text-sm">
            {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {t('save')} {changedFields.size > 0 && `(${changedFields.size})`}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 p-1 rounded-xl overflow-x-auto">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.key
                  ? 'bg-white dark:bg-gray-600 text-riadah-700 dark:text-accent-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100'
              }`}>
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Settings Form */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {(fieldsMap[activeTab] || []).map(field => renderField(field, activeTab))}
        </div>
      </div>

      {/* Numbering Preview */}
      {activeTab === 'numbering' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Eye className="w-5 h-5" /> {t('numberPreview')}
            </h3>
            <button onClick={handlePreview} className="flex items-center gap-2 px-3 py-1.5 bg-riadah-50 dark:bg-riadah-900/20 text-riadah-700 dark:text-accent-400 rounded-lg hover:bg-riadah-100 dark:hover:bg-riadah-900/40 text-sm">
              <RefreshCw className="w-3.5 h-3.5" /> {t('refresh')}
            </button>
          </div>
          {preview && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(preview).map(([key, value]) => {
                const labels = { order: t('salesOrder'), purchase: t('purchaseOrder'), invoice: t('invoice'), journal: t('journalEntry') };
                return (
                  <div key={key} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{labels[key]}</p>
                      <p className="font-mono text-sm font-bold text-gray-900 dark:text-gray-100 mt-1">{value}</p>
                    </div>
                    <button onClick={() => copyToClipboard(value, key)}
                      className="p-1.5 text-gray-400 dark:text-gray-500 hover:text-accent-500 dark:hover:text-accent-400 hover:bg-riadah-50 dark:hover:bg-riadah-900/30 rounded-lg transition-colors">
                      {copied === key ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
