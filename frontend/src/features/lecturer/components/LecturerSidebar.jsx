
import { NavLink } from "react-router-dom";

import {
  BookOpen,
  GraduationCap,
  KeyRound,
  LayoutDashboard,
  UserRound,
} from "lucide-react";


const MENU_ITEMS = [
  {
    label: "Dashboard",
    path: "/lecturer",
    icon: LayoutDashboard,
    end: true,
  },
  {
    label: "Profile",
    path: "/lecturer/profile",
    icon: UserRound,
  },
  {
    label: "Gradebook",
    path: "/lecturer/gradebook",
    icon: BookOpen,
  },
  {
    label: "Change Password",
    path: "/lecturer/change-password",
    icon: KeyRound,
  },
];


function MenuLink({ item }) {
  const Icon = item.icon;

  return (
    <NavLink
      to={item.path}
      end={item.end}
      className={({ isActive }) =>
        [
          "relative flex h-[43px] items-center gap-3",
          "rounded-xl px-3.5",
          "text-[13px] transition-all duration-150",
          isActive
            ? [
                "bg-[#476FA9]",
                "font-semibold text-white",
                "shadow-[0_3px_8px_rgba(56,101,158,0.18)]",
              ].join(" ")
            : [
                "font-medium text-[#56789E]",
                "hover:bg-white/50",
                "hover:text-[#365D91]",
              ].join(" "),
        ].join(" ")
      }
    >
      <Icon
        size={18}
        strokeWidth={1.8}
        className="shrink-0"
      />

      <span className="truncate">
        {item.label}
      </span>
    </NavLink>
  );
}


export default function LecturerSidebar() {
  return (
    <aside
      className={[
        "flex w-full shrink-0 flex-col",
        "border-b border-[#C2D8EC]",
        "bg-[#D6E7F8]",
        "px-[19px] py-[22px]",
        "md:sticky md:top-0",
        "md:h-dvh md:w-[254px]",
        "md:border-b-0 md:border-r",
      ].join(" ")}
    >
      {/* ACADEMIA LOGO */}
      <div className="mb-[32px] flex items-center gap-3 px-[7px]">
        <div
          className={[
            "flex h-10 w-10 shrink-0",
            "items-center justify-center",
            "rounded-[13px]",
            "bg-[#8DB9E1] text-white",
            "shadow-[0_4px_10px_rgba(76,125,181,0.13)]",
          ].join(" ")}
        >
          <GraduationCap
            size={23}
            strokeWidth={1.8}
          />
        </div>

        <div className="min-w-0">
          <h2 className="text-[19px] font-bold leading-[23px] tracking-tight text-[#365D91]">
            Academia
          </h2>

          <p className="mt-0.5 whitespace-nowrap text-[11px] text-[#7094B8]">
            Student Management
          </p>
        </div>
      </div>

      {/* MENU HEADING */}
      <p
        className={[
          "mb-3 px-[11px]",
          "text-[10px] font-bold uppercase",
          "tracking-[0.18em]",
          "text-[#789FC6]",
        ].join(" ")}
      >
        Lecturer Menu
      </p>

      {/* LECTURER NAVIGATION */}
      <nav
        aria-label="Lecturer navigation"
        className="flex flex-col gap-[6px]"
      >
        {MENU_ITEMS.map((item) => (
          <MenuLink
            key={item.path}
            item={item}
          />
        ))}
      </nav>
    </aside>
  );
}
