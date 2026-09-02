"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, markApplication, listMyApplications, getLatestReadiness } from "../../../lib/api";

export default function CompanyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const companyId = params?.id as string;

  const [company, setCompany] = useState<any>(null);
  const [readiness, setReadiness] = useState<any>(null);
  const [prepPlan, setPrepPlan] = useState<any>(null);
  const [resumeMatch, setResumeMatch] = useState<any>(null);
  const [applicationStatus, setApplicationStatus] = useState<string>("not_applied");
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    try {
      const [compRes, readRes, prepRes, appsRes, resumeRes] = await Promise.all([
        api.get(`/companies/${companyId}`).catch(async () => {
          const all = await api.get("/companies/");
          return { data: all.data.find((c: any) => c.id === companyId) };
        }),
        getLatestReadiness().catch(() => null),
        api.get(`/prep-plan/latest?company_id=${companyId}`).catch(() => null),
        listMyApplications().catch(() => []),
        api.get(`/resume/latest?target_company_id=${companyId}`).catch(() => null),
      ]);

      setCompany(compRes.data || null);
      setReadiness(readRes);
      setPrepPlan(prepRes?.data || null);
      setResumeMatch(resumeRes?.data || null);

      const appMatch = appsRes.find((a: any) => a.company_id === companyId);
      if (appMatch) {
        setApplicationStatus(appMatch.status);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (companyId) {
      loadData();
    }
  }, [companyId]);

  async function handleMarkApplied() {
    setApplicationStatus("applied");
    await markApplication(companyId, "applied");
  }

  if (loading) {
    return (
      <main style={{ maxWidth: 840, margin: "0 auto", padding: "40px 24px" }}>
        <p style={{ color: "var(--ink-soft)" }}>Loading company detail...</p>
      </main>
    );
  }

  if (!company) {
    return (
      <main style={{ maxWidth: 840, margin: "0 auto", padding: "40px 24px" }}>
        <h2>Company Not Found</h2>
        <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>The requested target company profile could not be loaded.</p>
        <button onClick={() => router.push("/companies")} className="btn btn-secondary" style={{ marginTop: 16 }}>
          ← Back to Target Companies
        </button>
      </main>
    );
  }

  let badgeText = "UNVERIFIED";
  let badgeBg = "rgba(107,114,128,0.1)";
  let badgeColor = "#4b5563";

  if (company.is_curated_verified) {
    badgeText = "✓ VERIFIED BY PLACEMENT CELL";
    badgeBg = "rgba(31,92,74,0.1)";
    badgeColor = "var(--primary)";
  } else if (company.source_type === "alumni_report") {
    badgeText = "ALUMNI REPORTED";
    badgeBg = "rgba(217,119,6,0.1)";
    badgeColor = "#b45309";
  } else if (company.source_type === "ai_recommended") {
    badgeText = "AI RECOMMENDED";
    badgeBg = "rgba(59,130,246,0.1)";
    badgeColor = "#2563eb";
  }

  const overallScore = readiness?.composite_score;
  const isAssessed = overallScore !== undefined && overallScore !== null;
  const breakdown = readiness?.breakdown || {};
  const weaknesses = breakdown?.top_weaknesses || [];

  const completedTasks = prepPlan?.tasks?.filter((t: any) => t.is_completed).length || 0;
  const totalTasks = prepPlan?.tasks?.length || 0;
  const nextTask = prepPlan?.tasks?.find((t: any) => !t.is_completed);

  return (
    <main style={{ maxWidth: 840, margin: "0 auto", padding: "40px 24px" }}>
      <button
        onClick={() => router.push("/companies")}
        className="btn btn-secondary"
        style={{ marginBottom: 20, fontSize: 13 }}
      >
        ← Back to Target Companies
      </button>

      {/* COMPANY HEADER */}
      <div className="card" style={{ padding: 24, marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <h1 style={{ fontSize: 28, fontWeight: 800 }}>{company.name}</h1>
              <span className="mono" style={{ fontSize: 11, background: badgeBg, color: badgeColor, padding: "3px 10px", borderRadius: 12, fontWeight: 700 }}>
                {badgeText}
              </span>
            </div>
            <p style={{ color: "var(--ink-soft)", fontSize: 14, marginTop: 6 }}>
              Source: {company.source_info || company.source_type || "Institutional Placement Repository"}
            </p>

            <div style={{ display: "flex", gap: 6, marginTop: 12, flexWrap: "wrap" }}>
              {company.roles?.map((role: string) => (
                <span key={role} className="badge badge-not-applied">{role}</span>
              ))}
            </div>
          </div>

          <span className={`badge ${applicationStatus !== "not_applied" ? "badge-applied" : "badge-not-applied"}`}>
            {applicationStatus !== "not_applied" ? "Applied" : "Not applied"}
          </span>
        </div>
      </div>

      {/* ELIGIBILITY */}
      <div className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Placement Eligibility Requirements</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
          <div>
            <span style={{ fontSize: 12, color: "var(--ink-soft)", textTransform: "uppercase" }}>Minimum CGPA</span>
            <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4 }}>
              {company.min_cgpa ? company.min_cgpa : "Not available"}
            </div>
          </div>
          <div>
            <span style={{ fontSize: 12, color: "var(--ink-soft)", textTransform: "uppercase" }}>Preferred Branches</span>
            <div style={{ fontSize: 15, fontWeight: 600, marginTop: 4 }}>
              {company.preferred_branches?.length ? company.preferred_branches.join(", ") : "Not available"}
            </div>
          </div>
          <div>
            <span style={{ fontSize: 12, color: "var(--ink-soft)", textTransform: "uppercase" }}>Data Confidence</span>
            <div style={{ fontSize: 15, fontWeight: 600, marginTop: 4 }}>
              {company.confidence ? company.confidence : "Not available"}
            </div>
          </div>
        </div>
      </div>

      {/* HIRING PROCESS */}
      <div className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Hiring Process & Rounds</h3>
        {company.rounds && company.rounds.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {company.rounds.map((round: any, idx: number) => (
              <div key={idx} style={{ padding: 14, borderRadius: 8, border: "1px solid var(--line)", background: "rgba(0,0,0,0.01)" }}>
                <div style={{ fontWeight: 700, fontSize: 15 }}>
                  {idx + 1}. {round.name || round.round_name || `Round ${idx + 1}`}
                </div>
                {round.difficulty && <span style={{ fontSize: 12, color: "var(--ink-soft)" }}>Difficulty: {round.difficulty}</span>}
                {round.subjects && <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 4 }}>Subjects: {round.subjects.join(", ")}</p>}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: "var(--ink-soft)", fontSize: 14 }}>Hiring process information not available yet.</p>
        )}
      </div>

      {/* READINESS & SKILL GAPS */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
        <div className="card" style={{ padding: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Overall Placement Readiness</h3>
          <div style={{ fontSize: 32, fontWeight: 800, color: isAssessed ? "var(--primary)" : "var(--ink-soft)" }}>
            {isAssessed ? `${overallScore}%` : "Not Assessed"}
          </div>
          <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 6 }}>
            {isAssessed ? "Calculated from your recent assessments & mock interviews." : "Take a placement assessment to view your readiness index."}
          </p>
        </div>

        <div className="card" style={{ padding: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Relevant Skill Gaps</h3>
          {weaknesses.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {weaknesses.map((w: string) => (
                <span key={w} className="badge" style={{ background: "rgba(239,68,68,0.1)", color: "#dc2626" }}>
                  {w}
                </span>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: 13, color: "var(--ink-soft)" }}>
              {isAssessed ? "No critical skill gaps identified." : "Not Assessed"}
            </p>
          )}
        </div>
      </div>

      {/* RESUME MATCH & PREPARATION */}
      <div className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Resume & Preparation Status</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div>
            <h4 style={{ fontSize: 14, fontWeight: 600, color: "var(--ink-soft)" }}>Resume Match</h4>
            {resumeMatch?.match_result ? (
              <div style={{ marginTop: 6 }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: "var(--primary)" }}>
                  {resumeMatch.match_result.match_score_percent}% Match
                </div>
                {resumeMatch.match_result.missing_keywords?.length > 0 && (
                  <p style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
                    Missing keywords: {resumeMatch.match_result.missing_keywords.join(", ")}
                  </p>
                )}
              </div>
            ) : (
              <p style={{ fontSize: 14, marginTop: 6, color: "var(--ink-soft)" }}>
                Upload your resume to see your company-specific match.
              </p>
            )}
            <button onClick={() => router.push("/resume")} className="btn btn-secondary" style={{ marginTop: 10, fontSize: 13 }}>
              Upload / Analyze Resume →
            </button>
          </div>

          <div>
            <h4 style={{ fontSize: 14, fontWeight: 600, color: "var(--ink-soft)" }}>Preparation Plan</h4>
            {totalTasks > 0 ? (
              <div style={{ marginTop: 6 }}>
                <p style={{ fontSize: 14, fontWeight: 700 }}>
                  Progress: {completedTasks} / {totalTasks} tasks completed
                </p>
                {nextTask && (
                  <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 4 }}>
                    Next task: <strong>{nextTask.title}</strong>
                  </p>
                )}
              </div>
            ) : (
              <p style={{ fontSize: 14, marginTop: 6, color: "var(--ink-soft)" }}>Start your preparation plan to track your target readiness.</p>
            )}
          </div>
        </div>
      </div>

      {/* PRIMARY ACTION CTA BAR */}
      <div className="card" style={{ padding: 24, background: "rgba(31,92,74,0.03)", borderColor: "var(--primary)" }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Target Preparation Actions</h3>
        <p style={{ fontSize: 14, color: "var(--ink-soft)", marginBottom: 16 }}>
          Generate a personalized company preparation roadmap, practice AI mock interviews, or apply directly.
        </p>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <a
            href={`/prep-plan?company_id=${company.id}`}
            className="btn btn-primary"
            style={{ textDecoration: "none", fontSize: 14, background: "var(--primary)", color: "#fff", fontWeight: 700, padding: "10px 20px", borderRadius: 8 }}
          >
            START PREPARATION →
          </a>
          <button
            onClick={() => router.push("/mock-interview")}
            className="btn btn-secondary"
            style={{ fontSize: 14, padding: "10px 20px", borderRadius: 8 }}
          >
            Practice Mock Interview
          </button>
          {applicationStatus === "not_applied" && (
            <button
              onClick={handleMarkApplied}
              className="btn btn-secondary"
              style={{ fontSize: 14, padding: "10px 20px", borderRadius: 8 }}
            >
              Mark as Applied
            </button>
          )}
        </div>
      </div>
    </main>
  );
}
