"use client";

import RequireAuth from "../../components/RequireAuth";
import { useEffect, useState } from "react";
import {
  browseJobListings,
  searchJobListings,
  JobListingItem,
} from "../../lib/api";

function JobsPageContent() {
  const [listings, setListings] = useState<JobListingItem[]>([]);
  const [loading, setLoading] = useState(false);

  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");

  const [error, setError] = useState<string | null>(null);

  async function searchJobs() {
    const keywords = search.trim();

    if (!keywords) {
      setError("Please enter a job role to search.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Call dedicated student search endpoint (GET /job-listings/search)
      const data = await searchJobListings({
        keywords,
        location: location.trim() || undefined,
        results_per_page: 20,
      });

      setListings(data);
    } catch (e: any) {
      console.error("Job search failed:", e);

      setError(
        e?.response?.data?.detail ||
          "Unable to fetch jobs right now. Please try again."
      );

      setListings([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Load existing jobs when page opens
    async function loadInitialJobs() {
      setLoading(true);

      try {
        const data = await browseJobListings();
        setListings(data);
      } catch (e) {
        console.error("Failed to load jobs:", e);
      } finally {
        setLoading(false);
      }
    }

    loadInitialJobs();
  }, []);

  return (
    <main
      style={{
        maxWidth: 900,
        margin: "0 auto",
        padding: "48px 24px",
      }}
    >
      <h1 style={{ fontSize: 32 }}>Job Listings</h1>

      <p
        style={{
          color: "var(--ink-soft)",
          marginTop: 8,
        }}
      >
        Search live job openings directly from Adzuna.
      </p>

      {/* SEARCH BOX */}
      <div
        className="card"
        style={{
          padding: 20,
          marginTop: 24,
        }}
      >
        <div
          style={{
            display: "flex",
            gap: 10,
            flexWrap: "wrap",
          }}
        >
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                searchJobs();
              }
            }}
            placeholder="Search job role (e.g. Software Engineer)"
            style={{
              flex: 2,
              minWidth: 250,
            }}
          />

          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                searchJobs();
              }
            }}
            placeholder="Location (e.g. Bangalore)"
            style={{
              flex: 1,
              minWidth: 180,
            }}
          />

          <button
            onClick={searchJobs}
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? "Searching..." : "Search Jobs"}
          </button>
        </div>

        {error && (
          <p
            style={{
              color: "var(--danger)",
              marginTop: 12,
              fontSize: 14,
            }}
          >
            {error}
          </p>
        )}
      </div>

      {/* RESULTS */}
      {loading && (
        <p
          style={{
            color: "var(--ink-soft)",
            marginTop: 24,
          }}
        >
          Searching live jobs...
        </p>
      )}

      {!loading && listings.length > 0 && (
        <p
          style={{
            color: "var(--ink-soft)",
            marginTop: 24,
            fontSize: 14,
          }}
        >
          Found {listings.length} job listings
        </p>
      )}

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 12,
          marginTop: 20,
        }}
      >
        {listings.map((job) => (
          <div
            key={job.id}
            className="card"
            style={{
              padding: 20,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: 16,
              }}
            >
              <div>
                <h3 style={{ fontSize: 17 }}>
                  {job.role_title}
                </h3>

                <p
                  style={{
                    fontSize: 14,
                    color: "var(--ink-soft)",
                    marginTop: 5,
                  }}
                >
                  {job.company_name}
                  {job.location ? ` · ${job.location}` : ""}
                  {job.posted_at ? ` · Posted ${new Date(job.posted_at).toLocaleDateString()}` : ""}
                </p>
                {job.description_snippet && (
                  <p
                    style={{
                      fontSize: 13,
                      color: "var(--ink-soft)",
                      marginTop: 10,
                      lineHeight: 1.5,
                    }}
                  >
                    {job.description_snippet.length > 250
                      ? `${job.description_snippet.substring(0, 250)}...`
                      : job.description_snippet}
                  </p>
                )}
              </div>

              <a
                href={job.apply_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
                style={{
                  textDecoration: "none",
                  fontSize: 13,
                  whiteSpace: "nowrap",
                }}
              >
                Apply →
              </a>
            </div>
          </div>
        ))}

        {!loading && listings.length === 0 && !error && (
          <div
            className="card"
            style={{
              padding: 32,
              textAlign: "center",
            }}
          >
            <p
              style={{
                color: "var(--ink-soft)",
              }}
            >
              Search for a job role to see available openings.
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
