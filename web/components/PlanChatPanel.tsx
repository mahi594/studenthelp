"use client";
import React, { useState } from "react";
import { customizeRoadmap, customizePrepPlan, PrepPlan, RoadmapPhase } from "../lib/api";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

interface PlanChatPanelProps {
  planType: "roadmap" | "prep_plan";
  planId: string;
  onPlanUpdated: (updatedPlan: any) => void;
}

export default function PlanChatPanel({ planType, planId, onPlanUpdated }: PlanChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: `Hi! I'm your AI plan assistant. You can ask me to adjust your daily workload, skip topics you already know, shift deadlines, or reorder tasks. What would you like to customize?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [modifying, setModifying] = useState(false);

  async function handleSend() {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");

    const newMessages: ChatMessage[] = [...messages, { role: "user", content: userMessage }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const historyPayload = newMessages.map((m) => ({ role: m.role, content: m.content }));

      let response: any;
      if (planType === "roadmap") {
        response = await customizeRoadmap(planId, userMessage, historyPayload);
      } else {
        response = await customizePrepPlan(planId, userMessage, historyPayload);
      }

      if (response.plan_modified) {
        setModifying(true);
        setTimeout(() => setModifying(false), 1500);

        if (response.roadmap) {
          onPlanUpdated(response.roadmap);
        } else if (response.prep_plan) {
          onPlanUpdated(response.prep_plan);
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.explanation || (response.plan_modified ? "I've updated your plan accordingly!" : "Processed your request."),
        },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: e?.response?.data?.detail || "Sorry, I couldn't update the plan. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ padding: 20, marginTop: 24, border: "1.5px solid var(--primary)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ fontSize: 16, margin: 0, color: "var(--primary)" }}>
          💬 Customize {planType === "roadmap" ? "Roadmap" : "Prep Plan"} with AI Chatbot
        </h3>
        {modifying && (
          <span className="badge badge-applied" style={{ fontSize: 11, animation: "pulse 1s infinite" }}>
            ⚡ Plan Modified & Saved
          </span>
        )}
      </div>

      {/* Chat Messages Log */}
      <div
        style={{
          maxHeight: 280,
          overflowY: "auto",
          padding: 12,
          background: "var(--surface)",
          borderRadius: 8,
          border: "1px solid var(--line)",
          display: "flex",
          flexDirection: "column",
          gap: 10,
          marginBottom: 12,
        }}
      >
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "85%",
              padding: "9px 13px",
              borderRadius: 12,
              background: m.role === "user" ? "var(--primary)" : "#f3f4f6",
              color: m.role === "user" ? "#ffffff" : "#111827",
              fontSize: 13.5,
              lineHeight: 1.45,
            }}
          >
            {m.content}
          </div>
        ))}
        {loading && (
          <div style={{ fontSize: 12, color: "var(--ink-soft)", fontStyle: "italic", alignSelf: "flex-start" }}>
            AI is analyzing request and updating plan...
          </div>
        )}
      </div>

      {/* Input controls */}
      <div style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          placeholder="e.g. Reduce daily workload to 2 hours, or Skip arrays topic"
          disabled={loading}
          style={{ flex: 1, padding: "8px 12px", fontSize: 13.5 }}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()} className="btn btn-primary" style={{ whiteSpace: "nowrap" }}>
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}
