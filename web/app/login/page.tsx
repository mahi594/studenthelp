"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { login } from "../../lib/api";
import { useAuth } from "../../lib/auth-context";

export default function LoginPage() {
  // useSearchParams() opts this subtree out of static rendering unless it's
  // wrapped in Suspense - without this, `next build` fails on this page.
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refresh } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    setError(null);
    setLoading(true);
    try {
      const res = await login(email, password);
      if (res.must_change_password) {
        // Restricted token only - don't call refresh()/getCurrentUser() yet,
        // it would 401 on this token and log the user back out. The
        // change-password page itself calls refresh() once a full token
        // comes back from POST /auth/change-password.
        router.push("/change-password");
        return;
      }
      await refresh();
      router.push(searchParams.get("next") || "/dashboard");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Login failed. Check your email and password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 400, margin: "0 auto", padding: "80px 24px" }}>
      <h1 style={{ fontSize: 28 }}>Log in</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8, fontSize: 14 }}>
        Welcome back — let's see where you stand.
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

        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 16, marginBottom: 6 }}>
          Password
        </label>
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          type="password"
          placeholder="••••••••"
          style={{ width: "100%" }}
        />

        {error && <p style={{ color: "var(--danger)", fontSize: 13, marginTop: 14 }}>{error}</p>}

        <button onClick={handleSubmit} disabled={loading} className="btn btn-primary" style={{ width: "100%", marginTop: 20 }}>
          {loading ? "Logging in..." : "Log in"}
        </button>
      </div>

      <p style={{ fontSize: 14, color: "var(--ink-soft)", marginTop: 20, textAlign: "center" }}>
        New here? <Link href="/register">Create an account</Link>
      </p>
    </main>
  );
}
