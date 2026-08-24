"use client";
import RequireAuth from "../../components/RequireAuth";

import { useEffect, useState } from "react";
import Link from "next/link";
import ReadinessLadder from "../../components/ReadinessLadder";
import ReadinessTrendChart from "../../components/ReadinessTrendChart";
import {
  getLatestReadiness,
  getReadinessHistory,
  computeReadiness,
  getQuizWeeklyStatus,
  getMyLeetcodeRecommendations,
  getLatestPrepPlan,
  QuizWeeklySubjectStatus,
  PrepPlan,
} from "../../lib/api";

function DashboardPageContent() {
  const [readiness, setReadiness] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [weeklyStatus, setWeeklyStatus] = useState<QuizWeeklySubjectStatus[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [prepPlan, setPrepPlan] = useState<PrepPlan | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [data, historyData] = await Promise.all([getLatestReadiness(), getReadinessHistory()]);
      setReadiness(data);
      setHistory(historyData);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Log in to view your Placement Readiness Index.");
    } finally {
      setLoading(false);
    }
  }

  async function recompute() {
    setLoading(true);
    try {
      const data = await computeReadiness();
      setReadiness(data);
      const historyData = await getReadinessHistory();
      setHistory(historyData);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    getQuizWeeklyStatus().then(setWeeklyStatus).catch(() => {});
    getMyLeetcodeRecommendations().then(setRecommendations).catch(() => {});
    getLatestPrepPlan().then(setPrepPlan).catch(() => {});
  }, []);

  const hasScore = readiness?.composite_score !== null && readiness?.composite_score !== undefined;
  const isInsufficientData = readiness && readiness.data_status === "insufficient";
  const score = hasScore ? readiness.composite_score : null;
  const breakdown = readiness?.breakdown ?? {};
  const version = readiness?.algorithm_version || breakdown?.algorithm_version || "v1";
  const weaknesses: string[] = breakdown?.top_weaknesses || [];
  const dueSubjects = weeklyStatus.filter((s) => s.is_due);

  // val is null when that dimension has no underlying assessment data yet -
  // rendered as "Not Assessed", never as a fabricated 0%.
  const dimensions = [
    { key: "dsa", label: "DSA & Problem Solving", val: breakdown.dsa ?? null, weight: "25%" },
    { key: "cs_fundamentals", label: "CS Fundamentals (DBMS, OS, CN)", val: breakdown.cs_fundamentals ?? null, weight: "15%" },
    { key: "aptitude", label: "Aptitude & Reasoning", val: breakdown.aptitude ?? null, weight: "15%" },
    { key: "resume", label: "Resume Impact", val: breakdown.resume ?? null, weight: "15%" },
    { key: "communication", label: "Communication Skills", val: breakdown.communication ?? null, weight: "10%" },
    { key: "interview", label: "Technical Interviewing", val: breakdown.interview ?? null, weight: "10%" },
    { key: "company_prep", label: "Target Company Preparation", val: breakdown.company_prep ?? null, weight: "10%" },
  ];

  return (
    <main style={{ maxWidth: 880, margin: "0 auto", padding: "40px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <h1 style={{ fontSize: 30, fontWeight: 800 }}>Placement Readiness Index</h1>
            <span className="mono" style={{ fontSize: 11, background: "var(--accent-soft)", color: "var(--accent)", padding: "2px 8px", borderRadius: 12, fontWeight: 600 }}>
              Alg {version}
            </span>
          </div>
          <p style={{ color: "var(--ink-soft)", marginTop: 6, fontSize: 14 }}>
            Multidimensional evaluation of your technical, communication, and resume readiness.
          </p>
        </div>
        <button onClick={recompute} className="btn btn-secondary" style={{ fontSize: 13, height: 38 }}>
          Recalculate Score
        </button>
      </div>

      {error && (
        <div className="card" style={{ padding: 20, marginTop: 24, borderColor: "var(--danger)" }}>
          <span style={{ color: "var(--danger)", fontSize: 14 }}>{error}</span>
        </div>
      )}

      {!error && (
        <>
          {/* Main Index Score Card */}
          <div className="card" style={{ padding: 28, marginTop: 24 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 24, alignItems: "center" }}>
              <div>
                <span className="mono" style={{ fontSize: 12, color: "var(--ink-soft)", letterSpacing: "0.05em" }}>OVERALL READINESS INDEX</span>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginTop: 4 }}>
                  <span className="display mono" style={{ fontSize: hasScore ? 56 : 22, fontWeight: 800, color: hasScore ? "var(--primary)" : "var(--ink-soft)" }}>
                    {loading ? "—" : hasScore ? score : "Unavailable"}
                  </span>
                  {hasScore && <span style={{ color: "var(--ink-soft)", fontSize: 18, fontWeight: 600 }}>/ 100</span>}
                </div>
                {!loading && !hasScore && (
                  <p style={{ color: "var(--ink-soft)", fontSize: 13, marginTop: 6 }}>
                    Readiness score unavailable — complete more assessments to unlock your index.
                  </p>
                )}
                {hasScore && (
                  <div style={{ marginTop: 14 }}>
                    <ReadinessLadder score={score} />
                  </div>
                )}
              </div>

              <div style={{ borderLeft: "1px solid var(--line)", paddingLeft: 24 }}>
                <span className="mono" style={{ fontSize: 12, color: "var(--danger)", letterSpacing: "0.05em", fontWeight: 700 }}>
                  TOP IDENTIFIED SKILL GAPS
                </span>
                {weaknesses.length > 0 ? (
                  <ul style={{ marginTop: 10, paddingLeft: 18, margin: "10px 0 0", color: "var(--ink)" }}>
                    {weaknesses.map((w, i) => (
                      <li key={i} style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>
                        {w}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ marginTop: 10, fontSize: 13, color: "var(--ink-soft)" }}>
                    Not enough assessment data yet to identify gaps.
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* 7-Dimension Breakdown */}
          <div className="card" style={{ padding: 28, marginTop: 24 }}>
            <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 18 }}>Multidimensional Skill Breakdown</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {dimensions.map((d) => (
                <div key={d.key}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
                    <span>
                      {d.label} <span style={{ color: "var(--ink-soft)", fontSize: 11 }}>({d.weight})</span>
                    </span>
                    <span className="mono" style={{ fontWeight: d.val === null ? 500 : 700, color: d.val === null ? "var(--ink-soft)" : undefined }}>
                      {loading ? "—" : d.val === null ? "Not Assessed" : `${d.val}%`}
                    </span>
                  </div>
                  <div style={{ background: "var(--line)", borderRadius: 6, height: 8, overflow: "hidden" }}>
                    <div
                      style={{
                        background: d.val === null ? "var(--line)" : d.val >= 75 ? "var(--primary)" : d.val >= 50 ? "#d97706" : "var(--danger)",
                        height: "100%",
                        width: `${d.val === null ? 0 : Math.min(100, Math.max(0, d.val))}%`,
                        transition: "width 400ms ease",
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Next Best Actions */}
          <div className="card" style={{ padding: 24, marginTop: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>Next Best Actions</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginTop: 14 }}>
              {dueSubjects.length > 0 && (
                <div style={{ padding: 16, borderRadius: 10, background: "var(--accent-soft)", border: "1px solid rgba(79,70,229,0.15)" }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "var(--accent)" }}>Assessment Due</div>
                  <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
                    {dueSubjects.map((s) => s.subject).join(", ")}
                  </div>
                  <Link href="/quiz" className="btn btn-secondary" style={{ marginTop: 10, fontSize: 12, padding: "6px 12px", textDecoration: "none", display: "inline-block" }}>
                    Start Assessment
                  </Link>
                </div>
              )}

              {prepPlan ? (
                <div style={{ padding: 16, borderRadius: 10, background: "rgba(31,92,74,0.06)", border: "1px solid rgba(31,92,74,0.15)" }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "var(--primary)" }}>Prep Plan Progress</div>
                  <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
                    {prepPlan.progress_percent}% completed ({prepPlan.days_total} days)
                  </div>
                  <Link href="/prep-plan" className="btn btn-secondary" style={{ marginTop: 10, fontSize: 12, padding: "6px 12px", textDecoration: "none", display: "inline-block" }}>
                    Continue Plan
                  </Link>
                </div>
              ) : (
                <div style={{ padding: 16, borderRadius: 10, background: "rgba(31,92,74,0.06)", border: "1px solid rgba(31,92,74,0.15)" }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "var(--primary)" }}>Target Company</div>
                  <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
                    Select a target company & generate plan
                  </div>
                  <Link href="/companies" className="btn btn-secondary" style={{ marginTop: 10, fontSize: 12, padding: "6px 12px", textDecoration: "none", display: "inline-block" }}>
                    Select Target
                  </Link>
                </div>
              )}

              {recommendations.length > 0 && (
                <div style={{ padding: 16, borderRadius: 10, background: "rgba(217,119,6,0.08)", border: "1px solid rgba(217,119,6,0.15)" }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#b45309" }}>Weak Topic Practice</div>
                  <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
                    {recommendations.length} recommended problems
                  </div>
                  <Link href="/leetcode" className="btn btn-secondary" style={{ marginTop: 10, fontSize: 12, padding: "6px 12px", textDecoration: "none", display: "inline-block" }}>
                    View Practice
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* Readiness Trend Chart */}
          <div className="card" style={{ padding: 28, marginTop: 24 }}>
            <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 16 }}>Readiness Trend Over Time</h3>
            <ReadinessTrendChart history={history} />
          </div>
        </>
      )}
    </main>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardPageContent />
    </RequireAuth>
  );
}