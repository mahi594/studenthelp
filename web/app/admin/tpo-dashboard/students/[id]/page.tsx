"use client";
import RequireAuth from "../../../../../components/RequireAuth";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getTpoStudentDetail } from "../../../../../lib/api";
import ReadinessLadder from "../../../../../components/ReadinessLadder";

const DIMENSION_LABELS: Record<string, string> = {
  dsa: "DSA & Problem Solving",
  cs_fundamentals: "CS Fundamentals",
  aptitude: "Aptitude & Reasoning",
  communication: "Communication Skills",
  resume: "Resume Impact",
  interview: "Technical Interviewing",
  company_prep: "Target Company Preparation",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ padding: 24, marginTop: 20 }}>
      <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 14, letterSpacing: "0.02em", textTransform: "uppercase", color: "var(--ink-soft)" }}>
        {title}
      </h2>
      {children}
    </div>
  );
}

function TpoStudentDetailContent() {
  const params = useParams();
  const studentId = params?.id as string;
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!studentId) return;
    setLoading(true);
    getTpoStudentDetail(studentId)
      .then(setData)
      .catch((e: any) => setError(e?.response?.data?.detail || "Could not load this student. They may not be in your institution."))
      .finally(() => setLoading(false));
  }, [studentId]);

  if (loading) {
    return (
      <main style={{ maxWidth: 900, margin: "0 auto", padding: "60px 24px", textAlign: "center" }}>
        <span className="mono" style={{ fontSize: 13, color: "var(--ink-soft)" }}>Loading student profile…</span>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main style={{ maxWidth: 900, margin: "0 auto", padding: "60px 24px" }}>
        <div className="card" style={{ padding: 20, borderColor: "var(--danger)" }}>
          <span style={{ color: "var(--danger)", fontSize: 14 }}>{error || "Student not found."}</span>
        </div>
        <Link href="/admin/tpo-dashboard" style={{ display: "inline-block", marginTop: 16, fontSize: 13, color: "var(--primary)" }}>
          ← Back to dashboard
        </Link>
      </main>
    );
  }

  const hasScore = data.composite_score !== null && data.composite_score !== undefined;
  const breakdown = data.breakdown || {};

  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: "40px 24px" }}>
      <Link href="/admin/tpo-dashboard" style={{ fontSize: 13, color: "var(--primary)", textDecoration: "none" }}>
        ← Back to dashboard
      </Link>

      {/* Student Profile */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16, marginTop: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800 }}>{data.name}</h1>
          <p style={{ color: "var(--ink-soft)", marginTop: 4, fontSize: 14 }}>
            {data.email} · {data.branch || "Branch unknown"} · Class of {data.grad_year || "—"} · CGPA {data.cgpa || "—"}
          </p>
        </div>
        <span className="badge" style={{
          background: data.risk_category === "Interview Ready" ? "rgba(31,92,74,0.12)" : data.risk_category === "Needs Significant Support" ? "#FBE4DC" : "rgba(0,0,0,0.05)",
          color: data.risk_category === "Interview Ready" ? "var(--primary)" : data.risk_category === "Needs Significant Support" ? "var(--danger)" : "var(--ink)",
          fontSize: 12, fontWeight: 700, padding: "6px 12px",
        }}>
          {data.risk_category}
        </span>
      </div>

      {/* Placement Readiness */}
      <Section title="Placement Readiness">
        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <span className="display mono" style={{ fontSize: hasScore ? 48 : 20, fontWeight: 800, color: hasScore ? "var(--primary)" : "var(--ink-soft)" }}>
            {hasScore ? data.composite_score : "Unavailable"}
          </span>
          {hasScore && <span style={{ color: "var(--ink-soft)", fontSize: 16 }}>/ 100</span>}
        </div>
        {!hasScore && (
          <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 4 }}>
            Readiness score unavailable — student has not completed enough assessments yet.
          </p>
        )}
        <p style={{ fontSize: 11, color: "var(--ink-soft)", marginTop: 8 }}>
          Placement Readiness Index — measures current preparation based on StudentHelp assessment data.
          Algorithm version: <span className="mono">{data.algorithm_version}</span>
        </p>
        {data.readiness_trend?.length > 1 && (
          <div style={{ marginTop: 12, fontSize: 12, color: "var(--ink-soft)" }}>
            {data.readiness_trend.length} readiness snapshots recorded, oldest {new Date(data.readiness_trend[0].date).toLocaleDateString()} →
            latest {new Date(data.readiness_trend[data.readiness_trend.length - 1].date).toLocaleDateString()}
          </div>
        )}
      </Section>

      {/* Skill Breakdown */}
      <Section title="Skill Breakdown">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {Object.entries(DIMENSION_LABELS).map(([key, label]) => {
            const val = breakdown[key];
            return (
              <div key={key}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                  <span>{label}</span>
                  <span className="mono" style={{ fontWeight: val === null || val === undefined ? 500 : 700, color: val === null || val === undefined ? "var(--ink-soft)" : undefined }}>
                    {val === null || val === undefined ? "Not Assessed" : `${val}%`}
                  </span>
                </div>
                <div style={{ background: "var(--line)", borderRadius: 6, height: 6, overflow: "hidden" }}>
                  <div style={{
                    background: val === null || val === undefined ? "var(--line)" : val >= 75 ? "var(--primary)" : val >= 50 ? "#d97706" : "var(--danger)",
                    height: "100%",
                    width: `${val === null || val === undefined ? 0 : Math.min(100, Math.max(0, val))}%`,
                  }} />
                </div>
              </div>
            );
          })}
        </div>
      </Section>

      {/* Assessment History */}
      <Section title="Assessment History">
        {data.assessment_history?.length ? (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--line)", textAlign: "left" }}>
                <th style={{ padding: "6px 8px" }}>Date</th>
                <th style={{ padding: "6px 8px" }}>Subject</th>
                <th style={{ padding: "6px 8px" }}>Score</th>
              </tr>
            </thead>
            <tbody>
              {data.assessment_history.map((a: any, i: number) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--line)" }}>
                  <td style={{ padding: "6px 8px" }}>{new Date(a.date).toLocaleDateString()}</td>
                  <td style={{ padding: "6px 8px" }}>{a.subject}</td>
                  <td style={{ padding: "6px 8px" }} className="mono">{a.score_percent}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ fontSize: 13, color: "var(--ink-soft)" }}>No assessments taken yet.</p>
        )}
      </Section>

      {/* Target Companies */}
      <Section title="Target Companies">
        {data.target_companies?.length ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {data.target_companies.map((c: any) => (
              <div key={c.company_id} style={{ padding: 12, border: "1px solid var(--line)", borderRadius: 8, display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
                <div>
                  <strong>{c.name}</strong>
                  <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>{(c.roles || []).join(", ") || "Role not specified"}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div className="mono" style={{ fontSize: 13, fontWeight: 700 }}>
                    {c.resume_match_percent !== null && c.resume_match_percent !== undefined ? `${c.resume_match_percent}% match` : "Not analyzed"}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--ink-soft)" }}>{c.resume_match_note}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: 13, color: "var(--ink-soft)" }}>No target companies selected yet.</p>
        )}
      </Section>

      {/* Preparation */}
      <Section title="Preparation">
        {data.preparation?.has_plan ? (
          <div>
            <p style={{ fontSize: 13 }}>
              Plan for <strong>{data.preparation.target_company_name || "general preparation"}</strong> · {data.preparation.days_total} days
            </p>
            <div style={{ background: "var(--line)", borderRadius: 6, height: 8, overflow: "hidden", marginTop: 8, maxWidth: 300 }}>
              <div style={{ background: "var(--primary)", height: "100%", width: `${data.preparation.progress_percent || 0}%` }} />
            </div>
            <p style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>{data.preparation.progress_percent || 0}% complete</p>
          </div>
        ) : (
          <p style={{ fontSize: 13, color: "var(--ink-soft)" }}>No preparation plan generated yet.</p>
        )}
      </Section>

      {/* Mock Interviews */}
      <Section title="Mock Interviews">
        {data.mock_interviews?.length ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {data.mock_interviews.map((m: any, i: number) => (
              <div key={i} style={{ padding: 12, border: "1px solid var(--line)", borderRadius: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                  <span>{new Date(m.date).toLocaleDateString()}</span>
                  <span className="mono" style={{ fontWeight: 700 }}>{m.overall_score !== null ? `${m.overall_score}/100` : "Not scored"}</span>
                </div>
                {m.is_ai_generated_feedback && (
                  <div style={{ fontSize: 11, color: "var(--ink-soft)", marginTop: 4 }}>AI-generated feedback</div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: 13, color: "var(--ink-soft)" }}>No mock interviews completed yet.</p>
        )}
      </Section>

      {/* Interventions */}
      <Section title="Interventions">
        {data.interventions?.length ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {data.interventions.map((iv: any) => (
              <div key={iv.id} style={{ padding: 12, border: "1px solid var(--line)", borderRadius: 8, display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
                <div>
                  <strong>{iv.title}</strong>
                  <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>{iv.status === "completed" ? "Completed" : "Active"}</div>
                </div>
                <div style={{ textAlign: "right", fontSize: 12 }}>
                  {iv.post_avg_score !== null && iv.post_avg_score !== undefined ? (
                    <>
                      Before: {iv.pre_avg_score ?? "—"} → After: {iv.post_avg_score}
                      {iv.improvement_delta !== null && iv.improvement_delta !== undefined && (
                        <div style={{ fontWeight: 700, color: "var(--primary)" }}>
                          {iv.improvement_delta >= 0 ? "+" : ""}{iv.improvement_delta} pts
                        </div>
                      )}
                    </>
                  ) : (
                    <span style={{ color: "var(--ink-soft)" }}>Post-assessment not completed</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: 13, color: "var(--ink-soft)" }}>No interventions assigned to this student.</p>
        )}
      </Section>
    </main>
  );
}

export default function TpoStudentDetailPage() {
  return (
    <RequireAuth role="tpo">
      <TpoStudentDetailContent />
    </RequireAuth>
  );
}
