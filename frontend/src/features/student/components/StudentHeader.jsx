
import { LogOut } from "lucide-react";

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

export default function StudentHeader({
  user,
  sidebarCollapsed,
  onToggleSidebar,
  onLogout,
  loggingOut,
}) {
  const displayName =
    user?.fullName || user?.username || "Student";

  const avatarLetter =
    displayName.trim().charAt(0).toUpperCase() || "S";

  return (
    <header className="aca-header flex min-h-[70px] flex-wrap items-center justify-between gap-3 px-5 py-3 md:px-8">
      {/* HEADER LEFT */}

      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          className="aca-sidebar-toggle hidden md:inline-flex"
          onClick={onToggleSidebar}
          aria-expanded={!sidebarCollapsed}
          aria-controls="student-sidebar"
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
            Student Portal
          </p>

          <p className="mt-1 truncate text-xs text-[#8CA0B6]">
            Academia Student Portal
          </p>
        </div>
      </div>

      {/* HEADER RIGHT */}

      <div className="ml-auto flex items-center gap-2 sm:gap-3">
        {/* STUDENT NAME */}

        <span className="hidden max-w-48 truncate text-sm font-semibold text-[#486582] sm:inline">
          {displayName}
        </span>

        {/* STUDENT BADGE */}

        <span className="aca-tag-mint">
          Student
        </span>

        {/* STUDENT AVATAR */}

        <span
          aria-label={`${displayName} avatar`}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#D5E9FF] text-sm font-bold text-[#476FA9]"
        >
          {avatarLetter}
        </span>

        {/* LOGOUT BUTTON */}

        <button
          type="button"
          onClick={onLogout}
          disabled={loggingOut}
          className="aca-logout-btn"
          aria-label={
            loggingOut ? "Logging out" : "Log out"
          }
        >
          <LogOut
            size={17}
            strokeWidth={2}
            aria-hidden="true"
          />

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
  );
}
