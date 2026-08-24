"use client";
import RequireAuth from "../../../components/RequireAuth";

import { useEffect, useState } from "react";
import {
  generateQuizQuestions,
  listPendingQuizQuestions,
  approveQuizQuestion,
  rejectQuizQuestion,
  listCompanies,
} from "../../../lib/api";

function QuizApprovalPageContent() {
  const [subject, setSubject] = useState("DSA");
  const [numQuestions, setNumQuestions] = useState(5);
  const [companyId, setCompanyId] = useState("");
  const [companies, setCompanies] = useState<any[]>([]);
  const [pending, setPending] = useState<any[]>([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadCompanies() {
    setCompanies(await listCompanies());
  }

  async function loadPending() {
    const data = await listPendingQuizQuestions();
    setPending(data);
  }

  useEffect(() => {
    loadCompanies();
    loadPending();
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      await generateQuizQuestions({
        subject,
        num_questions: numQuestions,
        company_id: companyId || undefined,
      });
      await loadPending();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Generation failed. Check your AI provider keys.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleApprove(id: string) {
    setPending((prev) => prev.filter((q) => q.id !== id));
    await approveQuizQuestion(id);
  }

  async function handleReject(id: string) {
    setPending((prev) => prev.filter((q) => q.id !== id));
    await rejectQuizQuestion(id);
  }

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Quiz approval</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
        AI drafts questions — nothing reaches students until you approve it here.
      </p>

      <div className="card" style={{ padding: 24, marginTop: 24 }}>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Subject, e.g. DSA" style={{ flex: 1, minWidth: 140 }} />
          <input
            type="number"
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            style={{ width: 80 }}
          />
          <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={{ flex: 1, minWidth: 160 }}>
            <option value="">No specific company (general)</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <button onClick={handleGenerate} disabled={generating} className="btn btn-primary">
            {generating ? "Generating..." : "Generate with AI"}
          </button>
        </div>
        {error && <p style={{ color: "var(--danger)", fontSize: 14, marginTop: 12 }}>{error}</p>}
      </div>

      <h2 style={{ fontSize: 22, marginTop: 40 }}>Pending review ({pending.length})</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 16 }}>
        {pending.map((q) => (
          <div key={q.id} className="card" style={{ padding: 20 }}>
            <span className="mono" style={{ fontSize: 12, color: "var(--accent)" }}>
              {q.subject?.toUpperCase()} · {q.difficulty || "unrated"}
            </span>
            <div style={{ fontWeight: 600, marginTop: 6, fontSize: 15 }}>{q.question_text}</div>
            <ul style={{ marginTop: 10, paddingLeft: 20, fontSize: 14 }}>
              {q.options?.map((opt: string, i: number) => (
                <li key={i} style={{ color: i === q.correct_option_index ? "var(--primary)" : "var(--ink-soft)", fontWeight: i === q.correct_option_index ? 600 : 400 }}>
                  {opt} {i === q.correct_option_index && "✓"}
                </li>
              ))}
            </ul>
            {q.explanation && (
              <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 10 }}>{q.explanation}</p>
            )}
            <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
              <button onClick={() => handleApprove(q.id)} className="btn btn-primary" style={{ fontSize: 13 }}>
                Approve
              </button>
              <button onClick={() => handleReject(q.id)} className="btn btn-secondary" style={{ fontSize: 13 }}>
                Reject
              </button>
            </div>
          </div>
        ))}
        {pending.length === 0 && (
          <p style={{ color: "var(--ink-soft)" }}>Nothing waiting for review right now.</p>
        )}
      </div>
    </main>
  );
}

export default function QuizApprovalPage() {
  return (
    <RequireAuth role="admin">
      <QuizApprovalPageContent />
    </RequireAuth>
  );
}
