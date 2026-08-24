"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth-context";
import NotificationBell from "./NotificationBell";
import Icon, { IconName } from "./icons";

type NavLink = { href: string; label: string; icon: IconName };

const GROUPS: { label: string | null; links: NavLink[] }[] = [
  {
    label: null,
    links: [{ href: "/dashboard", label: "Dashboard", icon: "grid" }],
  },
  {
    label: "Prepare",
    links: [
      { href: "/leetcode", label: "LeetCode Practice", icon: "code" },
      { href: "/quiz", label: "Quiz", icon: "check-square" },
      { href: "/companies", label: "Companies", icon: "building" },
      { href: "/prep-plan", label: "Prep Plan", icon: "list" },
      { href: "/roadmap", label: "Roadmap", icon: "map" },
      { href: "/resume", label: "Resume", icon: "file-text" },
      { href: "/mock-interview", label: "Mock Interview", icon: "mic" },
    ],
  },
  {
    label: "Explore",
    links: [
      { href: "/jobs", label: "Jobs", icon: "search" },
      { href: "/community", label: "Community", icon: "users" },
      { href: "/chat", label: "Ask StudentHelp", icon: "message-circle" },
    ],
  },
  {
    label: "Track",
    links: [
      { href: "/applications", label: "My Applications", icon: "briefcase" },
      { href: "/profile", label: "Profile", icon: "user" },
    ],
  },
];

const ADMIN_NAV_GROUPS: { label: string | null; links: NavLink[] }[] = [
  {
    label: "Admin Portal",
    links: [
      { href: "/admin/tpo-dashboard", label: "TPO Dashboard", icon: "bar-chart" },
      { href: "/admin/leetcode-tracker", label: "LeetCode Tracker", icon: "fire" },
      { href: "/admin/audit-logs", label: "Audit Logs", icon: "shield-check" },
    ],
  },
  {
    label: "Management",
    links: [
      { href: "/admin/companies", label: "Manage Companies", icon: "settings" },
      { href: "/admin/quiz-approval", label: "Quiz Approval", icon: "check-square" },
    ],
  },
];


// Content admins only (not tpo_admin) can create other admin/tpo_admin
// accounts - appended dynamically below rather than baked into the
// constant above, so a tpo_admin browsing /admin never sees this link.
const ADMIN_ONLY_LINK: NavLink = { href: "/admin/create-admin", label: "Create Admin", icon: "user" };


const COLLAPSE_KEY = "studenthelp:sidebar-collapsed";
const EXPANDED_W = 244;
const COLLAPSED_W = 68;

function NavItem({
  link,
  active,
  collapsed,
  accent = false,
}: {
  link: NavLink;
  active: boolean;
  collapsed: boolean;
  accent?: boolean;
}) {
  return (
    <Link
      href={link.href}
      title={collapsed ? link.label : undefined}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: collapsed ? "10px 0" : "9px 12px",
        justifyContent: collapsed ? "center" : "flex-start",
        borderRadius: 10,
        textDecoration: "none",
        fontSize: 13.5,
        fontWeight: 600,
        color: active ? "var(--primary)" : "var(--ink-soft)",
        background: active ? (accent ? "var(--accent-soft)" : "rgba(31,92,74,0.09)") : "transparent",
        transition: "background 120ms ease, color 120ms ease",
        whiteSpace: "nowrap",
        overflow: "hidden",
      }}
    >
      <Icon name={link.icon} size={18} />
      {!collapsed && <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>{link.label}</span>}
    </Link>
  );
}

