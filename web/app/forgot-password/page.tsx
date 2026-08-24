"use client";

import { useState } from "react";
import Link from "next/link";
import { forgotPassword } from "../../lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [devToken, setDevToken] = useState<string | null>(null);

  async function handleSubmit() {
    setLoading(true);
    setMessage(null);
    setDevToken(null);
    try {
      const res = await forgotPassword(email);
      setMessage(res.message);
      // dev_reset_token only appears when SMTP isn't configured - see
      // backend app/services/email_service.is_email_configured. Never shown
      // once real email sending is wired up.
      if (res.dev_reset_token) setDevToken(res.dev_reset_token);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 400, margin: "0 auto", padding: "80px 24px" }}>
      <h1 style={{ fontSize: 28 }}>Forgot password</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8, fontSize: 14 }}>
        Enter your email and we'll send you a reset link.
      </p>

      <div className="card" style={{ padding: 28, marginTop: 24 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
          Email
        </label>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          type="email"
          placeholder="you@example.com"
          style={{ width: "100%" }}
        />

        <button onClick={handleSubmit} disabled={loading || !email} className="btn btn-primary" style={{ width: "100%", marginTop: 20 }}>
          {loading ? "Sending..." : "Send reset link"}
        </button>

        {message && <p style={{ color: "var(--ink-soft)", fontSize: 13, marginTop: 14 }}>{message}</p>}

        {devToken && (
          <div style={{ marginTop: 14 }}>
            <p className="mono" style={{ fontSize: 12, color: "var(--ink-soft)" }}>
              Dev mode (no SMTP configured yet):
            </p>
            <Link href={`/reset-password?token=${devToken}`} style={{ fontSize: 13 }}>
              Continue to reset password →
            </Link>
          </div>
        )}
      </div>

      <p style={{ fontSize: 14, color: "var(--ink-soft)", marginTop: 20, textAlign: "center" }}>
        <Link href="/login">Back to login</Link>
      </p>
    </main>
  );
}
