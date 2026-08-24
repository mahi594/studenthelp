"use client";

import { useEffect, useState } from "react";
import RequireAuth from "../../../components/RequireAuth";
import { listAuditLogs, AuditLogItem } from "../../../lib/api";

function AuditLogsContent() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState<string>("");

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  async function fetchLogs() {
    setLoading(true);
    try {
      const data = await listAuditLogs({ action: actionFilter || undefined, limit: 100 });
      setLogs(data);
    } catch (err) {
      console.error("Failed to load audit logs", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 1000, margin: "0 auto", padding: "40px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700 }}>Institutional Audit Logs</h1>
          <p style={{ color: "var(--ink-soft)", fontSize: 14, marginTop: 4 }}>
            System-recorded operational events for your placement cell tenant.
          </p>
        </div>
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          style={{ padding: "8px 12px", borderRadius: 6, border: "1px solid #d1d5db" }}
        >
          <option value="">All Actions</option>
          <option value="company_verified">Company Verified</option>
          <option value="csv_export">CSV Exported</option>
          <option value="intervention_completed">Intervention Completed</option>
        </select>
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 32, textAlign: "center", color: "var(--ink-soft)" }}>Loading audit records...</div>
        ) : logs.length === 0 ? (
          <div style={{ padding: 32, textAlign: "center", color: "var(--ink-soft)" }}>No audit records found.</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ background: "#f9fafb", borderBottom: "1px solid #e5e7eb", textAlign: "left" }}>
                <th style={{ padding: "12px 16px" }}>Timestamp</th>
                <th style={{ padding: "12px 16px" }}>Action</th>
                <th style={{ padding: "12px 16px" }}>Resource Type</th>
                <th style={{ padding: "12px 16px" }}>Resource ID</th>
                <th style={{ padding: "12px 16px" }}>Context Metadata</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "12px 16px", color: "var(--ink-soft)" }}>
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td style={{ padding: "12px 16px", fontWeight: 600 }}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: 12,
                        background: "#e0f2fe",
                        color: "#0369a1",
                        fontSize: 11,
                      }}
                    >
                      {log.action}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px" }}>{log.resource_type}</td>
                  <td style={{ padding: "12px 16px", fontFamily: "monospace", fontSize: 12 }}>
                    {log.resource_id ? `${log.resource_id.substring(0, 8)}...` : "—"}
                  </td>
                  <td style={{ padding: "12px 16px", color: "var(--ink-soft)" }}>
                    {log.metadata_json ? JSON.stringify(log.metadata_json) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}

export default function AuditLogsPage() {
  return (
    <RequireAuth role="tpo">
      <AuditLogsContent />
    </RequireAuth>
  );
}

