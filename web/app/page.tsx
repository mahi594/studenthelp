import Link from "next/link";
import ReadinessLadder from "../components/ReadinessLadder";

export default function HomePage() {
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "72px 24px" }}>
      <div style={{ maxWidth: 620 }}>
        <span
          className="mono"
          style={{
            fontSize: 13,
            color: "var(--accent)",
            fontWeight: 600,
            letterSpacing: "0.04em",
          }}
        >
          PLACEMENT SEASON, HANDLED
        </span>
        <h1 style={{ fontSize: 52, lineHeight: 1.08, marginTop: 12 }}>
          Know exactly what to study, who's hiring, and how ready you are.
        </h1>
        <p style={{ fontSize: 17, color: "var(--ink-soft)", marginTop: 20, lineHeight: 1.6 }}>
          StudentHelp turns curated company data and your quiz performance into a
          day-by-day plan — no more guessing what to prepare or which resume to send.
        </p>

        <div style={{ marginTop: 32, display: "flex", gap: 12 }}>
          <Link href="/dashboard" className="btn btn-primary" style={{ textDecoration: "none", display: "inline-block" }}>
            Go to your dashboard
          </Link>
          <Link href="/companies" className="btn btn-secondary" style={{ textDecoration: "none", display: "inline-block" }}>
            Browse companies
          </Link>
        </div>
      </div>

      <div className="card" style={{ marginTop: 64, padding: 32, maxWidth: 480 }}>
        <span className="mono" style={{ fontSize: 12, color: "var(--ink-soft)" }}>
          EXAMPLE READINESS SCORE
        </span>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 8 }}>
          <span className="display mono" style={{ fontSize: 40 }}>68</span>
          <span style={{ color: "var(--ink-soft)", fontSize: 14 }}>/ 100 — climbing</span>
        </div>
        <div style={{ marginTop: 16 }}>
          <ReadinessLadder score={68} />
        </div>
      </div>
    </main>
  );
}
