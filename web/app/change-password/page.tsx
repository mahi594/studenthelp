"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { changePassword } from "../../lib/api";
import { useAuth } from "../../lib/auth-context";
import { isLoggedIn } from "../../lib/api";

export default function ChangePasswordPage() {
  const router = useRouter();
  const { refresh } = useAuth();

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit() {
    setError(null);
    if (password !== confirm) {
      setError("Passwords don't match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await changePassword(password);
      setDone(true);
      // The token in localStorage is now a full access token (see
      // changePassword() in lib/api.ts) - refresh the auth context with it
      // before routing in, so /dashboard doesn't bounce back to /login.
      await refresh();
      setTimeout(() => router.push("/dashboard"), 1000);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Couldn't update your password. Try logging in again.");
    } finally {
      setLoading(false);
    }
  }

  if (typeof window !== "undefined" && !isLoggedIn()) {
    return (
      <main style={{ maxWidth: 400, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
        <p style={{ color: "var(--ink-soft)" }}>You need to log in first.</p>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 400, margin: "0 auto", padding: "80px 24px" }}>
      <h1 style={{ fontSize: 28 }}>Set your password</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8, fontSize: 14 }}>
        Your account was created with a temporary password. Set your own before continuing.
      </p>

      <div className="card" style={{ padding: 28, marginTop: 24 }}>
        {done ? (
          <p style={{ color: "var(--primary)", fontSize: 14 }}>Password updated. Taking you to your dashboard...</p>
        ) : (
          <>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
              New password
            </label>
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" style={{ width: "100%" }} />

            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 16, marginBottom: 6 }}>
              Confirm password
            </label>
            <input
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              type="password"
              style={{ width: "100%" }}
            />

            {error && <p style={{ color: "var(--danger)", fontSize: 13, marginTop: 14 }}>{error}</p>}

            <button onClick={handleSubmit} disabled={loading} className="btn btn-primary" style={{ width: "100%", marginTop: 20 }}>
              {loading ? "Saving..." : "Set password & continue"}
            </button>
          </>
        )}
      </div>
    </main>
  );
}
