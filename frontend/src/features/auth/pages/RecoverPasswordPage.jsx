
import { Link } from "react-router-dom";

import {
  ArrowLeft,
  KeyRound,
  ShieldCheck,
} from "lucide-react";

import { ROUTES } from "../../../config/routes";

function RecoverPasswordPage() {
  return (
    <section className="mx-auto w-full max-w-[370px]">

      {/* PAGE HEADER */}
      <header className="mb-6 text-center">

        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#DFEEFF] text-[#286CAC]">
          <KeyRound
            size={28}
            strokeWidth={1.8}
            aria-hidden="true"
          />
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-[#194B7C]">
          Recover Password
        </h1>

        <p className="mt-2 text-sm leading-6 text-slate-500">
          Recover access to your Academia account.
        </p>

      </header>

      {/* RECOVERY INFORMATION */}
      <div className="rounded-xl border border-[#D5E2F0] bg-white/75 p-5">

        <div className="flex items-start gap-3">

          <ShieldCheck
            size={21}
            strokeWidth={1.8}
            aria-hidden="true"
            className="mt-0.5 shrink-0 text-[#3674B6]"
          />

          <div>
            <h2 className="text-sm font-semibold text-[#194B7C]">
              Account Verification Required
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-600">
              Password recovery requires verification
              using your registered contact information.
            </p>

            <p className="mt-3 text-xs leading-5 text-slate-500">
              This service will be available after the
              authentication backend is connected.
            </p>
          </div>

        </div>
      </div>

      {/* BACK TO LOGIN */}
      <Link
        to={ROUTES.LOGIN}
        className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#3674B6] text-sm font-semibold text-white transition-colors hover:bg-[#28649F] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
      >
        <ArrowLeft size={17} aria-hidden="true" />
        Back to Login
      </Link>

      {/* FOOTER */}
      <p className="mt-5 text-center text-[11px] text-slate-400">
        Academia · Group 05
      </p>

    </section>
  );
}

export default RecoverPasswordPage;
