"use client";
import RequireAuth from "../../components/RequireAuth";

import { useEffect, useRef, useState } from "react";
import { listCompanies, uploadAndMatchResume, getResumeHistory } from "../../lib/api";

type MatchResult = {
  ats_score?: number;
  match_score_percent?: number;
  keyword_match_percent?: number;
  section_detection?: {
    contact_info?: boolean;
    education?: boolean;
    experience?: boolean;
    projects?: boolean;
    skills?: boolean;
    certifications?: boolean;
    achievements?: boolean;
  };
  detected_sections?: string[];
  missing_sections?: string[];
  matched_skills?: string[];
  missing_skills?: string[];
  matched_keywords?: string[];
  missing_keywords?: string[];
  experience_alignment?: string;
  education_match?: string;
  role_alignment?: string;
  quality_warnings?: string[];
  recommendations?: string[];
  suggestions?: string[];
  meets_cgpa_cutoff?: boolean | null;
  [key: string]: any;
};

type HistoricalScan = {
  id: string;
  file_url: string;
  target_company_id?: string | null;
  match_result?: MatchResult;
  created_at?: string;
};

const MAX_RESUME_BYTES = 15 * 1024 * 1024; // 15 MB

function ResumePageContent() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ file_url: string; match_result: MatchResult } | null>(null);
  const [history, setHistory] = useState<HistoricalScan[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listCompanies().then(setCompanies);
    loadHistory();
  }, []);

  async function loadHistory(targetCompId?: string) {
    try {
      const scans = await getResumeHistory(targetCompId);
      setHistory(scans);
    } catch (e) {
      console.error("Failed to load ATS history:", e);
    }
  }

  function handleCompanySelect(id: string) {
    setCompanyId(id);
    loadHistory(id || undefined);
  }

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
      loadHistory(companyId);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to upload and analyze resume");
    } finally {
      setLoading(false);
    }
  }

  const match = result?.match_result;
  const score = match?.ats_score ?? match?.match_score_percent ?? 0;

  return (
    <main style={{ maxWidth: 840, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 32 }}>ATS Resume Tracker & Analyzer</h1>
      <p style={{ color: "var(--ink-soft)", marginTop: 8, fontSize: 15 }}>
        Screen your resume against target company requirements, detect section/keyword gaps, and track ATS compatibility score improvements over time.
      </p>

      {/* Upload Card */}
      <div className="card" style={{ padding: 24, marginTop: 24 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginBottom: 6 }}>
          Target company / Role
        </label>
        <select value={companyId} onChange={(e) => handleCompanySelect(e.target.value)} style={{ width: "100%" }}>
          <option value="">Select target company</option>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <label style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-soft)", display: "block", marginTop: 16, marginBottom: 6 }}>
          Resume File (PDF)
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
          {loading ? "Analyzing ATS Compatibility..." : "Run ATS Scan & Match"}
        </button>
      </div>

      {error && (
        <div className="card" style={{ padding: 16, marginTop: 16, borderColor: "var(--danger)" }}>
          <span style={{ color: "var(--danger)", fontSize: 14 }}>{error}</span>
        </div>
      )}

      {/* ATS Analysis Result */}
      {result && (
        <div className="card" style={{ padding: 28, marginTop: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: 22 }}>Detailed ATS Analysis Result</h3>
            <a href={result.file_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 13, textDecoration: "none", color: "var(--primary)" }}>
              View Uploaded PDF →
            </a>
          </div>

          <div style={{ display: "flex", gap: 24, marginTop: 20, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ padding: "16px 24px", borderRadius: 12, background: "var(--surface)", border: "1.5px solid var(--line)", textAlign: "center" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase" }}>ATS Score</div>
              <div style={{ fontSize: 36, fontWeight: 800, color: score >= 75 ? "var(--accent)" : score >= 50 ? "#d97706" : "var(--danger)" }}>
                {score}/100
              </div>
            </div>

            {match?.keyword_match_percent !== undefined && (
              <div style={{ padding: "16px 20px", borderRadius: 12, background: "var(--surface)", border: "1px solid var(--line)", textAlign: "center" }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-soft)", textTransform: "uppercase" }}>Keyword Match</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: "var(--ink)" }}>{match.keyword_match_percent}%</div>
              </div>
            )}

            {match?.meets_cgpa_cutoff !== null && match?.meets_cgpa_cutoff !== undefined && (
              <span className={`badge ${match.meets_cgpa_cutoff ? "badge-applied" : "badge-rejected"}`} style={{ fontSize: 13, padding: "8px 14px" }}>
                {match.meets_cgpa_cutoff ? "✓ Meets CGPA Cutoff" : "✕ Below CGPA Cutoff"}
              </span>
            )}
          </div>

          {/* Section Detection Matrix */}
          {match?.section_detection && (
            <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid var(--line)" }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: "var(--ink)" }}>A. Section Detection & ATS Readability</span>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
                {Object.entries(match.section_detection).map(([sec, detected]) => (
                  <span
                    key={sec}
                    className={`badge ${detected ? "badge-applied" : "badge-rejected"}`}
                    style={{ fontSize: 12, textTransform: "capitalize" }}
                  >
                    {detected ? `✓ ${sec.replace("_", " ")}` : `✕ Missing ${sec.replace("_", " ")}`}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Skills & Keywords Breakdown */}
          <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid var(--line)", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <div>
              <span style={{ fontSize: 13, fontWeight: 700, color: "var(--accent)" }}>Matched Keywords & Skills</span>
              <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                {(match?.matched_keywords || match?.matched_skills || []).map((k) => (
                  <span key={k} className="badge badge-applied" style={{ fontSize: 12 }}>{k}</span>
                ))}
                {(!match?.matched_keywords?.length && !match?.matched_skills?.length) && (
                  <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>None detected</span>
                )}
              </div>
            </div>

            <div>
              <span style={{ fontSize: 13, fontWeight: 700, color: "var(--danger)" }}>Missing Keywords & Skills</span>
              <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                {(match?.missing_keywords || match?.missing_skills || []).map((k) => (
                  <span key={k} className="badge badge-not-applied" style={{ fontSize: 12 }}>{k}</span>
                ))}
                {(!match?.missing_keywords?.length && !match?.missing_skills?.length) && (
                  <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>None missing</span>
                )}
              </div>
            </div>
          </div>

          {/* Quality Warnings */}
          {match?.quality_warnings && match.quality_warnings.length > 0 && (
            <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid var(--line)" }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: "var(--danger)" }}>ATS Formatting & Readability Warnings</span>
              <ul style={{ paddingLeft: 20, marginTop: 6, color: "var(--ink-soft)" }}>
                {match.quality_warnings.map((w, i) => (
                  <li key={i} style={{ fontSize: 13, marginTop: 4 }}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Actionable Recommendations */}
          {((match?.recommendations && match.recommendations.length > 0) || (match?.suggestions && match.suggestions.length > 0)) && (
            <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid var(--line)" }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: "var(--ink)" }}>Actionable Improvement Recommendations</span>
              <ol style={{ paddingLeft: 20, marginTop: 8 }}>
                {(match?.recommendations || match?.suggestions || []).map((rec, i) => (
                  <li key={i} style={{ fontSize: 14, marginTop: 6, lineHeight: 1.5, color: "var(--ink)" }}>
                    {rec}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      {/* Historical ATS Scan Tracker */}
      {history.length > 0 && (
        <div style={{ marginTop: 36 }}>
          <h2 style={{ fontSize: 22, marginBottom: 16 }}>Historical ATS Scan Progress</h2>
          <div className="card" style={{ padding: 20 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {history.map((scan, idx) => {
                const scanScore = scan.match_result?.ats_score ?? scan.match_result?.match_score_percent ?? 0;
                const prevScore = idx < history.length - 1 ? (history[idx + 1].match_result?.ats_score ?? history[idx + 1].match_result?.match_score_percent ?? 0) : null;
                const delta = prevScore !== null ? scanScore - prevScore : null;

                const companyObj = companies.find((c) => c.id === scan.target_company_id);

                return (
                  <div
                    key={scan.id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "12px 16px",
                      borderRadius: 8,
                      background: "var(--surface)",
                      border: "1px solid var(--line)",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>
                        {companyObj ? companyObj.name : "Company Match"}
                      </div>
                      <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 2 }}>
                        {scan.created_at ? new Date(scan.created_at).toLocaleString() : "Previous Scan"}
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      {delta !== null && delta !== 0 && (
                        <span style={{ fontSize: 12, fontWeight: 700, color: delta > 0 ? "var(--accent)" : "var(--danger)" }}>
                          {delta > 0 ? `+${delta} pts` : `${delta} pts`}
                        </span>
                      )}
                      <div style={{ fontSize: 18, fontWeight: 800, color: scanScore >= 75 ? "var(--accent)" : "var(--ink)" }}>
                        {scanScore}%
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
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