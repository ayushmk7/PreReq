import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { MessageCircle, X, Send, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { chatService } from '../services/chatService';

interface ChatbotProps {
  examId?: string | null;
}

const MarkdownMessage: React.FC<{ content: string }> = ({ content }) => {
  return (
    <div className="text-sm leading-relaxed space-y-2">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="my-1 whitespace-pre-wrap">{children}</p>,
          ul: ({ children }) => <ul className="list-disc pl-5 my-2 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 my-2 space-y-1">{children}</ol>,
          li: ({ children }) => <li>{children}</li>,
          h1: ({ children }) => <h1 className="text-base font-semibold mt-2 mb-1">{children}</h1>,
          h2: ({ children }) => <h2 className="text-sm font-semibold mt-2 mb-1">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1">{children}</h3>,
          code: ({ className, children }) => {
            const isInline = !className;
            if (isInline) {
              return <code className="px-1 py-0.5 rounded bg-surface text-xs">{children}</code>;
            }
            return (
              <pre className="my-2 p-2 rounded-lg bg-surface overflow-x-auto">
                <code className="text-xs">{children}</code>
              </pre>
            );
          },
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer noopener"
              className="underline underline-offset-2 text-blue-700"
            >
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="my-2 overflow-x-auto">
              <table className="min-w-full border border-border rounded-lg text-xs">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-surface">{children}</thead>,
          th: ({ children }) => <th className="border border-border px-2 py-1 text-left font-semibold">{children}</th>,
          td: ({ children }) => <td className="border border-border px-2 py-1 align-top">{children}</td>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-border pl-3 italic text-muted-foreground my-2">
              {children}
            </blockquote>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export const Chatbot: React.FC<ChatbotProps> = ({ examId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Array<{ text: string; isBot: boolean }>>([
    { text: "Hi! I'm your PreReq assistant. Ask me anything about your exam data.", isBot: true },
  ]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!isOpen) return;

    let cancelled = false;

    const checkStatus = async () => {
      setStatus('checking');
      const online = await chatService.isOnline();
      if (!cancelled) {
        setStatus(online ? 'online' : 'offline');
      }
    };

    void checkStatus();
    const interval = window.setInterval(checkStatus, 30000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [isOpen]);

  const handleSend = async () => {
    if (!input.trim() || sending || status !== 'online') return;
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { text: userMsg, isBot: false }]);
    setSending(true);

    try {
      let sid = sessionId;
      if (!sid) {
        const session = await chatService.createSession({
          exam_id: examId ?? undefined,
          title: userMsg.slice(0, 60),
        });
        sid = session.id;
        setSessionId(sid);
      }
      const res = await chatService.sendMessage(sid!, { message: userMsg, exam_id: examId ?? undefined });
      setMessages(prev => [...prev, { text: res.assistant_message, isBot: true }]);
    } catch {
      setMessages(prev => [...prev, { text: 'Sorry, something went wrong. Please try again.', isBot: true }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-[#00274C] text-white shadow-lg hover:shadow-xl flex items-center justify-center z-50 transition-shadow"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.div key="close" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.2 }}>
              <X className="w-6 h-6" />
            </motion.div>
          ) : (
            <motion.div key="open" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.2 }}>
              <MessageCircle className="w-6 h-6" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 right-6 w-96 h-[32rem] bg-white rounded-2xl shadow-2xl border border-border z-50 flex flex-col overflow-hidden"
          >
            <div className="bg-[#00274C] text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`w-3 h-3 rounded-full ${
                    status === 'online'
                      ? 'bg-[#FFCB05] animate-pulse'
                      : status === 'checking'
                        ? 'bg-gray-300 animate-pulse'
                        : 'bg-red-400'
                  }`}
                />
                <div>
                  <h3 className="font-medium">PreReq Assistant</h3>
                  <p className="text-xs opacity-75">
                    {sending
                      ? 'Thinking...'
                      : status === 'checking'
                        ? 'Checking...'
                        : status === 'online'
                          ? 'Online'
                          : 'Offline'}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-surface">
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
                >
                  <div className={`max-w-[80%] px-4 py-2 rounded-2xl ${message.isBot ? 'bg-white text-foreground border border-border' : 'bg-[#00274C] text-white'}`}>
                    {message.isBot ? (
                      <MarkdownMessage content={message.text} />
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                    )}
                  </div>
                </motion.div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="px-4 py-2 rounded-2xl bg-white text-foreground border border-border">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <div className="p-4 bg-white border-t border-border">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-2 bg-surface border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  disabled={sending || status !== 'online'}
                />
                <button
                  onClick={handleSend}
                  disabled={sending || !input.trim() || status !== 'online'}
                  className="w-10 h-10 rounded-xl bg-[#FFCB05] text-[#00274C] flex items-center justify-center hover:bg-[#FFD633] transition-colors disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
