"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { resetPassword } from "../../lib/api";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

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
      await resetPassword(token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 1500);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "That reset link is invalid or expired.");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <main style={{ maxWidth: 400, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
        <p style={{ color: "var(--danger)" }}>Missing reset token.</p>
        <Link href="/forgot-password">Request a new reset link</Link>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 400, margin: "0 auto", padding: "80px 24px" }}>
      <h1 style={{ fontSize: 28 }}>Set a new password</h1>

      <div className="card" style={{ padding: 28, marginTop: 24 }}>
        {done ? (
          <p style={{ color: "var(--primary)", fontSize: 14 }}>Password updated. Redirecting to login...</p>
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
              {loading ? "Saving..." : "Update password"}
            </button>
          </>
        )}
      </div>
    </main>
  );
}
