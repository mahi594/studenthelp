"use client";

import RequireAuth from "../../components/RequireAuth";

import { useEffect, useState } from "react";
import Link from "next/link";
import { updateProfile, resendVerification, syncLeetCodeProfile } from "../../lib/api";
import { useAuth } from "../../lib/auth-context";

function ProfilePageContent() {
  const { user, refresh } = useAuth();
  const [verifySending, setVerifySending] = useState(false);
  const [verifyMessage, setVerifyMessage] = useState<string | null>(null);
  const [devVerifyToken, setDevVerifyToken] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    branch: "",
    grad_year: "",
    cgpa: "",
    college_name: "",
    leetcode_username: "",
    leetcode_daily_goal: "1",
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    setForm({
      name: user.name || "",
      branch: user.branch || "",
      grad_year: user.grad_year ? String(user.grad_year) : "",
      cgpa: user.cgpa || "",
      college_name: user.college_name || "",
      leetcode_username: user.leetcode_username || "",
      leetcode_daily_goal: String(user.leetcode_daily_goal || 1),
    });
  }, [user]);

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setSaved(false);
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await updateProfile({
        name: form.name,
        branch: form.branch || undefined,
        grad_year: form.grad_year ? Number(form.grad_year) : undefined,
        cgpa: form.cgpa || undefined,
        college_name: form.college_name || undefined,
        leetcode_username: form.leetcode_username || undefined,
        leetcode_daily_goal: form.leetcode_daily_goal ? Number(form.leetcode_daily_goal) : undefined,
      });
      await refresh();
      setSaved(true);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Couldn't save your changes. Try again.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSyncLeetCode() {
    setSyncing(true);
    setSyncMsg(null);
    try {
      await syncLeetCodeProfile({
        leetcode_username: form.leetcode_username,
        leetcode_daily_goal: Number(form.leetcode_daily_goal || 1),
      });
      await refresh();
      setSyncMsg("LeetCode profile synced successfully!");
    } catch (e: any) {
      setSyncMsg("Could not sync LeetCode stats automatically. Saved handle.");
    } finally {
      setSyncing(false);
    }
  }

  async function handleResendVerification() {
    setVerifySending(true);
    setVerifyMessage(null);
    setDevVerifyToken(null);
    try {
      const res = await resendVerification();
      setVerifyMessage(res.message);
      if (res.dev_verify_token) setDevVerifyToken(res.dev_verify_token);
    } finally {
      setVerifySending(false);
    }
  }

  return (
    <main style={{ maxWidth: 560, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Profile</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
        Keep your details and LeetCode handle updated for daily practice and TPO dashboard tracking.
      </p>

      {user && !user.email_verified && (
        <div className="card" style={{ padding: 18, marginTop: 20, borderColor: "var(--accent)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
            <span style={{ fontSize: 14 }}>Your email isn't verified yet.</span>
            <button onClick={handleResendVerification} disabled={verifySending} className="btn btn-secondary" style={{ fontSize: 13 }}>
              {verifySending ? "Sending..." : "Resend verification email"}
            </button>
          </div>
          {verifyMessage && <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 10 }}>{verifyMessage}</p>}
          {devVerifyToken && (
            <Link href={`/verify-email?token=${devVerifyToken}`} style={{ fontSize: 13, marginTop: 6, display: "inline-block" }}>
              Dev mode: click to verify now →
            </Link>
          )}
        </div>
      )}

      {/* LeetCode Practice & Daily Goal Card */}
      <div className="card" style={{ padding: 24, marginTop: 24, background: "linear-gradient(135deg, rgba(245,158,11,0.06), rgba(239,68,68,0.03))", border: "1px solid rgba(245,158,11,0.3)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ fontSize: 18, margin: 0, color: "#b45309", display: "flex", alignItems: "center", gap: 8 }}>
            <span>🔥 LeetCode Daily Practice Goal</span>
          </h3>
          <Link href="/leetcode" className="btn btn-primary" style={{ fontSize: 12, padding: "5px 12px", textDecoration: "none" }}>
            Open LeetCode Hub →
          </Link>
        </div>
        <p style={{ fontSize: 13, color: "var(--ink-soft)", marginBottom: 16 }}>
          Connect your LeetCode profile to practice daily. Target at least 1 question every day for placement readiness!
        </p>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <div style={{ flex: 2, minWidth: 180 }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", display: "block", marginBottom: 4 }}>
              LeetCode Username
            </label>
            <input
              value={form.leetcode_username}
              onChange={(e) => update("leetcode_username", e.target.value)}
              placeholder="e.g. tourist or neetcode"
              style={{ width: "100%" }}
            />
          </div>
          <div style={{ flex: 1, minWidth: 120 }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-soft)", display: "block", marginBottom: 4 }}>
              Daily Goal
            </label>
            <select
              value={form.leetcode_daily_goal}
              onChange={(e) => update("leetcode_daily_goal", e.target.value)}
              style={{ width: "100%", padding: "10px", borderRadius: 8, border: "1px solid var(--line)" }}
            >
              <option value="1">1 Question / day</option>
              <option value="2">2 Questions / day</option>
              <option value="3">3 Questions / day</option>
            </select>
          </div>
        </div>

        {user?.leetcode_username && (
          <div style={{ display: "flex", gap: 16, marginTop: 14, background: "var(--surface)", padding: 12, borderRadius: 8, fontSize: 13, flexWrap: "wrap" }}>
            <div><strong>Streak:</strong> 🔥 {user.leetcode_streak || 0} days</div>
            <div><strong>Total Solved:</strong> ⚡ {user.leetcode_total_solved || 0}</div>
            <div><strong>Easy:</strong> 🟢 {user.leetcode_easy_solved || 0}</div>
            <div><strong>Medium:</strong> 🟡 {user.leetcode_medium_solved || 0}</div>
            <div><strong>Hard:</strong> 🔴 {user.leetcode_hard_solved || 0}</div>
          </div>
        )}

        <div style={{ marginTop: 14, display: "flex", gap: 10, alignItems: "center" }}>
          <button onClick={handleSyncLeetCode} disabled={syncing} className="btn btn-secondary" style={{ fontSize: 12 }}>
            {syncing ? "Syncing..." : "Sync LeetCode Stats"}
          </button>
          {syncMsg && <span style={{ fontSize: 12, color: "var(--primary)" }}>{syncMsg}</span>}
        </div>
      </div>

      <div className="card" style={{ padding: 28, marginTop: 24 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
          Name
        </label>
        <input value={form.name} onChange={(e) => update("name", e.target.value)} style={{ width: "100%" }} />

        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 16, marginBottom: 6 }}>
          Email
        </label>
        <input value={user?.email || ""} disabled style={{ width: "100%", opacity: 0.6 }} />

        <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
              Branch
            </label>
            <input value={form.branch} onChange={(e) => update("branch", e.target.value)} placeholder="CSE" style={{ width: "100%" }} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
              Grad year
            </label>
            <input
              value={form.grad_year}
              onChange={(e) => update("grad_year", e.target.value)}
              placeholder="2027"
              type="number"
              style={{ width: "100%" }}
            />
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
              CGPA
            </label>
            <input value={form.cgpa} onChange={(e) => update("cgpa", e.target.value)} placeholder="8.4" style={{ width: "100%" }} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
              College
            </label>
            <input
              value={form.college_name}
              onChange={(e) => update("college_name", e.target.value)}
              placeholder="Your college name"
              style={{ width: "100%" }}
            />
          </div>
        </div>

        {error && <p style={{ color: "var(--danger)", fontSize: 13, marginTop: 14 }}>{error}</p>}
        {saved && <p style={{ color: "var(--primary)", fontSize: 13, marginTop: 14 }}>Saved.</p>}

        <button onClick={handleSave} disabled={saving} className="btn btn-primary" style={{ width: "100%", marginTop: 20 }}>
          {saving ? "Saving..." : "Save changes"}
        </button>
      </div>

      <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 20 }}>
        Need to change your password? <Link href="/forgot-password">Reset it here</Link>.
      </p>
    </main>
  );
}

export default function ProfilePage() {
  return (
    <RequireAuth>
      <ProfilePageContent />
    </RequireAuth>
  );
}

