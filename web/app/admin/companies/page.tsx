"use client";
import RequireAuth from "../../../components/RequireAuth";

import { useEffect, useState } from "react";
import { api, createCompany, addRound, deleteRound } from "../../../lib/api";

const ROUND_TYPES = ["OA", "Technical", "System Design", "HR", "Managerial"];

function RoundForm({ companyId, onAdded }: { companyId: string; onAdded: () => void }) {
  const [roundType, setRoundType] = useState(ROUND_TYPES[0]);
  const [subjects, setSubjects] = useState("");
  const [difficulty, setDifficulty] = useState("Medium");
  const [notes, setNotes] = useState("");
  const [orderIndex, setOrderIndex] = useState(1);
  const [saving, setSaving] = useState(false);

  async function handleAdd() {
    setSaving(true);
    try {
      await addRound(companyId, {
        order_index: orderIndex,
        round_type: roundType,
        subjects_tested: subjects.split(",").map((s) => s.trim()).filter(Boolean),
        difficulty,
        notes: notes || undefined,
      });
      setSubjects("");
      setNotes("");
      setOrderIndex((n) => n + 1);
      onAdded();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginTop: 12 }}>
      <input
        type="number"
        value={orderIndex}
        onChange={(e) => setOrderIndex(Number(e.target.value))}
        style={{ width: 60 }}
        title="Order"
      />
      <select value={roundType} onChange={(e) => setRoundType(e.target.value)}>
        {ROUND_TYPES.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>
      <input
        placeholder="Subjects (comma-separated, e.g. DSA, OS)"
        value={subjects}
        onChange={(e) => setSubjects(e.target.value)}
        style={{ flex: 1, minWidth: 200 }}
      />
      <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
        <option>Easy</option>
        <option>Medium</option>
        <option>Hard</option>
      </select>
      <input
        placeholder="Notes (optional)"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        style={{ flex: 1, minWidth: 160 }}
      />
      <button onClick={handleAdd} disabled={saving} className="btn btn-secondary" style={{ fontSize: 13 }}>
        {saving ? "Adding..." : "+ Round"}
      </button>
    </div>
  );
}

function AdminCompaniesPageContent() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    roles: "",
    tags: "",
    min_cgpa: "",
    preferred_branches: "",
    resume_keywords: "",
    apply_url: "",
  });
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadCompanies() {
    const res = await api.get("/companies/");
    setCompanies(res.data);
  }

  async function handleDeleteRound(companyId: string, roundId: string) {
    await deleteRound(companyId, roundId);
    loadCompanies();
  }

  useEffect(() => {
    loadCompanies();
  }, []);

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  const toList = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

  async function handleSubmit() {
    setStatus(null);
    setError(null);
    try {
      await createCompany({
        name: form.name,
        roles: toList(form.roles),
        tags: toList(form.tags),
        min_cgpa: form.min_cgpa || null,
        preferred_branches: toList(form.preferred_branches),
        resume_keywords: toList(form.resume_keywords),
        apply_url: form.apply_url || null,
      });
      setStatus(`Added "${form.name}".`);
      setForm({ name: "", roles: "", tags: "", min_cgpa: "", preferred_branches: "", resume_keywords: "", apply_url: "" });
      loadCompanies();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to add company. Are you logged in as an admin?");
    }
  }

  const fields: [string, string, string][] = [
    ["name", "Company name", "e.g. Example Corp"],
    ["roles", "Roles (comma-separated)", "e.g. SDE-1, Analyst"],
    ["tags", "Tags (comma-separated)", "e.g. product-based, core"],
    ["min_cgpa", "Minimum CGPA", "e.g. 7.0"],
    ["preferred_branches", "Preferred branches (comma-separated)", "e.g. CSE, IT, ECE"],
    ["resume_keywords", "Resume keywords (comma-separated)", "e.g. DSA, React, SQL"],
    ["apply_url", "Apply link", "https://company.com/careers/apply"],
  ];

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Add a company</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
        Curated by admins only — this is the trusted data everything else in the app builds on.
      </p>

      <div className="card" style={{ padding: 28, marginTop: 24 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {fields.map(([key, label, placeholder]) => (
            <div key={key}>
              <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
                {label}
              </label>
              <input
                value={(form as any)[key]}
                onChange={(e) => update(key, e.target.value)}
                placeholder={placeholder}
                style={{ width: "100%" }}
              />
            </div>
          ))}
        </div>

        {error && <p style={{ color: "var(--danger)", fontSize: 14, marginTop: 16 }}>{error}</p>}
        {status && <p style={{ color: "var(--primary)", fontSize: 14, marginTop: 16 }}>{status}</p>}

        <button onClick={handleSubmit} className="btn btn-primary" style={{ marginTop: 20 }}>
          Add company
        </button>
      </div>

      <h2 style={{ fontSize: 22, marginTop: 48 }}>Existing companies ({companies.length})</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 16 }}>
        {companies.map((c) => {
          const isExpanded = expandedId === c.id;
          return (
            <div key={c.id} className="card" style={{ padding: 16 }}>
              <div
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
                onClick={() => setExpandedId(isExpanded ? null : c.id)}
              >
                <div>
                  <div style={{ fontWeight: 600 }}>{c.name}</div>
                  <div style={{ fontSize: 13, color: "var(--ink-soft)" }}>{c.roles?.join(", ")}</div>
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span className="badge badge-not-applied">{c.rounds?.length || 0} rounds</span>
                  {c.apply_url ? (
                    <span className="badge badge-applied">Has apply link</span>
                  ) : (
                    <span className="badge badge-not-applied">No apply link</span>
                  )}
                </div>
              </div>

              {isExpanded && (
                <div style={{ marginTop: 16, borderTop: "1px solid var(--line)", paddingTop: 16 }}>
                  {c.rounds?.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {c.rounds
                        .slice()
                        .sort((a: any, b: any) => a.order_index - b.order_index)
                        .map((r: any) => (
                          <div
                            key={r.id}
                            style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 13 }}
                          >
                            <span>
                              <strong>#{r.order_index} {r.round_type}</strong>
                              {r.subjects_tested?.length > 0 && ` — ${r.subjects_tested.join(", ")}`}
                              {r.difficulty && ` (${r.difficulty})`}
                            </span>
                            <button
                              onClick={() => handleDeleteRound(c.id, r.id)}
                              className="btn btn-secondary"
                              style={{ fontSize: 12, padding: "4px 10px" }}
                            >
                              Remove
                            </button>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <p style={{ fontSize: 13, color: "var(--ink-soft)" }}>No rounds curated yet.</p>
                  )}
                  <RoundForm companyId={c.id} onAdded={loadCompanies} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </main>
  );
}

export default function AdminCompaniesPage() {
  return (
    <RequireAuth role="admin">
      <AdminCompaniesPageContent />
    </RequireAuth>
  );
}
