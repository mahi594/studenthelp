"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register, login } from "../../lib/api";
import { useAuth } from "../../lib/auth-context";

export default function RegisterPage() {
  const router = useRouter();
  const { refresh } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "", branch: "", grad_year: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit() {
    setError(null);
    setLoading(true);
    try {
      await register({
        name: form.name,
        email: form.email,
        password: form.password,
        branch: form.branch || undefined,
        grad_year: form.grad_year ? Number(form.grad_year) : undefined,
      });
      await login(form.email, form.password);
      await refresh();
      router.push("/dashboard");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Registration failed. Try a different email.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 420, margin: "0 auto", padding: "72px 24px" }}>
      <h1 style={{ fontSize: 28 }}>Create your account</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8, fontSize: 14 }}>
        Takes a minute — then we'll start tracking your readiness.
      </p>

      <div className="card" style={{ padding: 28, marginTop: 24, display: "flex", flexDirection: "column", gap: 14 }}>
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>Name</label>
          <input value={form.name} onChange={(e) => update("name", e.target.value)} style={{ width: "100%" }} />
        </div>
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>Email</label>
          <input value={form.email} onChange={(e) => update("email", e.target.value)} type="email" style={{ width: "100%" }} />
        </div>
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>Password</label>
          <input value={form.password} onChange={(e) => update("password", e.target.value)} type="password" style={{ width: "100%" }} />
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>Branch</label>
            <input value={form.branch} onChange={(e) => update("branch", e.target.value)} placeholder="CSE" style={{ width: "100%" }} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>Grad year</label>
            <input value={form.grad_year} onChange={(e) => update("grad_year", e.target.value)} placeholder="2027" style={{ width: "100%" }} />
          </div>
        </div>

        {error && <p style={{ color: "var(--danger)", fontSize: 13 }}>{error}</p>}

        <button onClick={handleSubmit} disabled={loading} className="btn btn-primary" style={{ width: "100%", marginTop: 6 }}>
          {loading ? "Creating account..." : "Create account"}
        </button>
      </div>

      <p style={{ fontSize: 14, color: "var(--ink-soft)", marginTop: 20, textAlign: "center" }}>
        Already have an account? <Link href="/login">Log in</Link>
      </p>
    </main>
  );
}
