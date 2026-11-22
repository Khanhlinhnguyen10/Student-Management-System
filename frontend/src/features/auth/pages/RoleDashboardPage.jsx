
import { useState } from "react";
import { useAuth } from "../context/AuthContext";

const ROLE_NAMES = {
  Administrator: "Administrator Dashboard",
  Student: "Student Dashboard",
  Lecturer: "Lecturer Dashboard",
};

export default function RoleDashboardPage() {
  const { user, signOut } = useAuth();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogout() {
    setLoading(true);
    setError("");

    try {
      await signOut();
    } catch (err) {
      setError(err.message || "Không thể đăng xuất.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10">
      <div className="mx-auto max-w-4xl rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              {ROLE_NAMES[user.role]}
            </h1>

            <p className="mt-3 text-slate-600">
              Welcome, {user.fullName}
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Username: {user.username}
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Role: {user.role}
            </p>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            disabled={loading}
            className="rounded-lg bg-slate-900 px-5 py-2.5 font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {loading ? "Logging out..." : "Log out"}
          </button>
        </div>

        {error && (
          <p role="alert" className="mt-4 text-sm text-red-600">
            {error}
          </p>
        )}
      </div>
    </main>
  );
}
