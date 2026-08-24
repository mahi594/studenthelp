"use client";
import RequireAuth from "../../../components/RequireAuth";

import { useState } from "react";
import { createAdmin } from "../../../lib/api";

function CreateAdminPageContent() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"admin" | "tpo_admin">("admin");
  const [collegeName, setCollegeName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ email: string; temp_password: string; email_sent: boolean } | null>(null);

  async function handleCreate() {
    setError(null);
    setResult(null);
    if (!name.trim() || !email.trim()) {
      setError("Name and email are required.");
      return;
    }
    if (role === "tpo_admin" && !collegeName.trim()) {
      setError("College name is required for a TPO account, so their dashboard is scoped correctly.");
      return;
    }
    setLoading(true);
    try {
      const res = await createAdmin({
        name: name.trim(),
        email: email.trim(),
        role,
        college_name: role === "tpo_admin" ? collegeName.trim() : undefined,
      });
      setResult({ email: res.email, temp_password: res.temp_password, email_sent: res.email_sent });
      setName("");
      setEmail("");
      setCollegeName("");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Couldn't create the account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 560, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Create admin account</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
        The new account gets a system-generated temporary password and must set their own before
        they can access anything else.
      </p>

      <div className="card" style={{ padding: 28, marginTop: 24 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
          Name
        </label>
        <input value={name} onChange={(e) => setName(e.target.value)} style={{ width: "100%" }} />

        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 16, marginBottom: 6 }}>
          Email
        </label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" style={{ width: "100%" }} />

        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 16, marginBottom: 6 }}>
          Role
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => setRole("admin")}
            className={role === "admin" ? "btn btn-primary" : "btn btn-secondary"}
            style={{ fontSize: 13 }}
          >
            Content admin
          </button>
          <button
            onClick={() => setRole("tpo_admin")}
            className={role === "tpo_admin" ? "btn btn-primary" : "btn btn-secondary"}
            style={{ fontSize: 13 }}
          >
            TPO admin
          </button>
        </div>

        {role === "tpo_admin" && (
          <>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 16, marginBottom: 6 }}>
              College name (scopes their dashboard)
            </label>
            <input value={collegeName} onChange={(e) => setCollegeName(e.target.value)} style={{ width: "100%" }} />
          </>
        )}

        {error && <p style={{ color: "var(--danger)", fontSize: 14, marginTop: 16 }}>{error}</p>}

        <button onClick={handleCreate} disabled={loading} className="btn btn-primary" style={{ width: "100%", marginTop: 24 }}>
          {loading ? "Creating..." : "Create account"}
        </button>
      </div>

      {result && (
        <div className="card" style={{ padding: 24, marginTop: 20, borderColor: "var(--primary)" }}>
          <h3 style={{ fontSize: 16 }}>Account created</h3>
          <p style={{ fontSize: 14, color: "var(--ink-soft)", marginTop: 8 }}>
            {result.email_sent
              ? "A temporary password has also been emailed to them, but it's shown here once too:"
              : "Email isn't configured, so you'll need to share this with them yourself:"}
          </p>
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 4 }}>
            <span className="mono" style={{ fontSize: 13 }}>Email: {result.email}</span>
            <span className="mono" style={{ fontSize: 13, fontWeight: 700 }}>Temp password: {result.temp_password}</span>
          </div>
          <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 12 }}>
            This password only works once - they'll be forced to set their own on first login and won't
            be able to reach any other page until they do.
          </p>
        </div>
      )}
    </main>
  );
}

export default function CreateAdminPage() {
  return (
    <RequireAuth role="admin">
      <CreateAdminPageContent />
    </RequireAuth>
  );
}
