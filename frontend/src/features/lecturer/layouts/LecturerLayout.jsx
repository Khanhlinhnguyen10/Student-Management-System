
import { useState } from "react";
import { Outlet } from "react-router-dom";

import {
  BookOpen,
  LogOut,
} from "lucide-react";

import { useAuth } from "../../auth/context/AuthContext";
import LecturerSidebar from "../components/LecturerSidebar";


function getInitial(name) {
  if (typeof name !== "string" || !name.trim()) {
    return "L";
  }

  return name.trim().charAt(0).toUpperCase();
}


export default function LecturerLayout() {
  const { user, signOut } = useAuth();

  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState("");

  const displayName =
    user?.fullName || user?.username || "Lecturer";

  async function handleLogout() {
    if (loggingOut) return;

    setLoggingOut(true);
    setLogoutError("");

    try {
      await signOut();
    } catch (error) {
      setLogoutError(
        error?.message || "Unable to log out."
      );
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <div
      className={[
        "flex min-h-dvh flex-col",
        "bg-[#F3F7FD] text-[#365D91]",
        "md:h-dvh md:flex-row md:overflow-hidden",
      ].join(" ")}
    >
      {/* SIDEBAR */}
      <LecturerSidebar />

      {/* MAIN AREA */}
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">

        {/* COMPACT TOP HEADER */}
        <header
          className={[
            "z-10 flex min-h-[58px] shrink-0",
            "items-center justify-between gap-3",
            "border-b border-[#DCE8F6]",
            "bg-white px-4 py-2",
            "lg:px-6",
          ].join(" ")}
        >
          {/* LEFT */}
          <div className="flex min-w-0 items-center gap-2.5">
            <div
              className={[
                "flex h-8 w-8 shrink-0",
                "items-center justify-center",
                "rounded-[10px]",
                "border border-[#D8E7F7]",
                "bg-[#EFF6FF] text-[#527FB7]",
              ].join(" ")}
            >
              <BookOpen
                size={17}
                strokeWidth={1.8}
              />
            </div>

            <div className="min-w-0">
              <p
                className={[
                  "truncate text-[10px] font-bold",
                  "uppercase tracking-[0.16em]",
                  "text-[#5F8AC4]",
                ].join(" ")}
              >
                Lecturer Portal
              </p>

              <p className="mt-0.5 truncate text-[10px] text-[#8AA4C4]">
                Academia Lecturer Portal
              </p>
            </div>
          </div>

          {/* RIGHT */}
          <div className="flex shrink-0 items-center gap-2">

            <span
              className={[
                "hidden max-w-[180px] truncate",
                "text-[12px] font-bold text-[#365D91]",
                "sm:block",
              ].join(" ")}
              title={displayName}
            >
              {displayName}
            </span>

            <span
              className={[
                "hidden rounded-full",
                "bg-[#DDF3EA] px-2.5 py-1",
                "text-[10px] font-bold",
                "text-[#36826D]",
                "sm:inline-flex",
              ].join(" ")}
            >
              Lecturer
            </span>

            <div
              className={[
                "flex h-8 w-8 shrink-0",
                "items-center justify-center",
                "rounded-full bg-[#D5E7FF]",
                "text-[12px] font-bold text-[#527FB7]",
              ].join(" ")}
              aria-label={`Account: ${displayName}`}
              title={displayName}
            >
              {getInitial(displayName)}
            </div>

            <button
              type="button"
              onClick={handleLogout}
              disabled={loggingOut}
              className={[
                "inline-flex h-9 shrink-0",
                "items-center justify-center gap-2",
                "rounded-[10px] bg-[#BA3449]",
                "px-3 text-[11px] font-bold text-white",
                "shadow-[0_3px_8px_rgba(186,52,73,0.12)]",
                "transition-colors hover:bg-[#A92B40]",
                "disabled:cursor-not-allowed",
                "disabled:opacity-60",
              ].join(" ")}
            >
              <LogOut
                size={15}
                strokeWidth={1.8}
              />

              <span className="hidden sm:inline">
                {loggingOut ? "Logging out..." : "Log out"}
              </span>
            </button>
          </div>
        </header>

        {/* LOGOUT ERROR */}
        {logoutError && (
          <div
            role="alert"
            className={[
              "mx-4 mt-2 shrink-0 rounded-lg",
              "border border-red-200 bg-red-50",
              "px-3 py-2 text-xs text-red-700",
              "lg:mx-6",
            ].join(" ")}
          >
            {logoutError}
          </div>
        )}

        {/* PAGE CONTENT */}
        <main
          className={[
            "min-h-0 min-w-0 flex-1",
            "bg-[#F3F7FD]",
            "md:overflow-y-auto",
          ].join(" ")}
        >
          <div
            className={[
              "mx-auto w-full max-w-[1400px]",
              "px-4 py-3",
              "lg:px-6 lg:py-3",
            ].join(" ")}
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
