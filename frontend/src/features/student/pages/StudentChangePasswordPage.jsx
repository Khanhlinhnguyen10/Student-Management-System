
import { useState } from "react";

import {
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";

// =============================================
// API
// =============================================

async function readResponse(response, fallbackMessage) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      data.error || fallbackMessage
    );

    error.status = response.status;
    throw error;
  }

  return data;
}

async function changePassword(payload) {
  const csrfResponse = await fetch("/api/auth/csrf", {
    method: "GET",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
    },
  });

  const csrfData = await readResponse(
    csrfResponse,
    "Unable to verify your session."
  );

  if (!csrfData.csrfToken) {
    throw new Error("CSRF token is missing.");
  }

  const response = await fetch(
    "/api/auth/change-password",
    {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-CSRF-Token": csrfData.csrfToken,
      },
      body: JSON.stringify(payload),
    }
  );

  return readResponse(
    response,
    "Unable to change password."
  );
}

// =============================================
// INPUT COMPONENT
// =============================================

function PasswordField({
  id,
  label,
  value,
  onChange,
  autoComplete,
  placeholder,
}) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="min-w-0">
      <label
        htmlFor={id}
        className="mb-1.5 block text-xs font-semibold text-[#536D8D]"
      >
        {label}
      </label>

      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          autoComplete={autoComplete}
          placeholder={placeholder}
          maxLength={128}
          required
          className="h-10 w-full rounded-xl border border-[#D9E6F3] bg-[#F8FBFF] px-3 pr-11 text-sm text-[#365D91] outline-none transition focus:border-[#83ACDD] focus:ring-2 focus:ring-[#DCEAFB]"
        />

        <button
          type="button"
          onClick={() => setVisible((previous) => !previous)}
          aria-label={`${visible ? "Hide" : "Show"} ${label}`}
          aria-pressed={visible}
          className="absolute inset-y-0 right-3 flex items-center text-[#839BB6] hover:text-[#476FA9]"
        >
          {visible ? (
            <EyeOff size={17} aria-hidden="true" />
          ) : (
            <Eye size={17} aria-hidden="true" />
          )}
        </button>
      </div>
    </div>
  );
}

// =============================================
// PASSWORD REQUIREMENTS
// =============================================

const REQUIREMENTS = [
  "8 to 128 characters",
  "At least one uppercase letter",
  "At least one lowercase letter",
  "At least one number",
  "At least one special character",
  "Different from your current password",
];

// =============================================
// PAGE
// =============================================

export default function StudentChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    if (submitting) return;

    setError("");
    setSuccess("");

    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }

    setSubmitting(true);

    try {
      const result = await changePassword({
        currentPassword,
        newPassword,
        confirmPassword,
      });

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      setSuccess(
        result.message || "Password changed successfully."
      );
    } catch (err) {
      setError(
        err.status === 401
          ? "Your session has expired. Please log in again."
          : err.message || "Unable to change password."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-w-0 space-y-3 pb-1">

      {/* HEADER */}

      <section>
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#6389B7]">
          Student / Account Security
        </p>

        <h1 className="aca-title mt-1 text-2xl">
          Change Password
        </h1>

        <p className="mt-1 text-xs text-[#71849A]">
          Update your password to protect your academic account.
        </p>
      </section>

      {/* TWO-COLUMN LAYOUT */}

      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.55fr)_minmax(280px,1fr)]">

        {/* LEFT: PASSWORD FORM */}

        <section className="aca-panel min-w-0 p-5">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#E5F0FC] text-[#476FA9]">
              <LockKeyhole size={20} aria-hidden="true" />
            </div>

            <div>
              <h2 className="text-base font-bold text-[#365D91]">
                Update Password
              </h2>

              <p className="mt-0.5 text-xs text-[#8295AA]">
                Enter your current and new password.
              </p>
            </div>
          </div>

          <form
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            {/* CURRENT PASSWORD */}

            <PasswordField
              id="current-password"
              label="Current Password"
              value={currentPassword}
              onChange={setCurrentPassword}
              autoComplete="current-password"
              placeholder="Enter current password"
            />

            <div className="border-t border-[#EDF2F8]" />

            {/* NEW PASSWORDS SIDE BY SIDE */}

            <div className="grid gap-4 sm:grid-cols-2">
              <PasswordField
                id="new-password"
                label="New Password"
                value={newPassword}
                onChange={setNewPassword}
                autoComplete="new-password"
                placeholder="Enter new password"
              />

              <PasswordField
                id="confirm-password"
                label="Confirm New Password"
                value={confirmPassword}
                onChange={setConfirmPassword}
                autoComplete="new-password"
                placeholder="Confirm new password"
              />
            </div>

            {/* ERROR */}

            {error && (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-xl border border-[#F5CDD2] bg-[#FFF1F2] px-3 py-2 text-xs text-[#AE4757]"
              >
                <AlertCircle
                  size={16}
                  className="shrink-0"
                  aria-hidden="true"
                />
                <span>{error}</span>
              </div>
            )}

            {/* SUCCESS */}

            {success && (
              <div
                role="status"
                className="flex items-start gap-2 rounded-xl border border-[#C9EADB] bg-[#EBF8F1] px-3 py-2 text-xs text-[#35775F]"
              >
                <CheckCircle2
                  size={16}
                  className="shrink-0"
                  aria-hidden="true"
                />
                <span>{success}</span>
              </div>
            )}

            {/* SUBMIT */}

            <button
              type="submit"
              disabled={submitting}
              className="flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-[#729FD6] text-sm font-semibold text-white transition hover:bg-[#5D8CC8] disabled:cursor-not-allowed disabled:opacity-60"
            >
              <KeyRound size={17} aria-hidden="true" />

              {submitting
                ? "Updating Password..."
                : "Change Password"}
            </button>
          </form>
        </section>

        {/* RIGHT: SECURITY INFORMATION */}

        <aside className="min-w-0 space-y-3">
          <section className="rounded-2xl border border-[#DAE9F8] bg-gradient-to-br from-[#E6F1FC] to-[#F2F0FB] p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/80 text-[#476FA9]">
                <ShieldCheck
                  size={21}
                  aria-hidden="true"
                />
              </div>

              <div>
                <h2 className="text-base font-bold text-[#365D91]">
                  Password Security
                </h2>

                <p className="mt-0.5 text-xs text-[#7088A3]">
                  Keep your academic information safe.
                </p>
              </div>
            </div>
          </section>

          <section className="aca-panel p-4">
            <h3 className="text-sm font-bold text-[#365D91]">
              Password Requirements
            </h3>

            <ul className="mt-3 space-y-2">
              {REQUIREMENTS.map((rule) => (
                <li
                  key={rule}
                  className="flex items-center gap-2 text-xs text-[#71849A]"
                >
                  <CheckCircle2
                    size={14}
                    className="shrink-0 text-[#79B5A3]"
                    aria-hidden="true"
                  />
                  <span>{rule}</span>
                </li>
              ))}
            </ul>

            <div className="mt-3 border-t border-[#EDF2F8] pt-3">
              <p className="text-[11px] leading-5 text-[#8295AA]">
                Passwords are verified securely by the
                server and stored as password hashes.
              </p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
