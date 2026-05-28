/**
 * ChatbotPage — Full-page AI chatbot interface for RIADAH ERP.
 *
 * Features:
 *  - Left sidebar with conversation history (RTL: right side in visual layout)
 *  - Main chat area with user / assistant message bubbles
 *  - Input bar with send button
 *  - New Conversation button
 *  - Auto-scroll on new messages
 *  - Loading indicator while waiting for AI response
 *  - Inline **bold** formatting for assistant responses
 *  - Glass-morphism + dark mode support
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useTheme } from '../context/ThemeContext';
import { chatbotAPI } from '../api';
import {
  Send,
  Plus,
  MessageSquare,
  Trash2,
  Bot,
  User,
  Loader2,
  X,
  Menu,
  PanelRightOpen,
} from 'lucide-react';
import toast from 'react-hot-toast';

/* ─── Helpers ─── */

/** Convert **text** to <strong>text</strong> for simple markdown bold. */
const formatBold = (text) => {
  // Split on **...** patterns while preserving everything else.
  const parts = text.split(/\*\*(.*?)\*\*/g);
  if (parts.length === 1) return text; // no bold markers
  return parts.map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part,
  );
};

/** Format an ISO date string into a readable Arabic-friendly relative time. */
function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'الآن';
  if (mins < 60) return `منذ ${mins} دقيقة`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `منذ ${hrs} ساعة`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `منذ ${days} يوم`;
  return new Date(dateStr).toLocaleDateString('ar-SA', {
    month: 'short',
    day: 'numeric',
  });
}

function truncate(str, max = 36) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '...' : str;
}

/* ─── Component ─── */

