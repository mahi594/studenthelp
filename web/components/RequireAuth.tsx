"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../lib/auth-context";

type Props = {
  children: React.ReactNode;
  /** "admin" = admin only. "tpo" = admin or tpo_admin. Omit for "any logged-in user". */
  role?: "admin" | "tpo";
};

export default function RequireAuth({ children, role }: Props) {
  const { user, loading, isAdmin, isTpoOrAdmin } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const roleOk = !role || (role === "admin" ? isAdmin : isTpoOrAdmin);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    if (!roleOk) {
      router.replace("/dashboard");
    }
  }, [loading, user, roleOk, pathname, router]);

  // Nothing to show while we're checking auth, or during the brief window
  // before the redirect effect above fires - avoids a flash of protected
  // content (or of the "old" error-message UI) for logged-out users.
  if (loading || !user || !roleOk) {
    return (
      <main style={{ maxWidth: 720, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
        <span className="mono" style={{ fontSize: 13, color: "var(--ink-soft)" }}>
          {loading ? "Checking your session..." : "Redirecting..."}
        </span>
      </main>
    );
  }

  return <>{children}</>;
}
