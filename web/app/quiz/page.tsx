"use client";
import RequireAuth from "../../components/RequireAuth";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getQuizQuestions, submitQuizAnswers, getQuizWeeklyStatus, QuizWeeklySubjectStatus } from "../../lib/api";
import ReadinessLadder from "../../components/ReadinessLadder";

const SUBJECTS = ["DSA", "DBMS", "OS", "Aptitude", "CN", "OOP"];

type Question = {
  id: string;
  subject: string;
  difficulty: string | null;
  question_text: string;
  options: string[];
};

function daysUntil(iso: string | null): number {
  if (!iso) return 0;
  const ms = new Date(iso).getTime() - Date.now();
  return Math.max(0, Math.ceil(ms / (1000 * 60 * 60 * 24)));
}

function QuizPageContent() {
  const [stage, setStage] = useState<"pick" | "taking" | "result">("pick");
  const [subject, setSubject] = useState("DSA");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [weeklyStatus, setWeeklyStatus] = useState<QuizWeeklySubjectStatus[]>([]);

  useEffect(() => {
    getQuizWeeklyStatus().then(setWeeklyStatus).catch(() => {});
  }, []);

  const statusBySubject = Object.fromEntries(weeklyStatus.map((s) => [s.subject, s]));

  async function startQuiz() {
    setLoading(true);
    setError(null);
    try {
      const data = await getQuizQuestions(subject, undefined, 10);
      setQuestions(data);
      setCurrent(0);
      setAnswers({});
      setStage("taking");
    } catch (e: any) {
      setError(
        e?.response?.data?.detail ||
          `No approved questions for ${subject} yet. Ask an admin to generate and approve some.`
      );
    } finally {
      setLoading(false);
    }
  }

  function selectAnswer(questionId: string, optionIndex: number) {
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));
  }

  function nextQuestion() {
    if (current < questions.length - 1) {
      setCurrent(current + 1);
    } else {
      handleSubmit();
    }
  }

  async function handleSubmit() {
    setLoading(true);
    try {
      const payload = questions.map((q) => ({
        question_id: q.id,
        selected_option_index: answers[q.id] ?? -1,
      }));
      const res = await submitQuizAnswers(subject, payload);
      setResult(res);
      setStage("result");
      getQuizWeeklyStatus().then(setWeeklyStatus).catch(() => {});
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setStage("pick");
    setResult(null);
  }

  if (stage === "pick") {
    return (
      <main style={{ maxWidth: 560, margin: "0 auto", padding: "56px 24px" }}>
        <h1 style={{ fontSize: 32 }}>Diagnostic quiz</h1>
        <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
          Ten questions. This is what tells us what to prioritize in your prep plan and roadmap.
        </p>

        <div className="card" style={{ padding: 28, marginTop: 24 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 10 }}>
            Choose a subject
          </label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {SUBJECTS.map((s) => {
              const st = statusBySubject[s];
              const due = !st || st.is_due;
              return (
                <button
                  key={s}
                  onClick={() => setSubject(s)}
                  className={subject === s ? "btn btn-primary" : "btn btn-secondary"}
                  style={{ fontSize: 13, position: "relative" }}
                  title={!due && st?.next_eligible_at ? `Next attempt available in ${daysUntil(st.next_eligible_at)} day(s)` : "Due this week"}
                >
                  {s}
                  {due ? (
                    <span style={{ marginLeft: 6, fontSize: 10, color: subject === s ? "inherit" : "var(--primary)" }}>●</span>
                  ) : (
                    <span style={{ marginLeft: 6, fontSize: 10, opacity: 0.6 }}>
                      {daysUntil(st!.next_eligible_at)}d
                    </span>
                  )}
                </button>
              );
            })}
          </div>
          <p style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 10 }}>
            ● = due this week. Otherwise, shows days until your next attempt unlocks (weekly cadence).
          </p>

          {error && <p style={{ color: "var(--danger)", fontSize: 14, marginTop: 16 }}>{error}</p>}

          <button onClick={startQuiz} disabled={loading} className="btn btn-primary" style={{ marginTop: 24, width: "100%" }}>
            {loading ? "Loading..." : "Start quiz"}
          </button>
        </div>
      </main>
    );
  }

  if (stage === "taking") {
    const q = questions[current];
    const selected = answers[q.id];

    return (
      <main style={{ maxWidth: 560, margin: "0 auto", padding: "56px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--ink-soft)", marginBottom: 10 }}>
          <span>{subject}</span>
          <span className="mono">{current + 1} / {questions.length}</span>
        </div>
        <ReadinessLadder score={(current / questions.length) * 100} rungs={questions.length} height={8} />

        <div className="card" style={{ padding: 28, marginTop: 24 }}>
          <div style={{ fontSize: 18, fontWeight: 600, lineHeight: 1.4 }}>{q.question_text}</div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 20 }}>
            {q.options.map((opt, i) => (
              <button
                key={i}
                onClick={() => selectAnswer(q.id, i)}
                style={{
                  textAlign: "left",
                  padding: "12px 16px",
                  borderRadius: 10,
                  border: selected === i ? "2px solid var(--primary)" : "1.5px solid var(--line)",
                  background: selected === i ? "var(--accent-soft)" : "var(--surface)",
                  fontSize: 14,
                  fontWeight: selected === i ? 600 : 500,
                  cursor: "pointer",
                }}
              >
                {opt}
              </button>
            ))}
          </div>

          <button
            onClick={nextQuestion}
            disabled={selected === undefined || loading}
            className="btn btn-primary"
            style={{ marginTop: 24, width: "100%" }}
          >
            {current < questions.length - 1 ? "Next" : loading ? "Submitting..." : "Finish quiz"}
          </button>
        </div>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 560, margin: "0 auto", padding: "56px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Quiz complete</h1>

      <div className="card" style={{ padding: 32, marginTop: 24 }}>
        <span className="mono" style={{ fontSize: 12, color: "var(--ink-soft)" }}>{subject.toUpperCase()} SCORE</span>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 8 }}>
          <span className="display mono" style={{ fontSize: 44 }}>{result?.score_percent}</span>
          <span style={{ color: "var(--ink-soft)" }}>/ 100</span>
        </div>
        <p style={{ fontSize: 14, color: "var(--ink-soft)", marginTop: 8 }}>
          {result?.correct_count} of {result?.total_count} correct
        </p>
        <div style={{ marginTop: 16 }}>
          <ReadinessLadder score={result?.score_percent ?? 0} />
        </div>
      </div>

      {result?.question_breakdown?.length > 0 && (
        <div style={{ marginTop: 28 }}>
          <h2 style={{ fontSize: 20, marginBottom: 14 }}>Question-by-Question Review</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {result.question_breakdown.map((item: any, idx: number) => (
              <div key={item.question_id || idx} className="card" style={{ padding: 20 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 12 }}>
                  <span style={{ fontSize: 15, fontWeight: 600, flex: 1 }}>
                    {idx + 1}. {item.question_text}
                  </span>
                  <span
                    className="badge"
                    style={{
                      backgroundColor: item.is_correct ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                      color: item.is_correct ? "#10b981" : "#ef4444",
                      fontWeight: 600,
                      fontSize: 12,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {item.is_correct ? "✓ Correct" : "✗ Incorrect"}
                  </span>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 12 }}>
                  {item.options?.map((opt: string, optIdx: number) => {
                    const isSelected = item.selected_option_index === optIdx;
                    const isCorrectOption = item.correct_option_index === optIdx;

                    let bg = "var(--surface)";
                    let border = "1px solid var(--line)";
                    let label = null;

                    if (isCorrectOption) {
                      bg = "rgba(16, 185, 129, 0.08)";
                      border = "1.5px solid #10b981";
                      label = <span style={{ color: "#10b981", fontSize: 12, fontWeight: 600 }}>Correct Answer</span>;
                    } else if (isSelected && !item.is_correct) {
                      bg = "rgba(239, 68, 68, 0.08)";
                      border = "1.5px solid #ef4444";
                      label = <span style={{ color: "#ef4444", fontSize: 12, fontWeight: 600 }}>Your Selection</span>;
                    }

                    return (
                      <div
                        key={optIdx}
                        style={{
                          padding: "10px 14px",
                          borderRadius: 8,
                          background: bg,
                          border: border,
                          fontSize: 13.5,
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}
                      >
                        <span>{opt}</span>
                        {label}
                      </div>
                    );
                  })}
                </div>

                {item.explanation && (
                  <div
                    style={{
                      marginTop: 14,
                      padding: 12,
                      borderRadius: 8,
                      background: "rgba(59, 130, 246, 0.06)",
                      borderLeft: "3px solid var(--primary)",
                      fontSize: 13,
                      color: "var(--ink-soft)",
                    }}
                  >
                    <strong style={{ color: "var(--ink)" }}>Explanation: </strong>
                    {item.explanation}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {result?.is_weak_subject && result?.recommended_leetcode?.length > 0 && (
        <div className="card" style={{ padding: 24, marginTop: 20 }}>
          <h3 style={{ fontSize: 16 }}>Recommended practice for {subject}</h3>
          <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 4 }}>
            Picked based on this score - a notification with these was also sent to you.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 14 }}>
            {result.recommended_leetcode.map((p: any) => (
              <a
                key={p.id}
                href={p.leetcode_url}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "10px 14px",
                  borderRadius: 8,
                  border: "1.5px solid var(--line)",
                  textDecoration: "none",
                  color: "var(--ink)",
                  fontSize: 13.5,
                }}
              >
                <span>{p.title}</span>
                <span className="mono" style={{ fontSize: 11, color: "var(--ink-soft)" }}>{p.difficulty}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
        <button onClick={reset} className="btn btn-secondary">Take another quiz</button>
        <Link href="/dashboard" className="btn btn-primary" style={{ textDecoration: "none" }}>
          See your readiness score
        </Link>
      </div>
    </main>
  );
}


export default function QuizPage() {
  return (
    <RequireAuth>
      <QuizPageContent />
    </RequireAuth>
  );
}
