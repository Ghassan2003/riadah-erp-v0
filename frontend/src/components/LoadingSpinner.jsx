/**
 * Loading spinner component with skeleton and dark mode support.
 */

export default function LoadingSpinner({ message = 'جاري التحميل...', type = 'spinner' }) {
  if (type === 'skeleton') {
    return <SkeletonLoader />;
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      <div className="text-center animate-fade-in">
        <div className="relative mx-auto mb-6">
          <div className="w-16 h-16 rounded-full border-4 border-riadah-200 dark:border-riadah-900"></div>
          <div className="w-16 h-16 rounded-full border-4 border-transparent border-t-blue-600 dark:border-t-blue-400 animate-spin absolute top-0"></div>
          <div className="w-10 h-10 rounded-full border-3 border-transparent border-t-blue-400 dark:border-t-blue-300 animate-spin absolute top-3 right-3" style={{ animationDuration: '0.8s', animationDirection: 'reverse' }}></div>
        </div>
        <p className="text-gray-600 dark:text-gray-400 text-lg font-medium font-arabic">{message}</p>
      </div>
    </div>
  );
}

/** Skeleton loading cards */
export function SkeletonLoader() {
  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="skeleton h-8 w-48 rounded-lg"></div>
        <div className="flex gap-2">
          <div className="skeleton h-10 w-28 rounded-lg"></div>
          <div className="skeleton h-10 w-28 rounded-lg"></div>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="skeleton w-10 h-10 rounded-lg"></div>
              <div className="flex-1">
                <div className="skeleton h-3 w-24 rounded mb-2"></div>
                <div className="skeleton h-6 w-16 rounded"></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Table skeleton */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="skeleton h-10 w-full max-w-md rounded-lg"></div>
        </div>
        <div className="p-4 space-y-3">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="flex items-center gap-4">
              <div className="skeleton h-4 w-4 rounded"></div>
              <div className="skeleton h-4 flex-1 rounded"></div>
              <div className="skeleton h-4 w-24 rounded"></div>
              <div className="skeleton h-4 w-20 rounded"></div>
              <div className="skeleton h-8 w-20 rounded-lg"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/** Inline loading spinner */
export function InlineSpinner({ size = 'md' }) {
  const sizeMap = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' };
  return (
    <RefreshIcon className={`${sizeMap[size]} animate-spin text-accent-500`} />
  );
}

function RefreshIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 2v6h-6" /><path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
      <path d="M3 22v-6h6" /><path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
    </svg>
  );
}
