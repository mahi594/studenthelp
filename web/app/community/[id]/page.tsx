"use client";
import RequireAuth from "../../../components/RequireAuth";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getQuestion, answerQuestion, upvoteAnswer, QAQuestionDetail } from "../../../lib/api";

function CommunityQuestionPageContent() {
  const params = useParams();
  const router = useRouter();
  const questionId = params.id as string;

  const [question, setQuestion] = useState<QAQuestionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [answerBody, setAnswerBody] = useState("");
  const [posting, setPosting] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await getQuestion(questionId);
      setQuestion(data);
    } catch (e: any) {
      if (e?.response?.status === 404) setNotFound(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionId]);

  async function handleAnswer() {
    if (!answerBody.trim()) return;
    setPosting(true);
    try {
      await answerQuestion(questionId, answerBody);
      setAnswerBody("");
      load();
    } finally {
      setPosting(false);
    }
  }

  async function handleUpvote(answerId: string) {
    await upvoteAnswer(answerId);
    load();
  }

  if (notFound) {
    return (
      <main style={{ maxWidth: 680, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
        <p style={{ color: "var(--ink-soft)" }}>This question doesn't exist or was removed.</p>
        <button onClick={() => router.push("/community")} className="btn btn-secondary" style={{ marginTop: 16 }}>
          Back to Community
        </button>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 680, margin: "0 auto", padding: "48px 24px" }}>
      {loading && <p style={{ color: "var(--ink-soft)" }}>Loading...</p>}

      {question && (
        <>
          <div className="card" style={{ padding: 24 }}>
            <h1 style={{ fontSize: 24 }}>{question.title}</h1>
            <p style={{ fontSize: 15, marginTop: 12, whiteSpace: "pre-wrap" }}>{question.body}</p>
            <span className="mono" style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 14, display: "block" }}>
              {question.author_name} · {new Date(question.created_at).toLocaleDateString()}
            </span>
          </div>

          <h2 style={{ fontSize: 18, marginTop: 32 }}>
            {question.answers.length} {question.answers.length === 1 ? "Answer" : "Answers"}
          </h2>

          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
            {question.answers
              .slice()
              .sort((a, b) => b.upvotes - a.upvotes)
              .map((a) => (
                <div key={a.id} className="card" style={{ padding: 18, display: "flex", gap: 14 }}>
                  <button
                    onClick={() => handleUpvote(a.id)}
                    className="btn btn-secondary"
                    style={{ fontSize: 12, padding: "6px 10px", height: "fit-content" }}
                  >
                    ▲ {a.upvotes}
                  </button>
                  <div>
                    <p style={{ fontSize: 14, whiteSpace: "pre-wrap" }}>{a.body}</p>
                    <span className="mono" style={{ fontSize: 11, color: "var(--ink-soft)", marginTop: 8, display: "block" }}>
                      {a.author_name} · {new Date(a.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
          </div>

          <div className="card" style={{ padding: 20, marginTop: 20 }}>
            <textarea
              value={answerBody}
              onChange={(e) => setAnswerBody(e.target.value)}
              placeholder="Share what you know..."
              rows={3}
              style={{ width: "100%" }}
            />
            <button onClick={handleAnswer} disabled={posting || !answerBody.trim()} className="btn btn-primary" style={{ marginTop: 10 }}>
              {posting ? "Posting..." : "Post answer"}
            </button>
          </div>
        </>
      )}
    </main>
  );
}

export default function CommunityQuestionPage() {
  return (
    <RequireAuth>
      <CommunityQuestionPageContent />
    </RequireAuth>
  );
}
