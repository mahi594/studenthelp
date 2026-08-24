"use client";

import { useEffect, useState } from "react";
import RequireAuth from "../../components/RequireAuth";
import {
  getLeetCodeProfile,
  getLeetCodeRecommendations,
  logLeetCodeProblem,
  LeetCodeProfile,
  LeetCodeRecommendation,
  LeetCodeLogItem,
} from "../../lib/api";

function LeetCodePageContent() {
  const [profile, setProfile] = useState<LeetCodeProfile | null>(null);
  const [recommendations, setRecommendations] = useState<LeetCodeRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLevel, setSelectedLevel] = useState<string>("All");
  const [selectedTopic, setSelectedTopic] = useState<string>("All");

  // Log Modal State
  const [showLogModal, setShowLogModal] = useState(false);
  const [logForm, setLogForm] = useState({
    problem_title: "",
    difficulty: "Easy",
    topic: "Arrays",
    notes: "",
  });
  const [logging, setLogging] = useState(false);
  const [logSuccess, setLogSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchRecommendations();
  }, [selectedLevel, selectedTopic]);

  async function fetchData() {
    setLoading(true);
    try {
      const pData = await getLeetCodeProfile();
      setProfile(pData);
      await fetchRecommendations();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function fetchRecommendations() {
    try {
      const recs = await getLeetCodeRecommendations({
        level: selectedLevel === "All" ? undefined : selectedLevel,
        topic: selectedTopic === "All" ? undefined : selectedTopic,
      });
      setRecommendations(recs);
    } catch (err) {
      console.error(err);
    }
  }

  async function handleLogProblem(e: React.FormEvent) {
    e.preventDefault();
    if (!logForm.problem_title.trim()) return;
    setLogging(true);
    setLogSuccess(null);
    try {
      await logLeetCodeProblem({
        problem_title: logForm.problem_title.trim(),
        difficulty: logForm.difficulty,
        topic: logForm.topic,
        notes: logForm.notes.trim() || undefined,
      });
      setLogSuccess(`Logged "${logForm.problem_title}" successfully! Streak updated & Admin notified.`);
      setLogForm({ problem_title: "", difficulty: "Easy", topic: "Arrays", notes: "" });
      setShowLogModal(false);
      await fetchData();
    } catch (err) {
      alert("Failed to log problem. Please try again.");
    } finally {
      setLogging(false);
    }
  }

  function openLogForRec(rec: LeetCodeRecommendation) {
    setLogForm({
      problem_title: rec.title,
      difficulty: rec.difficulty,
      topic: rec.topic,
      notes: "",
    });
    setShowLogModal(true);
  }

  return (
    <main style={{ maxWidth: 1040, margin: "0 auto", padding: "40px 24px" }}>
      {/* Header Banner */}
      <div
        className="card"
        style={{
          padding: 28,
          background: "linear-gradient(135deg, #1f5c4a 0%, #0f382c 100%)",
          color: "#fff",
          borderRadius: 16,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 20,
        }}
      >
        <div>
          <div style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: "0.08em", opacity: 0.85, fontWeight: 700 }}>
            PLACEMENT PREPARATION
          </div>
          <h1 style={{ fontSize: 32, margin: "6px 0 8px 0", color: "#ffffff" }}>
            LeetCode Daily Practice Hub
          </h1>
          <p style={{ margin: 0, opacity: 0.9, fontSize: 14.5, maxWidth: 580 }}>
            Solve at least <strong>1 question daily</strong> to build problem-solving consistency, keep your streak alive, and notify your placement team!
          </p>
        </div>

        <button
          onClick={() => setShowLogModal(true)}
          className="btn"
          style={{
            background: "#f59e0b",
            color: "#000",
            fontWeight: 700,
            fontSize: 14,
            padding: "12px 22px",
            borderRadius: 10,
            border: "none",
            cursor: "pointer",
            boxShadow: "0 4px 12px rgba(245,158,11,0.3)",
          }}
        >
          + Log Solved Problem Today
        </button>
      </div>

      {logSuccess && (
        <div
          style={{
            marginTop: 16,
            padding: 14,
            borderRadius: 10,
            background: "rgba(31,92,74,0.12)",
            border: "1px solid var(--primary)",
            color: "var(--primary)",
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          ✓ {logSuccess}
        </div>
      )}

      {/* Stats Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: 16, marginTop: 24 }}>
        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase" }}>
            Daily Status
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, marginTop: 8, color: profile?.solved_today ? "var(--primary)" : "#d97706" }}>
            {profile?.solved_today ? "✅ Completed Today" : "⏳ 0 / 1 Solved Today"}
          </div>
          <p style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
            {profile?.solved_today ? "Great work! Streak preserved." : "Solve at least 1 problem to keep your streak!"}
          </p>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase" }}>
            Current Streak
          </div>
          <div style={{ fontSize: 26, fontWeight: 800, marginTop: 8, color: "#d97706" }}>
            🔥 {profile?.streak || 0} Days
          </div>
          <p style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
            Consecutive daily solved target
          </p>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase" }}>
            Total Questions Solved
          </div>
          <div style={{ fontSize: 26, fontWeight: 800, marginTop: 8, color: "var(--ink)" }}>
            ⚡ {profile?.total_solved || 0}
          </div>
          <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4, display: "flex", gap: 10 }}>
            <span style={{ color: "#16a34a" }}>🟢 {profile?.easy_solved || 0} E</span>
            <span style={{ color: "#d97706" }}>🟡 {profile?.medium_solved || 0} M</span>
            <span style={{ color: "#dc2626" }}>🔴 {profile?.hard_solved || 0} H</span>
          </div>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase" }}>
            LeetCode Handle
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, marginTop: 8, color: "var(--ink)" }}>
            {profile?.username ? `@${profile.username}` : "Not Connected"}
          </div>
          <p style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
            {profile?.username ? "Linked in Profile" : "Set in Profile settings"}
          </p>
        </div>
      </div>

      {/* Recommended LeetCode Problems Section */}
      <div style={{ marginTop: 36 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h2 style={{ fontSize: 22, margin: 0 }}>Recommended Problems For You</h2>
            <p style={{ fontSize: 13.5, color: "var(--ink-soft)", margin: "4px 0 0 0" }}>
              Tailored according to your level (Beginner, Intermediate, Advanced) and key placement topics.
            </p>
          </div>

          {/* Level & Topic Filters */}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)", fontSize: 13, background: "var(--surface)" }}
            >
              <option value="All">All Levels</option>
              <option value="Beginner">Beginner (Warmup)</option>
              <option value="Intermediate">Intermediate (Standard)</option>
              <option value="Advanced">Advanced (FAANG / Hard)</option>
            </select>

            <select
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
              style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--line)", fontSize: 13, background: "var(--surface)" }}
            >
              <option value="All">All Topics</option>
              <option value="Arrays">Arrays & Hashing</option>
              <option value="Strings">Strings</option>
              <option value="Two Pointers">Two Pointers</option>
              <option value="Trees">Trees & BFS</option>
              <option value="Dynamic Programming">Dynamic Programming</option>
              <option value="Graphs">Graphs</option>
            </select>
          </div>
        </div>

        {/* Problem Cards List */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(310px, 1fr))", gap: 18, marginTop: 20 }}>
          {recommendations.map((rec) => (
            <div key={rec.id} className="card" style={{ padding: 20, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      padding: "3px 8px",
                      borderRadius: 6,
                      background:
                        rec.difficulty === "Easy"
                          ? "rgba(22,163,74,0.12)"
                          : rec.difficulty === "Medium"
                          ? "rgba(217,119,6,0.12)"
                          : "rgba(220,38,38,0.12)",
                      color:
                        rec.difficulty === "Easy"
                          ? "#16a34a"
                          : rec.difficulty === "Medium"
                          ? "#d97706"
                          : "#dc2626",
                    }}
                  >
                    {rec.difficulty} • {rec.level}
                  </span>
                  <span className="mono" style={{ fontSize: 11, color: "var(--ink-soft)" }}>
                    #{rec.id}
                  </span>
                </div>

                <h3 style={{ fontSize: 16.5, margin: "6px 0 8px 0", color: "var(--ink)" }}>{rec.title}</h3>
                <p style={{ fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.4, margin: "0 0 12px 0" }}>
                  {rec.description}
                </p>

                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
                  <span style={{ fontSize: 11, padding: "2px 7px", borderRadius: 4, background: "rgba(0,0,0,0.05)", color: "var(--ink-soft)" }}>
                    {rec.topic}
                  </span>
                  {rec.tags.map((t, idx) => (
                    <span key={idx} style={{ fontSize: 11, padding: "2px 7px", borderRadius: 4, background: "rgba(0,0,0,0.04)", color: "var(--ink-soft)" }}>
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ display: "flex", gap: 10, borderTop: "1px solid var(--line)", paddingTop: 14 }}>
                <a
                  href={rec.leetcode_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary"
                  style={{ flex: 1, textAlign: "center", justifyContent: "center", fontSize: 12.5, textDecoration: "none" }}
                >
                  Solve on LeetCode ↗
                </a>
                <button
                  onClick={() => openLogForRec(rec)}
                  className="btn btn-primary"
                  style={{ fontSize: 12.5, padding: "6px 12px" }}
                >
                  Mark Solved
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity Log */}
      {profile?.recent_logs && profile.recent_logs.length > 0 && (
        <div style={{ marginTop: 40 }}>
          <h2 style={{ fontSize: 20, marginBottom: 14 }}>Your Recent Solved Questions</h2>
          <div className="card" style={{ padding: 0, overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13.5 }}>
              <thead>
                <tr style={{ background: "rgba(0,0,0,0.02)", borderBottom: "1px solid var(--line)", textAlign: "left" }}>
                  <th style={{ padding: "12px 16px" }}>Problem</th>
                  <th style={{ padding: "12px 16px" }}>Difficulty</th>
                  <th style={{ padding: "12px 16px" }}>Topic</th>
                  <th style={{ padding: "12px 16px" }}>Solved At</th>
                </tr>
              </thead>
              <tbody>
                {profile.recent_logs.map((log: LeetCodeLogItem) => (
                  <tr key={log.id} style={{ borderBottom: "1px solid var(--line)" }}>
                    <td style={{ padding: "12px 16px", fontWeight: 600 }}>{log.problem_title}</td>
                    <td style={{ padding: "12px 16px" }}>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          padding: "2px 7px",
                          borderRadius: 4,
                          background:
                            log.difficulty === "Easy"
                              ? "rgba(22,163,74,0.12)"
                              : log.difficulty === "Medium"
                              ? "rgba(217,119,6,0.12)"
                              : "rgba(220,38,38,0.12)",
                          color:
                            log.difficulty === "Easy"
                              ? "#16a34a"
                              : log.difficulty === "Medium"
                              ? "#d97706"
                              : "#dc2626",
                        }}
                      >
                        {log.difficulty}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px", color: "var(--ink-soft)" }}>{log.topic || "General"}</td>
                    <td style={{ padding: "12px 16px", color: "var(--ink-soft)" }}>
                      {new Date(log.solved_at).toLocaleDateString()} {new Date(log.solved_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Log Problem Modal */}
      {showLogModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: 16,
          }}
        >
          <div className="card" style={{ width: "100%", maxWidth: 460, padding: 28, background: "#fff" }}>
            <h3 style={{ fontSize: 20, margin: "0 0 16px 0" }}>Log Solved Question</h3>
            <form onSubmit={handleLogProblem}>
              <label style={{ fontSize: 12.5, fontWeight: 700, display: "block", marginBottom: 6 }}>
                Problem Title *
              </label>
              <input
                required
                value={logForm.problem_title}
                onChange={(e) => setLogForm({ ...logForm, problem_title: e.target.value })}
                placeholder="e.g. 3Sum or Two Sum"
                style={{ width: "100%", marginBottom: 14 }}
              />

              <div style={{ display: "flex", gap: 12, marginBottom: 14 }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 12.5, fontWeight: 700, display: "block", marginBottom: 6 }}>
                    Difficulty
                  </label>
                  <select
                    value={logForm.difficulty}
                    onChange={(e) => setLogForm({ ...logForm, difficulty: e.target.value })}
                    style={{ width: "100%", padding: "9px", borderRadius: 8, border: "1px solid var(--line)" }}
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 12.5, fontWeight: 700, display: "block", marginBottom: 6 }}>
                    Topic
                  </label>
                  <input
                    value={logForm.topic}
                    onChange={(e) => setLogForm({ ...logForm, topic: e.target.value })}
                    placeholder="e.g. Arrays, Trees, DP"
                    style={{ width: "100%" }}
                  />
                </div>
              </div>

              <label style={{ fontSize: 12.5, fontWeight: 700, display: "block", marginBottom: 6 }}>
                Optional Notes
              </label>
              <textarea
                value={logForm.notes}
                onChange={(e) => setLogForm({ ...logForm, notes: e.target.value })}
                placeholder="Key insights, time complexity, pattern used..."
                rows={3}
                style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid var(--line)", marginBottom: 20 }}
              />

              <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
                <button
                  type="button"
                  onClick={() => setShowLogModal(false)}
                  className="btn btn-secondary"
                  style={{ fontSize: 13 }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={logging}
                  className="btn btn-primary"
                  style={{ fontSize: 13 }}
                >
                  {logging ? "Logging..." : "Log & Maintain Streak"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}

export default function LeetCodePage() {
  return (
    <RequireAuth>
      <LeetCodePageContent />
    </RequireAuth>
  );
}
