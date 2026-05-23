/**
 * Export utilities for downloading files (Excel, CSV, etc.).
 * Provides a shared downloadBlob helper used across all list pages.
 */

/**
 * Download a Blob as a file with the given filename.
 * @param {Blob} blob - The file content as a Blob.
 * @param {string} filename - The name for the downloaded file (e.g. 'products.xlsx').
 */
export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Extract filename from Content-Disposition header.
 * @param {string} contentDisposition - The Content-Disposition header value.
 * @returns {string} The filename, or 'export.xlsx' as fallback.
 */
export function getFilenameFromHeader(contentDisposition) {
  if (!contentDisposition) return 'export.xlsx';
  const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
  if (match && match[1]) {
    let filename = match[1].replace(/['"]/g, '');
    // Handle RFC 5987 encoded filenames
    if (filename.startsWith('UTF-8')) {
      filename = decodeURIComponent(filename.replace(/^UTF-8''/, ''));
    }
    return filename || 'export.xlsx';
  }
  return 'export.xlsx';
}
