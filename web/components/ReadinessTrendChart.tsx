"use client";

type ReadinessSnapshot = {
  composite_score: number;
  computed_at: string;
};

export default function ReadinessTrendChart({ history }: { history: ReadinessSnapshot[] }) {
  if (!history || history.length < 2) {
    return (
      <p style={{ fontSize: 13, color: "var(--ink-soft)" }}>
        Keep taking quizzes and updating your resume - once you have a few readiness snapshots, your trend will show up here.
      </p>
    );
  }

  const width = 600;
  const height = 140;
  const padding = 24;

  const scores = history.map((h) => h.composite_score);
  const minScore = Math.min(...scores, 0);
  const maxScore = Math.max(...scores, 100);

  const points = history.map((h, i) => {
    const x = padding + (i / (history.length - 1)) * (width - padding * 2);
    const y =
      height - padding - ((h.composite_score - minScore) / (maxScore - minScore || 1)) * (height - padding * 2);
    return { x, y, score: h.composite_score, date: h.computed_at };
  });

  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  const firstDate = new Date(history[0].computed_at);
  const lastDate = new Date(history[history.length - 1].computed_at);
  const fmt = (d: Date) => d.toLocaleDateString(undefined, { month: "short", day: "numeric" });

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto" }}>
        <path d={pathD} fill="none" stroke="var(--primary)" strokeWidth={2} />
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={3.5} fill="var(--primary)">
            <title>{`${new Date(p.date).toLocaleDateString()}: ${p.score}/100`}</title>
          </circle>
        ))}
      </svg>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--ink-soft)", marginTop: 4 }}>
        <span>{fmt(firstDate)}</span>
        <span>{fmt(lastDate)}</span>
      </div>
    </div>
  );
}