
import { Outlet } from "react-router-dom";
import { GraduationCap } from "lucide-react";

function AuthLayout() {
  return (
    <div className="min-h-dvh overflow-x-hidden bg-[#F3F9FF]">
      <main className="grid min-h-dvh lg:grid-cols-2">

        {/* LEFT: PASTEL BLUE BRANDING */}
        <section className="relative hidden min-h-dvh overflow-hidden bg-[#B8D9F3] lg:flex lg:flex-col lg:justify-center">

          {/* Circle 1: top left */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -left-24 -top-24 h-80 w-80 rounded-full bg-white/35 blur-2xl"
          />

          {/* Circle 2: bottom left */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -bottom-32 left-24 h-96 w-96 rounded-full bg-[#75B5E3]/30 blur-3xl"
          />

          {/* Subtle background glow */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute right-0 top-1/3 h-64 w-64 rounded-full bg-white/20 blur-3xl"
          />

          {/* Branding content */}
          <div className="relative z-10 px-10 pr-24 xl:px-16 xl:pr-28">

            {/* Brand logo */}
            <div className="mb-7 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/65 text-blue-800 shadow-sm">
                <GraduationCap
                  size={26}
                  strokeWidth={1.8}
                  aria-hidden="true"
                />
              </div>

              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[#356D9D]">
                Academic Portal
              </span>
            </div>

            {/* Academia title */}
            <h1 className="text-5xl font-extrabold tracking-tight text-[#194B7C] xl:text-6xl">
              ACADEMIA
            </h1>

            {/* Accent line */}
            <div className="mt-5 h-1 w-20 rounded-full bg-[#4C91C9]" />
          </div>

          {/* Curved separator */}
          <svg
            className="pointer-events-none absolute -right-px top-0 z-20 h-full w-24"
            viewBox="0 0 96 900"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path
              d="
                M 96 0
                C 24 150, 115 310, 56 450
                C 0 590, 115 750, 96 900
                L 96 900
                L 96 0
                Z
              "
              fill="#F3F9FF"
            />
          </svg>
        </section>

        {/* RIGHT: AUTHENTICATION CONTENT */}
        <section className="relative flex min-h-dvh items-center justify-center bg-[#F3F9FF] px-6 py-5 sm:px-10 lg:py-4">

          {/* Light background glow */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute right-0 top-0 h-52 w-52 rounded-full bg-white/60 blur-3xl"
          />

          {/* Login / Recover Password */}
          <div className="relative z-10 w-full max-w-sm">
            <Outlet />
          </div>

        </section>
      </main>
    </div>
  );
}

export default AuthLayout;
