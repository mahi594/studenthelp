"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "../../lib/api";

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailContent />
    </Suspense>
  );
}

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [status, setStatus] = useState<"checking" | "success" | "error">("checking");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("Missing verification token.");
      return;
    }
    verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((e) => {
        setStatus("error");
        setError(e?.response?.data?.detail || "That verification link is invalid or expired.");
      });
  }, [token]);

  return (
    <main style={{ maxWidth: 420, margin: "0 auto", padding: "100px 24px", textAlign: "center" }}>
      <div className="card" style={{ padding: 32 }}>
        {status === "checking" && (
          <p style={{ color: "var(--ink-soft)" }}>Verifying your email...</p>
        )}
        {status === "success" && (
          <>
            <h1 style={{ fontSize: 24 }}>Email verified</h1>
            <p style={{ color: "var(--ink-soft)", marginTop: 12 }}>
              You're all set. Head back to your dashboard.
            </p>
            <Link href="/dashboard" className="btn btn-primary" style={{ textDecoration: "none", display: "inline-block", marginTop: 20 }}>
              Go to dashboard
            </Link>
          </>
        )}
        {status === "error" && (
          <>
            <h1 style={{ fontSize: 24, color: "var(--danger)" }}>Verification failed</h1>
            <p style={{ color: "var(--ink-soft)", marginTop: 12 }}>{error}</p>
            <Link href="/profile" style={{ marginTop: 20, display: "inline-block" }}>
              Go to profile to request a new link
            </Link>
          </>
        )}
      </div>
    </main>
  );
}
