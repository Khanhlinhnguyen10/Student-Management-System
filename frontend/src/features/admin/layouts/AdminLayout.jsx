
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../../auth/context/AuthContext";

import "../../../styles/academia-pastel.css";
import { CalendarDays } from "lucide-react";
const MENU = [
  {
    label: "Dashboard",
    short: "DB",
    to: "/admin",
    end: true,
  },
  {
    label: "Create Account",
    short: "CA",
    to: "/admin/createaccount",
  },
  {
    label: "Students",
    short: "ST",
    to: "/admin/students",
  },
  {
    label: "Lecturers",
    short: "LE",
    to: "/admin/lecturers",
  },
  {
    label: "Assign Lecturer",
    short: "AL",
    to: "/admin/assignlecturer",
  },
  {
    label: "Semesters",
    short: "SE",
    to: "/admin/semesters",
  },
  {
    label: "Faculties",
    short: "FA",
    to: "/admin/faculties",
  },
  {
    label: "Courses",
    short: "CO",
    to: "/admin/courses",
  },
  {
    label: "Class Sections",
    short: "CS",
    to: "/admin/class-sections",
    icon: CalendarDays,
  },
];

function AcademiaLogo() {
  return (
    <div className="aca-brand flex items-center gap-3 px-2">
      <span className="aca-logo-symbol flex h-10 w-10 items-center justify-center rounded-xl">
        <svg
          width="25"
          height="25"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="m2 9 10-5 10 5-10 5Z" />
          <path d="M6 11v5c3 3 9 3 12 0v-5" />
          <path d="M22 9v7" />
        </svg>
      </span>

      <div className="aca-brand-text">
        <p className="aca-logo text-lg">
          Academia
        </p>

        <p className="whitespace-nowrap text-[11px] tracking-wide text-[#8098B2]">
          Student Management
        </p>
      </div>
    </div>
  );
}

function SidebarToggleIcon({ collapsed }) {
  return (
    <svg
      width="19"
      height="19"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect
        x="3"
        y="4"
        width="18"
        height="16"
        rx="2"
      />
      <path d="M9 4v16" />
      {collapsed ? (
        <path d="m14 9 3 3-3 3" />
      ) : (
        <path d="m16 9-3 3 3 3" />
      )}
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="m16 17 5-5-5-5" />
      <path d="M21 12H9" />
    </svg>
  );
}

export default function AdminLayout() {
  const { user, signOut } = useAuth();

  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);

  const [loggingOut, setLoggingOut] = useState(false);
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
      <aside
        id="admin-sidebar"
        className="aca-sidebar flex flex-col border-b p-5 md:sticky md:top-0 md:h-screen md:w-64 md:shrink-0 md:overflow-y-auto md:border-b-0 md:border-r"
      >
        <div className="mb-8">
          <AcademiaLogo />
        </div>

        <div className="aca-sidebar-section-label mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.15em]">
          Main Menu
        </div>

        <nav
          aria-label="Administrator navigation"
          className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 md:grid-cols-1"
        >
          {MENU.map((item) =>
            item.to ? (
              <NavLink
                key={item.label}
                to={item.to}
                end={item.end}
                data-short={item.short}
                title={item.label}
                className={({ isActive }) =>
                  `aca-nav ${
                    isActive ? "is-active" : ""
                  }`
                }
              >
                <span>{item.label}</span>
              </NavLink>
            ) : (
              <span
                key={item.label}
                data-short={item.short}
                title={item.label}
                aria-disabled="true"
                className="aca-nav is-disabled"
              >
                <span>{item.label}</span>
              </span>
            )
          )}
        </nav>
      </aside>

      {/* MAIN AREA */}
      <div className="min-w-0 flex-1">
        {/* HEADER */}
        <header className="aca-header flex min-h-[70px] flex-wrap items-center justify-between gap-3 px-5 py-3 md:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              className="aca-sidebar-toggle hidden md:inline-flex"
              onClick={toggleSidebar}
              aria-expanded={!sidebarCollapsed}
              aria-controls="admin-sidebar"
              aria-label={
                sidebarCollapsed
                  ? "Expand sidebar"
                  : "Collapse sidebar"
              }
              title={
                sidebarCollapsed
                  ? "Expand sidebar"
                  : "Collapse sidebar"
              }
            >
              <SidebarToggleIcon
                collapsed={sidebarCollapsed}
              />
            </button>

            <div className="min-w-0">
              <p className="truncate text-xs font-bold uppercase tracking-[0.16em] text-[#6A90BB]">
                Administrator
              </p>

              <p className="mt-1 truncate text-xs text-[#8CA0B6]">
                Academia Management Portal
              </p>
            </div>
          </div>

          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <span className="hidden max-w-48 truncate text-sm font-semibold text-[#486582] sm:inline">
              {user?.fullName || user?.username}
            </span>

            <span className="aca-tag-mint">
              Admin
            </span>

            <span
              aria-label="Administrator avatar"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#D5E9FF] text-sm font-bold text-[#476FA9]"
            >
              {(user?.fullName || user?.username || "A")
                .charAt(0)
                .toUpperCase()}
            </span>

            <button
              type="button"
              onClick={handleLogout}
              disabled={loggingOut}
              className="aca-logout-btn"
            >
              <LogoutIcon />

              <span className="hidden sm:inline">
                {loggingOut
                  ? "Logging out..."
                  : "Log out"}
              </span>

              <span className="sm:hidden">
                {loggingOut ? "..." : "Exit"}
              </span>
            </button>
          </div>
        </header>

        {/* PAGE CONTENT */}
        <main className="aca-content w-full px-4 py-7 sm:px-6 md:px-8">
          <div className="mx-auto w-full max-w-7xl">
            <Outlet />
          </div>
        </main>

        {/* LOGOUT ERROR */}
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
