
import { useState } from "react";
import { Link } from "react-router-dom";

import { ROUTES } from "../../../config/routes";
import { useAuth } from "../context/AuthContext";

const ROLES = [
  { value: "Student", label: "Student" },
  { value: "Lecturer", label: "Lecturer" },
  { value: "Administrator", label: "Admin" },
];

export default function LoginForm() {
  const { signIn } = useAuth();

  const [role, setRole] = useState("Student");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!username.trim() || !password) {
      setError("Vui lòng nhập đầy đủ tài khoản và mật khẩu.");
      return;
    }

    setLoading(true);

    try {
      await signIn({
        username: username.trim(),
        password,
        role,
      });

      // AppRoutes redirects based on the role returned by Flask.
    } catch (err) {
      if (err.status === 401) {
        setError("Tài khoản, mật khẩu hoặc vai trò không đúng.");
      } else if (err.status === 429) {
        setError("Bạn thử đăng nhập quá nhiều lần. Vui lòng thử lại sau.");
      } else {
        setError(err.message || "Đăng nhập thất bại.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-5">
      <div>
        <label className="mb-2 block text-sm font-semibold text-slate-700">
          Login as
        </label>

        <div
          className="grid grid-cols-3 gap-2"
          role="group"
          aria-label="Login role"
        >
          {ROLES.map((item) => (
            <button
              key={item.value}
              type="button"
              onClick={() => {
                setRole(item.value);
                setError("");
              }}
              aria-pressed={role === item.value}
              className={`rounded-lg border px-3 py-2.5 text-sm font-medium transition ${
                role === item.value
                  ? "border-blue-600 bg-blue-50 text-blue-700"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label
          htmlFor="login-username"
          className="mb-2 block text-sm font-semibold text-slate-700"
        >
          Username
        </label>

        <input
          id="login-username"
          type="text"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          placeholder="Enter your username"
          maxLength={50}
          required
          className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none focus:border-blue-500"
        />
      </div>

      <div>
        <label
          htmlFor="login-password"
          className="mb-2 block text-sm font-semibold text-slate-700"
        >
          Password
        </label>

        <div className="relative">
          <input
            id="login-password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
            required
            className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 pr-20 text-slate-900 outline-none focus:border-blue-500"
          />

          <button
            type="button"
            onClick={() => setShowPassword((value) => !value)}
            aria-label={showPassword ? "Hide password" : "Show password"}
            className="absolute inset-y-0 right-3 text-sm font-medium text-blue-600"
          >
            {showPassword ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      <div className="text-right">
        <Link
          to={ROUTES.RECOVER_PASSWORD}
          className="text-sm font-medium text-blue-600 hover:underline"
        >
          Forgot password?
        </Link>
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}
