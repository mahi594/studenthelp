"use client";

import RequireAuth from "../../components/RequireAuth";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { listCompanies, listMyApplications, markApplication } from "../../lib/api";

type Company = {
  id: string;
  name: string;
  roles: string[];
  apply_url?: string | null;
};

type Application = {
  id: string;
  company_id: string;
  status: string;
  applied_at: string | null;
  updated_at: string;
};

const STATUS_OPTIONS = [
  { value: "applied", label: "Applied" },
  { value: "interviewing", label: "Interviewing" },
  { value: "offered", label: "Offered" },
  { value: "rejected", label: "Rejected" },
];

const STATUS_LABEL: Record<string, string> = {
  applied: "Applied",
  interviewing: "Interviewing",
  offered: "Offered",
  rejected: "Rejected",
  not_applied: "Not applied",
};

function ApplicationsPageContent() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  async function loadAll() {
    setLoading(true);
    try {
      const [companiesData, appsData] = await Promise.all([listCompanies(), listMyApplications()]);
      setCompanies(companiesData);
      setApplications(appsData);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  const companyById = useMemo(() => {
    const map: Record<string, Company> = {};
    companies.forEach((c) => (map[c.id] = c));
    return map;
  }, [companies]);

  // Only companies with an actual application row (status != not_applied
  // lives implicitly by just not being marked yet) show up here - this page
  // is "what have I applied to", not the full company browser.
  const rows = applications
    .filter((a) => companyById[a.company_id])
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

  const counts = rows.reduce<Record<string, number>>((acc, a) => {
    acc[a.status] = (acc[a.status] || 0) + 1;
    return acc;
  }, {});

  async function handleStatusChange(companyId: string, status: string) {
    setUpdatingId(companyId);
    setApplications((prev) =>
      prev.map((a) => (a.company_id === companyId ? { ...a, status } : a))
    );
    try {
      await markApplication(companyId, status);
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <main style={{ maxWidth: 800, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>My applications</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
        Everything you've applied to, in one place, with the current stage of each.
      </p>

      {!loading && rows.length > 0 && (
        <div style={{ display: "flex", gap: 10, marginTop: 20, flexWrap: "wrap" }}>
          {STATUS_OPTIONS.map((opt) => (
            <span key={opt.value} className={`badge badge-${opt.value}`}>
              {counts[opt.value] || 0} {opt.label}
            </span>
          ))}
        </div>
      )}

      {loading && <p style={{ color: "var(--ink-soft)", marginTop: 24 }}>Loading...</p>}

      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 24 }}>
        {rows.map((application) => {
          const company = companyById[application.company_id];
          return (
            <div key={application.id} className="card" style={{ padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
                <div>
                  <h3 style={{ fontSize: 20 }}>{company.name}</h3>
                  <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    {company.roles?.map((role) => (
                      <span key={role} className="badge badge-not-applied">
                        {role}
                      </span>
                    ))}
                  </div>
                  {application.applied_at && (
                    <p className="mono" style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 10 }}>
                      Applied {new Date(application.applied_at).toLocaleDateString()}
                    </p>
                  )}
                </div>

                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 10 }}>
                  <span className={`badge badge-${application.status}`}>
                    {STATUS_LABEL[application.status] || application.status}
                  </span>
                  <select
                    value={application.status}
                    disabled={updatingId === company.id}
                    onChange={(e) => handleStatusChange(company.id, e.target.value)}
                    style={{ fontSize: 13, padding: "6px 10px" }}
                  >
                    {STATUS_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {company.apply_url && (
                <a
                  href={company.apply_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ fontSize: 13, marginTop: 16, display: "inline-block" }}
                >
                  View listing →
                </a>
              )}
            </div>
          );
        })}

        {!loading && rows.length === 0 && (
          <div className="card" style={{ padding: 32, textAlign: "center" }}>
            <p style={{ color: "var(--ink-soft)" }}>You haven't applied anywhere yet.</p>
            <Link href="/companies" className="btn btn-primary" style={{ textDecoration: "none", marginTop: 16, display: "inline-block" }}>
              Browse companies
            </Link>
          </div>
        )}
      </div>
    </main>
  );
}

export default function ApplicationsPage() {
  return (
    <RequireAuth>
      <ApplicationsPageContent />
    </RequireAuth>
  );
}
