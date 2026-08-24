"use client";
import RequireAuth from "../../components/RequireAuth";

import { useEffect, useState } from "react";
import { browseJobListings, refreshJobListings, JobListingItem } from "../../lib/api";
import { useAuth } from "../../lib/auth-context";

function JobsPageContent() {
  const { isAdmin } = useAuth();
  const [listings, setListings] = useState<JobListingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState("");

  const [keywords, setKeywords] = useState("software engineer");
  const [location, setLocation] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await browseJobListings(roleFilter ? { role: roleFilter } : undefined);
      setListings(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roleFilter]);

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshMessage(null);
    setRefreshError(null);
    try {
      const res = await refreshJobListings({ keywords, location: location || undefined });
      setRefreshMessage(`Fetched ${res.fetched}, added ${res.created} new (${res.skipped_duplicates} already known).`);
      load();
    } catch (e: any) {
      setRefreshError(e?.response?.data?.detail || "Failed to refresh listings - check Adzuna API keys are set.");
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Job listings</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
        Live openings pulled in from Adzuna, refreshed periodically.
      </p>

      {isAdmin && (
        <div className="card" style={{ padding: 20, marginTop: 20 }}>
          <span className="mono" style={{ fontSize: 11, color: "var(--ink-soft)" }}>ADMIN: REFRESH LISTINGS</span>
          <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
            <input value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="Keywords" style={{ flex: 1, minWidth: 160 }} />
            <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Location (optional)" style={{ flex: 1, minWidth: 160 }} />
            <button onClick={handleRefresh} disabled={refreshing} className="btn btn-primary">
              {refreshing ? "Fetching..." : "Refresh from Adzuna"}
            </button>
          </div>
          {refreshMessage && <p style={{ fontSize: 13, color: "var(--primary)", marginTop: 10 }}>{refreshMessage}</p>}
          {refreshError && <p style={{ fontSize: 13, color: "var(--danger)", marginTop: 10 }}>{refreshError}</p>}
        </div>
      )}

      <input
        value={roleFilter}
        onChange={(e) => setRoleFilter(e.target.value)}
        placeholder="Filter by role (e.g. SDE)"
        style={{ width: "100%", marginTop: 24 }}
      />

      {loading && <p style={{ color: "var(--ink-soft)", marginTop: 24 }}>Loading...</p>}

      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 20 }}>
        {listings.map((job) => (
          <div key={job.id} className="card" style={{ padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
              <div>
                <h3 style={{ fontSize: 17 }}>{job.role_title}</h3>
                <p style={{ fontSize: 14, color: "var(--ink-soft)", marginTop: 4 }}>
                  {job.company_name}{job.location ? ` · ${job.location}` : ""}
                </p>
              </div>
              <a href={job.apply_url} target="_blank" rel="noopener noreferrer" className="btn btn-primary" style={{ textDecoration: "none", fontSize: 13, whiteSpace: "nowrap" }}>
                Apply →
              </a>
            </div>
          </div>
        ))}

        {!loading && listings.length === 0 && (
          <div className="card" style={{ padding: 32, textAlign: "center" }}>
            <p style={{ color: "var(--ink-soft)" }}>
              {isAdmin ? "No listings yet - fetch some above." : "No listings available right now."}
            </p>
          </div>
        )}
      </div>
    </main>
  );
}

export default function JobsPage() {
  return (
    <RequireAuth>
      <JobsPageContent />
    </RequireAuth>
  );
}
