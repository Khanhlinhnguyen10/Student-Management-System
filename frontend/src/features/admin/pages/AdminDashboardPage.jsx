
import { Link } from "react-router-dom";

import {
  ArrowRight,
  BookOpen,
  Building2,
  CalendarDays,
  CalendarRange,
  GraduationCap,
  LayoutDashboard,
  UserRoundCheck,
  UserRoundPlus,
  Users,
} from "lucide-react";

import { useAuth } from "../../auth/context/AuthContext";

// =========================================
// ADMINISTRATOR DASHBOARD MODULES
// =========================================

const ADMIN_MODULES = [
  {
    title: "Create Account",
    description:
      "Create user accounts and assign the appropriate system roles.",
    path: "/admin/createaccount",
    icon: UserRoundPlus,
    iconBackground: "bg-[#E8F1FF]",
    iconColor: "text-[#527FC0]",
  },
  {
    title: "Students",
    description:
      "View student records, search by name or ID, and inspect academic status.",
    path: "/admin/students",
    icon: Users,
    iconBackground: "bg-[#E8F1FF]",
    iconColor: "text-[#527FC0]",
  },
  {
    title: "Lecturers",
    description:
      "View lecturer information and search lecturer records.",
    path: "/admin/lecturers",
    icon: GraduationCap,
    iconBackground: "bg-[#F0EBFF]",
    iconColor: "text-[#8470B9]",
  },
  {
    title: "Assign Lecturer",
    description:
      "Assign lecturers to class sections and validate teaching schedules.",
    path: "/admin/assignlecturer",
    icon: UserRoundCheck,
    iconBackground: "bg-[#E6F7F1]",
    iconColor: "text-[#429B83]",
  },
  {
    title: "Semesters",
    description:
      "Manage academic years, semester dates, and semester records.",
    path: "/admin/semesters",
    icon: CalendarDays,
    iconBackground: "bg-[#FFF0E8]",
    iconColor: "text-[#C88A62]",
  },
  {
    title: "Faculties",
    description:
      "Manage faculty information and organizational records.",
    path: "/admin/faculties",
    icon: Building2,
    iconBackground: "bg-[#F0EBFF]",
    iconColor: "text-[#8470B9]",
  },
  {
    title: "Courses",
    description:
      "Manage courses, grading weights, credits, and prerequisites.",
    path: "/admin/courses",
    icon: BookOpen,
    iconBackground: "bg-[#E8F1FF]",
    iconColor: "text-[#527FC0]",
  },
  {
    title: "Class Sections",
    description:
      "Manage class sections, rooms, schedules, and enrollment capacity.",
    path: "/admin/class-sections",
    icon: CalendarRange,
    iconBackground: "bg-[#E6F7F1]",
    iconColor: "text-[#429B83]",
  },
];

// =========================================
// DASHBOARD MODULE CARD
// =========================================

function DashboardModuleCard({ module }) {
  const Icon = module.icon;

  return (
    <Link
      to={module.path}
      className={[
        "group flex h-full flex-col",
        "rounded-2xl border border-[#E2EAF5]",
        "bg-white p-5 shadow-sm",
        "transition-all duration-200",
        "hover:-translate-y-0.5",
        "hover:border-[#B6CFEF]",
        "hover:shadow-md",
        "focus-visible:outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-[#83B1E3]",
      ].join(" ")}
    >
      {/* ICON */}

      <div
        className={[
          "flex h-12 w-12 items-center",
          "justify-center rounded-xl",
          module.iconBackground,
          module.iconColor,
        ].join(" ")}
      >
        <Icon
          size={22}
          strokeWidth={1.8}
        />
      </div>

      {/* CONTENT */}

      <div className="mt-4 flex-1">
        <h3 className="text-base font-bold text-[#2F5488]">
          {module.title}
        </h3>

        <p className="mt-2 text-sm leading-6 text-slate-500">
          {module.description}
        </p>
      </div>

      {/* ACTION LINK */}

      <div
        className={[
          "mt-5 flex items-center gap-2",
          "text-sm font-semibold text-[#476FA9]",
          "transition-colors",
          "group-hover:text-[#315C96]",
        ].join(" ")}
      >
        Open module

        <ArrowRight
          size={16}
          className="transition-transform group-hover:translate-x-1"
        />
      </div>
    </Link>
  );
}

// =========================================
// ADMINISTRATOR DASHBOARD
// =========================================

export default function AdminDashboardPage() {
  const { user } = useAuth();

  const displayName =
    user?.fullName ||
    user?.full_name ||
    user?.displayName ||
    user?.name ||
    "Administrator";

  return (
    <div className="min-h-full bg-[#F7FAFF] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-7">

        {/* ================================= */}
        {/* PAGE HEADER */}
        {/* ================================= */}

        <div>
          <div className="mb-3 flex items-center gap-2">
            <div
              className={[
                "flex h-10 w-10 items-center",
                "justify-center rounded-xl",
                "bg-[#E7F0FF] text-[#476FA9]",
              ].join(" ")}
            >
              <LayoutDashboard size={20} />
            </div>

            <span
              className={[
                "text-xs font-bold uppercase",
                "tracking-[0.14em] text-[#6E91C2]",
              ].join(" ")}
            >
              Administrator Portal
            </span>
          </div>

          <h1
            className={[
              "text-2xl font-bold",
              "tracking-tight text-[#2F5488]",
            ].join(" ")}
          >
            Dashboard
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Welcome back,{" "}
            <span className="font-semibold text-slate-700">
              {displayName}
            </span>
            .
          </p>
        </div>

        {/* ================================= */}
        {/* SECTION HEADER */}
        {/* ================================= */}

        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-[#365B91]">
              Management Modules
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Select a module to manage academic records
              and administrative operations.
            </p>
          </div>

          <div
            className={[
              "rounded-full border border-[#D8E6F8]",
              "bg-[#EDF5FF] px-3 py-1.5",
              "text-xs font-semibold text-[#527FB8]",
            ].join(" ")}
          >
            {ADMIN_MODULES.length} modules
          </div>
        </div>

        {/* ================================= */}
        {/* MODULE GRID */}
        {/* ================================= */}

        <div
          className={[
            "grid grid-cols-1 gap-5",
            "md:grid-cols-2",
            "xl:grid-cols-3",
          ].join(" ")}
        >
          {ADMIN_MODULES.map((module) => (
            <DashboardModuleCard
              key={module.path}
              module={module}
            />
          ))}
        </div>

        {/* ================================= */}
        {/* FOOTNOTE */}
        {/* ================================= */}

        <div
          className={[
            "rounded-xl border border-[#DFEAF8]",
            "bg-[#EFF6FF] px-4 py-3",
          ].join(" ")}
        >
          <p className="text-xs leading-5 text-[#5C7EAA]">
            Administrator access is restricted to
            authorized users. Lecturer assignments
            are managed separately from Class Section
            Management.
          </p>
        </div>

      </div>
    </div>
  );
}
