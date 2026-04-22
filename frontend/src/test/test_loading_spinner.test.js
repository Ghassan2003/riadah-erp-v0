/**
 * Tests for LoadingSpinner component.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoadingSpinner, { SkeletonLoader, InlineSpinner } from '../components/LoadingSpinner';
import React from 'react';

describe('LoadingSpinner', () => {
  beforeEach(() => {
    document.documentElement.classList.remove('dark');
  });

  it('should render with default message', () => {
    render(React.createElement(LoadingSpinner));
    expect(screen.getByText('جاري التحميل...')).toBeInTheDocument();
  });

  it('should render with custom message', () => {
    render(React.createElement(LoadingSpinner, { message: 'يرجى الانتظار' }));
    expect(screen.getByText('يرجى الانتظار')).toBeInTheDocument();
  });

  it('should render spinner type by default', () => {
    const { container } = render(React.createElement(LoadingSpinner));
    const spinners = container.querySelectorAll('.animate-spin');
    expect(spinners.length).toBeGreaterThanOrEqual(1);
  });

  it('should render skeleton when type is skeleton', () => {
    const { container } = render(React.createElement(LoadingSpinner, { type: 'skeleton' }));
    const skeletons = container.querySelectorAll('.skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('should apply dark mode classes', () => {
    document.documentElement.classList.add('dark');
    const { container } = render(React.createElement(LoadingSpinner));
    const wrapper = container.firstElementChild;
    expect(wrapper.className).toContain('dark:bg-gray-900');
  });

  it('should apply light mode classes by default', () => {
    const { container } = render(React.createElement(LoadingSpinner));
    const wrapper = container.firstElementChild;
    expect(wrapper.className).toContain('bg-gray-50');
  });
});

describe('SkeletonLoader', () => {
  it('should render skeleton cards', () => {
    const { container } = render(React.createElement(SkeletonLoader));
    const skeletons = container.querySelectorAll('.skeleton');
    expect(skeletons.length).toBeGreaterThan(5);
  });

  it('should render stats cards grid', () => {
    const { container } = render(React.createElement(SkeletonLoader));
    const grid = container.querySelector('.grid');
    expect(grid).toBeInTheDocument();
    expect(grid.children.length).toBe(4);
  });
});

describe('InlineSpinner', () => {
  it('should render SVG element', () => {
    const { container } = render(React.createElement(InlineSpinner));
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('should have animate-spin class', () => {
    const { container } = render(React.createElement(InlineSpinner));
    const svg = container.querySelector('svg');
    expect(svg.getAttribute('class')).toContain('animate-spin');
  });

  it('should render without crashing for all sizes', () => {
    const { container: sm } = render(React.createElement(InlineSpinner, { size: 'sm' }));
    const { container: md } = render(React.createElement(InlineSpinner, { size: 'md' }));
    const { container: lg } = render(React.createElement(InlineSpinner, { size: 'lg' }));
    expect(sm.querySelector('svg')).toBeInTheDocument();
    expect(md.querySelector('svg')).toBeInTheDocument();
    expect(lg.querySelector('svg')).toBeInTheDocument();
  });
});
