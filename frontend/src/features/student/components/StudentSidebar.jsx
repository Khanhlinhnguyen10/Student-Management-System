
import { NavLink } from "react-router-dom";

import {
  BookOpen,
  FileText,
  GraduationCap,
  KeyRound,
  LayoutDashboard,
  UserRound,
} from "lucide-react";

// =============================================
// STUDENT MENU
// =============================================

const MENU = [
  {
    label: "Dashboard",
    to: "/student",
    end: true,
    short: "DB",
    Icon: LayoutDashboard,
  },
  {
    label: "Profile",
    to: "/student/profile",
    short: "PR",
    Icon: UserRound,
  },
  {
    label: "Curriculum",
    to: "/student/curriculum",
    short: "CU",
    Icon: BookOpen,
  },
  {
    label: "Transcript",
    to: "/student/transcript",
    short: "TR",
    Icon: FileText,
  },
  {
    label: "Change Password",
    to: "/student/change-password",
    short: "PW",
    Icon: KeyRound,
  },
];

// =============================================
// BRAND
// =============================================

function AcademiaLogo() {
  return (
    <div className="aca-brand flex items-center gap-3 px-2">
      <span className="aca-logo-symbol flex h-10 w-10 items-center justify-center rounded-xl">
        <GraduationCap
          size={25}
          strokeWidth={1.8}
          aria-hidden="true"
        />
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

// =============================================
// STUDENT SIDEBAR
// =============================================

export default function StudentSidebar() {
  return (
    <aside
      id="student-sidebar"
      className="aca-sidebar flex flex-col border-b p-5 md:sticky md:top-0 md:h-screen md:w-64 md:shrink-0 md:overflow-y-auto md:border-b-0 md:border-r"
    >
      {/* LOGO */}

      <div className="mb-8">
        <AcademiaLogo />
      </div>

      {/* MENU TITLE */}

      <div className="aca-sidebar-section-label mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.15em]">
        Student Menu
      </div>

      {/* NAVIGATION */}

      <nav
        aria-label="Student navigation"
        className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 md:grid-cols-1"
      >
        {MENU.map((item) => {
          const Icon = item.Icon;

          return (
            <NavLink
              key={item.label}
              to={item.to}
              end={item.end}
              title={item.label}
              data-short={item.short}
              className={({ isActive }) =>
                `aca-nav ${
                  isActive ? "is-active" : ""
                }`
              }
            >
              <Icon
                size={18}
                strokeWidth={1.9}
                aria-hidden="true"
              />

              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
