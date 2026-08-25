"use client";
import RequireAuth from "../../components/RequireAuth";

import { useEffect, useState } from "react";
import {
  listCompanies,
  startMockInterview,
  respondMockInterview,
  finishMockInterview,
  MockInterviewSession,
} from "../../lib/api";

function MockInterviewPageContent() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [roleOrSubject, setRoleOrSubject] = useState("SDE-1");
  const [companyId, setCompanyId] = useState("");
  const [session, setSession] = useState<MockInterviewSession | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCompanies().then(setCompanies);
  }, []);

  async function handleStart() {
    setLoading(true);
    setError(null);
    try {
      const s = await startMockInterview(roleOrSubject, companyId || undefined);
      setSession(s);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to start mock interview");
    } finally {
      setLoading(false);
    }
  }

  async function handleRespond() {
    if (!session || !answer.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const s = await respondMockInterview(session.id, answer);
      setSession(s);
      setAnswer("");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to send response");
    } finally {
      setLoading(false);
    }
  }

  async function handleFinish() {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      const s = await finishMockInterview(session.id);
      setSession(s);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to finish session");
    } finally {
      setLoading(false);
    }
  }

  const candidateTurns = session?.transcript.filter((t) => t.role === "candidate").length || 0;

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Mock interview</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
        A turn-by-turn AI interviewer that adapts to your answers, then scores the full transcript.
      </p>

      {!session && (
        <div className="card" style={{ padding: 24, marginTop: 24 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
            Role / subject
          </label>
          <input
            value={roleOrSubject}
            onChange={(e) => setRoleOrSubject(e.target.value)}
            placeholder="e.g. SDE-1, DSA, System Design"
            style={{ width: "100%" }}
          />

          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 16, marginBottom: 6 }}>
            Target company (optional)
          </label>
          <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={{ width: "100%" }}>
            <option value="">General (no specific company)</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          <button onClick={handleStart} disabled={loading} className="btn btn-primary" style={{ width: "100%", marginTop: 20 }}>
            {loading ? "Starting..." : "Start interview"}
          </button>
        </div>
      )}

      {error && (
        <div className="card" style={{ padding: 16, marginTop: 16, borderColor: "var(--danger)" }}>
          <span style={{ color: "var(--danger)", fontSize: 14 }}>{error}</span>
        </div>
      )}

      {session && (
        <div style={{ marginTop: 24 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {session.transcript.map((turn, i) => (
              <div
                key={i}
                className="card"
                style={{
                  padding: 16,
                  alignSelf: turn.role === "interviewer" ? "flex-start" : "flex-end",
                  maxWidth: "85%",
                  background: turn.role === "interviewer" ? "var(--surface)" : "var(--accent-soft)",
                }}
              >
                <span className="mono" style={{ fontSize: 11, color: "var(--ink-soft)", fontWeight: 600 }}>
                  {turn.role === "interviewer" ? "INTERVIEWER" : "YOU"}
                </span>
                <p style={{ fontSize: 14, marginTop: 6 }}>{turn.content}</p>
              </div>
            ))}
          </div>

          {session.status === "in_progress" && (
            <div className="card" style={{ padding: 20, marginTop: 20 }}>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Type your answer..."
                rows={4}
                style={{ width: "100%" }}
              />
              <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
                <button onClick={handleRespond} disabled={loading || !answer.trim()} className="btn btn-primary" style={{ flex: 1 }}>
                  {loading ? "Sending..." : "Send answer"}
                </button>
                <button onClick={handleFinish} disabled={loading || candidateTurns === 0} className="btn btn-secondary">
                  Finish & get feedback
                </button>
              </div>
              {candidateTurns === 0 && (
                <p style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 8 }}>
                  Answer at least one question before finishing.
                </p>
              )}
            </div>
          )}

          {session.status === "completed" && (
            <div className="card" style={{ padding: 24, marginTop: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ fontSize: 20, fontWeight: 700 }}>Mock Interview Evaluation Result</h3>
                <span className="mono" style={{ fontSize: 11, background: "rgba(59,130,246,0.1)", color: "#2563eb", padding: "3px 10px", borderRadius: 12, fontWeight: 700 }}>
                  AI Evaluation Indicators
                </span>
              </div>

              {session.overall_score !== null && (
                <div style={{ marginTop: 12 }}>
                  <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>Overall Score</span>
                  <p style={{ fontSize: 36, fontWeight: 800, color: "var(--primary)", marginTop: 2 }}>
                    {session.overall_score} <span style={{ fontSize: 18, color: "var(--ink-soft)", fontWeight: 500 }}>/ 100</span>
                  </p>
                </div>
              )}

              {session.feedback && (
                <div style={{ marginTop: 20, background: "var(--surface)", padding: 16, borderRadius: 8, border: "1px solid var(--line)" }}>
                  <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: "var(--ink)" }}>Structured Indicators (0-100)</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
                    <div>
                      <span style={{ fontSize: 12, color: "var(--ink-soft)" }}>Technical Knowledge</span>
                      <p style={{ fontSize: 18, fontWeight: 700 }}>{session.feedback.technical_knowledge ?? session.overall_score ?? "N/A"}</p>
                    </div>
                    <div>
                      <span style={{ fontSize: 12, color: "var(--ink-soft)" }}>Problem Solving</span>
                      <p style={{ fontSize: 18, fontWeight: 700 }}>{session.feedback.problem_solving ?? session.overall_score ?? "N/A"}</p>
                    </div>
                    <div>
                      <span style={{ fontSize: 12, color: "var(--ink-soft)" }}>Communication</span>
                      <p style={{ fontSize: 18, fontWeight: 700 }}>{session.feedback.communication_score ?? session.overall_score ?? "N/A"}</p>
                    </div>
                    <div>
                      <span style={{ fontSize: 12, color: "var(--ink-soft)" }}>Answer Structure</span>
                      <p style={{ fontSize: 18, fontWeight: 700 }}>{session.feedback.answer_structure ?? session.overall_score ?? "N/A"}</p>
                    </div>
                    <div>
                      <span style={{ fontSize: 12, color: "var(--ink-soft)" }}>Technical Depth</span>
                      <p style={{ fontSize: 18, fontWeight: 700 }}>{session.feedback.technical_depth ?? session.overall_score ?? "N/A"}</p>
                    </div>
                  </div>
                </div>
              )}

              {session.feedback?.strengths?.length ? (
                <div style={{ marginTop: 18 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "var(--primary)" }}>Key Strengths</span>
                  <ul style={{ paddingLeft: 20, marginTop: 6 }}>
                    {session.feedback.strengths.map((s, i) => (
                      <li key={i} style={{ fontSize: 14, marginTop: 4 }}>{s}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {session.feedback?.improvements?.length ? (
                <div style={{ marginTop: 18 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "#b45309" }}>Areas to Improve</span>
                  <ul style={{ paddingLeft: 20, marginTop: 6 }}>
                    {session.feedback.improvements.map((s, i) => (
                      <li key={i} style={{ fontSize: 14, marginTop: 4 }}>{s}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <button
                onClick={() => { setSession(null); setAnswer(""); }}
                className="btn btn-secondary"
                style={{ marginTop: 24 }}
              >
                Start another session
              </button>
            </div>
          )}

        </div>
      )}
    </main>
  );
}

export default function MockInterviewPage() {
  return (
    <RequireAuth>
      <MockInterviewPageContent />
    </RequireAuth>
  );
}
