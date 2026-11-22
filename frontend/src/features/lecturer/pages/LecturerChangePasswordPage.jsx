
import { useState } from "react";
import { Link } from "react-router-dom";

import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LockKeyhole,
  Save,
  ShieldCheck,
} from "lucide-react";

import {
  changeLecturerPassword,
} from "../api/lecturerPasswordApi";


const INITIAL_FORM = {
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
};


const PASSWORD_RULES = [
  "8 to 128 characters",
  "At least one uppercase letter",
  "At least one lowercase letter",
  "At least one number",
  "At least one special character",
  "Different from current password",
];


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
        className="mb-1.5 block text-[12px] font-semibold text-[#365D91]"
      >
        {label}
      </label>

      <div className="relative">
        <input
          id={id}
          name={id}
          type={visible ? "text" : "password"}
          value={value}
          onChange={(event) =>
            onChange(event.target.value)
          }
          autoComplete={autoComplete}
          placeholder={placeholder}
          required
          className={[
            "h-[41px] w-full rounded-[10px]",
            "border border-[#CBDDF0]",
            "bg-[#F8FBFF]",
            "px-3.5 pr-10",
            "text-[12px] text-[#31577F]",
            "outline-none transition-all",
            "placeholder:text-[#9AB0C6]",
            "focus:border-[#75A7DE]",
            "focus:ring-2 focus:ring-[#D9EAFE]",
          ].join(" ")}
        />

        <button
          type="button"
          onClick={() =>
            setVisible((previous) => !previous)
          }
          aria-label={
            visible ? "Hide password" : "Show password"
          }
          aria-pressed={visible}
          className={[
            "absolute right-2.5 top-1/2",
            "-translate-y-1/2",
            "rounded-lg p-1.5",
            "text-[#7B9CBD]",
            "transition-colors",
            "hover:bg-[#E9F3FD]",
            "hover:text-[#416DA3]",
          ].join(" ")}
        >
          {visible ? (
            <EyeOff size={16} />
          ) : (
            <Eye size={16} />
          )}
        </button>
      </div>
    </div>
  );
}


function validateForm(form) {
  const {
    currentPassword,
    newPassword,
    confirmPassword,
  } = form;

  if (!currentPassword) {
    return "Please enter your current password.";
  }

  if (!newPassword) {
    return "Please enter your new password.";
  }

  if (
    newPassword.length < 8 ||
    newPassword.length > 128
  ) {
    return "New password must contain 8 to 128 characters.";
  }

  if (
    !/[A-Z]/.test(newPassword) ||
    !/[a-z]/.test(newPassword) ||
    !/[0-9]/.test(newPassword) ||
    !/[^A-Za-z0-9]/.test(newPassword)
  ) {
    return (
      "New password must include uppercase, lowercase, " +
      "number and special characters."
    );
  }

  if (newPassword === currentPassword) {
    return "New password must differ from your current password.";
  }

  if (newPassword !== confirmPassword) {
    return "Password confirmation does not match.";
  }

  return null;
}


