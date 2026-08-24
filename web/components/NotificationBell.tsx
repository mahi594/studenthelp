"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AppNotification,
  listNotifications,
  getUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
} from "../lib/api";

export default function NotificationBell() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [loaded, setLoaded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const count = await getUnreadNotificationCount();
        if (!cancelled) setUnreadCount(count);
      } catch {
        // Not logged in yet, or a transient failure - fail silently, next
        // poll will retry. A notification bell shouldn't surface errors.
      }
    }

    poll();
    const interval = setInterval(poll, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleOpen() {
    setOpen((prev) => !prev);
    if (!loaded) {
      const data = await listNotifications();
      setNotifications(data);
      setLoaded(true);
    }
  }

  async function handleNotificationClick(n: AppNotification) {
    if (!n.is_read) {
      await markNotificationRead(n.id);
      setNotifications((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    }
    setOpen(false);
    if (n.link) router.push(n.link);
  }

  async function handleMarkAllRead() {
    await markAllNotificationsRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
  }

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      <button
        onClick={handleOpen}
        aria-label="Notifications"
        className="btn btn-secondary"
        style={{ fontSize: 13, padding: "6px 12px", position: "relative" }}
      >
        🔔
        {unreadCount > 0 && (
          <span
            className="mono"
            style={{
              position: "absolute",
              top: -4,
              right: -4,
              background: "var(--danger)",
              color: "#fff",
              borderRadius: 999,
              fontSize: 10,
              fontWeight: 700,
              minWidth: 16,
              height: 16,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "0 4px",
            }}
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          className="card"
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 8px)",
            width: 320,
            maxHeight: 400,
            overflowY: "auto",
            padding: 12,
            zIndex: 20,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Notifications</span>
            {unreadCount > 0 && (
              <button onClick={handleMarkAllRead} style={{ fontSize: 12, background: "none", border: "none", color: "var(--primary)", cursor: "pointer" }}>
                Mark all read
              </button>
            )}
          </div>

          {notifications.length === 0 && (
            <p style={{ fontSize: 13, color: "var(--ink-soft)", padding: "12px 4px" }}>Nothing yet.</p>
          )}

          {notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => handleNotificationClick(n)}
              style={{
                padding: "10px 8px",
                borderRadius: 8,
                cursor: "pointer",
                background: n.is_read ? "transparent" : "var(--accent-soft)",
                marginBottom: 4,
              }}
            >
              <div style={{ fontSize: 13, fontWeight: 600 }}>{n.title}</div>
              {n.body && <div style={{ fontSize: 12, color: "var(--ink-soft)", marginTop: 2 }}>{n.body}</div>}
              <div className="mono" style={{ fontSize: 10, color: "var(--ink-soft)", marginTop: 4 }}>
                {new Date(n.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