export default function Sidebar({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAdmin, isTpoOrAdmin, loading, logout: authLogout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = typeof window !== "undefined" ? window.localStorage.getItem(COLLAPSE_KEY) : null;
    if (saved === "1") setCollapsed(true);
  }, []);

  function toggleCollapsed() {
    setCollapsed((c) => {
      const next = !c;
      if (typeof window !== "undefined") window.localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
      return next;
    });
  }

  function handleLogout() {
    authLogout();
    router.push("/login");
  }

  const loggedIn = !!user;

  // Logged-out visitors (login/register/forgot-password/etc.) get a slim
  // top bar instead of the app sidebar - there's nothing to navigate yet.
  if (!loading && !loggedIn) {
    return (
      <>
        <nav
          style={{
            borderBottom: "1px solid var(--line)",
            background: "var(--surface)",
            position: "sticky",
            top: 0,
            zIndex: 10,
          }}
        >
          <div
            style={{
              maxWidth: 1120,
              margin: "0 auto",
              padding: "16px 24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <Link href="/dashboard" style={{ textDecoration: "none" }}>
              <span className="display" style={{ fontSize: 20, color: "var(--ink)" }}>
                StudentHelp
              </span>
            </Link>
            <Link
              href="/login"
              className="btn btn-primary"
              style={{ fontSize: 13, padding: "6px 14px", textDecoration: "none" }}
            >
              Log in
            </Link>
          </div>
        </nav>
        {children}
      </>
    );
  }

  const width = collapsed ? COLLAPSED_W : EXPANDED_W;

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width,
          flexShrink: 0,
          borderRight: "1px solid var(--line)",
          background: "var(--surface)",
          display: "flex",
          flexDirection: "column",
          position: "sticky",
          top: 0,
          height: "100vh",
          overflowY: "auto",
          overflowX: "hidden",
          transition: mounted ? "width 160ms ease" : undefined,
          padding: "18px 12px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "space-between",
            padding: collapsed ? "0 0 18px" : "0 6px 18px",
          }}
        >
          {!collapsed && (
            <Link href="/dashboard" style={{ textDecoration: "none" }}>
              <span className="display" style={{ fontSize: 19, color: "var(--ink)" }}>
                StudentHelp
              </span>
            </Link>
          )}
          {!collapsed && loggedIn && <NotificationBell />}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 18, flex: 1 }}>
          {isTpoOrAdmin && pathname.startsWith("/admin") ? (
            // Dedicated Admin Navigation Bar
            ADMIN_NAV_GROUPS.map((group, i) => (
              <div key={i} style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                {group.label && !collapsed && (
                  <span
                    className="mono"
                    style={{
                      fontSize: 10.5,
                      letterSpacing: "0.06em",
                      color: "var(--accent)",
                      padding: "0 12px",
                      marginBottom: 2,
                      textTransform: "uppercase",
                    }}
                  >
                    {group.label}
                  </span>
                )}
                {group.links.map((link) => (
                  <NavItem key={link.href} link={link} active={pathname === link.href} collapsed={collapsed} accent />
                ))}
                {group.label === "Management" && isAdmin && (
                  <NavItem link={ADMIN_ONLY_LINK} active={pathname === ADMIN_ONLY_LINK.href} collapsed={collapsed} accent />
                )}
              </div>
            ))
          ) : (
            // Standard Student Navigation Bar
            <>
              {GROUPS.map((group, i) => (
                <div key={i} style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                  {group.label && !collapsed && (
                    <span
                      className="mono"
                      style={{
                        fontSize: 10.5,
                        letterSpacing: "0.06em",
                        color: "var(--ink-soft)",
                        padding: "0 12px",
                        marginBottom: 2,
                        textTransform: "uppercase",
                      }}
                    >
                      {group.label}
                    </span>
                  )}
                  {group.links.map((link) => (
                    <NavItem key={link.href} link={link} active={pathname === link.href} collapsed={collapsed} />
                  ))}
                </div>
              ))}

              {isTpoOrAdmin && (
                <div style={{ borderTop: "1px solid var(--line)", paddingTop: 14 }}>
                  <Link
                    href="/admin/tpo-dashboard"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      padding: collapsed ? "10px 0" : "9px 12px",
                      justifyContent: collapsed ? "center" : "flex-start",
                      borderRadius: 10,
                      textDecoration: "none",
                      fontSize: 13,
                      fontWeight: 700,
                      color: "var(--accent)",
                      background: "var(--accent-soft)",
                    }}
                  >
                    <Icon name="shield-check" size={18} />
                    {!collapsed && <span>Switch to Admin Portal</span>}
                  </Link>
                </div>
              )}
            </>
          )}

          {isTpoOrAdmin && pathname.startsWith("/admin") && (
            <div style={{ borderTop: "1px solid var(--line)", paddingTop: 14 }}>
              <Link
                href="/dashboard"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: collapsed ? "10px 0" : "9px 12px",
                  justifyContent: collapsed ? "center" : "flex-start",
                  borderRadius: 10,
                  textDecoration: "none",
                  fontSize: 13,
                  fontWeight: 600,
                  color: "var(--ink-soft)",
                  background: "rgba(0,0,0,0.03)",
                }}
              >
                <Icon name="grid" size={18} />
                {!collapsed && <span>Switch to Student View</span>}
              </Link>
            </div>
          )}
        </div>


        <div style={{ borderTop: "1px solid var(--line)", paddingTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          {collapsed && loggedIn && (
            <div style={{ display: "flex", justifyContent: "center" }}>
              <NotificationBell />
            </div>
          )}
          {!collapsed && user && (
            <div style={{ padding: "0 12px", overflow: "hidden" }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {user.name || user.email}
              </div>
              <div className="mono" style={{ fontSize: 11, color: "var(--ink-soft)", textTransform: "capitalize" }}>
                {user.role?.replace("_", " ") || "student"}
              </div>
            </div>
          )}
          <button
            onClick={handleLogout}
            title="Log out"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              justifyContent: collapsed ? "center" : "flex-start",
              padding: collapsed ? "9px 0" : "9px 12px",
              borderRadius: 10,
              border: "none",
              background: "transparent",
              color: "var(--danger)",
              fontSize: 13.5,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <Icon name="log-out" size={17} />
            {!collapsed && "Log out"}
          </button>
          <button
            onClick={toggleCollapsed}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              justifyContent: collapsed ? "center" : "flex-start",
              padding: collapsed ? "9px 0" : "9px 12px",
              borderRadius: 10,
              border: "none",
              background: "transparent",
              color: "var(--ink-soft)",
              fontSize: 13.5,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <Icon name={collapsed ? "chevron-right" : "chevron-left"} size={17} />
            {!collapsed && "Collapse"}
          </button>
        </div>
      </aside>

      <div style={{ flex: 1, minWidth: 0 }}>{children}</div>
    </div>
  );
}
