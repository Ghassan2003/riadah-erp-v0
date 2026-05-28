/**
 * ChatWidget — Floating mini-chat widget for RIADAH ERP.
 *
 * Features:
 *  - Floating button with bounce animation (bottom-left for RTL)
 *  - Popup mini-chat window with header, messages, and input
 *  - Uses inline fetch for API calls (no external api import)
 *  - Auth token from localStorage (key: 'access_token')
 *  - Auto-scroll on new messages
 *  - Typing indicator while waiting for response
 *  - Inline **bold** formatting
 *  - Dark mode support
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Send,
  MessageSquare,
  X,
  Bot,
  User,
  Loader2,
  Minimize2,
} from 'lucide-react';

/* ─── Helpers ─── */

const API_BASE = '/api';

/** Get the stored JWT access token. */
function getToken() {
  return localStorage.getItem('access_token') || null;
}

/** Convert **text** to <strong>text</strong>. */
const formatBold = (text) => {
  const parts = text.split(/\*\*(.*?)\*\*/g);
  if (parts.length === 1) return text;
  return parts.map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part,
  );
};

/** Format time for message timestamp. */
function formatTime(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleTimeString('ar-SA', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/* ─── Component ─── */

export default function ChatWidget() {
  /* ── State ── */
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]); // { id, role, content, created_at }
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [minimized, setMinimized] = useState(false);

  /* ── Refs ── */
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const inactivityTimer = useRef(null);
  const widgetContainerRef = useRef(null);

  /* ── Auto-scroll ── */
  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending, scrollToBottom]);

  /* ── Auto-open input focus when opened ── */
  useEffect(() => {
    if (open && !minimized) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [open, minimized]);

  /* ── Auto-hide after 3 minutes of inactivity ── */
  const resetInactivity = useCallback(() => {
    if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
    inactivityTimer.current = setTimeout(() => {
      if (open) {
        setMinimized(true);
      }
    }, 180_000); // 3 min
  }, [open]);

  useEffect(() => {
    if (open && !minimized) {
      window.addEventListener('mousemove', resetInactivity);
      window.addEventListener('keydown', resetInactivity);
      resetInactivity();
    }
    return () => {
      window.removeEventListener('mousemove', resetInactivity);
      window.removeEventListener('keydown', resetInactivity);
      if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
    };
  }, [open, minimized, resetInactivity]);

  /* ── Send message ── */
  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;

    const token = getToken();
    if (!token) return;

    // Optimistic user message
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const res = await fetch(`${API_BASE}/chatbot/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId || undefined,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'فشل في إرسال الرسالة');
      }

      const data = await res.json();

      const assistantMsg = {
        id: data.message_id || Date.now() + 1,
        role: 'assistant',
        content: data.response,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id);
      }
    } catch (err) {
      // Show error as assistant message
      const errorMsg = {
        id: Date.now() + 2,
        role: 'assistant',
        content: `⚠️ ${err.message || 'حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.'}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      // Remove optimistic message on failure
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    } finally {
      setSending(false);
      inputRef.current?.focus();
      resetInactivity();
    }
  }, [input, sending, conversationId, resetInactivity]);

  /* ── Keyboard handler ── */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /* ── Reset conversation ── */
  const startNewChat = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    inputRef.current?.focus();
  }, []);

  /* ────────────────────────────────────────
     Render
     ──────────────────────────────────────── */

  return (
    <div ref={widgetContainerRef} className="fixed bottom-6 left-6 z-50 flex flex-col items-end gap-3" dir="rtl">
      {/* ── Chat popup window ── */}
      <div
        className={`
          ${open && !minimized ? 'opacity-100 scale-100 pointer-events-auto' : 'opacity-0 scale-90 pointer-events-none'}
          w-[370px] max-w-[calc(100vw-2rem)] h-[520px] max-h-[calc(100vh-8rem)]
          rounded-2xl overflow-hidden
          bg-white dark:bg-gray-900
          border border-gray-200 dark:border-gray-700/60
          shadow-2xl shadow-black/10 dark:shadow-black/30
          flex flex-col
          transition-all duration-300 ease-out
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-l from-riadah-500 to-riadah-700 dark:from-riadah-600 dark:to-riadah-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
              <Bot className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">المساعد الذكي</h3>
              <p className="text-[10px] text-riadah-200 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                متصل الآن
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {/* Minimize */}
            <button
              onClick={() => setMinimized(true)}
              className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
              title="تصغير"
            >
              <Minimize2 className="w-4 h-4" />
            </button>
            {/* New chat */}
            <button
              onClick={startNewChat}
              className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
              title="محادثة جديدة"
            >
              <MessageSquare className="w-4 h-4" />
            </button>
            {/* Close */}
            <button
              onClick={() => setOpen(false)}
              className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
              title="إغلاق"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-gray-50/50 dark:bg-gray-900/50">
          {messages.length === 0 ? (
            /* Welcome state */
            <div className="flex items-center justify-center h-full">
              <div className="text-center px-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-bl from-accent-500/15 to-riadah-500/15 dark:from-accent-500/10 dark:to-riadah-500/10 flex items-center justify-center mx-auto mb-4">
                  <Bot className="w-7 h-7 text-accent-500" />
                </div>
                <h4 className="text-base font-bold text-gray-800 dark:text-gray-100 mb-1.5">
                  المساعد الذكي
                </h4>
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed mb-4">
                  مرحباً! كيف يمكنني مساعدتك اليوم؟
                </p>
                <div className="flex flex-wrap justify-center gap-1.5">
                  {['ملخص المبيعات', 'الموظفون', 'التقارير'].map((s, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setInput(s);
                        inputRef.current?.focus();
                      }}
                      className="px-2.5 py-1 text-[11px] font-medium rounded-full border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-accent-500/10 hover:border-accent-500/30 hover:text-accent-600 dark:hover:text-accent-400 transition-all"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-end gap-2 ${
                  msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                }`}
              >
                {/* Avatar */}
                <div
                  className={`
                    w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0
                    ${
                      msg.role === 'user'
                        ? 'bg-riadah-500 text-white'
                        : 'bg-gradient-to-bl from-accent-500 to-accent-600 text-white'
                    }
                  `}
                >
                  {msg.role === 'user' ? (
                    <User className="w-3.5 h-3.5" />
                  ) : (
                    <Bot className="w-3.5 h-3.5" />
                  )}
                </div>

                {/* Bubble */}
                <div
                  className={`
                    max-w-[80%] px-3.5 py-2.5 rounded-2xl shadow-sm
                    ${
                      msg.role === 'user'
                        ? 'bg-riadah-500 text-white rounded-tr-md'
                        : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-tl-md border border-gray-200/60 dark:border-gray-700/40'
                    }
                  `}
                >
                  <div
                    className={`text-[13px] leading-relaxed whitespace-pre-wrap break-words ${
                      msg.role === 'user' ? 'text-white/95' : ''
                    }`}
                  >
                    {msg.role === 'assistant' ? formatBold(msg.content) : msg.content}
                  </div>
                  <p
                    className={`text-[8px] mt-1 ${
                      msg.role === 'user'
                        ? 'text-riadah-300/50'
                        : 'text-gray-400 dark:text-gray-500'
                    }`}
                  >
                    {formatTime(msg.created_at)}
                  </p>
                </div>
              </div>
            ))
          )}

          {/* Typing indicator */}
          {sending && (
            <div className="flex items-end gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-bl from-accent-500 to-accent-600 flex items-center justify-center flex-shrink-0">
                <Bot className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="bg-white dark:bg-gray-800 px-3.5 py-2.5 rounded-2xl rounded-tl-md border border-gray-200/60 dark:border-gray-700/40 shadow-sm">
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-3 py-2.5 border-t border-gray-200 dark:border-gray-700/60 bg-white dark:bg-gray-900">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="اكتب رسالتك..."
              disabled={sending}
              rows={1}
              className="
                flex-1 px-3 py-2.5 rounded-xl text-[13px] resize-none
                bg-gray-100 dark:bg-gray-800
                border border-gray-200 dark:border-gray-700
                text-gray-800 dark:text-gray-200
                placeholder-gray-400 dark:placeholder-gray-500
                focus:outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-150
              "
              style={{ minHeight: '40px', maxHeight: '90px' }}
              onInput={(e) => {
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 90) + 'px';
              }}
            />
            <button
              onClick={sendMessage}
              disabled={sending || !input.trim()}
              className="
                flex-shrink-0 w-9 h-9 rounded-xl
                bg-gradient-to-bl from-accent-500 to-accent-600
                text-white shadow-sm hover:shadow-md
                hover:from-accent-600 hover:to-accent-700
                disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none
                flex items-center justify-center
                transition-all duration-150 active:scale-95
              "
            >
              {sending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ── Minimized indicator ── */}
      {open && minimized && (
        <div
          className="
            flex items-center gap-2 px-3 py-2 rounded-full cursor-pointer
            bg-riadah-500 text-white shadow-lg hover:shadow-xl
            animate-fade-in transition-shadow duration-200
          "
          onClick={() => setMinimized(false)}
        >
          <Bot className="w-4 h-4" />
          <span className="text-xs font-medium">المساعد الذكي</span>
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        </div>
      )}

      {/* ── Floating action button ── */}
      {!open && (
        <button
          onClick={() => {
            setOpen(true);
            setMinimized(false);
          }}
          className="
            group relative w-14 h-14 rounded-full
            bg-gradient-to-bl from-accent-500 to-riadah-600
            text-white shadow-lg shadow-accent-500/30 hover:shadow-xl hover:shadow-accent-500/40
            flex items-center justify-center
            transition-all duration-300 ease-out
            animate-bounce-subtle
            hover:scale-110 active:scale-95
          "
          title="المساعد الذكي"
        >
          {/* Pulse ring */}
          <span className="absolute inset-0 rounded-full bg-accent-500 animate-ping opacity-20" />

          {/* Icon */}
          <MessageSquare className="w-6 h-6 relative z-10" />

          {/* Badge dot (notification feel) */}
          <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 border-2 border-white dark:border-gray-900 rounded-full" />
        </button>
      )}
    </div>
  );
}
