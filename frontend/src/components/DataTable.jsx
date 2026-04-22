/**
 * DataTable - Advanced, reusable data table component.
 * Supports: search, filtering, sorting, pagination, row selection.
 * Fully i18n-aware with RTL/LTR and dark mode support.
 */

import { useState, useMemo, useEffect } from 'react';
import {
  Search, ChevronUp, ChevronDown, ChevronsLeft, ChevronsRight,
  ChevronLeft, ChevronRight, Filter, X, ArrowUpDown,
} from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

export default function DataTable({
  data = [],
  columns = [],
  searchable = true,
  searchPlaceholder = '',
  searchKeys = [],
  pageSize = 20,
  pageSizeOptions = [10, 20, 50, 100],
  onSelectionChange,
  actions,
  emptyMessage,
  emptyIcon: EmptyIcon,
  striped = true,
  hoverable = true,
  compact = false,
  className = '',
  headerActions,
  footerExtra,
}) {
  const { t, isRTL } = useI18n();

  const [searchQuery, setSearchQuery] = useState('');
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(pageSize);
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [filterOpen, setFilterOpen] = useState(false);

  // Resolve translatable defaults
  const resolvedPlaceholder = searchPlaceholder || t('search');
  const resolvedEmptyMessage = emptyMessage || t('noData');

  // Reset page when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  // Determine current locale for locale-aware sorting
  const sortLocale = isRTL ? 'ar' : 'en';

  // Filter and sort data
  const processedData = useMemo(() => {
    let result = [...data];

    // Search
    if (searchQuery && searchKeys.length > 0) {
      const query = searchQuery.toLowerCase();
      result = result.filter(row =>
        searchKeys.some(key => {
          const value = getNestedValue(row, key);
          return value != null && String(value).toLowerCase().includes(query);
        })
      );
    }

    // Sort
    if (sortColumn) {
      result.sort((a, b) => {
        const aVal = getNestedValue(a, sortColumn);
        const bVal = getNestedValue(b, sortColumn);

        if (aVal == null) return 1;
        if (bVal == null) return -1;

        const aStr = String(aVal).toLowerCase();
        const bStr = String(bVal).toLowerCase();

        // Try numeric comparison
        const aNum = parseFloat(aStr);
        const bNum = parseFloat(bStr);
        if (!isNaN(aNum) && !isNaN(bNum)) {
          return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
        }

        return sortDirection === 'asc'
          ? aStr.localeCompare(bStr, sortLocale)
          : bStr.localeCompare(aStr, sortLocale);
      });
    }

    return result;
  }, [data, searchQuery, sortColumn, sortDirection, searchKeys, sortLocale]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(processedData.length / rowsPerPage));
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const startIndex = (safeCurrentPage - 1) * rowsPerPage;
  const paginatedData = processedData.slice(startIndex, startIndex + rowsPerPage);

  // Selection
  const allSelected = paginatedData.length > 0 && paginatedData.every(row => selectedRows.has(row.id));
  const someSelected = paginatedData.some(row => selectedRows.has(row.id)) && !allSelected;

  const toggleAll = () => {
    const newSet = new Set(selectedRows);
    if (allSelected) {
      paginatedData.forEach(row => newSet.delete(row.id));
    } else {
      paginatedData.forEach(row => newSet.add(row.id));
    }
    setSelectedRows(newSet);
    onSelectionChange?.(newSet);
  };

  const toggleRow = (id) => {
    const newSet = new Set(selectedRows);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedRows(newSet);
    onSelectionChange?.(newSet);
  };

  // Sort handler
  const handleSort = (key) => {
    if (!key) return;
    if (sortColumn === key) {
      setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(key);
      setSortDirection('asc');
    }
  };

  // RTL-aware icon classes for search
  const searchIconPos = isRTL ? 'right-3' : 'left-3';
  const clearIconPos = isRTL ? 'left-3' : 'right-3';
  const inputPaddingIcon = isRTL ? 'pr-9 pl-3' : 'pl-9 pr-3';
  const inputPaddingWithClear = isRTL ? 'pr-9 pl-9' : 'pl-9 pr-9';

  // RTL-aware pagination icons:
  // RTL: right = beginning → ChevronsRight = first, ChevronRight = prev
  // LTR: left = beginning → ChevronsLeft = first, ChevronLeft = prev
  const FirstPageIcon = isRTL ? ChevronsRight : ChevronsLeft;
  const PrevPageIcon = isRTL ? ChevronRight : ChevronLeft;
  const NextPageIcon = isRTL ? ChevronLeft : ChevronRight;
  const LastPageIcon = isRTL ? ChevronsLeft : ChevronsRight;

  // Stagger animation style for rows
  const rowStyle = (idx) => ({
    animation: 'dataTableFadeIn 0.25s ease-out both',
    animationDelay: `${idx * 30}ms`,
  });

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden transition-colors duration-200 ${className}`}
    >
      {/* ──── Header with search & actions ──── */}
      {(searchable || headerActions) && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex flex-wrap gap-3 items-center">
            {searchable && (
              <div className="relative flex-1 min-w-[200px]">
                <Search
                  className={`absolute ${searchIconPos} top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500 pointer-events-none`}
                />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={resolvedPlaceholder}
                  className={`w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400 rounded-lg ${searchQuery ? inputPaddingWithClear : inputPaddingIcon} py-2 text-sm focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors`}
                  dir="auto"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className={`absolute ${clearIconPos} top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors`}
                    title={t('clearSearch')}
                    aria-label={t('clearSearch')}
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
            {headerActions && <div className="flex gap-2">{headerActions}</div>}
          </div>
        </div>
      )}

      {/* ──── Table ──── */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/70">
              {onSelectionChange && (
                <th className="px-4 py-3 w-10">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(el) => { if (el) el.indeterminate = someSelected; }}
                    onChange={toggleAll}
                    className="rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
                  />
                </th>
              )}
              {columns.map((col) => {
                const isSorted = sortColumn === col.key;
                return (
                  <th
                    key={col.key}
                    onClick={() => col.sortable !== false && handleSort(col.key)}
                    className={`px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider transition-colors whitespace-nowrap ${
                      col.sortable !== false
                        ? 'cursor-pointer hover:text-gray-700 dark:hover:text-gray-200'
                        : ''
                    } ${
                      col.align === 'center'
                        ? 'text-center'
                        : col.align === 'left'
                          ? 'text-left'
                          : 'text-right'
                    }`}
                  >
                    <div className="flex items-center gap-1.5">
                      {typeof col.header === 'function' ? col.header() : col.label || col.key}
                      {col.sortable !== false && (
                        <span className="text-gray-400 dark:text-gray-500">
                          {isSorted
                            ? sortDirection === 'asc'
                              ? <ChevronUp className="w-3.5 h-3.5 text-accent-500" />
                              : <ChevronDown className="w-3.5 h-3.5 text-accent-500" />
                            : <ArrowUpDown className="w-3 h-3" />}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
              {actions && (
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider text-center whitespace-nowrap">
                  {t('actions')}
                </th>
              )}
            </tr>
          </thead>

          <tbody
            className={`divide-y divide-gray-100 dark:divide-gray-700 ${
              striped ? 'even:bg-gray-50/50 dark:even:bg-gray-700/30' : ''
            }`}
          >
            {paginatedData.length > 0 ? (
              paginatedData.map((row, idx) => (
                <tr
                  key={row.id || idx}
                  style={rowStyle(idx)}
                  className={`transition-all duration-150 hover:bg-riadah-50/50 dark:hover:bg-riadah-900/20 ${
                    selectedRows.has(row.id)
                      ? 'bg-riadah-50/80 dark:bg-riadah-900/30'
                      : ''
                  }`}
                >
                  {onSelectionChange && (
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedRows.has(row.id)}
                        onChange={() => toggleRow(row.id)}
                        className="rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
                      />
                    </td>
                  )}
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`px-4 py-3 text-sm dark:text-gray-300 transition-colors ${
                        col.align === 'center'
                          ? 'text-center'
                          : col.align === 'left'
                            ? 'text-left'
                            : 'text-right'
                      } ${compact ? 'py-2' : ''}`}
                    >
                      {col.render
                        ? col.render(getNestedValue(row, col.key), row)
                        : <span>{getNestedValue(row, col.key) ?? '-'}</span>}
                    </td>
                  ))}
                  {actions && (
                    <td className="px-4 py-3">
                      <div className="flex gap-1 justify-center">{actions(row)}</div>
                    </td>
                  )}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={
                    columns.length + (onSelectionChange ? 1 : 0) + (actions ? 1 : 0)
                  }
                  className="px-4 py-12 text-center"
                >
                  <div className="text-gray-400 dark:text-gray-500">
                    {EmptyIcon && <EmptyIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />}
                    <p className="text-sm">{resolvedEmptyMessage}</p>
                    {searchQuery && (
                      <button
                        onClick={() => setSearchQuery('')}
                        className="text-xs text-accent-500 hover:text-accent-500 dark:text-accent-400 dark:hover:text-accent-300 mt-1 transition-colors"
                      >
                        {t('clearSearch')}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ──── Pagination & Footer ──── */}
      {processedData.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
          {/* Showing info & page-size selector */}
          <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
            <span>
              {t('showing')} {(startIndex + 1)} - {Math.min(startIndex + rowsPerPage, processedData.length)} {t('of')} {processedData.length} {t('results')}
            </span>
            <select
              value={rowsPerPage}
              onChange={(e) => { setRowsPerPage(Number(e.target.value)); setCurrentPage(1); }}
              className="border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-lg px-2 py-1 text-xs focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-colors"
            >
              {pageSizeOptions.map(opt => (
                <option key={opt} value={opt}>
                  {opt} {t('rows')}
                </option>
              ))}
            </select>
          </div>

          {/* Page navigation */}
          <div className="flex items-center gap-1">
            {/* First page */}
            <button
              onClick={() => setCurrentPage(1)}
              disabled={safeCurrentPage <= 1}
              className="p-1.5 rounded text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-30 transition-colors"
              aria-label={t('firstPage', 'First page')}
            >
              <FirstPageIcon className="w-4 h-4" />
            </button>

            {/* Previous page */}
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={safeCurrentPage <= 1}
              className="p-1.5 rounded text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-30 transition-colors"
              aria-label={t('previous')}
            >
              <PrevPageIcon className="w-4 h-4" />
            </button>

            {/* Page numbers */}
            {generatePageNumbers(safeCurrentPage, totalPages).map((p, i) =>
              p === '...' ? (
                <span key={`dots-${i}`} className="px-2 text-gray-400 dark:text-gray-500 text-sm select-none">
                  …
                </span>
              ) : (
                <button
                  key={p}
                  onClick={() => setCurrentPage(p)}
                  className={`min-w-[32px] h-8 rounded-lg text-sm font-medium transition-colors ${
                    p === safeCurrentPage
                      ? 'bg-riadah-500 text-white shadow-sm dark:bg-riadah-500'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  {p}
                </button>
              )
            )}

            {/* Next page */}
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={safeCurrentPage >= totalPages}
              className="p-1.5 rounded text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-30 transition-colors"
              aria-label={t('next')}
            >
              <NextPageIcon className="w-4 h-4" />
            </button>

            {/* Last page */}
            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={safeCurrentPage >= totalPages}
              className="p-1.5 rounded text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-30 transition-colors"
              aria-label={t('lastPage', 'Last page')}
            >
              <LastPageIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Extra footer content */}
          {footerExtra && <div className="w-full">{footerExtra}</div>}
        </div>
      )}

      {/* ──── Stagger animation keyframes ──── */}
      <style>{`
        @keyframes dataTableFadeIn {
          from {
            opacity: 0;
            transform: translateY(6px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}

// ──── Helper: get nested value from object ────
function getNestedValue(obj, path) {
  return path.split('.').reduce((acc, key) => acc?.[key], obj);
}

// ──── Helper: generate page number array with ellipsis ────
function generatePageNumbers(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = [];
  if (current <= 3) {
    pages.push(1, 2, 3, 4, '...', total);
  } else if (current >= total - 2) {
    pages.push(1, '...', total - 3, total - 2, total - 1, total);
  } else {
    pages.push(1, '...', current - 1, current, current + 1, '...', total);
  }
  return pages;
}
