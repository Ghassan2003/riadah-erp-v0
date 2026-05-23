/**
 * ErrorBoundary - حد أخطاء React مع صفحة خطأ صديقة للمستخدم.
 * يدعم: الوضع الداكن، إعادة المحاولة، التسجيل في وحدة التحكم.
 */

import { Component } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

// Inner component that can use hooks
function ErrorFallback({ error, onRetry }) {
  const { t } = useI18n();

  return (
    <div className="min-h-[400px] flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-900">
      <div className="text-center max-w-md animate-fade-in">
        {/* Icon */}
        <div className="w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-6">
          <AlertTriangle className="w-10 h-10 text-red-500 dark:text-red-400" />
        </div>

        {/* Title */}
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
          {t('somethingWentWrong')}
        </h2>

        {/* Description */}
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
          {t('errorDescription')}
        </p>

        {/* Error details (development) */}
        {error && process.env.NODE_ENV === 'development' && (
          <pre className="text-xs text-left bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-6 text-red-600 dark:text-red-400 overflow-auto max-h-32">
            {error.toString()}
          </pre>
        )}

        {/* Actions */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={onRetry}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-riadah-500 hover:bg-riadah-600 text-white text-sm font-medium transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            {t('tryAgain')}
          </button>
          <button
            onClick={() => (window.location.href = '/dashboard')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium transition-colors"
          >
            <Home className="w-4 h-4" />
            {t('goHome')}
          </button>
        </div>
      </div>
    </div>
  );
}

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          onRetry={this.handleRetry}
        />
      );
    }

    return this.props.children;
  }
}
