
import { Menu, UserRound } from "lucide-react";

function Header({
  title = "Dashboard",
  subtitle = "Academic management system",
  user,
  onMenuClick,
}) {
  const displayName = user?.fullName || user?.username || "User";
  const displayRole = user?.role || "";

  return (
    <header className="flex min-h-20 items-center justify-between gap-4 border-b border-[#DCE9F5] bg-white px-5 py-4 sm:px-7">

      {/* LEFT: Mobile menu and page information */}
      <div className="flex min-w-0 items-center gap-3">

        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Open navigation menu"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-[#456987] transition-colors hover:bg-[#E6F1FF] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 lg:hidden"
        >
          <Menu size={22} aria-hidden="true" />
        </button>

        <div className="min-w-0">
          <h1 className="truncate text-xl font-bold tracking-tight text-[#194B7C] sm:text-2xl">
            {title}
          </h1>

          <p className="mt-1 hidden truncate text-xs text-slate-500 sm:block">
            {subtitle}
          </p>
        </div>
      </div>

      {/* RIGHT: Authenticated user information */}
      <div className="flex shrink-0 items-center gap-3">

        <div className="hidden max-w-44 text-right sm:block">
          <p className="truncate text-sm font-semibold text-[#194B7C]">
            {displayName}
          </p>

          <p className="mt-0.5 text-xs text-slate-500">
            {displayRole}
          </p>
        </div>

        <div
          aria-label="Account"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-[#E3F1FF] text-[#3674B6]"
        >
          <UserRound
            size={21}
            strokeWidth={1.8}
            aria-hidden="true"
          />
        </div>
      </div>

    </header>
  );
}

export default Header;
