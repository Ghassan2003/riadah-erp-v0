/**
 * ScrollToTop — زر العودة للأعلى مع شريط تقدم القراءة
 * يظهر عند النزول 300px ويعرض شريط تقدم القراءة
 */

import { useState, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

export default function ScrollToTop() {
  const [visible, setVisible] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollPercent = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;

      setVisible(scrollTop > 300);
      setProgress(Math.min(scrollPercent, 100));
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      {/* شريط تقدم القراءة في أعلى الصفحة */}
      <div className="fixed top-0 left-0 right-0 z-[100] h-0.5 bg-transparent">
        <div
          className="h-full bg-gradient-to-l from-blue-500 via-purple-500 to-pink-500 transition-all duration-150 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* زر العودة للأعلى */}
      <button
        onClick={scrollToTop}
        aria-label="العودة للأعلى"
        className={`
          fixed bottom-24 left-6 z-50
          w-11 h-11 rounded-full
          bg-gradient-to-br from-blue-500 to-purple-600
          text-white shadow-lg shadow-blue-500/25
          hover:shadow-xl hover:shadow-blue-500/30 hover:-translate-y-0.5
          active:scale-95
          flex items-center justify-center
          transition-all duration-300 ease-out
          ${visible ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 translate-y-4 pointer-events-none'}
        `}
      >
        <ArrowUp className="w-5 h-5" />
      </button>
    </>
  );
}
