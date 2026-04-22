/**
 * صفحة تعليمات الفيديو - نظام تعليمي شامل
 * يتضمن: عرض الفيديوهات، مشغل فيديو مدمج، رفع فيديو، تتبع التقدم، تعليقات
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import {
  videosAPI, videoCategoriesAPI, videoProgressAPI, videoCommentsAPI,
} from '../api';
import {
  Video, Play, Clock, Eye, ThumbsUp, Search, Filter,
  Plus, X, Upload, ChevronRight, Star, BookOpen,
  Settings, Package, ShoppingCart, Truck, FileText,
  FolderKanban, BarChart3, Users, ClipboardList,
  Wrench, GraduationCap, MessageCircle, Send,
  Heart, Share2, Bookmark, ArrowRight, CheckCircle2,
  Circle, Loader2, AlertCircle, Trash2, Edit3,
} from 'lucide-react';

const CATEGORIES_MAP = {
  getting_started: { icon: GraduationCap, color: '#3B82F6' },
  inventory: { icon: Package, color: '#10B981' },
  sales: { icon: ShoppingCart, color: '#F59E0B' },
  purchases: { icon: Truck, color: '#8B5CF6' },
  accounting: { icon: BookOpen, color: '#EF4444' },
  hr: { icon: Users, color: '#EC4899' },
  documents: { icon: FileText, color: '#06B6D4' },
  projects: { icon: FolderKanban, color: '#F97316' },
  reports: { icon: BarChart3, color: '#14B8A6' },
  settings: { icon: Settings, color: '#6366F1' },
  advanced: { icon: Wrench, color: '#A855F7' },
  troubleshooting: { icon: ClipboardList, color: '#DC2626' },
};

const CATEGORY_KEYS = {
  ar: {
    getting_started: 'categoryGettingStarted',
    inventory: 'categoryInventory',
    sales: 'categorySales',
    purchases: 'categoryPurchases',
    accounting: 'categoryAccounting',
    hr: 'categoryHr',
    documents: 'categoryDocuments',
    projects: 'categoryProjects',
    reports: 'categoryReports',
    settings: 'categorySettings',
    advanced: 'categoryAdvanced',
    troubleshooting: 'categoryTroubleshooting',
  },
  en: {
    getting_started: 'Getting Started',
    inventory: 'Inventory',
    sales: 'Sales',
    purchases: 'Purchases',
    accounting: 'Accounting',
    hr: 'Human Resources',
    documents: 'Documents',
    projects: 'Projects',
    reports: 'Reports',
    settings: 'Settings',
    advanced: 'Advanced',
    troubleshooting: 'Troubleshooting',
  },
};

export default function VideoInstructionsPage() {
  const { t, locale, isRTL } = useI18n();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // State
  const [videos, setVideos] = useState([]);
  const [featuredVideos, setFeaturedVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedVideoDetail, setSelectedVideoDetail] = useState(null);
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploadModal, setUploadModal] = useState(false);
  const [userProgress, setUserProgress] = useState({});
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  const videoRef = useRef(null);
  const progressIntervalRef = useRef(null);

  // Fetch initial data
  useEffect(() => {
    fetchInitialData();
    return () => {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    };
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [videosRes, featuredRes, statsRes, progressRes] = await Promise.all([
        videosAPI.list({ page_size: 100 }),
        videosAPI.featured(),
        videosAPI.stats(),
        videoProgressAPI.list().catch(() => ({ data: [] })),
      ]);

      const videosData = videosRes.data.results || videosRes.data || [];
      setVideos(videosData);
      setFeaturedVideos(featuredRes.data.results || featuredRes.data || []);
      setStats(statsRes.data);

      // Build progress map
      const progressMap = {};
      (progressRes.data || []).forEach(p => {
        progressMap[p.video] = {
          watched_seconds: p.watched_seconds,
          is_completed: p.is_completed,
          progress_percent: p.progress_percent,
        };
      });
      setUserProgress(progressMap);
    } catch (err) {
      console.error('Error fetching videos:', err);
    } finally {
      setLoading(false);
    }
  };

  // Select video and load details
  const handleSelectVideo = async (video) => {
    setSelectedVideo(video);
    try {
      const res = await videosAPI.get(video.id);
      setSelectedVideoDetail(res.data);
      // Load comments
      const commentsRes = await videoCommentsAPI.list(video.id);
      setComments(commentsRes.data.results || commentsRes.data || []);
    } catch (err) {
      console.error('Error loading video details:', err);
      setSelectedVideoDetail(video);
    }
  };

  // Filter videos
  const filteredVideos = videos.filter(v => {
    const matchCategory = activeCategory === 'all' || v.category === activeCategory;
    const matchSearch = !searchQuery ||
      v.title_ar?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.title_en?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.description_ar?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchTab =
      activeTab === 'all' ||
      (activeTab === 'featured' && v.is_featured) ||
      (activeTab === 'completed' && userProgress[v.id]?.is_completed) ||
      (activeTab === 'in-progress' && userProgress[v.id] && !userProgress[v.id].is_completed);
    return matchCategory && matchSearch && matchTab;
  });

  // Track video progress
  const handleTimeUpdate = useCallback(() => {
    if (!videoRef.current || !selectedVideo) return;
    const currentTime = Math.floor(videoRef.current.currentTime);
    const progress = userProgress[selectedVideo.id];
    if (!progress || currentTime - progress.watched_seconds >= 5) {
      const isCompleted = selectedVideo.duration_seconds > 0 &&
        currentTime >= selectedVideo.duration_seconds * 0.9;
      videoProgressAPI.update({
        video: selectedVideo.id,
        watched_seconds: currentTime,
        is_completed,
      }).catch(() => {});
      setUserProgress(prev => ({
        ...prev,
        [selectedVideo.id]: {
          watched_seconds: currentTime,
          is_completed: isCompleted || prev[selectedVideo.id]?.is_completed || false,
          progress_percent: selectedVideo.duration_seconds > 0
            ? Math.min(100, Math.floor((currentTime / selectedVideo.duration_seconds) * 100))
            : 0,
        },
      }));
    }
  }, [selectedVideo, userProgress]);

  // Like video
  const handleLike = async (videoId) => {
    try {
      await videosAPI.like(videoId);
      setVideos(prev => prev.map(v =>
        v.id === videoId ? { ...v, likes_count: v.likes_count + 1 } : v
      ));
      if (selectedVideoDetail?.id === videoId) {
        setSelectedVideoDetail(prev => ({
          ...prev,
          likes_count: prev.likes_count + 1,
        }));
      }
    } catch {}
  };

  // Add comment
  const handleAddComment = async () => {
    if (!newComment.trim() || !selectedVideo) return;
    try {
      const res = await videoCommentsAPI.create(selectedVideo.id, { comment: newComment });
      setComments(prev => [res.data, ...prev]);
      setNewComment('');
      toast.success(t('success'));
    } catch {
      toast.error(t('error'));
    }
  };

  // Delete comment
  const handleDeleteComment = async (commentId) => {
    try {
      await videoCommentsAPI.delete(commentId);
      setComments(prev => prev.filter(c => c.id !== commentId));
    } catch {}
  };

  // Delete video (admin)
  const handleDeleteVideo = async (videoId) => {
    if (!window.confirm(t('confirmDeleteVideo'))) return;
    try {
      await videosAPI.delete(videoId);
      setVideos(prev => prev.filter(v => v.id !== videoId));
      if (selectedVideo?.id === videoId) {
        setSelectedVideo(null);
        setSelectedVideoDetail(null);
      }
      toast.success(t('videoDeletedSuccess'));
    } catch {
      toast.error(t('error'));
    }
  };

  // YouTube embed URL helper
  const getYoutubeEmbedUrl = (url) => {
    if (!url) return null;
    const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\s]+)/);
    return match ? `https://www.youtube.com/embed/${match[1]}` : null;
  };

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    title_ar: '', title_en: '', description_ar: '',
    video_url: '', category: 'getting_started',
    difficulty_level: 'beginner', tags: '',
    is_featured: false, duration_seconds: 0,
  });

  const handleUpload = async (e) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      Object.entries(uploadForm).forEach(([key, val]) => {
        if (val !== null && val !== undefined) {
          formData.append(key, val);
        }
      });
      await videosAPI.create(formData);
      toast.success(t('videoCreated'));
      setUploadModal(false);
      setUploadForm({
        title_ar: '', title_en: '', description_ar: '',
        video_url: '', category: 'getting_started',
        difficulty_level: 'beginner', tags: '',
        is_featured: false, duration_seconds: 0,
      });
      fetchInitialData();
    } catch {
      toast.error(t('error'));
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '--:--';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
      : `${m}:${String(s).padStart(2, '0')}`;
  };

  const formatWatchTime = (seconds) => {
    if (!seconds) return '0:00';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  // Get category display name
  const getCategoryName = (catKey) => {
    const keyMap = CATEGORY_KEYS[locale] || CATEGORY_KEYS.en;
    return keyMap[catKey] || catKey;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-pink-600 flex items-center justify-center shadow-lg">
              <Video className="w-5 h-5 text-white" />
            </div>
            {t('videoInstructions')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('videoInstructionsDesc')}</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setUploadModal(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-riadah-500 to-riadah-500 hover:from-riadah-500 hover:to-riadah-700 text-white rounded-xl font-medium shadow-lg shadow-riadah-500/25 transition-all duration-200 hover:scale-105 active:scale-95"
          >
            <Upload className="w-4 h-4" />
            {t('videoUpload')}
          </button>
        )}
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: t('videoCount'), value: stats.total_videos, icon: Video, color: 'from-riadah-400 to-riadah-500' },
            { label: t('watchedVideos'), value: stats.user_stats?.watched_count || 0, icon: Eye, color: 'from-green-500 to-emerald-600' },
            { label: t('completedCount'), value: stats.user_stats?.completed_count || 0, icon: CheckCircle2, color: 'from-purple-500 to-violet-600' },
            { label: t('totalWatchTime'), value: formatWatchTime(stats.user_stats?.total_watch_time || 0), icon: Clock, color: 'from-orange-500 to-red-500' },
          ].map((stat, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center shadow-md`}>
                  <stat.icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{stat.label}</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{stat.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 ${isRTL ? 'right-3' : 'left-3'}`} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('searchVideos')}
              className={`w-full pl-10 ${isRTL ? 'pr-10' : ''} py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none transition-all text-gray-900 dark:text-white`}
            />
          </div>
          {/* Category Filter */}
          <div className="relative">
            <Filter className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 ${isRTL ? 'right-3' : 'left-3'}`} />
            <select
              value={activeCategory}
              onChange={(e) => setActiveCategory(e.target.value)}
              className={`pl-10 ${isRTL ? 'pr-10' : ''} py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none transition-all appearance-none min-w-[180px] text-gray-900 dark:text-white`}
            >
              <option value="all">{t('allVideos')}</option>
              {Object.keys(CATEGORIES_MAP).map(key => (
                <option key={key} value={key}>{getCategoryName(key)}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {[
          { key: 'all', label: t('allVideos'), icon: Video },
          { key: 'featured', label: t('featuredVideos'), icon: Star },
          { key: 'in-progress', label: t('continueWatching'), icon: Play },
          { key: 'completed', label: t('completedVideos'), icon: CheckCircle2 },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
              activeTab === tab.key
                ? 'bg-riadah-500 text-white shadow-md shadow-riadah-500/25'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Category Cards */}
      {activeTab === 'all' && !searchQuery && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
          {Object.entries(CATEGORIES_MAP).map(([key, { icon: Icon, color }]) => {
            const count = videos.filter(v => v.category === key).length;
            if (count === 0) return null;
            return (
              <button
                key={key}
                onClick={() => setActiveCategory(activeCategory === key ? 'all' : key)}
                className={`group p-4 rounded-2xl border-2 transition-all duration-200 hover:scale-105 active:scale-95 ${
                  activeCategory === key
                    ? 'border-accent-500 bg-riadah-50 dark:bg-riadah-900/20 shadow-md'
                    : 'border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-200 dark:hover:border-gray-600'
                }`}
              >
                <div className="w-10 h-10 rounded-xl mx-auto mb-2 flex items-center justify-center" style={{ backgroundColor: color + '20' }}>
                  <Icon className="w-5 h-5" style={{ color }} />
                </div>
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300 text-center leading-tight">
                  {getCategoryName(key)}
                </p>
                <p className="text-xs text-gray-400 mt-1 text-center">{count}</p>
              </button>
            );
          })}
        </div>
      )}

      {/* Main Content */}
      <div className={`grid gap-6 ${selectedVideo ? 'lg:grid-cols-3' : 'grid-cols-1'}`}>
        {/* Video List */}
        <div className={`${selectedVideo ? 'lg:col-span-1' : 'lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 grid gap-4'}`}>
          {filteredVideos.length === 0 ? (
            <div className="col-span-full flex flex-col items-center justify-center py-16 text-center">
              <div className="w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
                <Video className="w-10 h-10 text-gray-300 dark:text-gray-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-600 dark:text-gray-400">{t('noVideos')}</h3>
              <p className="text-sm text-gray-400 mt-1">{t('noVideosDesc')}</p>
            </div>
          ) : selectedVideo ? (
            /* Sidebar video list when a video is selected */
            <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1">
              {filteredVideos.map(video => {
                const cat = CATEGORIES_MAP[video.category] || CATEGORIES_MAP.getting_started;
                const CatIcon = cat.icon;
                const progress = userProgress[video.id];
                const isSelected = selectedVideo.id === video.id;

                return (
                  <button
                    key={video.id}
                    onClick={() => handleSelectVideo(video)}
                    className={`w-full flex gap-3 p-3 rounded-xl text-start transition-all ${
                      isSelected
                        ? 'bg-riadah-50 dark:bg-riadah-900/20 border border-riadah-200 dark:border-riadah-800'
                        : 'bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    {/* Thumbnail */}
                    <div className="relative w-28 h-16 rounded-lg overflow-hidden flex-shrink-0 bg-gray-200 dark:bg-gray-700">
                      {video.thumbnail ? (
                        <img src={video.thumbnail} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <CatIcon className="w-6 h-6 text-gray-400" />
                        </div>
                      )}
                      {/* Duration badge */}
                      <span className="absolute bottom-1 left-1 bg-black/75 text-white text-[10px] px-1.5 py-0.5 rounded-md font-medium">
                        {formatDuration(video.duration_seconds)}
                      </span>
                      {/* Progress bar */}
                      {progress && !progress.is_completed && (
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-400/30">
                          <div className="h-full bg-riadah-500 rounded-r" style={{ width: `${progress.progress_percent}%` }} />
                        </div>
                      )}
                      {/* Completed indicator */}
                      {progress?.is_completed && (
                        <div className="absolute top-1 right-1 w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                          <CheckCircle2 className="w-3 h-3 text-white" />
                        </div>
                      )}
                      {/* Playing indicator */}
                      {isSelected && (
                        <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                          <div className="w-8 h-8 bg-riadah-500/90 rounded-full flex items-center justify-center">
                            <Play className="w-4 h-4 text-white" />
                          </div>
                        </div>
                      )}
                    </div>
                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium truncate ${isSelected ? 'text-accent-500 dark:text-accent-400' : 'text-gray-900 dark:text-white'}`}>
                        {video.title_ar}
                      </p>
                      <p className="text-xs text-gray-500 mt-1 flex items-center gap-2">
                        <span className="flex items-center gap-1"><Eye className="w-3 h-3" />{video.views_count}</span>
                        <span className="flex items-center gap-1"><ThumbsUp className="w-3 h-3" />{video.likes_count}</span>
                      </p>
                      <span className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ backgroundColor: cat.color + '15', color: cat.color }}>
                        {getCategoryName(video.category)}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            /* Grid view when no video selected */
            filteredVideos.map(video => {
              const cat = CATEGORIES_MAP[video.category] || CATEGORIES_MAP.getting_started;
              const CatIcon = cat.icon;
              const progress = userProgress[video.id];

              return (
                <button
                  key={video.id}
                  onClick={() => handleSelectVideo(video)}
                  className="group bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] text-start"
                >
                  {/* Thumbnail */}
                  <div className="relative aspect-video bg-gray-200 dark:bg-gray-700 overflow-hidden">
                    {video.thumbnail ? (
                      <img src={video.thumbnail} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br" style={{ backgroundColor: cat.color + '15' }}>
                        <CatIcon className="w-12 h-12" style={{ color: cat.color + '60' }} />
                      </div>
                    )}
                    {/* Play overlay */}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all flex items-center justify-center">
                      <div className="w-12 h-12 bg-white/90 dark:bg-gray-900/90 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transform scale-75 group-hover:scale-100 transition-all shadow-lg">
                        <Play className="w-5 h-5 text-gray-900 dark:text-white" style={{ transform: isRTL ? 'scaleX(-1)' : '' }} />
                      </div>
                    </div>
                    {/* Duration */}
                    <span className="absolute bottom-2 left-2 bg-black/75 text-white text-xs px-2 py-0.5 rounded-md font-medium">
                      {formatDuration(video.duration_seconds)}
                    </span>
                    {/* Featured badge */}
                    {video.is_featured && (
                      <span className="absolute top-2 right-2 bg-yellow-500 text-white text-[10px] px-2 py-0.5 rounded-full font-bold flex items-center gap-1">
                        <Star className="w-3 h-3" /> {t('featured')}
                      </span>
                    )}
                    {/* Progress */}
                    {progress && !progress.is_completed && (
                      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-400/30">
                        <div className="h-full bg-riadah-500 rounded-r" style={{ width: `${progress.progress_percent}%` }} />
                      </div>
                    )}
                    {progress?.is_completed && (
                      <div className="absolute top-2 left-2">
                        <CheckCircle2 className="w-5 h-5 text-green-500 drop-shadow-lg" />
                      </div>
                    )}
                  </div>
                  {/* Content */}
                  <div className="p-4">
                    <h3 className="font-semibold text-sm text-gray-900 dark:text-white line-clamp-2 leading-tight">
                      {video.title_ar}
                    </h3>
                    {video.description_ar && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                        {video.description_ar}
                      </p>
                    )}
                    <div className="flex items-center justify-between mt-3">
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        <span className="flex items-center gap-1"><Eye className="w-3 h-3" />{video.views_count}</span>
                        <span className="flex items-center gap-1"><ThumbsUp className="w-3 h-3" />{video.likes_count}</span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ backgroundColor: cat.color + '15', color: cat.color }}>
                        {getCategoryName(video.category)}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Video Player Section */}
        {selectedVideo && (
          <div className="lg:col-span-2 space-y-4">
            {/* Video Player */}
            <div className="bg-black rounded-2xl overflow-hidden shadow-xl">
              <div className="relative aspect-video">
                {(() => {
                  const youtubeUrl = getYoutubeEmbedUrl(selectedVideo.video_source || selectedVideo.video_url);
                  if (youtubeUrl) {
                    return (
                      <iframe
                        src={`${youtubeUrl}?autoplay=1&rel=0`}
                        title={selectedVideo.title_ar}
                        className="w-full h-full"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      />
                    );
                  }
                  if (selectedVideo.video_file) {
                    return (
                      <video
                        ref={videoRef}
                        src={selectedVideo.video_file}
                        controls
                        autoPlay
                        className="w-full h-full"
                        onTimeUpdate={handleTimeUpdate}
                      >
                        <track kind="captions" />
                      </video>
                    );
                  }
                  if (selectedVideo.video_url) {
                    return (
                      <video
                        ref={videoRef}
                        src={selectedVideo.video_url}
                        controls
                        autoPlay
                        className="w-full h-full"
                        onTimeUpdate={handleTimeUpdate}
                      />
                    );
                  }
                  return (
                    <div className="w-full h-full flex flex-col items-center justify-center text-gray-500 bg-gray-900">
                      <AlertCircle className="w-12 h-12 mb-2" />
                      <p>No video source available</p>
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* Video Info */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div className="flex-1">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    {selectedVideoDetail?.title_ar || selectedVideo.title_ar}
                  </h2>
                  {selectedVideoDetail?.description_ar && (
                    <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm leading-relaxed">
                      {selectedVideoDetail.description_ar}
                    </p>
                  )}
                  <div className="flex flex-wrap items-center gap-4 mt-4">
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1.5">
                        <Eye className="w-4 h-4" />
                        {selectedVideoDetail?.views_count || selectedVideo.views_count} {t('videoViews')}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-4 h-4" />
                        {formatDuration(selectedVideo.duration_seconds)}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <ThumbsUp className="w-4 h-4" />
                        {selectedVideoDetail?.likes_count || selectedVideo.likes_count}
                      </span>
                    </div>
                    <span className="text-xs px-3 py-1 rounded-full font-medium" style={{
                      backgroundColor: (CATEGORIES_MAP[selectedVideo.category]?.color || '#3B82F6') + '15',
                      color: CATEGORIES_MAP[selectedVideo.category]?.color || '#3B82F6',
                    }}>
                      {getCategoryName(selectedVideo.category)}
                    </span>
                    <span className="text-xs px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-gray-600 dark:text-gray-400">
                      {t(selectedVideo.difficulty_level || 'beginner')}
                    </span>
                  </div>
                  {/* Progress indicator */}
                  {userProgress[selectedVideo.id] && (
                    <div className="mt-4">
                      <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                        <span>{t('videoProgress')}</span>
                        <span className="font-bold text-accent-500 dark:text-accent-400">
                          {userProgress[selectedVideo.id].progress_percent}%
                        </span>
                        {userProgress[selectedVideo.id].is_completed && (
                          <CheckCircle2 className="w-4 h-4 text-green-500" />
                        )}
                      </div>
                      <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${userProgress[selectedVideo.id].is_completed ? 'bg-green-500' : 'bg-riadah-500'}`}
                          style={{ width: `${userProgress[selectedVideo.id].progress_percent}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
                {/* Action buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleLike(selectedVideo.id)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-red-500 transition-all"
                  >
                    <Heart className="w-4 h-4" /> {t('likeVideo')}
                  </button>
                  <button
                    onClick={() => {
                      if (navigator.share) {
                        navigator.share({ title: selectedVideo.title_ar, url: window.location.href });
                      } else {
                        navigator.clipboard.writeText(window.location.href);
                        toast.success(locale === 'ar' ? 'تم نسخ الرابط' : 'Link copied');
                      }
                    }}
                    className="flex items-center gap-1.5 px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-riadah-50 dark:hover:bg-riadah-900/20 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-accent-500 transition-all"
                  >
                    <Share2 className="w-4 h-4" /> {t('shareVideo')}
                  </button>
                  {isAdmin && (
                    <button
                      onClick={() => handleDeleteVideo(selectedVideo.id)}
                      className="flex items-center gap-1.5 px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-red-500 transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Comments Section */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                <MessageCircle className="w-5 h-5" />
                {t('videoComments')} ({comments.length})
              </h3>
              {/* Add comment */}
              <div className="flex gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-riadah-300 to-riadah-500 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                  {user?.first_name?.[0] || user?.username?.[0] || 'م'}
                </div>
                <div className="flex-1 flex gap-2">
                  <input
                    type="text"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddComment()}
                    placeholder={t('commentPlaceholder')}
                    className="flex-1 px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-gray-900 dark:text-white"
                  />
                  <button
                    onClick={handleAddComment}
                    disabled={!newComment.trim()}
                    className="px-4 py-2 bg-riadah-500 hover:bg-riadah-600 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white rounded-xl text-sm font-medium transition-all disabled:cursor-not-allowed"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
              {/* Comments list */}
              {comments.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-4">{t('noComments')}</p>
              ) : (
                <div className="space-y-4 max-h-80 overflow-y-auto">
                  {comments.map(comment => (
                    <div key={comment.id} className="flex gap-3 group">
                      <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center text-xs font-bold text-gray-600 dark:text-gray-300 flex-shrink-0">
                        {(comment.user_name || comment.user_username || 'م')[0]}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-gray-900 dark:text-white">
                            {comment.user_name || comment.user_username}
                          </span>
                          <span className="text-xs text-gray-400">{comment.created_at}</span>
                          {comment.is_pinned && <span className="text-[10px] bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded-full">{t('featured')}</span>}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{comment.comment}</p>
                        {(comment.user === user?.id || isAdmin) && (
                          <button
                            onClick={() => handleDeleteComment(comment.id)}
                            className="text-xs text-red-500 hover:text-red-600 mt-1 opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Trash2 className="w-3 h-3 inline" /> {t('delete')}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Related Videos */}
            {selectedVideoDetail?.related_videos?.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                <h3 className="font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                  <ArrowRight className="w-5 h-5" />
                  {t('relatedVideos')}
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {selectedVideoDetail.related_videos.map(rv => {
                    const cat = CATEGORIES_MAP[rv.category] || CATEGORIES_MAP.getting_started;
                    const CatIcon = cat.icon;
                    return (
                      <button
                        key={rv.id}
                        onClick={() => handleSelectVideo(rv)}
                        className="flex gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-all text-start"
                      >
                        <div className="w-20 h-14 rounded-lg bg-gray-200 dark:bg-gray-600 flex-shrink-0 flex items-center justify-center overflow-hidden">
                          {rv.thumbnail ? (
                            <img src={rv.thumbnail} alt="" className="w-full h-full object-cover" />
                          ) : (
                            <CatIcon className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{rv.title_ar}</p>
                          <p className="text-xs text-gray-500 mt-0.5">{formatDuration(rv.duration_seconds)}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Close video button */}
            <button
              onClick={() => { setSelectedVideo(null); setSelectedVideoDetail(null); setComments([]); }}
              className="w-full py-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 transition-all flex items-center justify-center gap-2"
            >
              <X className="w-4 h-4" />
              {t('back')}
            </button>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {uploadModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setUploadModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-700">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Upload className="w-5 h-5" /> {t('videoUploadTitle')}
              </h2>
              <button onClick={() => setUploadModal(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <form onSubmit={handleUpload} className="p-6 space-y-4">
              {/* Title Arabic */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('videoTitle')} (عربي)</label>
                <input
                  type="text"
                  required
                  value={uploadForm.title_ar}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, title_ar: e.target.value }))}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-gray-900 dark:text-white"
                />
              </div>
              {/* Title English */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('videoTitle')} (English)</label>
                <input
                  type="text"
                  value={uploadForm.title_en}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, title_en: e.target.value }))}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-gray-900 dark:text-white"
                  dir="ltr"
                />
              </div>
              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('videoDescription')} (عربي)</label>
                <textarea
                  rows={3}
                  value={uploadForm.description_ar}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, description_ar: e.target.value }))}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-gray-900 dark:text-white resize-none"
                />
              </div>
              {/* Video URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('videoUrl')}</label>
                <input
                  type="url"
                  required
                  value={uploadForm.video_url}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, video_url: e.target.value }))}
                  placeholder={t('videoUrlPlaceholder')}
                  dir="ltr"
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-gray-900 dark:text-white"
                />
              </div>
              {/* Category & Difficulty */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('videoCategories')}</label>
                  <select
                    value={uploadForm.category}
                    onChange={(e) => setUploadForm(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-gray-900 dark:text-white appearance-none"
                  >
                    {Object.keys(CATEGORIES_MAP).map(key => (
                      <option key={key} value={key}>{getCategoryName(key)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('videoDifficulty')}</label>
                  <select
                    value={uploadForm.difficulty_level}
                    onChange={(e) => setUploadForm(prev => ({ ...prev, difficulty_level: e.target.value }))}
                    className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-gray-900 dark:text-white appearance-none"
                  >
                    <option value="beginner">{t('beginner')}</option>
                    <option value="intermediate">{t('intermediate')}</option>
                    <option value="advanced">{t('advanced')}</option>
                  </select>
                </div>
              </div>
              {/* Duration */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('videoDuration')} ({locale === 'ar' ? 'بالثواني' : 'in seconds'})</label>
                <input
                  type="number"
                  min="0"
                  value={uploadForm.duration_seconds}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, duration_seconds: parseInt(e.target.value) || 0 }))}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-gray-900 dark:text-white"
                />
              </div>
              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('videoTags')}</label>
                <input
                  type="text"
                  value={uploadForm.tags}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, tags: e.target.value }))}
                  placeholder={locale === 'ar' ? 'مفصولة بفواصل: مخزون, منتجات, رصيد' : 'comma separated: inventory, products, balance'}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none text-gray-900 dark:text-white"
                />
              </div>
              {/* Featured toggle */}
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={uploadForm.is_featured}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, is_featured: e.target.checked }))}
                  className="w-4 h-4 rounded border-gray-300 text-accent-500 focus:ring-accent-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">{t('featured')}</span>
              </label>
              {/* Submit */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  className="flex-1 py-3 bg-gradient-to-r from-riadah-500 to-riadah-500 hover:from-riadah-500 hover:to-riadah-700 text-white rounded-xl font-medium shadow-lg shadow-riadah-500/25 transition-all"
                >
                  {t('videoUpload')}
                </button>
                <button
                  type="button"
                  onClick={() => setUploadModal(false)}
                  className="px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-all"
                >
                  {t('cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
