
import { GraduationCap } from "lucide-react";
import LoginForm from "../components/LoginForm";

function LoginPage() {
  return (
    <section className="mx-auto w-full max-w-[370px]">

      {/* Login header */}
      <header className="mb-5 text-center">

        {/* Academia logo */}
        <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#DFEEFF] text-[#286CAC]">
          <GraduationCap
            size={28}
            strokeWidth={1.8}
            aria-hidden="true"
          />
        </div>

        {/* Welcome title */}
        <h1 className="text-2xl font-bold tracking-tight text-[#194B7C]">
          Welcome back
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          Sign in to your Academia account
        </p>

      </header>

      {/* Login form */}
      <LoginForm />

      {/* Footer */}
      <p className="mt-4 text-center text-[11px] text-slate-400">
        Academia · Group 05
      </p>

    </section>
  );
}

export default LoginPage;
