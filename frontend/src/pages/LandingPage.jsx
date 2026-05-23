/**
 * LandingPage — صفحة تعريفية احترافية لخدمات نظام RIADAH ERP
 * صفحة عامة (بدون تسجيل دخول) تعرض قدرات النظام
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useI18n } from '../i18n/I18nContext';
import { useTheme } from '../context/ThemeContext';
import {
  BarChart3, Shield, Users, Warehouse, FileText, TrendingUp,
  ShoppingCart, Package, Truck, Calculator, UserCheck, Building2,
  ClipboardList, CreditCard, PieChart, Bell, Settings, Globe,
  CheckCircle2, ArrowLeft, ArrowRight, Star, Zap, Lock,
  Headphones, Clock, Layers, Target, Award, ChevronDown,
  Menu, X, Sun, Moon, HeartHandshake, ShieldCheck, Store,
  ArrowUp, Bot, MessageSquareText, BrainCircuit, LineChart,
  Handshake, Briefcase, Receipt, Landmark, Wrench, GraduationCap,
  Gavel, Globe2, Rocket, FileBarChart, Cpu, Sparkles
} from 'lucide-react';

/* ───────────── Icon Badge Component ───────────── */
const IconBadge = ({ children, color = 'bg-blue-500/20 text-blue-400' }) => (
  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${color} shrink-0`}>
    {children}
  </div>
);

/* ───────────── Feature Card ───────────── */
const FeatureCard = ({ icon, iconColor, title, desc, badge }) => (
  <div className="group relative bg-white/5 dark:bg-white/5 backdrop-blur-sm border border-gray-200/20 dark:border-white/10 rounded-2xl p-6 hover:bg-white/10 dark:hover:bg-white/8 hover:border-blue-400/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-500/10">
    <div className="flex items-start gap-4">
      <IconBadge color={iconColor}>{icon}</IconBadge>
      <div className="flex-1 min-w-0">
        {badge && (
          <span className="inline-block px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-500/20 text-emerald-400 mb-2">
            {badge}
          </span>
        )}
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">{title}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{desc}</p>
      </div>
    </div>
  </div>
);

/* ───────────── Stat Card ───────────── */
const StatCard = ({ number, label, icon }) => (
  <div className="text-center p-6">
    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
      {icon}
    </div>
    <div className="text-3xl md:text-4xl font-black text-white mb-1">{number}</div>
    <div className="text-sm text-gray-400">{label}</div>
  </div>
);

/* ───────────── Benefit Item ───────────── */
const BenefitItem = ({ text }) => (
  <div className="flex items-center gap-3 py-2">
    <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
    <span className="text-gray-700 dark:text-gray-300">{text}</span>
  </div>
);

/* ══════════════════════════════════════════════════════════════════════
   MAIN LANDING PAGE
   ══════════════════════════════════════════════════════════════════════ */
/* ───────────── Intersection Observer Hook ───────────── */
function useInView(options = {}) {
  const [ref, setRef] = useState(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    if (!ref) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setInView(true); obs.disconnect(); } }, { threshold: 0.15, ...options });
    obs.observe(ref);
    return () => obs.disconnect();
  }, [ref]);
  return [setRef, inView];
}

/* ───────────── Animated Section Wrapper ───────────── */
function AnimatedSection({ children, className = '', delay = 0 }) {
  const [ref, inView] = useInView();
  return (
    <div ref={ref} className={`transition-all duration-700 ease-out ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'} ${className}`} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

export default function LandingPage() {
  const { t, locale, setLocale } = useI18n();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [mobileMenu, setMobileMenu] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeFaq, setActiveFaq] = useState(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 20);
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      setScrollProgress(docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0);
      setShowScrollTop(window.scrollY > 500);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  /* ───── Services Data ───── */
  const services = [
    { icon: <BarChart3 className="w-7 h-7" />, iconColor: 'bg-blue-500/20 text-blue-400', title: t('landing.s1Title'), desc: t('landing.s1Desc') },
    { icon: <ShoppingCart className="w-7 h-7" />, iconColor: 'bg-emerald-500/20 text-emerald-400', title: t('landing.s2Title'), desc: t('landing.s2Desc') },
    { icon: <Truck className="w-7 h-7" />, iconColor: 'bg-amber-500/20 text-amber-400', title: t('landing.s3Title'), desc: t('landing.s3Desc') },
    { icon: <FileText className="w-7 h-7" />, iconColor: 'bg-violet-500/20 text-violet-400', title: t('landing.s4Title'), desc: t('landing.s4Desc') },
    { icon: <Users className="w-7 h-7" />, iconColor: 'bg-pink-500/20 text-pink-400', title: t('landing.s5Title'), desc: t('landing.s5Desc') },
    { icon: <Building2 className="w-7 h-7" />, iconColor: 'bg-cyan-500/20 text-cyan-400', title: t('landing.s6Title'), desc: t('landing.s6Desc') },
    { icon: <HeartHandshake className="w-7 h-7" />, iconColor: 'bg-orange-500/20 text-orange-400', title: t('landing.s7Title'), desc: t('landing.s7Desc') },
    { icon: <ClipboardList className="w-7 h-7" />, iconColor: 'bg-teal-500/20 text-teal-400', title: t('landing.s8Title'), desc: t('landing.s8Desc') },
    { icon: <ShieldCheck className="w-7 h-7" />, iconColor: 'bg-indigo-500/20 text-indigo-400', title: t('landing.s9Title'), desc: t('landing.s9Desc') },
    { icon: <Calculator className="w-7 h-7" />, iconColor: 'bg-rose-500/20 text-rose-400', title: t('landing.s10Title'), desc: t('landing.s10Desc') },
    { icon: <Store className="w-7 h-7" />, iconColor: 'bg-sky-500/20 text-sky-400', title: t('landing.s11Title'), desc: t('landing.s11Desc') },
    { icon: <TrendingUp className="w-7 h-7" />, iconColor: 'bg-lime-500/20 text-lime-400', title: t('landing.s12Title'), desc: t('landing.s12Desc'), badge: t('landing.new') },
  ];

  const faqs = [
    { q: t('landing.faq1Q'), a: t('landing.faq1A') },
    { q: t('landing.faq2Q'), a: t('landing.faq2A') },
    { q: t('landing.faq3Q'), a: t('landing.faq3A') },
    { q: t('landing.faq4Q'), a: t('landing.faq4A') },
    { q: t('landing.faq5Q'), a: t('landing.faq5A') },
  ];

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    setMobileMenu(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100" dir={locale === 'ar' ? 'rtl' : 'ltr'}>

      {/* ════════ SCROLL PROGRESS BAR ════════ */}
      <div className="fixed top-0 left-0 right-0 z-[60] h-1">
        <div className="h-full bg-gradient-to-l from-blue-500 via-purple-500 to-pink-500 transition-all duration-100 ease-out" style={{ width: `${scrollProgress}%` }} />
      </div>

      {/* ════════ SCROLL TO TOP ════════ */}
      <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="العودة للأعلى"
        className={`fixed bottom-6 left-6 z-50 w-12 h-12 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/25 hover:shadow-xl hover:-translate-y-1 active:scale-95 flex items-center justify-center transition-all duration-300 ${showScrollTop ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}>
        <ArrowUp className="w-5 h-5" />
      </button>

      {/* ════════ NAVBAR ════════ */}
      <nav className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${scrolled ? 'bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl shadow-lg shadow-black/5' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 md:h-20">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
                <Layers className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-black bg-gradient-to-l from-blue-600 to-purple-600 bg-clip-text text-transparent">
                RIADAH ERP
              </span>
            </div>

            {/* Desktop Links */}
            <div className="hidden md:flex items-center gap-8">
              <button onClick={() => scrollTo('services')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                {t('landing.navServices')}
              </button>
              <button onClick={() => scrollTo('features')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                {t('landing.navFeatures')}
              </button>
              <button onClick={() => scrollTo('faq')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                {t('landing.navFaq')}
              </button>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button onClick={toggleTheme} className="p-2 rounded-xl hover:bg-gray-200/50 dark:hover:bg-gray-800/50 transition-colors">
                {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              <button onClick={() => setLocale(locale === 'ar' ? 'en' : 'ar')} className="hidden sm:flex px-3 py-1.5 text-xs font-bold rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                {locale === 'ar' ? 'EN' : 'عربي'}
              </button>
              <Link to="/login" className="hidden md:inline-flex px-5 py-2 text-sm font-bold rounded-xl bg-gradient-to-l from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 hover:-translate-y-0.5 transition-all">
                {t('landing.navLogin')}
              </Link>
              <Link to="/register" className="hidden md:inline-flex px-5 py-2 text-sm font-bold rounded-xl border-2 border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white transition-all">
                {t('landing.navRegister')}
              </Link>
              <button onClick={() => setMobileMenu(!mobileMenu)} className="md:hidden p-2 rounded-xl hover:bg-gray-200/50 dark:hover:bg-gray-800/50">
                {mobileMenu ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenu && (
          <div className="md:hidden bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border-t border-gray-200/20 dark:border-gray-800/50 px-4 py-4 space-y-2">
            <button onClick={() => scrollTo('services')} className="block w-full text-right px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">{t('landing.navServices')}</button>
            <button onClick={() => scrollTo('features')} className="block w-full text-right px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">{t('landing.navFeatures')}</button>
            <button onClick={() => scrollTo('faq')} className="block w-full text-right px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">{t('landing.navFaq')}</button>
            <div className="flex gap-2 pt-2">
              <Link to="/login" className="flex-1 text-center px-4 py-2 text-sm font-bold rounded-xl bg-gradient-to-l from-blue-600 to-purple-600 text-white">{t('landing.navLogin')}</Link>
              <Link to="/register" className="flex-1 text-center px-4 py-2 text-sm font-bold rounded-xl border-2 border-blue-600 text-blue-600">{t('landing.navRegister')}</Link>
            </div>
          </div>
        )}
      </nav>

      {/* ════════ HERO SECTION ════════ */}
      <section className="relative pt-28 md:pt-36 pb-16 md:pb-24 overflow-hidden">
        {/* Background decorations */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-blue-500/10 dark:bg-blue-500/5 blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-purple-500/10 dark:bg-purple-500/5 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-gradient-to-br from-blue-500/5 to-purple-500/5 dark:from-blue-500/3 dark:to-purple-500/3 blur-3xl" />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Text */}
            <div className="text-center lg:text-start space-y-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 dark:bg-blue-500/10 border border-blue-500/20">
                <Zap className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">{t('landing.heroBadge')}</span>
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black leading-tight">
                <span className="bg-gradient-to-l from-blue-600 via-purple-600 to-pink-500 bg-clip-text text-transparent">
                  {t('landing.heroTitle1')}
                </span>
                <br />
                {t('landing.heroTitle2')}
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-400 max-w-lg mx-auto lg:mx-0 leading-relaxed">
                {t('landing.heroDesc')}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link to="/register" className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-bold rounded-2xl bg-gradient-to-l from-blue-600 to-purple-600 text-white shadow-xl shadow-blue-500/25 hover:shadow-2xl hover:shadow-blue-500/30 hover:-translate-y-1 transition-all">
                  {t('landing.heroCta')}
                  <ArrowLeft className="w-5 h-5" />
                </Link>
                <button onClick={() => scrollTo('services')} className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-bold rounded-2xl border-2 border-gray-300 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 transition-all">
                  {t('landing.heroCta2')}
                  <ChevronDown className="w-5 h-5" />
                </button>
              </div>
              {/* Trust badges */}
              <div className="flex items-center gap-6 justify-center lg:justify-start pt-4">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs text-gray-500">{t('landing.trust1')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-blue-500" />
                  <span className="text-xs text-gray-500">{t('landing.trust2')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Headphones className="w-4 h-4 text-purple-500" />
                  <span className="text-xs text-gray-500">{t('landing.trust3')}</span>
                </div>
              </div>
            </div>

            {/* Hero Image */}
            <div className="relative">
              <div className="relative rounded-3xl overflow-hidden shadow-2xl shadow-blue-500/10 border border-gray-200/30 dark:border-gray-800/50">
                <img src="/hero-illustration.png" alt="RIADAH ERP Dashboard" className="w-full h-auto" loading="eager" />
                <div className="absolute inset-0 bg-gradient-to-t from-white/20 dark:from-gray-950/30 to-transparent" />
              </div>
              {/* Floating cards */}
              <div className="absolute -bottom-4 -right-4 sm:bottom-4 sm:right-4 bg-white dark:bg-gray-900 rounded-2xl p-4 shadow-xl border border-gray-200/30 dark:border-gray-800/50 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-emerald-500" />
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{t('landing.float1')}</div>
                    <div className="text-sm font-bold text-emerald-500">+37.2%</div>
                  </div>
                </div>
              </div>
              <div className="absolute -top-4 -left-4 sm:top-4 sm:left-4 bg-white dark:bg-gray-900 rounded-2xl p-4 shadow-xl border border-gray-200/30 dark:border-gray-800/50 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                    <UserCheck className="w-5 h-5 text-blue-500" />
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{t('landing.float2')}</div>
                    <div className="text-sm font-bold text-blue-500">1,247</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ════════ STATS SECTION ════════ */}
      <AnimatedSection>
      <section className="relative py-16 bg-gradient-to-l from-blue-600 to-purple-700 overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-72 h-72 rounded-full bg-white blur-3xl" />
          <div className="absolute bottom-0 right-0 w-96 h-96 rounded-full bg-white blur-3xl" />
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <StatCard number="29+" label={t('landing.stat1')} icon={<Layers className="w-7 h-7" />} />
            <StatCard number="80+" label={t('landing.stat2')} icon={<Shield className="w-7 h-7" />} />
            <StatCard number="24/7" label={t('landing.stat3')} icon={<Clock className="w-7 h-7" />} />
            <StatCard number="99.9%" label={t('landing.stat4')} icon={<Award className="w-7 h-7" />} />
          </div>
        </div>
      </section>
      </AnimatedSection>

      {/* ════════ SERVICES SECTION ════════ */}
      <section id="services" className="py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section header */}
          <AnimatedSection>
          <div className="text-center max-w-2xl mx-auto mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 mb-6">
              <Package className="w-4 h-4 text-purple-500" />
              <span className="text-sm font-semibold text-purple-600 dark:text-purple-400">{t('landing.servicesBadge')}</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-black mb-4">{t('landing.servicesTitle')}</h2>
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{t('landing.servicesDesc')}</p>
          </div>
          </AnimatedSection>

          {/* Services grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 stagger-children">
            {services.map((s, i) => (
              <FeatureCard key={i} {...s} />
            ))}
          </div>
        </div>
      </section>

      {/* ════════ WHY CHOOSE US ════════ */}
      <AnimatedSection>
      <section id="features" className="py-20 md:py-28 bg-gray-100/50 dark:bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left: Benefits */}
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
                <Star className="w-4 h-4 text-emerald-500" />
                <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">{t('landing.whyBadge')}</span>
              </div>
              <h2 className="text-3xl md:text-4xl font-black mb-6">{t('landing.whyTitle')}</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">{t('landing.whyDesc')}</p>
              <div className="space-y-3">
                <BenefitItem text={t('landing.benefit1')} />
                <BenefitItem text={t('landing.benefit2')} />
                <BenefitItem text={t('landing.benefit3')} />
                <BenefitItem text={t('landing.benefit4')} />
                <BenefitItem text={t('landing.benefit5')} />
                <BenefitItem text={t('landing.benefit6')} />
                <BenefitItem text={t('landing.benefit7')} />
                <BenefitItem text={t('landing.benefit8')} />
              </div>
            </div>

            {/* Right: Feature cards stack */}
            <div className="space-y-6">
              <div className="bg-white dark:bg-gray-800/50 rounded-3xl p-8 border border-gray-200/50 dark:border-gray-800/50 shadow-lg">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                    <Globe className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{t('landing.card1Title')}</h3>
                    <p className="text-sm text-gray-500">{t('landing.card1Sub')}</p>
                  </div>
                </div>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">{t('landing.card1Desc')}</p>
              </div>
              <div className="bg-white dark:bg-gray-800/50 rounded-3xl p-8 border border-gray-200/50 dark:border-gray-800/50 shadow-lg">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Calculator className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{t('landing.card2Title')}</h3>
                    <p className="text-sm text-gray-500">{t('landing.card2Sub')}</p>
                  </div>
                </div>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">{t('landing.card2Desc')}</p>
              </div>
              <div className="bg-white dark:bg-gray-800/50 rounded-3xl p-8 border border-gray-200/50 dark:border-gray-800/50 shadow-lg">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                    <Bell className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{t('landing.card3Title')}</h3>
                    <p className="text-sm text-gray-500">{t('landing.card3Sub')}</p>
                  </div>
                </div>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">{t('landing.card3Desc')}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
      </AnimatedSection>

      {/* ════════ HOW IT WORKS ════════ */}
      <AnimatedSection>
      <section className="py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 mb-6">
              <Settings className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">{t('landing.stepsBadge')}</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-black mb-4">{t('landing.stepsTitle')}</h2>
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{t('landing.stepsDesc')}</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', icon: <UserCheck className="w-8 h-8" />, title: t('landing.step1Title'), desc: t('landing.step1Desc'), color: 'from-blue-500 to-cyan-500' },
              { step: '02', icon: <Settings className="w-8 h-8" />, title: t('landing.step2Title'), desc: t('landing.step2Desc'), color: 'from-purple-500 to-pink-500' },
              { step: '03', icon: <TrendingUp className="w-8 h-8" />, title: t('landing.step3Title'), desc: t('landing.step3Desc'), color: 'from-emerald-500 to-teal-500' },
            ].map((item, i) => (
              <div key={i} className="relative text-center group">
                {/* Connector line */}
                {i < 2 && (
                  <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-0.5 bg-gradient-to-l from-gray-300 dark:from-gray-700 to-gray-200 dark:to-gray-800" />
                )}
                <div className={`w-24 h-24 mx-auto mb-6 rounded-3xl bg-gradient-to-br ${item.color} flex items-center justify-center text-white shadow-xl group-hover:scale-110 transition-transform duration-300`}>
                  {item.icon}
                </div>
                <div className="text-xs font-bold text-gray-400 mb-2">{item.step}</div>
                <h3 className="text-xl font-bold mb-3">{item.title}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed max-w-xs mx-auto">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      </AnimatedSection>

      {/* ════════ CTA SECTION ════════ */}
      <AnimatedSection>
      <section className="py-20 md:py-28">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 rounded-3xl p-10 md:p-16 text-center overflow-hidden">
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-white blur-3xl" />
              <div className="absolute bottom-0 left-0 w-80 h-80 rounded-full bg-white blur-3xl" />
            </div>
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-black text-white mb-4">{t('landing.ctaTitle')}</h2>
              <p className="text-lg text-white/80 mb-8 max-w-2xl mx-auto">{t('landing.ctaDesc')}</p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/register" className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-bold rounded-2xl bg-white text-blue-600 shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all">
                  {t('landing.ctaBtn1')}
                  <ArrowLeft className="w-5 h-5" />
                </Link>
                <button onClick={() => scrollTo('services')} className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-bold rounded-2xl border-2 border-white/30 text-white hover:bg-white/10 transition-all">
                  {t('landing.ctaBtn2')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
      </AnimatedSection>

      {/* ════════ FAQ SECTION ════════ */}
      <AnimatedSection>
      <section id="faq" className="py-20 md:py-28 bg-gray-100/50 dark:bg-gray-900/50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 mb-6">
              <PieChart className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-semibold text-amber-600 dark:text-amber-400">{t('landing.faqBadge')}</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-black mb-4">{t('landing.faqTitle')}</h2>
            <p className="text-gray-600 dark:text-gray-400">{t('landing.faqSubtitle')}</p>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 overflow-hidden">
                <button
                  onClick={() => setActiveFaq(activeFaq === i ? null : i)}
                  className="w-full flex items-center justify-between p-6 text-right hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <span className="font-bold text-base">{faq.q}</span>
                  <ChevronDown className={`w-5 h-5 text-gray-400 shrink-0 transition-transform duration-300 ${activeFaq === i ? 'rotate-180' : ''}`} />
                </button>
                {activeFaq === i && (
                  <div className="px-6 pb-6">
                    <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">{faq.a}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>
      </AnimatedSection>

      {/* ════════ FOOTER ════════ */}
      <footer className="bg-gray-900 dark:bg-gray-950 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-10">
            {/* Brand */}
            <div className="md:col-span-1">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                  <Layers className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-black">RIADAH ERP</span>
              </div>
              <p className="text-sm text-gray-400 leading-relaxed mb-4">{t('landing.footerDesc')}</p>
              <div className="flex gap-3">
                <Link to="/login" className="px-4 py-2 text-xs font-bold rounded-lg bg-white/10 hover:bg-white/20 transition-colors">{t('landing.navLogin')}</Link>
                <Link to="/register" className="px-4 py-2 text-xs font-bold rounded-lg bg-gradient-to-l from-blue-600 to-purple-600 hover:opacity-90 transition-opacity">{t('landing.navRegister')}</Link>
              </div>
            </div>

            {/* Services */}
            <div>
              <h4 className="font-bold mb-4 text-sm">{t('landing.footerServices')}</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>{t('landing.s1Title')}</li>
                <li>{t('landing.s2Title')}</li>
                <li>{t('landing.s5Title')}</li>
                <li>{t('landing.s9Title')}</li>
                <li>{t('landing.s11Title')}</li>
              </ul>
            </div>

            {/* Links */}
            <div>
              <h4 className="font-bold mb-4 text-sm">{t('landing.footerLinks')}</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><button onClick={() => scrollTo('services')} className="hover:text-white transition-colors">{t('landing.navServices')}</button></li>
                <li><button onClick={() => scrollTo('features')} className="hover:text-white transition-colors">{t('landing.navFeatures')}</button></li>
                <li><button onClick={() => scrollTo('faq')} className="hover:text-white transition-colors">{t('landing.navFaq')}</button></li>
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h4 className="font-bold mb-4 text-sm">{t('landing.footerContact')}</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>{t('landing.footerEmail')}</li>
                <li>{t('landing.footerPhone')}</li>
                <li>{t('landing.footerLocation')}</li>
              </ul>
            </div>
          </div>

          {/* Bottom */}
          <div className="mt-12 pt-8 border-t border-gray-800 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-500">{t('landing.footerCopy')}</p>
            <p className="text-sm text-gray-500">{t('landing.footerMade')}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
