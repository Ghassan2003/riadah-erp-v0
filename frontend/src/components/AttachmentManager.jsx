/**
 * AttachmentManager - Reusable component for managing file attachments.
 * Supports: drag-and-drop upload, file type icons, image preview,
 * download, delete, bulk delete, file size formatting, and Arabic/English.
 *
 * Usage:
 *   <AttachmentManager
 *     contentType="sales.order"  // Django content type: app_label.model
 *     objectId={123}             // The ID of the related object
 *     allowedTypes={['pdf', 'doc', 'docx']}  // Optional: restrict types
 *     maxSize={50 * 1024 * 1024}              // Optional: max size in bytes
 *     category="contracts"                    // Optional: filter by category
 *   />
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Upload,
  FileText,
  FileSpreadsheet,
  FileImage,
  Archive,
  File,
  Download,
  Trash2,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  Paperclip,
  Eye,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';
import { attachmentsAPI } from '../api';
import ConfirmDialog from './ConfirmDialog';

// =============================================
// Constants
// =============================================

const ALL_ALLOWED_TYPES = [
  'pdf', 'doc', 'docx', 'xls', 'xlsx',
  'png', 'jpg', 'jpeg', 'gif', 'zip', 'txt',
];

const DEFAULT_MAX_SIZE = 50 * 1024 * 1024; // 50MB

// File type → icon mapping
const FILE_TYPE_ICONS = {
  pdf: { icon: FileText, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20' },
  doc: { icon: FileText, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20' },
  docx: { icon: FileText, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20' },
  xls: { icon: FileSpreadsheet, color: 'text-green-600', bg: 'bg-green-50 dark:bg-green-900/20' },
  xlsx: { icon: FileSpreadsheet, color: 'text-green-600', bg: 'bg-green-50 dark:bg-green-900/20' },
  png: { icon: FileImage, color: 'text-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
  jpg: { icon: FileImage, color: 'text-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
  jpeg: { icon: FileImage, color: 'text-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
  gif: { icon: FileImage, color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-900/20' },
  zip: { icon: Archive, color: 'text-yellow-600', bg: 'bg-yellow-50 dark:bg-yellow-900/20' },
  txt: { icon: File, color: 'text-gray-500', bg: 'bg-gray-50 dark:bg-gray-900/20' },
};

// Image extensions for preview
const IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif'];

// =============================================
// Helpers
// =============================================

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const value = bytes / Math.pow(1024, i);
  return `${value.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function getFileExtension(fileName) {
  if (!fileName || !fileName.includes('.')) return '';
  return fileName.split('.').pop().toLowerCase();
}

function getFileTypeInfo(ext) {
  return FILE_TYPE_ICONS[ext] || { icon: File, color: 'text-gray-500', bg: 'bg-gray-50 dark:bg-gray-900/20' };
}

function getAcceptString(allowedTypes) {
  return allowedTypes.map(t => `.${t}`).join(',');
}

// =============================================
// Component
// =============================================

export default function AttachmentManager({
  contentType,
  objectId,
  allowedTypes,
  maxSize = DEFAULT_MAX_SIZE,
  category = '',
  readOnly = false,
}) {
  const { t, isRTL } = useI18n();

  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Image preview modal
  const [previewImage, setPreviewImage] = useState(null);

  // Edit description
  const [editingId, setEditingId] = useState(null);
  const [editDescription, setEditDescription] = useState('');
  const [saving, setSaving] = useState(false);

  const fileInputRef = useRef(null);
  const allowed = allowedTypes || ALL_ALLOWED_TYPES;

  // =============================================
  // Fetch attachments
  // =============================================

  const fetchAttachments = useCallback(async () => {
    if (!contentType || !objectId) return;
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (category) params.category = category;
      const res = await attachmentsAPI.list(contentType, objectId, params);
      setAttachments(res.data.results || res.data || []);
    } catch (err) {
      setError(
        isRTL
          ? 'فشل في تحميل المرفقات'
          : 'Failed to load attachments'
      );
    } finally {
      setLoading(false);
    }
  }, [contentType, objectId, category, isRTL]);

  useEffect(() => {
    fetchAttachments();
  }, [fetchAttachments]);

  // =============================================
  // Upload
  // =============================================

  const validateFile = useCallback((file) => {
    const ext = getFileExtension(file.name);
    if (!ext || !allowed.includes(ext)) {
      return isRTL
        ? `نوع الملف "${ext || 'غير معروف'}" غير مدعوم. الأنواع المسموحة: ${allowed.join(', ')}`
        : `File type "${ext || 'unknown'}" not allowed. Allowed: ${allowed.join(', ')}`;
    }
    if (file.size > maxSize) {
      return isRTL
        ? `حجم الملف (${formatFileSize(file.size)}) يتجاوز الحد المسموح (${formatFileSize(maxSize)})`
        : `File size (${formatFileSize(file.size)}) exceeds limit (${formatFileSize(maxSize)})`;
    }
    if (file.size === 0) {
      return isRTL ? 'الملف فارغ' : 'File is empty';
    }
    return null;
  }, [allowed, maxSize, isRTL]);

  const uploadFiles = useCallback(async (files) => {
    if (!files || files.length === 0) return;

    for (const file of files) {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        setSuccess('');
        return;
      }
    }

    setUploading(true);
    setUploadProgress(0);
    setError('');
    setSuccess('');

    try {
      const totalFiles = files.length;
      for (let i = 0; i < totalFiles; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('content_type_str', contentType);
        formData.append('object_id', String(objectId));

        await attachmentsAPI.upload(formData);
        setUploadProgress(Math.round(((i + 1) / totalFiles) * 100));
      }

      setSuccess(
        isRTL
          ? `تم رفع ${totalFiles} مرفق(ات) بنجاح`
          : `${totalFiles} attachment(s) uploaded successfully`
      );
      fetchAttachments();
    } catch (err) {
      const msg = err.response?.data?.file?.[0]
        || err.response?.data?.error
        || (isRTL ? 'فشل في رفع الملف' : 'Failed to upload file');
      setError(msg);
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [contentType, objectId, validateFile, fetchAttachments, isRTL]);

  // =============================================
  // Drag and drop
  // =============================================

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!readOnly) setDragOver(true);
  }, [readOnly]);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    if (readOnly) return;
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) uploadFiles(files);
  }, [readOnly, uploadFiles]);

  const handleFileSelect = useCallback((e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) uploadFiles(files);
  }, [uploadFiles]);

  // =============================================
  // Download
  // =============================================

  const handleDownload = useCallback(async (attachment) => {
    try {
      const res = await attachmentsAPI.download(attachment.id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', attachment.file_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        isRTL ? 'فشل في تحميل الملف' : 'Failed to download file'
      );
    }
  }, [isRTL]);

  // =============================================
  // Delete
  // =============================================

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await attachmentsAPI.delete(deleteTarget.id);
      setAttachments(prev => prev.filter(a => a.id !== deleteTarget.id));
      setSuccess(isRTL ? 'تم حذف المرفق' : 'Attachment deleted');
    } catch {
      setError(isRTL ? 'فشل في حذف المرفق' : 'Failed to delete attachment');
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  }, [deleteTarget, isRTL]);

  // =============================================
  // Update description
  // =============================================

  const startEditing = useCallback((attachment) => {
    setEditingId(attachment.id);
    setEditDescription(attachment.description || '');
  }, []);

  const saveDescription = useCallback(async () => {
    if (!editingId) return;
    setSaving(true);
    try {
      await attachmentsAPI.update(editingId, { description: editDescription });
      setAttachments(prev =>
        prev.map(a => a.id === editingId ? { ...a, description: editDescription } : a)
      );
      setSuccess(isRTL ? 'تم تحديث الوصف' : 'Description updated');
    } catch {
      setError(isRTL ? 'فشل في تحديث الوصف' : 'Failed to update description');
    } finally {
      setSaving(false);
      setEditingId(null);
    }
  }, [editingId, editDescription, isRTL]);

  // =============================================
  // Auto-clear messages
  // =============================================

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(''), 4000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(''), 6000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // =============================================
  // Render
  // =============================================

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Paperclip className="w-5 h-5 text-gray-500" />
          <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200">
            {isRTL ? 'المرفقات' : 'Attachments'}
          </h3>
          {attachments.length > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
              {attachments.length}
            </span>
          )}
        </div>
        {!readOnly && (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="
              flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium
              rounded-lg text-white bg-primary hover:bg-primary/90
              dark:bg-accent-500 dark:hover:bg-accent-600
              transition-colors disabled:opacity-50 disabled:cursor-not-allowed
            "
          >
            <Upload className="w-4 h-4" />
            {isRTL ? 'رفع ملف' : 'Upload'}
          </button>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={getAcceptString(allowed)}
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Drag-and-drop zone */}
      {!readOnly && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer
            ${dragOver
              ? 'border-primary bg-primary/5 dark:border-accent-500 dark:bg-accent-500/10'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }
          `}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className={`w-8 h-8 mx-auto mb-2 ${dragOver ? 'text-primary dark:text-accent-400' : 'text-gray-400 dark:text-gray-500'}`} />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {isRTL
              ? 'اسحب الملفات وأفلتها هنا أو انقر للاختيار'
              : 'Drag & drop files here or click to browse'}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            {isRTL
              ? `الأنواع المسموحة: ${allowed.join(', ')} — الحد الأقصى: ${formatFileSize(maxSize)}`
              : `Allowed: ${allowed.join(', ')} — Max: ${formatFileSize(maxSize)}`
            }
          </p>
        </div>
      )}

      {/* Upload progress */}
      {uploading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-300 flex items-center gap-1.5">
              <Loader2 className="w-4 h-4 animate-spin text-primary dark:text-accent-400" />
              {isRTL ? 'جارٍ الرفع...' : 'Uploading...'}
            </span>
            <span className="text-gray-500">{uploadProgress}%</span>
          </div>
          <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary dark:bg-accent-500 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Success / Error messages */}
      {success && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 text-sm">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError('')} className="flex-shrink-0 hover:opacity-70">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Attachments list */}
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : attachments.length === 0 ? (
        <div className="text-center py-8 text-gray-400 dark:text-gray-500">
          <Paperclip className="w-10 h-10 mx-auto mb-2 opacity-40" />
          <p className="text-sm">
            {isRTL ? 'لا توجد مرفقات' : 'No attachments'}
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {attachments.map((attachment) => {
            const ext = getFileExtension(attachment.file_name);
            const typeInfo = getFileTypeInfo(ext);
            const TypeIcon = typeInfo.icon;
            const isImage = IMAGE_EXTENSIONS.includes(ext);

            return (
              <div
                key={attachment.id}
                className="
                  flex items-center gap-3 p-3 rounded-lg border
                  border-gray-100 dark:border-gray-700
                  bg-white dark:bg-gray-800
                  hover:shadow-sm transition-shadow
                "
              >
                {/* File icon or image preview */}
                {isImage && attachment.file_url ? (
                  <div
                    className="w-10 h-10 rounded-lg overflow-hidden flex-shrink-0 cursor-pointer bg-gray-100 dark:bg-gray-700"
                    onClick={() => setPreviewImage(attachment.file_url)}
                  >
                    <img
                      src={attachment.file_url}
                      alt={attachment.file_name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${typeInfo.bg}`}>
                    <TypeIcon className={`w-5 h-5 ${typeInfo.color}`} />
                  </div>
                )}

                {/* File info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                      {attachment.file_name}
                    </p>
                    {isImage && attachment.file_url && (
                      <button
                        onClick={() => setPreviewImage(attachment.file_url)}
                        className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title={isRTL ? 'معاينة' : 'Preview'}
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500">
                    <span className="uppercase font-medium">{ext}</span>
                    <span>·</span>
                    <span>{formatFileSize(attachment.file_size)}</span>
                    {attachment.description && (
                      <>
                        <span>·</span>
                        <span className="truncate max-w-[150px]">{attachment.description}</span>
                      </>
                    )}
                    {attachment.uploaded_by_name && (
                      <>
                        <span>·</span>
                        <span>{attachment.uploaded_by_name}</span>
                      </>
                    )}
                  </div>

                  {/* Edit description inline */}
                  {editingId === attachment.id && (
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <input
                        type="text"
                        value={editDescription}
                        onChange={(e) => setEditDescription(e.target.value)}
                        placeholder={isRTL ? 'الوصف...' : 'Description...'}
                        className="
                          flex-1 text-xs px-2 py-1 rounded border
                          border-gray-200 dark:border-gray-600
                          bg-white dark:bg-gray-700
                          text-gray-700 dark:text-gray-300
                          focus:outline-none focus:ring-1 focus:ring-primary dark:focus:ring-accent-500
                        "
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') saveDescription();
                          if (e.key === 'Escape') setEditingId(null);
                        }}
                        autoFocus
                      />
                      <button
                        onClick={saveDescription}
                        disabled={saving}
                        className="text-xs px-2 py-1 rounded bg-primary dark:bg-accent-500 text-white hover:opacity-90 disabled:opacity-50"
                      >
                        {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : '✓'}
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="text-xs px-1.5 py-1 text-gray-400 hover:text-gray-600"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Actions */}
                {!readOnly && (
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                      onClick={() => startEditing(attachment)}
                      className="
                        p-1.5 rounded-md text-gray-400 hover:text-gray-600
                        hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-300
                        transition-colors
                      "
                      title={isRTL ? 'تعديل الوصف' : 'Edit description'}
                    >
                      <FileText className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDownload(attachment)}
                      className="
                        p-1.5 rounded-md text-gray-400 hover:text-primary
                        dark:hover:text-accent-400
                        hover:bg-gray-100 dark:hover:bg-gray-700
                        transition-colors
                      "
                      title={isRTL ? 'تحميل' : 'Download'}
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setDeleteTarget(attachment)}
                      className="
                        p-1.5 rounded-md text-gray-400 hover:text-red-500
                        hover:bg-red-50 dark:hover:bg-red-900/20
                        transition-colors
                      "
                      title={isRTL ? 'حذف' : 'Delete'}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title={isRTL ? 'حذف المرفق' : 'Delete Attachment'}
        message={
          deleteTarget
            ? (isRTL
                ? `هل أنت متأكد من حذف "${deleteTarget.file_name}"؟ لا يمكن التراجع عن هذا الإجراء.`
                : `Are you sure you want to delete "${deleteTarget.file_name}"? This action cannot be undone.`
              )
            : ''
        }
        confirmText={isRTL ? 'حذف' : 'Delete'}
        cancelText={isRTL ? 'إلغاء' : 'Cancel'}
        loading={deleting}
      />

      {/* Image preview modal */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setPreviewImage(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh]">
            <button
              onClick={() => setPreviewImage(null)}
              className="
                absolute -top-3 -right-3 z-10
                w-8 h-8 rounded-full bg-white dark:bg-gray-800
                flex items-center justify-center
                shadow-lg text-gray-600 hover:text-gray-900
                dark:text-gray-300 dark:hover:text-white
                transition-colors
              "
            >
              <X className="w-4 h-4" />
            </button>
            <img
              src={previewImage}
              alt="Preview"
              className="max-w-full max-h-[85vh] object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </div>
  );
}
