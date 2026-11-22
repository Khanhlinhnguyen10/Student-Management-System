
import { Link } from "react-router-dom";
import { ROUTES } from "../../config/routes";

function NotFoundPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center bg-[#F3F9FF] px-4 text-center">
      <h1 className="text-6xl font-bold text-[#194B7C]">
        404
      </h1>

      <h2 className="mt-4 text-2xl font-semibold text-slate-800">
        Page Not Found
      </h2>

      <p className="mt-3 text-sm text-slate-600">
        The requested page could not be found.
      </p>

      <Link
        to={ROUTES.LOGIN}
        className="mt-6 rounded-lg bg-[#3674B6] px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-[#28649F]"
      >
        Back to Login
      </Link>
    </main>
  );
}

export default NotFoundPage;
