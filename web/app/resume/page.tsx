"use client";
import RequireAuth from "../../components/RequireAuth";

import { useEffect, useRef, useState } from "react";
import { listCompanies, uploadAndMatchResume } from "../../lib/api";

type MatchResult = {
  match_score_percent?: number;
  missing_keywords?: string[];
  suggestions?: string[];
  meets_cgpa_cutoff?: boolean | null;
  [key: string]: any;
};

const MAX_RESUME_BYTES = 15 * 1024 * 1024; // 15 MB - keep in sync with backend MAX_RESUME_UPLOAD_BYTES

function ResumePageContent() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ file_url: string; match_result: MatchResult } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listCompanies().then(setCompanies);
  }, []);

  function handleFileChange(selected: File | null) {
    setError(null);
    if (selected && selected.size > MAX_RESUME_BYTES) {
      setError("Resume file is too large. Maximum allowed size is 15 MB.");
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    setFile(selected);
  }

  async function handleUpload() {
    if (!file || !companyId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await uploadAndMatchResume(companyId, file);
      setResult(res);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to upload and match resume");
    } finally {
      setLoading(false);
    }
  }

  const match = result?.match_result;

  return (
    <main style={{ maxWidth: 680, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>Resume match</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8 }}>
        Upload your resume as a PDF and see how it stacks up against a target company's requirements.
      </p>

      <div className="card" style={{ padding: 24, marginTop: 24 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
          Target company
        </label>
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)} style={{ width: "100%" }}>
          <option value="">Select a company</option>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 16, marginBottom: 6 }}>
          Resume (PDF)
        </label>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
          style={{ width: "100%" }}
        />
        <p style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>PDF only, up to 15 MB.</p>
        {file && (
          <p style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 2 }}>
            Selected: {file.name} ({(file.size / (1024 * 1024)).toFixed(1)} MB)
          </p>
        )}

        <button
          onClick={handleUpload}
          disabled={loading || !file || !companyId}
          className="btn btn-primary"
          style={{ width: "100%", marginTop: 20 }}
        >
          {loading ? "Uploading & matching..." : "Upload & match"}
        </button>
      </div>

      {error && (
        <div className="card" style={{ padding: 16, marginTop: 16, borderColor: "var(--danger)" }}>
          <span style={{ color: "var(--danger)", fontSize: 14 }}>{error}</span>
        </div>
      )}

      {result && (
        <div className="card" style={{ padding: 24, marginTop: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: 20 }}>Match result</h3>
            <a href={result.file_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 13 }}>
              View uploaded PDF →
            </a>
          </div>

          {match?.match_score_percent !== undefined && (
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12 }}>
              <p style={{ fontSize: 32, fontWeight: 700, color: "var(--primary)" }}>
                {match.match_score_percent}% match
              </p>
              {match.meets_cgpa_cutoff !== null && match.meets_cgpa_cutoff !== undefined && (
                <span className={`badge ${match.meets_cgpa_cutoff ? "badge-applied" : "badge-rejected"}`}>
                  {match.meets_cgpa_cutoff ? "Meets CGPA cutoff" : "Below CGPA cutoff"}
                </span>
              )}
            </div>
          )}

          {match?.missing_keywords && match.missing_keywords.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--danger)" }}>Missing</span>
              <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
                {match.missing_keywords.map((k) => (
                  <span key={k} className="badge badge-not-applied">{k}</span>
                ))}
              </div>
            </div>
          )}

          {match?.suggestions && match.suggestions.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)" }}>Suggestions</span>
              <ul style={{ paddingLeft: 20, marginTop: 6 }}>
                {match.suggestions.map((s, i) => (
                  <li key={i} style={{ fontSize: 14, marginTop: 4 }}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </main>
  );
}

export default function ResumePage() {
  return (
    <RequireAuth>
      <ResumePageContent />
    </RequireAuth>
  );
}