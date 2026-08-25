"use client";

import { useEffect, useState } from "react";
import { api, markApplication, listMyApplications } from "../../lib/api";

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [applications, setApplications] = useState<Record<string, string>>({});
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadAll() {
    setLoading(true);
    try {
      const [companiesRes, appsRes] = await Promise.all([
        api.get("/companies/"),
        listMyApplications().catch(() => []),
      ]);
      setCompanies(companiesRes.data);
      const map: Record<string, string> = {};
      appsRes.forEach((a: any) => {
        map[a.company_id] = a.status;
      });
      setApplications(map);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function handleMarkApplied(companyId: string) {
    setApplications((prev) => ({ ...prev, [companyId]: "applied" }));
    await markApplication(companyId, "applied");
  }

  const query = search.trim().toLowerCase();
  const filtered = companies.filter((c) => {
    if (!query) return true;
    const nameMatch = c.name?.toLowerCase().includes(query);
    const rolesMatch = c.roles?.some((r: string) => r.toLowerCase().includes(query));
    const tagsMatch = c.tags?.some((t: string) => t.toLowerCase().includes(query));
    const branchMatch = c.preferred_branches?.some((b: string) => b.toLowerCase().includes(query));
    return nameMatch || rolesMatch || tagsMatch || branchMatch;
  });

  return (
    <main style={{ maxWidth: 840, margin: "0 auto", padding: "40px 24px" }}>
      <h1 style={{ fontSize: 32, fontWeight: 800 }}>Target Companies</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 6, fontSize: 15 }}>
        Curated institutional company profiles, hiring rounds, and verified recruitment requirements.
      </p>

      <input
        placeholder="Search by company name, role, or tag..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ width: "100%", marginTop: 20, padding: "10px 14px", borderRadius: 8, border: "1px solid var(--line)" }}
      />

      {loading && <p style={{ color: "var(--ink-soft)", marginTop: 24 }}>Loading company data...</p>}

      <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 24 }}>
        {filtered.map((company) => {
          const status = applications[company.id] || "not_applied";
          const isApplied = status !== "not_applied";
          
          let badgeText = "UNVERIFIED";
          let badgeBg = "rgba(107,114,128,0.1)";
          let badgeColor = "#4b5563";

          if (company.is_curated_verified) {
            badgeText = "✓ VERIFIED BY PLACEMENT CELL";
            badgeBg = "rgba(31,92,74,0.1)";
            badgeColor = "var(--primary)";
          } else if (company.source_type === "alumni_report") {
            badgeText = "ALUMNI REPORTED";
            badgeBg = "rgba(217,119,6,0.1)";
            badgeColor = "#b45309";
          } else if (company.source_type === "ai_recommended") {
            badgeText = "AI RECOMMENDED";
            badgeBg = "rgba(59,130,246,0.1)";
            badgeColor = "#2563eb";
          }

          return (
            <div key={company.id} className="card" style={{ padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <h3 style={{ fontSize: 20, fontWeight: 700 }}>{company.name}</h3>
                    <span className="mono" style={{ fontSize: 11, background: badgeBg, color: badgeColor, padding: "2px 8px", borderRadius: 12, fontWeight: 700 }}>
                      {badgeText}
                    </span>
                  </div>

                  <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
                    {company.roles?.map((role: string) => (
                      <span key={role} className="badge badge-not-applied">{role}</span>
                    ))}
                  </div>
                </div>


                <span className={`badge ${isApplied ? "badge-applied" : "badge-not-applied"}`}>
                  {isApplied ? "Applied" : "Not applied"}
                </span>
              </div>

              {company.min_cgpa && (
                <div style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 12, display: "flex", gap: 16, flexWrap: "wrap" }}>
                  <span>Min CGPA: <strong style={{ color: "var(--ink)" }}>{company.min_cgpa}</strong></span>
                  {company.preferred_branches?.length > 0 && (
                    <span>Branches: <strong style={{ color: "var(--ink)" }}>{company.preferred_branches.join(", ")}</strong></span>
                  )}
                  {company.confidence && (
                    <span>Confidence: <strong style={{ color: "var(--ink)" }}>{company.confidence}</strong></span>
                  )}
                </div>
              )}

              <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
                {company.apply_url && (
                  <a
                    href={company.apply_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary"
                    style={{ textDecoration: "none", fontSize: 13 }}
                  >
                    Apply now →
                  </a>
                )}
                {!isApplied && (
                  <button
                    onClick={() => handleMarkApplied(company.id)}
                    className="btn btn-secondary"
                    style={{ fontSize: 13 }}
                  >
                    Mark as applied
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {!loading && filtered.length === 0 && (
          <p style={{ color: "var(--ink-soft)" }}>No target companies match your search query.</p>
        )}
      </div>
    </main>
  );
}
