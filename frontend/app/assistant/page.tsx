"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { api } from "@/lib/api";
import {
  MessageSquareText,
  Send,
  Sparkles,
  Copy,
  Check,
  Smartphone,
  ExternalLink,
  Bot,
  User,
  RefreshCw,
  HelpCircle,
} from "lucide-react";
import { AssistantChatMessage } from "@/types";

const SUGGESTED_QUESTIONS = [
  "Mera sabse bada loss-making product kaunsa hai?",
  "What is my real net profit and margin this month?",
  "How much GST ITC can I claim in GSTR-3B Table 4?",
  "Which PPC campaigns are bleeding money?",
  "What is my courier RTO rate on Cash-on-Delivery?",
];

interface ExtendedChatMessage extends AssistantChatMessage {
  context_tags?: string[];
  suggested_followups?: string[];
}

export default function AssistantPage() {
  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState<ExtendedChatMessage[]>([
    {
      role: "assistant",
      content:
        "Namaste! How can I help you with your store's profits, fees, or inventory today?",
    },
  ]);
  const [suggestedFollowups, setSuggestedFollowups] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch WhatsApp Daily Morning Digest
  const { data: whatsappData, isLoading: isLoadingWhatsapp } = useQuery({
    queryKey: ["whatsappDigest"],
    queryFn: () => api.getWhatsAppDigest(),
  });

  const chatMutation = useMutation({
    mutationFn: (variables: { message: string; conversation_history: AssistantChatMessage[] }) =>
      api.chatWithAssistant(variables),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          context_tags: data.context_tags,
          suggested_followups: data.suggested_followups,
        },
      ]);
      if (data.suggested_followups && data.suggested_followups.length > 0) {
        setSuggestedFollowups(data.suggested_followups);
      }
    },
  });

  const handleSend = (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || chatMutation.isPending) return;

    const userMessage: ExtendedChatMessage = { role: "user", content: text };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputMessage("");

    // Send the last 8 messages as conversation context
    const history: AssistantChatMessage[] = updatedMessages.slice(-8).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    chatMutation.mutate({
      message: text,
      conversation_history: history,
    });
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatMutation.isPending]);

  const copyWhatsApp = () => {
    if (whatsappData?.message_text) {
      navigator.clipboard.writeText(whatsappData.message_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex-1 pb-16">
      <Header />

      <main className="px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              AI Assistant
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Store intelligence and daily WhatsApp briefings.
            </p>
          </div>
        </div>

        {/* Main Grid: Left Chat (2 cols) and Right WhatsApp Mockup (1 col) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Chat Stream (7 Cols) */}
          <div className="lg:col-span-7 rounded-xl border border-slate-200 bg-white shadow-sm flex flex-col h-[650px] overflow-hidden">
            {/* Chat Top Banner */}
            <div className="p-4 border-b border-slate-100 bg-slate-50/75 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-sm shadow-emerald-200">
                  <Bot className="h-4 w-4" />
                </div>
                <div>
                  <h2 className="text-xs font-bold text-slate-900">Sellora Copilot</h2>
                  <p className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    Live Context Grounded (Database Connected)
                  </p>
                </div>
              </div>

              <span className="text-[11px] text-slate-400">Apex Retail India</span>
            </div>

            {/* Quick Suggestion Pills */}
            <div className="p-3 border-b border-slate-100 bg-white flex items-center gap-2 overflow-x-auto no-scrollbar">
              {SUGGESTED_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  className="shrink-0 text-[11px] font-medium text-slate-700 bg-slate-100 hover:bg-emerald-50 hover:text-emerald-800 hover:border-emerald-200 border border-slate-200 px-3 py-1 rounded-full transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Message Stream */}
            <div className="flex-1 p-5 overflow-y-auto space-y-4">
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-2.5 ${
                    m.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {m.role === "assistant" && (
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-600 text-white text-xs shrink-0 mt-0.5 shadow-sm shadow-emerald-200">
                      <Bot className="h-3.5 w-3.5" />
                    </div>
                  )}

                  <div
                    className={`rounded-xl p-3.5 text-xs max-w-[85%] leading-relaxed whitespace-pre-wrap ${
                      m.role === "user"
                        ? "bg-slate-900 text-white shadow-sm"
                        : "bg-slate-50 border border-slate-200/80 text-slate-800 shadow-2xs"
                    }`}
                  >
                    {m.content}

                    {m.context_tags && m.context_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2.5 pt-2 border-t border-slate-200/60">
                        {m.context_tags.map((tag, tIdx) => (
                          <span
                            key={tIdx}
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                          >
                            <span className="h-1 w-1 rounded-full bg-emerald-500"></span>
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {m.role === "user" && (
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-800 text-white text-xs shrink-0 mt-0.5">
                      <User className="h-3.5 w-3.5" />
                    </div>
                  )}
                </div>
              ))}

              {chatMutation.isPending && (
                <div className="flex items-center gap-2 text-xs text-slate-400 pl-10">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-emerald-600" />
                  <span>Analyzing store database and crafting reply...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Contextual Smart Follow-up Suggestions */}
            {suggestedFollowups.length > 0 && (
              <div className="px-3 py-2 bg-slate-50/90 border-t border-slate-100 flex items-center gap-2 overflow-x-auto no-scrollbar">
                <div className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 shrink-0">
                  <Sparkles className="h-3 w-3" />
                  <span>Suggested:</span>
                </div>
                {suggestedFollowups.map((f, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(f)}
                    disabled={chatMutation.isPending}
                    className="shrink-0 text-[11px] font-medium text-slate-700 bg-white hover:bg-emerald-50 hover:text-emerald-800 hover:border-emerald-300 border border-slate-200 px-2.5 py-1 rounded-full shadow-2xs transition-colors disabled:opacity-50"
                  >
                    {f}
                  </button>
                ))}
              </div>
            )}

            {/* Input Bar */}
            <div className="p-3 border-t border-slate-100 bg-white">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask anything about your store..."
                  className="flex-1 rounded-lg border border-slate-200 px-3.5 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || chatMutation.isPending}
                  className="flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500 transition-colors disabled:opacity-50"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </form>
            </div>
          </div>

          {/* Right Column: WhatsApp Morning Briefing (5 Cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50/50 via-white to-slate-50 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-emerald-100 pb-3">
                <div className="flex items-center gap-2">
                  <Smartphone className="h-5 w-5 text-emerald-600" />
                  <div>
                    <h2 className="text-sm font-bold text-slate-900">WhatsApp Morning Digest</h2>
                    <p className="text-[11px] text-slate-500">Daily business summary for store owners</p>
                  </div>
                </div>
                <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                  Ready
                </span>
              </div>

              {/* Mobile Mockup Preview */}
              <div className="rounded-xl border border-slate-300 bg-[#EFEAE2] p-4 shadow-inner space-y-2">
                <div className="flex items-center justify-between text-[11px] font-bold text-slate-600 border-b border-slate-300/60 pb-1.5">
                  <span>📱 WhatsApp Message Preview</span>
                  <span className="text-[10px] text-slate-500">08:00 AM</span>
                </div>

                <div className="rounded-lg bg-white p-3.5 shadow-sm text-xs font-sans text-slate-800 leading-relaxed whitespace-pre-wrap border border-slate-200/60">
                  {isLoadingWhatsapp ? (
                    <span className="text-slate-400">Loading daily briefing...</span>
                  ) : (
                    whatsappData?.message_text
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <button
                  onClick={copyWhatsApp}
                  className="flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm transition-colors"
                >
                  {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                  <span>{copied ? "Copied!" : "Copy Text"}</span>
                </button>

                {whatsappData && (
                  <a
                    href={whatsappData.whatsapp_direct_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500 transition-colors"
                  >
                    <ExternalLink className="h-4 w-4" />
                    <span>Open in WhatsApp</span>
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

