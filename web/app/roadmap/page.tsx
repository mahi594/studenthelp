"use client";
import RequireAuth from "../../components/RequireAuth";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listCompanies, getLatestRoadmap, generateRoadmap, RoadmapPhase } from "../../lib/api";

function RoadmapPageContent() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [horizonMonths, setHorizonMonths] = useState(6);
  const [phases, setPhases] = useState<RoadmapPhase[]>([]);
  const [createdAt, setCreatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        const [companiesData, existing] = await Promise.all([listCompanies(), getLatestRoadmap()]);
        setCompanies(companiesData);
        if (existing) {
          setPhases(existing.phases || []);
          setCreatedAt(existing.created_at);
          setHorizonMonths(existing.horizon_months);
          if (existing.target_company_ids && existing.target_company_ids.length > 0) {
            setSelectedCompanies(existing.target_company_ids);
          }
        }
      } finally {
        setInitialLoading(false);
      }
    }
    init();
  }, []);

  function toggleCompany(id: string) {
    setSelectedCompanies((prev) => (prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]));
  }

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const roadmap = await generateRoadmap(horizonMonths, selectedCompanies);
      setPhases(roadmap.phases || []);
      setCreatedAt(roadmap.created_at);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to generate roadmap");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 840, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Your placement roadmap</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8, fontSize: 15 }}>
        A long-term, multi-month strategy built from your diagnostic quiz performance — prioritizing your weakest subjects first.
      </p>

      <div className="card" style={{ padding: 24, marginTop: 24 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 8 }}>
          Planning Horizon (Months)
        </label>
        <input
          type="number"
          value={horizonMonths}
          onChange={(e) => setHorizonMonths(Number(e.target.value))}
          style={{ width: 120, padding: "8px 12px", fontSize: 14 }}
        />

        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 20, marginBottom: 8 }}>
          Target Companies (Saved context)
        </label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {companies.map((c) => {
            const isSelected = selectedCompanies.includes(c.id);
            return (
              <button
                key={c.id}
                onClick={() => toggleCompany(c.id)}
                className={isSelected ? "badge badge-applied" : "badge badge-not-applied"}
                style={{
                  padding: "6px 12px",
                  borderRadius: 20,
                  border: isSelected ? "1.5px solid var(--primary)" : "1px solid var(--line)",
                  cursor: "pointer",
                  fontWeight: isSelected ? 600 : 400,
                }}
              >
                {isSelected ? `✓ ${c.name}` : `+ ${c.name}`}
              </button>
            );
          })}
        </div>

        <button onClick={handleGenerate} disabled={loading} className="btn btn-primary" style={{ marginTop: 24, width: "100%" }}>
          {loading ? "Generating Roadmap..." : phases.length > 0 ? "Regenerate Roadmap" : "Generate Roadmap"}
        </button>

        {selectedCompanies.length > 0 && (
          <div style={{ marginTop: 18, paddingTop: 16, borderTop: "1px solid var(--line)" }}>
            <p style={{ fontSize: 13, color: "var(--ink-soft)", marginBottom: 8 }}>
              Need custom modifications or company-specific round pacing? Customize your roadmap via chat.
            </p>
            <Link
              href={`/chat?company_id=${selectedCompanies[0]}&company_name=${encodeURIComponent(
                companies.find((c) => c.id === selectedCompanies[0])?.name || ""
              )}`}
              className="btn btn-secondary"
              style={{ textDecoration: "none", fontSize: 13 }}
            >
              Customize in Chat
            </Link>
          </div>
        )}
      </div>

      {error && (
        <div className="card" style={{ padding: 16, marginTop: 16, borderColor: "var(--danger)" }}>
          <span style={{ color: "var(--danger)", fontSize: 14 }}>{error}</span>
        </div>
      )}

      {initialLoading && <p style={{ color: "var(--ink-soft)", marginTop: 24 }}>Loading roadmap details...</p>}

      {!initialLoading && phases.length > 0 && (
        <div style={{ marginTop: 36 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h2 style={{ fontSize: 22, margin: 0 }}>Interactive Roadmap Timeline</h2>
            {createdAt && (
              <span className="mono" style={{ fontSize: 12, color: "var(--ink-soft)" }}>
                Generated {new Date(createdAt).toLocaleDateString()}
              </span>
            )}
          </div>

          {/* Visual Progress Chart Bar */}
          <div className="card" style={{ padding: 20, marginBottom: 24, background: "var(--surface)" }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "var(--ink-soft)", marginBottom: 8 }}>
              TIMELINE BREAKDOWN ({horizonMonths} MONTHS)
            </div>
            <div style={{ display: "flex", height: 12, borderRadius: 6, overflow: "hidden", gap: 2, background: "var(--line)" }}>
              {phases.map((_, idx) => (
                <div
                  key={idx}
                  style={{
                    flex: 1,
                    background: `hsl(${210 + idx * 35}, 75%, 55%)`,
                    borderRadius: 2,
                  }}
                  title={`Phase ${idx + 1}`}
                />
              ))}
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontSize: 11, color: "var(--ink-soft)" }}>
              <span>Month 1</span>
              <span>Month {Math.ceil(horizonMonths / 2)}</span>
              <span>Month {horizonMonths}</span>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 16, position: "relative" }}>
            {phases.map((p, i) => (
              <div
                key={i}
                className="card"
                style={{
                  padding: 24,
                  borderLeft: `4px solid hsl(${210 + i * 35}, 75%, 55%)`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span className="mono" style={{ fontSize: 13, color: "var(--primary)", fontWeight: 700 }}>
                    PHASE {i + 1}: {p.phase?.toUpperCase()}
                  </span>
                  <span className="badge" style={{ fontSize: 11, background: "var(--accent-soft)" }}>
                    Step {i + 1} of {phases.length}
                  </span>
                </div>

                <div style={{ display: "flex", gap: 6, marginTop: 12, flexWrap: "wrap" }}>
                  {p.focus_subjects?.map((s) => (
                    <span key={s} className="badge badge-not-applied" style={{ fontSize: 12, fontWeight: 500 }}>
                      {s}
                    </span>
                  ))}
                </div>

                <p style={{ fontSize: 14, color: "var(--ink-soft)", marginTop: 14, lineHeight: 1.5 }}>
                  {p.reason}
                </p>

                {p.milestones?.length > 0 && (
                  <div style={{ marginTop: 16, paddingTop: 14, borderTop: "1px dashed var(--line)" }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "var(--ink-soft)", marginBottom: 10 }}>
                      ACTIONABLE MILESTONES
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {p.milestones.map((m, j) => (
                        <label key={j} style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 14, cursor: "pointer" }}>
                          <input type="checkbox" style={{ marginTop: 3 }} />
                          <span>{m}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!initialLoading && phases.length === 0 && !error && (
        <div className="card" style={{ padding: 40, marginTop: 24, textAlign: "center" }}>
          <p style={{ color: "var(--ink-soft)", fontSize: 15 }}>No roadmap generated yet. Select your target companies and click Generate Roadmap above.</p>
        </div>
      )}
    </main>
  );
}


export default function RoadmapPage() {
  return (
    <RequireAuth>
      <RoadmapPageContent />
    </RequireAuth>
  );
}
