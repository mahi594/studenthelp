"use client";
import RequireAuth from "../../components/RequireAuth";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { askChat, getChatHistory, ChatMessage } from "../../lib/api";

function ChatPageContent() {
  const searchParams = useSearchParams();
  const companyId = searchParams.get("company_id") || undefined;
  const companyName = searchParams.get("company_name") || undefined;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);

  useEffect(() => {
    async function loadHistory() {
      try {
        const history = await getChatHistory();
        if (history && history.length > 0) {
          setMessages(history);
        }
      } catch (e) {
        // Fall back gracefully
      } finally {
        setHistoryLoading(false);
      }
    }
    loadHistory();
  }, []);

  async function sendMessage() {
    if (!input.trim()) return;
    const question = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);
    try {
      const res = await askChat(question, companyId);
      setMessages(res.history);
    } finally {
      setLoading(false);
    }
  }


  return (
    <main style={{ maxWidth: 700, margin: "0 auto", padding: "48px 24px", display: "flex", flexDirection: "column", height: "calc(100vh - 65px)" }}>
      <h1 style={{ fontSize: 28 }}>Ask StudentHelp</h1>
      {companyId && companyName ? (
        <div
          className="card"
          style={{ padding: "10px 16px", marginTop: 12, marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}
        >
          <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>
            Customizing your roadmap for <strong style={{ color: "var(--ink)" }}>{companyName}</strong> - every answer below is scoped to it.
          </span>
          <Link href="/roadmap" style={{ fontSize: 12, color: "var(--primary)", textDecoration: "none", whiteSpace: "nowrap", marginLeft: 12 }}>
            Back to roadmap
          </Link>
        </div>
      ) : (
        <p style={{ color: "var(--ink-soft)", marginTop: 6, marginBottom: 24, fontSize: 14 }}>
          Ask anything about placement prep, interviews, subjects to study, or a specific company.
        </p>
      )}

      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
        {messages.length === 0 && (
          <div className="card" style={{ padding: 20, color: "var(--ink-soft)", fontSize: 14 }}>
            {companyName
              ? `Try: "What should I add to my ${companyName} roadmap for the next phase?" or "I'm weaker in system design, adjust the plan."`
              : 'Try: "What should I focus on for a product-based company interview?"'}
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={m.role === "user" ? "" : "card"}
            style={{
              padding: "12px 16px",
              borderRadius: 14,
              maxWidth: "80%",
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              background: m.role === "user" ? "var(--primary)" : undefined,
              color: m.role === "user" ? "#fff" : "var(--ink)",
              fontSize: 15,
              lineHeight: 1.5,
            }}
          >
            {m.content}
          </div>
        ))}
        {loading && <div style={{ color: "var(--ink-soft)", fontSize: 13 }}>Thinking...</div>}
      </div>

      <div style={{ display: "flex", gap: 10, marginTop: 20, paddingBottom: 12 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder={companyName ? `Ask about your ${companyName} roadmap...` : "Ask a question..."}
          style={{ flex: 1 }}
        />
        <button onClick={sendMessage} className="btn btn-primary">
          Send
        </button>
      </div>
    </main>
  );
}

export default function ChatPage() {
  return (
    <RequireAuth>
      <Suspense fallback={null}>
        <ChatPageContent />
      </Suspense>
    </RequireAuth>
  );
}
