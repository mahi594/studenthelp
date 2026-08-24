"use client";

import { useEffect, useState } from "react";
import RequireAuth from "../../../components/RequireAuth";
import { getAdminLeetCodeTrack, LeetCodeStudentSummary } from "../../../lib/api";

function LeetCodeTrackerContent() {
  const [students, setStudents] = useState<LeetCodeStudentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<"all" | "solved" | "pending">("all");

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const data = await getAdminLeetCodeTrack();
      setStudents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const filtered = students.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.email.toLowerCase().includes(search.toLowerCase()) ||
      (s.leetcode_username && s.leetcode_username.toLowerCase().includes(search.toLowerCase()));

    if (!matchesSearch) return false;
    if (filterStatus === "solved") return s.solved_today;
    if (filterStatus === "pending") return !s.solved_today;
    return true;
  });

  const solvedTodayCount = students.filter((s) => s.solved_today).length;

  return (
    <main style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 30, margin: 0 }}>Student LeetCode Daily Tracker</h1>
          <p style={{ fontSize: 14, color: "var(--ink-soft)", marginTop: 6 }}>
            Monitor student problem-solving consistency, daily practice streaks, and recent submissions in real time.
          </p>
        </div>
        <button onClick={fetchData} className="btn btn-secondary" style={{ fontSize: 13 }}>
          ↻ Refresh Tracker
        </button>
      </div>

      {/* Summary Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginTop: 24 }}>
        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase" }}>
            Total Registered Students
          </div>
          <div style={{ fontSize: 26, fontWeight: 800, marginTop: 8 }}>{students.length}</div>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase" }}>
            Completed Practice Today
          </div>
          <div style={{ fontSize: 26, fontWeight: 800, marginTop: 8, color: "var(--primary)" }}>
            ✅ {solvedTodayCount} / {students.length}
          </div>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase" }}>
            Pending Today
          </div>
          <div style={{ fontSize: 26, fontWeight: 800, marginTop: 8, color: "#d97706" }}>
            ⏳ {students.length - solvedTodayCount}
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div style={{ display: "flex", gap: 12, marginTop: 28, flexWrap: "wrap" }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by student name, email, or handle..."
          style={{ flex: 1, minWidth: 260, padding: "10px 14px" }}
        />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as any)}
          style={{ padding: "10px 14px", borderRadius: 8, border: "1px solid var(--line)", fontSize: 13, background: "var(--surface)" }}
        >
          <option value="all">All Students</option>
          <option value="solved">Solved Today ✅</option>
          <option value="pending">Pending Today ⏳</option>
        </select>
      </div>

      {/* Student Tracker Table */}
      <div className="card" style={{ padding: 0, marginTop: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 32, textAlign: "center", color: "var(--ink-soft)" }}>Loading student tracker data...</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 32, textAlign: "center", color: "var(--ink-soft)" }}>No students match your query.</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13.5 }}>
            <thead>
              <tr style={{ background: "rgba(0,0,0,0.02)", borderBottom: "1px solid var(--line)", textAlign: "left" }}>
                <th style={{ padding: "12px 16px" }}>Student</th>
                <th style={{ padding: "12px 16px" }}>LeetCode Handle</th>
                <th style={{ padding: "12px 16px" }}>Today's Status</th>
                <th style={{ padding: "12px 16px" }}>Streak</th>
                <th style={{ padding: "12px 16px" }}>Total Solved</th>
                <th style={{ padding: "12px 16px" }}>Latest Problem Logged</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => (
                <tr key={s.user_id} style={{ borderBottom: "1px solid var(--line)" }}>
                  <td style={{ padding: "12px 16px" }}>
                    <div style={{ fontWeight: 700, color: "var(--ink)" }}>{s.name}</div>
                    <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>{s.email}</div>
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    {s.leetcode_username ? (
                      <a
                        href={`https://leetcode.com/${s.leetcode_username}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: "var(--primary)", fontWeight: 600, textDecoration: "none" }}
                      >
                        @{s.leetcode_username} ↗
                      </a>
                    ) : (
                      <span style={{ color: "var(--ink-soft)", fontStyle: "italic" }}>Not set</span>
                    )}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <span
                      style={{
                        fontSize: 11.5,
                        fontWeight: 700,
                        padding: "3px 9px",
                        borderRadius: 6,
                        background: s.solved_today ? "rgba(31,92,74,0.12)" : "rgba(217,119,6,0.12)",
                        color: s.solved_today ? "var(--primary)" : "#d97706",
                      }}
                    >
                      {s.solved_today ? "✅ Solved Today" : "⏳ Pending"}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px", fontWeight: 700, color: "#d97706" }}>
                    🔥 {s.streak} Days
                  </td>
                  <td style={{ padding: "12px 16px", fontWeight: 600 }}>
                    ⚡ {s.total_solved}
                  </td>
                  <td style={{ padding: "12px 16px", color: "var(--ink-soft)" }}>
                    {s.latest_problem ? (
                      <div>
                        <span style={{ fontWeight: 600, color: "var(--ink)" }}>{s.latest_problem}</span>
                        {s.last_solved_date && <div style={{ fontSize: 11 }}>({s.last_solved_date})</div>}
                      </div>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}

export default function LeetCodeTrackerPage() {
  return (
    <RequireAuth role="tpo">
      <LeetCodeTrackerContent />
    </RequireAuth>
  );
}

