"use client";
import RequireAuth from "../../../components/RequireAuth";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTpoDashboard, api } from "../../../lib/api";
import ReadinessLadder from "../../../components/ReadinessLadder";

function TpoDashboardPageContent() {
  const [data, setData] = useState<any>(null);
  const [branch, setBranch] = useState("");
  const [gradYear, setGradYear] = useState("");
  const [cgpaMin, setCgpaMin] = useState("");
  const [cgpaMax, setCgpaMax] = useState("");
  const [readinessMin, setReadinessMin] = useState("");
  const [readinessMax, setReadinessMax] = useState("");
  const [riskFilter, setRiskFilter] = useState("All");
  const [assessmentStatus, setAssessmentStatus] = useState("All");
  const [interviewStatus, setInterviewStatus] = useState("All");
  const [skillTopic, setSkillTopic] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const [interventions, setInterventions] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Intervention Creation Modal State
  const [showInterventionModal, setShowInterventionModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newTopic, setNewTopic] = useState("DSA");
  const [newType, setNewType] = useState("workshop");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      // All filtering happens server-side (see /tpo/dashboard query params) -
      // the frontend never fetches the whole student roster and filters it
      // client-side.
      const filterParams: Record<string, any> = { page, page_size: pageSize };
      if (branch) filterParams.branch = branch;
      if (gradYear) filterParams.grad_year = Number(gradYear);
      if (cgpaMin) filterParams.cgpa_min = Number(cgpaMin);
      if (cgpaMax) filterParams.cgpa_max = Number(cgpaMax);
      if (readinessMin) filterParams.readiness_min = Number(readinessMin);
      if (readinessMax) filterParams.readiness_max = Number(readinessMax);
      if (riskFilter !== "All") filterParams.risk_category = riskFilter;
      if (assessmentStatus !== "All") filterParams.assessment_status = assessmentStatus;
      if (interviewStatus !== "All") filterParams.interview_status = interviewStatus;
      if (skillTopic) filterParams.skill_topic = skillTopic;

      const [dashboardRes, interventionsRes] = await Promise.all([
        getTpoDashboard(filterParams),
        api.get("/tpo/interventions").then((res) => res.data).catch(() => []),
      ]);
      setData(dashboardRes);
      setInterventions(interventionsRes);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "You need TPO or Admin permissions to access this page.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  function applyFilters() {
    setPage(1);
    // load() re-runs via the page effect above when page resets to 1, but if
    // it was already 1 the effect won't refire - so also call load directly.
    if (page === 1) load();
  }

  async function handleCreateIntervention() {
    if (!newTitle.trim()) return;
    try {
      // Targets students from the CURRENTLY LOADED page whose readiness is
      // below the "On Track" threshold - if there are more matching
      // students on other pages, narrow the filters/page size before
      // creating the intervention so they're included too.
      const targetIds = (data?.all_students || [])
        .filter((s: any) => s.latest_composite_score !== null && s.latest_composite_score < 65)
        .map((s: any) => s.user_id);

      await api.post("/tpo/interventions", {
        title: newTitle,
        skill_topic: newTopic,
        intervention_type: newType,
        target_student_ids: targetIds,
      });

      setShowInterventionModal(false);
      setNewTitle("");
      load();
    } catch (e: any) {
      alert("Failed to create intervention: " + (e?.response?.data?.detail || e.message));
    }
  }

  async function handleCompleteIntervention(id: string) {
    try {
      await api.post(`/tpo/interventions/${id}/complete`);
      load();
    } catch (e: any) {
      alert("Failed to complete intervention: " + (e?.response?.data?.detail || e.message));
    }
  }

  async function handleExportCSV() {
    try {
      const res = await api.get("/tpo/export", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `tpo_placement_readiness_report_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (e: any) {
      alert("Export failed: " + (e?.response?.data?.detail || e.message));
    }
  }

  const allStudents = data?.all_students || [];

  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "40px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 30, fontWeight: 800 }}>Placement Cell (TPO) Portal</h1>
          <p style={{ color: "var(--ink-soft)", marginTop: 6, fontSize: 14 }}>
            Institutional batch readiness overview, skill gap detection, and intervention impact tracking.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={handleExportCSV} className="btn btn-secondary" style={{ fontSize: 13, height: 38 }}>
            📥 Export CSV Report
          </button>
          <button onClick={() => setShowInterventionModal(true)} className="btn btn-primary" style={{ fontSize: 13, height: 38 }}>
            + Create Intervention
          </button>
        </div>
      </div>

      {/* Filter Row - every filter here is sent to the server (see load()
          above); the frontend never fetches the whole roster and filters it
          client-side. */}
      <div className="card" style={{ padding: 16, marginTop: 24 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10 }}>
          <input
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="Branch (e.g. CSE)"
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
          />
          <input
            value={gradYear}
            onChange={(e) => setGradYear(e.target.value)}
            placeholder="Grad Year"
            type="number"
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
          />
          <input
            value={cgpaMin}
            onChange={(e) => setCgpaMin(e.target.value)}
            placeholder="CGPA min"
            type="number" step="0.1"
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
          />
          <input
            value={cgpaMax}
            onChange={(e) => setCgpaMax(e.target.value)}
            placeholder="CGPA max"
            type="number" step="0.1"
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
          />
          <input
            value={readinessMin}
            onChange={(e) => setReadinessMin(e.target.value)}
            placeholder="Readiness min"
            type="number"
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
          />
          <input
            value={readinessMax}
            onChange={(e) => setReadinessMax(e.target.value)}
            placeholder="Readiness max"
            type="number"
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
          />
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)", background: "var(--surface)", fontSize: 13 }}
          >
            <option value="All">All Risk Categories</option>
            <option value="Not Assessed">Not Assessed</option>
            <option value="Needs Significant Support">Needs Significant Support (&lt;50)</option>
            <option value="Needs Attention">Needs Attention (50-64)</option>
            <option value="On Track">On Track (65-79)</option>
            <option value="Interview Ready">Interview Ready (80+)</option>
          </select>
          <select
            value={assessmentStatus}
            onChange={(e) => setAssessmentStatus(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)", background: "var(--surface)", fontSize: 13 }}
          >
            <option value="All">Assessment: Any</option>
            <option value="assessed">Assessed</option>
            <option value="not_assessed">Not Assessed</option>
          </select>
          <select
            value={interviewStatus}
            onChange={(e) => setInterviewStatus(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)", background: "var(--surface)", fontSize: 13 }}
          >
            <option value="All">Interview: Any</option>
            <option value="attempted">Attempted</option>
            <option value="not_attempted">Not Attempted</option>
          </select>
          <input
            value={skillTopic}
            onChange={(e) => setSkillTopic(e.target.value)}
            placeholder="Weak in skill (e.g. dsa)"
            style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
          />
        </div>
        <div style={{ marginTop: 12 }}>
          <button onClick={applyFilters} className="btn btn-secondary" style={{ fontSize: 13, height: 36 }}>
            Apply Filters
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ padding: 20, marginTop: 24, borderColor: "var(--danger)" }}>
          <span style={{ color: "var(--danger)", fontSize: 14 }}>{error}</span>
        </div>
      )}

      {!error && !loading && data && (
        <>
          {/* Institutional KPI Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginTop: 24 }}>
            <div className="card" style={{ padding: 20 }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--ink-soft)", textTransform: "uppercase" }}>Total Batch</span>
              <div className="display" style={{ fontSize: 32, fontWeight: 800, marginTop: 4 }}>{data.total_students}</div>
            </div>
            <div className="card" style={{ padding: 20 }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--ink-soft)", textTransform: "uppercase" }}>Assessed</span>
              <div className="display" style={{ fontSize: 32, fontWeight: 800, marginTop: 4 }}>
                {data.students_with_score} <span style={{ fontSize: 14, color: "var(--ink-soft)" }}>/ {data.total_students}</span>
              </div>
            </div>
            <div className="card" style={{ padding: 20 }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--ink-soft)", textTransform: "uppercase" }}>Batch Avg Score</span>
              <div className="display" style={{ fontSize: 32, fontWeight: 800, marginTop: 4, color: "var(--primary)" }}>
                {data.batch_average_score ?? "—"}
              </div>
            </div>
            <div className="card" style={{ padding: 20 }}>
              <span className="mono" style={{ fontSize: 11, color: "var(--danger)", textTransform: "uppercase" }}>Needs Support</span>
              <div className="display" style={{ fontSize: 32, fontWeight: 800, marginTop: 4, color: "var(--danger)" }}>
                {data.flagged_students?.length ?? 0}
              </div>
            </div>
          </div>

          {/* Active & Historical Interventions */}
          <div className="card" style={{ padding: 24, marginTop: 28 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 14 }}>Placement Cell Interventions</h2>
            {interventions.length === 0 ? (
              <p style={{ color: "var(--ink-soft)", fontSize: 13 }}>No active or completed interventions recorded yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {interventions.map((item: any) => (
                  <div key={item.id} style={{ padding: 16, borderRadius: 10, border: "1px solid var(--line)", background: "var(--surface)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontWeight: 700, fontSize: 15 }}>{item.title}</span>
                        <span className="mono" style={{ fontSize: 11, background: item.status === "completed" ? "rgba(31,92,74,0.1)" : "rgba(217,119,6,0.1)", color: item.status === "completed" ? "var(--primary)" : "#b45309", padding: "2px 8px", borderRadius: 12, fontWeight: 600 }}>
                          {item.status === "completed" ? "Completed" : "Active"}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
                        Topic: <strong>{item.skill_topic}</strong> · Type: {item.intervention_type} · Target: {item.target_student_ids?.length || 0} students
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                      {item.status === "completed" ? (
                        <div style={{ textAlign: "right" }}>
                          {item.post_avg_score !== null && item.post_avg_score !== undefined ? (
                            <>
                              <div className="mono" style={{ fontSize: 13, fontWeight: 700, color: "var(--primary)" }}>
                                Before: {item.pre_avg_score ?? "—"} → After: {item.post_avg_score}
                              </div>
                              <div style={{ fontSize: 12, color: "var(--primary)", fontWeight: 800 }}>
                                {item.improvement_delta !== null && item.improvement_delta !== undefined
                                  ? `${item.improvement_delta >= 0 ? "+" : ""}${item.improvement_delta} pts Improvement`
                                  : "Improvement not calculable (no pre-baseline)"}
                              </div>
                            </>
                          ) : (
                            <div style={{ fontSize: 12, color: "var(--ink-soft)", fontWeight: 600 }}>
                              Post-assessment not completed
                            </div>
                          )}
                          <div style={{ fontSize: 11, color: "var(--ink-soft)", marginTop: 2 }}>
                            Eligible: {item.eligible_count ?? item.target_student_ids?.length ?? 0} · Reassessed: {item.reassessed_count ?? 0}
                          </div>
                        </div>
                      ) : (
                        <button onClick={() => handleCompleteIntervention(item.id)} className="btn btn-secondary" style={{ fontSize: 12, padding: "6px 12px" }}>
                          Mark Complete &amp; Measure Impact
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Branch Performance Breakdown */}
          {data.branch_breakdown?.length > 0 && (
            <div className="card" style={{ padding: 24, marginTop: 28 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 14 }}>Branch Readiness Distribution</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {data.branch_breakdown.map((b: any) => (
                  <div key={b.branch} style={{ padding: 14, borderRadius: 8, border: "1px solid var(--line)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 6 }}>
                      <span style={{ fontWeight: 700 }}>{b.branch}</span>
                      <span className="mono" style={{ color: "var(--ink-soft)" }}>
                        Avg Score: {b.average_score} · {b.student_count} students
                      </span>
                    </div>
                    <ReadinessLadder score={b.average_score} rungs={10} height={8} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Student Roster Table */}
          <div className="card" style={{ padding: 24, marginTop: 28 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 8 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700 }}>Student Batch Roster</h2>
              <span style={{ fontSize: 12, color: "var(--ink-soft)" }}>
                {data.total_matching ?? allStudents.length} matching · Page {data.page ?? 1} of {data.total_pages ?? 1}
              </span>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid var(--line)", textAlign: "left" }}>
                    <th style={{ padding: "10px 8px" }}>Name</th>
                    <th style={{ padding: "10px 8px" }}>Email</th>
                    <th style={{ padding: "10px 8px" }}>Branch</th>
                    <th style={{ padding: "10px 8px" }}>Grad Year</th>
                    <th style={{ padding: "10px 8px" }}>Readiness Score</th>
                    <th style={{ padding: "10px 8px" }}>Risk Category</th>
                  </tr>
                </thead>
                <tbody>
                  {allStudents.map((s: any) => (
                    <tr key={s.user_id} style={{ borderBottom: "1px solid var(--line)" }}>
                      <td style={{ padding: "10px 8px", fontWeight: 600 }}>
                        <Link href={`/admin/tpo-dashboard/students/${s.user_id}`} style={{ color: "var(--primary)", textDecoration: "none" }}>
                          {s.name}
                        </Link>
                      </td>
                      <td style={{ padding: "10px 8px", color: "var(--ink-soft)" }}>{s.email}</td>
                      <td style={{ padding: "10px 8px" }}>{s.branch || "—"}</td>
                      <td style={{ padding: "10px 8px" }}>{s.grad_year || "—"}</td>
                      <td style={{ padding: "10px 8px", fontWeight: 700 }} className="mono">
                        {s.latest_composite_score !== null ? `${s.latest_composite_score}%` : "Not Assessed"}
                      </td>
                      <td style={{ padding: "10px 8px" }}>
                        <span className="badge" style={{
                          background: s.risk_category === "Interview Ready" ? "rgba(31,92,74,0.12)" : s.risk_category === "Needs Significant Support" ? "#FBE4DC" : "rgba(0,0,0,0.05)",
                          color: s.risk_category === "Interview Ready" ? "var(--primary)" : s.risk_category === "Needs Significant Support" ? "var(--danger)" : "var(--ink)",
                          fontSize: 11, fontWeight: 700
                        }}>
                          {s.risk_category}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {allStudents.length === 0 && (
                    <tr>
                      <td colSpan={6} style={{ padding: 20, textAlign: "center", color: "var(--ink-soft)" }}>
                        No students found matching current filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            {(data.total_pages ?? 1) > 1 && (
              <div style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 16 }}>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: 12, padding: "6px 14px" }}
                  disabled={(data.page ?? 1) <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  ← Previous
                </button>
                <span style={{ fontSize: 12, color: "var(--ink-soft)", alignSelf: "center" }}>
                  Page {data.page ?? 1} of {data.total_pages ?? 1}
                </span>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: 12, padding: "6px 14px" }}
                  disabled={(data.page ?? 1) >= (data.total_pages ?? 1)}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next →
                </button>
              </div>
            )}
          </div>
        </>
      )}

      {/* Modal for Creating Intervention */}
      {showInterventionModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}>
          <div className="card" style={{ width: 440, padding: 28, background: "var(--surface)" }}>
            <h3 style={{ fontSize: 18, fontWeight: 700 }}>Create Placement Intervention</h3>
            <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 4 }}>
              Target students needing support and assign remediations.
            </p>

            <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>Intervention Title</label>
                <input
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. 7-Day DSA Problem Solving Bootcamp"
                  style={{ width: "100%", marginTop: 4, padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>Skill Topic</label>
                <select
                  value={newTopic}
                  onChange={(e) => setNewTopic(e.target.value)}
                  style={{ width: "100%", marginTop: 4, padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
                >
                  <option value="DSA">DSA &amp; Algorithms</option>
                  <option value="Communication">Communication &amp; Soft Skills</option>
                  <option value="Aptitude">Aptitude &amp; Reasoning</option>
                  <option value="DBMS">DBMS &amp; SQL</option>
                  <option value="OS">Operating Systems</option>
                  <option value="System Design">System Design</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)" }}>Type</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  style={{ width: "100%", marginTop: 4, padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)" }}
                >
                  <option value="workshop">Workshop</option>
                  <option value="assignment">Assignment Suite</option>
                  <option value="mock_test">Mock Test Series</option>
                </select>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 20 }}>
              <button onClick={() => setShowInterventionModal(false)} className="btn btn-secondary" style={{ fontSize: 13 }}>
                Cancel
              </button>
              <button onClick={handleCreateIntervention} className="btn btn-primary" style={{ fontSize: 13 }}>
                Assign &amp; Launch
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

export default function TpoDashboardPage() {
  return (
    <RequireAuth role="tpo">
      <TpoDashboardPageContent />
    </RequireAuth>
  );
}
