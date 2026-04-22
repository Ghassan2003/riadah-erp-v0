/**
 * Documents page - file upload and document management.
 * Features: drag & drop upload, document list with filters, download, delete.
 * Supports dark mode and i18n.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { documentsAPI } from '../api';
import { useI18n } from '../i18n/I18nContext';
import {
  Upload, FileText, Image, FileSpreadsheet, File,
  Download, Trash2, Search, Filter, Loader2,
  AlertTriangle, X, FileUp, FolderOpen,
  ChevronLeft, ChevronRight,
} from 'lucide-react';
import toast from 'react-hot-toast';

const FILE_TYPE_CONFIG_MAP = {
  pdf:         { labelKey: 'pdf',         color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',         icon: FileText },
  image:       { labelKey: 'image',       color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300', icon: Image },
  spreadsheet: { labelKey: 'spreadsheet', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300', icon: FileSpreadsheet },
  document:    { labelKey: 'document',    color: 'bg-riadah-100 text-riadah-700 dark:bg-riadah-900/30 dark:text-accent-300',       icon: FileText },
  default:     { labelKey: 'file',        color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',       icon: File },
};

function getFileType(filename) {
  const ext = (filename || '').split('.').pop().toLowerCase();
  if (['pdf'].includes(ext)) return 'pdf';
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return 'image';
  if (['xlsx', 'xls', 'csv'].includes(ext)) return 'spreadsheet';
  if (['doc', 'docx', 'txt', 'rtf'].includes(ext)) return 'document';
  return 'default';
}

export default function DocumentsPage() {
  const { t } = useI18n();
  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Delete confirmation
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const fetchDocuments = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = {
        page,
        search: searchTerm || undefined,
        category: categoryFilter || undefined,
      };
      const response = await documentsAPI.list(params);
      const data = response.data;
      setDocuments(data.results || (Array.isArray(data) ? data : []));
      setTotalCount(data.count || data.length || 0);
      setCurrentPage(page);
    } catch {
      toast.error(t('failedLoadingDocuments'));
    } finally {
      setLoading(false);
    }
  }, [searchTerm, categoryFilter, t]);

  const fetchCategories = async () => {
    try {
      const response = await documentsAPI.categories();
      setCategories(Array.isArray(response.data) ? response.data : []);
    } catch { /* silent */ }
  };

  useEffect(() => {
    fetchDocuments(1);
    fetchCategories();
  }, [fetchDocuments]);

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  // File upload handling
  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', file.name);
        await documentsAPI.upload(formData);
      }
      toast.success(t('documentUploaded'));
      fetchDocuments(1);
    } catch (error) {
      toast.error(error.response?.data?.error || t('failedUploadingDocument'));
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
      e.target.value = '';
    }
  };

  // Download
  const handleDownload = async (doc) => {
    try {
      const response = await documentsAPI.download(doc.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.file_name || doc.title || 'document');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error(t('failedDownloadingDocument'));
    }
  };

  // Delete
  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleteLoading(true);
    try {
      await documentsAPI.delete(deleteConfirm.id);
      toast.success(t('documentDeleted'));
      setDeleteConfirm(null);
      fetchDocuments(currentPage);
    } catch (error) {
      toast.error(error.response?.data?.error || t('failedDeletingDocument'));
    } finally {
      setDeleteLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return `0 ${t('bytes')}`;
    const sizes = [t('bytes'), t('kilobytes'), t('megabytes'), t('gigabytes')];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('manageDocuments')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('manageDocumentsDesc')}</p>
        </div>
      </div>

      {/* Upload area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          dragActive
            ? 'border-accent-500 bg-riadah-50 dark:bg-riadah-900/20'
            : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-gray-400 dark:hover:border-gray-500'
        } ${uploading ? 'opacity-60 pointer-events-none' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileInput}
          className="hidden"
        />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-10 h-10 animate-spin text-accent-500" />
            <p className="text-gray-600 dark:text-gray-300 font-medium">{t('uploadingFiles')}</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-xl bg-riadah-50 dark:bg-riadah-900/20 flex items-center justify-center">
              <FileUp className="w-7 h-7 text-accent-500" />
            </div>
            <div>
              <p className="text-gray-700 dark:text-gray-300 font-medium">{t('dragFilesHere')}</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-accent-500 dark:text-accent-400 hover:text-accent-600 dark:hover:text-accent-300 font-medium underline mt-1"
              >
                {t('chooseFilesToUpload')}
              </button>
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500">{t('supportedFormats')}</p>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={handleSearch}
            placeholder={t('searchDocuments')}
            className="w-full pr-10 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white"
          />
        </div>
        <div className="relative">
          <Filter className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          <select
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value); setCurrentPage(1); }}
            className="appearance-none pr-9 pl-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 bg-white text-sm"
          >
            <option value="">{t('allCategories')}</option>
            {categories.map((cat, i) => (
              <option key={i} value={cat.id || cat}>{typeof cat === 'object' ? cat.name : cat}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Documents list */}
      <div className="space-y-3">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700">
            <FolderOpen className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
            <p className="text-lg font-medium">{t('noDocuments')}</p>
            <p className="text-sm mt-1">
              {searchTerm ? t('noResults') : t('uploadNewDocuments')}
            </p>
          </div>
        ) : (
          <>
            {documents.map((doc) => {
              const fileType = getFileType(doc.file_name || doc.title || '');
              const typeConfig = FILE_TYPE_CONFIG_MAP[fileType] || FILE_TYPE_CONFIG_MAP.default;
              const TypeIcon = typeConfig.icon;
              return (
                <div
                  key={doc.id}
                  className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    {/* File type icon */}
                    <div className={`w-12 h-12 rounded-xl ${typeConfig.color} flex items-center justify-center flex-shrink-0`}>
                      <TypeIcon className="w-6 h-6" />
                    </div>
                    {/* File info */}
                    <div className="min-w-0">
                      <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{doc.title || doc.file_name || t('document')}</p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${typeConfig.color}`}>
                          {t(typeConfig.labelKey)}
                        </span>
                        {doc.file_size && <span>{formatFileSize(doc.file_size)}</span>}
                        {doc.uploaded_at && <span>{doc.uploaded_at}</span>}
                        {doc.uploaded_by && <span>{t('by')}: {doc.uploaded_by}</span>}
                      </div>
                    </div>
                  </div>
                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleDownload(doc)}
                      className="p-2 text-accent-500 hover:bg-riadah-50 dark:text-accent-400 dark:hover:bg-riadah-900/20 rounded-lg transition-colors"
                      title={t('download')}
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(doc)}
                      className="p-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                      title={t('delete')}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t('showing')} {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalCount)} {t('of')} {totalCount}
                </p>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => fetchDocuments(currentPage - 1)}
                    disabled={currentPage <= 1}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                  <span className="px-3 py-1 text-sm font-medium text-accent-500 dark:text-accent-400 bg-riadah-50 dark:bg-riadah-900/20 rounded-lg">
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    onClick={() => fetchDocuments(currentPage + 1)}
                    disabled={currentPage >= totalPages}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Delete confirmation modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50 dark:bg-black/70" onClick={() => setDeleteConfirm(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 w-full max-w-sm p-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">{t('confirm')}</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                {t('confirmDeleteDocument')} <span className="font-semibold text-gray-900 dark:text-gray-100"> "{deleteConfirm.title || deleteConfirm.file_name}"</span>?
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">{t('permanentDeleteNote')}</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDelete}
                  disabled={deleteLoading}
                  className="flex-1 bg-red-600 dark:bg-red-700 hover:bg-red-700 dark:hover:bg-red-800 disabled:bg-red-400 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {deleteLoading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('deleting')}...</>
                  ) : (
                    <><Trash2 className="w-4 h-4" /> {t('deleteDocument')}</>
                  )}
                </button>
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  {t('cancel')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
