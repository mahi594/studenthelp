"use client";
import RequireAuth from "../../components/RequireAuth";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listCompanies, listQuestions, createQuestion, QAQuestionListItem } from "../../lib/api";

function CommunityPageContent() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [questions, setQuestions] = useState<QAQuestionListItem[]>([]);
  const [companyFilter, setCompanyFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadQuestions() {
    setLoading(true);
    try {
      const data = await listQuestions(companyFilter ? { company_id: companyFilter } : undefined);
      setQuestions(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    listCompanies().then(setCompanies);
  }, []);

  useEffect(() => {
    loadQuestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyFilter]);

  async function handlePost() {
    if (!title.trim() || !body.trim()) return;
    setPosting(true);
    setError(null);
    try {
      await createQuestion({ title, body, company_id: companyId || undefined });
      setTitle("");
      setBody("");
      setCompanyId("");
      setShowForm(false);
      loadQuestions();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to post question");
    } finally {
      setPosting(false);
    }
  }

  const companyName = (id: string | null) => companies.find((c) => c.id === id)?.name;

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "48px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 32 }}>Community</h1>
          <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
            Ask peers about interview experiences, prep strategies, anything placement-related.
          </p>
        </div>
        <button onClick={() => setShowForm((s) => !s)} className="btn btn-primary">
          {showForm ? "Cancel" : "+ Ask a question"}
        </button>
      </div>

      {showForm && (
        <div className="card" style={{ padding: 24, marginTop: 20 }}>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Question title"
            style={{ width: "100%" }}
          />
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Add some detail..."
            rows={4}
            style={{ width: "100%", marginTop: 12 }}
          />
          <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={{ width: "100%", marginTop: 12 }}>
            <option value="">Not company-specific</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          {error && <p style={{ color: "var(--danger)", fontSize: 13, marginTop: 10 }}>{error}</p>}
          <button onClick={handlePost} disabled={posting} className="btn btn-primary" style={{ marginTop: 14 }}>
            {posting ? "Posting..." : "Post question"}
          </button>
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 24, flexWrap: "wrap" }}>
        <button
          onClick={() => setCompanyFilter("")}
          className={companyFilter === "" ? "badge badge-applied" : "badge badge-not-applied"}
          style={{ border: "none", cursor: "pointer" }}
        >
          All
        </button>
        {companies.map((c) => (
          <button
            key={c.id}
            onClick={() => setCompanyFilter(c.id)}
            className={companyFilter === c.id ? "badge badge-applied" : "badge badge-not-applied"}
            style={{ border: "none", cursor: "pointer" }}
          >
            {c.name}
          </button>
        ))}
      </div>

      {loading && <p style={{ color: "var(--ink-soft)", marginTop: 24 }}>Loading...</p>}

      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 20 }}>
        {questions.map((q) => (
          <Link key={q.id} href={`/community/${q.id}`} style={{ textDecoration: "none" }}>
            <div className="card" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                <div>
                  <h3 style={{ fontSize: 17, color: "var(--ink)" }}>{q.title}</h3>
                  <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 6 }}>
                    {q.body.length > 140 ? q.body.slice(0, 140) + "..." : q.body}
                  </p>
                  <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap", alignItems: "center" }}>
                    <span className="mono" style={{ fontSize: 11, color: "var(--ink-soft)" }}>
                      {q.author_name} · {new Date(q.created_at).toLocaleDateString()}
                    </span>
                    {q.company_id && <span className="badge badge-not-applied">{companyName(q.company_id)}</span>}
                  </div>
                </div>
                <span className="badge badge-applied" style={{ whiteSpace: "nowrap" }}>
                  {q.answer_count} {q.answer_count === 1 ? "answer" : "answers"}
                </span>
              </div>
            </div>
          </Link>
        ))}

        {!loading && questions.length === 0 && (
          <div className="card" style={{ padding: 32, textAlign: "center" }}>
            <p style={{ color: "var(--ink-soft)" }}>No questions yet - be the first to ask.</p>
          </div>
        )}
      </div>
    </main>
  );
}

export default function CommunityPage() {
  return (
    <RequireAuth>
      <CommunityPageContent />
    </RequireAuth>
  );
}