export default function ChatbotPage() {
  const { isDark } = useTheme();

  /* ── State ── */
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);        // { id, role, content, created_at }
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingConv, setLoadingConv] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true); // responsive toggle

  /* ── Refs ── */
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  /* ── Scroll to bottom ── */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending, scrollToBottom]);

  /* ────────────────────────────────────────
     API helpers
     ──────────────────────────────────────── */

  /** Fetch the list of conversations. */
  const fetchConversations = useCallback(async () => {
    try {
      const res = await chatbotAPI.listConversations();
      setConversations(res.data?.results || res.data || []);
    } catch {
      // silent — conversations list is non-critical
    }
  }, []);

  /** Load messages for a specific conversation. */
  const loadConversation = useCallback(async (convId) => {
    setActiveConvId(convId);
    setLoadingConv(true);
    try {
      const res = await chatbotAPI.getConversation(convId);
      setMessages(res.data?.messages || []);
    } catch {
      toast.error('فشل في تحميل المحادثة');
      setMessages([]);
    } finally {
      setLoadingConv(false);
      inputRef.current?.focus();
    }
  }, []);

  /** Delete a conversation and reset state if it was active. */
  const deleteConversation = useCallback(
    async (convId, e) => {
      e?.stopPropagation();
      try {
        await chatbotAPI.deleteConversation(convId);
        setConversations((prev) => prev.filter((c) => c.id !== convId));
        if (activeConvId === convId) {
          setActiveConvId(null);
          setMessages([]);
        }
        toast.success('تم حذف المحادثة');
      } catch {
        toast.error('فشل في حذف المحادثة');
      }
    },
    [activeConvId],
  );

  /** Send a message and append the AI response. */
  const sendMessage = useCallback(async () => {
    const text = inputValue.trim();
    if (!text || sending) return;

    // Optimistically add user message to the UI
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setSending(true);

    try {
      const res = await chatbotAPI.sendMessage({
        message: text,
        conversation_id: activeConvId || undefined,
      });

      const { response, conversation_id } = res.data;

      // Add assistant message
      const assistantMsg = {
        id: res.data.message_id || Date.now() + 1,
        role: 'assistant',
        content: response,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // If this was a new conversation (no activeConvId), set it now
      if (!activeConvId && conversation_id) {
        setActiveConvId(conversation_id);
      }

      // Refresh conversations list to update titles / ordering
      fetchConversations();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'حدث خطأ أثناء إرسال الرسالة';
      toast.error(msg);
      // Remove optimistic user message on failure
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }, [inputValue, sending, activeConvId, fetchConversations]);

  /* ── Initial load ── */
  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  /* ── Keyboard handler ── */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /* ────────────────────────────────────────
     Render
     ──────────────────────────────────────── */

  return (
    <div className="flex h-[calc(100vh-80px)] min-h-[500px] gap-0 rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-700/60 bg-white dark:bg-gray-900 shadow-sm animate-fade-in">
      {/* ── Sidebar overlay for mobile ── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ── */}
      <aside
        className={`
          ${sidebarOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
          fixed lg:static inset-y-0 right-0 z-30 lg:z-auto
          w-72 lg:w-64 xl:w-72 flex-shrink-0
          flex flex-col
          bg-gray-50/80 dark:bg-gray-800/80 backdrop-blur-xl
          border-l border-gray-200 dark:border-gray-700/60
          transition-transform duration-300 ease-in-out
        `}
      >
        {/* Sidebar header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700/60">
          <h2 className="text-sm font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-accent-500" />
            المحادثات
          </h2>
          <div className="flex items-center gap-1">
            {/* New Conversation button */}
            <button
              onClick={() => {
                setActiveConvId(null);
                setMessages([]);
                setSidebarOpen(false);
                inputRef.current?.focus();
              }}
              className="p-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-accent-500/10 hover:text-accent-500 transition-colors"
              title="محادثة جديدة"
            >
              <Plus className="w-4 h-4" />
            </button>
            {/* Close sidebar on mobile */}
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors lg:hidden"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-3">
                <MessageSquare className="w-5 h-5 text-gray-400 dark:text-gray-500" />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                لا توجد محادثات سابقة
                <br />
                ابدأ محادثة جديدة مع المساعد الذكي
              </p>
            </div>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => {
                  loadConversation(conv.id);
                  setSidebarOpen(false);
                }}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-right transition-all duration-150 group
                  ${
                    activeConvId === conv.id
                      ? 'bg-accent-500/10 dark:bg-accent-500/15 border border-accent-500/30 shadow-sm'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-700/50 border border-transparent'
                  }
                `}
              >
                {/* Icon */}
                <div
                  className={`
                    w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                    ${
                      activeConvId === conv.id
                        ? 'bg-accent-500/20 text-accent-500'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                    }
                  `}
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-sm font-medium truncate ${
                      activeConvId === conv.id
                        ? 'text-accent-600 dark:text-accent-400'
                        : 'text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {truncate(conv.title, 28)}
                  </p>
                  <div className="flex items-center justify-between mt-0.5">
                    <span className="text-[10px] text-gray-400 dark:text-gray-500">
                      {timeAgo(conv.created_at)}
                    </span>
                    {conv.message_count > 0 && (
                      <span className="text-[10px] text-gray-400 dark:text-gray-500">
                        {conv.message_count} رسالة
                      </span>
                    )}
                  </div>
                </div>

                {/* Delete button */}
                <button
                  onClick={(e) => deleteConversation(conv.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-500/10 transition-all flex-shrink-0"
                  title="حذف المحادثة"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </button>
            ))
          )}
        </div>

        {/* Sidebar footer */}
        <div className="p-3 border-t border-gray-200 dark:border-gray-700/60">
          <button
            onClick={() => {
              setActiveConvId(null);
              setMessages([]);
              setSidebarOpen(false);
              inputRef.current?.focus();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-white bg-gradient-to-l from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 shadow-md hover:shadow-lg transition-all duration-200 active:scale-[0.97]"
          >
            <Plus className="w-4 h-4" />
            محادثة جديدة
          </button>
        </div>
      </aside>

      {/* ── Main Chat Area ── */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Chat header */}
        <div className="flex items-center justify-between px-4 sm:px-6 py-3.5 border-b border-gray-200 dark:border-gray-700/60 glass">
          <div className="flex items-center gap-3">
            {/* Open sidebar button (mobile or collapsed) */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors lg:hidden"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-bl from-accent-500 to-riadah-600 flex items-center justify-center shadow-md">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-gray-800 dark:text-gray-100">
                  المساعد الذكي
                </h1>
                <p className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                  متصل الآن
                </p>
              </div>
            </div>
          </div>

          {/* Open sidebar on desktop (when collapsed) */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="hidden lg:flex p-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="فتح قائمة المحادثات"
          >
            <PanelRightOpen className="w-5 h-5" />
          </button>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-4">
          {loadingConv ? (
            /* Loading conversation */
            <div className="flex items-center justify-center h-full">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  جاري تحميل المحادثة...
                </p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            /* Empty state — welcome screen */
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md px-4">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-bl from-accent-500/20 to-riadah-500/20 dark:from-accent-500/10 dark:to-riadah-500/10 flex items-center justify-center mx-auto mb-5 shadow-inner">
                  <Bot className="w-10 h-10 text-accent-500" />
                </div>
                <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-2">
                  مرحباً بك في المساعد الذكي
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-6">
                  يمكنني مساعدتك في إدارة نظام ريادة ERP.
                  <br />
                  اسألني عن المبيعات، الموظفين، التقارير المالية، والمزيد.
                </p>

                {/* Suggestion chips */}
                <div className="flex flex-wrap justify-center gap-2">
                  {[
                    'ما هي المبيعات لهذا الشهر؟',
                    'أظهر لي تقرير الموظفين',
                    'ما هي الفواتير المعلقة؟',
                    'ملخص الوضع المالي',
                  ].map((suggestion, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setInputValue(suggestion);
                        inputRef.current?.focus();
                      }}
                      className="px-3 py-1.5 text-xs font-medium rounded-full border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-accent-500/10 hover:border-accent-500/30 hover:text-accent-600 dark:hover:text-accent-400 transition-all duration-150"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Messages */
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-end gap-2.5 ${
                  msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                }`}
              >
                {/* Avatar */}
                <div
                  className={`
                    w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm
                    ${
                      msg.role === 'user'
                        ? 'bg-riadah-500 text-white'
                        : 'bg-gradient-to-bl from-accent-500 to-accent-600 text-white'
                    }
                  `}
                >
                  {msg.role === 'user' ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                </div>

                {/* Bubble */}
                <div
                  className={`
                    max-w-[75%] sm:max-w-[70%] lg:max-w-[65%] px-4 py-3 rounded-2xl shadow-sm
                    ${
                      msg.role === 'user'
                        ? 'bg-riadah-500 text-white rounded-tr-md'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-tl-md border border-gray-200/60 dark:border-gray-700/40'
                    }
                  `}
                >
                  {/* Role label */}
                  <p
                    className={`text-[10px] font-semibold mb-1 ${
                      msg.role === 'user'
                        ? 'text-riadah-200'
                        : 'text-accent-500'
                    }`}
                  >
                    {msg.role === 'user' ? 'أنت' : 'المساعد الذكي'}
                  </p>

                  {/* Content */}
                  <div
                    className={`text-sm leading-relaxed whitespace-pre-wrap break-words ${
                      msg.role === 'user' ? 'text-white/95' : ''
                    }`}
                  >
                    {msg.role === 'assistant' ? formatBold(msg.content) : msg.content}
                  </div>

                  {/* Timestamp */}
                  <p
                    className={`text-[9px] mt-1.5 ${
                      msg.role === 'user'
                        ? 'text-riadah-300/60'
                        : 'text-gray-400 dark:text-gray-500'
                    }`}
                  >
                    {msg.created_at
                      ? new Date(msg.created_at).toLocaleTimeString('ar-SA', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      : ''}
                  </p>
                </div>
              </div>
            ))
          )}

          {/* Typing indicator */}
          {sending && (
            <div className="flex items-end gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-bl from-accent-500 to-accent-600 flex items-center justify-center flex-shrink-0 shadow-sm">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-gray-100 dark:bg-gray-800 px-4 py-3 rounded-2xl rounded-tl-md border border-gray-200/60 dark:border-gray-700/40 shadow-sm">
                <p className="text-[10px] font-semibold text-accent-500 mb-1.5">
                  المساعد الذكي
                </p>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="px-4 sm:px-6 py-3.5 border-t border-gray-200 dark:border-gray-700/60 glass">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="اكتب رسالتك هنا..."
                disabled={sending}
                rows={1}
                className="
                  w-full px-4 py-3 rounded-xl text-sm resize-none
                  bg-gray-100 dark:bg-gray-800
                  border border-gray-200 dark:border-gray-700
                  text-gray-800 dark:text-gray-200
                  placeholder-gray-400 dark:placeholder-gray-500
                  focus:outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500
                  disabled:opacity-50 disabled:cursor-not-allowed
                  transition-all duration-150
                "
                style={{ minHeight: '44px', maxHeight: '120px' }}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                }}
              />
            </div>

            <button
              onClick={sendMessage}
              disabled={sending || !inputValue.trim()}
              className="
                flex-shrink-0 w-11 h-11 rounded-xl
                bg-gradient-to-bl from-accent-500 to-accent-600
                text-white shadow-md hover:shadow-lg
                hover:from-accent-600 hover:to-accent-700
                disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none
                flex items-center justify-center
                transition-all duration-150 active:scale-95
              "
            >
              {sending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Hint */}
          <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-2 text-center">
            اضغط Enter للإرسال · Shift+Enter لسطر جديد
          </p>
        </div>
      </main>
    </div>
  );
}