export default function LecturerChangePasswordPage() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function updateField(field, value) {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));

    setError("");
    setSuccess("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (loading) {
      return;
    }

    setError("");
    setSuccess("");

    const validationError = validateForm(form);

    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    try {
      const response = await changeLecturerPassword({
        currentPassword: form.currentPassword,
        newPassword: form.newPassword,
        confirmPassword: form.confirmPassword,
      });

      setForm({ ...INITIAL_FORM });

      setSuccess(
        response?.message ||
          "Password changed successfully."
      );
    } catch (requestError) {
      if (requestError?.status === 401) {
        setError(
          "Your session has expired. Please log in again."
        );
      } else if (requestError?.status === 409) {
        setError(
          "Your password has changed in another request. " +
            "Please verify your current password and try again."
        );
      } else {
        setError(
          requestError?.message ||
            "Unable to change your password."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1100px] pb-3">

      {/* MAIN PANEL */}
      <section
        className={[
          "overflow-hidden rounded-[16px]",
          "border border-[#D6E5F5]",
          "bg-white",
          "shadow-[0_2px_6px_rgba(65,110,165,0.05)]",
        ].join(" ")}
      >

        {/* COMPACT PAGE HEADER */}
        <div
          className={[
            "flex items-center gap-3",
            "border-b border-[#DFEAF7]",
            "bg-gradient-to-r",
            "from-[#E8F3FF]",
            "via-[#EEF4FF]",
            "to-[#F4EEFC]",
            "px-5 py-3.5",
          ].join(" ")}
        >
          <div
            className={[
              "flex h-10 w-10 shrink-0",
              "items-center justify-center",
              "rounded-xl bg-white/90",
              "text-[#476FA9]",
              "shadow-sm",
            ].join(" ")}
          >
            <LockKeyhole size={20} strokeWidth={1.8} />
          </div>

          <div className="min-w-0">
            <p
              className={[
                "text-[9px] font-bold",
                "uppercase tracking-[0.15em]",
                "text-[#7C9DCA]",
              ].join(" ")}
            >
              Lecturer / Account Security
            </p>

            <h1 className="mt-0.5 text-[19px] font-bold leading-tight text-[#315D94]">
              Change Password
            </h1>

            <p className="mt-0.5 text-[11px] text-[#7393B8]">
              Securely update your account password.
            </p>
          </div>
        </div>

        {/* FORM AND REQUIREMENTS */}
        <div
          className={[
            "grid grid-cols-1",
            "lg:grid-cols-[minmax(0,1fr)_270px]",
          ].join(" ")}
        >

          {/* LEFT: PASSWORD FORM */}
          <div className="min-w-0 px-5 py-4 sm:px-6">

            <div className="mb-4 flex items-center gap-2.5">
              <div
                className={[
                  "flex h-8 w-8",
                  "items-center justify-center",
                  "rounded-lg bg-[#E8F2FE]",
                  "text-[#527FB7]",
                ].join(" ")}
              >
                <KeyRound size={17} />
              </div>

              <div>
                <h2 className="text-[13px] font-bold text-[#315D94]">
                  Password Information
                </h2>

                <p className="text-[11px] text-[#819DBD]">
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
                id="currentPassword"
                label="Current Password"
                value={form.currentPassword}
                onChange={(value) =>
                  updateField("currentPassword", value)
                }
                autoComplete="current-password"
                placeholder="Enter your current password"
              />

              {/* NEW PASSWORD + CONFIRM PASSWORD */}
              <div
                className={[
                  "grid grid-cols-1 gap-3",
                  "sm:grid-cols-2",
                ].join(" ")}
              >
                <PasswordField
                  id="newPassword"
                  label="New Password"
                  value={form.newPassword}
                  onChange={(value) =>
                    updateField("newPassword", value)
                  }
                  autoComplete="new-password"
                  placeholder="Enter new password"
                />

                <PasswordField
                  id="confirmPassword"
                  label="Confirm New Password"
                  value={form.confirmPassword}
                  onChange={(value) =>
                    updateField("confirmPassword", value)
                  }
                  autoComplete="new-password"
                  placeholder="Confirm new password"
                />
              </div>

              {/* ERROR MESSAGE */}
              {error && (
                <div
                  role="alert"
                  className={[
                    "flex items-start gap-2",
                    "rounded-lg border border-[#F4D0D0]",
                    "bg-[#FFF3F2]",
                    "px-3 py-2",
                    "text-[11px] text-[#AC4F55]",
                  ].join(" ")}
                >
                  <AlertCircle
                    size={15}
                    className="shrink-0"
                  />
                  <span>{error}</span>
                </div>
              )}

              {/* SUCCESS MESSAGE */}
              {success && (
                <div
                  role="status"
                  className={[
                    "flex items-start gap-2",
                    "rounded-lg border border-[#C9E9DC]",
                    "bg-[#EFFAF5]",
                    "px-3 py-2",
                    "text-[11px] text-[#247A60]",
                  ].join(" ")}
                >
                  <CheckCircle2
                    size={15}
                    className="shrink-0"
                  />
                  <span>{success}</span>
                </div>
              )}

              {/* ACTION BUTTONS */}
              <div
                className={[
                  "flex flex-wrap items-center",
                  "justify-between gap-3",
                  "border-t border-[#EAF1F9]",
                  "pt-4",
                ].join(" ")}
              >
                <Link
                  to="/lecturer"
                  className={[
                    "inline-flex h-[37px]",
                    "items-center gap-2",
                    "rounded-lg border border-[#D6E4F3]",
                    "bg-white px-3.5",
                    "text-[11px] font-semibold",
                    "text-[#6488AE]",
                    "transition hover:bg-[#F0F7FF]",
                  ].join(" ")}
                >
                  <ArrowLeft size={14} />
                  Back to Dashboard
                </Link>

                <button
                  type="submit"
                  disabled={loading}
                  className={[
                    "inline-flex h-[37px]",
                    "items-center justify-center gap-2",
                    "rounded-lg bg-[#476FA9]",
                    "px-4 text-[11px]",
                    "font-bold text-white",
                    "shadow-[0_3px_8px_rgba(66,108,165,0.15)]",
                    "transition hover:bg-[#3A619B]",
                    "disabled:cursor-not-allowed",
                    "disabled:opacity-60",
                  ].join(" ")}
                >
                  <Save size={15} />

                  {loading
                    ? "Saving..."
                    : "Update Password"}
                </button>
              </div>
            </form>
          </div>

          {/* RIGHT: PASSWORD REQUIREMENTS */}
          <aside
            className={[
              "border-t border-[#E6EEF8]",
              "bg-[#FAFCFF]",
              "px-5 py-4",
              "lg:border-l lg:border-t-0",
            ].join(" ")}
          >
            <div className="mb-3 flex items-center gap-2.5">
              <div
                className={[
                  "flex h-8 w-8",
                  "items-center justify-center",
                  "rounded-lg bg-[#E4F5EF]",
                  "text-[#3B967E]",
                ].join(" ")}
              >
                <ShieldCheck size={17} />
              </div>

              <h3 className="text-[12px] font-bold text-[#315D94]">
                Password Requirements
              </h3>
            </div>

            <ul className="space-y-2.5">
              {PASSWORD_RULES.map((rule) => (
                <li
                  key={rule}
                  className="flex items-start gap-2"
                >
                  <CheckCircle2
                    size={14}
                    className="mt-[1px] shrink-0 text-[#55AA91]"
                  />

                  <span className="text-[11px] leading-4 text-[#6686A9]">
                    {rule}
                  </span>
                </li>
              ))}
            </ul>

            <div
              className={[
                "mt-4 rounded-[11px]",
                "border border-[#D9E8F8]",
                "bg-[#EDF6FF]",
                "px-3 py-3",
              ].join(" ")}
            >
              <div className="flex items-center gap-2">
                <ShieldCheck
                  size={15}
                  className="text-[#4D89B4]"
                />

                <h4 className="text-[11px] font-bold text-[#416D9F]">
                  Account Security
                </h4>
              </div>

              <p className="mt-1.5 text-[11px] leading-[18px] text-[#6989AA]">
                Never share your password with others.
                Your changes are saved securely.
              </p>
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
}
