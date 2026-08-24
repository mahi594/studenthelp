"use client";
import RequireAuth from "../../components/RequireAuth";

import { useState, useEffect } from "react";
import { listCompanies, generatePrepPlan, getLatestPrepPlan, updatePrepPlanTaskStatus, PrepPlan, PrepPlanTask } from "../../lib/api";
import ReadinessLadder from "../../components/ReadinessLadder";

function PrepPlanPageContent() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>("");
  const [days, setDays] = useState<number>(14);
  const [plan, setPlan] = useState<PrepPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [updatingTaskIndex, setUpdatingTaskIndex] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  async function loadInitialData() {
    try {
      const [compList, latestPlan] = await Promise.all([
        listCompanies().catch(() => []),
        getLatestPrepPlan().catch(() => null),
      ]);
      setCompanies(compList);
      if (latestPlan) {
        setPlan(latestPlan);
        if (latestPlan.target_company_id) {
          setSelectedCompany(latestPlan.target_company_id);
        }
      }
    } catch (e: any) {
      console.error(e);
    }
  }

  async function handleGenerate() {
    if (!selectedCompany) return;
    setLoading(true);
    setError(null);
    try {
      const newPlan = await generatePrepPlan(selectedCompany, days);
      setPlan(newPlan);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to generate plan");
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleTask(taskIndex: number, currentCompleted: boolean) {
    if (!plan) return;
    setUpdatingTaskIndex(taskIndex);
    try {
      const updatedPlan = await updatePrepPlanTaskStatus(plan.id, taskIndex, !currentCompleted);
      setPlan(updatedPlan);
    } catch (e: any) {
      setError("Failed to update task completion");
    } finally {
      setUpdatingTaskIndex(null);
    }
  }

  const tasks = plan?.tasks || [];
  const progressScore = plan ? plan.progress_percent : 0;
  const completedCount = tasks.filter((t) => t.completed || t.status === "completed").length;

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Your Prep Plan</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
        A day-by-day plan built from your weak subjects and your target company's real interview rounds.
      </p>

      <div className="card" style={{ padding: 24, marginTop: 24 }}>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <select value={selectedCompany} onChange={(e) => setSelectedCompany(e.target.value)} style={{ flex: 1, minWidth: 180 }}>
            <option value="">Select target company</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>Days:</span>
            <input
              type="number"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              style={{ width: 70 }}
              min={1}
              max={60}
            />
          </div>
          <button onClick={handleGenerate} disabled={loading || !selectedCompany} className="btn btn-primary">
            {loading ? "Generating..." : "Generate New Plan"}
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ padding: 16, marginTop: 16, borderColor: "var(--danger)" }}>
          <span style={{ color: "var(--danger)", fontSize: 14 }}>{error}</span>
        </div>
      )}

      {plan && tasks.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <div className="card" style={{ padding: "20px 24px", marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <span style={{ fontWeight: 600, fontSize: 15 }}>Preparation Progress: {progressScore}%</span>
              <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>
                {completedCount} of {tasks.length} tasks completed
              </span>
            </div>
            <ReadinessLadder score={progressScore} rungs={10} height={10} />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {tasks.map((t, i) => {
              const isDone = t.completed || t.status === "completed";
              return (
                <div
                  key={i}
                  className="card"
                  style={{
                    padding: 20,
                    opacity: isDone ? 0.8 : 1,
                    borderColor: isDone ? "var(--accent)" : undefined,
                    transition: "all 0.2s ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
                    <input
                      type="checkbox"
                      checked={!!isDone}
                      disabled={updatingTaskIndex === i}
                      onChange={() => handleToggleTask(i, !!isDone)}
                      style={{ marginTop: 4, width: 18, height: 18, cursor: "pointer" }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span className="mono" style={{ fontSize: 12, color: "var(--accent)", fontWeight: 600 }}>
                          DAY {t.day} · {t.topic?.toUpperCase()}
                        </span>
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: 600,
                            padding: "2px 8px",
                            borderRadius: 12,
                            background: isDone ? "#d1fae5" : "#f3f4f6",
                            color: isDone ? "#065f46" : "#374151",
                          }}
                        >
                          {isDone ? "✓ Completed" : "Planned"}
                        </span>
                      </div>
                      <div
                        style={{
                          fontSize: 16,
                          fontWeight: 600,
                          marginTop: 6,
                          textDecoration: isDone ? "line-through" : "none",
                          color: isDone ? "var(--ink-soft)" : "inherit",
                        }}
                      >
                        {t.task}
                      </div>
                      <div style={{ fontSize: 14, color: "var(--ink-soft)", marginTop: 6 }}>{t.reason}</div>
                      {t.source_url && (
                        <a href={t.source_url} target="_blank" rel="noreferrer" style={{ fontSize: 13, marginTop: 10, display: "inline-block" }}>
                          📖 {t.source_title || "Study Resource"} →
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </main>
  );
}

export default function PrepPlanPage() {
  return (
    <RequireAuth>
      <PrepPlanPageContent />
    </RequireAuth>
  );
}
