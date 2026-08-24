"use client";

/**
 * The app's signature visual: a row of chunky rounded rungs that fill
 * left-to-right as a score (0-100) climbs. Used for the readiness score
 * hero, and reused as a progress indicator for prep plans / roadmap phases
 * so the whole app visually reinforces "climbing toward ready."
 */
export default function ReadinessLadder({
  score,
  rungs = 10,
  height = 14,
}: {
  score: number;
  rungs?: number;
  height?: number;
}) {
  const filledRungs = Math.round((score / 100) * rungs);

  return (
    <div className="ladder" role="progressbar" aria-valuenow={score} aria-valuemin={0} aria-valuemax={100}>
      {Array.from({ length: rungs }).map((_, i) => (
        <div
          key={i}
          className={`ladder-rung ${i < filledRungs ? "filled" : ""} ${
            i === filledRungs - 1 && score < 100 ? "accent" : ""
          }`}
          style={{ height }}
        />
      ))}
    </div>
  );
}
