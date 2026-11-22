
import { useState } from "react";
import { Outlet } from "react-router-dom";

import { useAuth } from "../../auth/context/AuthContext";

import StudentSidebar from "../components/StudentSidebar";
import StudentHeader from "../components/StudentHeader";

import "../../../styles/academia-pastel.css";

export default function StudentLayout() {
  const { user, signOut } = useAuth();

  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);

  const [loggingOut, setLoggingOut] =
    useState(false);

  const [error, setError] = useState("");

  function toggleSidebar() {
    setSidebarCollapsed((previous) => !previous);
  }

  async function handleLogout() {
    if (loggingOut) return;

    setLoggingOut(true);
    setError("");

    try {
      await signOut();
    } catch (err) {
      setError(
        err.message || "Unable to log out."
      );
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <div
      className={`academia-ui min-h-screen md:flex ${
        sidebarCollapsed
          ? "is-sidebar-collapsed"
          : ""
      }`}
    >
      {/* SIDEBAR */}

      <StudentSidebar />

      {/* MAIN CONTENT */}

      <div className="min-w-0 flex-1">
        {/* HEADER */}

        <StudentHeader
          user={user}
          sidebarCollapsed={sidebarCollapsed}
          onToggleSidebar={toggleSidebar}
          onLogout={handleLogout}
          loggingOut={loggingOut}
        />

        {/* PAGE CONTENT */}

        <main className="aca-content w-full px-4 py-7 sm:px-6 md:px-8">
          <div className="mx-auto w-full max-w-7xl">
            <Outlet />
          </div>
        </main>

        {/* ERROR MESSAGE */}

        {error && (
          <div
            role="alert"
            className="fixed bottom-5 right-5 z-50 rounded-xl border border-red-200 bg-white px-4 py-3 text-sm text-red-600 shadow-lg"
          >
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
