import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "../components/Sidebar";
import { AuthProvider } from "../lib/auth-context";

export const metadata: Metadata = {
  title: "StudentHelp — Placement Prep",
  description: "Personalized placement preparation: what to study, who's hiring, and how ready you are.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Sidebar>{children}</Sidebar>
        </AuthProvider>
      </body>
    </html>
  );
}
