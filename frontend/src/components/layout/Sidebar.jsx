
import { NavLink } from "react-router-dom";

import {
  GraduationCap,
  LogOut,
  X,
} from "lucide-react";

import { ROLE_MENUS } from "../../config/roleMenus";

function Sidebar({
  role,
  isOpen = false,
  onClose,
  onLogout,
}) {
  const menuItems = ROLE_MENUS[role] ?? [];

  const handleLogout = () => {
    // Logout thực tế sẽ được xử lý thông qua
    // Flask Authentication API ở Stage 2.
    onLogout?.();
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/30 lg:hidden"
        />
      )}

      {/* Sidebar */}
      <aside
        aria-label={`${role ?? "User"} navigation`}
        className={`
          fixed inset-y-0 left-0 z-50
          flex w-64 flex-col
          border-r border-[#BFD9EF]
          bg-[#D5E9FB]
          transition-transform duration-200
          lg:static lg:translate-x-0
          ${
            isOpen
              ? "translate-x-0"
              : "-translate-x-full"
          }
        `}
      >

        {/* Branding */}
        <div className="flex h-20 shrink-0 items-center justify-between border-b border-[#BED8EE] px-5">

          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#3674B6] text-white">
              <GraduationCap
                size={23}
                strokeWidth={1.8}
                aria-hidden="true"
              />
            </div>

            <div>
              <h1 className="text-base font-extrabold tracking-wide text-[#194B7C]">
                ACADEMIA
              </h1>

              <p className="text-[11px] text-[#456987]">
                Academic Portal
              </p>
            </div>
          </div>

          {/* Close button on mobile */}
          <button
            type="button"
            aria-label="Close sidebar"
            onClick={onClose}
            className="rounded-lg p-1 text-[#456987] hover:bg-white/60 lg:hidden"
          >
            <X size={20} aria-hidden="true" />
          </button>

        </div>

        {/* Role label */}
        <div className="px-5 pb-2 pt-5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#456987]">
            {role ?? "Navigation"}
          </p>
        </div>

        {/* Navigation */}
        <nav
          aria-label="Main navigation"
          className="flex-1 space-y-1 overflow-y-auto px-3 pb-4"
        >
          {menuItems.map(({ label, path, Icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === `/${role?.toLowerCase()}`}
              onClick={onClose}
              className={({ isActive }) =>
                `
                  flex items-center gap-3 rounded-lg
                  px-3 py-2.5 text-sm font-medium
                  transition-colors
                  focus-visible:outline
                  focus-visible:outline-2
                  focus-visible:outline-offset-2
                  focus-visible:outline-blue-700
                  ${
                    isActive
                      ? "bg-[#3674B6] text-white shadow-sm"
                      : "text-[#365C7C] hover:bg-white/65"
                  }
                `
              }
            >
              <Icon
                size={18}
                strokeWidth={1.8}
                aria-hidden="true"
              />

              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="shrink-0 border-t border-[#BED8EE] p-3">
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-[#365C7C] transition-colors hover:bg-white/65 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
          >
            <LogOut
              size={18}
              strokeWidth={1.8}
              aria-hidden="true"
            />

            <span>Log out</span>
          </button>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
