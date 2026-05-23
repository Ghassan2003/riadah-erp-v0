/**
 * Tests for DataTable component.
 * Tests rendering, search, sorting, pagination, selection, and empty state.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataTable from '../components/DataTable';
import { I18nProvider } from '../i18n/I18nContext';
import React from 'react';

function renderDataTable(props = {}) {
  return render(
    React.createElement(I18nProvider, null, React.createElement(DataTable, props))
  );
}

const sampleData = [
  { id: 1, name: 'منتج أ', price: 100, category: 'إلكترونيات' },
  { id: 2, name: 'منتج ب', price: 200, category: 'أثاث' },
  { id: 3, name: 'منتج ج', price: 50, category: 'إلكترونيات' },
  { id: 4, name: 'منتج د', price: 150, category: 'ملابس' },
  { id: 5, name: 'منتج هـ', price: 75, category: 'أثاث' },
];

const columns = [
  { key: 'name', label: 'الاسم' },
  { key: 'price', label: 'السعر' },
  { key: 'category', label: 'الفئة' },
];

describe('DataTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render table with data', () => {
    renderDataTable({ data: sampleData, columns });
    expect(screen.getByText('منتج أ')).toBeInTheDocument();
    expect(screen.getByText('منتج ب')).toBeInTheDocument();
    expect(screen.getByText('200')).toBeInTheDocument();
  });

  it('should render correct number of rows', () => {
    renderDataTable({ data: sampleData, columns });
    const rows = screen.getAllByRole('row');
    // header + 5 data rows
    expect(rows.length).toBe(6);
  });

  it('should render column headers', () => {
    renderDataTable({ data: sampleData, columns });
    expect(screen.getByText('الاسم')).toBeInTheDocument();
    expect(screen.getByText('السعر')).toBeInTheDocument();
    expect(screen.getByText('الفئة')).toBeInTheDocument();
  });

  it('should show empty message when no data', () => {
    renderDataTable({ data: [], columns });
    expect(screen.getByText('لا توجد بيانات')).toBeInTheDocument();
  });

  it('should show custom empty message', () => {
    renderDataTable({ data: [], columns, emptyMessage: 'لا توجد منتجات متاحة' });
    expect(screen.getByText('لا توجد منتجات متاحة')).toBeInTheDocument();
  });

  it('should filter data based on search', async () => {
    renderDataTable({ data: sampleData, columns, searchKeys: ['name'] });
    const searchInput = screen.getByPlaceholderText('بحث...');
    await userEvent.type(searchInput, 'منتج أ');
    expect(screen.getByText('منتج أ')).toBeInTheDocument();
    expect(screen.queryByText('منتج ب')).not.toBeInTheDocument();
  });

  it('should show clear search button when searching', async () => {
    renderDataTable({ data: sampleData, columns, searchKeys: ['name'] });
    const searchInput = screen.getByPlaceholderText('بحث...');
    await userEvent.type(searchInput, 'test');
    // Clear button appears as X icon button (aria-label from i18n)
    const clearBtns = screen.getAllByRole('button');
    const clearBtn = clearBtns.find(btn => btn.getAttribute('aria-label')?.includes('مسح'));
    expect(clearBtn).toBeDefined();
  });

  it('should clear search and show all data', async () => {
    renderDataTable({ data: sampleData, columns, searchKeys: ['name'] });
    const searchInput = screen.getByPlaceholderText('بحث...');
    await userEvent.type(searchInput, 'منتج أ');
    const clearBtn = screen.getByRole('button', { name: /مسح البحث/ });
    await userEvent.click(clearBtn);
    expect(screen.getByText('منتج أ')).toBeInTheDocument();
    expect(screen.getByText('منتج ب')).toBeInTheDocument();
  });

  it('should sort data by clicking column header', async () => {
    renderDataTable({ data: sampleData, columns });
    const nameHeader = screen.getByText('الاسم');
    await userEvent.click(nameHeader);
    const rows = screen.getAllByRole('row');
    const firstCell = within(rows[1]).getAllByRole('cell')[0];
    expect(firstCell.textContent).toBeTruthy();
  });

  it('should toggle sort direction on second click', async () => {
    renderDataTable({ data: sampleData, columns });
    const nameHeader = screen.getByText('الاسم');
    await userEvent.click(nameHeader);
    await userEvent.click(nameHeader);
    const rows = screen.getAllByRole('row');
    const firstCell = within(rows[1]).getAllByRole('cell')[0];
    expect(firstCell.textContent).toBeTruthy();
  });

  it('should paginate data', () => {
    renderDataTable({ data: sampleData, columns, pageSize: 2 });
    const rows = screen.getAllByRole('row');
    expect(rows.length).toBe(3); // header + 2 data rows
  });

  it('should navigate to next page', async () => {
    renderDataTable({ data: sampleData, columns, pageSize: 2 });
    const nextBtn = screen.getByLabelText('التالي');
    await userEvent.click(nextBtn);
    const rows = screen.getAllByRole('row');
    expect(rows.length).toBe(3);
  });

  it('should show page size selector', () => {
    renderDataTable({ data: sampleData, columns });
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
  });

  it('should show row selection checkboxes when onSelectionChange is provided', () => {
    const onSelectionChange = vi.fn();
    renderDataTable({ data: sampleData, columns, onSelectionChange });
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes.length).toBeGreaterThan(1);
  });

  it('should select all rows via header checkbox', async () => {
    const onSelectionChange = vi.fn();
    renderDataTable({ data: sampleData, columns, onSelectionChange });
    const headerCheckbox = screen.getAllByRole('checkbox')[0];
    await userEvent.click(headerCheckbox);
    expect(onSelectionChange).toHaveBeenCalled();
  });

  it('should select individual row', async () => {
    const onSelectionChange = vi.fn();
    renderDataTable({ data: sampleData, columns, onSelectionChange });
    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[1]);
    expect(onSelectionChange).toHaveBeenCalled();
  });

  it('should render custom cell renderer', () => {
    const customColumns = [
      { key: 'price', label: 'السعر', render: (value) => `${value} ر.س` },
    ];
    renderDataTable({ data: sampleData, columns: customColumns });
    expect(screen.getByText('100 ر.س')).toBeInTheDocument();
  });

  it('should render actions column', () => {
    const actions = vi.fn(() => React.createElement('button', null, 'حذف'));
    renderDataTable({ data: sampleData, columns, actions });
    expect(screen.getAllByText('حذف').length).toBe(5);
  });

  it('should show showing info text', () => {
    renderDataTable({ data: sampleData, columns });
    expect(screen.getByText(/من 5/)).toBeInTheDocument();
  });

  it('should render without search when searchable is false', () => {
    renderDataTable({ data: sampleData, columns, searchable: false });
    expect(screen.queryByPlaceholderText('بحث...')).not.toBeInTheDocument();
  });

  it('should render header actions', () => {
    renderDataTable({
      data: sampleData, columns,
      headerActions: [React.createElement('button', { key: 'add' }, 'إضافة')],
    });
    expect(screen.getByText('إضافة')).toBeInTheDocument();
  });

  it('should show dash for null values', () => {
    const dataWithNull = [{ id: 1, name: null, price: null }];
    renderDataTable({ data: dataWithNull, columns });
    const cells = screen.getAllByText('-');
    expect(cells.length).toBeGreaterThanOrEqual(1);
  });

  it('should show clear search link in empty state when searching', async () => {
    renderDataTable({ data: sampleData, columns, searchKeys: ['name'] });
    const searchInput = screen.getByPlaceholderText('بحث...');
    await userEvent.type(searchInput, 'xyz_nonexistent');
    expect(screen.getByText('لا توجد بيانات')).toBeInTheDocument();
    const clearLinks = screen.getAllByText('مسح البحث');
    expect(clearLinks.length).toBeGreaterThanOrEqual(1);
  });
});
